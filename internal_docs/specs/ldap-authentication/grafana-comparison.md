<a id="grafana-source-code-research"></a>

# Grafana 源码研究

**完整 Grafana 源码分析** — 审阅 Grafana LDAP 实现的详细发现，用于确保 Phoenix 兼容性。

<a id="files-reviewed"></a>

## 已审阅文件

1. [settings.go](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/settings.go) — 结构定义、默认值
2. [ldap.toml](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/conf/ldap.toml) — 配置示例
3. [service/ldap.go](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/service/ldap.go) — 校验、默认值
4. [ldap.go](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/ldap.go) — 组匹配逻辑
5. [helpers.go](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/helpers.go) — `IsMemberOf()` 函数
6. [multildap.go](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/multildap/multildap.go) — 多服务器故障转移

<a id="grafanas-grouptoorgrole-struct"></a>

## Grafana 的 GroupToOrgRole 结构

```go
type GroupToOrgRole struct {
    GroupDN        string   `json:"group_dn"`
    OrgId          int64    `json:"org_id"`          // Defaults to 1
    IsGrafanaAdmin *bool    `json:"grafana_admin"`   // Optional, for server admin
    OrgRole        RoleType `json:"org_role"`        // "Admin", "Editor", "Viewer"
}
```

<a id="grafanas-group-matching-logic"></a>

## Grafana 组匹配逻辑

```go
func IsMemberOf(memberOf []string, group string) bool {
    if group == "*" {
        return true  // Wildcard matches ALL users
    }
    for _, member := range memberOf {
        if strings.EqualFold(member, group) {  // Case-insensitive!
            return true
        }
    }
    return false
}
```

<a id="phoenix-adaptation"></a>

## Phoenix 适配

Phoenix 适配 Grafana 配置格式，同时考虑 Phoenix 特有差异：

**相似之处**：
- ✅ 支持通配符 `"*"`，与 Grafana 一致，最先检查，匹配所有用户
- ✅ **不区分大小写的 DN 匹配**，与 Grafana 一致（`strings.EqualFold`）
- ✅ 首次匹配优先，与 Grafana 一致
- ✅ 多服务器故障转移，按顺序尝试，与 Grafana 一致

**Phoenix 特有差异**：
- ✅ 字段名称为 `role`，不是 `org_role`，Phoenix 没有组织概念
- ✅ 值为 `"ADMIN"`、`"MEMBER"`、`"VIEWER"`，全大写，与 Phoenix 角色名一致
- ⚠️ 省略 `org_id`，Phoenix 不支持多组织
- ⚠️ 省略 `grafana_admin`，Phoenix 没有服务器管理员概念
- ⚠️ 省略团队同步（`TeamOrgGroupDTO`），Phoenix 只有角色，没有团队

<a id="configuration-field-comparison"></a>

## 配置字段对比

完整逐字段对比 Grafana `ServerConfig` 结构与 Phoenix 环境变量。

<a id="server-connection"></a>

### 服务器连接

| Grafana (`settings.go`) | Phoenix | 状态 |
|------------------------|---------|--------|
| `Host string` | `PHOENIX_LDAP_HOST` | ✅ 一致 |
| `Port int` （默认 389） | `PHOENIX_LDAP_PORT` （根据模式默认为 389/636） | ✅ 一致 |

<a id="tls-configuration"></a>

### TLS 配置

| Grafana | Phoenix | 状态 |
|---------|---------|--------|
| `UseSSL bool` | 合并配置： `PHOENIX_LDAP_TLS_MODE=ldaps` | ✅ 等效 |
| `StartTLS bool` | 合并配置： `PHOENIX_LDAP_TLS_MODE=starttls` | ✅ 等效 |
| `SkipVerifySSL bool` | `PHOENIX_LDAP_TLS_VERIFY` （逻辑取反） | ✅ 等效 |
| `MinTLSVersion string` | ❌ 未实现 | ⚠️ 低优先级 |
| `TLSCiphers []string` | ❌ 未实现 | ⚠️ 低优先级 |
| `RootCACert string` | `PHOENIX_LDAP_TLS_CA_CERT_FILE` | ✅ 一致 |
| `ClientCert string` | `PHOENIX_LDAP_TLS_CLIENT_CERT_FILE` | ✅ 一致 |
| `ClientKey string` | `PHOENIX_LDAP_TLS_CLIENT_KEY_FILE` | ✅ 一致 |

