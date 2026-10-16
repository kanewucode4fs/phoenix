<a id="optional-email-for-ldap-users"></a>

# LDAP 用户邮箱可选

<a id="problem-statement"></a>

## 问题说明

某些 LDAP 目录未为用户填充 `mail` 属性。当前 Phoenix 因数据库约束（`email VARCHAR NOT NULL`）而要求所有用户具有邮箱，导致 LDAP 中没有邮箱的组织无法使用 Phoenix LDAP 身份验证。

**用户需求：**在 `PHOENIX_LDAP_ATTR_EMAIL` 为空或属性不存在时支持 LDAP 身份验证。

<a id="constraints"></a>

## 约束

1. **数据库结构无法立即更改** — `email` 列具有 `NOT NULL` 约束和唯一索引
2. **代码库广泛使用邮箱** — UI 显示、欢迎邮件、密码重置和管理员检查
3. **必须保持用户查找完整性** — 需要稳定标识符识别回访用户

<a id="solution-overview"></a>

## 方案概览

<a id="two-phase-approach"></a>

### 两阶段方案

| 阶段 | 方案 | 时间 |
|-------|----------|----------|
| **阶段 1（过渡）** | 带 PUA 标记的占位邮箱 | 现在 |
| **阶段 2（最终）** | 允许 `email` 列为空 | 未来 |

过渡方案可立即支持无邮箱 LDAP，最终方案则提供更整洁的长期实现。

---

<a id="phase-1-bridge-solution-placeholder"></a>

## 阶段 1：过渡方案（占位值）

<a id="design"></a>

### 设计

`PHOENIX_LDAP_ATTR_EMAIL` 为空时，Phoenix 生成**占位值**，满足 `NOT NULL` 约束：

```python
from hashlib import md5

NULL_EMAIL_MARKER_PREFIX = "\ue000NULL(stopgap)"  # PUA character + "NULL" indicator


def generate_null_email_marker(unique_id: str) -> str:
    """Generate a deterministic placeholder from unique_id.

    Using MD5 hash ensures:
    - Same unique_id always produces the same placeholder
    - No race conditions on concurrent logins
    - Placeholder is stable across restarts

    Note: MD5 is fine here - we're not using it for security,
    just for deterministic uniqueness.
    """
    normalized = unique_id.lower()  # Case-insensitive (UUIDs are case-insensitive)
    return f"{NULL_EMAIL_MARKER_PREFIX}{md5(normalized.encode()).hexdigest()}"
    # Example: unique_id "550E8400-E29B-41D4-A716-446655440000"
    #       → "\ue000NULL(stopgap)7f3d2a1b9c8e4f5da2b6c903e1f47d8b"


def is_null_email_marker(email: str) -> bool:
    """Check if email is a placeholder."""
    return email.startswith(NULL_EMAIL_MARKER_PREFIX)
```

<a id="why-this-format"></a>

### 为什么采用此格式？

| 组成 | 用途 |
|-----------|---------|
| `\uE000`（PUA） | 不可见标记，供程序检测 |
| `NULL` | 人类可读，表示邮箱缺失 |
| `md5(unique_id)` | 确定性哈希，32 位十六进制字符，确保唯一性 |

<a id="why-hash-instead-of-random"></a>

### 为什么使用哈希而非随机值？

| 方案 | 优点 | 缺点 |
|----------|------|------|
| `token_hex(8)` | 简单 | 每次登录尝试产生不同占位值 |
| `md5(unique_id)` | **确定性**，无竞态条件 | 需要 unique_id，本身已必需 |

使用哈希意味着：
- **幂等创建** — 同一用户并发登录产生相同占位值
- **稳定查找** — 边界情况下可按占位邮箱查找
- **无意外重复** — 相同 unique_id 始终映射至相同占位值

<a id="configuration"></a>

### 配置

```bash
# LDAP with email (default)
PHOENIX_LDAP_ATTR_EMAIL=mail

# LDAP without email - generates placeholder
PHOENIX_LDAP_ATTR_EMAIL=
PHOENIX_LDAP_ATTR_UNIQUE_ID=objectGUID  # Required when email is empty
```

