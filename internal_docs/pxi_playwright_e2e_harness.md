<a id="pxi-playwright-e2e-harness-proposal"></a>
# PXI Playwright 端到端测试框架提案

本提案基于现有 PXI 请求流程和 Phoenix 实验 API，描述通过 Phoenix 前端评测 PXI 的 Playwright 测试框架。

<a id="goals"></a>
## 目标

- 让复杂的前端驱动 Agent 场景易于编写 PXI 端到端测试。
- 在隔离环境中运行 Phoenix，使用确定性的种子数据。
- 通过真实界面测试 PXI，包括路由上下文、模型选择、流式传输和浏览器执行的工具。
- 将每个用例持久化为 Phoenix 实验运行，并附加 LLM 裁判评估。
- 收集足够的产物，无需本地重跑即可调试 Agent 故障。

<a id="current-pxi-mechanisms"></a>
## 当前 PXI 机制

PXI 聊天由前端运行时管理，但模型边界由服务端定义。

- `js/app/src/components/agent/useAgentChat.ts` 创建 AI SDK `Chat` 运行时，并通过 `useChat` 绑定 React。
- `js/app/src/components/agent/useAgentChatPanelState.ts` 将聊天 URL 构造为 `/chat?provider_type=...&provider=...&model_name=...` 或 `/chat?provider_type=custom&provider_id=...&model_name=...`。
- `js/app/src/agent/chat/buildAgentChatRequestBody.ts` 添加 PXI 专用请求字段：`userInstructions`、`traceNameSuffix`、`sessionId`、`ingestTraces`、`exportRemoteTraces`、`contexts` 和 `capabilities`。
- `src/phoenix/server/api/routers/chat.py` 处理 `POST /chat`，根据查询参数构建模型，向消息历史注入 Phoenix 上下文，解析服务端管理的工具，并流式返回响应。
- `src/phoenix/server/agents/tools/registry.py` 公布外部工具和受上下文控制的工具。外部工具目前有 `ask_user` 和 `bash`；提供所需界面上下文时，上下文工具目前有 `set_spans_filter`。
- `js/app/src/agent/extensions/toolRegistry.ts` 按名称分派浏览器执行工具，验证输入、检查能力，并通过 AI SDK 运行时返回工具输出。
- `js/app/src/store/agentStore.ts` 在本地存储的 `arize-phoenix-agent` 下持久化会话，并保存上下文、客户端操作、待处理信息征询和聊天状态等临时运行时状态。

框架不应在测试中重复工具 schema。应观察与用户所见相同的对话记录，并按需为现有流、存储和请求接口添加插桩。

<a id="current-experiment-apis"></a>
## 当前实验 API

Phoenix 已有将 PXI 测试结果持久化为实验所需的 REST 端点。

- 创建或更新带示例的数据集：`src/phoenix/server/api/routers/v1/datasets.py` 中的 `POST /v1/datasets/upload?sync=true`。
- 为数据集创建实验：`src/phoenix/server/api/routers/v1/experiments.py` 中的 `POST /v1/datasets/{dataset_id}/experiments`。
- 创建实验运行：`src/phoenix/server/api/routers/v1/experiment_runs.py` 中的 `POST /v1/experiments/{experiment_id}/runs`。
- 更新或插入实验评估：`src/phoenix/server/api/routers/v1/experiment_evaluations.py` 中的 `POST /v1/experiment_evaluations`。

TypeScript 客户端的 `js/packages/phoenix-client/src/experiments/runExperiment.ts` 已为普通任务实验封装了大部分流程。但 PXI 测试应直接调用 REST 或使用小型封装，因为任务是已完成的浏览器交互，而非由实验运行器管理的函数。

<a id="harness-architecture"></a>
## 测试框架架构

在 `js/app/tests/pxi/` 下添加 PXI 专用 Playwright fixture。

```ts
import { test as base } from "@playwright/test";

export const test = base.extend<{
  phoenix: PhoenixE2EApp;
  pxi: PxiDriver;
}>({
  phoenix: async ({}, use, testInfo) => {
    const app = await startPhoenixForPxiTest(testInfo);
    await use(app);
    await app.stop();
  },
  pxi: async ({ page, phoenix }, use, testInfo) => {
    const driver = new PxiDriver({ page, phoenix, testInfo });
    await use(driver);
    await driver.attachArtifactsOnFailure();
  },
});
```

