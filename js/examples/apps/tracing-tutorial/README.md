<a id="phoenix-tracing-tutorial-typescript"></a>

# Phoenix 追踪教程（TypeScript）

构建客服 Agent，使用 Phoenix 追踪每次 LLM 调用、工具执行及 RAG 检索。通过标注和 LLM 裁判评估响应质量，将多轮对话作为会话跟踪。

本教程与 Phoenix 追踪教程文档配套：

- [第 1 章：第一批追踪](https://docs.arize.com/phoenix/tracing/tutorial/your-first-traces)
- [第 2 章：标注与评估](https://docs.arize.com/phoenix/tracing/tutorial/annotations-and-evaluation)
- [第 3 章：会话](https://docs.arize.com/phoenix/tracing/tutorial/sessions)

<a id="prerequisites"></a>

## 前置条件

- 已安装 **Node.js 18+**
- **Phoenix** 在本地运行 (`uvx arize-phoenix serve`，或 `pip install arize-phoenix && phoenix serve`)
- **OpenAI API 密钥**

<a id="setup"></a>

## 配置

1. **安装依赖：**

```bash
pnpm install
```

2. **设置环境变量：**

```bash
# OpenAI API key (required)
export OPENAI_API_KEY=your-openai-api-key

# Optional: Custom Phoenix endpoint (defaults to http://localhost:6006)
export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

3. **启动 Phoenix**（若在本地运行）：

```bash
pip install arize-phoenix
phoenix serve
```

<a id="chapter-1-your-first-traces"></a>

## 第 1 章：第一批追踪

```bash
pnpm start
```

这会运行完整的客服 Agent，展示：

- **查询分类**：LLM 判断是订单状态问题还是常见问题
- **工具调用**：针对订单状态，调用 `lookupOrderStatus` 工具并总结结果
- **RAG 流水线**：针对常见问题，嵌入查询、搜索知识库并生成答案
- **交互反馈**：完成所有响应后，提示你逐一评价（y/n/s）

<a id="chapter-2-annotations-and-evaluation"></a>

## 第 2 章：标注与评估

运行 Agent 后评估响应：

```bash
pnpm evaluate
```

这会运行 LLM 裁判评估，执行：

- 从 Phoenix 获取近期 Span
- 对工具调用运行 **tool_result**（成功/错误）检查
- 对 RAG 查询运行 **retrieval_relevance**（LLM 裁判）评估
- 将评估结果作为标注写回 Phoenix
- 打印通过/失败率摘要

<a id="chapter-3-sessions"></a>

## 第 3 章：会话

运行多轮对话演示：

```bash
pnpm sessions
```

这会运行三种对话场景：

- **订单咨询**：客户询问订单后继续追问
- **常见问题对话**：同一会话中包含多个常见问题
- **混合对话**：在订单和常见问题之间切换

每段对话都有唯一会话 ID，可在 Phoenix 的**会话**选项卡查看。

然后评估会话：

```bash
pnpm evaluate:sessions
```

这会运行会话级评估：

- **对话连贯性**：Agent 是否保持上下文？
- **解决状态**：客户问题是否得到解决？

<a id="what-to-look-for-in-phoenix"></a>

## 在 Phoenix 中查看什么

运行脚本后，在 `http://localhost:6006` 打开 Phoenix。

<a id="traces-chapter-1"></a>

### 追踪（第 1 章）

每条 `support-agent` 追踪都展示完整请求流程：

**订单状态查询：**

```
support-agent (AGENT)
├── ai.generateText (classification → "order_status")
├── ai.generateText (with tool call)
│   └── tool: lookupOrderStatus
└── ai.generateText (summarizes tool result)
```

**常见问题查询：**

```
support-agent (AGENT)
├── ai.generateText (classification → "faq")
├── ai.embed (query embedding)
└── ai.generateText (RAG generation)
```

<a id="annotations-chapter-2"></a>

### 标注（第 2 章）

查看每条追踪的**标注**选项卡，了解：

- **user_feedback** - 用户交互式点赞/点踩反馈
- **tool_result** - 基于代码：success/error
- **retrieval_relevance** - LLM 评估：relevant/irrelevant

按标注值过滤追踪，发现失败模式。

<a id="sessions-chapter-3"></a>

### 会话（第 3 章）

点击 Phoenix 的**会话**选项卡，查看：

- **对话线程**：按会话 ID 分组的所有轮次
- **聊天视图**：点击会话查看完整往返对话
- **会话标注**：最后一轮上的连贯性和解决状态标注

按 `conversation_coherence` 或 `resolution_status` 过滤会话，找到存在问题的对话。

<a id="project-structure"></a>

## 项目结构

```
ts-tutorial/
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── instrumentation.ts    # Phoenix/OpenTelemetry setup
├── support-agent.ts      # Chapter 1 & 3: Support agent with sessions support
├── evaluate-traces.ts    # Chapter 2 & 3: LLM-as-Judge evaluation (spans + sessions)
└── README.md             # This file
```
