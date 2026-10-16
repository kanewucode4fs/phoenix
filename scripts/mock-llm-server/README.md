<a id="mock-llm-server"></a>

# LLM 模拟服务

一个 TypeScript 模拟服务，用于模拟 **OpenAI**、**Anthropic** 和 **Google GenAI（Gemini）** API，测试流式输出、限流和工具调用。包含用于监控和控制服务的**实时仪表盘**。

<a id="features"></a>

## 功能

- **OpenAI Chat Completions API**：完全兼容官方 OpenAI SDK
- **OpenAI Responses API**：较新的 API，支持基于事件的流式输出
- **Anthropic Messages API**：完全兼容官方 Anthropic SDK
- **Google GenAI（Gemini）API**：完全兼容官方 @google/genai SDK
- **流式支持**：SSE 流式输出，可配置分块大小和延迟
- **工具调用**：根据提供的 JSON Schema 生成模拟工具调用或使用响应
- **限流**：支持多种可配置限流模式
- **实时仪表盘**：监控连接、调整延迟、动态开关限流
- **错误注入**：模拟服务端错误、认证错误、超时和错误请求

<a id="quick-start"></a>

## 快速开始

```bash
# Install dependencies
pnpm install

# Build the dashboard (first time only)
pnpm run build:dashboard

# Start the server (development mode with hot reload)
pnpm dev

# Or start without hot reload
pnpm start
```

服务默认运行在 `http://localhost:57593`。

<a id="dashboard"></a>

## 仪表盘

实时监控仪表盘地址：`http://localhost:57593/dashboard`。

**功能：**

- **连接监控**：各端点的活跃连接数
- **请求速率图**：每秒请求数实时曲线
- **延迟控制**：调整流式延迟、抖动和分块大小
- **限流**：开关限流并选择策略，如 fixed-window、token-bucket
- **错误注入**：设置错误率和类型（500、401、403、400、超时）
- **事件日志**：实时展示全部事件

**API 端点：**

- `GET /api/config`：当前配置
- `PATCH /api/config/global`：更新全局配置
- `PATCH /api/config/endpoints/:endpoint`：端点级配置
- `GET /api/metrics`：当前指标快照
- `POST /api/rate-limit/reset`：重置限流计数器
- `WebSocket /ws`：实时指标与事件

<a id="usage-with-openai-sdk"></a>

## 配合 OpenAI SDK 使用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:57593/v1",
    api_key="fake-key",  # Any string works
)

# Non-streaming
response = client.chat.completions.create(
    model="gpt-4o", messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="gpt-4o", messages=[{"role": "user", "content": "Hello!"}], stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

<a id="tool-calls"></a>

### 工具调用

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ],
)

# The mock server will generate fake arguments matching the schema
tool_call = response.choices[0].message.tool_calls[0]
print(tool_call.function.name)  # "get_weather"
print(tool_call.function.arguments)  # '{"location": "San Francisco", "unit": "celsius"}'
```

<a id="usage-with-anthropic-sdk"></a>

## 配合 Anthropic SDK 使用

注意：Anthropic SDK 会自动向基础 URL 追加 `/v1`，因此应使用根 URL。

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:57593",  # SDK adds /v1 automatically
    api_key="fake-key",  # Any string works
)

# Non-streaming
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.content[0].text)

# Streaming
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="")
```

<a id="anthropic-tool-use"></a>

### Anthropic 工具使用

```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[
        {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    ],
)

# The mock server will generate fake input matching the schema
for block in response.content:
    if block.type == "tool_use":
        print(block.name)  # "get_weather"
        print(block.input)  # {"location": "San Francisco", "unit": "celsius"}
```

<a id="usage-with-google-genai-sdk"></a>

## 配合 Google GenAI SDK 使用

```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({
  vertexai: false,
  apiKey: "fake-key", // Any string works
  httpOptions: {
    baseUrl: "http://localhost:57593",
  },
});

// Non-streaming
const response = await ai.models.generateContent({
  model: "gemini-2.0-flash",
  contents: "Hello!",
});
console.log(response.text);

// Streaming
const stream = await ai.models.generateContentStream({
  model: "gemini-2.0-flash",
  contents: "Hello!",
});
for await (const chunk of stream) {
  console.log(chunk.text);
}
```

<a id="gemini-function-calling"></a>

### Gemini 函数调用

```typescript
const response = await ai.models.generateContent({
  model: "gemini-2.0-flash",
  contents: "What's the weather?",
  config: {
    tools: [
      {
        functionDeclarations: [
          {
            name: "get_weather",
            description: "Get the weather for a location",
            parameters: {
              type: "object",
              properties: {
                location: { type: "string", description: "City name" },
                unit: { type: "string", enum: ["celsius", "fahrenheit"] },
              },
              required: ["location"],
            },
          },
        ],
      },
    ],
  },
});

// The mock server will generate fake args matching the schema
if (response.functionCalls) {
  console.log(response.functionCalls[0].name); // "get_weather"
  console.log(response.functionCalls[0].args); // { location: "San Francisco", unit: "celsius" }
}
```

