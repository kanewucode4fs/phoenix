<a id="project-span-trace"></a>

# 项目、跨度与追踪（Project、Span、Trace）

<a id="project"></a>

## 项目（Project）

- `Project.spans(first, after, timeRange, sort: SpanSort, filterCondition: String, traceFilterCondition: String)` → `Span` 连接。**`Project` 上没有 `traces` 连接**，也没有根跨度参数。应使用 `spans(filterCondition: "parent_span is None")` 列出追踪记录，它保留根跨度，包括父跨度从未收到的孤儿跨度，与界面追踪表使用的查询一致，通常每条追踪一个；`parent_id is None` 只保留没有父 ID 的跨度。结合 `traceFilterCondition` 可保留匹配追踪的根跨度。
- `Project.trace(traceId: ID!)` → `Trace`：按 OTel 十六进制追踪 ID 查询。
- 汇总指标多数接收 `timeRange` 和 `filterCondition`：`traceCount`、`recordCount`（跨度数）、`tokenCountTotal`、`tokenCountPrompt`、`tokenCountCompletion`、`costSummary`、`latencyMsQuantile(probability: Float!)`、`spanLatencyMsQuantile(probability: Float!)`。
- 发现字段：`spanAnnotationNames`、`traceAnnotationNames`、`spanAnnotationSummary`、`documentEvaluationNames`，查询前先检查存在哪些评估或标注。
- `validateSpanFilterCondition(condition: String!)`：只检查筛选字符串，不运行查询。
- `filterCondition` 是跨度筛选表达式，`traceFilterCondition` 是追踪筛选表达式。两种语言均定义在 `references/filter-expressions.md` 中，包含词汇、运算符、根跨度作用域和可编译示例。

<a id="span"></a>

## 跨度（Span）

主要字段：`spanId`（OTel 十六进制 ID）、`name`、`spanKind`、`statusCode`、`startTime`、`latencyMs`、`cumulativeTokenCountTotal`、`input { truncatedValue value }`、`output { truncatedValue value }`、`spanAnnotations { name label score }`、`trace { traceId }`。**`Span` 没有 `traceId` 字段**，应通过嵌套的 `trace { traceId }` 读取 OTel 追踪 ID。

<a id="trace"></a>

## 追踪（Trace）

主要字段：`traceId`、`latencyMs`、`numSpans`、`rootSpan { ... }`（代表性根跨度，即最早的无父跨度，或父跨度从未收到的跨度，可用作一行式轮次或追踪摘要）、`spans(first, after, filterCondition)`、`projectSessionId`。

<a id="examples"></a>

## 示例

最近的根跨度，通常每条追踪一个，按耗时从长到短排列：

```graphql
query RecentTraces($id: ID!, $first: Int = 20) {
  node(id: $id) {
    ... on Project {
      spans(first: $first, filterCondition: "parent_span is None", sort: { col: latencyMs, dir: desc }) {
        edges {
          node {
            spanId
            name
            latencyMs
            statusCode
            startTime
            cumulativeTokenCountTotal
            trace { traceId numSpans }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```

时间窗口内出错追踪记录的根跨度：

```graphql
query ErroredTraces($id: ID!, $timeRange: TimeRange) {
  node(id: $id) {
    ... on Project {
      spans(
        first: 20
        timeRange: $timeRange
        filterCondition: "parent_span is None"
        traceFilterCondition: "error_count > 0"
      ) {
        edges { node { name latencyMs input { truncatedValue } trace { traceId } } }
      }
    }
  }
}
```

筛选跨度，例如出错的 LLM 跨度：

```graphql
query ErrorSpans($id: ID!) {
  node(id: $id) {
    ... on Project {
      spans(first: 20, filterCondition: "span_kind == 'LLM' and status_code == 'ERROR'") {
        edges { node { spanId name statusCode trace { traceId } } }
      }
    }
  }
}
```
