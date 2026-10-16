<a id="ldap-user-identification-strategy"></a>

# LDAP 用户识别策略

<a id="overview"></a>

## 概述

Phoenix 使用稳定标识符识别 LDAP 用户，具体策略取决于配置：

| 模式 | 标识符 | `oauth2_user_id` | 可应对的变化 |
|------|------------|------------------|----------|
| **简单模式**（默认） | 邮箱 | `NULL` | DN 变化、OU 移动、重命名 |
| **企业模式** | 唯一 ID（objectGUID/entryUUID） | UUID 字符串 | 包括邮箱变化在内的所有变化 |

<a id="which-mode-should-i-use"></a>

## 应选择哪种模式？

大多数部署**使用简单模式（默认）**：
- ✅ 无需额外配置
- ✅ 可处理 DN 变化、OU 移动和重命名
- ✅ 大多数组织的邮箱稳定
- ⚠️ LDAP 邮箱变化时，用户会获得新 Phoenix 账户，管理员可合并

**仅在预期用户邮箱变化时使用企业模式**：
- 公司品牌调整（oldcorp.com → newcorp.com）
- 组织中经常发生姓名变化
- 并购时迁移邮箱域
- 合规要求不可变用户追踪

**两者差异很小**：均能处理 DN 变化。企业模式的唯一额外收益，是在**邮箱变化**时不产生重复账户。

<a id="why-not-dn"></a>

## 为什么不使用 DN？

曾考虑将 DN（专有名称）作为标识符，但最终否决：

| 问题 | 频率 | 影响 |
|-------|-----------|--------|
| OU 重组 | 常见，每季度或每年 | 用户无法登录 |
| 域整合 | 偶尔，例如并购 | 大量用户无法登录 |
| 用户重命名 | 偶尔 | 用户无法登录 |
| DN 大小写差异 | 多 DC 的 AD | 重复账户 |

企业环境中 **DN 变化过于频繁**。组织调整是常规事项，每次变更都会使用户失联或需要管理员介入。

<a id="simple-mode-default"></a>

## 简单模式（默认）

未设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID` 时：

```
oauth2_user_id = NULL
Lookup: By email column (case-insensitive)
```

**行为：**

| 场景 | 行为 |
|----------|----------|
| DN 变化，OU 移动或重命名 | ✅ 按邮箱找到用户 |
| 邮箱不变 | ✅ 正常登录 |
| LDAP 邮箱变化 | ⚠️ 创建新账户，需要管理员介入 |

**实现：**

```python
# Simple mode: lookup by email only
user = await session.scalar(
    select(User)
    .where(User.oauth2_client_id == LDAP_CLIENT_ID_MARKER)
    .where(func.lower(User.email) == email.lower())
)

# New user creation
user = User(
    email=email,
    oauth2_client_id=LDAP_CLIENT_ID_MARKER,
    oauth2_user_id=None,  # Not used in simple mode
    ...
)
```

**邮箱适用于大多数组织的原因：**
- 单个用户邮箱很少变化
- 品牌调整、合并等邮箱变化通常是计划事件
- 必要时管理员可合并账户

<a id="enterprise-mode-unique-id"></a>

## 企业模式（唯一 ID）

设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID`（例如 `objectGUID`、`entryUUID`）时：

```
oauth2_user_id = <immutable unique ID from LDAP, lowercase normalized>
Lookup: By oauth2_user_id (case-insensitive), fallback to email for migration
```

**配置：**

```bash
# Active Directory
PHOENIX_LDAP_ATTR_UNIQUE_ID=objectGUID

# OpenLDAP (RFC 4530)
PHOENIX_LDAP_ATTR_UNIQUE_ID=entryUUID

# 389 Directory Server
PHOENIX_LDAP_ATTR_UNIQUE_ID=nsUniqueId
```

<a id="email-attribute-configuration"></a>

## 邮箱属性配置

`PHOENIX_LDAP_ATTR_EMAIL` 设置是**可选的**。Phoenix 有两种邮箱处理方式：

