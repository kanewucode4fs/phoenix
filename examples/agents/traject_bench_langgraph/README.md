<a id="traject-bench--langgraph"></a>

# TRAJECT-Bench 与 LangGraph 示例

这是使用 LangGraph 构建的单轮工具调用 Agent，通过 OpenInference 埋点，运行 [TRAJECT-Bench](https://huggingface.co/datasets/Jnnamchi/traject-bench) 任务。它与 tau-bench 示例在各方面均不同：单轮而非多轮、模拟工具而非真实数据库变更、并行和顺序工具模式而非对话模式。

<a id="what-this-does"></a>

## 功能说明

运行 Agent 执行 TRAJECT-Bench 任务，测试工具选择、参数准确性和执行顺序。任务覆盖电商、旅行、金融等多个领域，分为两类：

- **并行**：多个独立工具调用，可按任意顺序执行
- **顺序**：工具调用具有依赖关系，前一个调用的输出作为下一个调用的输入

工具根据数据集定义为每个任务动态创建，调用时返回预先记录的输出，从而将 Agent 的工具调用行为与外部 API 的不确定性隔离。

<a id="architecture"></a>

## 架构

```
                                  Agent 框架（追踪）
                                  +------------------------------+
  任务查询（单轮） -----> | LangGraph StateGraph         |
                                  |   "agent" 节点 (ChatOpenAI)  |
                                  |   "tools" 节点 (ToolNode)    |
                                  |   parallel_tool_calls=True/  |
                                  |     False，依据任务类型      |
                                  |   | LLM span                |
                                  |   | TOOL span               |
                                  +------------------------------+
                                           | OTel/OTLP
                                           v
                                  +------------------+
                                  | Phoenix（本地）  |
                                  | localhost:6006   |
                                  +------------------+
```

与 tau-bench 不同，由于各任务工具不同，**每个任务都会创建全新的图**。图使用系统提示词（任务描述和可用工具名称）及任务查询调用一次。Agent 在内部循环（agent → tools → agent），直到生成最终回答。

典型任务的 span 树：

```
LangGraph （自动）                        ← 图执行
  ChatOpenAI （自动，LLM）               ← 包含系统和用户消息的初始 LLM 调用
  <tool_1> （自动，TOOL）                ← 第一次工具调用
  <tool_2> （自动，TOOL）                ← 第二次工具调用（并行任务）
  ChatOpenAI （自动，LLM）               ← 携带工具结果的后续调用 → 最终回答
```

<a id="key-differences-from-the-tau-bench-examples"></a>

### 与 tau-bench 示例的主要区别

- **没有对话循环** — 输入单个查询，调用工具，输出最终回答。
- **动态工具** — 为每个任务根据数据集定义创建模拟函数，不使用静态工具代码。
- **并行工具调用** — 并行任务启用 `parallel_tool_calls=True`，因此 LLM 可以在一次响应中请求多个工具，在追踪中表现为同级 TOOL span。
- **没有模拟用户** — 不涉及外部用户交互。

<a id="usage"></a>

## 使用方法

在 `examples/agents/` 目录中执行：

```bash
# 运行选定的全部 9 个任务
python -m traject_bench_langgraph

# 运行指定任务
python -m traject_bench_langgraph --tasks parallel_simple:0 sequential:1

# 不使用 Phoenix
python -m traject_bench_langgraph --no-phoenix
```

> **说明**：首次运行会从 HuggingFace 下载 TRAJECT-Bench 数据集（下载量较小）。后续运行使用缓存版本。

<a id="file-structure"></a>

## 文件结构

| 文件 | 用途 |
|------|---------|
| `agent.py` | 为每个任务创建 LangGraph `StateGraph` 并执行单轮任务 |
| `tools.py` | 动态模拟工具工厂，根据数据集定义创建 LangChain `@tool` 函数 |
| `phoenix_setup.py` | OpenInference `LangChainInstrumentor` 和 Phoenix OTLP 设置 |
| `tasks.py` / `tasks_scaled.py` | 从 HuggingFace 数据集加载任务，处理字段名称不一致 |
| `run.py` | CLI 入口 |

<a id="how-mock-tools-work"></a>

## 模拟工具工作原理

每个 TRAJECT-Bench 任务以 JSON 定义其工具，包含名称、描述、参数和预期输出。`tools.py` 为每个工具动态创建 LangChain `@tool` 函数：

1. 清理工具名称（例如 `"Wayfair: reviews/list"` → `"wayfair_reviews_list"`）
2. 函数接收 `parameters` 字典，并返回预先记录的 `executed_output`
3. 文档字符串包含工具描述和参数规范

这意味着工具始终返回“正确”输出，评估重点是 Agent 是否以正确顺序、正确参数调用正确工具，而非处理真实 API 响应。
