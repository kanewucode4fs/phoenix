<a id="cli-agent-starter-kit"></a>

# CLI Agent 入门套件

这是一个集成 AI SDK 和 Anthropic 的 TypeScript CLI Agent 入门套件。

<a id="important-private-package"></a>

## 重要：私有包

此包在 package.json 中标记为 `"private": true`，**不会**发布到 npm。因此：

- 修改此包**不需要 changeset**
- 这是示例/入门套件，不是已发布的库
- 此处修改不需要版本管理或变更日志条目

<a id="available-skills"></a>

## 可用技能

本项目可使用 Phoenix 技能：`phoenix-cli`、`phoenix-tracing` 和 `phoenix-evals`。

处理 Phoenix 追踪、评估或 Phoenix CLI 时使用这些技能。

<a id="development"></a>

## 开发

```bash
pnpm dev    # Run the agent
pnpm build  # Build the TypeScript
pnpm start  # Run the compiled output
```

<a id="environment-variables"></a>

## 环境变量

- `ANTHROPIC_API_KEY` - 调用 Anthropic API 时必需

<a id="debugging-with-phoenix-cli"></a>

## 使用 Phoenix CLI 调试

<a id="quick-trace-check"></a>

### 快速检查追踪

验证是否正在采集追踪：

```bash
npx @arizeai/phoenix-cli traces \
  --endpoint http://localhost:6006 \
  --project cli-agent-starter-kit \
  --limit 5
```

<a id="view-recent-traces-with-key-details"></a>

### 查看近期追踪及关键详情

```bash
npx @arizeai/phoenix-cli traces \
  --endpoint http://localhost:6006 \
  --project cli-agent-starter-kit \
  --limit 5 \
  --format raw \
  --no-progress | jq '.[] | {
    traceId: .traceId,
    startTime: .spans[0].start_time,
    operation: .spans[0].attributes["operation.name"],
    model: .spans[0].attributes["ai.model.id"]
  }'
```

<a id="inspect-specific-trace-including-tool-calls"></a>

### 检查指定追踪（含工具调用）

```bash
npx @arizeai/phoenix-cli trace <trace-id> \
  --endpoint http://localhost:6006 \
  --project cli-agent-starter-kit \
  --format raw \
  --no-progress | jq '{
    traceId: .traceId,
    spanCount: (.spans | length),
    spans: [.spans[] | {
      name,
      span_kind,
      tool: .attributes["ai.toolCall.name"],
      model: .attributes["ai.model.id"]
    }]
  }'
```

<a id="important-notes"></a>

### 重要说明

- **项目名称**：必须与 `src/instrumentation.ts` 中的 `projectName` 一致（当前为 `cli-agent-starter-kit`）
- **端点**：本地 Phoenix 位于 `http://localhost:6006`
- **格式**：通过管道传给 `jq` 时，使用 `--format raw --no-progress`
- **遥测**：ToolLoopAgent 的构造函数需要设置 `experimental_telemetry: { isEnabled: true }`

<a id="common-span-attributes"></a>

### 常用 Span 属性

- `operation.name` - 操作类型（如 `ai.generateText`）
- `ai.model.id` - 模型名称（如 `claude-sonnet-4-20250514`）
- `ai.toolCall.name` - TOOL Span 的工具名称
- `ai.usage.completionTokens` / `ai.usage.promptTokens` - Token 数量
- `span_kind` - Span 类型：`AGENT`、`LLM`、`TOOL`、`CHAIN` 等。