| 配置 | 行为 |
|---------------|----------|
| `PHOENIX_LDAP_ATTR_EMAIL=mail`（默认） | 从 `mail` 属性读取邮箱，缺失时失败 |
| `PHOENIX_LDAP_ATTR_EMAIL=`（空） | 根据 unique_id 生成占位邮箱，要求设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID` |

```bash
# Default: read from mail attribute
PHOENIX_LDAP_ATTR_EMAIL=mail

# No email attribute available - generate placeholder (requires unique_id)
PHOENIX_LDAP_ATTR_EMAIL=
PHOENIX_LDAP_ATTR_UNIQUE_ID=objectGUID
# → User gets placeholder like "\ue000NULL(stopgap)7f3d2a1b9c8e4f5d"
```

| 环境变量 | 默认值 | 说明 |
|---------------------|---------|-------------|
| `PHOENIX_LDAP_ATTR_EMAIL` | `mail` | 用于读取邮箱的 LDAP 属性。设为空字符串时生成占位邮箱。 |

**约束：**若 `PHOENIX_LDAP_ATTR_EMAIL` 为空，**必须**设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID`，以防止用户名回收攻击，参见[安全考虑](#security-considerations-for-placeholder-emails)。

**邮箱解析逻辑：**

```
1. If PHOENIX_LDAP_ATTR_EMAIL is set and not empty:
   a. Read value from that LDAP attribute
   b. If attribute is missing or empty → ERROR (fail loudly)
   c. If value contains "@" → use as real email
   d. If value has no "@" → ERROR (expected email-like value)

2. If PHOENIX_LDAP_ATTR_EMAIL is empty:
   a. PHOENIX_LDAP_ATTR_UNIQUE_ID must be set → ERROR if not
   b. Generate placeholder: "{marker}{md5(unique_id)}"
```

**占位邮箱格式：**

```python
from hashlib import md5

NULL_EMAIL_MARKER_PREFIX = "\ue000NULL(stopgap)"  # PUA character + "None" indicator


def generate_null_email_marker(unique_id: str) -> str:
    """Generate a deterministic placeholder from unique_id."""
    normalized = unique_id.lower()  # Case-insensitive (UUIDs are case-insensitive)
    return f"{NULL_EMAIL_MARKER_PREFIX}{md5(normalized.encode()).hexdigest()}"
    # Example: "\ue000NULL(stopgap)7f3d2a1b9c8e4f5da2b6c903e1f47d8b"
```

占位值：
- 以 PUA 标记（`\uE000`）开头，便于程序检测
- 包含 `NULL`，表示没有真实邮箱
- 以 unique_id 的 MD5 哈希结尾，实现确定性唯一，满足唯一约束

**属性缺失时快速失败：**

若管理员明确配置 `PHOENIX_LDAP_ATTR_EMAIL=mail`，但用户 `mail` 属性缺失或为空，Phoenix 会**使登录失败并给出清晰错误**：

```python
from hashlib import md5

NULL_EMAIL_MARKER_PREFIX = "\ue000NULL(stopgap)"


def validate_ldap_config():
    """Validate LDAP configuration at startup."""
    if not settings.PHOENIX_LDAP_ATTR_EMAIL and not settings.PHOENIX_LDAP_ATTR_UNIQUE_ID:
        raise LDAPConfigurationError(
            "PHOENIX_LDAP_ATTR_UNIQUE_ID is required when PHOENIX_LDAP_ATTR_EMAIL is empty. "
            "Placeholder emails require unique_id to identify returning users."
        )


def generate_null_email_marker(unique_id: str) -> str:
    """Generate a deterministic placeholder from unique_id."""
    normalized = unique_id.lower()
    return f"{NULL_EMAIL_MARKER_PREFIX}{md5(normalized.encode()).hexdigest()}"


def get_email_from_ldap(ldap_user, username, unique_id: str):
    attr_name = settings.PHOENIX_LDAP_ATTR_EMAIL

    if attr_name:  # Explicit attribute configured
        value = ldap_user.get(attr_name)
        if not value:
            # FAIL LOUDLY - admin configured this attribute, it should exist
            raise LDAPConfigurationError(
                f"LDAP user '{username}' is missing required attribute '{attr_name}'. "
                f"Either populate this attribute in LDAP, or set PHOENIX_LDAP_ATTR_EMAIL= "
                f"(empty) to generate placeholders."
            )
        if "@" not in value:
            raise LDAPConfigurationError(
                f"LDAP attribute '{attr_name}' for user '{username}' does not contain '@'. "
                f"Expected an email address, got: '{value}'"
            )
        return value  # Real email
    else:  # No attribute configured - generate deterministic placeholder from unique_id
        return generate_null_email_marker(unique_id)
```

**为什么明确报错？**

| 场景 | 行为 | 原因 |
|----------|----------|-----------|
| `ATTR_EMAIL=mail`，用户具有 `mail` | ✅ 使用该值 | 按配置工作 |
| `ATTR_EMAIL=mail`，用户缺少 `mail` | ❌ **错误** | 配置问题，管理员预期存在该属性 |
| `ATTR_EMAIL=`（空） | ✅ 生成占位值 | 明确选择使用占位邮箱 |

静默回退会掩盖 LDAP 数据质量问题，导致用户状态不一致。

| `ATTR_EMAIL` | 属性值 | 最终邮箱 |
|--------------|-----------------|-----------------|
| `mail` | `alice@corp.com` | `alice@corp.com`，真实邮箱 |
| `mail` | *缺失* | ❌ **错误** |
| `mail` | `alice`，没有 @ | ❌ **错误** |
| *空* | *不读取* | `\ue000NULL(stopgap){md5_hash}`，占位值 |

**常见配置：**

```bash
# LDAP with mail attribute populated (default)
PHOENIX_LDAP_ATTR_EMAIL=mail

# No email in LDAP - generate placeholder from unique_id (unique_id REQUIRED)
PHOENIX_LDAP_ATTR_EMAIL=
PHOENIX_LDAP_ATTR_UNIQUE_ID=objectGUID  # Required when ATTR_EMAIL is empty
```

<a id="placeholder-marker-pua"></a>

### 占位标记（PUA）

未配置邮箱属性时，Phoenix 生成以**私用区（PUA）Unicode 字符**（`U+E000`）为前缀的**占位值**：

```python
NULL_EMAIL_MARKER_PREFIX = "\ue000NULL(stopgap)"  # PUA character + "None" indicator

# Real email (from mail attribute)
"alice@corp.com"

# Placeholder (no email in LDAP)
"\ue000NULL(stopgap)7f3d2a1b9c8e4f5da2b6c903e1f47d8b"
# ^^^^^^^^^^ marker at start
```

**为什么使用 PUA 标记？**

| 收益 | 说明 |
|---------|-------------|
| **程序检测** | `email.startswith(NULL_EMAIL_MARKER_PREFIX)` 区分真实邮箱与占位值 |
| **UI 可区别显示** | 显示用户名，而非占位值 |
| **明显不是邮箱** | 不伪装成邮箱地址，避免混淆 |
| **确定性** | 相同 unique_id 始终生成相同占位值 |
| **保持唯一性** | MD5 哈希确保满足唯一约束 |

**辅助函数：**

```python
NULL_EMAIL_MARKER_PREFIX = "\ue000NULL(stopgap)"


def is_null_email_marker(email: str) -> bool:
    """Check if email is a placeholder (not from LDAP mail attribute)."""
    return email.startswith(NULL_EMAIL_MARKER_PREFIX)


def get_display_identifier(user) -> str:
    """Return appropriate display value - email if real, username if placeholder."""
    if is_null_email_marker(user.email):
        return user.username
    return user.email
```

**UI 处理：**

```typescript
// Server injects into window.Config:
// - ldapEmailEnabled: boolean (true if PHOENIX_LDAP_ATTR_EMAIL is set)
// - nullEmailMarkerPrefix: string ("\ue000NULL(stopgap)")

function UserIdentifier({ user }: { user: User }) {
  const isPlaceholder = user.email.startsWith(window.Config.nullEmailMarkerPrefix);
  if (isPlaceholder) {
    return <span>{user.username}</span>;  // Show username, not placeholder
  }
  return <span>{user.email}</span>;
}
```

<a id="security-considerations-for-placeholder-emails"></a>

### 占位邮箱的安全考虑

<a id="1-why-unique-id-is-required-for-placeholders"></a>

#### 1. 占位值为何必须使用唯一 ID

`PHOENIX_LDAP_ATTR_EMAIL` 为空时，每次登录会生成**新的随机占位值**。没有稳定标识符，Phoenix 无法识别回访用户：

| 登录 | 生成的占位值 | 问题 |
|-------|----------------------|---------|
| 用户 A 首次登录 | `\ue000NULL(stopgap)7f3d2a1b9c8e4f5d...` | 创建新用户 |
| 用户 A 第二次登录 | `\ue000NULL(stopgap)7f3d2a1b9c8e4f5d...` | 相同，由 unique_id 确定性生成 |

**解决方案：**`PHOENIX_LDAP_ATTR_EMAIL` 为空时，**必须**设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID`，由 unique_id 提供稳定标识符：

```python
# With unique_id (required for placeholders):
# 1. Lookup by unique_id (UUID-A) → finds User A
# 2. Login succeeds, email placeholder unchanged
```

启动时强制校验此要求；启用占位邮箱却未配置 unique_id 属性时，Phoenix 会拒绝启动。

<a id="2-configuration-constraints-for-placeholder-mode"></a>

#### 2. 占位模式的配置约束

`PHOENIX_LDAP_ATTR_EMAIL` 为空，即占位模式时，启动时强制以下约束：

| 约束 | 原因 |
|------------|--------|
| 必须设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID` | 需要稳定标识符查找用户 |
| `PHOENIX_LDAP_ALLOW_SIGN_UP` 必须为 True | 需要自动配置，没有 unique_id 无法预配置 |
| 不允许 `PHOENIX_ADMINS` | 不知道 unique_id 就无法生成占位值并预配置 |

```python
if not PHOENIX_LDAP_ATTR_EMAIL:  # Placeholder mode
    if not PHOENIX_LDAP_ATTR_UNIQUE_ID:
        raise LDAPConfigurationError("PHOENIX_LDAP_ATTR_UNIQUE_ID is required")
    if not ldap_config.allow_sign_up:
        raise LDAPConfigurationError("PHOENIX_LDAP_ALLOW_SIGN_UP must be True")
    if get_env_admins():
        raise LDAPConfigurationError("PHOENIX_ADMINS is not supported")
```

**管理员工作流：**用户首次登录时自动创建，角色由 LDAP 组映射分配。

<a id="3-pua-marker-stripping"></a>

#### 3. PUA 标记剥离

某些系统可能剥离或规范化 Unicode 字符：

| 系统 | 风险 |
|--------|------|
| 日志聚合器 | 可能剥离非 ASCII 字符，丢失标记 |
| 导出 CSV | 可能破坏 Unicode |
| 外部集成 | 可能无法保留 PUA |

**防护：**
- 始终使用 `is_null_email_marker()` 辅助函数检查 PUA 前缀
- 外部导出应使用 `get_display_identifier()` 显示用户名，而非占位值

<a id="4-database-collation"></a>

#### 4. 数据库排序规则

确保数据库排序规则能正确处理 PUA 字符：

```sql
-- PostgreSQL: UTF-8 collation handles PUA correctly
-- Verify with:
SELECT E'\ue000NULL(stopgap)12345678' = E'\ue000NULL(stopgap)12345678';
-- Should return true
```

<a id="future-nullable-email"></a>

### 未来：邮箱可为空

> **说明：**占位邮箱是临时变通方案。`email` 列目前具有 `NOT NULL` 约束和唯一索引。未来数据库结构迁移计划：
>
> 1. 允许 `email` 为空：`ALTER TABLE users ALTER COLUMN email DROP NOT NULL`
> 2. 更新唯一索引：`CREATE UNIQUE INDEX ... WHERE email IS NOT NULL`
> 3. 对没有 `mail` 的 LDAP 用户存储 `NULL`，不再使用占位邮箱
> 4. 将现有包含 `U+E000` 的占位邮箱迁移为 `NULL`
>
> 在此之前，PUA 标记使系统无需更改数据库结构即可区分真实邮箱和占位邮箱。

**行为：**

| 场景 | 行为 |
|----------|----------|
| DN 变化，OU 移动或重命名 | ✅ 按 unique_id 找到用户 |
| LDAP 邮箱变化 | ✅ 按 unique_id 找到用户并更新邮箱 |
| 域整合 | ✅ 按 unique_id 找到用户 |
| 从简单模式迁移 | ✅ 按邮箱匹配已有用户并填充 unique_id |
| 邮箱回收分配给新员工 | ❌ 403 拒绝，管理员必须解决冲突 |

**实现：**

```python
# Enterprise mode: lookup by unique_id first (case-insensitive)
user = await session.scalar(
    select(User)
    .where(User.oauth2_client_id == LDAP_CLIENT_ID_MARKER)
    .where(func.lower(User.oauth2_user_id) == unique_id.lower())
)

# Fallback: email lookup (handles migration from simple mode)
if not user:
    user = await session.scalar(
        select(User)
        .where(User.oauth2_client_id == LDAP_CLIENT_ID_MARKER)
        .where(func.lower(User.email) == email.lower())
    )
    if user:
        # SECURITY: Only migrate if user has no existing unique_id
        # This prevents email recycling attacks (see Security section)
        if user.oauth2_user_id is None:
            user.oauth2_user_id = unique_id  # Migrate to unique_id
        elif user.oauth2_user_id.lower() != unique_id.lower():
            raise HTTPException(403, "Account conflict")  # Admin must resolve

# New user creation
user = User(
    email=email,
    oauth2_client_id=LDAP_CLIENT_ID_MARKER,
    oauth2_user_id=unique_id,  # Immutable identifier (lowercase)
    ...
)
```

<a id="unique-id-attribute-details"></a>

## 唯一 ID 属性详情

<a id="supported-attribute-types"></a>

### 支持的属性类型

**仅支持基于标准 UUID 的属性：**

| 目录 | 属性 | 格式 | 示例 |
|-----------|-----------|--------|---------|
| Active Directory | `objectGUID` | 16 字节二进制，混合字节序 | `0x...` → `550e8400-e29b-41d4-...` |
| OpenLDAP | `entryUUID` | 字符串 UUID，36 字节 | `550e8400-e29b-41d4-a716-...` |
| 389 DS | `nsUniqueId` | 字符串 UUID | `550e8400-e29b-41d4-a716-...` |

**不支持：**
- 包含 16 字符字符串 ID 的自定义属性，例如 `"EMP12345ABCD6789"`
- 非 UUID 的任意二进制格式

**为何限制？**
- 16 字节值被视为二进制 UUID，即 AD `objectGUID`
- 16 字符字符串 ID 会被 `uuid.UUID(bytes_le=...)` 错误转换
- 产生的乱码 UUID 与原字符串不匹配
- 使用启发式区分两者时，误报率约为七百七十万分之一，对大规模部署不可接受

组织使用非标准唯一 ID 属性时，应改用**简单模式**，基于邮箱识别。

<a id="active-directory-objectguid"></a>

### Active Directory：objectGUID

- **类型**：二进制，16 字节，按 MS-DTYP §2.3.4 使用混合字节序
- **不可变性**：永不变化，可应对所有操作
- **可用性**：所有 AD 用户对象
- **Phoenix 处理**：转换为小写 UUID 字符串

```python
# AD stores GUID in mixed-endian format (MS-DTYP §2.3.4):
# - Data1 (4 bytes): little-endian
# - Data2 (2 bytes): little-endian
# - Data3 (2 bytes): little-endian
# - Data4 (8 bytes): big-endian
import uuid

unique_id = str(uuid.UUID(bytes_le=raw_bytes))  # e.g., "550e8400-e29b-41d4-a716-446655440000"
```

<a id="openldap-entryuuid-rfc-4530"></a>

### OpenLDAP：entryUUID（RFC 4530）

- **类型**：字符串，UUID 格式，UTF-8 为 36 字节
- **不可变性**：永不变化
- **可用性**：需要 `entryUUID` 操作属性
- **Phoenix 处理**：从字节解码并规范化为小写
- **说明**：即使字符串属性，ldap3 也返回字节（`b"550e8400-..."`）

<a id="389-directory-server-nsuniqueid"></a>

### 389 Directory Server：nsUniqueId

- **类型**：字符串，UUID 格式
- **不可变性**：永不变化
- **Phoenix 处理**：规范化为小写

<a id="case-normalization"></a>

### 大小写规范化

所有唯一 ID 均规范化为**小写**，以保持数据库查找一致：

- RFC 4122/9562 规定 UUID 不区分大小写
- 防止大小写差异导致重复账户
- 数据库查找不区分大小写（`func.lower()`）
- 大小写不同的已有条目在下次登录时更新

<a id="security-email-recycling-attack-prevention"></a>

## 安全：防止邮箱回收攻击

企业模式中，邮箱回退逻辑必须防止**邮箱回收攻击**：

**攻击场景（未防护）：**
1. 用户 A 离职，数据库：`email=john@corp.com`、`oauth2_user_id=UUID-A`
2. 用户 B 入职，使用回收邮箱，LDAP：`email=john@corp.com`、`unique_id=UUID-B`
3. 用户 B 登录：
   - unique_id 查找：未找到 `UUID-B`
   - 邮箱查找：找到用户 A！
   - **未防护时**：将用户 A 的 `oauth2_user_id` 更新为 `UUID-B`
   - 用户 B 可以访问用户 A 的数据！🚨

**已实现的保护：**
```python
if user.oauth2_user_id is None:
    user.oauth2_user_id = unique_id  # Safe migration from simple mode
elif user.oauth2_user_id.lower() != unique_id.lower():
    raise HTTPException(status_code=403, ...)  # Reject - admin must resolve
```

**受保护的行为：**
| 邮箱查找结果 | `oauth2_user_id` | 操作 |
|--------------------|------------------|--------|
| 用户 | `NULL` | ✅ 迁移，设置 `oauth2_user_id` |
| 用户 | 相同 UUID，任意大小写 | ✅ 登录成功，必要时规范化大小写 |
| 用户 | 不同 UUID | ❌ **403 拒绝**，管理员必须解决 |

**为何拒绝而非新建账户？**
- 邮箱在数据库中唯一（`CREATE UNIQUE INDEX ix_users_email`）
- 无法创建相同邮箱的新用户
- 管理员必须删除旧账户、更新旧账户 unique_id 或修改邮箱

**结果：**明确拒绝邮箱回收，防止账户劫持，也避免令人困惑的数据库错误。

<a id="switching-from-simple-to-enterprise-mode"></a>

## 从简单模式切换至企业模式

若先使用简单模式（基于邮箱），之后启用 `PHOENIX_LDAP_ATTR_UNIQUE_ID`：

1. 设置 `PHOENIX_LDAP_ATTR_UNIQUE_ID=objectGUID`，或 `entryUUID` 等
2. 用户正常登录
3. 邮箱查找找到已有用户
4. 将 unique_id 填入 `oauth2_user_id`
5. 后续登录使用 unique_id 查找

**无需手动迁移**，下次登录自动完成。

<a id="admin-provisioned-users"></a>

## 管理员预配置用户

管理员可以在用户首次登录前预创建 LDAP 用户：

```graphql
mutation {
  createUser(
    email: "alice@example.com"
    username: "Alice Smith"
    role: MEMBER
    auth_method: LDAP
  )
}
```

**管理员创建后的状态：**
- `oauth2_client_id = LDAP_CLIENT_ID_MARKER`
- `oauth2_user_id = NULL`
- `email = "alice@example.com"`

**首次登录后的状态：**
- 简单模式：`oauth2_user_id` 保持 `NULL`
- 企业模式：`oauth2_user_id = <unique_id from LDAP>`

<a id="comparison-with-other-systems"></a>

## 与其他系统对比

<a id="grafana"></a>

### Grafana

Grafana 使用 DN 作为主要标识符，存于 `user_auth.auth_id`。

| 方面 | Grafana | Phoenix |
|--------|---------|---------|
| 主要标识符 | DN | 邮箱，简单模式；或 unique_id，企业模式 |
| DN 变化 | 用户无法登录 | ✅ 已处理 |
| 邮箱变化 | ✅ 通过 DN 处理 | ✅ 企业模式通过 unique_id 处理 |
| 数据库结构 | 独立 `user_auth` 表 | 使用 `oauth2_user_id` 列 |

**Phoenix 优势**：更能应对组织调整。

<a id="okta-azure-ad-connect"></a>

### Okta、Azure AD Connect

企业 IAM 系统使用 `objectGUID`/`entryUUID` 作为主要标识符。

配置 `PHOENIX_LDAP_ATTR_UNIQUE_ID` 时，**Phoenix 企业模式符合该模式**。

<a id="design-decision-summary"></a>

## 设计决策汇总

| 决策 | 原因 |
|----------|-----------|
| **默认使用邮箱标识符** | 简单，适合大多数组织，无需额外配置 |
| **可选 unique_id 支持** | 需要时提供企业级稳定性 |
| **不存储 DN 用于查找** | DN 变化过于频繁 |
| **oauth2_user_id 不存邮箱** | 避免冗余存储 |
| **企业模式回退至邮箱** | 从简单模式平滑迁移 |
| **小写规范化** | RFC 4122 规定 UUID 不区分大小写，防止不匹配 |
| **不区分大小写的数据库查找** | 处理大小写不同的历史数据 |
| **邮箱回收保护** | 防止通过回收邮箱劫持账户 |
| **unique_id 仅支持 UUID** | 识别 16 字符字符串的启发式误报率不可接受 |
| **可配置邮箱属性** | 支持读取 `mail` 或生成占位邮箱 |
| **可选邮箱（占位值）** | `PHOENIX_LDAP_ATTR_EMAIL=` 为空时，生成 `\ue000NULL(stopgap){md5_hash}` |
| **占位值必须配合 unique_id** | 用于识别回访用户，占位值随机；启动时强制校验 |
| **属性缺失快速失败** | 管理员配置的属性必须存在，不静默回退 |
| **带 PUA 标记的占位邮箱** | `NOT NULL` 约束的临时方案，便于程序检测 |
| **确定性占位值** | `\ue000NULL(stopgap){md5(unique_id)}`，无需邮箱格式，明显不是邮箱 |
| **未来允许邮箱为空** | 数据库结构可迁移后采用的整洁方案；占位邮箱迁移为 `NULL` |

<a id="references"></a>

## 参考资料

- [RFC 4122 — UUID URN 命名空间](https://www.rfc-editor.org/rfc/rfc4122.html)，UUID 不区分大小写
- [RFC 9562 — UUID 版本 7](https://www.rfc-editor.org/rfc/rfc9562.html)，更新的 UUID 规范，仍不区分大小写
- [RFC 4530 — entryUUID 操作属性](https://www.rfc-editor.org/rfc/rfc4530.html)
- [MS-DTYP §2.3.4 — GUID 结构](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/001eec5a-7f8b-4293-9e21-ca349392db40)，混合字节序格式
- [MS-ADTS — objectGUID 属性](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/)
- [Okta LDAP Agent — 用户匹配](https://help.okta.com/en/prod/Content/Topics/Directory/LDAP-agent-overview.htm)
