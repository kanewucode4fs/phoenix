<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-otel-ts">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        @arizeai/phoenix-otel
    </div>
</h1>
<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-otel">
        <img src="https://img.shields.io/npm/v/@arizeai/phoenix-otel" alt="NPM 版本">
    </a>
    <a href="https://arize.com/docs/phoenix">
        <img src="https://img.shields.io/badge/docs-blue?logo=readthedocs&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=js/packages/phoenix-otel/README.md" />
</p>

面向 Node.js 应用的轻量 OpenTelemetry 封装，简化向 [Arize Phoenix](https://github.com/Arize-ai/phoenix) 发送追踪的过程。`@arizeai/phoenix-otel` 处理提供程序注册和 OTLP 导出，并从同一包路径重新导出 `@arizeai/openinference-core` 的全部辅助 API，使你通过一次导入即可注册追踪和编写手动 Span。

> **注意**：此包正在积极开发中，API 可能变化。

<a id="features"></a>

## 功能

- **简单配置**：一行配置，提供合理默认值
- **环境变量**：从环境变量自动配置
- **批处理**：内置适用于生产的 Span 批处理
- **内含 OpenInference 辅助函数**：重新导出 `withSpan`、Span 类型封装（`traceChain`、`traceAgent`、`traceTool`、`traceLLM`、`traceRetriever`、`traceReranker`、`traceEmbedding`、`traceGuardrail`、`traceEvaluator`、`tracePrompt`）、`observe`、上下文设置函数、属性构建器、`OITracer` 和辅助工具
- **支持安全切换提供程序的封装**：重新导出的 OpenInference 辅助函数在被封装函数执行时解析默认追踪器，因此模块作用域封装会持续跟随全局提供程序变化
- **适合 Agent 的本地文档**：在 `node_modules/@arizeai/phoenix-otel/` 中附带整理过的文档和源码

<a id="installation"></a>

## 安装

```bash
npm install @arizeai/phoenix-otel
```

要求 Node.js 18 或更高版本，同时提供 ESM 和 CommonJS 入口。

<a id="quick-start"></a>

## 快速开始

<a id="basic-usage"></a>

### 基本用法

最简单的入门方式是将 `register()` 与内置追踪辅助函数配合使用：

```typescript
import { register, traceChain } from "@arizeai/phoenix-otel";

const provider = register({
  projectName: "my-app",
});

const answerQuestion = traceChain(
  async (question: string) => `Handled: ${question}`,
  { name: "answer-question" }
);

await answerQuestion("What is Phoenix?");
await provider.shutdown();
```

`register()` 配置 Phoenix 导出器。追踪辅助函数来自 `@arizeai/openinference-core`，通过 `@arizeai/phoenix-otel` 重新导出。

<a id="production-setup"></a>

### 生产配置

在生产中使用远程 Phoenix 实例：

```typescript
import { register } from "@arizeai/phoenix-otel";

register({
  projectName: "my-app",
  url: "https://your-phoenix-instance.com",
  apiKey: process.env.PHOENIX_API_KEY,
});
```

<a id="configuration"></a>

## 配置

<a id="environment-variables"></a>

### 环境变量

`register` 函数自动读取环境变量：

```bash
# For local Phoenix server (default)
export PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"

# For a remote Phoenix instance
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance.com"
export PHOENIX_API_KEY="your-api-key"
```

参数或环境变量未提供某项配置时，`register` 还会从当前工作目录开始向文件系统根目录逐级查找 `.env.phoenix`，在首个匹配处停止，并读取其中以 `PHOENIX_` 为前缀的键（dotenv 格式）。环境变量始终优先于文件；设置 `PHOENIX_DISCOVER_CONFIG=false` 可完全禁用发现。

`PHOENIX_API_KEY` 和 `PHOENIX_CLIENT_HEADERS` 作为同一凭证组解析。显式 `Authorization` 头会以不区分大小写的方式保留。若显式或进程凭证与文件中的 `PHOENIX_COLLECTOR_ENDPOINT` 配对，导出器会发出一次警告后继续，不记录凭证值。

<a id="configuration-options"></a>

### 配置选项

`register` 函数接收以下参数：

| 参数          | 类型                     | 默认值                   | 说明                                            |
| ------------------ | ------------------------ | ------------------------- | ------------------------------------------------------ |
| `projectName`      | `string`                 | `"default"`               | 用于在 Phoenix 中组织追踪的项目名称      |
| `url`              | `string`                 | `"http://localhost:6006"` | Phoenix 实例的 URL                       |
| `apiKey`           | `string`                 | `undefined`               | Phoenix 身份验证的 API 密钥                     |
| `headers`          | `Record<string, string>` | `{}`                      | OTLP 请求的自定义头                       |
| `batch`            | `boolean`                | `true`                    | 使用 Span 批处理（生产推荐） |
| `instrumentations` | `Instrumentation[]`      | `undefined`               | 要注册的 OpenTelemetry 插桩数组    |
| `global`           | `boolean`                | `true`                    | 全局注册追踪提供程序                  |
| `diagLogLevel`     | `DiagLogLevel`           | `undefined`               | 调试使用的诊断日志级别                 |

<a id="custom-span-processors"></a>

### 自定义 Span 处理器

`register()` 还接收 `spanProcessors`，用于替换默认 Phoenix 导出器配置。为此，包根入口重新导出 `OTLPTraceExporter`，仅支持 ESM 的 `@arizeai/phoenix-otel/vercel` 子路径重新导出 `@arizeai/openinference-vercel`（`OpenInferenceSimpleSpanProcessor`、`OpenInferenceBatchSpanProcessor`、`isOpenInferenceSpan` 和类型），无需安装底层包：

```typescript
import {
  ensureCollectorEndpoint,
  OTLPTraceExporter,
  register,
} from "@arizeai/phoenix-otel";
import {
  isOpenInferenceSpan,
  OpenInferenceSimpleSpanProcessor,
} from "@arizeai/phoenix-otel/vercel";

register({
  projectName: "my-agent",
  spanProcessors: [
    new OpenInferenceSimpleSpanProcessor({
      exporter: new OTLPTraceExporter({
        url: ensureCollectorEndpoint("http://localhost:6006"),
      }),
      // Export only AI spans, re-rooting any left orphaned by the filter
      spanFilter: isOpenInferenceSpan,
      reparentOrphanedSpans: true,
    }),
  ],
});
```

<a id="usage-examples"></a>

## 使用示例

<a id="with-the-vercel-ai-sdk-v7"></a>

### 配合 Vercel AI SDK（v7+）

AI SDK v7 遥测注册作用于整个进程，因此应用需要显式配置。安装 `ai` 和 `@ai-sdk/otel`，然后将此集成与 Phoenix 提供程序一起注册。下方禁用了请求头捕获，因为请求头可能包含授权令牌和 Cookie。

```typescript
// instrumentation.ts
import { OpenTelemetry } from "@ai-sdk/otel";
import { registerTelemetry } from "ai";
import { register } from "@arizeai/phoenix-otel";

const provider = register({
  projectName: "my-ai-app",
});

registerTelemetry(
  new OpenTelemetry({
    tracer: provider.getTracer("@arizeai/phoenix-otel/ai-sdk"),
    headers: false,
  })
);
```

```typescript
// main.ts
import "./instrumentation.ts";
import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

const result = await generateText({
  model: openai("gpt-4o-mini"),
  prompt: "Write a short story about a cat.",
});
```

> **注意**：AI SDK v6 及更早版本生成不同的 Span 结构，捆绑的 Span 处理器不支持该结构。使用 AI SDK v6 时，请使用 `@arizeai/phoenix-otel` 1.x（搭配 `@arizeai/openinference-vercel` 2.x）。

<a id="with-auto-instrumentation"></a>

### 配合自动插桩

自动为常用库插桩（最适合 CommonJS）：

```typescript
import { register } from "@arizeai/phoenix-otel";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { ExpressInstrumentation } from "@opentelemetry/instrumentation-express";

register({
  projectName: "my-express-app",
  instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()],
});
```

> **注意**：通过 `instrumentations` 参数自动插桩最适合 CommonJS 项目，ESM 项目需要手动插桩。

<a id="with-openai-esm"></a>

### 配合 OpenAI（ESM）

ESM 项目需手动为库插桩：

```typescript
// instrumentation.ts
import { register, registerInstrumentations } from "@arizeai/phoenix-otel";
import OpenAI from "openai";
import { OpenAIInstrumentation } from "@arizeai/openinference-instrumentation-openai";

register({
  projectName: "openai-app",
});

// Manual instrumentation for ESM
const instrumentation = new OpenAIInstrumentation();
instrumentation.manuallyInstrument(OpenAI);

registerInstrumentations({
  instrumentations: [instrumentation],
});
```

```typescript
// main.ts
import "./instrumentation.ts";
import OpenAI from "openai";

const openai = new OpenAI();

const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Hello!" }],
});
```

<a id="tracing-helpers"></a>

### 追踪辅助函数

此包包含 `withSpan` 及 Span 类型简写函数 `traceChain`、`traceAgent` 和 `traceTool`，用于通过 OpenInference Span 封装函数。每个辅助函数都会自动记录输入、输出、错误和 Span 类型。

```typescript
import {
  register,
  traceAgent,
  traceChain,
  traceTool,
  withSpan,
} from "@arizeai/phoenix-otel";

register({ projectName: "my-app" });

// traceTool — for tool calls and API lookups
const searchDocs = traceTool(
  async (query: string) => {
    const response = await fetch(`/api/search?q=${query}`);
    return response.json();
  },
  { name: "search-docs" }
);

// traceChain — for pipeline steps and orchestration
const summarize = traceChain(
  async (text: string) => `Summary of ${text.length} chars`,
  { name: "summarize" }
);

// traceAgent — for autonomous agent entry points
const supportAgent = traceAgent(
  async (question: string) => {
    const docs = await searchDocs(question);
    return summarize(JSON.stringify(docs));
  },
  { name: "support-agent" }
);

// withSpan — general purpose, specify kind explicitly
const retrieveDocs = withSpan(
  async (query: string) =>
    fetch(`/api/search?q=${query}`).then((r) => r.json()),
  { name: "retrieve-docs", kind: "RETRIEVER" }
);
```

这些辅助函数在被封装函数运行时解析默认追踪器，因此模块作用域定义的追踪函数会持续跟随全局提供程序变化。

<a id="additional-span-kind-wrappers"></a>

#### 其他 Span 类型封装

所有 OpenInference Span 类型都有对应封装，均为 `withSpan(fn, { ...options, kind })` 的简写。它们接受与 `traceChain`/`traceAgent`/`traceTool` 相同的选项（除预先设置的 `kind` 外）。这些封装在 `@arizeai/openinference-core` 中标记为 `@experimental`。

| 封装          | Span 类型   | 用途                                                                    |
| ---------------- | ----------- | ----------------------------------------------------------------------------- |
| `traceLLM`       | `LLM`       | 语言模型调用，包括聊天/文本补全及其他推断调用  |
| `traceRetriever` | `RETRIEVER` | 从知识库、向量存储或搜索索引获取文档（RAG） |
| `traceReranker`  | `RERANKER`  | 按相关性对候选文档重排或评分                        |
| `traceEmbedding` | `EMBEDDING` | 将文本或数据转换为向量表示                           |
| `traceGuardrail` | `GUARDRAIL` | 安全、验证或策略检查（内容审核、个人身份信息、合规）            |
| `traceEvaluator` | `EVALUATOR` | 评估输出质量，包括相关性、正确性或 LLM 裁判            |
| `tracePrompt`    | `PROMPT`    | 模型调用前构建、渲染提示词或处理提示词模板           |

```typescript
import {
  traceEmbedding,
  traceEvaluator,
  traceGuardrail,
  traceLLM,
  tracePrompt,
  traceReranker,
  traceRetriever,
} from "@arizeai/phoenix-otel";

const retrieveDocuments = traceRetriever(
  async (query: string) => vectorStore.similaritySearch(query, 5),
  { name: "vector-search" }
);

const evaluateAnswer = traceEvaluator(
  async (question: string, answer: string) => judge.score({ question, answer }),
  { name: "answer-evaluation" }
);
```

<a id="custom-input-and-output-processing"></a>

### 自定义输入与输出处理

若需要比默认 JSON 序列化的 `input.value` 和 `output.value` 更丰富的 OpenInference 属性，请使用 `processInput` 和 `processOutput`。

```typescript
import {
  OpenInferenceSpanKind,
  getInputAttributes,
  getRetrieverAttributes,
  withSpan,
} from "@arizeai/phoenix-otel";

const retrieveDocs = withSpan(
  async (query: string) => [`Doc A for ${query}`, `Doc B for ${query}`],
  {
    name: "retrieve-docs",
    kind: OpenInferenceSpanKind.RETRIEVER,
    processInput: (query) => getInputAttributes(query),
    processOutput: (documents) =>
      getRetrieverAttributes({
        documents: documents.map((content, index) => ({
          id: `doc-${index}`,
          content,
        })),
      }),
  }
);
```

<a id="context-attributes"></a>

### 上下文属性

通过上下文设置函数，将会话 ID、用户 ID、元数据和标签传播到所有子 Span：

```typescript
import {
  context,
  register,
  setMetadata,
  setSession,
  setUser,
  traceChain,
} from "@arizeai/phoenix-otel";

register({ projectName: "my-app" });

const handleQuery = traceChain(async (query: string) => `Handled: ${query}`, {
  name: "handle-query",
});

// All spans inside context.with() inherit session, user, and metadata
await context.with(
  setMetadata(
    setUser(setSession(context.active(), { sessionId: "sess-123" }), {
      userId: "user-456",
    }),
    { environment: "production" }
  ),
  () => handleQuery("Hello")
);
```

可用设置函数： `setSession`, `setUser`, `setMetadata`, `setTags`, `setAttributes`, `setPromptTemplate`.

若使用普通 OpenTelemetry 追踪器手动创建 Span，请将传播的上下文属性显式复制到 Span：

```typescript
import {
  context,
  getAttributesFromContext,
  register,
  trace,
} from "@arizeai/phoenix-otel";

register({ projectName: "my-app" });

const tracer = trace.getTracer("manual-tracer");
const span = tracer.startSpan("manual-span");
span.setAttributes(getAttributesFromContext(context.active()));
span.end();
```

<a id="decorators"></a>

### 装饰器

`observe` 为类方法封装追踪，同时保留方法的 `this` 上下文。使用 TypeScript 5+ 标准装饰器。

```typescript
import { OpenInferenceSpanKind, observe } from "@arizeai/phoenix-otel";

class ChatService {
  @observe({ kind: OpenInferenceSpanKind.CHAIN })
  async runWorkflow(message: string) {
    return `processed: ${message}`;
  }

  @observe({ name: "llm-call", kind: OpenInferenceSpanKind.LLM })
  async callModel(prompt: string) {
    return `model output for: ${prompt}`;
  }
}
```

<a id="attribute-helper-apis"></a>

### 属性辅助 API

要直接构建兼容 OpenInference 的 Span 属性时，使用属性辅助函数：

```typescript
import { getLLMAttributes, trace } from "@arizeai/phoenix-otel";

const tracer = trace.getTracer("llm-service");

tracer.startActiveSpan("llm-inference", (span) => {
  span.setAttributes(
    getLLMAttributes({
      provider: "openai",
      modelName: "gpt-4o-mini",
      inputMessages: [{ role: "user", content: "What is Phoenix?" }],
      outputMessages: [{ role: "assistant", content: "Phoenix is..." }],
      tokenCount: { prompt: 12, completion: 44, total: 56 },
      invocationParameters: { temperature: 0.2 },
    })
  );
  span.end();
});
```

可用辅助函数包括：

- `getLLMAttributes`
- `getEmbeddingAttributes`
- `getRetrieverAttributes`
- `getToolAttributes`
- `getMetadataAttributes`
- `getInputAttributes` / `getOutputAttributes`
- `defaultProcessInput` / `defaultProcessOutput`

<a id="trace-config-and-redaction"></a>

### 追踪配置与脱敏

`OITracer` 封装 OpenTelemetry 追踪器，可在 Span 写入前对敏感 OpenInference 属性脱敏或移除：

```typescript
import {
  OITracer,
  OpenInferenceSpanKind,
  trace,
  withSpan,
} from "@arizeai/phoenix-otel";

const tracer = new OITracer({
  tracer: trace.getTracer("my-service"),
  traceConfig: {
    hideInputs: true,
    hideOutputText: true,
    hideEmbeddingVectors: true,
    hideLLMTools: true,
    base64ImageMaxLength: 8_000,
  },
});

const safeLLMCall = withSpan(
  async (prompt: string) => `model response for ${prompt}`,
  {
    tracer,
    kind: OpenInferenceSpanKind.LLM,
    name: "safe-llm-call",
  }
);
```

支持的环境变量包括：

- `OPENINFERENCE_HIDE_INPUTS`
- `OPENINFERENCE_HIDE_OUTPUTS`
- `OPENINFERENCE_HIDE_INPUT_MESSAGES`
- `OPENINFERENCE_HIDE_OUTPUT_MESSAGES`
- `OPENINFERENCE_HIDE_INPUT_IMAGES`
- `OPENINFERENCE_HIDE_INPUT_TEXT`
- `OPENINFERENCE_HIDE_OUTPUT_TEXT`
- `OPENINFERENCE_HIDE_EMBEDDING_VECTORS`
- `OPENINFERENCE_BASE64_IMAGE_MAX_LENGTH`
- `OPENINFERENCE_HIDE_PROMPTS`
- `OPENINFERENCE_HIDE_LLM_TOOLS`

<a id="raw-opentelemetry-spans"></a>

### 原始 OpenTelemetry Span

要完全控制属性和时间，请直接使用 OpenTelemetry API：

```typescript
import { register, trace, SpanStatusCode } from "@arizeai/phoenix-otel";

register({ projectName: "my-app" });

const tracer = trace.getTracer("my-service");

async function processOrder(orderId: string) {
  return tracer.startActiveSpan("process-order", async (span) => {
    try {
      span.setAttribute("order.id", orderId);
      const result = await fetchOrderDetails(orderId);
      span.setAttribute("order.status", result.status);
      return result;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

<a id="utility-helpers"></a>

### 辅助工具

此包还重新导出 `@arizeai/openinference-core` 的小型工具：

- `withSafety({ fn, onError? })` 封装函数，出错时返回 `null`
- `safelyJSONStringify(value)` 和 `safelyJSONParse(value)` 保护 JSON 操作

<a id="development-vs-production"></a>

### 开发与生产

**开发**（带调试日志）：

```typescript
import { DiagLogLevel, register } from "@arizeai/phoenix-otel";

register({
  projectName: "my-app-dev",
  url: "http://localhost:6006",
  batch: false, // Immediate span delivery for faster feedback
  diagLogLevel: DiagLogLevel.DEBUG,
});
```

**生产**（性能优化）：

```typescript
import { register } from "@arizeai/phoenix-otel";

register({
  projectName: "my-app-prod",
  url: "https://your-phoenix-instance.com",
  apiKey: process.env.PHOENIX_API_KEY,
  batch: true, // Batch processing for better performance
});
```

<a id="custom-headers"></a>

### 自定义请求头

为 OTLP 请求添加自定义头：

```typescript
import { register } from "@arizeai/phoenix-otel";

register({
  projectName: "my-app",
  url: "https://your-phoenix-instance.com",
  headers: {
    "X-Custom-Header": "custom-value",
    "X-Environment": process.env.NODE_ENV || "development",
  },
});
```

<a id="non-global-provider"></a>

### 非全局提供程序

显式使用提供程序，不进行全局注册：

```typescript
import { register } from "@arizeai/phoenix-otel";

const provider = register({
  projectName: "my-app",
  global: false,
});

// Use the provider explicitly
const tracer = provider.getTracer("my-tracer");
```

<a id="docs-and-source-code-in-node_modules"></a>

## `node_modules` 中的文档与源代码

安装后，编码 Agent 可以查看随包分发的确切版本文档及实现：

```text
node_modules/@arizeai/phoenix-otel/docs/
node_modules/@arizeai/phoenix-otel/src/
```

由于 `@arizeai/phoenix-otel` 重新导出 `@arizeai/openinference-core`，该依赖文档也是有用的本地参考：

```text
node_modules/@arizeai/openinference-core/docs/
node_modules/@arizeai/openinference-core/src/
```

<a id="coding-agent-skill"></a>

## 编码 Agent 技能

Phoenix 仓库包含 [phoenix-tracing 技能](https://github.com/Arize-ai/phoenix/tree/main/.agents/skills/phoenix-tracing)，指导编码 Agent（Claude Code、Cursor 等）使用 OpenInference 追踪为 LLM 应用插桩。安装方式：

```bash
npx skills add Arize-ai/phoenix --skill phoenix-tracing
```

追踪辅助函数：

```typescript
import {
  observe,
  traceAgent,
  traceChain,
  traceEmbedding,
  traceEvaluator,
  traceGuardrail,
  traceLLM,
  tracePrompt,
  traceReranker,
  traceRetriever,
  traceTool,
  withSpan,
} from "@arizeai/phoenix-otel";
```

上下文属性设置函数：

```typescript
import {
  setAttributes,
  setMetadata,
  setPromptTemplate,
  setSession,
  setTags,
  setUser,
} from "@arizeai/phoenix-otel";
```

用于丰富 Span 数据的属性构建器：

```typescript
import {
  defaultProcessInput,
  defaultProcessOutput,
  getEmbeddingAttributes,
  getLLMAttributes,
  getRetrieverAttributes,
  getToolAttributes,
} from "@arizeai/phoenix-otel";
```

脱敏与辅助工具：

```typescript
import {
  OITracer,
  safelyJSONParse,
  safelyJSONStringify,
  withSafety,
} from "@arizeai/phoenix-otel";
```

追踪辅助封装在运行时解析默认追踪器，使实验及进程生命周期内切换提供程序的工作流中，Span 始终关联当前提供程序。

<a id="documentation"></a>

## 文档

- **[Phoenix 文档](https://arize.com/docs/phoenix)** - 完整 Phoenix 文档
- **[@arizeai/phoenix-otel 包文档](https://arize.com/docs/phoenix/sdk-api-reference/typescript/arizeai-phoenix-otel)** - 此包整理后的站点文档
- **[@arizeai/openinference-core 包文档](https://arize.com/docs/phoenix/sdk-api-reference/typescript/arizeai-openinference-core)** - 上游辅助函数和属性构建器参考
- **[OpenTelemetry JS](https://opentelemetry.io/docs/languages/js/)** - JavaScript 的 OpenTelemetry
- **[OpenInference](https://github.com/Arize-ai/openinference)** - OpenInference 语义约定

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g)
- 💡 在 _#phoenix-support_ 频道提问并反馈
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)
