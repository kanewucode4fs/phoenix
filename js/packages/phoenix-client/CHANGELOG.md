# @arizeai/phoenix-client

## 7.16.1

### 补丁变更

- 7b9f900: 将评估器元数据移到实验评估请求体的顶层

## 7.16.0

### 次版本变更

- f8ae2fc: 为 `projects` 子路径添加 `listProjectAnnotationConfigs`、`assignProjectAnnotationConfig`、`unassignProjectAnnotationConfig` 和 `setProjectAnnotationConfigs` 辅助函数，管理项目使用的标注配置。

## 7.15.0

### 次版本变更

- 5b37f12: 为 `prompts` 子路径添加 `upsertPromptVersionTag` 和 `deletePromptVersionTag` 辅助函数，用于创建、移动和删除提示词范围的版本标签。

## 7.14.0

### 次版本变更

- aab229f: 为 `datasets` 子路径添加 `createDatasetSplit`、`updateDatasetSplit` 和 `deleteDatasetSplit` 辅助函数。它们通过名称或 GlobalID 选择数据集，在已有数据集上创建划分、局部更新划分字段、幂等添加或移除示例成员，并在不删除示例的情况下删除划分。要求 Phoenix 服务器 19.20.0 或更高版本。
  
  同时从 datasets 子路径导出生成的 `DatasetSplit` 响应类型和 `DatasetIdentifier` 选择器类型。

## 7.13.0

### 次版本变更

- c282563: 为新的 `secrets` 子路径添加 `upsertOrDeleteSecrets` 辅助函数。通过 `PUT /v1/secrets` 对有序键/值或 null 批次原子创建、更新或删除，仅返回受影响键名，并避免在辅助函数输出和错误消息中暴露提交值。

## 7.12.0

### 次版本变更

- dab09f1: 为 `getTraces` 和 `listSessions` 添加 `filter` 表达式（要求 Phoenix 服务器 >= 20.12.0）。弃用独立的追踪错误和延迟参数，但保留其行为及对服务器 >= 20.8.0 的支持。

## 7.11.0

### 次版本变更

- 2b73847: `promptVersion()` 接收 `metadata`，使提示词版本可携带任意 JSON 元数据。

## 7.10.0

### 次版本变更

- c839254: 为 `getTraces` 添加 `error`、`minLatencyMs` 和 `maxLatencyMs` 过滤器，对应 `GET /v1/projects/{id}/traces` 查询参数（要求 Phoenix 服务器 >= 20.8.0）。

## 7.9.0

### 次版本变更

- bf047af: 新增 Meta（Muse Spark 模型）作为内置的 OpenAI 兼容模型提供商（`META`）。

## 7.8.0

### 次版本变更

- 58b7017: 新增 Z.ai（GLM 模型）作为内置的 OpenAI 兼容模型提供商（`ZAI`）。

## 7.7.1

### 补丁变更

- 1cdff14: 在 `getSession` 和 `listSessions` 返回的高层 `Session` 对象上公开累计提示词、补全和总 Token 数。

## 7.7.0

### 次版本变更

- 37916d7: 为 projects 入口添加 `setProjectRetentionPolicy`，用于按 GlobalID 分配已有保留策略，或将项目重置为默认策略。
- c48e50e: 为 traces 子路径添加 `transferTraces`，用于在 Phoenix 项目间移动追踪。
- 773c5e5: 通过 `@arizeai/phoenix-client/users` 入口添加类型化的 `getCurrentUser` 辅助函数。

### 补丁变更

- b27561d: 将可选 `openai` peer 依赖范围扩大到 `^6.10.0 || ^7.0.0`，使已使用 OpenAI SDK v7 的应用可安装客户端，而不发生 peer 冲突。

## 7.6.0

### 次版本变更