<a id="bind-configuration"></a>

### 绑定配置

| Grafana | Phoenix | 状态 |
|---------|---------|--------|
| `BindDN string` | `PHOENIX_LDAP_BIND_DN` | ✅ 一致 |
| `BindPassword string` | `PHOENIX_LDAP_BIND_PASSWORD` | ✅ 一致 |
| `Timeout int` （默认 10 秒） | ❌ 未实现 | ⚠️ 低优先级 |

<a id="user-search"></a>

### 用户搜索

| Grafana | Phoenix | 状态 |
|---------|---------|--------|
| `SearchBaseDNs []string` | `PHOENIX_LDAP_USER_SEARCH_BASE_DNS` （JSON 数组） | ✅ **一致** |
| `SearchFilter string` | `PHOENIX_LDAP_USER_SEARCH_FILTER` | ✅ 一致 |

<a id="attribute-mapping"></a>

### 属性映射

| Grafana (`AttributeMap`) | Phoenix | 状态 |
|--------------------------|---------|--------|
| `Email string` | `PHOENIX_LDAP_ATTR_EMAIL` | ✅ 一致 |
| `Name string` | `PHOENIX_LDAP_ATTR_DISPLAY_NAME` | ✅ 一致 |
| `MemberOf string` | `PHOENIX_LDAP_ATTR_MEMBER_OF` | ✅ 一致 |
| `Username string` | ❌ 无需配置，来自登录表单 | ✅ 不适用 |
| `Surname string` | ❌ 未实现 | ✅ 不需要 |
| ❌ Grafana 中不存在 | `PHOENIX_LDAP_ATTR_UNIQUE_ID` | ✅ Phoenix 额外功能 |

<a id="group-search-posix"></a>

### 组搜索（POSIX）

| Grafana | Phoenix | 状态 |
|---------|---------|--------|
| `GroupSearchBaseDNs []string` | `PHOENIX_LDAP_GROUP_SEARCH_BASE_DNS` （JSON 数组） | ✅ **一致** |
| `GroupSearchFilter string` | `PHOENIX_LDAP_GROUP_SEARCH_FILTER` | ✅ 一致 |
| `GroupSearchFilterUserAttribute string` | `PHOENIX_LDAP_GROUP_SEARCH_FILTER_USER_ATTR` | ✅ **一致** |

<a id="group-search-filter-user-attribute-behavior"></a>

#### 组搜索过滤器用户属性行为

Grafana 和 Phoenix 均支持 `group_search_filter_user_attribute`（Grafana）/`GROUP_SEARCH_FILTER_USER_ATTR`（Phoenix），行为相同：

**Grafana** (`ldap.go` 第 598—605 行):
```go
if config.GroupSearchFilterUserAttribute == "" {
    filterReplace = getAttribute(config.Attr.Username, entry)
} else {
    filterReplace = getAttribute(
        config.GroupSearchFilterUserAttribute,
        entry,
    )
}
```

**Phoenix** (`ldap.py`):
```python
if self.config.group_search_filter_user_attr:
    filter_value = _get_attribute(user_entry, self.config.group_search_filter_user_attr)
else:
    filter_value = username  # Uses login username
```

**常见值：**
- `"uid"`：用于采用 `memberUid` 的 POSIX 组，包含 uid 属性值
- `"dn"` 或 `"distinguishedName"`：用于 `member` 存放完整 DN 的组，例如 Active Directory
- 未设置（默认）：使用登录用户名，适用于大多数 POSIX 配置