`PhoenixE2EApp` 应封装服务端生命周期和 API 访问。

```ts
type PhoenixE2EApp = {
  baseURL: string;
  databaseURL: string;
  api: PhoenixApiClient;
  seed(seed: PxiSeedSpec): Promise<PxiSeedResult>;
  logs(): Promise<string[]>;
  stop(): Promise<void>;
};
```

首个实现可在可行时复用现有 Playwright `webServer` 路径，但目标应是每个工作进程独享 Phoenix 服务端，让 PXI 测试自行启用 LLM 凭证、隔离数据库路径和种子脚本，而不影响 `js/app/tests` 其余测试。

<a id="skill-layer"></a>
## 技能层

PXI 端到端测试工作流也应打包为 Agent 技能，但技能应补充具体测试框架，而非替代它。

确定性运行时行为必须由框架提供：启动 Phoenix、隔离 SQLite、初始化数据、驱动 Playwright、观察 PXI 轮次、判断结果、持久化实验记录和收集产物。技能自身无法保证这些，因为测试仍需可导入的代码，在 CI 中运行而无需 Agent 解读指令。

技能应提供编写层：可复用指引、模板、示例和脚手架脚本，供人工或编码 Agent 添加新场景。

建议技能名称：

```txt
phoenix-pxi-playwright
```

建议位置：

```txt
.agents/skills/phoenix-pxi-playwright/
```

建议结构：

```txt
.agents/skills/phoenix-pxi-playwright/
  SKILL.md
  resources/
    authoring-guide.md
    assertion-patterns.md
    seed-fixtures.md
    experiment-persistence.md
    debugging-failures.md
  templates/
    pxi-scenario.spec.ts
    pxi-seed.ts
    pxi-outcome-rubric.md
  scripts/
    scaffold-pxi-test.ts
```

有人要求添加、更新、调试或评审 PXI Playwright 测试时，应触发该技能元数据。

```yaml
---
name: phoenix-pxi-playwright
description: Write, extend, and debug PXI Playwright E2E tests for Phoenix. Use when adding PXI agent frontend tests, authoring LLM-as-judge outcomes, creating seed fixtures, persisting PXI test runs as Phoenix experiments, or debugging PXI E2E failures.
---
```

`SKILL.md` 应保持简短，指向聚焦的资源。应要求 Agent 使用 `js/app/tests/pxi/` 下的具体框架，而非在每个测试中生成专用 Playwright 基础设施。

技能应包含：

- 如何选择 `real`、`recorded` 或 `stubbed` LLM 模式。
- 如何选择或创建种子 fixture。
- 如何先编写确定性断言，再编写裁判断言。
- 如何为 `assertOutcome()` 编写评分标准。
- 如何将运行持久化为 Phoenix 实验。
- 失败后如何检查产物和实验记录。
- 哪些 PXI 内部机制重要：`POST /chat`、`buildAgentChatRequestBody`、`agentStore`、`resolve_tools` 和前端工具分派。

技能不应包含：

- 单独实现的 `PxiDriver`。
- 重复的实验客户端。
- 重复的 PXI 工具 schema。
- 要求 Agent 绕过共享框架的指令。

预期分工：

```txt
js/app/tests/pxi/*
  Runtime code used by Playwright, CI, and humans.

.agents/skills/phoenix-pxi-playwright/*
  Authoring workflow used by coding agents and teammates.
```

技能驱动工作流示例：

1. 用户要求：“添加解释追踪错误的 PXI 端到端测试。”
2. 加载技能，要求 Agent 检查可用种子 fixture。
3. Agent 从 `templates/pxi-scenario.spec.ts` 搭建测试。
4. 测试导入共享 `test` fixture，使用 `pxi.askAndWait()`、`pxi.expectToolCalled()` 和 `pxi.assertOutcome()`。
5. 测试通过 `pxi.persistExperiment()` 持久化结果。
6. Agent 运行相关 Playwright 命令，并报告实验 ID 或产物。

<a id="phoenix-startup"></a>
## Phoenix 启动

框架应使用隔离的 SQLite 数据库启动 Phoenix。

默认使用临时文件型 SQLite 数据库，而非字面上的 `sqlite:///:memory:`。文件数据库仍隔离且可丢弃，但当测试运行器、种子脚本和 Phoenix 服务端不在同一进程时，可避免跨进程可见性问题。