- d328c3e: 为 `prompts` 子路径添加 `deletePrompt` 辅助函数。它接收 `prompt` 选择器（`{ name }` 或 `{ promptId }`），与 `getPrompt` 的现有选择器风格一致，并调用 `DELETE /v1/prompts/{prompt_identifier}`（Phoenix 服务器 >= 13.20.0）。版本级选择器（`{ versionId }`、`{ name, tag }`）会被拒绝，不会扩大到整个提示词。删除会级联到提示词的所有版本及其版本标签和标签。
  
  还从 `types/prompts` 导出提示词级选择器联合类型 `PromptIdentifier`。

## 7.5.0

### 次版本变更

- 0ed987a: 重新启用 PXI Agent 会话服务器版本检查。连接的 Phoenix 服务器早于 Agent 会话聊天契约（服务器 < 20.0.0）时，PXI 现在会在启动时快速失败并给出明确升级提示，而不是首次发送时返回 404。phoenix-client 为其余 Agent 会话路由（列出、获取、局部更新、压缩、工具输出）添加能力要求，从包根入口导出全部 Agent 会话要求，并通过客户端配置的 fetch 调用 `getServerVersion`。

## 7.4.0

### 次版本变更

- 90729f3: 为 `PATCH /v1/prompts/{prompt_identifier}` 添加 `updatePrompt`（说明和元数据；要求 Phoenix 服务器 >= 19.18.0）。

## 7.3.1

### 补丁变更

- c892873: 为实验标签 REST 路由添加生成类型（`GET`/`POST /v1/experiments/{experiment_id}/tags` 和 `DELETE /v1/experiments/{experiment_id}/tags/{tag_identifier}`）

## 7.3.0

### 次版本变更

- d04f0fc: 引入 `PHOENIX_ENDPOINT` 作为 API 访问的规范基础 URL，与用于追踪导出的 `PHOENIX_COLLECTOR_ENDPOINT` 配套。

  此前 TypeScript 客户端仅读取 `PHOENIX_HOST`，因此将 `PHOENIX_COLLECTOR_ENDPOINT` 指向远程 Phoenix 后再读取 Span，会静默访问 `http://localhost:6006`。客户端基础 URL 现在依次解析 `PHOENIX_ENDPOINT`、追踪导出变量 `PHOENIX_COLLECTOR_ENDPOINT` 和 `OTEL_EXPORTER_OTLP_ENDPOINT`（移除任何 `/v1/traces` 路径），最后使用旧版 `PHOENIX_HOST`，与 Python 客户端逐层一致，使相同环境从任一语言连接同一服务器。

  `PHOENIX_BASE_URL` 作为未文档化的兼容性回退，优先级低于追踪导出变量。客户端文档多年使用此名称，但没有代码读取它，因此依照文档设置的值此前无效；将其排在其他变量之后，可使这些配置开始生效，而不会重定向同时设置两者的用户。它也不再能够单独取代发现的 `.env.phoenix`，因此 shell 中遗留的旧值不会重定向 `px setup` 配置的项目。

  解析链中的空值和纯空白值现在均视为未设置，因此 `export PHOENIX_ENDPOINT=` 会回退到下一变量，不会使所有使用方滞留在 localhost。

  实验和测试套件追踪遵循与 `register()` 相同的规则：显式指定 `baseUrl` 创建的客户端将 Span 导出到该服务器；基础 URL 来自环境的客户端则由追踪导出变量决定。发现的 `.env.phoenix` 中存在无法解析的端点时，现在会警告后回退，不再中止运行，跨层级凭证警告也适用于此路径。

  `@arizeai/phoenix-config` 新增 `ENV_PHOENIX_ENDPOINT`、`ENV_OTEL_EXPORTER_OTLP_ENDPOINT`、`ENV_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`、`getBaseUrlFromEnvironment[WithSource]()`、`getBaseUrlFromValues()`（对注入的环境记录使用相同优先级）、`getTraceExportEndpointFromEnvironment()` 和 `PHOENIX_CONNECTION_ENV_KEYS`（用于保持测试环境整洁）。

### 补丁变更

- 更新依赖 [d04f0fc]
- 更新依赖 [5420522]
  - @arizeai/phoenix-config@0.5.0
  - @arizeai/phoenix-otel@2.2.0

## 7.2.0

### 次版本变更