**Grafana 文档参考：**
- https://grafana.com/docs/grafana/latest/setup-grafana/configure-access/configure-authentication/ldap/

<a id="group-role-mappings"></a>

### 组角色映射

| Grafana (`GroupToOrgRole`) | Phoenix | 状态 |
|---------------------------|---------|--------|
| `GroupDN string` | `group_dn` | ✅ 一致 |
| `OrgRole RoleType` | `role` （不是 `org_role`） | ✅ 有意设计 |
| `OrgId int64` | ❌ 不适用 | ✅ 不适用，无组织 |
| `IsGrafanaAdmin *bool` | ❌ 不适用 | ✅ 不适用 |

<a id="sign-up-control"></a>

### 注册控制

| Grafana | Phoenix | 状态 |
|---------|---------|--------|
| `AllowSignUp bool` | `PHOENIX_LDAP_ALLOW_SIGN_UP` | ✅ 一致 |

---

<a id="missing-features-low-priority"></a>

### 缺少的功能（低优先级）

Phoenix 尚未实现以下 Grafana 功能，可在未来有需求时添加：

| 功能 | Grafana | 使用场景 |
|---------|---------|----------|
| `MinTLSVersion` | 强制 TLS 1.2+ | 企业安全合规 |
| `TLSCiphers` | 限制密码套件 | 企业安全合规 |
| `Timeout` | 连接超时，秒 | 网络可靠性 |

<a id="phoenix-extras-not-in-grafana"></a>

### Phoenix 额外功能（Grafana 不具备）

| 功能 | Phoenix | 使用场景 |
|---------|---------|----------|
| `PHOENIX_LDAP_ATTR_UNIQUE_ID` | 不可变用户标识符 | 应对邮箱变化，objectGUID、entryUUID |

---

<a id="implementation-logic-discrepancies"></a>

## 实现逻辑差异

详细比较 Grafana 和 Phoenix LDAP 实现的运行时行为。

<a id="1-multi-server-failover-behavior"></a>

### 1. 多服务器故障转移行为

Grafana 和 Phoenix 均支持多个 LDAP 服务器实现高可用，但处理不同错误条件的方式不同。

<a id="failover-trigger-comparison"></a>

#### 故障转移触发条件对比

| 错误条件 | Grafana | Phoenix | 是否一致？ |
|----------------|---------|---------|--------|
| **连接失败**，拨号错误 | ✅ 尝试下一台服务器 | ✅ 尝试下一台服务器 | ✅ 一致 |
| **用户不存在** | ✅ 尝试下一台服务器 | ❌ 立即返回 | ⚠️ **不同** |
| **密码无效** | ✅ 尝试下一台服务器 | ❌ 立即返回 | ⚠️ **不同** |
| **其他 LDAP 错误** | ❌ 返回错误 | ✅ 尝试下一台服务器 | ⚠️ **不同** |

<a id="grafanas-approach-multildapgo"></a>

#### Grafana 方案（`multildap.go`）

Grafana 定义会触发故障转移的“静默错误”：

```go
// isSilentError - these errors cause failover to next server
func isSilentError(err error) bool {
    continueErrs := []error{ErrInvalidCredentials, ErrCouldNotFindUser}
    for _, cerr := range continueErrs {
        if errors.Is(err, cerr) {
            return true
        }
    }
    return false
}

// Login - tries all servers
func (multiples *MultiLDAP) Login(query *login.LoginUserQuery) {
    ldapSilentErrors := []error{}
    
    for index, config := range multiples.configs {
        // Dial failure → try next server
        if err := server.Dial(); err != nil {
            if index == len(multiples.configs)-1 {
                return nil, err  // Last server, return error
            }
            continue  // Try next
        }
        
        user, err := server.Login(query)
        if err != nil {
            if isSilentError(err) {  // User not found OR invalid password
                ldapSilentErrors = append(ldapSilentErrors, err)
                continue  // TRY NEXT SERVER
            }
            return nil, err  // Other errors stop immediately
        }
        
        if user != nil {
            return user, nil  // Success!
        }
    }
    
    // After all servers tried:
    // - Return ErrInvalidCredentials if ANY server returned it
    // - Otherwise return ErrCouldNotFindUser
    for _, ldapErr := range ldapSilentErrors {
        if errors.Is(ldapErr, ErrInvalidCredentials) {
            return nil, ErrInvalidCredentials
        }
    }
    return nil, ErrCouldNotFindUser
}
```

