---
name: phoenix-graphql
description: >
  针对 Phoenix API 编写高效 GraphQL 查询。两种情况下加载：（1）自行通过 `phoenix-gql` bash 命令编写非简单数据分析查询之前，本技能提供模式入口和可免除内省的模式；（2）用户需要为自己的脚本、工具或 Phoenix 集成编写 GraphQL 查询时，本技能提供端点、认证和客户端示例。
summary: 使用高效 GraphQL 查询回答数据问题，或为脚本及 Phoenix API 集成提供可运行的 GraphQL。
---

<a id="two-modes"></a>

### 两种模式

- **内部数据分析**：由你查询 Phoenix 来回答问题，直接应用下述模式事实、效率规则和查询模式。
- **帮助用户集成**：用户需要用于自己代码或工具的 GraphQL 查询。除相同的模式事实和查询模式外，还应使用“外部 API 用法”一节的端点、认证和客户端示例。交给用户的查询应使用变量，并处理分页。

<a id="entrypoints"></a>

### 入口

顶层 `Query` 入口用于获取起始实体；各实体的模式细节位于下方“模式索引”列出的参考文件中。

- `node(id: ID!)`：通过 Relay 全局 ID 查找**任意**实体，并用内联片段解析，例如 `node(id: $id) { ... on Dataset { name } }`。这是获取数据集、提示词、实验、会话和标注的主要方式，这些实体**没有**按名称或按 ID 查询的专用辅助方法。
- `projects(...)`、`datasets(...)`、`prompts(...)`、`evaluators(...)` → Relay 连接，均提供 `filter`/`sort` 输入，可在只有名称时查找实体。
- 现有的按属性查询辅助方法只有：`getProjectByName(name: String!)`、`getProjectSessionById(sessionId: String!)`、`getDatasetExampleByExternalId(datasetId: GlobalID!, externalId: String!)`、`getSpanByOtelId(spanId: String!)`、`getTraceByOtelId(traceId: String!)`。**不存在** `getDatasetByName`、`getPromptByName` 或 `getExperimentById`，请改用 `node(id:)` 或连接的 `filter`。
- `viewer` → 已认证的 `User`；`projectCount`、`datasetCount`、`promptCount` 提供低成本计数。
- `compareExperiments(baseExperimentId: GlobalID!, compareExperimentIds: [GlobalID!]!, first, after, filterCondition)` → 实验比较。

<a id="schema-map"></a>

### 模式索引

各实体的字段参考和示例分布在独立参考文件中。加载本技能后，使用 `load_skill_reference` **只加载所需文件**：

- [项目、跨度与追踪](references/project-spans-traces.md)：Project 汇总指标与 `spans`，以及 Span 和 Trace 字段，是多数追踪分析的起点。
- [会话](references/sessions.md)：ProjectSession 多轮会话指标、令牌/费用和会话追踪。
- [数据集](references/datasets.md)：Dataset 和 DatasetExample 的示例、版本、划分和标签。
- [实验](references/experiments.md)：Experiment 和 ExperimentRun 的运行记录、汇总指标和比较。
- [提示词](references/prompts.md)：Prompt 和 PromptVersion 的版本、模板和标签。
- [标注](references/annotations.md)：跨度、追踪、会话、实验运行的标注字段及读取方法，以及写入笔记、标签和标注配置的变更操作。
- [筛选表达式](references/filter-expressions.md)：跨度、追踪、会话的筛选语言（`filterCondition`、`traceFilterCondition`、`sessionFilterCondition`），包含词汇、运算符、根跨度作用域和可编译示例。编写超出下方单行示例的条件前，应先加载。

<a id="conventions"></a>

### 约定

以下规则适用于每种实体：

- **分页**采用 Relay 风格：参数为 `first`/`after`；响应包含 `edges { node { ... } }` 和 `pageInfo { hasNextPage endCursor }`。游标是不透明字符串。部分连接只能向前翻页，如 `Project.spans`、`Experiment.runs` 和 `ProjectSession.traces`。
- **ID**：任意节点的 `id` 字段都是 Relay 全局 ID，即 `TypeName:rowId` 的 base64，配合 `node(id:)` 使用。OpenTelemetry 十六进制 ID 来自 `Span.spanId` 和 `Trace.traceId`，用于 OTel 查询。注意，`Span` **没有** `traceId` 字段，应通过嵌套的 `trace { traceId }` 读取。绝不能混用全局 ID 和 OTel ID。
- **`TimeRange`** 输入：`{ start: DateTime, end: DateTime }`，使用 ISO 8601 字符串；`end` 不包含边界，两者均可选。
- **`SpanSort`** 输入：`{ col: SpanColumn, dir: SortDir }`，例如 `{ col: startTime, dir: desc }`。常用 `SpanColumn` 值有 `startTime`、`latencyMs`、`tokenCountTotal`、`cumulativeTokenCountTotal`、`tokenCostTotal`。
- **筛选条件**（`filterCondition`、`traceFilterCondition`、`sessionFilterCondition`）采用 Python 布尔表达式，跨度、追踪、会话各有一种语言，例如 `span_kind == 'LLM'`、`status_code == 'ERROR'`、`'timeout' in output.value`、`annotations['Hallucination'].label == 'hallucinated'`。没有 `traces` 连接；列出追踪时使用 `parent_span is None`（根跨度，包含孤儿跨度），或使用 `parent_id is None` 查找没有父 ID 的跨度。未知跨度筛选名称会被编译为属性路径并匹配不到任何内容，因此编写条件前应读取 `references/filter-expressions.md`。