- 59aa7cb: 为新的 `@arizeai/phoenix-client/projects` 入口添加 `getProjects` 辅助函数。支持自动游标分页及可选的 `nameContains` 过滤器，映射到 `GET /v1/projects` 的 `name_contains` 查询参数（不区分大小写的子串匹配，要求 Phoenix 服务器 >= 17.16.0）。

## 7.1.1

### 补丁变更

- e35712a: 重新发布，以恢复失败的发布（版本已存在于 npm）

## 7.1.0

### 次版本变更

- df7057a: 为 `getSpans` 添加 `spanIds` 过滤器，支持按 Span ID 获取 Span（要求 Phoenix 服务器 >= 19.6.0）

## 7.0.1

### 补丁变更

- a6c3f88: 修复 `resumeExperiment` 和 `resumeEvaluation` 在首次错误时泄漏分离工作任务的问题。两者此前使用 `Promise.all([producer, ...workers])`，某个工作任务抛错（如启用 `stopOnFirstError`）时立即拒绝，但其余并发工作任务和生产者仍继续运行，在函数已返回或抛错后继续调用 API 并记录日志。现在通过 `Promise.allSettled` 等待每个任务结束，按优先级分类拒绝结果，确保后台工作不超出调用生命周期。也修复了这些延迟控制台输出引起的间歇 CI 清理错误（`Closing rpc while "onUserConsoleLog" was pending`）。

## 7.0.0

### 主版本变更

- 4867e34: `@arizeai/phoenix-client` 现在要求 AI SDK v7。可选 `ai` peer 依赖要求 v7（`^7.0.0`，此前为 `^6.0.90`）。AI SDK v7 不再自行通过全局追踪提供程序生成 OpenTelemetry Span；要追踪实验任务内的 AI SDK 调用，请在任务内构造并为每次调用传入 `@ai-sdk/otel` 集成：`generateText({ ..., telemetry: { integrations: [new OpenTelemetry()] } })`（见 `examples/run_experiment_with_ai_sdk.ts`）。`@arizeai/phoenix-evals` 的 Phoenix 评估器自动追踪，无需配置。核心客户端 API 保留 Node.js 18 兼容性，基于 AI SDK v7 的功能要求 AI SDK v7 支持的 Node.js 版本。检查已发布声明的类型现在要求 TypeScript >= 5.3：prompts 入口的 `.d.ts` 文件使用 `with { "resolution-mode": "import" }` 导入属性，旧 TypeScript 无法解析（`skipLibCheck` 也无法抑制）。

## 6.14.2

### 补丁变更

- 更新依赖 [dc451a6]
  - @arizeai/phoenix-otel@2.1.0

## 6.14.1

### 补丁变更

- 更新依赖 [30f0827]
  - @arizeai/phoenix-otel@2.0.0

## 6.14.0

### 次版本变更

- d6b1cbb: 为 Phoenix TypeScript 客户端添加可复用、支持凭证刷新的 fetch 封装，
  用于 OAuth 验证的 CLI API 和 PXI 请求，并将每个
  配置档案绑定到签发其 OAuth 令牌的端点。

## 6.13.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

### 补丁变更

- 更新依赖 [f94067b]
  - @arizeai/phoenix-config@0.4.0
  - @arizeai/phoenix-otel@1.2.0

## 6.12.2

### 补丁变更

- 更新依赖 [c0ab6a9]
  - @arizeai/phoenix-config@0.3.0
  - @arizeai/phoenix-otel@1.1.1

## 6.12.1

### 补丁变更

- 更新依赖 [1e7d9fc]
  - @arizeai/phoenix-config@0.2.0
  - @arizeai/phoenix-otel@1.1.0

## 6.12.0

### 次版本变更

- 7947440: 为 `@arizeai/phoenix-client/spans` 添加 `logSpans`，对应 Python 客户端的 `log_spans` API。它使用 Phoenix 简化 Span 结构（与 `getSpans` 返回结构相同）直接向项目提交 Span，无需 OpenTelemetry。请求中任意 Span 无效或重复时，抛出新的 `SpanCreationError`，包含 `invalidSpans`/`duplicateSpans` 详情。