**校验规则：**`PHOENIX_LDAP_ATTR_EMAIL` 为空时，**必须**设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID`。

<a id="why-require-unique-id"></a>

### 为什么必须使用唯一 ID？

`unique_id` 有两个用途：

1. **用户查找** — 回访用户的主要标识符
2. **占位值生成** — 确定性占位邮箱的哈希输入

```python
# unique_id is used for both:
user = await _lookup_by_unique_id(session, unique_id)  # Lookup
placeholder = generate_null_email_marker(unique_id)  # Generation
```

没有 `unique_id`，既无内容可哈希，也无法识别回访用户。

<a id="implementation-changes"></a>

### 实现变更

<a id="1-configuration-srcphoenixconfigpy"></a>

#### 1. 配置（`src/phoenix/config.py`）

```python
# Allow empty attr_email
attr_email_raw = getenv(ENV_PHOENIX_LDAP_ATTR_EMAIL, "mail")
attr_email = attr_email_raw if attr_email_raw else None

# Validations when email is empty (placeholder mode)
if not attr_email:
    if not attr_unique_id:
        raise ValueError(
            "PHOENIX_LDAP_ATTR_UNIQUE_ID is required when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Without email, unique_id is needed to identify returning users."
        )
    if not allow_sign_up:
        raise ValueError(
            "PHOENIX_LDAP_ALLOW_SIGN_UP must be True when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Placeholder emails require auto-provisioning on first login."
        )
    if get_env_admins():
        raise ValueError(
            "PHOENIX_ADMINS is not supported when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Users are auto-provisioned on first login with roles from LDAP group mapping."
        )
```

<a id="2-ldapuserinfo-srcphoenixserverldappy"></a>

#### 2. LDAPUserInfo（`src/phoenix/server/ldap.py`）

```python
class LDAPUserInfo(NamedTuple):
    email: str | None  # None if PHOENIX_LDAP_ATTR_EMAIL is empty
    display_name: str
    groups: list[str]
    user_dn: str
    ldap_username: str
    role: str
    unique_id: str | None = None
```

<a id="3-authentication-srcphoenixserverldappy"></a>

#### 3. 身份验证（`src/phoenix/server/ldap.py`）

```python
# In _authenticate()
if self.config.attr_email:
    email = _get_attribute(user_entry, self.config.attr_email)
    if not email:
        # Fail loudly if attribute configured but missing
        raise LDAPConfigurationError(
            f"LDAP user '{username}' is missing required attribute "
            f"'{self.config.attr_email}'. Either populate this attribute "
            f"or set PHOENIX_LDAP_ATTR_EMAIL= (empty) to use placeholders."
        )
else:
    email = None  # Will generate placeholder in get_or_create_ldap_user

return LDAPUserInfo(email=email, ...)
```

<a id="4-user-creation-srcphoenixserverapiroutersldappy"></a>

#### 4. 用户创建（`src/phoenix/server/api/routers/ldap.py`）

```python
async def get_or_create_ldap_user(
    session: AsyncSession,
    user_info: LDAPUserInfo,
    ldap_config: LDAPConfig,
) -> models.User:
    unique_id = user_info.unique_id  # Required when email is None
    
    # Real email or None
    email = sanitize_email(user_info.email) if user_info.email else None
    
    # Step 1: Lookup by unique_id first (always, when configured)
    user = None
    if unique_id:
        user = await _lookup_by_unique_id(session, unique_id)
    
    # Step 2: Fallback to email lookup (only for real emails)
    if not user and email:
        user = await _lookup_by_email(session, email)
        if user:
            # Migration logic for unique_id (existing code)
            ...
    
    # Step 3: Return existing user (update email if changed)
    if user:
        if email and user.email != email:
            user.email = email  # Sync email (works for both null marker → real and real → real)
        return user
    
    # Step 4: Create new user
    if not ldap_config.allow_sign_up:
        raise HTTPException(401, "Invalid username and/or password")
    
    # Use real email or generate deterministic placeholder
    db_email = email if email else generate_null_email_marker(unique_id)
    
    user = models.User(
        email=db_email,
        username=...,
        oauth2_client_id=LDAP_CLIENT_ID_MARKER,
        oauth2_user_id=unique_id,
        ...
    )
    session.add(user)
    return user
```

<a id="5-email-sending-srcphoenixserveremailsenderpy"></a>

#### 5. 邮件发送（`src/phoenix/server/email/sender.py`）

邮件发送自然处理空邮箱标记，无需显式检查。`email_validator` 库在发送前校验邮箱格式，而空邮箱标记不含 `@` 符号，因此无法通过校验：

```python
async def send_welcome_email(self, email: str, name: str) -> None:
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        logger.warning("Skipping welcome email for user with invalid email address")
        return
    # ... existing logic ...


