# @arizeai/phoenix-evals

## 2.6.0

### 次版本变更

- b7b7dfb: 分类评估器现在支持 TypeSafe 的 Jev 等 AI SDK 评估模型。传入评估模型作为 `model` 时，分类将通过 `experimental_evaluate` 作为单选题处理，不再使用 `generateObject`。结果包含 `label` 和 `score`，但没有 `explanation`，因为评估模型不生成文本。

## 2.5.0

### 次版本变更

- 63805d0: 添加 `createCompletenessEvaluator`，判断对话中每个有效用户请求是否确实完成。

### 补丁变更

- d67ea3f: 弃用 `createDocumentRelevanceEvaluator`，改用
  `createRetrievalRelevanceEvaluator`。将 `documentText` 重命名为 `context`，并将
  `unrelated` 标签改为 `irrelevant`。已弃用的工厂函数及类型将在
  下一个主版本中移除。

## 2.4.0

### 次版本变更

- 0e3b2c2: 添加内置个人身份信息检测评估器（`createPiiDetectionEvaluator`），筛查对话记录中的个人身份信息，涵盖系统指令、工具调用与结果，以及最终用户可能从未见过的检索内容。

## 2.3.0

### 次版本变更

- 7efa7b2: 添加内置检索相关性评估器（createRetrievalRelevanceEvaluator），检查某一步检索的外部信息是否与其所服务的请求相关。与文档相关性不同，它不依赖信息来源，而是整体评估检索信息，无论来自向量搜索、工具或 MCP 调用、网页搜索，还是嵌入在 LLM 轮次中的内容。

## 2.2.0

### 次版本变更

- 1aa1a84: 将 `createHallucinationEvaluator` 重新设计为基于对话依据的评估器。

  评估器输入改为 `input` 和 `output`，其中 `input` 是助手可用的对话，`output` 是被评判的响应。不再接受单独的 `context` 字段。

  标签从 `factual`/`hallucinated` 改为 `grounded`/`hallucinated`。分数按最小化优化，`hallucinated` 为 `1`，`grounded` 为 `0`。现有存储评估、仪表盘、阈值和标签过滤器可能需要迁移，不应与旧评估器结果直接比较。

## 2.1.0

### 次版本变更

- 899dece: 添加内置毒性评估器（createToxicityEvaluator），将文本分为有毒或无毒。

## 2.0.0

### 主版本变更

- 5a8f3f7: 将 `@arizeai/phoenix-evals` 升级到 AI SDK v7。评估器遥测使用 AI SDK v7 遥测 API，通过 `@ai-sdk/otel` 为每次调用提供 `OpenTelemetry` 集成，同时保留所有全局注册集成（日志、指标及到其他后端的追踪）；除非已有全局集成使用同一追踪器追踪，否则追加 Phoenix 追踪集成。评估器 Span 现在遵循 `@ai-sdk/otel` 生成的 OpenTelemetry `gen_ai.*` 约定，不再使用 AI SDK v6 的 `ai.*` Span 格式。`telemetry.tracer` 和 `telemetry.isEnabled` 选项继续按原样工作，提示词模板中的系统消息仍受支持。要求 Node.js >=22.12 及兼容 AI SDK v7 的模型提供商（如 `@ai-sdk/openai` v4）。

## 1.2.0

### 次版本变更

- f94067b: 添加 px setup 脚本，用于 Agent 接入引导

## 1.1.0

### 次版本变更

- 1f7d5f0: 为分类指标添加内置代码（非 LLM）评估器：`createPrecisionEvaluator`、`createRecallEvaluator`、`createF1Evaluator`、`createFBetaEvaluator`，以及组合辅助函数 `createPrecisionRecallFScoreEvaluators` 和底层 `computePrecisionRecallFScore` 函数。支持二分类（通过 `positiveLabel`）及多分类（`macro`/`micro`/`weighted` 平均），对应 Python 的 `PrecisionRecallFScore` 评估器。

## 1.0.3

### 补丁变更

- 5d14f23: 在 README 的社区章节添加 LinkedIn 链接。

## 1.0.2

### 补丁变更

- 1028be5: 将整理过的包文档和示例打包到 npm 包的 `docs/` 下。