```ts
type PhoenixStartupOptions = {
  database: "temp-sqlite" | { sqlitePath: string };
  seedScript?: string;
  seedDatabasePath?: string;
  env?: Record<string, string>;
};
```

显式设置环境变量。

```txt
PHOENIX_SQL_DATABASE_URL=sqlite:////tmp/pxi-e2e/worker-0/phoenix.db
PHOENIX_AGENTS_ASSISTANT_PROJECT_NAME=pxi-e2e-agent-{workerIndex}
PHOENIX_DISABLE_RATE_LIMIT=True
```

每次运行都应主动选择是否启用 LLM 凭证。

```txt
PXI_E2E_ASSISTANT_PROVIDER=OPENAI
PXI_E2E_ASSISTANT_MODEL=gpt-4.1-mini
PXI_E2E_JUDGE_PROVIDER=OPENAI
PXI_E2E_JUDGE_MODEL=gpt-4.1
OPENAI_API_KEY=...
```

缺少所需凭证时，框架应跳过真实 LLM 测试，除非测试显式使用桩响应或录制模式。

<a id="llm-modes"></a>
## LLM 模式

PXI 端到端测试需要多种可靠性配置。

```ts
type PxiLlmMode = "real" | "recorded" | "stubbed";
```

- `real`：通过 `POST /chat` 使用所选内置或自定义模型，最适合每夜运行和阻止发布的冒烟测试。
- `recorded`：重放捕获的数据流或模型/工具轨迹，最适合针对界面和协议行为的确定性 CI 检查。
- `stubbed`：将 `POST /chat` 或模型提供商路由到确定性响应，最适合前端流和工具分派测试。

第一阶段应支持 `real`，并为 `recorded` 和 `stubbed` 留出明确接入点。

<a id="pxi-driver-api"></a>
## PXI 驱动 API

`PxiDriver` 应封装用户可见操作和 PXI 专用断言。

```ts
class PxiDriver {
  seed(seed: PxiSeedSpec): Promise<PxiSeedResult>;
  gotoProject(projectIdOrName: string): Promise<void>;
  gotoTrace(traceId: string): Promise<void>;
  gotoSpan(spanId: string): Promise<void>;

  open(): Promise<void>;
  close(): Promise<void>;
  setModel(config: PxiModelConfig): Promise<void>;
  acknowledgeConsent(): Promise<void>;

  sendMessage(message: string): Promise<void>;
  waitForTurn(): Promise<PxiTurn>;
  askAndWait(message: string): Promise<PxiTurn>;

  messages(): Promise<PxiMessage[]>;
  latestAssistantMessage(): Promise<string>;

  enumerateTools(): Promise<PxiToolDefinition[]>;
  expectToolCalled(name: string | RegExp): Promise<void>;
  expectToolSequence(names: Array<string | RegExp>): Promise<void>;
  expectNoAgentError(): Promise<void>;

  assertOutcome(expectation: PxiOutcomeExpectation): Promise<PxiOutcomeAssertion>;
  persistExperiment(record?: Partial<PxiExperimentRecord>): Promise<PxiPersistedExperiment>;
}
```

`waitForTurn()` 应等待状态，而非固定时间。应观察已提交用户消息完成渲染、助手停止流式输出、`Thinking...` 加载提示消失、无内联聊天错误，且所有可见的信息征询状态已解决或报告。

```ts
type PxiTurn = {
  userMessage: string;
  assistantText: string;
  toolCalls: PxiToolCall[];
  toolResults: PxiToolResult[];
  errors: PxiError[];
  request?: PxiChatRequestSnapshot;
  responseMetadata?: unknown;
  durationMs: number;
};
```

初始实现可从本地存储或暴露的测试钩子解析 `AgentUIMessage.parts`。更稳健的实现应添加仅测试用插桩，记录每个 PXI 请求、助手流式片段、工具调用和输出，不只依赖 DOM 文本。

当前无法仅通过可见 DOM 可靠实现 `enumerateTools()`。应基于聊天请求/响应路径的插桩，或仅测试用服务端调试接口，捕获 `src/phoenix/server/agents/tools/registry.py` 为当前上下文解析的 `ToolDefinition`。

<a id="test-instrumentation"></a>
## 测试插桩

当前界面未暴露完善 PXI 测试所需的全部数据。应增加轻量、仅测试用插桩，由 `import.meta.env.MODE === "test"` 或等效 Playwright 环境标志保护。