<a id="configuration"></a>

## 配置

通过环境变量配置：

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `PORT` | 服务端口 | `57593` |
| `RATE_LIMIT_ENABLED` | 启用限流 | `false` |
| `RATE_LIMIT_MODE` | `always`、`random` 或 `after_n` | `after_n` |
| `RATE_LIMIT_AFTER_N` | N 次请求后失败，适用于 mode=after_n | `5` |
| `RATE_LIMIT_RANDOM_PROBABILITY` | 返回 429 的概率，适用于 mode=random | `0.3` |
| `RATE_LIMIT_REQUESTS` | 每个窗口的最大请求数 | `10` |
| `RATE_LIMIT_WINDOW_MS` | 限流窗口，单位为毫秒 | `60000` |
| `STREAM_INITIAL_DELAY_MS` | 首个分块前的初始延迟，即首令牌时间 | `100` |
| `STREAM_DELAY_MS` | 流式分块之间的基础延迟 | `10` |
| `STREAM_JITTER_MS` | 延迟上额外增加的随机抖动，范围为 0 到 N 毫秒 | `10` |
| `STREAM_CHUNK_SIZE` | 每个流式分块的字符数 | `10` |
| `TOOL_CALL_PROBABILITY` | 提供工具时触发工具调用的概率 | `0.75` |
| `DEFAULT_RESPONSE` | 固定响应文本；未设置时，50% 来自响应池，50% 为 lorem ipsum 占位文本 | 动态生成 |

<a id="example-test-rate-limiting"></a>

### 示例：测试限流

```bash
# Start with rate limiting enabled, fail after 3 requests
RATE_LIMIT_ENABLED=true RATE_LIMIT_MODE=after_n RATE_LIMIT_AFTER_N=3 pnpm start
```

<a id="example-fast-streaming"></a>

### 示例：快速流式输出

```bash
# Very fast streaming with small chunks
STREAM_DELAY_MS=10 STREAM_CHUNK_SIZE=5 pnpm start
```

<a id="example-always-make-tool-calls"></a>

### 示例：始终调用工具

```bash
TOOL_CALL_PROBABILITY=1.0 pnpm start
```

<a id="api-endpoints"></a>

## API 端点

<a id="openai-compatible"></a>

### 兼容 OpenAI

| 端点 | 说明 |
| --- | --- |
| `POST /v1/chat/completions` | Chat Completions API，支持流式和非流式 |
| `POST /v1/responses` | Responses API，支持流式和非流式 |
| `GET /v1/models` | 列出可用模型 |

<a id="anthropic-compatible"></a>

### 兼容 Anthropic

| 端点 | 说明 |
| --- | --- |
| `POST /v1/messages` | Messages API，支持流式和非流式 |

<a id="google-genai-gemini-compatible"></a>

### 兼容 Google GenAI（Gemini）

| 端点 | 说明 |
| --- | --- |
| `POST /v1beta/models/:model:generateContent` | 生成内容，非流式 |
| `POST /v1beta/models/:model:streamGenerateContent` | 生成内容，流式 |
| `POST /v1/models/:model:generateContent` | v1 生成内容，非流式 |
| `POST /v1/models/:model:streamGenerateContent` | v1 生成内容，流式 |

<a id="admin--monitoring"></a>

### 管理与监控

| 端点 | 说明 |
| --- | --- |
| `GET /health` | 健康检查 |
| `GET /api/config` | 查看当前配置 |
| `PATCH /api/config/global` | 更新全局配置 |
| `GET /api/config/endpoints` | 列出所有端点及配置 |
| `PATCH /api/config/endpoints/:endpoint` | 更新指定端点配置 |
| `DELETE /api/config/endpoints/:endpoint` | 清除端点覆盖配置 |
| `POST /api/config/reset` | 重置为初始配置 |
| `GET /api/metrics` | 当前指标快照 |
| `GET /api/metrics/latency/:endpoint` | 指定端点的延迟百分位数 |
| `POST /api/metrics/reset` | 重置全部指标 |
| `POST /api/rate-limit/reset` | 重置全部限流器状态 |
| `POST /api/rate-limit/reset/:endpoint` | 重置指定端点限流器 |
| `GET /api/rate-limit/strategies` | 列出可用策略 |
| `GET /api/detailed-metrics` | 完整详细指标快照 |
| `GET /api/detailed-metrics/export/json` | 将指标导出为 JSON |
| `GET /api/detailed-metrics/export/csv` | 将时间序列导出为 CSV |
| `GET /api/failure-modes` | 列出可用失败模式 |
| `WebSocket /ws` | 实时指标与事件 |

<a id="rate-limiting-strategies"></a>

## 限流策略

服务支持为每个端点分别配置多种限流策略：