## 1.0.1

### 补丁变更

- b4ded15: 使用最新功能更新各包 README
  - phoenix-client：添加会话章节，说明 `listSessions`、`getSession` 和 `addSessionAnnotation`
  - phoenix-evals：添加完整预置评估器表格（简洁性、正确性、文档相关性、拒绝回答、工具评估器），修复 `bindEvaluator` 导入路径
  - phoenix-mcp：扩展工具覆盖范围章节，提供完整准确的工具列表
  - phoenix-config：以完整文档替换单行占位说明（安装、环境变量、使用示例）
  - phoenix-cli：添加 `px annotation-config` 命令文档

## 1.0.0

### 主版本变更

- 03b10a8: feat: 将 zod 从 v3 升级到 v4

  破坏性变更：将 zod 从 v3 升级到 v4。这会改变使用
  `z.looseObject()`（此前为 `.passthrough()`）模式的 TypeScript 推断类型，现在其
  输出类型包含 `[x: string]: unknown`。使用这些类型的使用方可能需要
  更新代码。此外，`ZodError.errors` 已替换为
  `ZodError.issues`，`z.record()` 现在要求显式键模式，且
  `zod-to-json-schema` 已替换为原生 `z.toJSONSchema()`。

## 0.10.0

### 次版本变更

- b18325b: feat: 将 AI SDK 升级到 v6
- d43c4ee: feat: 添加简洁性评估器

## 0.9.0

### 次版本变更

- 0738cb9: 添加工具响应处理 LLM 评估器。
- d6d1953: 添加 createToolSelectionEvaluator，评估 LLM 工具选择决策。该评估器判断是否针对给定上下文选择正确工具，检查 LLM 是否为用户查询选择最佳可用工具。

## 0.8.0

### 次版本变更

- d1c89bf: 添加 createToolInvocationEvaluator，评估 LLM 工具调用

## 0.7.0

### 次版本变更

- da13ad5: 添加通用正确性评估器

## 0.6.5

### 补丁变更

- 4208604: 触发 changeset 发布

## 0.6.4

### 补丁变更

- c96475c: 触发 changeset 发布

## 0.6.3

### 补丁变更

- 857b617: 添加包链接

## 0.6.2

### 补丁变更

- 0589fc3: 创建评估器辅助工具

## 0.6.1

### 补丁变更

- 5cacc22: 创建评估器辅助函数

## 0.6.0

### 次版本变更

- 84877d6: 为评估器添加数据映射辅助函数

## 0.5.1

### 补丁变更

- 9408838: 添加消息模板支持

## 0.5.0

### 次版本变更

- aa5dc26: 将模板中的嵌套值序列化为 JSON

## 0.4.0

### 次版本变更

- 885be2a: 使 phoenix-client 能直接接收 Phoenix 评估器

## 0.3.1

### 补丁变更

- a756a95: 通过禁用 HTML 转义修复 Mustache.render

## 0.3.0

### 次版本变更

- f66c5b6: refactor: 将评估器的 source 改为 kind

## 0.2.2

### 补丁变更

- c7cc7d9: feat: 为 phoenix-client 添加 createOrGetDataset 辅助函数

  同时清理构建产物及示例脚本间的类型检查。

## 0.2.1

### 补丁变更

- c85780b: 为评估和实验添加泛型支持

## 0.2.0

### 次版本变更

- f92dab7: 添加名称、优化方向等

## 0.1.0

### 次版本变更

- f11969d: 记录来源和优化方向

## 0.0.8

### 补丁变更

- 7b204a5: 将 AI SDK 升级到 5

## 0.0.7

### 补丁变更

- 83748e6: 在各包中添加类型导出及更完善的文档

## 0.0.6

### 补丁变更

- a57ec81: 添加遥测控制

## 0.0.5

### 补丁变更

- 20db91d: 为评估添加追踪及追踪控制

## 0.0.4

### 补丁变更

- 2609fcd: 将 JS 目标提升为 es2017，以使用原生 async

## 0.0.3

### 补丁变更

- a6a4ca8: 在 README 添加文档

## 0.0.2

### 补丁变更

- b3e30db: 评估库 Alpha 版本