async def send_password_reset_email(self, email: str, reset_url: str) -> None:
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        logger.warning("Skipping password reset email for user with invalid email address")
        return
    # ... existing logic ...
```

此方式优于显式 `is_null_email_marker()` 检查，因为：
- 处理所有无效邮箱，而不仅是空值标记
- 发送前本就需要邮箱校验
- 无额外导入，不与 LDAP 专用代码耦合

<a id="6-graphql-layer-srcphoenixserverapitypesuserpy"></a>

#### 6. GraphQL 层（`src/phoenix/server/api/types/User.py`）

GraphQL 解析器在 API 边界过滤空邮箱标记，返回 `None`，即 GraphQL `null`：

```python
from phoenix.server.ldap import is_null_email_marker


@strawberry.field
async def email(self, info: Info[Context, None]) -> str | None:
    # ... fetch email from database ...
    if is_null_email_marker(val):
        return None
    return val
```

这样将占位值检测逻辑保留在后端，前端永远看不到标记格式。GraphQL schema 声明 `email: String`，允许为空。

<a id="6b-rest-api-layer-srcphoenixserverapiroutersv1userspy"></a>

#### 6b. REST API 层（`src/phoenix/server/api/routers/v1/users.py`）

REST API 返回空字符串 `""` 而非 `null`，以保持与现有 API 使用方的向后兼容：

```python
from phoenix.server.ldap import is_null_email_marker

# In list_users endpoint
email = ("" if is_null_email_marker(user.email) else user.email,)
```

**为何返回 `""` 而非 `null`？**
- REST API 已有契约，`email` 始终是字符串
- 改为 `null` 可能破坏预期字符串类型的现有集成
- 大多数语言中空字符串为假值，使用方可检查真假值
- GraphQL 可使用 `null`，因为 schema 变化（`String!` → `String`）是显式的

<a id="7-frontend"></a>

#### 7. 前端

**服务器向 window 对象注入配置：**

```tsx
declare global {
  interface Window {
    Config: {
      ldapManualUserCreationEnabled: boolean;  // false when PHOENIX_LDAP_ATTR_EMAIL is empty
      // ... other config
    };
  }
}
```

> **说明：**前端配置无需 `nullEmailMarkerPrefix`。后端 GraphQL 层为空邮箱标记返回 `null`，前端只需检查邮箱是否为真值。

<a id="8-ui-components"></a>

#### 8. UI 组件

**前端邮箱使用情况完整调查：**

| 文件 | 当前用途 | 所需变更 |
|------|---------------|---------------|
| `UsersCard.tsx` | “Add User”按钮 | 没有可用用户创建方法时禁用 |
| `UsersTable.tsx` | 以 mailto 链接显示邮箱 | 邮箱为空时隐藏 |
| `ViewerProfileCard.tsx` | 在个人资料卡片显示邮箱 | 邮箱为空时隐藏 |
| `UserAPIKeysTable.tsx` | 在表格显示用户邮箱 | 改为显示用户名 |
| `LDAPUserForm.tsx` | 创建 LDAP 用户的邮箱输入 | 无需变更，仅在 `ldapManualUserCreationEnabled=true` 时渲染 |
| `NewUserDialog.tsx` | 使用邮箱创建用户 | `ldapManualUserCreationEnabled=false` 时隐藏 LDAP 选项 |
| `UserForm.tsx` | 本地用户邮箱输入 | 无需变更，本地用户有真实邮箱 |
| `OAuthUserForm.tsx` | OAuth 用户邮箱输入 | 无需变更，OAuth 用户有真实邮箱 |
| `LoginForm.tsx` | 本地身份验证登录邮箱 | 无需变更，服务端拒绝占位值 |
| `ForgotPasswordForm.tsx` | 密码重置邮箱 | 无需变更，LDAP 用户不使用密码重置 |

**UsersCard.tsx:**
```tsx
// Disable "Add User" button only when no user creation method is available:
// - Basic auth disabled (can't create password users) AND
// - LDAP not enabled AND
// - Manual LDAP user creation not enabled
const isDisabled = useMemo(() => {
  // Disable when no user creation method is available:
  // - Basic auth is disabled AND
  // - No OAuth2 IDPs configured AND
  // - LDAP manual user creation is disabled
  return (
    window.Config.basicAuthDisabled &&
    !window.Config.oAuth2Idps.length &&
    !window.Config.ldapManualUserCreationEnabled
  );
}, []);