## 6.11.2

### 补丁变更

- 7afa183: 修复 `PHOENIX_TEST_TRACKING=false` 未能可靠禁用 vitest/jest 评估套件记录的问题。现在稳健读取该标志（容忍外围引号和空白），进程首次发现禁用后，会在整个进程中锁定关闭，因此某个套件无法再通过运行中修改环境为其他套件重新启用记录。运行和标注上传路径也直接遵循此标志作为保护。

## 6.11.1

### 补丁变更

- a027ada: 将 CI 评估测试环境变量 `PHOENIX_TEST_TRACING` 重命名为 `PHOENIX_TEST_TRACKING`，与内部“tracking”术语（`isTrackingEnabled`、`SuiteState.trackingDisabled`）一致。行为不变：设置 `PHOENIX_TEST_TRACKING=false` 可在本地运行套件，不将数据集、实验、运行或标注同步到 Phoenix。

  **测试版破坏性变更：** 若采用了 6.11.0 的测试版测试 API 并设置 `PHOENIX_TEST_TRACING=false`，请改为 `PHOENIX_TEST_TRACKING=false`。旧名称不再读取。

## 6.11.0

### 次版本变更

- 7efabf6: **测试版：** 为 `@arizeai/phoenix-client` 添加基于 vitest/jest 的 CI 评估测试 API。新入口 `./vitest`、`./vitest/reporter`、`./jest` 和 `./jest/reporter` 提供 Phoenix 报告器（计分板和结果表）、带优化 `direction`（"maximize"/"minimize"）的验收标准支持，以及将运行写回 Phoenix 的追踪功能。`jest` 和 `vitest` 作为可选 peer 依赖添加。

  此 API 处于测试阶段，未来发布中可能变化。

## 6.10.1

### 补丁变更

- 0347f22: 修复使用自定义示例 ID 上传数据集时，`evaluateExperiment` 无法将实验运行匹配到数据集示例的问题。运行现在在 `datasetExampleId` 中统一使用节点 GlobalID 标识示例；此前进程内创建的运行记录自定义示例 ID，服务器获取的运行记录 GlobalID。评估示例查询也改以 GlobalID 为键。运行记录在早于节点 ID 的服务器上还会回退到示例 `id` 字段（该字段在这些服务器中存放 GlobalID），而不再提交空 `dataset_example_id`。

## 6.10.0

### 次版本变更

- 6dceb10: 将标注批量删除命令重构为实体在前的复合名词：
  `px span delete-annotations` 改为 `px span-annotations delete`，
  `px trace delete-annotations` 改为 `px trace-annotations delete`，以及
  `px session delete-annotations` 改为 `px session-annotations delete`。标志
  集合、授权条件（`--all` XOR `[--start-time, --end-time)`）、载荷
  结构及退出码不变。

  为 `addTraceNote`、`addSpanNote` 和
  `addSessionNote`（及生成的 REST 类型）添加可选请求体字段 `identifier`。非空时，笔记按
  `(entity_id, name='note', identifier)` 更新或插入，因此重复调用时，
  相同标识符会覆盖已有笔记，而不是追加。为
  辅助函数提供 `identifier` 时，现在还会调用
  `ensureServerCapability` 检查新增标识符请求体参数的
  能力要求，使调用方在旧 Phoenix 服务器上快速失败（否则服务器会
  静默丢弃该字段并追加自动生成的笔记）。

## 6.9.3

### 补丁变更

- 更新依赖 [559acf8]
  - @arizeai/phoenix-otel@1.0.2

## 6.9.2

### 补丁变更

- d0cc4c4: 将 `openapi-fetch` 从 `^0.12.5` 更新到 `^0.17.0`。

## 6.9.1

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。
- 更新依赖 [5d14f23]
  - @arizeai/phoenix-config@0.1.4
  - @arizeai/phoenix-otel@1.0.1

## 6.9.0

### 次版本变更

