<a id="attribute-based-access-control"></a>
# 基于属性的访问控制

> **状态：仅设计，暂缓。** 下述数据模型已经确定，但 ABAC **不是**下一项工作。
> 它依赖目前尚不存在的资源属性基础设施（见前置条件）。
> 应先交付 [RBAC](./rbac.md)。

<a id="summary"></a>
## 概述

[声明式 RBAC](./rbac.md) 通过全局角色回答“该用户能在 Phoenix 中做什么？”。
ABAC 在此基础上匹配用户和资源的属性，回答“该用户能对**这个**资源做什么？”。

用户具有 `team`、`department` 或 `environment` 等属性，资源也具有相同属性。
授权可以要求这些属性匹配，例如仅当用户的 `team` 等于项目的 `team` 时授予
`project:update`，从而让一个角色在多个资源上授予恰当权限，无需为每个团队制定策略。

ABAC 建立在 RBAC 之上，并不替代 RBAC。角色仍定义用户拥有**哪些**
`entity:operation` 权限；ABAC 补充定义各项权限适用于**哪些资源**。

<a id="goals"></a>
## 目标

- 将权限限定为属性与用户匹配的资源。
- 原样复用 RBAC 权限目录。
- 新增用户、团队和资源时无需编辑已有角色。

<a id="non-goals"></a>
## 非目标

- 替代 RBAC 角色或全局授权。
- 通用策略语言，包括布尔逻辑、拒绝规则及允许/拒绝优先级。
  Phoenix 保留 RBAC 的累加授权模型：条件只缩小访问范围，不产生拒绝规则。
- 引入 RBAC 和外部认证现有能力之外的属性来源。

<a id="prerequisites"></a>
## 前置条件

ABAC 比较用户属性与资源属性，但 **Phoenix 资源目前没有属性**：
`projects` 没有所有者、创建者或团队列，数据集和提示词也没有。
目前既无可匹配的属性，也无可继承的来源。实现 ABAC 前需要：

1. **资源属性基础设施。** 资源需要存放带类型属性的位置及其取值来源。
   最可能的方案是在创建时记录 `created_by`，据此继承属性，并提供通用属性/标签存储。
2. **现有资源的迁移方案。** 所有已有资源都没有标签。严格条件
   `user.team == resource.team` 会拒绝所有缺少 `team` 的资源（null 不匹配任何值），
   因此启用后全部未标记资源都会突然不可见。“缺失时匹配”条件行为（见求值）提供了
   过渡办法，但具体回填计划仍属于该基础设施的职责，本文不假定其已经存在。

在这些条件具备之前，本规格只是设计参考，而非实施计划。

<a id="model"></a>
## 模型

<a id="attributes"></a>
### 属性

属性是用户或资源上带类型的键值对，例如 `team=ml-platform`。
属性键由 Phoenix 管理；值来自用户、资源以及外部认证（OAuth/LDAP）映射。

键示例：

- `environment` — `production`, `staging`, `dev`
- `team` — `ml-platform`, `growth`
- `department` — `engineering`, `research`

在资源上，这些属性采用**标签**形式，即用户为资源指定的键值标签
（标签存储是最可能采用的具体基础设施，见前置条件）。自身没有标签的资源从父级继承：
追踪的属性就是所属项目的标签，因此 `trace:read` 针对父项目求值，无需给每条追踪打标签。

例如，仅当 `user.environment == resource.environment` 时授予 `trace:read`，
就能用一个角色让每位用户仅访问自己环境中的数据。

<a id="conditions"></a>
### 条件

条件附加在**授权**上，即 RBAC 的 `(role, permission)` 关联，而非角色或权限目录条目。
这样同一角色可以只在 `user.team == resource.team` 时拥有 `project:update`，
同时保持 `project:read` 为全局权限。如果条件放在角色上，会强迫全部权限共用一个谓词；
如果放在目录上，则该权限在所有使用位置都会受条件约束。

- 仅当 `user.team == resource.team` 时授予 `project:update`
- 仅当 `user.department == resource.department` 时授予 `dataset:read`

相等比较最常见，但条件不限于此：比较可以忽略大小写，也可让值匹配 glob 模式
（如 `environment` 匹配 `prod-*`），使一个条件覆盖一组相关标签值，无需为每个值单独授权。

无条件授权与 RBAC 完全相同，保持全局有效。内置角色没有可编辑的授权行，
因此始终为全局授权；只有自定义角色带有条件。

<a id="evaluation"></a>
### 求值

授权先解析 RBAC 授权（角色是否拥有该权限），再针对目标资源计算条件。
两者都必须通过。无条件时，全局授权直接生效。

资源缺少条件指定的属性时，行为由各条件独立设置，而不是全局设置：

- **strict（严格）**：缺少属性时条件不通过，拒绝访问该资源。
  这是默认行为，提供严格隔离：`user.team == resource.team` 会隐藏所有未标记资源。
- **match-if-absent（缺失时匹配）**：缺少属性时条件通过，回退为全局授权。
  这样在回填标签期间已有未标记资源仍然可见，避免启用一个条件就突然隐藏全部资源
  （见前置条件）。

逐条件选择行为是迁移的调节手段：先以 match-if-absent 发布条件，回填标签，
再将需要严格隔离的条件收紧为 strict。

<a id="open-questions"></a>
## 待解决问题

- 首先发布哪些属性键，其值来自哪里？
- 上线时哪些条件默认为 strict，哪些默认为 match-if-absent？如何为现有资源回填标签？
