<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-client-ts">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        @arizeai/phoenix-client
    </div>
</h1>

<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-client">
        <img src="https://img.shields.io/npm/v/%40arizeai%2Fphoenix-client" alt="NPM 版本">
    </a>
    <a href="https://arize-ai.github.io/phoenix/">
        <img src="https://img.shields.io/badge/docs-blue?logo=typescript&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=js/packages/phoenix-client/README.md" />
</p>

此包提供 [Arize Phoenix](https://github.com/Arize-ai/phoenix) API 的 TypeScript 客户端。它仍在积极开发中，可能发生变更。

<a id="installation"></a>

## 安装

```bash
# or yarn, pnpm, bun, etc...
npm install @arizeai/phoenix-client
```

<a id="configuration"></a>

## 配置

如果环境变量存在，客户端会自动读取。

使用以下环境变量：

- `PHOENIX_ENDPOINT` - Phoenix 基础 URL，这是客户端的规范配置。
- `PHOENIX_API_KEY` - 用于身份验证的 API 密钥。
- `PHOENIX_CLIENT_HEADERS` - 添加到所有请求的自定义头，格式为 JSON 字符串化对象。
- `PHOENIX_COLLECTOR_ENDPOINT` - 由 OTel SDK 读取，用于追踪导出，通常与 `PHOENIX_ENDPOINT` URL 相同。未设置 `PHOENIX_ENDPOINT` 时，客户端用它访问 API。

```bash
PHOENIX_ENDPOINT='http://localhost:12345' PHOENIX_API_KEY='xxxxxx' pnpx tsx examples/list_datasets.ts
# emits the following request:
# GET http://localhost:12345/v1/datasets
# headers: {
#   "Authorization": "Bearer xxxxxx",
# }
```

也可直接向客户端传入配置选项，其优先级高于环境变量和默认值。

```ts
const phoenix = createClient({
  options: {
    baseUrl: "http://localhost:6006",
    headers: {
      Authorization: "Bearer xxxxxx",
    },
  },
});
```

对于可能过期的凭证，请创建带身份验证的 fetch 实现并传给客户端。令牌提供方负责存储和刷新令牌轮换。收到 `401` 的请求共享一次刷新操作，并重试一次。

```ts
import { createAuthFetch, createClient } from "@arizeai/phoenix-client";

const authFetch = createAuthFetch({
  getAccessToken: async ({ forceRefresh }) => {
    if (forceRefresh) {
      await refreshAndPersistTokens();
    }
    return loadTokens().accessToken;
  },
});

const phoenix = createClient({
  options: {
    baseUrl: "http://localhost:6006",
    fetch: authFetch,
  },
});
```

<a id="prompts"></a>

## 提示词

`@arizeai/phoenix-client` 提供 `prompts` 导出，包含操作 LLM 提示词的工具。

<a id="creating-a-prompt-and-push-it-to-phoenix"></a>

### 创建提示词并推送到 Phoenix

`createPrompt` 函数可在 Phoenix 中创建提示词，以进行版本管理和复用。

```ts
import { createPrompt, promptVersion } from "@arizeai/phoenix-client/prompts";

const version = createPrompt({
  name: "my-prompt",
  description: "test-description",
  version: promptVersion({
    description: "version description here",
    modelProvider: "OPENAI",
    modelName: "gpt-3.5-turbo",
    template: [
      {
        role: "user",
        content: "{{ question }}",
      },
    ],
    invocationParameters: {
      temperature: 0.8,
    },
  }),
});
```

推送到 Phoenix 的提示词会进行版本管理，并可打标签。

<a id="pulling-a-prompt-from-phoenix"></a>

### 从 Phoenix 拉取提示词

`getPrompt` 函数可根据提示词标识符从 Phoenix 拉取提示词，并以 Phoenix SDK Prompt 类型返回。

```ts
import { getPrompt } from "@arizeai/phoenix-client/prompts";

const prompt = await getPrompt({ name: "my-prompt" });
// ^ you now have a strongly-typed prompt object, in the Phoenix SDK Prompt type

const promptByTag = await getPrompt({ tag: "production", name: "my-prompt" });
// ^ you can optionally specify a tag to filter by

const promptByVersionId = await getPrompt({
  versionId: "1234567890",
});
// ^ you can optionally specify a prompt version Id to filter by
```

<a id="using-a-phoenix-prompt-with-an-llm-provider-sdk"></a>

### 配合 LLM 提供商 SDK 使用 Phoenix 提示词

`toSDK` 辅助函数可将 Phoenix Prompt 转换为 LLM 提供商 SDK 预期的格式，随后即可像往常一样使用该 SDK 和提示词。

若提示词在 Phoenix 中以 `openai` 格式保存，可用 `toSDK` 转换为 OpenAI，甚至 Anthropic 和 Vercel AI SDK 预期的格式。我们会尽力将其转换为你所选 LLM 提供商 SDK 的格式。

支持以下 LLM 提供商 SDK：

- Vercel AI SDK: `ai` [ai](https://www.npmjs.com/package/ai)
- OpenAI: `openai` [openai](https://www.npmjs.com/package/openai) （v6 和 v7）
- Anthropic: `anthropic` [@anthropic-ai/sdk](https://www.npmjs.com/package/@anthropic-ai/sdk)

> **注意：** 这些提供商 SDK 是可选 peer 依赖，安装 `@arizeai/phoenix-client` 不会安装它们。请自行安装转换目标 SDK，例如 `npm install ai`、`npm install openai` 或 `npm install @anthropic-ai/sdk`。未安装对应 SDK 时调用 `toSDK({ sdk: "ai" | "openai" | "anthropic" })` 会在运行时失败。

```ts
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { getPrompt, toSDK } from "@arizeai/phoenix-client/prompts";

const prompt = await getPrompt({ name: "my-prompt" });
const promptAsAI = toSDK({
  sdk: "ai",
  // ^ the SDK you want to convert the prompt to, supported SDKs are listed above
  variables: {
    "my-variable": "my-value",
  },
  // ^ you can format the prompt with variables, if the prompt has any variables in its template
  //   the format (Mustache, F-string, etc.) is specified in the Prompt itself
  prompt,
});
// ^ promptAsAI is now in the format expected by the Vercel AI SDK generateText function

const response = await generateText({
  model: openai(prompt.model_name),
  // ^ the model adapter provided by the Vercel AI SDK can be swapped out for any other model
  //   adapter supported by the Vercel AI SDK. Take care to use the correct model name for the
  //   LLM provider you are using.
  ...promptAsAI,
});
```

<a id="rest-endpoints"></a>

## REST 端点

客户端为 [Phoenix OpenAPI 规范](https://github.com/Arize-ai/phoenix/blob/main/schemas/openapi.json)定义的全部端点提供 REST API。

可在客户端对象中通过强类型字符串字面量及 TypeScript 自动补全访问端点。

```ts
import { createClient } from "@arizeai/phoenix-client";

const phoenix = createClient();

// Get all datasets
const datasets = await phoenix.GET("/v1/datasets");

// Get specific prompt
const prompt = await phoenix.GET("/v1/prompts/{prompt_identifier}/latest", {
  params: {
    path: {
      prompt_identifier: "my-prompt",
    },
  },
});
```

可在 Phoenix 内的 OpenAPI 查看器或 [Phoenix OpenAPI 规范](https://github.com/Arize-ai/phoenix/blob/main/schemas/openapi.json)中查看可用端点及参数的完整概览。

<a id="datasets"></a>

## 数据集

`@arizeai/phoenix-client` 可创建和管理数据集，即用于实验和评估的示例集合。

<a id="creating-a-dataset"></a>

### 创建数据集

提供名称、说明及示例数组即可创建数据集（每个示例包含 `input`、`output` 和可选的 `metadata`）。

```ts
import { createDataset } from "@arizeai/phoenix-client/datasets";

const { datasetId } = await createDataset({
  name: "questions",
  description: "a simple dataset of questions",
  examples: [
    {
      input: { question: "What is the capital of France" },
      output: { answer: "Paris" },
      metadata: {},
    },
    {
      input: { question: "What is the capital of the USA" },
      output: { answer: "Washington D.C." },
      metadata: {},
    },
  ],
});
// You can now use datasetId to run experiments or add more examples
```

<a id="experiments"></a>

## 实验

`@arizeai/phoenix-client` 提供实验 API，在数据集上运行和评估任务，适用于模型基准测试、输出评估和在 Phoenix 中跟踪实验结果。

<a id="running-an-experiment"></a>

### 运行实验

运行实验通常需要：

1. 创建数据集（或使用已有数据集）
2. 定义对每个示例运行的任务函数
3. 定义一个或多个评估器，为输出评分或打标签
4. 运行实验并检查结果

下面是完整示例：

```ts
import { createDataset } from "@arizeai/phoenix-client/datasets";
import {
  asExperimentEvaluator,
  runExperiment,
} from "@arizeai/phoenix-client/experiments";

// 1. Create a dataset
const { datasetId } = await createDataset({
  name: "names-dataset",
  description: "a simple dataset of names",
  examples: [
    {
      input: { name: "John" },
      output: { text: "Hello, John!" },
      metadata: {},
    },
    {
      input: { name: "Jane" },
      output: { text: "Hello, Jane!" },
      metadata: {},
    },
  ],
});

// 2. Define a task to run on each example
const task = async (example) => `hello ${example.input.name}`;

// 3. Define evaluators
const evaluators = [
  asExperimentEvaluator({
    name: "matches",
    kind: "CODE",
    evaluate: async ({ output, expected }) => {
      const matches = output === expected?.text;
      return {
        label: matches ? "matches" : "does not match",
        score: matches ? 1 : 0,
        explanation: matches
          ? "output matches expected"
          : "output does not match expected",
        metadata: {},
      };
    },
  }),
  asExperimentEvaluator({
    name: "contains-hello",
    kind: "CODE",
    evaluate: async ({ output }) => {
      const matches = typeof output === "string" && output.includes("hello");
      return {
        label: matches ? "contains hello" : "does not contain hello",
        score: matches ? 1 : 0,
        explanation: matches
          ? "output contains hello"
          : "output does not contain hello",
        metadata: {},
      };
    },
  }),
];

// 4. Run the experiment
const experiment = await runExperiment({
  dataset: { datasetId },
  task,
  evaluators,
});
```

> **提示：** 任务和评估器通过 [OpenTelemetry](https://opentelemetry.io/) 插桩。可直接在 Phoenix UI 查看实验运行和评估的详细追踪，用于调试和性能分析。

<a id="eval-tests"></a>

## 评估测试

此包还提供 Vitest 和 Jest 子模块，可将基于数据集的评估编写为普通测试套件。

```bash
npm install -D @arizeai/phoenix-client vitest dotenv
```

```ts
import * as px from "@arizeai/phoenix-client/vitest";
import { expect } from "vitest";

px.describe(
  "text-to-sql",
  () => {
    px.test(
      "select all",
      {
        input: { userQuery: "Get all users" },
        expected: { sql: "SELECT * FROM users;" },
      },
      async ({ input, expected }) => {
        const sql = await generateSql(input.userQuery);
        px.logOutput({ sql });
        expect(sql).toEqual(expected?.sql);
      }
    );
  },
  {
    acceptanceCriteria: [
      // every test must pass (100% of the auto-logged `pass` boolean is true)
      {
        annotationName: "pass",
        metric: "passRate",
        passFn: (a) => a.score === true,
        minPassRate: 1,
      },
    ],
  }
);
```

参考输出可通过三个可互换键之一提供：`expected`、`reference` 或 `output`，以匹配评估器预期的名称。它们都解析到同一位置，即数据集示例的 `output`，并以 `expected` 暴露给评估器和测试主体。同时提供多个键会产生类型错误。

使用 `@arizeai/phoenix-client/vitest/reporter` 或 `@arizeai/phoenix-client/jest/reporter`，在运行结束时打印 Phoenix 数据集和实验链接、标注汇总及验收标准。验收标准在套件完成后决定是否通过：`average` 检查聚合阈值（因此 CI 可允许平均值为 80%，同时仍运行每个用例），`passRate` 则要求至少一定比例的运行满足逐次运行的 `passFn` 谓词。

配置、完整 `describe` / `test` / `test.each` API、验收标准、重复执行、试运行模式及标注详情见 [CI 评估测试](https://arize.com/docs/phoenix/sdk-api-reference/typescript/packages/phoenix-client/ci-evals)、[Vitest](https://arize.com/docs/phoenix/sdk-api-reference/typescript/packages/phoenix-client/ci-evals-vitest)、[Jest](https://arize.com/docs/phoenix/sdk-api-reference/typescript/packages/phoenix-client/ci-evals-jest)和[标注](https://arize.com/docs/phoenix/sdk-api-reference/typescript/packages/phoenix-client/ci-evals-annotations)指南。

<a id="traces"></a>

## 追踪

`@arizeai/phoenix-client` 提供 `traces` 导出，用于从 Phoenix 项目获取追踪数据。

<a id="fetching-traces"></a>

### 获取追踪

使用 `getTraces` 获取追踪，可选过滤、排序和分页。

```ts
import { getTraces } from "@arizeai/phoenix-client/traces";

// Get the latest 10 traces
const result = await getTraces({
  project: { projectName: "my-project" },
  limit: 10,
});
console.log(result.data); // array of trace objects

// Filter by time range and include full span details
const detailed = await getTraces({
  project: { projectName: "my-project" },
  startTime: "2026-03-01T00:00:00Z",
  endTime: new Date(),
  includeSpans: true,
  sort: "latency_ms",
  order: "desc",
});

// Filter by session
const sessionTraces = await getTraces({
  project: { projectName: "my-project" },
  sessionId: "my-session-id",
});

// Filter by error status and latency (requires Phoenix server >= 20.12.0)
const slowFailures = await getTraces({
  project: { projectName: "my-project" },
  filter: "error_count > 0 and latency_ms >= 1000",
});
```

| 参数      | 类型                           | 说明                                                  |
| -------------- | ------------------------------ | ------------------------------------------------------------ |
| `project`      | `ProjectIdentifier`            | 项目（按名称或 ID），**必填**                   |
| `startTime`    | `Date \| string \| null`       | 追踪开始时间下界（包含）                    |
| `endTime`      | `Date \| string \| null`       | 追踪开始时间上界（不包含）                    |
| `sort`         | `"start_time" \| "latency_ms"` | 排序字段                                                   |
| `order`        | `"asc" \| "desc"`              | 排序方向                                               |
| `limit`        | `number`                       | 返回追踪的最大数量                           |
| `cursor`       | `string \| null`               | 分页游标                                            |
| `includeSpans` | `boolean`                      | 包含每条追踪的完整 Span 详情                     |
| `sessionId`    | `string \| string[] \| null`   | 按会话标识符过滤追踪                       |
| `filter`       | `string \| null`               | 追踪过滤表达式                                      |
| `error`        | `boolean \| null`              | 仅返回含有（`true`）或不含（`false`）出错 Span 的追踪 |
| `minLatencyMs` | `number \| null`               | 追踪延迟下界（毫秒，包含）                  |
| `maxLatencyMs` | `number \| null`               | 追踪延迟上界（毫秒，包含）                  |

`error`、`minLatencyMs` 和 `maxLatencyMs` 已弃用，但服务器 >= 20.8.0 仍支持。请改用 `filter` 中的 `error_count > 0` / `error_count == 0`、`latency_ms >= N` 和 `latency_ms <= N`。空表达式不执行过滤，无效表达式返回 HTTP 400。请求下一页时保持相同表达式。

<a id="pagination"></a>

### 分页

使用上一次结果的 `cursor` 获取下一页：

```ts
import { getTraces } from "@arizeai/phoenix-client/traces";

let cursor: string | null = null;
const allTraces = [];

do {
  const result = await getTraces({
    project: { projectName: "my-project" },
    limit: 50,
    cursor,
  });
  allTraces.push(...result.data);
  cursor = result.nextCursor ?? null;
} while (cursor);
```

> **注意：** 要求 Phoenix 服务器 >= 13.15.0。

<a id="trace-annotations"></a>

### 追踪标注

为整个追踪添加结构化反馈（按名称记录标签/分数）。单条追踪使用 `addTraceAnnotation`，批量使用 `logTraceAnnotations`。

```ts
import {
  addTraceAnnotation,
  logTraceAnnotations,
} from "@arizeai/phoenix-client/traces";

// Single annotation
const result = await addTraceAnnotation({
  traceAnnotation: {
    traceId: "abc123",
    name: "correctness",
    label: "correct",
    score: 1.0,
    annotatorKind: "HUMAN",
  },
  sync: true, // returns { id: "..." } when sync, null when async
});

// Batch
await logTraceAnnotations({
  traceAnnotations: [
    {
      traceId: "abc123",
      name: "correctness",
      label: "correct",
      score: 1.0,
      annotatorKind: "HUMAN",
    },
    {
      traceId: "def456",
      name: "faithfulness",
      label: "faithful",
      score: 0.9,
      annotatorKind: "LLM",
    },
  ],
  sync: true,
});
```

保留名称 `note` 会被拒绝；自由文本笔记请使用 `addTraceNote`（见下文）。

<a id="trace-notes"></a>

### 追踪笔记

笔记是一种用于自由文本的特殊标注，适用于开放编码：评审者在尚未建立评判标准时，对追踪记录定性观察。同一追踪可有多条笔记。

```ts
import { addTraceNote } from "@arizeai/phoenix-client/traces";

await addTraceNote({
  traceNote: {
    traceId: "abc123",
    note: "Needs follow-up — unexpected tool call sequence",
  },
});
```

> **注意：** `addTraceNote` 要求 Phoenix 服务器 >= 14.13.0。

<a id="spans"></a>

## Span

`@arizeai/phoenix-client` 提供 `spans` 导出，通过强大过滤能力查询 Span。

<a id="fetching-spans"></a>

### 获取 Span

使用 `getSpans` 获取 Span，可按类型、状态、名称、追踪等过滤。

```ts
import { getSpans } from "@arizeai/phoenix-client/spans";

// Get recent spans
const result = await getSpans({
  project: { projectName: "my-project" },
  limit: 100,
});

// Filter by span kind and status
const errorLLMSpans = await getSpans({
  project: { projectName: "my-project" },
  spanKind: "LLM",
  statusCode: "ERROR",
});

// Filter by name and trace
const spans = await getSpans({
  project: { projectName: "my-project" },
  name: "chat_completion",
  traceIds: ["trace-abc", "trace-def"],
});

// Root spans only
const rootSpans = await getSpans({
  project: { projectName: "my-project" },
  parentId: null,
});
```

| 参数    | 类型                                 | 说明                                                     |
| ------------ | ------------------------------------ | --------------------------------------------------------------- |
| `project`    | `ProjectIdentifier`                  | 项目（按名称或 ID），**必填**                      |
| `startTime`  | `Date \| string \| null`             | 时间下界（包含）                                      |
| `endTime`    | `Date \| string \| null`             | 时间上界（不包含）                                      |
| `limit`      | `number`                             | 返回 Span 的最大数量                               |
| `cursor`     | `string \| null`                     | 分页游标（Span GlobalID）                               |
| `traceIds`   | `string[] \| null`                   | 按追踪 ID 过滤                                           |
| `parentId`   | `string \| null`                     | 按父 Span ID 过滤（`null` 表示仅根 Span）           |
| `name`       | `string \| string[] \| null`         | 按 Span 名称过滤                                          |
| `spanKind`   | `SpanKindFilter \| SpanKindFilter[]` | 按 Span 类型过滤（`LLM`、`CHAIN`、`TOOL`、`RETRIEVER` 等） |
| `statusCode` | `SpanStatusCode \| SpanStatusCode[]` | 按状态码过滤（`OK`、`ERROR`、`UNSET`）                  |

<a id="logging-spans"></a>

### 写入 Span

使用 `logSpans` 以 Phoenix 简化 Span 结构直接向项目提交 Span，该结构与 `getSpans` 的返回结构相同，适用于无需经过 OpenTelemetry 的 Span 回填或迁移。若应用已通过 OpenTelemetry 插桩，请改用 `@arizeai/phoenix-otel` 导出 Span。

```ts
import { logSpans } from "@arizeai/phoenix-client/spans";

const result = await logSpans({
  project: { projectName: "my-project" },
  spans: [
    {
      name: "chat_completion",
      context: { trace_id: "abc123", span_id: "def456" },
      span_kind: "LLM",
      start_time: "2024-01-01T00:00:00Z",
      end_time: "2024-01-01T00:00:01Z",
      status_code: "OK",
      attributes: { "llm.model_name": "gpt-4" },
    },
  ],
});
console.log(`Queued ${result.totalQueued} of ${result.totalReceived} spans`);
```

若请求中的任意 Span 无效或与已有 Span 重复，则不会将任何 Span 加入队列，`logSpans` 会抛出包含 `invalidSpans` 和 `duplicateSpans` 详情的 `SpanCreationError`。

<a id="span-annotations"></a>

## Span 标注

`spans` 导出还提供管理 Span 标注的函数，可为 Span 添加评估、反馈和标签。

<a id="adding-a-single-annotation"></a>

### 添加单个标注

```ts
import { addSpanAnnotation } from "@arizeai/phoenix-client/spans";

const result = await addSpanAnnotation({
  spanAnnotation: {
    spanId: "f8b1c3a2d4e5f678",
    name: "correctness",
    label: "correct",
    score: 1.0,
    explanation: "The response accurately answered the question",
    annotatorKind: "HUMAN",
  },
  sync: true, // wait for the annotation ID to be returned
});
// result: { id: "annotation-id" } when sync: true, null when sync: false
```

<a id="logging-multiple-annotations"></a>

### 写入多个标注

```ts
import { logSpanAnnotations } from "@arizeai/phoenix-client/spans";

const results = await logSpanAnnotations({
  spanAnnotations: [
    {
      spanId: "f8b1c3a2d4e5f678",
      name: "relevance",
      label: "relevant",
      score: 0.95,
      annotatorKind: "LLM",
    },
    {
      spanId: "a1b2c3d4e5f67890",
      name: "relevance",
      label: "irrelevant",
      score: 0.2,
      annotatorKind: "LLM",
    },
  ],
  sync: true,
});
// results: [{ id: "..." }, { id: "..." }]
```

<a id="fetching-span-annotations"></a>

### 获取 Span 标注

```ts
import { getSpanAnnotations } from "@arizeai/phoenix-client/spans";

const result = await getSpanAnnotations({
  project: { projectName: "my-project" },
  spanIds: ["f8b1c3a2d4e5f678", "a1b2c3d4e5f67890"],
  includeAnnotationNames: ["relevance", "correctness"],
  limit: 100,
});
console.log(result.data); // array of span annotation objects
```

| 参数                | 类型                | 说明                                      |
| ------------------------ | ------------------- | ------------------------------------------------ |
| `project`                | `ProjectIdentifier` | 项目（按名称或 ID），**必填**       |
| `spanIds`                | `string[]`          | 需要获取标注的 Span ID，**必填** |
| `includeAnnotationNames` | `string[]`          | 只返回指定名称的标注         |
| `excludeAnnotationNames` | `string[]`          | 排除指定名称的标注             |
| `cursor`                 | `string \| null`    | 分页游标                                |
| `limit`                  | `number`            | 返回标注的最大数量                    |

<a id="sessions"></a>

## 会话

`@arizeai/phoenix-client` 提供 `sessions` 导出，用于管理对话会话及其标注。

<a id="fetching-sessions"></a>

### 获取会话

使用 `listSessions` 列出项目所有会话，或用 `getSession` 按 ID 获取单个会话。

```ts
import {
  listSessions,
  getSession,
  addSessionAnnotation,
  addSessionNote,
} from "@arizeai/phoenix-client/sessions";

// List all sessions for a project
const sessions = await listSessions({
  project: "my-project",
});

for (const session of sessions) {
  console.log(
    `Session: ${session.sessionId}, Traces: ${session.traces.length}`
  );
}

// Get a single session by its ID
const session = await getSession({ sessionId: "my-session-id" });
console.log(session.traces); // array of trace summaries in the session
```

<a id="adding-session-annotations"></a>

### 添加会话标注

```ts
await addSessionAnnotation({
  sessionAnnotation: {
    sessionId: "my-session-id",
    name: "user-satisfaction",
    label: "satisfied",
    score: 0.9,
    annotatorKind: "HUMAN",
  },
});
```

<a id="adding-session-notes"></a>

### 添加会话笔记

会话笔记要求 Phoenix 服务器 `14.17.0` 或更高版本。

```ts
await addSessionNote({
  sessionNote: {
    sessionId: "my-session-id",
    note: "Needs review",
  },
});
```

<a id="projects"></a>

## 项目

`@arizeai/phoenix-client` 提供 `projects` 导出，用于列出项目及管理分配给项目的保留策略和标注配置。

<a id="fetching-projects"></a>

### 获取项目

使用 `getProjects` 列出项目，分页会自动处理。

```ts
import { getProjects } from "@arizeai/phoenix-client/projects";

// List every project
const projects = await getProjects();

for (const project of projects) {
  console.log(`Project: ${project.name} (${project.id})`);
}
```

传入 `nameContains` 可按不区分大小写的项目名称子串过滤。过滤在服务器端执行，要求 Phoenix 服务器 `17.16.0` 或更高版本。

```ts
const agentProjects = await getProjects({ nameContains: "agent" });
```

<a id="assigning-a-retention-policy"></a>

### 分配保留策略

使用 `setProjectRetentionPolicy` 按 GlobalID 分配已有追踪保留策略，通过名称或 GlobalID 选择项目。

```ts
import { setProjectRetentionPolicy } from "@arizeai/phoenix-client/projects";

await setProjectRetentionPolicy({
  projectName: "support-bot",
  policyId: "UHJvamVjdFRyYWNlUmV0ZW50aW9uUG9saWN5OjI=",
});
```

传入 `policyId: null` 可将项目重置为 Phoenix 默认保留策略：

```ts
await setProjectRetentionPolicy({
  projectId: "UHJvamVjdDox",
  policyId: null,
});
```

此辅助函数只修改项目与已有策略的分配关系。创建、读取、更新和删除保留策略不属于 TypeScript 项目辅助函数的范围。

<a id="assigning-annotation-configs"></a>

### 分配标注配置

使用 `assignProjectAnnotationConfig` 和 `unassignProjectAnnotationConfig` 添加或移除单个标注配置，通过名称或 GlobalID 选择项目和配置。两个调用均幂等。这些辅助函数要求 Phoenix 服务器 `17.16.0` 或更高版本。

```ts
import {
  assignProjectAnnotationConfig,
  listProjectAnnotationConfigs,
  setProjectAnnotationConfigs,
  unassignProjectAnnotationConfig,
} from "@arizeai/phoenix-client/projects";

await assignProjectAnnotationConfig({
  projectName: "support-bot",
  configName: "correctness",
});

await unassignProjectAnnotationConfig({
  projectName: "support-bot",
  configName: "correctness",
});
```

使用 `setProjectAnnotationConfigs` 通过配置 GlobalID 替换整个集合。传入空列表可清除所有分配：

```ts
const configs = await listProjectAnnotationConfigs({
  projectName: "support-bot",
});

// Keep only the categorical configs
await setProjectAnnotationConfigs({
  projectName: "support-bot",
  configIds: configs
    .filter((config) => config.type === "CATEGORICAL")
    .map((config) => config.id),
});

await setProjectAnnotationConfigs({
  projectName: "support-bot",
  configIds: [],
});
```

若配置名称包含 `/`，请改用 `configId` 选择，因为服务器无法在 URL 路径中路由名称中的 `/`。

<a id="secrets"></a>

## 密钥

使用 `secrets` 入口以原子方式创建、更新或删除加密的提供商凭证。字符串值创建或更新键，`null` 则删除键。重复键取批次中最后一次出现的值。结果仅包含已变更的键名，绝不返回密钥值。

```ts
import { upsertOrDeleteSecrets } from "@arizeai/phoenix-client/secrets";

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) throw new Error("OPENAI_API_KEY is required");

const result = await upsertOrDeleteSecrets({
  secrets: [
    { key: "OPENAI_API_KEY", value: apiKey },
    { key: "OLD_PROVIDER_API_KEY", value: null },
  ],
});

console.log(result.upsertedKeys);
console.log(result.deletedKeys);
```

启用 Phoenix 身份验证时，管理密钥需要管理员权限。避免记录请求批次或以其他方式保留其中的值。

<a id="examples"></a>

## 示例

运行示例时，使用 `pnpm` 安装依赖并运行：

```bash
pnpm install
pnpx tsx examples/list_datasets.ts
# change the file name to run other examples
```

<a id="compatibility"></a>

## 兼容性

此包使用 [openapi-ts](https://openapi-ts.pages.dev/) 从 Phoenix OpenAPI 规范生成类型。

因此，此包只支持 `arize-phonix` 服务器 8.0.0 及更高版本。

兼容性表：

| Phoenix Client 版本 | Phoenix Server 版本 |
| ---------------------- | ---------------------- |
| ^2.0.0                 | ^9.0.0                 |
| ^1.0.0                 | ^8.0.0                 |

---

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g).
- 📚 阅读 [Phoenix 文档](https://arize.com/docs/phoenix).
- 💡 在 _#phoenix-support_ 频道提问并反馈。
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星。
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)，了解未来方向。