- 2993b04: 为 `traces` 子路径添加 `addTraceAnnotation` 和 `logTraceAnnotations`。通过公开已有 `/v1/trace_annotations` REST 端点，为追踪提供结构化（标签/分数/说明）反馈，使 TypeScript 客户端与 Python 客户端对齐。

### 补丁变更

- 2993b04: 澄清 `addSpanNote` 和 `addTraceNote` 的 TSDoc 及重新生成的 OpenAPI 说明。此前措辞暗示结构化标注“按名称唯一”，这是错误的；标注以 `(name, target_id, identifier)` 为键，因此提供不同标识符即可在同一 Span/追踪/会话中保存多个同名标注。笔记仍通过自动生成的 UUIDv4 标识符保持仅追加。
- 4e20267: 为 Phoenix CLI 添加会话标注和笔记命令，并为 TypeScript 客户端添加会话笔记辅助函数。创建会话笔记要求 Phoenix 服务器 14.17.0 或更高版本。

## 6.8.1

### 补丁变更

- e381885: 为数据集上传（`createDataset`、`appendDatasetExamples`）中的 `example_ids` 添加服务器版本检查，使面向 15.0.0 之前的 Phoenix 服务器的调用方看到明确能力错误，而非令人困惑的服务器错误。
- 187df7e: 重新生成会话笔记端点的 REST API 类型。

## 6.8.0

### 次版本变更

- a4dad8b: 添加 `addTraceNote()` 辅助函数，通过 `POST /v1/trace_notes` 创建追踪笔记。调用会执行服务器版本预检，连接的 Phoenix 服务器过旧时抛出描述性错误。要求 Phoenix 服务器 >= 14.13.0。

## 6.7.0

### 次版本变更

- e19a038: 为 `getSpans()` 添加 `attributes` 过滤器，支持类型感知的属性匹配。传入 `Record<string, string | number | boolean>`，以 AND 语义按属性键值对过滤 Span；JS 值类型决定如何匹配存储属性（如 `{ "user.id": 12345 }` 匹配存储整数，`{ "user.id": "12345" }` 匹配存储字符串）。要求 Phoenix 服务器 >= 14.9.0。

## 6.6.2

### 补丁变更

- 8444575: 将 `@anthropic-ai/sdk`、`openai` 和 `ai` 从 `optionalDependencies` 移到可选 `peerDependencies`。使用方不再自动安装这些提供商 SDK，只有使用方已依赖它们时才会安装。

## 6.6.1

### 补丁变更

- 1449f3d: 从 phoenix-otel 重新导出 OpenInference 语义约定，并更新 phoenix-client 从 phoenix-otel 导入，不再直接依赖 @arizeai/openinference-semantic-conventions。
- 更新依赖 [1449f3d]
  - @arizeai/phoenix-otel@1.0.0

## 6.6.0

### 次版本变更

- c70eca6: 为评估器参数添加可选 `traceId`，便于评估器获取和分析任务追踪，进行轨迹评估

## 6.5.5

### 补丁变更

- 1028be5: 将整理过的包文档和示例打包到 npm 包的 `docs/` 下。
- 更新依赖 [1028be5]
  - @arizeai/phoenix-otel@0.4.3

## 6.5.4

### 补丁变更

- b4ded15: 使用最新功能更新各包 README

  - phoenix-client：添加会话章节，说明 `listSessions`、`getSession` 和 `addSessionAnnotation`
  - phoenix-evals：添加完整预置评估器表格（简洁性、正确性、文档相关性、拒绝回答、工具评估器），修复 `bindEvaluator` 导入路径
  - phoenix-mcp：扩展工具覆盖范围章节，提供完整准确的工具列表
  - phoenix-config：以完整文档替换单行占位说明（安装、环境变量、使用示例）
  - phoenix-cli：添加 `px annotation-config` 命令文档

- 更新依赖 [b4ded15]
  - @arizeai/phoenix-config@0.1.3

## 6.5.3

### 补丁变更

- 更新依赖 [e4bdcf6]
  - @arizeai/phoenix-config@0.1.2

## 6.5.2

### 补丁变更