// Button is ENABLED when ANY of:
// - Basic auth is enabled (can create users with passwords)
// - LDAP is enabled
// - Manual LDAP user creation is enabled
```

**UsersTable.tsx:**
```tsx
// In the cell renderer - hide null/empty emails (GraphQL returns null for null email markers)
{row.original.email && (
  <a href={`mailto:${row.original.email}`}>
    {row.original.email}
  </a>
)}
```

**ViewerProfileCard.tsx:**
```tsx
// Hide email field when null (GraphQL returns null for null email markers)
{viewer.email && (
  <TextField value={viewer.email} isReadOnly size="S">
    <Label>Email</Label>
    <Input />
  </TextField>
)}
```

**NewUserDialog.tsx:**
```tsx
// Hide "LDAP" auth method option when manual LDAP user creation is disabled
// (because we can't know the email or unique_id ahead of time)
{window.Config.ldapManualUserCreationEnabled && (
  <Item key="LDAP">LDAP</Item>
)}
```

**LDAPUserForm.tsx:**

此组件无需变更。仅在 `ldapManualUserCreationEnabled=true` 时渲染表单，由 `NewUserDialog.tsx` 控制。父组件条件渲染已提供足够保护。

<a id="behavior-summary"></a>

### 行为汇总

| 场景 | `ATTR_EMAIL` | `ATTR_UNIQUE_ID` | 数据库邮箱 | 查找策略 |
|----------|--------------|------------------|-------------|-----------------|
| 标准 LDAP | `mail` | *可选* | 真实邮箱 | 先 unique_id，后邮箱 |
| 企业 LDAP | `mail` | `objectGUID` | 真实邮箱 | 先 unique_id，后邮箱 |
| 无邮箱 LDAP | *空* | `objectGUID` | 占位值 | 仅按 unique_id |

<a id="edge-cases-and-considerations"></a>

### 边界情况与考虑

<a id="1-case-normalization-of-unique-id"></a>

#### 1. 唯一 ID 大小写规范化

UUID 可能采用不同大小写。**哈希前先规范化为小写**，确保占位值一致：

```python
def generate_null_email_marker(unique_id: str) -> str:
    normalized = unique_id.lower()  # Normalize case
    return f"{NULL_EMAIL_MARKER_PREFIX}{md5(normalized.encode()).hexdigest()}"
```

<a id="2-configuration-changes-mid-flight"></a>

#### 2. 运行期间变更配置

| 场景 | 行为 |
|----------|----------|
| 从 `ATTR_EMAIL=mail` 切换为 `ATTR_EMAIL=` | 已有用户保留真实邮箱，新用户使用占位值。 |
| 从 `ATTR_EMAIL=` 切换为 `ATTR_EMAIL=mail` | 下次登录时，**占位值更新为真实邮箱**。 |
| 用户已有占位值，LDAP 现在有邮箱 | 更新为真实邮箱，始终允许占位值升级为真实邮箱。 |

**代码自然处理此情况：**

```python
if user:
    if email and user.email != email:
        user.email = email  # Works for both: null marker → real, and real → real
    return user
```

无需显式 `is_null_email_marker()` 检查；空值标记字符串永远不等于真实邮箱字符串，因此 `user.email != email` 可处理升级和同步两种情况。

<a id="3-admin-pre-provisioning-phoenix_admins"></a>

#### 3. 管理员预配置（`PHOENIX_ADMINS`）

**当前流程（真实邮箱）：**
1. 管理员设置 `PHOENIX_ADMINS=alice=alice@corp.com`
2. Facilitator 创建 `LDAPUser(email="alice@corp.com", username="alice", unique_id=None)`
3. 首次登录：按 unique_id 查找未找到 → 回退邮箱 → 匹配成功 → 填充 unique_id

**占位邮箱的问题：**
- 管理员无法提供真实邮箱，LDAP 中不存在
- 管理员无法生成占位值，因为事先不知道 `unique_id`
- 无法按邮箱预配置

**选项：**

| 选项 | 方案 | 复杂度 | 取舍 |
|--------|----------|------------|-----------|
| **A. 禁止** | `PHOENIX_ADMINS` 与占位模式同时使用时启动失败 | 低 | 用户首次登录从 LDAP 组映射获取角色 |
| **B. 用户名匹配** | 按用户名预配置，首次登录时匹配 | 中 | 用户名冲突风险 |
| **C. 唯一 ID 格式** | 占位模式使用 `PHOENIX_ADMINS=username=unique_id` | 中 | 管理员需先查询 LDAP |

**阶段 1 建议：选项 A（禁止）**

```python
# In config validation
if not attr_email:  # Placeholder mode
    if get_env_admins():
        raise ValueError(
            "PHOENIX_ADMINS is not supported when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Users are auto-provisioned on first login with roles from LDAP group mapping."
        )