| 策略 | 说明 |
| --- | --- |
| `none` | 禁用限流 |
| `fixed-window` | 经典固定时间窗口计数器 |
| `sliding-window` | 通过滑动窗口平滑限流 |
| `token-bucket` | 允许不超过桶容量的突发流量 |
| `leaky-bucket` | 以固定速率处理请求 |
| `after-n` | 前 N 次请求成功，之后全部返回 429，适用于测试重试逻辑 |
| `random` | 每个请求以可配置概率返回 429 |
| `always` | 每个请求都返回 429 |

<a id="responses-api-usage"></a>

## Responses API 用法

Responses API 的格式不同于 Chat Completions：

```python
import httpx2

response = httpx2.post(
    "http://localhost:57593/v1/responses",
    headers={"Authorization": "Bearer fake-key"},
    json={
        "model": "gpt-4o",
        "input": "What is 2+2?",
        # Or use structured input:
        # "input": [{"type": "message", "role": "user", "content": "Hello"}]
    },
)
print(response.json())
```

<a id="streaming-responses-api"></a>

### 流式输出（Responses API）

Responses API 使用带名称事件的流式输出：

```python
import httpx2

with httpx2.stream(
    "POST",
    "http://localhost:57593/v1/responses",
    headers={"Authorization": "Bearer fake-key"},
    json={"model": "gpt-4o", "input": "Hello", "stream": True},
) as response:
    for line in response.iter_lines():
        print(line)
        # Events: response.created, response.output_text.delta, response.completed, etc.
```

<a id="anthropic-streaming-details"></a>

## Anthropic 流式输出详情

Anthropic Messages API 使用另一种带名称事件的流式格式：

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:57593",  # SDK adds /v1 automatically
    api_key="fake-key",
)

with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="")
        elif event.type == "message_delta":
            print(f"\nStop reason: {event.delta.stop_reason}")
```

事件顺序：

1. `message_start`：初始消息对象，内容为空
2. `content_block_start`：每个内容块的开始，类型为 text 或 tool_use
3. `content_block_delta`：增量内容，类型为 text_delta 或 input_json_delta
4. `content_block_stop`：内容块结束
5. `message_delta`：最终 stop_reason 和 usage
6. `message_stop`：流结束

<a id="project-structure"></a>

## 项目结构

```
mock-llm-server/
├── src/
│   ├── server.ts              # Express server entry point
│   ├── config.ts              # Environment configuration
│   ├── registry.ts            # Central config & rate limiter registry
│   ├── types.ts               # TypeScript types (OpenAI + Anthropic + Gemini APIs)
│   ├── fake-data.ts           # JSON Schema → fake data generator
│   ├── metrics.ts             # Basic metrics collection
│   ├── detailed-metrics.ts    # Time series & histogram metrics
│   ├── admin/
│   │   ├── index.ts           # Admin module exports
│   │   ├── routes.ts          # REST API routes
│   │   └── websocket.ts       # WebSocket server for real-time updates
│   ├── handlers/
│   │   ├── chat-completions.ts   # OpenAI Chat Completions handler
│   │   ├── responses.ts          # OpenAI Responses API handler
│   │   ├── anthropic-messages.ts # Anthropic Messages API handler
│   │   └── gemini.ts             # Google GenAI (Gemini) handler
│   ├── middleware/
│   │   ├── index.ts           # Middleware exports
│   │   └── request-pipeline.ts # Request processing pipeline
│   ├── providers/
│   │   ├── index.ts           # Provider registry
│   │   ├── types.ts           # Provider type definitions
│   │   ├── openai-chat.ts     # OpenAI Chat provider config
│   │   ├── openai-responses.ts # OpenAI Responses provider config
│   │   ├── anthropic.ts       # Anthropic provider config
│   │   └── gemini.ts          # Gemini provider config
│   └── rate-limiting/
│       ├── index.ts           # Rate limiting exports
│       ├── types.ts           # Rate limiter interfaces
│       ├── factory.ts         # Strategy factory
│       └── strategies/
│           ├── simple.ts      # after-n, random, always strategies
│           ├── fixed-window.ts
│           ├── sliding-window.ts
│           ├── token-bucket.ts
│           └── leaky-bucket.ts
├── dashboard/                 # React monitoring dashboard
│   ├── src/
│   │   ├── App.tsx            # Main dashboard component
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts # WebSocket connection hook
│   │   └── components/
│   │       ├── ConnectionMonitor.tsx
│   │       ├── ConnectionsChart.tsx
│   │       ├── ErrorInjection.tsx
│   │       ├── EventLog.tsx
│   │       ├── FailureModes.tsx
│   │       ├── LatencyControls.tsx
│   │       ├── LatencyHistogram.tsx
│   │       ├── PeakIndicators.tsx
│   │       ├── RateLimitPanel.tsx
│   │       ├── RequestRateChart.tsx
│   │       └── ThroughputChart.tsx
│   └── package.json
├── tests/
│   ├── setup.ts
│   ├── chat-completions.test.ts
│   ├── anthropic-messages.test.ts
│   ├── gemini.test.ts
│   ├── responses.test.ts
│   ├── tool-calls.test.ts
│   ├── rate-limiting.test.ts
│   └── models.test.ts
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── README.md
```