- d204898: docs: 在包 README 中记录近期新增的命令和方法

## 6.5.1

### 补丁变更

- 91949d7: 为 getSpans 添加 name、spanKind 和 statusCode 过滤参数

## 6.5.0

### 次版本变更

- 9769f90: 为 phoenix-client 添加服务器版本检查。客户端现在从响应头读取服务器版本，并在调用新 API 路由或使用新参数前验证最低版本要求，避免客户端版本高于连接服务器时出现令人困惑的错误。

## 6.4.0

### 次版本变更

- 83b7f68: 添加 `getSessionTurns` 函数，获取会话中按顺序排列的对话轮次（根 Span 输入/输出）

## 6.3.0

### 次版本变更

- d951320: 为 `getSpans` 添加 `parentId` 参数，按父 Span ID 过滤

## 6.2.0

### 次版本变更

- 6d896e3: 为 `getSpans` 和 MCP `get-spans` 工具添加 `traceIds` 参数，按追踪 ID 过滤 Span。

## 6.1.0

### 次版本变更

- 6296d0a: 将 `listSessions` 的 `projectIdentifier: string` 替换为 `ProjectIdentifier` 判别联合类型。调用方现在可传入 `{ project: "name-or-id" }`、`{ projectId: "..." }` 或 `{ projectName: "..." }`，更明确表达意图并改善 IDE 自动补全。
- 6296d0a: 添加 `getSession` 和 `listSessions` API 查询会话数据。`getSession` 按 ID 或名称获取单个会话，`listSessions` 则通过基于游标的分页返回项目会话。

### 补丁变更

- b8ba989: 移除已弃用的 `ProjectSelector` 类型别名，请改用 `ProjectIdentifier`。

## 6.0.0

### 主版本变更

- 03b10a8: feat: 将 zod 从 v3 升级到 v4

  破坏性变更：将 zod 从 v3 升级到 v4。这会改变使用
  `z.looseObject()`（此前为 `.passthrough()`）模式的 TypeScript 推断类型，现在其
  输出类型包含 `[x: string]: unknown`。使用这些类型的使用方可能需要
  更新代码。此外，`ZodError.errors` 已替换为
  `ZodError.issues`，`z.record()` 现在要求显式键模式，且
  `zod-to-json-schema` 已替换为原生 `z.toJSONSchema()`。

### 补丁变更

- 更新依赖 [03b10a8]
  - @arizeai/phoenix-otel@0.4.2

## 5.9.0

### 次版本变更

- b18325b: feat: 将 AI SDK 升级到 v6

### 补丁变更

- db24319: fix: 改进实验运行输出的格式和清晰度
- 更新依赖 [db24319]
  - @arizeai/phoenix-config@0.1.1

## 5.8.2

### 补丁变更

- 8be1940: 将 `@arizeai/openinference-vercel` 依赖更新到 `^2.7.0`。
- 更新依赖 [7456462]
  - @arizeai/phoenix-otel@0.4.1

## 5.8.1

### 补丁变更

- 更新依赖 [a8896db]
  - @arizeai/phoenix-otel@0.4.0

## 5.8.0

### 次版本变更

- af4dc46: 为 Phoenix CLI 添加提示词内省命令
  - `px prompts`：列出全部可用提示词及名称和说明
  - `px prompt <identifier>`：显示指定提示词，支持 `--tag` 和 `--version` 选项
  - `--format text`：使用 XML 风格角色标签输出提示词内容，以便通过管道传给 Claude Code 等 AI 助手
  - 美化输出现在包含完整工具定义及参数、类型和说明
  - 为 phoenix-client 添加 `listPrompts` 函数

## 5.7.0

### 次版本变更

- 01eb1fb: feat: 添加 spanId 支持，将数据集示例关联到追踪

  - 为 `Example` 接口添加 `spanId` 字段，将数据集示例关联回来源 Span
  - 更新 `createDataset`，接收含 `spanId` 的示例并传给 API
  - 更新 `appendDatasetExamples`，接收含 `spanId` 的示例并传给 API
  - 为 Span ID 功能添加完整单元测试
  - 添加示例脚本，展示如何从 Span 创建带追踪关联的数据集

  此功能支持从数据集追溯 Phoenix 中的原始追踪，便于理解数据集示例的来源。