```

**依据：**
- 初始实现最简单、安全
- 占位模式已要求自动配置（`allow_sign_up=True`）
- LDAP 角色映射根据组成员关系自动分配角色，包括 ADMIN

<a id="4-allow_sign_upfalse-is-disallowed-phase-1"></a>

#### 4. 阶段 1 不允许 `ALLOW_SIGN_UP=False`

`PHOENIX_LDAP_ATTR_EMAIL` 为空（占位模式）时，阶段 1 **不允许** `PHOENIX_LDAP_ALLOW_SIGN_UP=False`，启动时强制校验：

```python
def validate_ldap_config():
    if not PHOENIX_LDAP_ATTR_EMAIL and not ldap_config.allow_sign_up:
        raise LDAPConfigurationError(
            "PHOENIX_LDAP_ALLOW_SIGN_UP must be True when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Placeholder emails require auto-provisioning on first login."
        )
```

**依据：**
- 占位邮箱在首次登录时根据 `unique_id` 生成
- 不知道 `unique_id` 时预配置用户不现实
- 自动配置是 LDAP 身份验证的自然流程

<a id="future-supporting-allow_sign_upfalse"></a>

##### 未来：支持 `ALLOW_SIGN_UP=False`

某些组织要求明确配置用户，不允许自动注册。未来可通过以下方案支持：

> **说明：**本节讨论应获得 Phoenix 访问权的**普通用户预配置**。无邮箱模式的**管理员角色分配**使用 `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS`，而非 `PHOENIX_ADMINS`。组角色映射在登录时根据 LDAP 组成员关系分配角色，包括 ADMIN。

**方案 1：基于唯一 ID 预配置**

**概念：**管理员查询用户的 `unique_id`，用计算出的占位值预配置。

```bash
# New format when placeholder mode
PHOENIX_ADMINS=alice:550E8400-E29B-41D4-A716-446655440000;bob:7C9E6679-7425-40DE-944B-E07FC1F90AE7
#             ^username:unique_id
```

**实现：**
```python
def parse_admins_placeholder_mode(env_value: str) -> dict[str, str]:
    """Parse username:unique_id pairs, return {placeholder_email: username}."""
    result = {}
    for pair in env_value.split(";"):
        username, unique_id = pair.strip().split(":")
        placeholder = generate_null_email_marker(unique_id)
        result[placeholder] = username
    return result
```

**首次登录流程：**
1. 用户通过 LDAP 身份验证
2. 按 unique_id 查找，找到预配置用户；其占位邮箱由相同 unique_id 派生并匹配
3. 登录成功

**优点：**
- 确定性，相同 unique_id 始终生成相同占位值
- 没有用户名冲突风险
- 管理员完全控制谁能访问

**缺点：**
- 管理员必须查询 LDAP 获取 unique_id，增加步骤
- unique_id 格式不同，例如 GUID、UUID 或字符串

**管理员工作流：**
```bash
# Query LDAP for user's objectGUID
ldapsearch -H ldap://dc.corp.com -b "dc=corp,dc=com" "(sAMAccountName=alice)" objectGUID

# Set env var with result
PHOENIX_ADMINS=alice:550e8400-e29b-41d4-a716-446655440000
```

**方案 2：带冲突预防的用户名匹配**

**概念：**仅按用户名预配置，首次登录按用户名匹配。

```bash
# Username-only format
PHOENIX_ADMINS=alice;bob;charlie
```

**实现：**
```python
def pre_provision_ldap_user_by_username(username: str) -> models.User:
    """Create LDAP user with temporary placeholder, no unique_id."""
    temp_placeholder = (
        f"{NULL_EMAIL_MARKER_PREFIX}PREPROV_{md5(username.lower().encode()).hexdigest()}"
    )
    return models.LDAPUser(
        email=temp_placeholder,
        username=username,
        unique_id=None,  # Will be populated on first login
    )
