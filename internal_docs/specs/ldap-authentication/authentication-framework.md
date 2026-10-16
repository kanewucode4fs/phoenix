<a id="authentication-method-framework"></a>

## 身份验证方法框架

<a id="configuration-permutations--behavior-matrix"></a>

### 配置组合与行为矩阵

Phoenix 现已支持三种身份验证方法：**LOCAL**（用户名/密码）、**OAuth2**（OIDC）和 **LDAP**。框架必须一致地处理所有有效组合。

<a id="configuration-variables"></a>

#### 配置变量

| 变量 | 作用 |
|----------|--------|
| `PHOENIX_ENABLE_AUTH` | 启用身份验证系统，默认 `false` |
| `PHOENIX_DISABLE_BASIC_AUTH` | 禁用 LOCAL 身份验证，默认 `false` |
| `PHOENIX_OAUTH2_*` | 配置 OAuth2/OIDC 提供方，可选 |
| `PHOENIX_LDAP_HOST` | 启用 LDAP 身份验证，可选 |

<a id="validation-rules-backend-configpy"></a>

#### 校验规则（后端：`config.py`）

```python
def get_env_auth_settings() -> AuthSettings:
    # ...
    oauth2_clients = OAuth2Clients.from_configs(get_env_oauth2_settings())
    ldap_config = LDAPConfig.from_env()
    
    # ✅ CRITICAL VALIDATION
    if enable_auth and disable_basic_auth and not oauth2_clients and not ldap_config:
        raise ValueError(
            f"{ENV_PHOENIX_DISABLE_BASIC_AUTH} is set, but no alternative authentication methods "
            "are configured. Please configure at least one of: OAuth2 "
            f"(PHOENIX_OAUTH2_*) or LDAP ({ENV_PHOENIX_LDAP_HOST})."
        )
```

<a id="complete-permutation-matrix"></a>

#### 完整组合矩阵

| 启用身份验证 | 禁用基本身份验证 | OAuth2 | LDAP | 后端结果 | 登录页显示 | 说明 |
|:------------:|:--------------:|:------:|:----:|----------------|------------------|-------|
| ❌ `false` | - | - | - | ✅ 有效 | 无 | 无需身份验证 |
| ✅ `true` | ❌ `false` | ❌ | ❌ | ✅ 有效 | **LOCAL 表单** | 标准用户名/密码 |
| ✅ `true` | ❌ `false` | ✅ | ❌ | ✅ 有效 | **LOCAL 表单** + “或” + **OAuth2 按钮** | 两种方法均可用 |
| ✅ `true` | ❌ `false` | ❌ | ✅ | ✅ 有效 | **LOCAL 表单** + “或” + **LDAP 表单** | 两种方法均可用 |
| ✅ `true` | ❌ `false` | ✅ | ✅ | ✅ 有效 | **LOCAL 表单** + “或” + **LDAP 表单** + “或” + **OAuth2 按钮** | 三种方法均可用<br>**管理员对话框**：LOCAL + OAuth2 + LDAP 选项卡 |
| ✅ `true` | ✅ `true` | ❌ | ❌ | ❌ **无效** | 不适用 | **错误**：“no alternative authentication methods are configured” |
| ✅ `true` | ✅ `true` | ✅ | ❌ | ✅ 有效 | **仅 OAuth2 按钮** | 仅 OAuth2 部署<br>**管理员对话框**：仅 OAuth2 选项卡 |
| ✅ `true` | ✅ `true` | ❌ | ✅ | ✅ 有效 | **仅 LDAP 表单** | 仅 LDAP 部署<br>**管理员对话框**：仅 LDAP 选项卡 |
| ✅ `true` | ✅ `true` | ✅ | ✅ | ✅ 有效 | **LDAP 表单** + “或” + **OAuth2 按钮** | 两种外部身份验证方法<br>**管理员对话框**：仅 OAuth2 + LDAP 选项卡 |