**Grafana 使用场景**：支持**异构 LDAP 服务器**：
- 不同服务器可能拥有不同用户群
- 用户“alice”可能仅存在于服务器 B，而不在服务器 A
- 常见于具有多个 AD 域或林的组织

<a id="phoenixs-approach-ldappy"></a>

#### Phoenix 方案（`ldap.py`）

Phoenix 仅在连接错误时执行故障转移：

```python
for server in self.servers:
    try:
        with self._establish_connection(server) as conn:
            user_entry = self._search_user(conn, escaped_username)
            if not user_entry:
                # User not found → STOP immediately (no failover)
                self._dummy_bind_for_timing(server, password)
                return None
            
            if not self._verify_user_password(server, user_dn, password):
                # Wrong password → STOP immediately (no failover)
                return None
            
            # Success!
            return LDAPUserInfo(...)
            
    except LDAPException as e:
        # Connection/protocol error → TRY NEXT SERVER
        logger.warning(f"LDAP server {server.host} failed: {type(e).__name__}")
        continue

# All servers failed with LDAPException
return None
```

**Phoenix 使用场景**：假定为**副本服务器**：
- 所有服务器均是同一目录的副本
- 所有服务器用户集相同
- “用户不存在”是确定答案，无需去其他位置尝试

<a id="design-rationale"></a>

#### 设计依据

**Phoenix 为何选择在“用户不存在”时不执行故障转移：**

1. **语义正确性**：基于副本的高可用场景中，服务器具有相同数据。用户不存在于服务器 A，也不会存在于服务器 B。

2. **避免掩盖问题**：在“用户不存在”时故障转移可能掩盖：
   - 复制延迟
   - 搜索基准配置错误
   - AD 全局编录与域控制器不一致

3. **安全**：在“密码无效”时尝试全部服务器可能：
   - 扩大攻击面，提供更多可探测服务器
   - 泄漏用户位于哪台服务器的信息

4. **简单**：单台服务器提供确定答案，无需聚合错误。

<a id="when-this-matters"></a>

#### 何时产生影响

| 场景 | Grafana | Phoenix |
|----------|---------|---------|
| **副本高可用**，相同用户集 | 可用，但检查冗余 | 可用，最优 |
| **多域/林**，不同用户集 | 可用 | ❌ 无法找到非主服务器上的用户 |
| **AD GC 与 DC**，部分属性与完整属性 | 可用 | GC 为主服务器时可能失败 |

<a id="known-limitation"></a>

#### 已知限制

**Phoenix 不支持异构 LDAP 服务器**，即不同服务器具有不同用户群。

| 架构 | 是否支持？ |
|--------------|------------|
| 副本高可用，相同服务器 | ✅ 完全支持 |
| 单 AD 域，多 DC | ✅ 完全支持 |
| 多域 AD 林 | ❌ 不支持 |
| 多个独立 LDAP 目录 | ❌ 不支持 |

**为何不与 Grafana 保持相同：**

1. **默认安全**：在“用户不存在”或“密码错误”时探测全部服务器会扩大攻击面，并允许用户名枚举。

2. **大多数部署是副本**：企业常见模式为相同服务器集构成高可用，而非异构目录。

3. **不掩盖基础设施问题**：在“用户不存在”时故障转移可能掩盖复制延迟、搜索基准配置错误或 AD GC/DC 不一致，这些问题应在基础设施层解决。

4. **更简单、更快**：单台服务器给出确定答案，失败时无需聚合错误或遍历全部服务器。

