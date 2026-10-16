<a id="decision-reversibility-analysis"></a>

# 决策可逆性分析

**框架**：单向门与双向门决策，Amazon/Bezos 框架

**单向门决策**（类型 1）：
- 承诺后很难或无法逆转
- 需要事先仔细分析和审议
- 示例：数据格式、外部 API 契约、向后兼容承诺

**双向门决策**（类型 2）：
- 可通过合理工作量轻松逆转或更改
- 可以快速推进和迭代
- 示例：内部代码结构、通过抽象隔离的库选择、配置方式

---

<a id="decision-by-decision-assessment"></a>

#### 逐项决策评估

**1. 标记格式（`\ue000LDAP(stopgap)`）**

**决策类型**：🚪 **单向门**（类型 1）

**不可逆原因**：
- 生产环境已有 LDAP 用户后，更改标记格式需要重写所有 `oauth2_client_id` 值
- 与真实 OAuth2 客户端 ID 冲突会导致数据损坏
- 对已有 LDAP 用户的向后兼容限制未来变更

**风险缓解**，充分事先校验：
- ✅ Unicode PUA（U+E000-U+F8FF）保证永不被 Unicode 标准分配，永久保证
- ✅ OAuth2 RFC 6749 将 client_id 限制为 ASCII，无法包含 Unicode
- ✅ 已验证实际 OAuth2 提供方，均不使用 Unicode
- ✅ 主动校验拒绝已配置 OAuth2 客户端 ID 中的 PUA 字符

**结论**：单向门，但已充分校验，确保作出正确选择。

---

**2. 允许注册的默认值（`true`）**

**决策类型**：🚪 **单向门**（类型 1）

**不可逆原因**：
- LDAP 以 `allow_sign_up=true` 为默认值发布后，已有用户会依赖此行为
- 后续版本将默认值改为 `false` 会破坏现有部署，自动注册突然失效
- 按自动注册预期部署的组织会遭遇用户投诉
- 配置文件兼容性：无法不破坏语义化版本约定而安全修改默认值

**风险缓解**：
- ✅ 与 Grafana 默认值一致，`conf/defaults.ini` 中为 `allow_sign_up: true`
- ✅ 提供显式停用机制（`PHOENIX_LDAP_ALLOW_SIGN_UP="false"`）
- ✅ 配置参考有完整文档
- ✅ 安全要求高的组织可在首次部署前禁用
- ✅ 单元测试已覆盖（`tests/unit/test_config.py::test_allow_sign_up_parsing`）

**安全考虑**：尽管 `true` 更宽松，仍是正确默认值，因为：
1. **兼容 Grafana**：符合用户预期
2. **最小意外**：LDAP 通常预期自动注册，与 OAuth2 不同
3. **易于收紧**：要求预配置的组织可从第一天设置 `allow_sign_up=false`
4. **通用错误消息**：无论设置如何，仍可防止用户名枚举

**结论**：单向门，但默认值符合行业标准 Grafana，并为安全要求高的部署提供显式停用。

<a id="allow-sign-up-behavior-grafana-vs-phoenix"></a>

#### 允许注册行为：Grafana 与 Phoenix

**Grafana 实现**（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L280-L327)）：

用户通过 LDAP 登录时：
1. **LDAP 身份验证** → 从 LDAP 服务器获取 DN、邮箱、姓名和组（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/ldap.go#L486)）
   ```go
   extUser := &login.ExternalUserInfo{
       AuthModule: login.LDAPAuthModule,
       AuthId:     user.DN,  // Distinguished Name, e.g. "cn=john,ou=users,dc=example,dc=com"
       // ... email, name, groups
   }
   ```

2. **多步骤用户查找**（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L622-L672)）：
   - **步骤 1**：检查 `user_auth` 表中 `auth_id=DN` 和 `auth_module="ldap"`（[第 627—638 行](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L627-L638)）
   - **步骤 2**：未找到时，按邮箱查询 `user` 表（[第 682—687 行](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L682-L687)）
   - **步骤 3**：仍未找到，按登录名或用户名查找（[第 690—695 行](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L690-L695)）
   - **步骤 4**：仍未找到 → `ErrUserNotFound`（[第 697—699 行](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L697-L699)）