暴露浏览器全局收集器，例如：

```ts
window.__PXI_E2E__ = {
  requests: [],
  turns: [],
  toolCalls: [],
  toolResults: [],
  contexts: [],
};
```

建议钩子：

- 在 `buildAgentChatRequestBody` 中，记录发出的 `contexts`、`capabilities`、`sessionId`、`ingestTraces` 和模型 URL。
- 在 `handleRegisteredAgentToolCall` 中，记录原始工具调用、解析错误、能力错误、处理器错误和成功输出。
- 在 `useAgentChat` 的 `onFinish` 中，记录最终消息和助手元数据。

这样保持生产行为不变，同时使测试可靠且可检查。

<a id="outcome-assertion"></a>
## 结果断言

`assertOutcome()` 首阶段应使用 LLM 裁判，同时继续运行工具使用和无 Agent 错误的确定性断言。

```ts
await pxi.expectToolCalled("set_spans_filter");
await pxi.expectNoAgentError();

await pxi.assertOutcome({
  name: "latency-root-cause",
  rubric: `
    The assistant identifies the slowest span as the root cause of latency.
    It cites evidence from the trace or visible Phoenix context.
    It does not invent services, spans, or errors that are not present.
  `,
  scoreThreshold: 0.8,
});
```

裁判输入应包含数据集示例输入、预期输出（如提供）、页面 URL、PXI 对话记录、公布和观察到的工具、工具结果及界面上下文快照。

```ts
type PxiOutcomeExpectation = {
  name: string;
  rubric: string;
  scoreThreshold?: number;
  mustMention?: string[];
  mustNotMention?: string[];
  mustUseTools?: string[];
  metadata?: Record<string, unknown>;
};

type PxiOutcomeAssertion = {
  passed: boolean;
  label: "pass" | "fail";
  score: number;
  explanation: string;
  evidence: string[];
  metadata: Record<string, unknown>;
};
```

裁判模型必须与被测 PXI 模型分开存储。

```ts
type PxiModelConfig = {
  assistantProvider: string;
  assistantModel: string;
  judgeProvider: string;
  judgeModel: string;
};
```

<a id="persisting-as-phoenix-experiments"></a>
## 持久化为 Phoenix 实验

每个 PXI 测试用例应映射为一个 Phoenix 数据集示例，每次 Playwright 执行应映射为一次实验运行和一条 LLM 评估标注。

数据集名称：

```txt
PXI E2E Agent Tests
```

示例 ID：

```txt
{suiteName}:{testName}:{fixtureName}:{scenarioVersion}
```

示例结构：

```ts
type PxiDatasetExample = {
  id: string;
  input: {
    prompt: string;
    route: string;
    seed: string;
    scenario: string;
  };
  output: {
    rubric: string;
  };
  metadata: {
    suite: string;
    test: string;
    fixture: string;
    version: string;
  };
};
```

持久化流程：

1. 使用 `action: "update"` 和稳定的 `example_ids`，通过 `POST /v1/datasets/upload?sync=true` 更新或插入数据集。
2. 从 `GET /v1/datasets/{id}/examples` 获取示例，解析实验运行所需的 `DatasetExample` GlobalID。
3. 通过 `POST /v1/datasets/{dataset_id}/experiments` 创建实验。
4. 通过 `POST /v1/experiments/{experiment_id}/runs` 创建运行。
5. 通过 `POST /v1/experiment_evaluations` 更新或插入裁判结果。

实验命名：

```txt
pxi-e2e-{branch}-{sha}
pxi-e2e-nightly-{date}
pxi-e2e-local-{user}-{timestamp}
```

实验元数据：

```ts
type PxiExperimentMetadata = {
  kind: "pxi-playwright-e2e";
  branch?: string;
  gitSha?: string;
  playwrightProject: string;
  assistantProvider: string;
  assistantModel: string;
  judgeProvider: string;
  judgeModel: string;
  seedDatabase?: string;
  seedScript?: string;
};
```

实验运行输出：

```ts
type PxiExperimentRunOutput = {
  prompt: string;
  assistantText: string;
  transcript: PxiMessage[];
  toolCalls: PxiToolCall[];
  toolResults: PxiToolResult[];
  contexts: unknown[];
  capabilities: Record<string, boolean>;
  url: string;
  durationMs: number;
  artifacts: Record<string, string>;
};
```