```

**首次登录流程：**
1. 用户通过 LDAP 身份验证，username=alice、unique_id=UUID-A
2. 按 unique_id 查找，未找到
3. 按邮箱，即 unique_id 派生占位值查找，未找到
4. **新增：**在没有 unique_id 的 LDAP 用户中按用户名查找，找到！
5. 校验：用户为 LDAP 用户且没有 unique_id，表示已预配置
6. 更新：设置 unique_id，将临时占位值替换为真实占位值
7. 登录成功

```python
# In get_or_create_ldap_user
if not user and not ldap_config.allow_sign_up:
    # Try username match for pre-provisioned users
    user = await session.scalar(
        select(models.User)
        .where(models.User.username == user_info.display_name)
        .where(models.User.oauth2_client_id == LDAP_CLIENT_ID_MARKER)
        .where(models.User.oauth2_user_id.is_(None))  # No unique_id = pre-provisioned
    )
    if user:
        # Claim this pre-provisioned user
        user.oauth2_user_id = unique_id
        user.email = generate_null_email_marker(unique_id)
```

**优点：**
- 管理员工作流简单，仅需用户名
- 无需查询 LDAP 获取 unique_id

**缺点：**
- displayName 与 sAMAccountName 不同时，存在用户名冲突风险
- 同名用户同时首次登录会产生竞态条件
- 安全性：按用户名匹配弱于按 unique_id 匹配

**防护：**
- 仅匹配预配置用户，oauth2_user_id IS NULL
- 用户名匹配发生时记录警告
- 考虑要求精确用户名匹配，区分大小写

**方案 3：带 LDAP 查询的管理员 API**

**概念：**管理员 API 直接查询 LDAP 以配置用户。

```
POST /api/v1/admin/ldap/provision
{
  "username": "alice",
  "role": "ADMIN"
}
```

**服务端流程：**
1. API 使用服务账户向 LDAP 身份验证
2. 按用户名查询 LDAP
3. 从 LDAP 响应获取 unique_id
4. 使用计算出的占位邮箱创建用户
5. 返回创建的用户

**优点：**
- 管理员体验最佳，仅需提供用户名
- 服务器处理 LDAP 查询，无需手动复制 unique_id
- 完整校验，用户必须存在于 LDAP

**缺点：**
- 需要具有读取权限的 LDAP 服务账户
- API 实现更复杂
- 配置时依赖 LDAP 网络

**比较矩阵**

| 方面 | 方案 1：唯一 ID | 方案 2：用户名 | 方案 3：管理员 API |
|--------|---------------------|--------------------|--------------------|
| 管理员工作量 | 高，查询 LDAP | 低，仅需用户名 | 低，API 调用 |
| 实现 | 低 | 中 | 高 |
| 安全性 | 高 | 中 | 高 |
| LDAP 依赖 | 管理员操作时 | 无 | 配置时 |
| 冲突风险 | 无 | 用户名冲突 | 无 |
| 兼容阶段 1 | 是 | 是 | 否，需要新 API |

**未来建议**

**短期（如近期需要）：**方案 1，基于唯一 ID
- 可添加至现有 `PHOENIX_ADMINS` 解析
- 无需新 API
- 安全性最高

**长期：**方案 3，管理员 API
- 管理员体验最佳
- 与 LDAP 完整校验
- 可结合“从 LDAP 配置”UI 按钮

<a id="5-search-and-filtering"></a>

#### 5. 搜索与过滤

- 按邮箱搜索用户**不会找到**使用占位值的用户
- 可以接受，因为占位邮箱没有意义
- 考虑在 UI 添加“无邮箱用户”过滤器

<a id="6-exportimport"></a>

#### 6. 导出与导入

导出用户时，例如 CSV：
- GraphQL API 为空邮箱标记返回 `null`，因此 API 导出显示空或 null 邮箱
- REST API 为空邮箱标记返回空字符串 `""`，避免破坏现有 API 契约
- 直接数据库导出会显示原始占位值（`\ue000NULL(stopgap)...`）
- 通过 API 导入时，邮箱校验会拒绝空邮箱标记格式，因为没有 `@` 符号

<a id="7-md5-collision-risk"></a>

#### 7. MD5 冲突风险

- MD5 生成 128 位哈希
- 对同为 128 位的 UUID，生日攻击冲突概率约为 2^64 分之一
- 数千用户规模下，冲突概率极低
- 若真的发生，邮箱唯一约束会在插入时捕获

<a id="8-audit-logs"></a>

#### 8. 审计日志

- 不记录占位邮箱，它们只是噪声
- LDAP 用户改为记录 `username` 和 `unique_id`

<a id="security-considerations"></a>

### 安全考虑

<a id="1-unique-id-is-mandatory"></a>

#### 1. 唯一 ID 必填

占位邮箱需要 `unique_id` 进行确定性生成和用户查找，启动时强制校验。

<a id="2-pua-character-safety"></a>

#### 2. PUA 字符安全

- `\uE000` 是有效 Unicode 字符，在 PostgreSQL UTF-8 中安全
- 不会与真实邮箱冲突，有效邮箱不会以 PUA 开头
- 某些外部系统如日志、导出可能剥离它，需使用辅助函数

<a id="3-no-email-operations"></a>

#### 3. 不支持邮件操作

使用占位邮箱的用户无法：
- 接收欢迎邮件
- 使用密码重置，LDAP 用户本来就不需要
- 通过邮箱被联系

<a id="4-login-and-api-endpoints-naturally-reject-null-email-markers"></a>

#### 4. 登录和 API 端点自然拒绝空邮箱标记

**风险：**用户尝试使用空邮箱标记登录或创建账户。

**防护：**无需显式检查。标准邮箱校验正则（`EMAIL_PATTERN`）要求存在 `@` 符号：

```python
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+[.][^@\s]+\Z")
```

空邮箱标记（`\ue000NULL(stopgap)abc123...`）不含 `@` 符号，因此会被现有邮箱格式校验自动拒绝，适用于：
- 本地登录端点，邮箱/密码身份验证
- REST API 用户创建（`POST /v1/users`）
- GraphQL 用户创建（`createUser` 变更）

LDAP 用户通过 LDAP 绑定身份验证，而非邮箱/密码，因此本地登录拒绝仅属于纵深防御。

<a id="5-md5-hash-does-not-reveal-unique-id"></a>

#### 5. MD5 哈希不暴露唯一 ID

- MD5 是单向哈希，无法逆向获得 unique_id
- 但若攻击者**知道**用户 unique_id，例如能访问 LDAP，便可计算预期占位邮箱，确认用户是否存在于 Phoenix
- **风险级别：**低，unique_id 通常不是秘密，且仅确认存在性

<a id="6-malicious-ldap-email-injection"></a>

#### 6. 恶意 LDAP 邮箱注入

**风险：**LDAP 管理员将用户邮箱设为以 `\uE000` 开头，使其看似占位值。

**影响：**
- 用户邮箱在 UI 隐藏，被视为占位值
- 用户无法接收 Phoenix 邮件

**风险级别：**低，需要 LDAP 管理员权限，影响限于用户体验

<a id="7-pua-stripping-attack"></a>

#### 7. PUA 剥离攻击

**风险：**系统在直接数据库导出或导入时剥离 PUA 字符：
- `\ue000NULL(stopgap)7f3d...` 变成 `NULL7f3d...`
- 可能作为“真实”邮箱被导入

**防护：**
- GraphQL API 对占位值导出空字符串，PUA 从不暴露给前端
- 直接数据库导入应校验邮箱格式，拒绝以“NULL”加十六进制开头的字符串
- 标准邮箱校验拒绝两种格式，因为均无 `@` 符号

<a id="8-api-user-creation-security"></a>

#### 8. API 用户创建安全

**风险：**管理员不知道 unique_id，却通过 API 创建 LDAP 用户。

**场景：**
1. 管理员提供真实邮箱 → 原样存储
2. 管理员未提供邮箱 → 必须失败或使用临时占位值

**建议：**对于通过 API 创建、没有邮箱的 LDAP 用户：
- 方案 A：要求邮箱，管理员必须知道
- 方案 B：生成临时随机占位值，在首次 LDAP 登录时替换
- 方案 C：创建时要求 unique_id

当前建议：**方案 A**，最简单，避免临时占位值的复杂度。

<a id="9-multi-ldap-server-collision-future"></a>

#### 9. 多 LDAP 服务器冲突（未来）

**风险：**若 Phoenix 支持多个 LDAP 服务器，不同服务器的相同 unique_id 会生成相同占位邮箱。

**防护（未来）：**在哈希中包含服务器标识符：

```python
def generate_null_email_marker(unique_id: str, server_id: str) -> str:
    normalized = f"{server_id}:{unique_id}".lower()
    return f"{NULL_EMAIL_MARKER_PREFIX}{md5(normalized.encode()).hexdigest()}"