3. **未找到用户且 `allow_sign_up=false`** → 拒绝登录（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L296-L298)）：
   ```go
   if errors.Is(err, user.ErrUserNotFound) {
       if !id.ClientParams.AllowSignUp {
           s.log.FromContext(ctx).Warn("Failed to create user, signup is not allowed for module", 
               "auth_module", id.AuthenticatedBy, "auth_id", id.AuthID)
           return errUserSignupDisabled.Errorf("%w", errSignupNotAllowed)
       }
   }
   ```

4. **找到用户时** → 创建或更新 `user_auth` 表，将用户关联 LDAP，并同步属性（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L317-L326)、[第 467 行](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L467)）：
   ```go
   needsConnectionCreation := userAuth == nil  // No existing user_auth record
   // ... update user attributes (email, name, role) ...
   s.upsertAuthConnection(ctx, usr.ID, identity, needsConnectionCreation)
   ```

**关键发现**：Grafana 允许管理员通过**任意身份验证方法**创建用户，例如本地、OAuth2，然后在首次 LDAP 登录时创建 `auth_info` 记录，自动“转换”为 LDAP。

**Grafana 配置**（[源码](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/docs/sources/setup-grafana/configure-access/configure-authentication/ldap/index.md#L40-L52)）：
```ini
[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml
allow_sign_up = true  # Default: true
```
> “启用 LDAP 后，Grafana 默认会在 LDAP 身份验证成功时自动创建用户。若仅希望已有 Grafana 用户能登录，可将 `allow_sign_up` 改为 `false`。”

**Phoenix 实现差异**：

由于零迁移约束，Phoenix **无法**将 LOCAL 用户转换为 LDAP：
- **结构约束**：LOCAL 用户的 `password_hash` 和 `password_salt` 具有 `NOT NULL` 约束
- **存储差异**：LDAP 用户存为 `OAuth2User`，具有 `oauth2_client_id="\ue000LDAP(stopgap)"`
- **无转换路径**：不迁移便无法将 `auth_method` 从 `LOCAL` 改为 `OAUTH2`

**Phoenix 方案**：

| 场景 | Grafana | Phoenix（零迁移） |
|----------|---------|--------------------------|
| **`allow_sign_up=true`**（默认） | 首次 LDAP 登录自动创建用户 | ✅ 相同，通过 `/auth/ldap/login` 自动创建 |
| **`allow_sign_up=false`** | 管理员使用任意验证方法创建用户，LDAP 登录时转为 LDAP | 管理员通过 GraphQL `createUser(auth_method: LDAP)` 创建 |
| **用户查找策略** | 1）`user_auth` 中的 DN，2）邮箱，3）用户名 | **仅邮箱**，权威唯一标识符 |
| **管理员工作流** | 以邮箱和用户名创建 → LDAP 发现属性 | ✅ 相同，以邮箱和 displayName 创建 → LDAP 同步 |
| **邮箱冲突** | 允许转换，同一用户使用不同身份验证 | ⚠️ 拒绝登录，防止劫持 |

**Phoenix 实现**（`src/phoenix/server/api/routers/auth.py`）：

用户通过 LDAP 登录时：
1. **LDAP 身份验证** → 从 LDAP 服务器获取邮箱、姓名和组

2. **直接按邮箱查找**，邮箱是唯一标识符：
   ```python
   # Email lookup (returned from LDAP authentication)
   user = await session.scalar(
       select(models.User)
       .where(models.User.oauth2_client_id == LDAP_CLIENT_ID_MARKER)
       .where(func.lower(models.User.email) == user_info["email"].lower())
   )
   ```

3. **未找到用户且 `allow_sign_up=false`** → 拒绝登录：
   ```python
   if not user:
       if not ldap_config.allow_sign_up:
           raise HTTPException(status_code=401, detail="Invalid username and/or password")
   ```

4. **安全检查**：防止 LDAP 劫持 LOCAL/OAuth2 用户：
   ```python
   # When creating new user (allow_sign_up=true)
   existing_user = await session.scalar(
       select(models.User).where(func.lower(models.User.email) == email.lower())
   )
   if existing_user and existing_user.oauth2_client_id != LDAP_CLIENT_ID_MARKER:
       raise HTTPException(status_code=401, detail="Invalid username and/or password")
   ```

5. **找到用户时** → 更新邮箱、显示名称、角色等属性

**Phoenix 用户创建变更**（`src/phoenix/server/api/mutations/user_mutations.py`）：
```python
if input.auth_method is AuthMethod.LDAP:
    # LDAP users are stored with special Unicode marker
    from phoenix.server.ldap import LDAP_CLIENT_ID_MARKER

    user = models.OAuth2User(
        email=email,  # Unique identifier
        username=input.username,  # Display name (will sync from LDAP)
        oauth2_client_id=LDAP_CLIENT_ID_MARKER,  # Identifies as LDAP
        oauth2_user_id=None,  # NULL until first login (then upgraded to DN)
    )
```

**取舍**：

| 方面 | Grafana（灵活） | Phoenix（零迁移） |
|--------|-------------------|--------------------------|
| **管理员工作流（`allow_sign_up=false`）** | 使用任意验证方法创建用户 → LDAP 登录自动转换 | 必须明确创建为 LDAP 用户 |
| **邮箱回退** | ✅ 支持，未找到 DN 时按邮箱查找 | ✅ 支持，未找到用户名时按邮箱查找 |
| **跨验证方式灵活性** | 用户可从 LOCAL 无缝切换至 LDAP | ❌ 受结构约束，无法切换 |
| **安全** | 灵活，但可能混淆 | 严格，防止意外劫持 |
| **数据库复杂度** | 独立 `user` 和 `user_auth` 表 | 单一 `users` 表，复用 OAuth2 列 |
| **迁移路径** | 已分离 | 之后可迁移至方案 2（[附录 H](#appendix-h-approach-1--2-migration-plan)） |

**Phoenix 方案可接受的原因**：
1. **零迁移 MVP**：无需结构变更，立即满足企业用户
2. **身份验证方法明确**：管理员显式指定 `auth_method: LDAP`，意图更清楚
3. **安全**：防止意外账户劫持，LDAP 无法接管 LOCAL 用户
4. **存在迁移路径**：需要时可在方案 2 采用 Grafana 的灵活模型

**Grafana 参考资料**：
- [用户同步逻辑](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/authn/authnimpl/sync/user_sync.go#L280-L327)
- [LDAP 配置文档](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/docs/sources/setup-grafana/configure-access/configure-authentication/ldap/index.md#L40-L52)
- [LDAP 服务配置](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/service/ldap.go#L96)
- [设置结构](https://github.com/grafana/grafana/blob/84a07be6e4e1acd8f064c3b390c30188d5703afc/pkg/services/ldap/settings.go#L20-L26)

---

**3. 库选择（ldap3）**

**决策类型**：🚪🚪 **双向门**（类型 2）

**可逆原因**：
- `LDAPAuthenticator` 类抽象库细节
- 更换库仅需修改一个模块（`src/phoenix/server/ldap.py`）
- 基于接口的设计尽量减少全库耦合
- 外部 API 不暴露库专有类型

**库质量**，降低更换可能性：
- 符合 RFC
- 活跃维护
- 纯 Python 实现

**结论**：双向门。抽象层保留必要时更换库的灵活性。

---

**4. 环境变量与 TOML 配置**

**决策类型**：**混合**

**配置方式** = 🚪🚪 **双向门**：
- 之后可添加 TOML 文件支持，不破坏环境变量用户
- 优先级顺序：环境变量覆盖文件配置，向后兼容
- 两种配置方式可以同时共存

**环境变量名称** = 🚪 **单向门**：
- 发布后更名属于用户不兼容变更
- 自托管用户会在部署文件和脚本中配置这些名称
- 需要提前谨慎选择

**更改这些变量会破坏什么？**

| 变更 | 用户影响 | 缓解工作量 |
|--------|-------------|-------------------|
| 重命名 `PHOENIX_LDAP_*` → `PHOENIX_AUTH_LDAP_*` | 🔴 **不兼容**：所有用户配置无效 | 高，需要弃用期、文档和迁移指南 |
| 更改 `GROUP_ROLE_MAPPINGS` JSON 结构 | 🔴 **不兼容**：全部角色映射失败 | 高，需要版本检测、自动迁移 |
| 将 `role` 值从大写改为小写 | 🔴 **不兼容**：全部角色映射失败 | 高，除非添加不区分大小写解析 |
| 添加新可选变量 | 🟢 **安全**：向后兼容 | 无，用户逐步采用 |
| 修改默认值，例如 `PORT` 从 389 改为 636 | 🟡 **有风险**：静默行为变化 | 中，发布说明记录，升级时警告 |
| 移除可选变量 | 🔴 **不兼容**：依赖它的用户失败 | 高，需要弃用期 |

<a id="contract-guarantees"></a>

#### 契约保证

**承诺保持的内容**，破坏这些保证需要提升主版本：
1. ✅ 所有 `PHOENIX_LDAP_*` 变量名称保持不变
2. ✅ `GROUP_ROLE_MAPPINGS` JSON 结构与 Grafana `GroupToOrgRole` 一致，去除 `org_id`
   - **单向门**：字段名 `group_dn` 和 `role` 已固定
3. ✅ `role` 值为 **Phoenix 角色**：`"ADMIN"`、`"MEMBER"`、`"VIEWER"`，全大写
   - **单向门**：角色值固定，使用 Phoenix 原生值，而非 Grafana 的“Admin”/“Editor”/“Viewer”
4. ✅ 布尔值使用字符串 `"true"`/`"false"`，不区分大小写
5. ✅ 多服务器格式为 `HOST` 中逗号分隔
6. ✅ 搜索过滤器使用 `%s` 作为用户名或 DN 占位符
7. ✅ 默认值符合 Grafana 生产建议，TLS 开启、校验开启、端口 389、超时 10 秒

**命名校验**：
- ✅ 遵循 Phoenix 约定：`PHOENIX_*` 前缀
- ✅ 名称清晰描述用途：`PHOENIX_LDAP_HOST`、`PHOENIX_LDAP_BIND_DN`
- ✅ 与现有 `PHOENIX_OAUTH2_*` 变量模式一致
- ✅ 使用命名空间：`LDAP_` 前缀防止冲突
- ✅ **与 Grafana 不冲突**：Grafana 不直接使用环境变量，仅在 TOML 文件中通过 `${VAR}` 插值，因此 Phoenix 命名独立

**Grafana 与 Phoenix 配置对比**：

| 方面 | Grafana | Phoenix（MVP 规范） |
|--------|---------|-------------------|
| **主要方式** | TOML 文件（[ldap.toml](https://github.com/grafana/grafana/blob/main/conf/ldap.toml)） | 环境变量 |
| **配置文件指定** | `[auth.ldap] config_file = /etc/grafana/ldap.toml` | `PHOENIX_LDAP_*` 环境变量 |
| **多服务器支持** | 每台服务器独立配置 | 全部服务器共享配置 |
| **组映射** | 原生 TOML 数组 | 环境变量中的 JSON 字符串 |
| **环境变量插值** | ✅ TOML 中的 `${ENV_PASSWORD}` | ✅ 直接使用环境变量 |
| **使用场景** | 异构 LDAP 林 | 仅副本故障转移 |

**已从 Grafana 源码验证**（`pkg/setting/setting.go:1480-1488`、`conf/defaults.ini:987-991`、`pkg/services/ldap/testdata/ldap.toml:10`）：
```ini
# Grafana main config (defaults.ini)
[auth.ldap]
enabled = false
config_file = /etc/grafana/ldap.toml
allow_sign_up = true
```

```toml
# Grafana LDAP config (ldap.toml)
[[servers]]
host = "127.0.0.1"
bind_dn = "cn=admin,dc=grafana,dc=org"
bind_password = '${ENV_PASSWORD}'  # Env var interpolation within TOML
```

**关键发现**：Grafana 不直接使用 `GRAFANA_LDAP_HOST` 之类的环境变量，仅在 TOML 文件内部使用环境变量插值。

**关键限制**：

根据 [ldap_multiple.toml](https://raw.githubusercontent.com/grafana/grafana/84a07be6e4e1acd8f064c3b390c30188d5703afc/conf/ldap_multiple.toml)，Grafana 支持**每台服务器不同配置**：
```toml
[[servers]]
host = "10.0.0.1"
bind_dn = "cn=admin,dc=forest1,dc=com"
[[servers.group_mappings]]
group_dn = "cn=admins,dc=forest1,dc=com"

[[servers]]  # DIFFERENT config!
host = "10.0.0.2"
bind_dn = "cn=admin,dc=forest2,dc=com"
[[servers.group_mappings]]
group_dn = "cn=editors,dc=forest2,dc=com"
```

Phoenix 的环境变量方案**无法**支持此情况，假定所有服务器都是相同副本。

**取舍**：

**方案 A：保留环境变量**，当前规范
- ✅ 与 Phoenix 模式一致，例如 `PHOENIX_OAUTH2_*`
- ✅ 对大多数单 LDAP 服务器用户更简单
- ✅ 容器友好，十二要素应用模式
- ⚠️ **限制**：仅支持副本故障转移，不支持异构服务器
- ⚠️ 组映射为 JSON 字符串，可读性较差
- ✅ 之后可添加 TOML，无不兼容变更

**方案 B：使用 TOML 文件**
- ✅ 完整兼容 Grafana
- ✅ 支持异构服务器
- ✅ 复杂配置更易阅读
- ⚠️ 偏离 Phoenix 模式
- ⚠️ 需要文件管理，例如容器挂载
- ✅ 之后可添加环境变量回退，无不兼容变更

**方案 C：混合**，未来推荐
- MVP 先使用环境变量
- MVP 后添加 TOML 文件支持
- 优先级：`PHOENIX_LDAP_CONFIG_FILE` > 环境变量
- 保持向后兼容

**MVP 建议**：使用环境变量，记录仅支持副本的限制，未来规划 TOML。

**结论**：
- **配置方式**：双向门，先使用环境变量，后加 TOML
- **具体环境变量名称**：单向门，发布时必须正确
- **已记录限制**：多服务器假定为副本，配置相同

---

**5. 方案 1 的语义债务**

**决策类型**：🚪🚪 **双向门**（类型 2）

**可逆原因**：
- 迁移路径直接，方案 1 → 方案 2
- 数据迁移脚本简单，将 `oauth2_client_id` 重写至独立列
- 无向后兼容陷阱，数据库结构和代码均由我们控制
- 协调后可随时执行迁移

**不迁移的语义债务**，延期工作：
- LDAP 用户使用 `auth_method='OAUTH2'`，造成开发者困惑
- 无法使用多态 `LDAPUser` 类
- 列名不反映实际用途
- 代码质量债务累积

**迁移路径**：
1. 添加独立 LDAP 列（`ldap_username`）
2. 回填现有 LDAP 用户
3. 更新代码以使用 `LDAPUser` 多态类
4. 可选清理旧代码路径

**参见**：[附录 H](#appendix-h-approach-1--2-migration-plan)，提供推荐的单事务 Alembic 迁移，以及适用于大型部署的分阶段迁移。

**结论**：双向门。选择方案 1 不会锁定未来选择，代码质量成为优先事项时可随时迁移至方案 2。

---

**6. 无多态 LDAPUser（方案 1）**

**决策类型**：🚪🚪 **双向门**（类型 2）

**可逆原因**：
- 与第 5 项相同，方案 1 → 方案 2
- 添加 `auth_method='LDAP'` 和独立列后，即可添加 `LDAPUser` 类
- 无向后兼容陷阱

**不迁移的架构债务**，延期工作：
- 无法使用多态 `LDAPUser` 类
- 无法使用 `isinstance(user, LDAPUser)` 检查
- 无法使用 `session.query(LDAPUser).all()` 查询
- 与 `LocalUser`/`OAuth2User` 模式不一致

**解决方案**：
- 第 5 项的同一迁移可启用多态
- 添加 `polymorphic_identity="LDAP"` 的 `LDAPUser` 类

**结论**：双向门。之后可随方案 2 迁移添加多态。

---

<a id="overall-decision-analysis"></a>

#### 整体决策分析

**框架汇总**：单向门（类型 1）与双向门（类型 2）决策

| 决策 | 门类型 | 分析 |
|----------|-----------|----------|
| **配置结构** | | |
| 标记格式（`\ue000LDAP(stopgap)`） | 🚪 **单向** | 生产数据存在后，更改格式需要数据迁移。**风险：极低**，已充分验证无冲突 |
| 环境变量名称（PHOENIX_LDAP_*） | 🚪 **单向** | 发布后更名破坏用户配置。**风险：极低**，符合既有 Phoenix 约定 |
| JSON 字段名（`group_dn`、`role`） | 🚪 **单向** | 公共 API 契约。**风险：极低**，Phoenix 使用 `role` 而非 `org_role`，无组织概念 |
| 角色值（ADMIN/MEMBER/VIEWER） | 🚪 **单向** | 配置契约。**风险：极低**，符合 Phoenix 现有角色 |
| **行为契约** | | |
| 通配符“*”匹配所有用户 | 🚪 **单向** | 用户据此配置。**风险：极低** |
| 不区分大小写的 DN 匹配 | 🚪 **单向** | 配置解析行为。**风险：极低**，兼容 Grafana 和 LDAP 标准 |
| 首次匹配优先 | 🚪 **单向** | 决定角色分配。**风险：极低**，兼容 Grafana，文档充分 |
| 显示名称回退邮箱 | 🚪 **单向** | 用户可能依赖。**风险：极低**，合理默认值，已测试 |
| 多服务器逗号分隔格式 | 🚪 **单向** | 解析契约。**风险：极低**，简单标准模式 |
| 过滤器占位符 `%s` 格式 | 🚪 **单向** | 查询构建契约。**风险：极低**，LDAP 工具标准做法 |
| **实现灵活性** | | |
| 库选择（ldap3） | 🚪🚪 **双向** | 抽象层允许更换库，无需修改其他代码。 |
| 环境变量配置方式 | 🚪🚪 **双向** | 之后可增加 TOML/文件配置，同时保留环境变量。 |
| 方案 1 语义债务 | 🚪🚪 **双向** | 可随时通过数据迁移和代码更新迁移至方案 2。 |
| 无多态（方案 1） | 🚪🚪 **双向** | 可通过同一方案 2 迁移添加多态。 |

**关键洞察**：

**单向门决策**，需事先仔细分析：
- **标记格式**（`\ue000LDAP(stopgap)`）：更改需要数据迁移
  - ✅ 充分验证，Unicode PUA 保证、OAuth2 规范分析和实际提供方验证
  - ✅ 主动防御，校验拒绝 OAuth2 客户端 ID 中的 PUA
  - ✅ 风险低，全部证据支持此选择
- **环境变量名称**（`PHOENIX_LDAP_*`）：更改破坏用户配置
  - ✅ 遵循 Phoenix 约定（`PHOENIX_*` 前缀）
  - ✅ 清晰描述性名称符合行业标准
  - ✅ 与现有 `PHOENIX_OAUTH2_*` 模式一致
  - ✅ 风险低，名称标准，未来不太需要改变

**双向门决策**，可迭代改进：
- **其他所有事项**：均可之后更改或扩展
  - 库：通过抽象层替换
  - 配置方式：在环境变量之外添加 TOML 文件配置
  - 数据库结构：未来迁移添加列，方案 1 → 2
  - 代码结构：通过迁移添加多态

**方案 1 与方案 2**：
- **均为双向门**，可从方案 1 迁移至方案 2
- **区别**：架构工作的时间，现在或未来
- **均不锁定选择**：保留未来变更灵活性
- **选择**：发布速度，方案 1；或事先保证代码质量，方案 2

---

<a id="appendix-f-security-deep-dive"></a>

### 附录 F：安全详解
