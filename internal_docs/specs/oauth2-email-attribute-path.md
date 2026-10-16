<a id="oauth2oidc-email-attribute-path-configuration"></a>
# OAuth2/OIDC 邮箱属性路径配置

<a id="problem-statement"></a>
## 问题说明

使用 Microsoft Entra ID（Azure AD）作为 OAuth2 身份提供商时，Phoenix 要求 ID token 包含 `email` 声明。但 Entra ID 用户目录中可能未填充 `mail` 属性。

即使应用注册配置了可选 `email` 声明，用户 `mail` 为空时，token 仍不会包含 `email`。

**当前错误:**
> "Missing or invalid 'email' claim. Please ensure your OIDC provider is configured to include the 'email' scope."

**GitHub 问题:** https://github.com/Arize-ai/phoenix/issues/11065

---

<a id="table-of-contents"></a>
## 目录

1. [问题说明](#problem-statement)
2. [背景](#background)
3. [设计决策](#design-decision)
4. [解决方案](#solution)
5. [实施计划](#implementation-plan)
6. [测试计划](#testing-plan)
7. [运维考虑](#operational-considerations)
8. [已知限制](#known-limitations)
9. [未来考虑](#future-considerations)
10. [汇总](#summary)
11. [参考资料](#references)

---

<a id="background"></a>
## 背景

<a id="azure-ad-claim-analysis"></a>
### Azure AD 声明分析

| 声明 | 说明 | 唯一？ | 邮箱格式？ | 可用性 |
|-------|-------------|---------|---------------|--------------|
| `sub` | OIDC 主体标识符（UUID） | ✅ 全局 | ❌ | ✅ 始终 |
| `email` | 用户邮箱 | ❌ | ✅ | ❌ 可能为空 |
| `preferred_username` | 登录标识符 | ✅ 租户内 | ⚠️ 不保证 | ⚠️ v2.0 + `profile` scope |
| `upn` | 用户主体名称 | ✅ 租户内 | ✅ 始终为 `user@domain` | ⚠️ v2.0 可选声明 |
| `name` | 显示名称 | ❌ | ❌ | ⚠️ `profile` scope |

**关键事实：**

- **`preferred_username` 与 `upn` 是不同声明。** 根据 [Microsoft 文档](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference)，`preferred_username` 可能为邮箱、电话或无固定格式的通用用户名。
- **具体到 Azure AD**，`preferred_username` 通常包含邮箱格式的 UPN，但 OIDC 不保证。
- **UPN 始终为邮箱格式**，因为 Azure AD 要求后缀是有效、已验证且符合 RFC 822 的域，见 [Microsoft Entra UserPrincipalName 填充](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-userprincipalname)。
- **v2.0 token 中的 `upn`** 是[可选声明](https://learn.microsoft.com/en-us/entra/identity-platform/optional-claims-reference)，必须在 Token Configuration 显式配置。
- **`preferred_username` 可用性**：请求 `profile` scope 时，v2.0 token 默认包含，见 [Microsoft ID token 声明参考](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference)。

<a id="grafanas-approach"></a>
### Grafana 的方案

Grafana 通过两种方式处理：

1. **Azure AD 连接器**：硬编码回退到 `preferred_username`：
   ```go
   func (claims *azureClaims) extractEmail() string {
       if claims.Email == "" {
           if claims.PreferredUsername != "" {
               return claims.PreferredUsername
           }
       }
       return claims.Email
   }
   ```

2. **通用 OAuth**：可配置 JMESPath：
   - `email_attribute_path`：提取邮箱的 JMESPath 表达式。
   - `email_attribute_name`：Attributes 映射键名。
   - 自动回退，将 `upn` 解析为邮箱。

---

<a id="design-decision"></a>
## 设计决策

<a id="approaches-considered-and-rejected"></a>
### 考虑过但拒绝的方案

**1. 自动回退链**

```python
# Rejected
for claim in ["email", "preferred_username", "upn"]:
    value = user_claims.get(claim)
    if value and is_valid_email_format(value):
        return value
```

**问题：**
- 将 Azure AD 知识硬编码进 Phoenix。
- IDP 名由用户定义，Phoenix 无法可靠检测 Azure AD。
- 为其他 IDP 引入隐式、意外行为。

**2. 为用户标识符增加独立数据库列**

| 实体 | 示例（Azure AD） | 当前列 |
|--------|-------------------|----------------|
| 主体 ID | `abc123-uuid-...` | `oauth2_user_id` ✅ |
| 登录标识符 | `john.doe@company.onmicrosoft.com`（UPN） | **无** |
| 显示名称 | `John Doe` | `username` ✅ |
| 联系邮箱 | `john.doe@company.com`，可能为空 | `email` |

**问题：** 新增列需要数据库迁移。

**3. 像 LDAP 一样允许空邮箱**

`PHOENIX_LDAP_ATTR_EMAIL` 为空时，LDAP 支持可选邮箱，但会禁用管理员预配置。企业通常需要管理员预创建用户。

<a id="chosen-approach-configurable-jmespath-extraction"></a>
### 选定方案：可配置 JMESPath 提取

**核心理由：** Phoenix 不验证 OAuth2 用户邮箱格式，`email` 列仅要求：
1. 非空字符串。
2. 唯一值。
3. 清理，即去除首尾空白并转小写。

Phoenix 原本接受 IDP 提供的任意值，改变的是信任**哪个声明**，而非**如何验证**。

**为何适用于 Azure AD：**
1. `preferred_username` 非空且唯一，满足列约束。
2. 通常包含邮箱格式的 UPN。
3. 与现有 `GROUPS_ATTRIBUTE_PATH`、`ROLE_ATTRIBUTE_PATH` 模式一致。

**向后兼容说明：** 现在添加邮箱格式验证会破坏兼容性，已有 OAuth2 用户可能存有非邮箱值。本功能遵守现有契约。

---

<a id="solution"></a>
## 解决方案

<a id="configuration"></a>
### 配置

```bash
# JMESPath expression to extract email from claims
# Default: "email" (OIDC standard claim)
PHOENIX_OAUTH2_{IDP}_EMAIL_ATTRIBUTE_PATH=preferred_username
```

<a id="recommended-configuration-for-azure-ad"></a>
### Azure AD 推荐配置

**建议：** 使用 `preferred_username`，无需修改 Azure AD 配置。

| 声明 | Phoenix 配置 | Azure AD 所需配置 |
|-------|----------------|-------------------------|
| `preferred_username` | `EMAIL_ATTRIBUTE_PATH=preferred_username` | ✅ 无，v2.0 token 的 `profile` scope 默认提供 |
| `upn` | `EMAIL_ATTRIBUTE_PATH=upn` | ❌ 必须在 Azure Portal → Token Configuration 添加可选声明 |

**`preferred_username` 前提：**
- Phoenix 默认已请求 `openid email profile`。
- v2.0 token 的 `profile` scope 包含 `preferred_username`。
- 无需修改 scope 或 Azure 配置。

**边界情况：** `preferred_username` 不是邮箱格式，如电话或普通用户名，也会存储，因为 Phoenix 不验证邮箱格式。`mailto:` 可能异常，但登录有效。

<a id="behavior"></a>
### 行为

| 配置 | 使用声明 | 说明 |
|--------------|------------|-------|
| 未设置，默认 | `email` | 标准 OIDC 行为 |
| `=preferred_username` | `preferred_username` | **Azure AD 推荐** |
| `=upn` | `upn` | 需配置 Azure AD 可选声明 |
| `=some.nested.path` | JMESPath 结果 | 用于自定义声明 |

<a id="extraction-logic"></a>
### 提取逻辑

```python
import jmespath
from phoenix.auth import sanitize_email


def extract_email(user_claims: dict, email_attribute_path: str) -> str | None:
    """Extract email from user claims using configured path.

    Args:
        user_claims: Merged claims from ID token and/or UserInfo endpoint
        email_attribute_path: JMESPath expression (default: "email")

    Returns:
        Extracted email string (lowercased), or None if not found/empty
    """
    if not email_attribute_path:
        email_attribute_path = "email"

    value = jmespath.search(email_attribute_path, user_claims)

    if isinstance(value, str) and value.strip():
        return sanitize_email(value)  # trim + lowercase

    return None
```

<a id="case-sensitivity"></a>
### 大小写敏感性

**路径区分大小写：** JMESPath 声明名必须完全一致。`preferred_username` 有效，`Preferred_Username`、`preferredUsername` 无效。

**值转小写：** 所有值通过 `sanitize_email()` 转小写，这是 Phoenix 处理全部邮箱值的现有行为。

**为何安全：** Azure AD 按忽略大小写的方式保证 UPN 唯一，不能同时存在 UPN 为 `User@Domain.com` 和 `user@domain.com` 的用户，见 [LDAP 字符串语法](https://learn.microsoft.com/en-us/windows/win32/adschema/a-userprincipalname)。

**管理员预配置可用：** 管理员使用 `John.Doe@Company.com`，IDP 返回 `john.doe@company.com`，比较前都转小写，能够匹配。

<a id="error-handling"></a>
### 错误处理

提取返回 `None` 时，抛出 `MissingEmailScope`，消息包含配置路径：

```python
email = extract_email(user_claims, config.email_attribute_path)
if not email:
    path = config.email_attribute_path or "email"
    raise MissingEmailScope(
        f"Missing or invalid '{path}' claim. "
        "Please ensure your OIDC provider includes this claim, "
        "or configure PHOENIX_OAUTH2_{IDP}_EMAIL_ATTRIBUTE_PATH."
    )
```

---

<a id="implementation-plan"></a>
## 实施计划

<a id="phase-1-add-configuration"></a>
### 阶段 1：添加配置

**文件：** `src/phoenix/config.py`

```python
@dataclass
class OAuth2ClientConfig:
    # ... existing fields ...
    
    email_attribute_path: Optional[str] = None
    """JMESPath expression to extract email from user claims.
    
    Default: "email" (standard OIDC claim)
    
    For Azure AD/Entra ID without email attribute:
        PHOENIX_OAUTH2_AZURE_AD_EMAIL_ATTRIBUTE_PATH=preferred_username
    """
```

环境变量解析：

```python
email_attribute_path = getenv(
    f"PHOENIX_OAUTH2_{idp_name.upper()}_EMAIL_ATTRIBUTE_PATH",
    None,  # None means use default "email"
)
```

<a id="phase-2-update-extraction-logic"></a>
### 阶段 2：更新提取逻辑

**文件：** `src/phoenix/server/api/routers/oauth2.py`

```python
def _parse_user_info(
    user_info: dict[str, Any],
    email_attribute_path: str | None = None,
) -> UserInfo:
    """Parse and validate user info from OIDC claims."""
    
    path = email_attribute_path or "email"
    email = jmespath.search(path, user_info)
    
    if not isinstance(email, str) or not email.strip():
        raise MissingEmailScope(
            f"Missing or invalid '{path}' claim. "
            "Please ensure your OIDC provider includes this claim."
        )
    email = email.strip()
    
    # ... rest unchanged ...
```

<a id="phase-3-pass-configuration-through"></a>
### 阶段 3：传递配置

**文件：** `src/phoenix/server/api/routers/oauth2.py`

```python
user_info = _parse_user_info(
    user_claims,
    email_attribute_path=oauth2_client.email_attribute_path,
)
```

<a id="phase-4-jmespath-dependency"></a>
### 阶段 4：JMESPath 依赖

JMESPath 已为现有依赖，在 `src/phoenix/server/oauth2.py` 中用于 `GROUPS_ATTRIBUTE_PATH` 和 `ROLE_ATTRIBUTE_PATH`，无需改动。

<a id="phase-5-update-documentation"></a>
### 阶段 5：更新文档

**文件：**
- `docs/`：添加 Azure AD 配置示例。
- 错误消息：包含配置提示。

**文档要点：**
1. 值存储前转**小写**，为现有行为。
2. 管理员预配置不区分大小写。
3. 无破坏性变更，全部 OAuth2 邮箱原本已通过 `sanitize_email()` 转小写。

---

<a id="testing-plan"></a>
## 测试计划

<a id="unit-tests"></a>
### 单元测试

1. **默认行为**：`email_attribute_path=None` 使用 `email`。
2. **自定义路径**：`email_attribute_path="preferred_username"` 正确提取。
3. **嵌套路径**：`email_attribute_path="attributes.email"` 支持 JMESPath。
4. **声明缺失**：抛出带有用消息的 `MissingEmailScope`。
5. **空值**：空串视为缺失。
6. **大小写**：提取值转小写。

<a id="integration-tests"></a>
### 集成测试

1. **模拟 Azure AD**：包含 `preferred_username`，没有 `email`。
2. **管理员预配置**：按 UPN 创建，登录时匹配。
3. **标准 IDP**：默认行为不变。

---

<a id="operational-considerations"></a>
## 运维考虑

<a id="admin-provisioning"></a>
### 管理员预配置

管理员通常知道用户 UPN，因为它就是登录名。使用 `EMAIL_ATTRIBUTE_PATH=preferred_username` 时：

- 使用 UPN 预创建用户，例如 `john.doe@company.onmicrosoft.com`。
- 首次登录按邮箱匹配，此时 `oauth2_user_id` 尚未设置。
- 后续按 `sub` 匹配，存于 `oauth2_user_id`。

**重要：** 必须使用 IDP 返回的精确值。以 `user@company.com` 创建而 IDP 返回 `user@company.onmicrosoft.com` 时，首次登录无法匹配。

<a id="email-routing-smtp"></a>
### 邮件路由（SMTP）

UPN 是身份标识，不保证为联系地址：

- `user@company.onmicrosoft.com`：可能有邮箱，也可能没有。
- `user@company.com`：仅配置邮箱后可用。

**影响：**
- Phoenix 界面的 `mailto:` 可能无效。
- 发往不可路由 UPN 的邮件会退信。
- 与现有 `email` 可能包含不可投递地址的情况无异。

<a id="upn-changes-in-azure-ad"></a>
### Azure AD 中 UPN 变化

因改名或域迁移修改 UPN 时：
- **首次登录之后：** 按存于 `oauth2_user_id` 的 `sub` 匹配，无问题。
- **尚未登录的管理员预创建用户：** 使用旧 UPN 创建时，首次可能无法匹配。

`oauth2_user_id`，即 `sub`，稳定且在首次成功登录后用于匹配，因此可缓解风险。

<a id="changing-configuration-for-existing-deployments"></a>
### 修改已有部署配置

用户已存在后更改 `EMAIL_ATTRIBUTE_PATH`：
- 下次按存于 `oauth2_user_id` 的 `sub` 匹配。
- `email` 更新为新提取值。
- 无数据丢失，但显示邮箱变化。

**邮箱唯一性冲突：** 新值与其他用户邮箱冲突时：
- 捕获 `IntegrityError` 并抛出 `EmailAlreadyInUse`。
- 登录失败，提示 "An account for {email} is already in use"。
- 管理员需删除或更新冲突记录。

<a id="rollback-scenario-critical-limitation"></a>
### 回滚场景（严重限制）

**场景：**
1. 使用 `EMAIL_ATTRIBUTE_PATH=preferred_username` 部署。
2. 用户登录，设置 `oauth2_user_id`，邮箱列保存 UPN。
3. 回滚配置，移除 `EMAIL_ATTRIBUTE_PATH`，默认使用 `email`。
4. 用户再次登录。
5. **用户无法登录。**

**原因：** 当前流程在查找用户**之前**解析用户信息，包括提取邮箱：

```python
# Current flow in oauth2.py
user_info = _parse_user_info(user_claims)  # ← Fails here if email claim is null
# Never reaches user lookup by oauth2_user_id
```

邮箱提取失败时，尚未按 `oauth2_user_id` 匹配，就抛出 `MissingEmailScope`。

**替代方法：**
1. `email` 仍为空时**不要回滚**，这是配置存在的原因。
2. 回滚前**修复 IDP**，填充 `email`。
3. **手动更新数据库**，若已知真实邮箱，将用户邮箱改回。

**未来考虑：** 先按 `oauth2_user_id` 查找，仅新用户要求提取邮箱，使配置变更更可逆。

<a id="per-idp-configuration"></a>
### 按 IDP 配置

各 IDP 可采用不同设置：

```bash
PHOENIX_OAUTH2_GOOGLE_EMAIL_ATTRIBUTE_PATH=email          # default
PHOENIX_OAUTH2_AZURE_AD_EMAIL_ATTRIBUTE_PATH=preferred_username  # custom
```

<a id="azure-ad-v10-endpoints"></a>
### Azure AD v1.0 端点

Microsoft Entra ID 有两版 OIDC 端点：
- v1.0：`https://login.microsoftonline.com/{tenant}/oauth2/authorize`
- v2.0：`https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`

使用 v1.0，即 URL 不含 `/v2.0/` 时：
- 默认不提供 `preferred_username`。
- 可选方案：
  1. 在 Azure Portal 添加 `preferred_username` 可选声明。
  2. 改用 `upn`，也需可选声明配置。
  3. 迁移到 Microsoft 推荐的 v2.0 端点。

---

<a id="known-limitations"></a>
## 已知限制

<a id="critical"></a>
### 严重限制

1. **配置回滚导致无法登录**：启用 `EMAIL_ATTRIBUTE_PATH` 并有用户登录后，在 `email` 仍为空时回滚会锁住用户。见[回滚场景](#rollback-scenario-critical-limitation)。

2. **配置变化引发邮箱冲突**：新值与其他用户邮箱相同，登录报错 "An account for {email} is already in use."，需管理员手动解决。

<a id="semantic"></a>
### 语义

3. **`email` 列可能存非邮箱值**：实际为用户标识字段，后续开发者可能误以为是邮箱格式。

4. **界面标签为 Email**：用户在 Email 字段看到 UPN，可能困惑。

<a id="integration"></a>
### 集成

5. **外部集成可能失效**：导出到要求有效邮箱的系统时，可能验证失败。

<a id="configuration"></a>
### 配置

6. **JMESPath 配置错误**：拼写或语法错误静默失败，视为缺失声明。错误应明确尝试的路径。

7. **JMESPath 返回非字符串**：数组、对象等非字符串值视为缺失。

---

<a id="future-considerations"></a>
## 未来考虑

<a id="email_attribute_pathnull-optional-email"></a>
### `EMAIL_ATTRIBUTE_PATH=null`（可选邮箱）

对于完全没有类邮箱声明的 IDP：

```bash
PHOENIX_OAUTH2_{IDP}_EMAIL_ATTRIBUTE_PATH=null
```

**行为：**
- 复用 LDAP 基础设施，生成空邮箱标记。
- 要求 `ALLOW_SIGN_UP=True`，禁用管理员预配置。
- 仅按 `sub`（`oauth2_user_id`）匹配。

**为何暂缓：** 原问题 #11065 针对始终有 UPN 的 Azure AD，`EMAIL_ATTRIBUTE_PATH=preferred_username` 已解决。`=null` 用于更少见边界情况。

<a id="username-attribute-path"></a>
### 用户名属性路径

曾考虑 `USERNAME_ATTRIBUTE_PATH`，但暂缓：
- 当前 `name` 提取适合多数场景。
- 已有用户名冲突处理，采用随机后缀。
- 出现需求时再加。

---

<a id="summary"></a>
## 汇总

| 方面 | 决定 |
|--------|----------|
| **方案** | 可配置 JMESPath 提取 |
| **配置** | `PHOENIX_OAUTH2_{IDP}_EMAIL_ATTRIBUTE_PATH` |
| **默认** | `"email"`，OIDC 标准、向后兼容 |
| **Azure AD 方案** | 设为 `preferred_username`，无需 Azure 配置 |
| **值处理** | `sanitize_email()` 转小写，现有行为 |
| **验证** | 无，OAuth2 邮箱不验证格式 |
| **管理员预配置** | 可用，UPN 租户内唯一 |
| **复杂度** | 低，沿用 `GROUPS_ATTRIBUTE_PATH` 模式 |

---

<a id="references"></a>
## 参考资料

- GitHub 问题: https://github.com/Arize-ai/phoenix/issues/11065
- Grafana 通用 OAuth: https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/generic-oauth/
- Grafana Azure AD: https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/azuread/
- Microsoft Entra ID 声明: https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference
- Microsoft UPN 填充: https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-userprincipalname
- LDAP 字符串语法（大小写敏感性）: https://learn.microsoft.com/en-us/windows/win32/adschema/a-userprincipalname
- LDAP 可选邮箱设计: [./ldap-authentication/optional-email.md](./ldap-authentication/optional-email.md)
