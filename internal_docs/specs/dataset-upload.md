<a id="dataset-upload-rest-api"></a>
# 数据集上传 REST API

作者：@xandersong

<a id="what-we-built"></a>
## 已实现的功能

`POST /v1/datasets/upload` REST 端点接受三种显式操作：`create`、`append` 和 `update`。每种操作对“同名数据集已存在时怎么办”都有不同语义，不存在隐藏模式标志。

<a id="key-components"></a>
### 关键组件

| 组件 | 位置 | 用途 |
|---|---|---|
| 插入逻辑 | `src/phoenix/db/insertion/dataset.py` | 差异算法、批量数据库写入 |
| REST 路由器 | `src/phoenix/server/api/routers/v1/datasets.py` | 将操作分派到插入层 |
| 内容哈希 | `src/phoenix/utilities/content_hashing.py` | 对规范化 JSON 计算 SHA-256 以去重 |
| JCS 内置第三方库 | `src/phoenix/vendor/json_canonicalization_scheme/` | RFC 8785 JSON 规范化方案 |
| 数据库迁移 | `src/phoenix/db/migrations/versions/575aa27302ee_dataset_upsert.py` | 添加 `external_id` 和 `content_hash` 列 |

<a id="api-surface"></a>
### API 接口

```
POST /v1/datasets/upload
Content-Type: application/json

{
  "action": "create" | "append" | "update",
  "name": "my-dataset",
  "inputs": [...],
  "outputs": [...],
  "metadata": [...],
  "example_ids": [...],    // optional, enables stable identity matching
  "splits": [...]           // optional
}
```

各操作的行为：

- **create**：同名数据集已存在时返回 **409**。否则创建数据集，并将全部传入示例作为 CREATE 修订插入。
- **append**：向已有数据集添加传入示例，数据集不存在时自动创建。对最新版本按 `external_id` 或内容哈希去重；匹配示例内容变化时执行更新。绝不删除已有示例。
- **update**：与最新版本进行声明式对账，按需创建、修改或删除示例，使数据集收敛到传入载荷。不存在时自动创建。仅在实际发生变化时生成新版本。

两个 SDK 客户端，即 Python / JS 的 `arize-phoenix-client`，在底层 `action` 参数中仅提供 `update` 和 `append`。`create` 仅用于 REST，由 Phoenix 界面的“创建数据集”按钮使用，以获得 409 冲突保护行为。

<a id="client-fallback-for-older-servers"></a>
### 客户端对旧服务端的回退

客户端向本次变更之前的 Phoenix 服务端（v15 之前）发送 `action=update` 时，服务端返回 **422**，响应体为 `"Invalid dateset action: update"`，其中拼写错误来自服务端枚举错误。客户端检测到这一特定响应后，会警告用户升级到 Phoenix v15 或更新版本，并自动以 `action=create` 重试同一请求。在旧服务端，默认 `strict=false` 的 `action=create` 采用宽松的更新或插入行为，因此回退保留声明式语义，但不具备名称冲突时返回 409 的保护。

<a id="why-we-built-it"></a>
## 实现原因

<a id="the-problem"></a>
### 问题

本次变更前，只有 `create`（直接插入）和 `append`（直接追加）两种写操作，无法：

1. **删除示例**：移除不再相关的示例。
2. **更新示例**：内容变化时更新而不产生重复。
3. **避免空版本**：数据集实际未变时不创建空版本。

从标注工具、数据流水线或 CI 等外部来源维护数据集的团队，需要声明式“期望状态”原语：“这是数据集现在应有的样子，请计算发生了哪些变化。”这就是 `update`。

与此同时，交互式界面流程需要明确的安全行为：“我要创建新数据集，如果名称已被占用，请阻止我。”这就是 `create`。

<a id="design-goals"></a>
### 设计目标

- **幂等**：同一 `update` 载荷上传两次，不产生新版本或重复数据。
- **最小差异**：仅实际变化的示例生成新修订记录，保持存储和审计历史简洁。
- **两种匹配策略**：调用方可使用稳定 `external_id` 显式标识，也可回退到内容哈希进行隐式去重。
- **一种行为对应一个动词**：没有隐藏模式标志。

<a id="how-it-works"></a>
## 工作原理

<a id="content-hashing"></a>
### 内容哈希

将各示例的 `input`、`output` 和 `metadata` 字典合为单个对象 `{"input": ..., "metadata": ..., "output": ...}`，通过 JSON 规范化方案（RFC 8785，不依赖键顺序、数值格式确定）序列化，再计算 SHA-256。哈希保存在修订行的 `content_hash` 列，用于匹配。

特性：

- 确定性：逻辑内容相同，哈希始终相同。
- 与键顺序无关：`{"a": 1, "b": 2}` == `{"b": 2, "a": 1}`。
- 对列表顺序敏感：`[1, 2, 3]` != `[3, 2, 1]`。
- 仅 `input`/`output`/`metadata` 参与计算；`splits`、`span_id`、`external_id` 不影响哈希。

<a id="diff-algorithm-_diff_examples"></a>
### 差异算法（`_diff_examples`）

给定传入示例和上一版本示例及其 `external_id`、`content_hash`，按两级优先级匹配：

1. **external_id 匹配**，优先级最高：传入示例有 `external_id`，且旧示例具有同一值时，无论内容如何均配对。
2. **content_hash 匹配**：无 external_id 匹配时，配对第一个尚未匹配且内容哈希相同的旧示例。
3. **无匹配**：传入示例为新示例。