<a id="efficiency-rules"></a>

### 效率规则

- **不要执行完整模式内省。** 应读取相关的 `Schema map`（模式索引）资源，其中包含实体的字段和参数。只有资源未覆盖所需字段时，才对单个类型内省：`{ __type(name: "Project") { fields { name args { name type { name kind } } } } }`。
- **在一次查询中通过别名批量执行独立查询**，避免多次往返，例如 `p50: latencyMsQuantile(probability: 0.5) p99: latencyMsQuantile(probability: 0.99)`。
- 只选择所需字段，保持较小分页大小（10–50），仅在必要时翻页。
- 通过查询变量传值，绝不使用字符串插值。文档最多为 2 KiB UTF-8，变量值不计入此限制。
- 跨度的 `input`/`output` 载荷可能很大。概览时请求 `input { truncatedValue }`（前 100 个字符），只有打算仔细阅读的跨度才请求 `input { value }`（完整载荷）。

<a id="patterns"></a>

### 查询模式

以下两种典型结构用于理解基本用法；实体专属示例见各参考资源。

通过 `node(id:)` 和内联片段访问实体并读取字段：

```graphql
query GetEntity($id: ID!) {
  node(id: $id) {
    ... on Dataset { name exampleCount }
  }
}
```

在一次往返中通过别名批量查询独立项目汇总指标：

```graphql
query Overview($name: String!, $timeRange: TimeRange) {
  getProjectByName(name: $name) {
    traceCount(timeRange: $timeRange)
    p50: latencyMsQuantile(probability: 0.5, timeRange: $timeRange)
    p99: latencyMsQuantile(probability: 0.99, timeRange: $timeRange)
    errorCount: recordCount(timeRange: $timeRange, filterCondition: "status_code == 'ERROR'")
  }
}
```

<a id="execution-surfaces-internal-mode"></a>

### 执行方式（内部模式）

- `phoenix-gql`（bash）：运行 `phoenix-gql --help` 查看选项和当前权限。通过管道传给 `jq` 时使用 `--data-only`，大结果使用 `--output <file>`，变量使用 `--vars '<json>'`。只有运行时权限允许时才能执行变更操作，工具每次调用都会报告权限。

<a id="external-api-usage-user-facing-mode"></a>

### 外部 API 用法（面向用户模式）

用户自行调用 API 所需的信息：

- **端点**：`POST <phoenix-endpoint>/graphql`，JSON 请求体为 `{ "query": "...", "variables": { ... } }`，其中 `<phoenix-endpoint>` 是 `PHOENIX_ENDPOINT` 指定的 Phoenix 基础 URL。同一路径的 GET 请求提供 GraphiQL IDE。
- **认证**：将 Phoenix API 密钥作为 Bearer 令牌发送：`Authorization: Bearer <API_KEY>`。API 密钥在 Phoenix 设置中创建。
- GraphQL 模式主要面向 Phoenix 界面，不同版本间可能变化。对稳定的程序化访问，应在能满足需求时推荐 REST API（`/v1/...`）及 `arize-phoenix-client` Python / `@arizeai/phoenix-client` TypeScript 包，其余需求再使用 GraphQL。

curl 示例：

```bash
curl -s "$PHOENIX_ENDPOINT/graphql" \
  -H "Authorization: Bearer $PHOENIX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query($n: String!) { getProjectByName(name: $n) { traceCount } }", "variables": {"n": "default"}}'
```

Python 示例：

```python
import httpx

resp = httpx.post(
    f"{endpoint}/graphql",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"query": query, "variables": variables},
)
resp.raise_for_status()
data = resp.json()["data"]
```

交给用户查询时，应包含带变量定义的完整操作、变量载荷示例，以及分页说明：读取 `pageInfo { hasNextPage endCursor }`，将 `endCursor` 作为 `after` 继续请求。
