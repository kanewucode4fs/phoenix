<a id="mastra--phoenix-typescript-quickstart"></a>

# Mastra + Phoenix TypeScript 快速开始

本快速开始结合 [Mastra](https://mastra.ai)（多 Agent 框架）和 [Phoenix](https://docs.arize.com/phoenix/)，对金融分析 Agent 系统进行追踪、评估和实验。

<a id="whats-in-this-quickstart"></a>

## 本快速开始的内容

- **Agent**：金融编排器（协调研究和报告）、金融研究员（搜索和总结）、金融撰稿人（根据研究生成报告）。
- **工具**：`financialSearchTool`（金融数据查询）、`financialAnalysisTool`（运行研究员 → 撰稿人流水线）。
- **追踪**：Mastra 可观测性通过 Arize 导出器向 Phoenix 导出追踪。
- **评估**：针对编排器输出的 Span 级完整性评估（位于 `evals/evals.ts`）。
- **实验**：在 Phoenix 数据集上运行编排器，并使用完整性分类器评估。

<a id="prerequisites"></a>

## 前置条件

- **Node.js** >= 22.13.0
- **pnpm** （或 npm）
- 用于追踪和实验的 **Phoenix** 服务器（本地或托管）
- 供 Agent 和评估使用的 **OpenAI API 密钥**

<a id="setup"></a>

## 配置

1. **安装依赖**

   ```bash
   pnpm install
   ```

2. **环境变量**

   在项目根目录创建 `.env`，内容包括：
   - `OPENAI_API_KEY` – 供 Mastra Agent 和 phoenix-evals 使用
   - `PHOENIX_COLLECTOR_ENDPOINT` – 发送追踪的确切 URL（如 `http://localhost:6006/v1/traces`）
   - `PHOENIX_ENDPOINT` – API 客户端使用的 Phoenix 服务器基础 URL（如 `http://localhost:6006`）
   - `PHOENIX_API_KEY` – （可选）Phoenix 实例要求时设置
   - `PHOENIX_PROJECT_NAME` – （可选）追踪项目名称；默认 `mastra-tracing-quickstart`

   评估和实验脚本通过服务器基础 URL `PHOENIX_ENDPOINT` 调用 Phoenix API。`PHOENIX_COLLECTOR_ENDPOINT` 是发送追踪的确切 URL；Mastra 的 `ArizeExporter` 按原样向其发送 POST，因此该 URL 包含 OTLP `/v1/traces` 路径，并由 `src/mastra/index.ts` 直接传递。

<a id="scripts"></a>

## 脚本

| 脚本             | 说明                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm dev`         | 启动 Mastra 开发服务器（Agent + 工具）。默认 API：`http://localhost:4111`。                                                                   |
| `pnpm build`       | 构建 Mastra 应用。                                                                                                                             |
| `pnpm start`       | 运行构建后的 Mastra 服务器。                                                                                                                      |
| `pnpm add_traces`  | 用示例问题调用编排器，并向 Phoenix 发送追踪。**要求 Mastra 服务器正在运行**（例如在另一终端运行 `pnpm dev`）。 |
| `pnpm evals`       | 从 Phoenix 获取编排器 Span，运行完整性评估，并将标注写回 Phoenix。                                                |
| `pnpm experiments` | 运行 Phoenix 实验：加载数据集，为每个示例运行编排器任务，并使用完整性评估器评估。                      |

<a id="typical-workflow"></a>

## 典型流程

1. **启动 Phoenix**（本地部署时）。
2. **启动 Mastra**: `pnpm dev`.
3. **生成追踪**：在另一终端运行 `pnpm add_traces`（或用自己的输入调用 Mastra API）。
4. **运行评估**：用 `pnpm evals` 为编排器 Span 评分，并在 Phoenix 中添加完整性标注。
5. **运行实验**：确保已有数据集（如 `"ts quickstart fails"`），其中示例的 `input` 是消息数组；然后运行 `pnpm experiments`。

<a id="project-structure"></a>

## 项目结构

```
src/mastra/
├── index.ts              # Mastra instance + Phoenix observability (Arize exporter)
├── agents/
│   ├── financial-orchestrator-agent.ts
│   ├── financial-researcher-agent.ts
│   └── financial-writer-agent.ts
├── tools/
│   ├── financial-search-tool.ts
│   └── financial-analysis-tool.ts
├── evals/
│   ├── add_traces.ts     # Sample questions → orchestrator → traces to Phoenix
│   └── evals.ts          # Completeness eval on spans, log annotations to Phoenix
└── experiments/
    └── experiment.ts     # runExperiment with dataset, task, completeness evaluator
```

<a id="dataset-for-experiments"></a>

## 实验数据集

实验脚本要求 Phoenix 数据集（如名称为 `"ts quickstart fails"`）中示例的 `input` 字段为以下形式之一：

- 消息数组：`[{ "role": "user", "content": "Research AAPL, MSFT with focus on valuation" }]`，或
- 包含 `input` 键的对象，该键存放上述数组。

任务将此输入传给金融编排器 Agent，并使用返回的报告进行完整性评估。
