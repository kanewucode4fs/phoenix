<a id="ai-sdk-v7-agent-tracing"></a>

# AI SDK v7 Agent 追踪

使用 `@arizeai/phoenix-otel` 追踪的最简 [Vercel AI SDK](https://ai-sdk.dev/) v7 Agent。导入 [`instrumentation.ts`](./instrumentation.ts) 会注册 Phoenix 遥测；随后 [`agent.ts`](./agent.ts) 运行仅带一个天气工具的 `ToolLoopAgent`。Agent Span、每个 LLM 步骤及工具调用都会在 Phoenix 中显示为一条追踪。

<a id="version-compatibility"></a>

## 版本兼容性

| Vercel AI SDK | @arizeai/phoenix-otel |
| ------------- | --------------------- |
| v7+           | 2.x（本示例）    |
| v6 及更早版本  | 1.x                   |

AI SDK v7 要求 Node.js 22.12 或更高版本。

<a id="prerequisites"></a>

## 前置条件

- Node.js >= 22.12
- 运行中的 Phoenix 实例（默认 `http://localhost:6006`）
- 环境中已设置 `OPENAI_API_KEY`

<a id="run"></a>

## 运行

```shell
# From the js/ directory
pnpm install
# Build the workspace-linked @arizeai/phoenix-otel package
pnpm --filter @arizeai/phoenix-otel build

export OPENAI_API_KEY=sk-...
pnpm --filter ai-sdk-agent start
```

打开 [http://localhost:6006](http://localhost:6006)，在 `ai-sdk-agent` 项目中查看追踪。

<a id="configuration"></a>

## 配置

| 环境变量         | 说明                          | 默认值                 |
| ---------------------------- | ------------------------------------ | ----------------------- |
| `OPENAI_API_KEY`             | OpenAI API 密钥                       | 必填                |
| `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix OTLP 端点                | `http://localhost:6006` |
| `PHOENIX_API_KEY`            | Phoenix API 密钥（启用身份验证时） | 无                    |