<a id="frontend-rendering-logic-loginpagetsx"></a>

#### 前端渲染逻辑（`LoginPage.tsx`）

```typescript
const showLoginForm = !window.Config.basicAuthDisabled;
const showLDAPForm = window.Config.ldapEnabled;
const hasOAuth2Idps = window.Config.oAuth2Idps.length > 0;
```

**分隔符逻辑**：
1. LOCAL 和 LDAP 均存在时，在两者之间显示“or”：`{showLoginForm ? <div>or</div> : null}`
2. 在 LOCAL 或 LDAP 与 OAuth2 之间显示“or”：`{(showLoginForm || showLDAPForm) && hasOAuth2Idps ? <div>or</div> : null}`

<a id="admin-user-creation-logic-newuserdialogtsx"></a>

#### 管理员创建用户逻辑（`NewUserDialog.tsx`）

**选项卡可见性逻辑**：
```typescript
const showLocalTab = !window.Config.basicAuthDisabled;
const showOAuth2Tab = window.Config.oAuth2Idps.length > 0;
const showLDAPTab = window.Config.ldapEnabled;
```

**智能默认选项卡选择**：
```typescript
const defaultTab = showLocalTab
  ? "local"      // Prefer LOCAL if available
  : showOAuth2Tab
    ? "oauth2"   // Then OAuth2 if configured
    : showLDAPTab
      ? "ldap"   // Then LDAP if configured
      : "local"; // Fallback (should never happen)
```

**选项卡显示规则**：
- **LOCAL 选项卡**：仅在 `!basicAuthDisabled` 时显示，允许标准密码身份验证
- **OAuth2 选项卡**：仅在 `oAuth2Idps.length > 0` 时显示，已配置至少一个 OAuth2 提供方
- **LDAP 选项卡**：仅在 `ldapEnabled` 时显示，已配置 LDAP

**原因**：仅显示实际已配置且可用的身份验证方法，防止管理员创建无效用户。

<a id="security-cross-authentication-prevention"></a>

#### 安全：防止跨身份验证方式登录

**问题**：不同身份验证系统中的用户可能具有相同邮箱，造成安全漏洞：
- 邮箱为 `alice@corp.com` 的 LDAP 用户 → OAuth2 登录劫持账户
- 邮箱为 `bob@corp.com` 的 OAuth2 用户 → LDAP 登录创建重复账户

**解决方案**（在 `auth.py` 和 `oauth2.py` 中实现）：

1. **LDAP 登录检查 OAuth2 冲突** (`auth.py`):
```python
# Before creating LDAP user, check for OAuth2 user with same email
existing_oauth2_user = await session.scalar(
    select(models.User)
    .where(models.User.auth_method == "OAUTH2")
    .where(models.User.oauth2_client_id != LDAP_CLIENT_ID_MARKER)
    .where(func.lower(models.User.email) == email.lower())
)
if existing_oauth2_user:
    raise Unauthorized("Invalid username and/or password")  # Generic error
```

2. **OAuth2 登录检查 LDAP 冲突** (`oauth2.py`):
```python
if user.oauth2_client_id == LDAP_CLIENT_ID_MARKER:
    raise SignInNotAllowed("Sign in is not allowed.")  # Generic error
```

**错误消息**：始终使用通用消息，防止用户名枚举。

<a id="key-design-principles"></a>

#### 关键设计原则

1. **后端优先校验**：无效配置在启动时失败，而非运行时
2. **安全默认值**：`PHOENIX_DISABLE_BASIC_AUTH=true` 要求提供替代身份验证方式
3. **平滑降级**：前端适配可用身份验证方法
4. **禁止用户名枚举**：所有场景使用通用错误消息
5. **跨验证方式安全**：每种身份验证方法隔离，防止账户劫持

<a id="startup-admin-provisioning-phoenix_admins"></a>

#### 启动时配置管理员（`PHOENIX_ADMINS`）

