<a id="configuration-reference"></a>

# 配置参考

**⚠️ 关键要求：这些环境变量名称属于不可逆决策。发布后更名会破坏用户配置。**

<a id="environment-variable-contract-summary"></a>

## 环境变量契约汇总

| 变量 | 必填？ | 默认值 | 类型 | 说明 |
|----------|-----------|---------|------|-------|
| `PHOENIX_LDAP_HOST` | ✅ **必填** | - | 字符串 | 逗号分隔，用于故障转移 |
| `PHOENIX_LDAP_PORT` | 可选 | `389` （starttls） 或 `636` （ldaps） | 整数 | 默认值取决于 `tls_mode` |
| `PHOENIX_LDAP_TLS_MODE` | 可选 | `starttls` | `none\|starttls\|ldaps` | TLS 连接模式 |
| `PHOENIX_LDAP_TLS_VERIFY` | 可选 | `true` | 布尔值 | **生产环境始终设为 true** |
| `PHOENIX_LDAP_TLS_CA_CERT_FILE` | 可选 | - | 路径 | 私有 CA 使用的自定义 CA 证书（PEM） |
| `PHOENIX_LDAP_TLS_CLIENT_CERT_FILE` | 可选 | - | 路径 | 双向 TLS 客户端证书（PEM） |
| `PHOENIX_LDAP_TLS_CLIENT_KEY_FILE` | 可选 | - | 路径 | 双向 TLS 客户端私钥（PEM） |
| `PHOENIX_LDAP_BIND_DN` | 可选 | - | 字符串 | 服务账户，搜索绑定模式必需 |
| `PHOENIX_LDAP_BIND_PASSWORD` | 可选 | - | 字符串 | 服务账户密码 |
| `PHOENIX_LDAP_USER_SEARCH_BASE_DNS` | ✅ **必填** | - | JSON 数组 | `'["ou=users,dc=example,dc=com"]'` |
| `PHOENIX_LDAP_USER_SEARCH_FILTER` | 可选 | `(&(objectClass=user)(sAMAccountName=%s))` | 字符串 | `%s` = 用户名占位符 |
| `PHOENIX_LDAP_ATTR_EMAIL` | 可选 | `mail` | 字符串 | 邮箱属性名 |
| `PHOENIX_LDAP_ATTR_DISPLAY_NAME` | 可选 | `displayName` | 字符串 | 显示名称属性 |
| `PHOENIX_LDAP_ATTR_MEMBER_OF` | 可选 | `memberOf` | 字符串 | 组成员属性，未设置 `GROUP_SEARCH_FILTER` 时使用 |
| `PHOENIX_LDAP_GROUP_SEARCH_BASE_DNS` | 条件必填 | - | JSON 数组 | 设置以下字段时必需： `GROUP_SEARCH_FILTER`  |
| `PHOENIX_LDAP_GROUP_SEARCH_FILTER` | 可选 | - | 字符串 | 设置后启用 POSIX 模式，忽略 `ATTR_MEMBER_OF` |
| `PHOENIX_LDAP_GROUP_SEARCH_FILTER_USER_ATTR` | 可选 | - | 字符串 | 替换 GROUP_SEARCH_FILTER 的属性，默认使用登录用户名 |
| `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS` | ✅ **必填** | `[]` | JSON 数组 | **兼容 Grafana 的格式** |
| `PHOENIX_LDAP_ALLOW_SIGN_UP` | 可选 | `true` | 布尔值 | 首次登录时自动创建用户 |
| `PHOENIX_LDAP_ATTR_UNIQUE_ID` | 可选 | - | 字符串 | 不可变 ID，仅在预期邮箱变化时使用 |

<a id="tls-mode-default"></a>

### 默认 TLS 模式

