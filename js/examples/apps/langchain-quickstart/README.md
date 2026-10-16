<a id="langchain-typescript-quickstart"></a>

# LangChain TypeScript 快速开始

集成 Phoenix 追踪及可选评估的 LangChain TypeScript 旅行规划 Agent。

<a id="prerequisites"></a>

## 前置条件

- 已安装 **Node.js 18+**
- **Phoenix** 在本地运行 (`pip install arize-phoenix && phoenix serve`) 或可访问 Phoenix Cloud
- **OpenAI API 密钥**（`OPENAI_API_KEY`），用于 Agent LLM
- **Tavily API 密钥**（`TAVILY_API_KEY`），用于工具搜索（essential_info、budget_basics、local_flavor）

<a id="setup"></a>

## 配置

1. **安装依赖：**

```bash
cd js/examples/apps/langchain-quickstart
npm install
```

2. **设置环境变量：**

将 `.env.example` 复制为 `.env` 并填写：

```bash
# Required for the agent
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key

# Optional: Phoenix (defaults shown). Traces are exported to
# PHOENIX_COLLECTOR_ENDPOINT; the eval scripts call the Phoenix API on PHOENIX_ENDPOINT.
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_PROJECT_NAME=langchain-travel-agent

# Optional: for custom_evals (uses Fireworks model)
FIREWORKS_API_KEY=your-fireworks-api-key
```

3. **启动 Phoenix**（若在本地运行）：

```bash
pip install arize-phoenix
phoenix serve
```

<a id="running-the-application"></a>

## 运行应用

```bash
npm start
```

这会：

- 创建带有三个工具的 LangChain Agent：**essential_info**、**budget_basics**、**local_flavor**
- 运行三次旅行规划查询（爱尔兰、日本、葡萄牙），包含目的地、时长和兴趣
- 将所有追踪发送到 Phoenix 以进行可视化

Agent 接到的指令是每次请求都调用全部三个工具，并按以下结构回复：(a) Essentials（基本信息），(b) Budget（预算），(c) Local flavor（当地特色）。

<a id="evaluations"></a>

## 评估

运行 Agent 并向 Phoenix 发送追踪后，可对这些追踪运行评估。

**预置正确性评估器**（默认使用 OpenAI）：

```bash
npm run pre_built_evals
```

- 从 Phoenix 获取 LangGraph（Agent）Span，运行内置正确性评估器，并将标注写回 Phoenix。
- 为默认评估器模型设置 `OPENAI_API_KEY`。可选：取消 `src/pre_built_evals.ts` 中相应代码块的注释并配置，以使用自定义 LLM（如 Fireworks）。

**自定义正确性评估器**（旅行 Agent 评判标准，使用 Fireworks）：

```bash
npm run custom_evals
```

- 使用带旅行计划正确性模板的自定义分类评估器。
- 需要 `PHOENIX_ENDPOINT` 和 `FIREWORKS_API_KEY`。
- 评估相同的 LangGraph Span，并以 `custom_correctness` 记录标注。

<a id="what-to-look-for-in-phoenix"></a>

## 在 Phoenix 中查看什么

运行应用后，在 `http://localhost:6006` 打开 Phoenix。

<a id="traces"></a>

### 追踪

每次 Agent 调用都会创建一条追踪，展示：

- 包含输入消息和最终输出的 **LangGraph**（Agent）Span
- 工具调用：**essential_info**、**budget_basics**、**local_flavor**（由 Tavily 支持）
- Token 用量、延迟、提示词及响应

运行评估后，可在 LangGraph Span 上看到 Span 标注（如 correctness / custom_correctness）。

<a id="project-structure"></a>

### 项目结构

```
langchain-quickstart/
├── package.json              # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── .env.example              # Example environment variables
├── src/
│   ├── index.ts              # Main app: Phoenix register + LangChain agent
│   ├── tools.ts              # Travel tools (essential_info, budget_basics, local_flavor)
│   ├── pre_built_evals.ts    # Pre-built correctness eval → Phoenix annotations
│   ├── custom_evals.ts       # Custom correctness eval (travel rubric, Fireworks)
│   └── instrumentation.ts   # Standalone Phoenix setup (optional; index.ts inlines its own)
├── README.md
└── SETUP.md
```

**关键文件：**

- `src/index.ts` – 注册 Phoenix（`@arizeai/phoenix-otel`），为 LangChain 插桩，并使用 `travelTools` 运行旅行 Agent。
- `src/tools.ts` – 定义三个由 Tavily 支持的工具及其模式（目的地、时长、兴趣）。
- `src/pre_built_evals.ts` – 获取 Agent Span，运行 Phoenix 正确性评估器并记录标注。
- `src/custom_evals.ts` – 获取相同 Span，使用自定义正确性模板和 Fireworks LLM，并记录标注。

**主要依赖：** `langchain`, `@langchain/core`, `@arizeai/phoenix-otel`, `@arizeai/openinference-instrumentation-langchain`, `@arizeai/phoenix-client`, `@arizeai/phoenix-evals`, `@ai-sdk/openai`, `dotenv`, `zod`.

<a id="troubleshooting"></a>

## 故障排查

**错误：未设置 OPENAI_API_KEY 或 TAVILY_API_KEY**

- 确保两者均已设置（例如在 `.env` 中，或通过 `export OPENAI_API_KEY=...` 和 `export TAVILY_API_KEY=...`）。

**Phoenix 中未出现追踪**

- 确保 Phoenix 正在运行：`phoenix serve`
- 检查 Phoenix 端点是否可访问（默认：http://localhost:6006 ）
- 确认 `PHOENIX_PROJECT_NAME` 与 UI 中打开的项目一致（默认：`langchain-travel-agent`）

**TypeScript / 模块错误**

- 运行 `npm install` 并使用 Node.js 18+
- 确认 `"type": "module"` 及导入路径与你的配置匹配

**"Failed to log annotations to Phoenix: ... 404 Not Found"** （运行 `npm run pre_built_evals` 或 `npm run custom_evals` 时）

- Phoenix 服务器可能未提供 Span 标注 API。请升级并重启：
  ```bash
  pip install -U arize-phoenix
  phoenix serve
  ```
- 或在 Phoenix 仓库根目录运行：`uv run phoenix serve`
- 评估仍会运行并打印结果；在服务器升级前，仅向 Phoenix 发送标注会失败。

**custom_evals：设置 PHOENIX_ENDPOINT**

- 在 `.env` 中设置它（如 `PHOENIX_ENDPOINT=http://localhost:6006`），并确保为 Fireworks 评估器模型设置 `FIREWORKS_API_KEY`。
