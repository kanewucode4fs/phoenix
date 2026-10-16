<a id="vercel-eve-agent-tracing"></a>

# Vercel Eve Agent 追踪

使用 `@arizeai/phoenix-otel` 追踪的最简 [Vercel Eve](https://eve.dev/) Agent。Eve 在服务器启动时自动发现 [`agent/instrumentation.ts`](./agent/instrumentation.ts)；其中的 `register()` 调用负责配置提供程序及全局连接，并通过 `spanProcessors` 传入 OpenInference Span 处理器，仅保留 AI Span（过滤 Eve 工作流引擎内部 Span）。每一轮随后作为一条清晰的追踪写入 Phoenix：包括根 Span `ai.eve.turn`、各模型步骤及 [`get_weather`](./agent/tools/get_weather.ts) 工具调用。

在 Phoenix 中阅读 Eve 追踪的完整教程见 [Vercel Eve 集成文档](https://arize.com/docs/phoenix/integrations/typescript/vercel/eve-tracing)。

<a id="prerequisites"></a>

## 前置条件

- Node.js >= 24 （Eve CLI 要求）
- 运行中的 Phoenix 实例（默认 `http://localhost:6006`）
- 环境中已设置 `OPENAI_API_KEY`（Agent 直接使用 `@ai-sdk/openai` 模型；若要使用 Vercel AI Gateway，请在 [`agent/agent.ts`](./agent/agent.ts) 中改用网关模型 ID）

<a id="run"></a>

## 运行

```shell
# From the js/ directory
pnpm install
# Build the workspace-linked @arizeai/phoenix-otel package
pnpm --filter @arizeai/phoenix-otel build

export OPENAI_API_KEY=sk-...
pnpm --filter eve-agent dev
```

`eve dev` 打开交互式终端 UI，并在 `http://127.0.0.1:2000` 提供 Agent 的 HTTP 通道。在终端 UI 中发送“布鲁克林天气如何？”之类的消息，或通过 HTTP 发送：

```shell
curl -X POST http://127.0.0.1:2000/eve/v1/session \
  -H 'content-type: application/json' \
  -d '{"message":"What is the weather in Brooklyn?"}'
```

打开 [http://localhost:6006](http://localhost:6006)，在 `eve-agent` 项目中查看追踪。

<a id="configuration"></a>

## 配置

| 环境变量         | 说明                          | 默认值                 |
| ---------------------------- | ------------------------------------ | ----------------------- |
| `OPENAI_API_KEY`             | OpenAI API 密钥                       | 必填                |
| `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix OTLP 端点                | `http://localhost:6006` |
| `PHOENIX_API_KEY`            | Phoenix API 密钥（启用身份验证时） | 无                    |
| `PHOENIX_PROJECT_NAME`       | 接收追踪的 Phoenix 项目    | Agent 名称          |