```

<a id="10-timing-attack-on-user-existence"></a>

#### 10. 用户存在性时序攻击

**风险：**攻击者通过测量响应时间差异探测用户是否存在。

**分析：**
- 占位邮箱检查为 `O(1)` 字符串前缀比较
- 占位值和真实邮箱采用相同代码路径
- 不会引入额外时序泄漏

**风险级别：**无，没有新增攻击面

---

<a id="phase-2-eventual-solution-nullable-email"></a>

## 阶段 2：最终方案（邮箱可为空）

<a id="database-migration"></a>

### 数据库迁移

```sql
-- Step 1: Allow NULL
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

-- Step 2: Partial unique index (NULLs are allowed, non-NULLs must be unique)
DROP INDEX ix_users_email;
CREATE UNIQUE INDEX ix_users_email ON users (email) WHERE email IS NOT NULL;

-- Step 3: Migrate placeholders to NULL
UPDATE users SET email = NULL WHERE email LIKE E'\uE000%';
```

<a id="code-changes"></a>

### 代码变更

1. **模型：**`email: Mapped[Optional[str]]`
2. **GraphQL：**`email: Optional[str]`，移除 `is_null_email_marker()` 检查，直接返回 `None`
3. **REST API：**`email: Optional[str] = None`
4. **前端：**处理 `null` 而非空字符串，变化很小，两者均为假值
5. **移除：**后端 `is_null_email_marker()` 辅助函数，不再需要

<a id="effort-estimate"></a>

### 工作量估计

| 任务 | 工作量 |
|------|--------|
| 数据库迁移 | 1 天 |
| 后端类型变更 | 2 小时 |
| 前端空值处理 | 4 小时 |
| 测试 | 4 小时 |
| **合计** | **2—3 天** |

---

<a id="migration-path"></a>

## 迁移路径

```
┌─────────────────────────────────────────────────────────────────┐
│                         Current State                           │
│  email: NOT NULL, all users have email                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: Bridge Solution                     │
│  - LDAP users without email get placeholder in DB               │
│  - DB email: "\ue000NULL(stopgap){md5_hash}"                             │
│  - GraphQL returns null for placeholders (UI checks truthiness) │
│  - Email operations skipped for placeholder                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (Future)
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 2: Eventual Solution                   │
│  - email column becomes nullable                                │
│  - Placeholder emails migrated to NULL                          │
│  - Clean, honest representation                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

