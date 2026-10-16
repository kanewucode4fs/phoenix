<a id="tau-bench--langgraph"></a>

# tau-bench 与 LangGraph 示例

这是使用 LangGraph 构建的客服 Agent，通过 OpenInference 埋点，运行 tau-bench 零售领域任务。它是 [OpenAI Agents SDK 实现](../tau_bench_openai_agents/README.md)的 LangGraph 对应版本，使用相同工具、数据库和模拟用户，仅框架不同。比较两者追踪可以了解框架选择如何影响可获取的轨迹信息。

<a id="what-this-does"></a>

## 功能说明

运行与 OpenAI Agents SDK 版本相同的零售客服 Agent，执行相同 tau-bench 任务。Agent 使用 16 个工具验证用户身份、查询订单并执行取消、退货、换货和修改等变更，全部追踪至 Phoenix。

<a id="architecture"></a>

## 架构

```
模拟用户（不追踪）          Agent 框架（追踪）
+---------------------+    消息   +------------------------------+
| LLMUserSimulationEnv | -------> | LangGraph StateGraph         |
| (litellm/gpt-4o)    | <------- |   "agent" 节点 (ChatOpenAI)  |
+---------------------+  响应     |   "tools" 节点 (ToolNode)    |
                                  |   条件路由        |
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

Agent 是一个包含两个节点的 `StateGraph(MessagesState)`：

- **"agent"** — 使用完整消息历史和已绑定工具调用 `ChatOpenAI`
- **"tools"** — 通过 `ToolNode` 执行工具调用

条件路由在 agent → tools 之间循环，直到 LLM 生成不含工具调用的响应，随后路由至 END。

每个外层轮次（用户消息 → Agent 响应，内部可能包含多个工具调用循环）生成一棵 span 树：

```
conversation.turn （手动）              ← 包围完整轮次
  LangGraph （自动）                      ← 图执行
    ChatOpenAI （自动，LLM）              ← 包含消息历史的 LLM 调用
    <tool_name> （自动，TOOL）            ← 工具执行（若有）
    ChatOpenAI （自动，LLM）              ← 后续 LLM 调用
```

<a id="key-differences-from-the-openai-agents-sdk-version"></a>

### 与 OpenAI Agents SDK 版本的主要区别

- **Span 嵌套**：LangGraph 生成更扁平的 span 树，LLM 和 TOOL span 是图 span 下的同级节点，不嵌套在 Agent 工作流 span 下。
- **消息累积**：LangGraph 的 `MessagesState` 持续传递完整对话历史，因此后续 LLM span 包含此前的所有消息。token 用量随对话长度增长。
- **轮次边界**：两种实现都使用手动 `conversation.turn` span 对每个轮次分组，但内部结构不同。

<a id="usage"></a>

## 使用方法

在 `examples/agents/` 目录中执行：

```bash
# 运行选定的全部 10 个任务
python -m tau_bench_langgraph

# 运行指定任务
python -m tau_bench_langgraph --tasks dev:0 dev:12

# 不使用 Phoenix
python -m tau_bench_langgraph --no-phoenix
```

<a id="file-structure"></a>

## 文件结构

| 文件 | 用途 |
|------|---------|
| `agent.py` | LangGraph `StateGraph` 定义和多轮对话循环 |
| `tools.py` | 16 个以 LangChain `@tool` 函数实现的零售工具，封装 tau-bench `Tool.invoke()` |
| `db.py` | 内存数据库加载器；为每个任务深拷贝 tau-bench JSON 数据 |
| `user_sim.py` | 模拟用户封装，与 OpenAI Agents SDK 版本相同 |
| `phoenix_setup.py` | OpenInference `LangChainInstrumentor` 和 Phoenix OTLP 设置 |
| `tasks.py` / `tasks_scaled.py` | 从 tau-bench dev/train 划分选择任务 |
| `run.py` | CLI 入口 |