**未来增强**：若客户需要多域或异构 LDAP 支持，可添加显式启用的配置标志，例如 `PHOENIX_LDAP_FAILOVER_MODE=heterogeneous`。

---

<a id="2-dn-comparison-for-group-matching"></a>

### 2. 组匹配中的 DN 比较

| 方面 | Grafana | Phoenix | 影响 |
|--------|---------|---------|--------|
| 方法 | `strings.EqualFold()` | RFC 4514 规范化 | ✅ Phoenix 更健壮 |
| 处理空白 | ❌ 否 | ✅ 是 | Phoenix 更佳 |
| 处理多值 RDN | ❌ 否 | ✅ 是 | Phoenix 更佳 |

**Grafana** (`helpers.go`):
```go
func IsMemberOf(memberOf []string, group string) bool {
    if group == "*" { return true }
    for _, member := range memberOf {
        if strings.EqualFold(member, group) {  // Simple case-insensitive
            return true
        }
    }
    return false
}
```

**Phoenix** (`ldap.py`):
```python
def _is_member_of(canonical_user_groups: set[str], target_group: str) -> bool:
    if target_group == "*":
        return True
    target_canonical = canonicalize_dn(target_group)  # Full RFC 4514
    return target_canonical in canonical_user_groups
```

**结果**：Phoenix 能正确匹配仅空白或属性顺序不同的 DN。Grafana 可能无法匹配等价 DN。

---

<a id="3-no-group-match-behavior"></a>

### 3. 无组匹配时的行为

| 方面 | Grafana | Phoenix | 影响 |
|--------|---------|---------|--------|
| 无组匹配时的行为 | 拒绝并禁用用户 | 拒绝访问 | ✅ 一致 |
| `SkipOrgRoleSync` 选项 | ✅ 是 | ❌ 否 | ⚠️ Phoenix 更严格 |

**Grafana** (`ldap.go`):
```go
// validateGrafanaUser - denies access if groups configured but none match
if !server.cfg.SkipOrgRoleSync && len(server.Config.Groups) > 0 &&
    (len(user.OrgRoles) == 0 && ...) {
    return ErrInvalidCredentials
}

// SkipOrgRoleSync option allows bypassing group checks entirely
if server.cfg.SkipOrgRoleSync {
    server.log.Debug("Skipping organization role mapping.")
    return extUser, nil  // Allow login without role assignment
}
```

**Phoenix** (`ldap.py`):
```python
role = self.map_groups_to_role(groups)
if not role:
    return None  # Always deny if no matching groups
```

**依据**：Phoenix 出于安全考虑，有意不提供 `SkipOrgRoleSync`；每个 LDAP 用户都必须有明确角色分配。

---

<a id="4-role-assignment-strategy"></a>

### 4. 角色分配策略

| 方面 | Grafana | Phoenix | 影响 |
|--------|---------|---------|--------|
| 多组织支持 | ✅ 支持，每个组织独立角色 | ❌ 不支持，单一角色 | ✅ 不适用 |
| 首次匹配优先 | 每个组织 | 全局 | ✅ 等效 |
| 通配符 `"*"` | ✅ 是 | ✅ 是 | ✅ 一致 |

**Grafana** (`ldap.go`):
```go
for _, group := range server.Config.Groups {
    // Only use first match FOR EACH ORG
    if extUser.OrgRoles[group.OrgId] != "" {
        continue
    }
    if IsMemberOf(memberOf, group.GroupDN) {
        extUser.OrgRoles[group.OrgId] = group.OrgRole
    }
}
```

**Phoenix** (`ldap.py`):
```python
for mapping in self.config.group_role_mappings:
    if _is_member_of(canonical_user_groups, group_dn):
        return _validate_phoenix_role(role)  # Return immediately
```

**结果**：单组织使用场景下实际等效，Phoenix 没有多组织概念。

---

<a id="summary-table"></a>

### 汇总表