匹配后的分类：

| 传入示例 | 旧示例 | 结果 |
|---|---|---|
| 已匹配，哈希相同 | — | **不变**，无新修订，隐式沿用 |
| 已匹配，哈希不同 | — | **PATCH** 修订 |
| 无匹配 | — | **CREATE** 修订，新示例行加修订 |
| — | 未匹配 | **DELETE** 修订，`append` 时跳过 |

不存在创建、修改或删除时，复用最新版本 ID，不创建新版本。

<a id="split-handling"></a>
### 划分处理

根据请求是否提供划分，采用两种模式：

- **splits_provided=True**：对于 `create` 和 `update`，删除数据集全部现有划分分配，并根据传入示例重建。对于 `append`，仅重建本次涉及示例的分配，未涉及示例保留现有划分。
- **splits_provided=False**：保留仍存在示例的划分分配，仅删除的示例失去分配。

<a id="schema-changes"></a>
### 数据库结构变更

迁移添加两列：

- `dataset_examples.external_id`：VARCHAR，可空；`(dataset_id, external_id)` 上具有唯一约束，每个数据集中每个 external_id 最多对应一个示例。
- `dataset_example_revisions.content_hash`：VARCHAR，可空；保存 SHA-256 十六进制摘要，并建立索引以便高效查找。

<a id="edge-cases"></a>
## 边界情况

<a id="duplicate-example_ids-in-a-single-request"></a>
### 单个请求中 example_ids 重复

任何数据库写入之前以验证错误拒绝。REST 层通过 `Counter` 检查重复，任意 example_id 出现多次即返回 422。

<a id="create-on-an-existing-name"></a>
### 对已存在名称执行 `create`

抛出 `DatasetNameConflictError` → **409**。请求在任何写入前被拒绝，不留下部分状态。

<a id="update-or-append-on-a-non-existent-dataset"></a>
### 对不存在的数据集执行 `update` 或 `append`

先创建数据集，再将全部传入示例作为 CREATE 处理，因为没有旧版本可比较。

<a id="two-incoming-examples-with-identical-content-but-no-external_id"></a>
### 两个传入示例内容相同，但没有 external_id

第一个通过内容哈希匹配已有示例，保持不变。第二个找不到尚未匹配的旧示例，被分类为 CREATE。这是正确行为：算法通过 `already_matched` 集合跟踪已经匹配的旧示例。

<a id="external_id-present-on-incoming-but-not-on-previous-or-vice-versa"></a>
### 传入示例有 external_id，而旧示例没有，或反过来

匹配平稳降级：传入示例有 external_id，但没有旧示例共享该值时，尝试内容哈希匹配。旧示例有 external_id，但没有传入示例引用它时，该旧示例未匹配：`update` 下变为 DELETE，`append` 下忽略。

<a id="re-adding-a-previously-deleted-example-with-same-external_id"></a>
### 重新添加已删除示例，external_id 相同

复用已有 `dataset_example` 行，通过 `_get_existing_example_ids` 查找，不创建重复行。在已有示例行上附加新的 CREATE 修订。

<a id="empty-update-payload"></a>
### 空 `update` 载荷

全部旧示例变为 DELETE，等效于清空数据集，并创建包含对应 DELETE 修订的新版本。

<a id="missing-span_ids"></a>
### 缺少 span_ids

记录警告，示例不关联 span。由于 span 链接可选，这不是致命错误。

<a id="race-conditions-in-split-creation"></a>
### 创建划分时的竞态条件

通过 `ON CONFLICT DO NOTHING` 处理，避免并发请求创建同名划分时失败。

<a id="length-mismatches"></a>
### 长度不一致

REST 层验证 `inputs`、`outputs`、`metadata`、`splits`、`span_ids` 和 `example_ids` 数组在提供时长度相同。不一致返回 422。

<a id="no-op-update-content-unchanged"></a>
### 无操作 `update`，内容未变

全部传入示例与旧示例匹配且哈希相同时，不创建新版本。响应返回现有最新版本 ID，各计数为零。

<a id="future-work"></a>
## 后续工作

<a id="batch-patchdelete-revisions"></a>
### 批量 PATCH/DELETE 修订

目前 PATCH 和 DELETE 修订通过 `insert_dataset_example_revision` 逐条插入。大型数据集变化较多时应批量处理；CREATE/APPEND 路径已经有批量插入函数。

<a id="partial-merge-semantics"></a>
### 部分合并语义

`update` 是全量替换：旧版本中不在传入批次里的示例均被删除。可新增 `merge` 操作，只新增或更新而不删除，适用于仅掌握部分示例的增量流水线。

<a id="streaming--chunked-upload"></a>
### 流式或分块上传

对于超过 100k 示例的超大型数据集，流式上传协议可避免把全部载荷加载到内存。

<a id="content-hash-on-legacy-data"></a>
### 旧数据的内容哈希

在内容哈希迁移前创建的数据集，其哈希为 `NULL`。回填迁移或惰性计算策略可使 `update` 适用于旧数据集，无需一次性重新计算。

<a id="webhook--event-notifications"></a>
### Webhook 或事件通知

将数据集变化事件，包括创建、修改和删除，发布到事件总线或 webhook，可使下游系统响应数据集更新，例如触发重新评估。
