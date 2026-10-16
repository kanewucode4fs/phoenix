<a id="projectsession"></a>

# 项目会话（ProjectSession）

会话将同一段多轮对话中的追踪记录组织在一起。

<a id="reaching-a-session"></a>

## 获取会话

- `Project.sessions(timeRange, first, after, sort, sessionFilterCondition)` → `ProjectSession` 连接。`sessionFilterCondition` 是会话筛选表达式；通过 `Project.sessionFilterVocabulary` 发现可绑定名称，通过 `Project.validateSessionFilterCondition` 验证条件。面向用户的语法参考（聚合、推导式、标注、根跨度访问）见[筛选表达式](https://arize.com/docs/phoenix/tracing/how-to-tracing/filter-expressions)文档；实际强制的语法见 `internal_docs/specs/session-filter-dsl.md`。
- `getProjectSessionById(sessionId: String!)` → `ProjectSession`：`sessionId` 是原始会话字符串，不是全局 ID。

<a id="fields"></a>

## 字段

- `sessionId`、`startTime`、`endTime`、`project`
- `numTraces`、`numTracesWithError`
- `firstInput { value }`、`lastOutput { value }`
- `tokenUsage { prompt completion total }`：各项均为 `Float`
- `costSummary { total { cost tokens } prompt { cost tokens } completion { cost tokens } }`、`costDetailSummaryEntries`
- `traceLatencyMsQuantile(probability: Float!)`：百分位数字段，不是 `latency`
- `traces(first, after)`：只能向前分页，实际上必须传入 `first`。通过追踪记录的 `rootSpan { name input { truncatedValue } output { truncatedValue } }` 汇总每一轮。
- `sessionAnnotations { name label score }`、`sessionAnnotationSummaries(filter)`

<a id="example"></a>

## 示例

一次请求获取会话汇总指标，并从每条追踪的根跨度读取逐轮摘要。

```graphql
query SessionDetail($id: ID!) {
  node(id: $id) {
    ... on ProjectSession {
      sessionId
      numTraces
      numTracesWithError
      tokenUsage { total }
      costSummary { total { cost tokens } }
      p50: traceLatencyMsQuantile(probability: 0.5)
      traces(first: 20) {
        edges {
          node {
            traceId
            latencyMs
            numSpans
            rootSpan {
              spanId
              name
              statusCode
              input { truncatedValue }
              output { truncatedValue }
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```