评估结果：

```ts
{
  name: "pxi_outcome",
  annotator_kind: "LLM",
  result: {
    label: assertion.passed ? "pass" : "fail",
    score: assertion.score,
    explanation: assertion.explanation,
  },
  metadata: {
    rubric: expectation.rubric,
    evidence: assertion.evidence,
    judgeModel,
  },
}
```

应允许测试在持久化之后失败。即使 `assertOutcome()` 失败，保留实验运行和失败评估记录也更有价值。

<a id="seed-fixtures"></a>
## 种子 fixture

种子 fixture 应面向场景，而非面向数据表。

```txt
empty-project
project-with-traces
trace-with-slow-span
trace-with-error
project-with-span-filterable-traces
dataset-with-experiments
```

每个种子应返回稳定句柄。

```ts
type PxiSeedResult = {
  fixture: string;
  projectId?: string;
  projectName?: string;
  traceId?: string;
  spanId?: string;
  datasetId?: string;
  metadata: Record<string, unknown>;
};
```

种子脚本可以将准备好的 SQLite 数据库复制到工作进程临时目录，也可在服务端启动前，对 `PHOENIX_SQL_DATABASE_URL` 运行脚本。

<a id="example-test"></a>
## 测试示例

```ts
import { test } from "./pxi";

test("PXI explains trace latency", async ({ pxi }) => {
  const seed = await pxi.seed("trace-with-slow-span");

  await pxi.gotoTrace(seed.traceId);
  await pxi.open();
  await pxi.acknowledgeConsent();

  const turn = await pxi.askAndWait("Why is this trace slow?");

  await pxi.expectNoAgentError();
  await pxi.expectToolCalled(/bash|set_spans_filter/);

  const assertion = await pxi.assertOutcome({
    name: "latency-root-cause",
    rubric: `
      The assistant should identify the slowest span and explain that it dominates trace latency.
      The answer should cite evidence from the trace or UI context.
      The answer should not claim that no trace is selected.
    `,
    scoreThreshold: 0.8,
    metadata: { traceId: seed.traceId },
  });

  await pxi.persistExperiment({ assertion, turn });
});
```

预期的具体工具名应因场景而异。当前已检查代码中，`set_spans_filter` 是唯一的上下文 PXI 工具，而 `ask_user` 和 `bash` 始终作为外部工具公布。

<a id="debug-artifacts"></a>
## 调试产物

失败时，框架应附加：

- Playwright 追踪。
- 浏览器控制台日志。
- 网络失败及失败的 `POST /chat` 响应。
- Phoenix 服务端日志。
- PXI 请求体快照。
- PXI 流式消息快照。
- 工具调用和输出。
- 活动路由上下文与已挂载上下文。
- 持久化成功时的实验 ID、运行 ID 和评估 ID。

<a id="implementation-plan"></a>
## 实施计划

1. 添加 `js/app/tests/pxi/fixtures.ts`，提供 `PhoenixE2EApp` 和 `PxiDriver` fixture。
2. 为每个工作进程添加独立 Phoenix 启动，使用临时文件型 SQLite 和环境变量注入。
3. 添加种子 fixture 约定及一个 `trace-with-slow-span` 种子。
4. 添加仅测试用 PXI 插桩，记录请求、轮次、工具和上下文快照。
5. 实现 `open`、`acknowledgeConsent`、`sendMessage`、`waitForTurn`、`askAndWait`、`expectNoAgentError` 和对话记录提取。
6. 使用配置的裁判模型和结构化 JSON 输出，实现 `assertOutcome()`。
7. 通过现有 REST 端点实现实验持久化。
8. 添加一个真实 LLM 冒烟测试，以及一个确定性或桩响应框架测试。

<a id="open-questions"></a>
## 待解决问题

- PXI 端到端测试应放在常规 `js/app/tests` Playwright 项目中，还是因需要 LLM 凭证而单独建项目，仅按需或每夜运行？
- 实验结果应持久化到被测隔离 Phoenix 实例，还是可选地记录到长期运行实例，以跨 CI 运行跟踪趋势？
- 仅测试用 PXI 插桩应使用浏览器全局变量，还是通过小型应用级测试 provider 暴露，以避免全局变量？
- `recorded` 模式应重放完整 AI SDK 数据流，还是在流协议之前的模型提供商层设置桩响应？