## 5.6.1

### 补丁变更

- ed59696: feat: 更新生成的 API 模式

## 5.6.0

### 次版本变更

- 0f2950e: 集中管理 Phoenix 配置

### 补丁变更

- 更新依赖 [0f2950e]
  - @arizeai/phoenix-config@0.1.0

## 5.5.5

### 补丁变更

- 5132ce4: 将 openai 更新到最新版本

## 5.5.4

### 补丁变更

- 4208604: 触发 changeset 发布
- 更新依赖 [4208604]
  - @arizeai/phoenix-otel@0.3.4

## 5.5.3

### 补丁变更

- c96475c: 触发 changeset 发布
- 更新依赖 [c96475c]
  - @arizeai/phoenix-otel@0.3.3

## 5.5.2

### 补丁变更

- 857b617: 添加包链接
- 更新依赖 [857b617]
  - @arizeai/phoenix-otel@0.3.2

## 5.5.1

### 补丁变更

- 更新依赖 [ce5febf]
  - @arizeai/phoenix-otel@0.3.1

## 5.5.0

### 次版本变更

- cb45336: 创建数据集或添加示例时支持划分

## 5.4.1

### 补丁变更

- b87d2a4: 正确处理 baseURL 中的子路径

## 5.4.0

### 次版本变更

- 885be2a: 使 phoenix-client 能直接接收 Phoenix 评估器

## 5.3.0

### 次版本变更

- 557865c: 添加实验恢复和管理功能

  **新增 API：**

  - `createExperiment()`：创建实验，但不运行
  - `resumeExperiment()`：恢复未完成的实验运行（处理失败或缺失的运行）
  - `resumeEvaluation()`：为已完成实验添加评估，或重试失败评估
  - `listExperiments()`：列出实验，支持过滤和分页
  - `deleteExperiment()`：删除实验

### 补丁变更

- b000189: 修复通道错误问题
- 0c92232: 创建提示词时允许元数据

## 5.2.1

### 补丁变更

- 更新依赖 [419ea76]
  - @arizeai/phoenix-otel@0.3.0

## 5.2.0

### 次版本变更

- f9d8b06: 切换为 Apache 2 许可证

## 5.1.1

### 补丁变更

- 更新依赖 [8bbff3a]
  - @arizeai/phoenix-otel@0.2.1

## 5.1.0

### 次版本变更

- de6f111: 重构为在整个客户端中使用 phoenix-otel

### 补丁变更

- 更新依赖 [de6f111]
  - @arizeai/phoenix-otel@0.2.0

## 5.0.0

### 主版本变更

- 950fda5: feat: 添加数据集划分支持

  本次发布引入数据集划分支持，可对数据集示例分段并查询指定部分。`DatasetSelector` 接口增强为支持按划分过滤，实现更精细的数据集管理和实验。

  ## 新功能

  - **数据集划分支持**：通过增强的 `DatasetSelector` 接口按划分查询示例
  - **基于划分的实验**：在指定数据集划分上运行实验，进行定向评估
  - **增强的数据集类型**：更新类型定义，支持基于划分的数据集操作

  ## 破坏性变更

  - **`runExperiment` API 变更**：
    - 已从 `runExperiment` 移除 `datasetVersionId` 参数
    - 版本选择现在通过 `DatasetSelector` 接口处理
    - 请改为在 `DatasetSelector` 参数中传入 `versionId` 和 `splits` 属性

  ## 迁移指南

  **修改前：**

  ```typescript
  runExperiment({
    dataset: { datasetId: "my-dataset" },
    datasetVersionId: "version-123",
    // ... other params
  });
  ```

  **修改后：**

  ```typescript
  runExperiment({
    dataset: {
      datasetId: "my-dataset",
      versionId: "version-123",
      splits: ["train", "test"],
    },
    // ... other params
  });
  ```

## 4.2.0

### 次版本变更

