<a id="integration-with-existing-phoenix-configuration"></a>

# 与现有 Phoenix 配置集成

**关键要求**：LDAP 必须与 `src/phoenix/config.py` 中现有的 Phoenix 身份验证系统集成。

<a id="current-authentication-configuration"></a>

#### 当前身份验证配置

**现有 `AuthSettings` NamedTuple** (`config.py:836-841`):
```python
class AuthSettings(NamedTuple):
    enable_auth: bool
    disable_basic_auth: bool
    phoenix_secret: Secret
    phoenix_admin_secret: Secret
    oauth2_clients: OAuth2Clients
```

**现有校验逻辑** (`config.py:844-870`):
```python
def get_env_auth_settings() -> AuthSettings:
    enable_auth = get_env_enable_auth()
    phoenix_secret = get_env_phoenix_secret()
    
    # Validation: Secret required when auth enabled
    if enable_auth and not phoenix_secret:
        raise ValueError(
            f"`{ENV_PHOENIX_SECRET}` must be set when "
            f"auth is enabled with `{ENV_PHOENIX_ENABLE_AUTH}`"
        )
    
    disable_basic_auth = get_env_disable_basic_auth()
    oauth2_clients = OAuth2Clients.from_configs(get_env_oauth2_settings())
    
    # ⚠️ CRITICAL VALIDATION: If basic auth disabled, must have alternative
    if enable_auth and disable_basic_auth and not oauth2_clients:
        raise ValueError(
            "OAuth2 is the only supported auth method but no OAuth2 client configs are provided."
        )
    
    return AuthSettings(...)
```

<a id="required-changes-for-ldap-integration"></a>

#### LDAP 集成所需变更

**1. 更新 `AuthSettings` NamedTuple**：

```python
class AuthSettings(NamedTuple):
    enable_auth: bool
    disable_basic_auth: bool
    phoenix_secret: Secret
    phoenix_admin_secret: Secret
    oauth2_clients: OAuth2Clients
    ldap_config: Optional[LDAPConfig]  # ✅ ADD THIS
```

**2. 添加 LDAP 配置加载器**：

```python
def get_env_ldap_config() -> Optional[LDAPConfig]:
    """Load LDAP configuration from environment variables.
    
    Returns:
        Optional[LDAPConfig]: LDAP configuration if PHOENIX_LDAP_HOST is set, None otherwise
    
    Raises:
        ValueError: If LDAP configuration is invalid
    """
    return LDAPConfig.from_env()
```

**3. 更新 `get_env_auth_settings()` 中的校验逻辑**：

```python
def get_env_auth_settings() -> AuthSettings:
    enable_auth = get_env_enable_auth()
    phoenix_secret = get_env_phoenix_secret()
    
    if enable_auth and not phoenix_secret:
        raise ValueError(
            f"`{ENV_PHOENIX_SECRET}` must be set when "
            f"auth is enabled with `{ENV_PHOENIX_ENABLE_AUTH}`"
        )
    
    phoenix_admin_secret = get_env_phoenix_admin_secret()
    disable_basic_auth = get_env_disable_basic_auth()
    
    oauth2_clients = OAuth2Clients.from_configs(get_env_oauth2_settings())
    ldap_config = get_env_ldap_config()  # ✅ ADD THIS
    
    # ✅ UPDATED VALIDATION: Check for LDAP or OAuth2 as alternative
    if enable_auth and disable_basic_auth and not oauth2_clients and not ldap_config:
        raise ValueError(
            "PHOENIX_DISABLE_BASIC_AUTH is set, but no alternative authentication methods "
            "are configured. Please configure at least one of: OAuth2 "
            "(PHOENIX_OAUTH2_*) or LDAP (PHOENIX_LDAP_*)."
        )
    
    return AuthSettings(
        enable_auth=enable_auth,
        disable_basic_auth=disable_basic_auth,
        phoenix_secret=phoenix_secret,
        phoenix_admin_secret=phoenix_admin_secret,
        oauth2_clients=oauth2_clients,
        ldap_config=ldap_config,  # ✅ ADD THIS
    )
```

**4. 更新 `create_app()` 签名**（`server/app.py:968`）：

```python
def create_app(
    db: DbSessionFactory,
    export_path: Path,
    model: Model,
    authentication_enabled: bool,
    # ... existing params ...
    oauth2_client_configs: Optional[list[OAuth2ClientConfig]] = None,
    ldap_config: Optional[LDAPConfig] = None,  # ✅ ADD THIS
    basic_auth_disabled: bool = False,
    # ... rest
) -> FastAPI:
```

**5. 更新 `main()` 以传递 LDAP 配置**（`server/main.py:458`）：

```python
app = create_app(
    db=factory,
    # ... existing params ...
    oauth2_client_configs=get_env_oauth2_settings(),
    ldap_config=auth_settings.ldap_config,  # ✅ ADD THIS
    allowed_origins=allowed_origins,
    management_url=management_url,
)
```

