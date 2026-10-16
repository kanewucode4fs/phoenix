<a id="quick-setup-guide"></a>

# 快速配置指南

按照以下步骤运行 LangChain TypeScript 旅行规划 Agent。

<a id="1-navigate-to-the-directory"></a>

## 1. 进入目录

```bash
cd js/examples/apps/langchain-quickstart
```

<a id="2-install-dependencies"></a>

## 2. 安装依赖

```bash
npm install
```

这会安装以下依赖（以及其他依赖）：

- `langchain` – LangChain 与 Agent
- `@langchain/core` – 回调与工具
- `zod` – 工具模式验证
- `@arizeai/phoenix-otel` – Phoenix 追踪
- `@arizeai/openinference-instrumentation-langchain` – LangChain 插桩
- `@arizeai/phoenix-client`, `@arizeai/phoenix-evals` – 获取 Span 及运行评估
- `@ai-sdk/openai` – 兼容 OpenAI 的模型（用于 Agent 和评估）
- `dotenv` – 加载 `.env`
- `tsx` – TypeScript 执行（开发）

<a id="3-set-environment-variables"></a>

## 3. 设置环境变量

根据 `.env.example` 创建 `.env`，至少设置：

```bash
# Required for the agent
OPENAI_API_KEY=your-key-here
TAVILY_API_KEY=your-tavily-key-here

# Optional: Phoenix (defaults). Traces are exported to PHOENIX_COLLECTOR_ENDPOINT;
# the eval scripts call the Phoenix API on PHOENIX_ENDPOINT.
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_PROJECT_NAME=langchain-travel-agent
```

运行 `npm run custom_evals` 还需要：

```bash
FIREWORKS_API_KEY=your-fireworks-key-here
```

<a id="4-start-phoenix-if-running-locally"></a>

## 4. 启动 Phoenix（若在本地运行）

在另一个终端中：

```bash
pip install arize-phoenix
phoenix serve
```

Phoenix 将在 `http://localhost:6006` 提供服务。

<a id="5-run-the-application"></a>

## 5. 运行应用

```bash
npm start
```

你应该看到：

- 三次旅行规划查询（爱尔兰、日本、葡萄牙），包含目的地、时长和兴趣
- Agent 使用三个工具（essential_info、budget_basics、local_flavor）生成的响应
- Phoenix `http://localhost:6006` 中的追踪

<a id="6-optional-run-evaluations"></a>

## 6. （可选）运行评估

Agent 运行并发送追踪后：

```bash
# Pre-built correctness eval (OpenAI)
npm run pre_built_evals

# Custom correctness eval (travel rubric, Fireworks)
npm run custom_evals
```

<a id="file-structure"></a>

## 文件结构

```
langchain-quickstart/
├── src/
│   ├── index.ts              # Phoenix register + LangChain travel agent
│   ├── tools.ts              # essential_info, budget_basics, local_flavor (Tavily)
│   ├── pre_built_evals.ts    # Pre-built correctness eval → Phoenix annotations
│   ├── custom_evals.ts       # Custom correctness eval (travel rubric, Fireworks)
│   └── instrumentation.ts   # Optional standalone Phoenix setup (not used by index.ts)
├── package.json              # Scripts: start, pre_built_evals, custom_evals
├── .env.example              # OPENAI, TAVILY, PHOENIX, FIREWORKS
├── README.md                  # Full documentation
└── SETUP.md                  # This file
```

**Note:** `index.ts` sets up Phoenix and LangChain 插桩 at the top of the file (it does not import `instrumentation.ts`).

<a id="what-the-code-does"></a>

## 代码的作用

1. **index.ts** – 注册 Phoenix，为 LangChain 插桩，并运行旅行规划 Agent；每次请求必须调用三个工具，按 Essentials（基本信息）、Budget（预算）、Local flavor（当地特色）回复。
2. **tools.ts** – 定义三个由 Tavily 支持的工具：**essential_info**（天气、最佳时间、景点、礼仪）、**budget_basics**（按目的地和时长分解费用）、**local_flavor**（按目的地和兴趣推荐体验）。
3. **pre_built_evals.ts** – 从 Phoenix 加载 LangGraph Span，运行内置正确性评估器，并向 Phoenix 记录标注。
4. **custom_evals.ts** – 加载相同 Span，使用 Fireworks 模型运行旅行 Agent 的自定义正确性模板，并以 `custom_correctness` 记录标注。

<a id="next-steps"></a>

## 后续步骤

- 在 `src/index.ts` 中修改目的地/时长/兴趣
- 在 `src/tools.ts` 中新增或修改工具
- 调整 `src/index.ts` 中的系统提示词
- 微调 `src/custom_evals.ts` 中的自定义评估模板
- 更多示例见 [LangChain JS 文档](https://js.langchain.com/)