- 85430fa: feat: 为 runExperiment 添加可配置 DiagLogLevel
- c7cc7d9: feat: 为 phoenix-client 添加 createOrGetDataset 辅助函数

  同时清理构建产物及示例脚本间的类型检查。

## 4.1.0

### 次版本变更

- 2981780: 添加会话标注函数

## 4.0.3

### 补丁变更

- e3a8ce2: 将追踪提供程序传递到实验，避免重复配置
- c85780b: 为评估和实验添加泛型支持

## 4.0.2

### 补丁变更

- 1b71c66: 确保重复次数大于 0

## 4.0.1

### 补丁变更

- e72a9ad: 不吞掉错误，允许不完整数据集（如仅包含输入）

## 4.0.0

### 主版本变更

- 7732f99: 针对 AI SDK 用户的破坏性变更：支持 AI SDK 5 的消息转换

## 3.2.0

### 次版本变更

- 4f43901: 添加文档标注记录支持

## 3.1.0

### 次版本变更

- ee0c829: 默认切换到批处理 Span 处理器，并使其可配置

## 3.0.0

### 主版本变更

- 3e80a50: 添加删除 Span 方法

### 次版本变更

- 8711bde: 将 openai 主版本更新到 ^5

## 2.4.0

### 次版本变更

- fe55fc5: 通过 versionId 获取数据集

## 2.3.5

### 补丁变更

- 83748e6: 在各包中添加类型导出及更完善的文档

## 2.3.4

### 补丁变更

- 20db91d: 为评估添加追踪及追踪控制

## 2.3.3

### 补丁变更

- 2609fcd: 将 JS 目标提升为 es2017，以使用原生 async

## 2.3.2

### 补丁变更

- 6ef8e47: 修复按名称拉取数据集

## 2.3.1

### 补丁变更

- b3e30db: 简化实验客户端 API 中任务输出的类型

## 2.3.0

### 次版本变更

- 3c97cc7: 添加按名称获取数据集的能力

## 2.2.0

### 次版本变更

- 1906611: 添加 getSpan 方法

### 补丁变更

- 4c52db4: 添加 ollama 提供商

## 2.1.1

### 补丁变更

- 5dd53be: 将 xai 作为提供商添加到 Playground

## 2.1.0

### 次版本变更

- b162720: 添加 deepseek 支持

## 2.0.1

### 补丁变更

- da7800a: feat(phoenix-client): 调用 runExperiment 时记录实验/数据集链接

## 2.0.0

### 主版本变更

- 118e881: feat: 支持创建数据集及重新运行实验

## 1.3.0

### 次版本变更

- 536258e: feat(phoenix-client): 将实验追踪导出到 Phoenix

## 1.2.0

### 次版本变更

- f7fae3b: feat(phoenix-client): 将实验结果记录到 Phoenix 服务器
- 9273417: feat: 将实验运行加入队列
- 4dd23c8: 支持在 Span 上记录标注

## 1.1.0

### 次版本变更

- fff5511: feat: 更新 OpenAPI 模式，增加新端点

## 1.0.2

### 补丁变更

- c99ee6f: 更新类型定义，包含 openai 的 max_completion_tokens 参数

## 1.0.1

### 补丁变更

- 2ffeb64: fix: 移除对 `ai` 包的运行时依赖

## 1.0.0

### 主版本变更

- 3f9e392: feat: 添加 Phoenix 提示词支持

  Phoenix 现在可以管理提示词，`@arizeai/phoenix-client` 包已更新以支持此功能。

  在首次发布中，支持以下内容：

  - 完整类型化的提示词 REST 端点
  - 拉取提示词
  - 将提示词转换为以下 LLM SDK 的调用参数：
    - OpenAI
    - Anthropic
    - Vercel AI SDK
      - 可将任意 Vercel AI SDK 提供商与提示词配合使用

### 补丁变更

- 95bfc7c: 添加通过 TypeScript 客户端 SDK 推送提示词的能力

## 0.0.1

### 补丁变更

- 76a9cdf: phoenix-client 预发布版本