<a id="implementation-checklist"></a>

## 实现检查清单

<a id="phase-1-bridge"></a>

### 阶段 1（过渡）

- [x] 添加 `NULL_EMAIL_MARKER_PREFIX` 常量
- [x] 添加 `generate_null_email_marker()` 函数
- [x] 添加 `is_null_email_marker()` 辅助函数
- [x] 更新 `LDAPConfig` 校验：
  - [x] `email` 为空时要求 `unique_id`
  - [x] `email` 为空时要求 `allow_sign_up=True`
  - [x] `email` 为空时禁止 `PHOENIX_ADMINS`
- [x] 将 `LDAPUserInfo.email` 类型更新为 `str | None`
- [x] 更新 `_authenticate()` 以处理缺失邮箱属性
- [x] 更新 `get_or_create_ldap_user()` 以生成占位值
- [x] 更新 GraphQL `User.email` 解析器，为空邮箱标记返回 `None`
- [x] 向 `window.Config` 注入 `ldapManualUserCreationEnabled`
- [x] 更新 `UsersCard.tsx`，没有创建方法时禁用“Add User”按钮
- [x] 更新 `UsersTable.tsx`，隐藏空邮箱
- [x] 更新 `ViewerProfileCard.tsx`，隐藏空邮箱
- [x] 更新 `UserAPIKeysTable.tsx`，显示用户名而非邮箱
- [x] 更新 `NewUserDialog.tsx`，禁用手动创建时隐藏 LDAP 选项
- [x] 邮件发送器自然跳过占位邮箱，通过邮箱校验实现
- [x] 验证邮箱校验拒绝空值标记，由 EMAIL_PATTERN 处理，因无 `@` 符号
- [x] 为空邮箱标记辅助函数添加单元测试
- [x] 为无邮箱 LDAP 添加集成测试
- [x] 更新文档

<a id="phase-2-future"></a>

### 阶段 2（未来）

- [ ] 创建数据库迁移
- [ ] 更新 SQLAlchemy 模型
- [ ] 更新 REST API 模型
- [ ] 移除后端 `is_null_email_marker()` 辅助函数
- [ ] 将已有占位邮箱迁移为 `NULL`
- [ ] 更新测试

---

<a id="references"></a>

## 参考资料

- [用户识别策略](./user-identification-strategy.md) — Phoenix 如何识别 LDAP 用户
- [README](./README.md) — LDAP 身份验证概览