配置 `PHOENIX_ADMINS` 后，Phoenix 会在启动时自动创建管理员用户（`facilitator.py:_ensure_admins`）：

| 条件 | 创建的用户类型 |
|-----------|-------------------|
| `PHOENIX_DISABLE_BASIC_AUTH=false` | `LocalUser`，使用随机密码，必须重置 |
| `PHOENIX_DISABLE_BASIC_AUTH=true` 且已配置 LDAP、未配置 OAuth2 | **LDAP 用户**（`oauth2_client_id=\ue000LDAP(stopgap)`、`oauth2_user_id=NULL`） |
| `PHOENIX_DISABLE_BASIC_AUTH=true` 且已配置 OAuth2 | `OAuth2User`，通用类型 |

**LDAP 启动管理员流程**：
```python
# facilitator.py creates LDAP admin at startup
user = models.OAuth2User(
    email=email,
    username=username,
    oauth2_client_id=LDAP_CLIENT_ID_MARKER,  # Identifies as LDAP
    oauth2_user_id=None,  # NULL until first login
)

# On first LDAP login (auth.py):
# 1. DN lookup fails (oauth2_user_id=NULL)
# 2. Email fallback finds user
# 3. Upgrades oauth2_user_id to DN
user.oauth2_user_id = user_dn  # Now DN-based lookup works
```

**配置示例**：
```bash
PHOENIX_ENABLE_AUTH=true
PHOENIX_DISABLE_BASIC_AUTH=true
PHOENIX_ADMINS="John Doe=john@example.com;Jane Smith=jane@example.com"
PHOENIX_LDAP_HOST=ldap.example.com
# ... other LDAP config
```
→ 启动时将 `john@example.com` 和 `jane@example.com` 创建为 LDAP 用户

<a id="common-deployment-scenarios"></a>

#### 常见部署场景

**场景 1：企业环境（LDAP + OAuth2）**
```bash
PHOENIX_ENABLE_AUTH=true
PHOENIX_DISABLE_BASIC_AUTH=true   # No password auth
PHOENIX_LDAP_HOST=ldap.corp.com
PHOENIX_OAUTH2_CLIENT_ID=...      # Google/Microsoft for external contractors
```
→ 登录页显示 LDAP 表单和 OAuth2 按钮

**场景 2：纯 LDAP 部署**
```bash
PHOENIX_ENABLE_AUTH=true
PHOENIX_DISABLE_BASIC_AUTH=true
PHOENIX_LDAP_HOST=ldap.corp.com
```
→ 登录页仅显示 LDAP 表单

**场景 3：所有方法可用（开发/测试）**
```bash
PHOENIX_ENABLE_AUTH=true
# PHOENIX_DISABLE_BASIC_AUTH not set (defaults to false)
PHOENIX_LDAP_HOST=ldap.corp.com
PHOENIX_OAUTH2_CLIENT_ID=...
```
→ 登录页显示 LOCAL + LDAP + OAuth2

**场景 4：禁用身份验证（本地开发）**
```bash
# PHOENIX_ENABLE_AUTH not set (defaults to false)
```
→ 无登录页，无需身份验证

<a id="testing-coverage"></a>

#### 测试覆盖

**后端校验**（`tests/unit/test_config.py`）：
- ✅ 接受有效配置
- ✅ 无效配置（禁用基本身份验证且无替代方式）抛出 `ValueError`
- ✅ LDAP 配置校验：主机、搜索基准和组映射

**前端渲染**（需要手动验证）：
- ✅ 为每种组合显示正确表单
- ✅ 分隔符位置正确
- ✅ 管理员对话框默认选项卡选择

**跨身份验证方式安全**（`tests/integration/auth/test_ldap.py`）：
- ✅ `test_ldap_user_cannot_login_via_oauth2`
- ✅ `test_ldap_login_rejected_when_oauth2_user_exists`

---