- Phoenix 将 `PHOENIX_LDAP_TLS_MODE` 默认为 `starttls`，可通过通常已开放的 389 端口连接，同时在任何绑定之前升级至 TLS。
- 这符合大多数 Active Directory/OpenLDAP 环境的开箱即用预期，除非明确选择 LDAPS，否则无需运维人员开放 636 端口。
- 实现始终在 `bind()` 前调用 `start_tls()`（参见[协议合规性](./protocol-compliance.md#7-starttls-implementation--security)）；Docker 中间人测试配置持续验证 StartTLS 流量保持加密，因此默认通道安全，并非明文。
- 希望从第一个字节就使用 TLS 的管理员可设置 `PHOENIX_LDAP_TLS_MODE=ldaps`，`LDAPConfig.from_env` 会自动将默认端口设为 636。

**关键设计决策**（已对照 Grafana 源码验证）：
- ✅ **前缀**：`PHOENIX_LDAP_*` 符合 Phoenix 约定，与 Grafana 不冲突
- ✅ **布尔值**：使用字符串 `"true"`/`"false"`，不用 `1`/`0`，语义更清晰
- ✅ **JSON 格式**：`GROUP_ROLE_MAPPINGS` 使用 Grafana 的 `GroupToOrgRole` 结构
- ✅ **默认值**：适用时与 Grafana 默认值一致，例如超时 10 秒、端口 389
- ⚠️ **限制**：多服务器仅支持副本，所有服务器必须共享配置

<a id="phoenix-vs-grafana-configuration-comparison"></a>

## Phoenix 与 Grafana 配置对比

下表将 Phoenix 环境变量映射至 Grafana TOML 配置文件结构，帮助用户在系统之间迁移。

| **配置** | **Phoenix（环境变量）** | **Grafana（ldap.toml）** | **说明** |
|-------------------|-------------------------------------|-------------------------|-----------|
| **启用 LDAP** | `PHOENIX_LDAP_HOST` （是否存在） | `[auth.ldap]`<br>`enabled = true`<br>`config_file = "/etc/grafana/ldap.toml"` | Phoenix：设置 HOST 时自动启用<br>Grafana：需要显式启用并指定文件路径 |
| **服务器主机** | `PHOENIX_LDAP_HOST="dc1.com,dc2.com"` | `[[servers]]`<br>`host = "dc1.com"`<br>`[[servers]]`<br>`host = "dc2.com"` | Phoenix：逗号分隔字符串<br>Grafana：多个 `[[servers]]` 块 |
| **服务器端口** | `PHOENIX_LDAP_PORT=389` | `port = 389` | 两者默认均为 389 |
| **TLS 模式** | `PHOENIX_LDAP_TLS_MODE="starttls"` | `use_ssl = false`<br>`start_tls = false` （默认） | Phoenix：单一 TLS_MODE，默认 StartTLS<br>Grafana：独立 SSL/StartTLS 标志；StartTLS 需显式启用 |
| **TLS 校验** | `PHOENIX_LDAP_TLS_VERIFY="true"` | `ssl_skip_verify = false` | 两者默认均校验证书 |
| **自定义 CA 证书** | `PHOENIX_LDAP_TLS_CA_CERT_FILE="/path/to/ca.pem"` | `root_ca_cert = "/path/to/ca.pem"` | 私有 CA 语义相同 |
| **客户端证书（mTLS）** | `PHOENIX_LDAP_TLS_CLIENT_CERT_FILE="/path/to/client.crt"`<br>`PHOENIX_LDAP_TLS_CLIENT_KEY_FILE="/path/to/client.key"` | `client_cert = "/path/to/client.crt"`<br>`client_key = "/path/to/client.key"` | 双向 TLS 语义相同 |
| **绑定 DN** | `PHOENIX_LDAP_BIND_DN="cn=admin,..."` | `bind_dn = "cn=admin,..."` | 语义相同 |
| **绑定密码** | `PHOENIX_LDAP_BIND_PASSWORD="secret"` | `bind_password = "secret"`<br>或 `bind_password = '${ENV_VAR}'` | Phoenix：直接使用环境变量<br>Grafana：TOML 值或插值 |
| **用户搜索基准** | `PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["ou=users,..."]'` | `search_base_dns = ["ou=users,dc=..."]` | 两者均为 DN 的 JSON/TOML 数组 |
| **用户搜索过滤器** | `PHOENIX_LDAP_USER_SEARCH_FILTER="(uid=%s)"` | `search_filter = "(uid=%s)"` | 相同： `%s` = 用户名 |
| **邮箱属性** | `PHOENIX_LDAP_ATTR_EMAIL="mail"` | `[servers.attributes]`<br>`email = "mail"` | Phoenix：直接使用环境变量<br>Grafana：嵌套 TOML 章节 |
| **名称属性** | `PHOENIX_LDAP_ATTR_DISPLAY_NAME="displayName"` | `name = "displayName"` | 两者均映射显示名称 |
| **唯一 ID** | `PHOENIX_LDAP_ATTR_UNIQUE_ID="objectGUID"` | 不支持 | Phoenix：可选不可变标识符，可应对邮箱变化 |
| **组成员关系** | `PHOENIX_LDAP_ATTR_MEMBER_OF="memberOf"` | `member_of = "memberOf"` | Active Directory 属性 |
| **组搜索基准** | `PHOENIX_LDAP_GROUP_SEARCH_BASE_DNS='["ou=groups,..."]'` | `group_search_base_dns = ["ou=groups,dc=..."]` | 两者均为 DN 的 JSON/TOML 数组 |
| **组搜索过滤器** | `PHOENIX_LDAP_GROUP_SEARCH_FILTER="(member=%s)"` | `group_search_filter = "(member=%s)"` | 相同： `%s` = 替换值 |
| **组过滤用户属性** | `PHOENIX_LDAP_GROUP_SEARCH_FILTER_USER_ATTR="uid"` | `group_search_filter_user_attribute = "uid"` | 替换以下占位符的属性值： `%s`，用于 GROUP_SEARCH_FILTER。未设置时使用登录用户名。 |
| **组→角色映射** | `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='[`<br>`  {"group_dn": "cn=admins,...", "role": "ADMIN"}`<br>`]'` | `[[servers.group_mappings]]`<br>`group_dn = "cn=admins,..."`<br>`org_role = "Admin"` | Phoenix：JSON 使用 `role` （无组织）<br>Grafana：TOML 使用 `org_role` |
| **允许注册** | `PHOENIX_LDAP_ALLOW_SIGN_UP="true"` | `[auth.ldap]`<br>`allow_sign_up = true` | 两者默认均为 `true` |
| **超时** | 不提供配置，使用 ldap3 默认值 | `timeout = 10` | Grafana：可按秒配置 |
| **连接池** | 不提供配置，使用 ldap3 默认值 | 不可配置 | 两者均使用底层库默认值 |

**主要区别**：

1. **配置方式**
   - Phoenix：纯环境变量，遵循十二要素应用模式
   - Grafana：TOML 配置文件，可选环境变量插值

2. **多服务器配置**
   - Phoenix：逗号分隔的副本，仅支持相同配置
   - Grafana：多个 `[[servers]]` 块，每台服务器可采用不同配置

3. **角色映射格式**
   - Phoenix：JSON 使用 `role` 字段，值为全大写（`ADMIN`、`MEMBER`、`VIEWER`）
   - Grafana：TOML 使用 `org_role` 字段，值为首字母大写（`Admin`、`Editor`、`Viewer`）

4. **迁移路径**
   - Grafana → Phoenix：必须手动将 TOML 转换为环境变量
   - 不能直接复用 `ldap.toml` 文件
   - 角色映射需要转换大小写（`Admin` → `ADMIN` 等）

**兼容性说明**：
- **Grafana 用户**：不能直接复用 `ldap.toml` 文件，必须转换为环境变量
- **字段名称**：Grafana 使用 `org_role`，Phoenix 使用 `role`，没有组织概念
- **角色值**：Grafana 使用首字母大写（`Admin`、`Editor`、`Viewer`），Phoenix 使用全大写（`ADMIN`、`MEMBER`、`VIEWER`）

**应避免的常见配置错误**：

| ❌ **错误** | ✅ **正确** | 原因 |
|-------------|---------------|---------|
| `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='{"admin":["..."]}'` | `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='[{"group_dn":"...", "role":"ADMIN"}]'` | 必须使用包含必需字段的 JSON 数组结构 |
| `"role": "admin"` （小写） | `"role": "ADMIN"` （大写） | Phoenix 使用大写角色名称 |
| `"role": "ADMIN"` （Grafana 字段） | `"role": "ADMIN"` （Phoenix 字段） | Phoenix 使用 `role`, 而非 `org_role` （没有组织概念） |
| `PHOENIX_LDAP_TLS_MODE=starttls` （无引号） | `PHOENIX_LDAP_TLS_MODE="starttls"` （有引号） | Shell 字符串可能需要引号 |
| `PHOENIX_LDAP_PORT="389"` （字符串） | `PHOENIX_LDAP_PORT=389` （整数） | 端口应为无引号整数 |
| 多行 `PHOENIX_LDAP_HOST` | `PHOENIX_LDAP_HOST="dc1.com,dc2.com"` | 使用逗号分隔，不使用多个变量 |
| `%s` 位于 `GROUP_SEARCH_FILTER` 用于用户名 | `%s` 位于 `USER_SEARCH_FILTER` | 用户过滤器使用用户名；组过滤器默认使用登录用户名，或 GROUP_SEARCH_FILTER_USER_ATTR 指定的属性 |

**校验清单**（已在代码中实现）：
1. ✅ `PHOENIX_LDAP_HOST` 不为空（config.py:1423）
2. ✅ `PHOENIX_LDAP_GROUP_ROLE_MAPPINGS` 是有效 JSON 数组（config.py:1433-1442）
3. ✅ 每个映射包含 `group_dn` 和 `role` 字段（config.py:1457-1476）
4. ✅ `role` 值为 `"ADMIN"`、`"MEMBER"` 或 `"VIEWER"`，不区分大小写（config.py:1449）
5. ✅ 设置 `GROUP_SEARCH_FILTER` 时，必须同时设置 `GROUP_SEARCH_BASE_DNS`
6. ✅ `TLS_MODE` 为 `"starttls"` 或 `"ldaps"`（config.py:1484-1488）
7. ⚠️ **安全**：生产环境中若 `TLS_MODE=none` 或 `TLS_VERIFY=false`，则发出警告（config.py）

---

<a id="complete-environment-variables"></a>

## 完整环境变量

```bash
# ==============================================================================
# LDAP Server Connection
# ==============================================================================

# LDAP server hosts (comma-separated for multiple servers)
# Examples:
#   - "ldap.example.com"
#   - "dc1.corp.com,dc2.corp.com,dc3.corp.com"
PHOENIX_LDAP_HOST="ldap.corp.example.com"

# LDAP server port (default: 389 for StartTLS, 636 for LDAPS)
PHOENIX_LDAP_PORT=389

# Use TLS (recommended: always true for production)
# Options: "none", "starttls", "ldaps"
PHOENIX_LDAP_TLS_MODE="starttls"

# TLS mode: "starttls" or "ldaps"
# - starttls: Start with plaintext, upgrade to TLS (port 389)
# - ldaps: TLS from the start (port 636)
PHOENIX_LDAP_TLS_MODE="starttls"

# Verify TLS certificates (recommended: always true for production)
# Options: "true" or "false"
PHOENIX_LDAP_TLS_VERIFY="true"

# ==============================================================================
# Bind Configuration (Service Account)
# ==============================================================================

# Service account DN for binding (optional for direct bind)
# Examples:
#   - Active Directory: "CN=svc-phoenix,OU=Service Accounts,DC=corp,DC=com"
#   - OpenLDAP: "cn=readonly,dc=example,dc=com"
PHOENIX_LDAP_BIND_DN="CN=svc-phoenix,OU=Service Accounts,DC=corp,DC=com"

# Service account password
PHOENIX_LDAP_BIND_PASSWORD="service-account-password-here"

# ==============================================================================
# User Search Configuration
# ==============================================================================

# JSON array of base DNs for user searches (searched in order until user found)
# Examples:
#   - '["OU=Users,DC=corp,DC=com"]'
#   - '["OU=Employees,DC=corp,DC=com", "OU=Contractors,DC=corp,DC=com"]'
PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["OU=Users,DC=corp,DC=com"]'

# User search filter (use %s as placeholder for username)
# Examples:
#   - Active Directory: "(&(objectClass=user)(sAMAccountName=%s))"
#   - OpenLDAP: "(&(objectClass=inetOrgPerson)(uid=%s))"
PHOENIX_LDAP_USER_SEARCH_FILTER="(&(objectClass=user)(sAMAccountName=%s))"

# ==============================================================================
# Attribute Mapping
# ==============================================================================

# LDAP attribute containing user's email
# Examples: "mail", "userPrincipalName", "email"
PHOENIX_LDAP_ATTR_EMAIL="mail"

# LDAP attribute containing user's display name
# Examples: "displayName", "cn", "name"
PHOENIX_LDAP_ATTR_DISPLAY_NAME="displayName"

# LDAP attribute containing group memberships (for Active Directory)
# Examples: "memberOf" (Active Directory), "" (use group search for POSIX)
PHOENIX_LDAP_ATTR_MEMBER_OF="memberOf"

# ==============================================================================
# User Identification (Optional)
# ==============================================================================

# Immutable unique ID attribute (only configure if you expect email changes)
# Use cases: company rebranding, M&A, frequent name changes, compliance requirements
# - Active Directory: "objectGUID"
# - OpenLDAP: "entryUUID"
# - 389 Directory Server: "nsUniqueId"
# When not set (default), email is used as the identifier.
# PHOENIX_LDAP_ATTR_UNIQUE_ID="objectGUID"

# ==============================================================================
# Group Search (for POSIX/OpenLDAP without memberOf)
# ==============================================================================

# JSON array of base DNs for group searches (groups collected from all bases)
# Examples:
#   - '["OU=Groups,DC=corp,DC=com"]'
#   - '["OU=Groups,DC=corp,DC=com", "OU=Teams,DC=corp,DC=com"]'
PHOENIX_LDAP_GROUP_SEARCH_BASE_DNS='["OU=Groups,DC=corp,DC=com"]'

# Group search filter (use %s as placeholder for substituted value)
# Example: "(&(objectClass=group)(member=%s))"
PHOENIX_LDAP_GROUP_SEARCH_FILTER="(&(objectClass=group)(member=%s))"

# Attribute from user entry to substitute for %s in GROUP_SEARCH_FILTER
# When set: Reads the specified attribute from the user's LDAP entry
# When not set (default): Uses the login username directly
#
# Common values:
#   - "uid": For POSIX groups using memberUid (contains uid attribute value)
#   - "dn" or "distinguishedName": For groups using member with full DNs (AD)
#   - Not set: Uses login username (works for most POSIX setups)
#
# Example POSIX (memberUid contains usernames):
#   PHOENIX_LDAP_GROUP_SEARCH_FILTER="(&(objectClass=posixGroup)(memberUid=%s))"
#   # GROUP_SEARCH_FILTER_USER_ATTR not set - uses login username
#
# Example AD (member contains full DNs):
#   PHOENIX_LDAP_GROUP_SEARCH_FILTER="(member:1.2.840.113556.1.4.1941:=%s)"
#   PHOENIX_LDAP_GROUP_SEARCH_FILTER_USER_ATTR="dn"
# PHOENIX_LDAP_GROUP_SEARCH_FILTER_USER_ATTR="uid"

# ==============================================================================
# Group to Role Mappings (Grafana-Compatible Format)
# ==============================================================================

# Grafana-compatible format (verified against Grafana source code)
# Based on: https://github.com/grafana/grafana/blob/main/pkg/services/ldap/settings.go
#
# Grafana's GroupToOrgRole struct (for reference):
#   type GroupToOrgRole struct {
#       GroupDN        string       `json:"group_dn"`         // REQUIRED
#       OrgRole        RoleType     `json:"org_role"`         // REQUIRED
#       OrgId          int64        `json:"org_id"`           // Optional (defaults to 1)
#       IsGrafanaAdmin *bool        `json:"grafana_admin"`    // Optional
#   }
#
# Phoenix JSON Schema (TypeScript notation):
#   Array<{
#     group_dn: string;      // REQUIRED: LDAP group DN or "*" for wildcard
#     role: "ADMIN" | "MEMBER" | "VIEWER";  // REQUIRED: Capitalized!
#   }>
#
# Phoenix Role Mapping (Direct - No Intermediary):
#   - "ADMIN"  → ADMIN role (Phoenix)
#   - "MEMBER" → MEMBER role (Phoenix)
#   - "VIEWER" → VIEWER role (Phoenix)
#
# Note: Phoenix uses its internal role names directly in the configuration.
# This differs from the original Grafana-compatible approach which used
# Grafana role names ("Admin", "Editor", "Viewer") as an intermediary.
#
# Matching Logic (verified against Grafana helpers.go):
#   - Wildcard "*" matches ALL users (checked first)
#   - DN matching is case-insensitive (strings.EqualFold)
#   - First match wins (priority order matters!)
#
PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='[
  {"group_dn": "CN=Phoenix Admins,OU=Groups,DC=corp,DC=com", "role": "ADMIN"},
  {"group_dn": "CN=Phoenix Users,OU=Groups,DC=corp,DC=com", "role": "MEMBER"},
  {"group_dn": "CN=Engineering,OU=Groups,DC=corp,DC=com", "role": "MEMBER"},
  {"group_dn": "CN=Phoenix Viewers,OU=Groups,DC=corp,DC=com", "role": "VIEWER"},
  {"group_dn": "*", "role": "VIEWER"}
]'

# ==============================================================================
# Sign-Up Control (Grafana-Compatible)
# ==============================================================================

# Allow automatic user creation on first LDAP login
# Options: "true" (default, matches Grafana) or "false"
# - "true": Any valid LDAP user can create an account on first login
# - "false": Users must be pre-provisioned before first login:
#     * Via PHOENIX_ADMINS env var at startup
#     * Via the application's user management UI
#   Pre-provisioned users are matched by email on first LDAP login.
# Security: Set to "false" in environments requiring pre-approved access
PHOENIX_LDAP_ALLOW_SIGN_UP="true"

```

<a id="configuration-examples"></a>

## 配置示例

**示例 1：Active Directory（单服务器）**
```bash
PHOENIX_LDAP_HOST="ad.corp.com"
PHOENIX_LDAP_PORT=389
PHOENIX_LDAP_TLS_MODE="starttls"
PHOENIX_LDAP_BIND_DN="CN=svc-phoenix,OU=Service Accounts,DC=corp,DC=com"
PHOENIX_LDAP_BIND_PASSWORD="password"
PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["OU=Users,DC=corp,DC=com"]'
PHOENIX_LDAP_USER_SEARCH_FILTER="(&(objectClass=user)(sAMAccountName=%s))"
PHOENIX_LDAP_ATTR_EMAIL="mail"
PHOENIX_LDAP_ATTR_DISPLAY_NAME="displayName"
PHOENIX_LDAP_ATTR_MEMBER_OF="memberOf"
# Optional: Only set if you expect user emails to change (rebranding, M&A)
# PHOENIX_LDAP_ATTR_UNIQUE_ID="objectGUID"
PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='[
  {"group_dn": "CN=Phoenix Admins,OU=Groups,DC=corp,DC=com", "role": "ADMIN"},
  {"group_dn": "CN=Phoenix Users,OU=Groups,DC=corp,DC=com", "role": "MEMBER"}
]'
```

**示例 2：OpenLDAP（POSIX 组）**
```bash
PHOENIX_LDAP_HOST="ldap.example.com"
PHOENIX_LDAP_PORT=389
PHOENIX_LDAP_TLS_MODE="starttls"
PHOENIX_LDAP_BIND_DN="cn=readonly,dc=example,dc=com"
PHOENIX_LDAP_BIND_PASSWORD="password"
PHOENIX_LDAP_USER_SEARCH_BASE_DNS='["ou=people,dc=example,dc=com"]'
PHOENIX_LDAP_USER_SEARCH_FILTER="(&(objectClass=inetOrgPerson)(uid=%s))"
PHOENIX_LDAP_ATTR_EMAIL="mail"
PHOENIX_LDAP_ATTR_DISPLAY_NAME="cn"
# Note: When GROUP_SEARCH_FILTER is set, POSIX mode is enabled automatically
# Optional: Only set if you expect user emails to change
# PHOENIX_LDAP_ATTR_UNIQUE_ID="entryUUID"
PHOENIX_LDAP_GROUP_SEARCH_BASE_DNS='["ou=groups,dc=example,dc=com"]'
PHOENIX_LDAP_GROUP_SEARCH_FILTER="(&(objectClass=posixGroup)(memberUid=%s))"
PHOENIX_LDAP_GROUP_ROLE_MAPPINGS='[
  {"group_dn": "cn=phoenix-admins,ou=groups,dc=example,dc=com", "role": "ADMIN"},
  {"group_dn": "*", "role": "VIEWER"}
]'
```

**示例 3：多台 LDAP 服务器（高可用）**
```bash
PHOENIX_LDAP_HOST="dc1.corp.com,dc2.corp.com,dc3.corp.com"
PHOENIX_LDAP_PORT=389
PHOENIX_LDAP_TLS_MODE="starttls"
# ... rest of configuration same as Example 1
```