**6. 在应用状态中保存 LDAP 配置**（`server/app.py`）：

```python
# Store LDAP config in app state for routers to access
if ldap_config:
    app.state.ldap_config = ldap_config
```

<a id="environment-variable-interactions"></a>

#### 环境变量交互

| 场景 | 行为 | 校验 |
|----------|----------|------------|
| `ENABLE_AUTH=false` | ✅ 忽略 LDAP 配置，无需身份验证 | 不校验 |
| `ENABLE_AUTH=true` 且缺少 `PHOENIX_SECRET` | ❌ 错误：必须设置密钥 | 现有校验 |
| `ENABLE_AUTH=true` + `DISABLE_BASIC_AUTH=true`，无 OAuth2、无 LDAP | ❌ 错误：没有可用身份验证方法 | ✅ **新增**校验 |
| `ENABLE_AUTH=true` + `DISABLE_BASIC_AUTH=true`，已配置 LDAP | ✅ 仅 LDAP 身份验证 | ✅ **新增**校验 |
| `ENABLE_AUTH=true` + `DISABLE_BASIC_AUTH=true` + OAuth2 + LDAP | ✅ OAuth2 + LDAP，不使用基本身份验证 | ✅ **新增**校验 |
| `ENABLE_AUTH=true` + `DISABLE_BASIC_AUTH=false` + LDAP | ✅ 基本身份验证与 LDAP 共存 | 默认可用 |
| 已设置 `PHOENIX_LDAP_HOST`，但 `GROUP_ROLE_MAPPINGS` JSON 格式错误 | ❌ 错误：无效 JSON | ✅ 在 `LDAPConfig.from_env()` 中校验 |

<a id="authlogin-endpoint-interaction"></a>

#### `/auth/login` 端点交互

**当前代码** (`server/api/routers/auth.py:67-70`):
```python
@router.post("/login")
async def login(request: Request) -> Response:
    if get_env_disable_basic_auth():  # ⚠️ Blocks basic auth
        raise HTTPException(status_code=403)
    # ... password validation ...
```

**无需变更**：LDAP 使用独立端点（`/auth/ldap/login`），因此这项检查正确。

<a id="csrf-protection-interaction"></a>

#### CSRF 防护交互

**当前警告** (`server/app.py:1034-1040`):
```python
elif email_sender or oauth2_client_configs:
    logger.warning(
        "CSRF protection can be enabled by listing trusted origins via "
        f"the `{ENV_PHOENIX_CSRF_TRUSTED_ORIGINS}` environment variable. "
        "This is recommended when setting up OAuth2 clients or sending "
        "password reset emails."
    )
```

**需要更新**：
```python
elif email_sender or oauth2_client_configs or ldap_config:  # ✅ ADD ldap_config
    logger.warning(
        "CSRF protection can be enabled by listing trusted origins via "
        f"the `{ENV_PHOENIX_CSRF_TRUSTED_ORIGINS}` environment variable. "
        "This is recommended when setting up OAuth2 clients, LDAP, or sending "
        "password reset emails."
    )
```

<a id="rate-limiting"></a>

#### 限流

**当前**：`/auth/login` 已限流（`server/api/routers/auth.py:52-61`）

**LDAP**：必须将新 `/auth/ldap/login` 端点加入限流路径：
```python
login_rate_limiter = fastapi_ip_rate_limiter(
    rate_limiter,
    paths=[
        "/auth/login",
        "/auth/ldap/login",  # ✅ ADD THIS
        "/auth/logout",
        "/auth/refresh",
        "/auth/password-reset-email",
        "/auth/password-reset",
    ],
)
```

<a id="summary-of-changes-needed"></a>

#### 所需变更汇总

| 文件 | 变更 | 影响 |
|------|--------|--------|
| `src/phoenix/config.py` | 为 `AuthSettings` 添加 `ldap_config: Optional[LDAPConfig]` | 不可逆变更，涉及 NamedTuple 字段顺序 |
| `src/phoenix/config.py` | 更新 `get_env_auth_settings()` 校验 | 允许 LDAP 作为替代身份验证方式 |
| `src/phoenix/config.py` | 添加 `get_env_ldap_config()` 函数 | 新函数 |
| `src/phoenix/server/app.py` | 为 `create_app()` 添加 `ldap_config` 参数 | 签名变更 |
| `src/phoenix/server/app.py` | 更新 CSRF 警告以包含 LDAP | 警告消息 |
| `src/phoenix/server/app.py` | 将 `ldap_config` 存入 `app.state` | 新状态 |
| `src/phoenix/server/main.py` | 传入 `ldap_config=auth_settings.ldap_config` | 调用位置 |
| `src/phoenix/server/api/routers/auth.py` | 将 `/auth/ldap/login` 加入限流路径 | 限流 |

**所有变更均向后兼容** — LDAP 可选，现有 OAuth2 和基本身份验证继续按原方式工作。

---

<a id="phase-1-core-ldap-authentication"></a>

### 阶段 1：核心 LDAP 身份验证
