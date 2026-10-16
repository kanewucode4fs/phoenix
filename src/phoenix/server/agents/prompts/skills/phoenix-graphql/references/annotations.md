<a id="annotations"></a>

# 标注

标注由人工、代码或 LLM 裁判添加到跨度、追踪记录、会话或实验运行上，包含具名标签或分数。**笔记**是保留名称为 `note` 的标注，正文位于 `explanation`；下文列出了专用笔记变更操作。

<a id="fields"></a>

## 字段

`SpanAnnotation` 和 `TraceAnnotation` 共享以下字段：

- `name`、`label`、`score`、`explanation`
- `annotatorKind`（`AnnotatorKind` 枚举：human / LLM / code）
- `metadata`、`identifier`、`createdAt`、`updatedAt`

`SpanAnnotation` 还包含 `spanId: GlobalID!` 和 `span`；`TraceAnnotation` 包含 `trace`，但没有 `traceId` 全局 ID 字段。`ProjectSessionAnnotation` 具有相同的标量结构。

`ExperimentRunAnnotation` 具有相同标量结构，并增加 `error: String`，使用 `startTime`/`endTime` 替代 `createdAt`/`updatedAt`。

<a id="reading-annotations"></a>

## 读取标注

- 按跨度：`Span.spanAnnotations { name label score explanation annotatorKind identifier }`；只读取笔记时使用 `Span.spanNotes { explanation identifier }`。
- 按追踪或会话：`Trace.traceAnnotations { ... }` 和 `ProjectSession.sessionAnnotations { ... }`；笔记是 `name == "note"` 的条目。
- 项目范围的发现和汇总：`Project.spanAnnotationNames`、`Project.spanAnnotationSummary`、`Project.traceAnnotationNames`、`Project.traceAnnotationSummary`；深入查询前先用这些字段了解已有标注名称。
- 在跨度 `filterCondition` 中，通过 `annotations['<name>'].label` / `.score` / `.explanation` 引用跨度标注，旧形式为 `evals['<name>']`。单独使用 `annotations['<name>']` 检查是否存在。
- 使用 `trace_annotations['<name>'].label` / `.score` / `.explanation` 引用追踪标注，也可用不带属性的形式检查是否存在。匹配时返回属于该标注追踪的跨度；在同一条件中添加 `parent_id is None` 可只返回根跨度。

<a id="example"></a>

## 示例

LLM 裁判标为幻觉的跨度，并附标注详情：

```graphql
query Hallucinations($id: ID!) {
  node(id: $id) {
    ... on Project {
      spans(first: 20, filterCondition: "annotations['Hallucination'].label == 'hallucinated'") {
        edges {
          node {
            spanId
            spanAnnotations { name label score explanation }
          }
        }
      }
    }
  }
}
```

带有较差质量标注的追踪记录的根跨度：

```graphql
query PoorQualityTraces($id: ID!) {
  node(id: $id) {
    ... on Project {
      spans(
        first: 20
        filterCondition: "parent_id is None and trace_annotations['quality'].label == 'poor'"
      ) {
        edges { node { spanId name trace { traceId } } }
      }
    }
  }
}
```

<a id="writing-notes"></a>

## 写入笔记

笔记是自由文本观察，每类实体有独立变更操作。每个输入只能通过 OpenTelemetry ID 或 Phoenix 节点 ID **二选一**指定实体，不能同时使用，并提供正文、`annotatorKind`（自己的判断使用 `LLM`，只有用户提供的判断才使用 `HUMAN`）、`source: API` 和可选 `identifier`。对同一实体再次传入相同 `identifier` 会更新或插入该笔记，不会新增第二条；省略时每次都会创建新笔记。

- `createSpanNotes(input: [CreateSpanNoteInput!]!)`：`{ span: { otelId } | { id }, note, annotatorKind, source, identifier }`
- `createTraceNotes(input: [CreateTraceNoteInput!]!)`：`{ trace: { otelId } | { id }, note, annotatorKind, source, identifier }`
- `createProjectSessionNotes(input: [CreateProjectSessionNoteInput!]!)`：`{ session: { sessionId } | { id }, note, annotatorKind, source, identifier }`，其中 `sessionId` 是应用原始的 `session.id`

```graphql
mutation NoteTrace($traceId: String!, $note: String!, $identifier: String!) {
  createTraceNotes(
    input: [{ trace: { otelId: $traceId }, note: $note, annotatorKind: LLM, source: API, identifier: $identifier }]
  ) {
    traceAnnotations { id name explanation identifier }
  }
}
```

变更操作同步执行，响应返回时记录已存在。传入多个输入可在一次调用中批量处理多个实体。

<a id="writing-labels"></a>

## 写入标签

带标签的标注包含 `name`（维度）和 `label`（结果），以及可选 `score`、`explanation`。输入**仅接受 Phoenix 节点 ID**，因此采样时读取 `id`，而非 OTel 十六进制 ID；并且必须提供 `metadata`，可传 `{}`。

- `createSpanAnnotations(input: [CreateSpanAnnotationInput!]!)`：`{ spanId, name, label, score, explanation, annotatorKind, source: API, metadata: {}, identifier }`
- `createTraceAnnotations(input: [CreateTraceAnnotationInput!]!)`：结构相同，但使用 `traceId`
- `createProjectSessionAnnotations(input: CreateProjectSessionAnnotationInput!)`：结构相同，但使用 `projectSessionId`；接收单个输入，而非列表

写入按 `(entity, name, identifier)` 更新或插入。`patchSpanAnnotations` / `patchTraceAnnotations` 按节点 ID 编辑现有标注；`deleteSpanAnnotations`、`deleteTraceAnnotations`、`deleteProjectSessionAnnotations` 按节点 ID 删除，没有按筛选条件批量清除的接口，因此需先收集 ID，例如 `Span.spanAnnotations { id identifier }`。

<a id="annotation-configs"></a>

## 标注配置

分类配置让标签集合成为界面中的正式选项，为标注人员提供下拉列表，并在不同运行之间共享词汇。标注 `name` 必须与配置 `name` 相同。

- `createAnnotationConfig(input: { annotationConfig: { categorical: { name, description, optimizationDirection: NONE, values: [{ label }, ...] } } })`：`AnnotationConfigInput` 是 `categorical`、`continuous`、`freeform` 的 `@oneOf`。
- `updateAnnotationConfig(input: UpdateAnnotationConfigInput!)`：出现新类别时替换值列表。
- `addAnnotationConfigToProject(input: [{ projectId, annotationConfigId }])`：附加到项目，使其在项目中显示。
- 创建近似重复配置前，先通过 `Query.annotationConfigs` 查找现有配置。