| 功能 | 一致 | 说明 |
|---------|-------|-------|
| 通配符 `"*"` 支持 | ✅ 一致 | 两者均先检查通配符 |
| 不区分大小写的 DN | ✅ 一致 | Phoenix 更健壮，RFC 4514 |
| 首次匹配优先 优先级 | ✅ 一致 | 两者均按配置顺序遍历 |
| 多服务器故障转移，连接错误 | ✅ 一致 | 两者均继续下一台服务器 |
| 多服务器故障转移，用户不存在 | ⚠️ 不同 | Grafana 继续，Phoenix 停止 |
| 多服务器故障转移，密码错误 | ⚠️ 不同 | Grafana 继续，Phoenix 停止 |
| 无组匹配即拒绝 | ✅ 一致 | 两者均拒绝访问 |
| SkipOrgRoleSync 选项 | ⚠️ 缺失 | Phoenix 有意省略 |
| DN 规范化 | ✅ Phoenix 更佳 | RFC 4514 与简单字符串比较 |

<a id="multi-server-architecture-support"></a>

### 多服务器架构支持

| 架构 | Grafana | Phoenix |
|--------------|---------|---------|
| **副本高可用**，相同服务器 | ✅ 可用 | ✅ 可用，最优 |
| **多域**，不同用户集 | ✅ 可用 | ⚠️ 仅在首台响应服务器上查找用户 |
| **AD 林**，多个域 | ✅ 可用 | ⚠️ 要求所有用户位于主域 |

---

<a id="key-compatibility-findings"></a>

## 主要兼容性发现

<a id="configuration-format"></a>

### 配置格式
- **Grafana**：基于 TOML，使用 `[[servers]]` 块
- **Phoenix**：环境变量，角色映射使用 JSON
- **兼容性**：逻辑结构相同，序列化格式不同

<a id="user-identification"></a>

### 用户识别
- **Grafana**：以 DN 为主要标识符，存于 `user_auth.auth_id`
- **Phoenix**：使用邮箱（简单模式）或 objectGUID 等不可变唯一 ID（企业模式）
- **主要区别**：Phoenix 不使用 DN 匹配身份，因为 DN 变化过于频繁
- **两者均**：支持登录时同步邮箱
- 详情参见[用户识别策略](./user-identification-strategy.md)

<a id="tls-security"></a>

### TLS 安全
- **两者均**：支持 STARTTLS 和 LDAPS
- **关键要求**：两者均要求显式 TLS 升级顺序，参见[协议合规性](./protocol-compliance.md#7-starttls-implementation--security)
- **发现**：Grafana v11.4 存在 STARTTLS 漏洞，已通过对抗性中间人代理测试

<a id="dn-handling"></a>

### DN 处理
- **Grafana**：通过 `strings.EqualFold()` 实现不区分大小写，用于用户识别
- **Phoenix**：仅为组 DN 匹配执行符合 RFC 4514 的规范化
- **主要区别**：Phoenix 不使用 DN 识别用户，而是使用邮箱或 unique_id

<a id="additional-grafana-implementation-patterns"></a>

## 更多 Grafana 实现模式

对影响 Phoenix 实现的 Grafana 特有模式的详细分析参见：

- [配置参考](./configuration.md) — Phoenix 与 Grafana 环境变量映射
- [安全详解](./security.md) — 基于 Grafana 模式的 LDAP 注入防护
- [协议合规性](./protocol-compliance.md) — TLS 安全测试，包含 Grafana v11.4 漏洞发现
- [用户识别策略](./user-identification-strategy.md) — 邮箱/唯一 ID 识别，不使用 DN

**说明**：主规范文档多处包含详细 Grafana 兼容性分析：
- 阶段 0：Grafana 兼容性验证，第 874—908 行
- 附录 A 中的 Grafana 实现详情小节，原文档第 1531—2416 行
- 决策可逆性分析，比较 Grafana 与 Phoenix 决策，第 3933—4383 行

