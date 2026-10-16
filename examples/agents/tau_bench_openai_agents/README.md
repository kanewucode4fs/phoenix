<a id="tau-bench--openai-agents-sdk"></a>

# tau-bench 与 OpenAI Agents SDK 示例

这是使用 OpenAI Agents SDK 构建的客服 Agent，通过 OpenInference 埋点，运行 tau-bench 零售领域任务。它属于轨迹评估研究的一部分，用于考察 Agent 框架自然处理工具调用对话时，OTel 追踪能够捕获哪些信息。

<a id="what-this-does"></a>

## 功能说明

运行零售客服 Agent，执行选定的 10 个 tau-bench 任务。Agent 会：

- 验证用户身份（通过邮箱，或姓名加邮政编码）
- 查询订单、商品和用户资料
- 取消、修改、退货和换货
- 遵循详细的零售策略（wiki.md）

所有 Agent 活动（LLM 调用、工具执行）均由 OpenInference 自动追踪，并导出至 Phoenix。

<a id="architecture"></a>

## 架构

```
模拟用户（不追踪）          Agent 框架（追踪）
+---------------------+    消息   +------------------------------+
| LLMUserSimulationEnv | -------> | OpenAI Agents SDK            |
| (litellm/gpt-4o)    | <------- |   Agent + 16 @function_tools |
+---------------------+  响应     |   | LLM span               |
                                  |   | TOOL span               |
                                  +------------------------------+
                                           | OTel/OTLP
                                           v
                                  +------------------+
                                  | Phoenix（本地）   |
                                  | http://localhost:  |
                                  | 6006               |
                                  +------------------+
```

外层多轮循环（`agent.py`）在模拟用户和 Agent 框架之间传递消息。仅 Agent 框架进行埋点；模拟用户代表真实用户，不进行追踪，与生产埋点的实际情况一致。

每次 `Runner.run()` 调用对应一个“Agent 轮次”：SDK 负责 LLM 调用 → 工具调用（若有）→ 最终文本响应。OpenInference 自动为整个过程埋点，每个轮次生成一棵 span 树：

```
conversation.turn （手动，AGENT）       <- 包围完整轮次
  Agent workflow （自动，AGENT）          <- SDK 编排
    RetailAgent （自动，AGENT）           <- Agent 节点
      response （自动，LLM）             <- 包含完整消息历史的 LLM 调用
      <tool_name> （自动，TOOL）         <- 工具执行（若有）
      response （自动，LLM）             <- 后续 LLM 调用（若调用了工具）
```

<a id="setup"></a>

## 设置

<a id="prerequisites"></a>

### 前置条件

- Python 3.11+
- 已设置 `OPENAI_API_KEY` 环境变量
- 本地运行的 Phoenix（`python -m phoenix.server.main serve`）

<a id="install-dependencies"></a>

### 安装依赖

```bash
pip install openai-agents openinference-instrumentation-openai-agents arize-phoenix litellm openai
```

<a id="usage"></a>

## 使用方法

在 `examples/agents/` 目录中执行：

```bash
# 运行选定的全部 10 个任务
python -m tau_bench_openai_agents.run

# 按标签运行指定任务（split:index 格式）
python -m tau_bench_openai_agents.run --tasks dev:0 dev:12 train:35

# 不使用 Phoenix（不导出追踪）
python -m tau_bench_openai_agents.run --no-phoenix

# 将结果保存至指定路径
python -m tau_bench_openai_agents.run --output results.json
```

默认将结果保存至 `results/tau_bench_openai_agents_<timestamp>.json`。

<a id="selected-tasks"></a>

## 选定任务

任务来自 **dev** 和 **train** 划分，不使用保留的 test 划分。所有划分均包含完整标准工具序列（带 `name` 和 `kwargs` 的 `actions`）。

| 任务 ID | 类别 | 概述 | 预期操作 |
|---------|----------|---------|-----------------|
| dev:0 | 单次取消 | 取消待处理订单，通过姓名和邮政编码验证身份 | 1（取消） |
| dev:1 | 单次换货 | 为已送达商品换货，通过邮箱验证身份 | 1（换货） |
| dev:6 | 身份验证边界情况 | 存在多个邮箱，用户不确定使用哪个 | 1（取消） |
| dev:9 | 单次修改 | 修改待处理订单商品 | 1（修改商品） |
| dev:12 | 复杂多次修改 | 3 个订单：分别修改付款方式和商品 | 6（3 组付款方式和商品修改） |
| dev:14 | 多步骤 | 同一订单修改地址和商品 | 2（地址和商品） |
| dev:15 | 策略边界 | 用户争辩，先提出超出范围的要求，再取消 | 1（取消） |
| dev:17 | 零操作 | 用户抱怨，无可执行操作 | 0 |
| train:35 | 多类型 | 地址、商品、退货和换货 | 4 |
| train:351 | 复杂多类型 | 取消、换货、付款方式、商品、退货和地址 | 7 |

<a id="file-structure"></a>

## 文件结构

| 文件 | 用途 |
|------|---------|
| `agent.py` | Agent 定义（`create_agent()`）和多轮对话循环（`run_conversation()`） |
| `tools.py` | 16 个以 `@function_tool` 函数实现的零售工具；每个工具通过共享的模块级 `_data` 字典调用 tau-bench `Tool.invoke()` |
| `db.py` | 内存数据库加载器；为每个任务深拷贝 tau-bench JSON 数据以隔离变更 |
| `user_sim.py` | 对 tau-bench `LLMUserSimulationEnv` 的延迟初始化封装，避免 `__init__` 中立即发起 LLM 调用 |
| `phoenix_setup.py` | OpenInference 埋点和 Phoenix OTLP 连接 |
| `tasks.py` | 从 dev/train 划分选择任务 |
| `run.py` | CLI 入口 |

<a id="how-it-works"></a>

## 工作原理

<a id="tool-integration"></a>

### 工具集成

工具以原生 `@function_tool` 装饰函数注册（`tools.py`）。每个函数封装一个 tau-bench `Tool` 类，并委托其 `invoke()` 方法执行。每个任务开始前，通过 `set_data()` 在模块级设置共享数据库（`_data` 字典）。OpenAI Agents SDK 根据函数签名和文档字符串自动生成工具 schema，与 tau-bench 的 `get_info()` 返回内容一致。

<a id="multi-turn-loop"></a>

### 多轮循环

`agent.py` 中的对话循环负责外层编排：

1. 为当前任务加载全新数据库副本（`load_data()` 执行深拷贝）
2. 使用任务指令初始化模拟用户，获取第一条消息
3. 对于每个轮次：
   - 调用 `Runner.run(agent, input)`，由 SDK 处理 LLM 和工具执行
   - 从 `run_result.final_output` 提取 Agent 文本响应
   - 检查终止工具调用（`transfer_to_human_agents`）
   - 将响应传给模拟用户，获取下一条消息
   - 通过 `run_result.to_input_list()` 加上新用户消息构建下一次输入
4. 遇到 `###STOP###`（用户满意）、终止工具调用或达到最大轮次数时结束

<a id="phoenix-instrumentation"></a>

### Phoenix 埋点

`phoenix_setup.py` 配置以下内容：

- `TracerProvider`，其 `Resource` 标记项目名称（`tau-bench-openai`）
- 指向本地 Phoenix 的 OTLP exporter
- 设置全局 tracer provider，使自动埋点和手动 span 共享它
- 使用 `OpenAIAgentsInstrumentor` 自动捕获 LLM/TOOL span

`agent.py` 在此基础上增加手动埋点：

- `using_attributes()` 上下文管理器将 `session_id`、`user_id`、`metadata` 和 `tags` 传播至轮次内的所有子 span
- 每个轮次由 `conversation.turn` span 包围，记录 `input.value`（用户消息）和 `output.value`（Agent 响应），为 Phoenix Sessions 提供可读的 HUMAN/AI 时间线

<a id="simulated-user"></a>

### 模拟用户

`user_sim.py` 通过延迟构造封装 tau-bench 的 `LLMUserSimulationEnv`。原始类在 `__init__` 中调用 `self.reset()`，触发无指令的 LLM 调用。封装使用 `object.__new__()` 构造对象而不调用 `__init__`，再手动设置必需字段，然后调用 `reset(instruction)`。

<a id="key-design-decisions"></a>

## 关键设计决策

1. **完整框架集成** — 工具是原生 `@function_tool`，而非适配器。SDK 执行工具，生成真实的 LLM 和 TOOL span。这里不使用 tau-bench 的 `Env.step()`。
2. **模拟用户不进行埋点** — 生产环境不会追踪用户。
3. **不追踪数据库状态** — 生产应用不会通过 OTel 追踪数据库变更。如果轨迹评估需要数据库状态变化，这便揭示了追踪未覆盖的信息。
4. **`parallel_tool_calls=False`** — 与 wiki.md 中 tau-bench 每轮仅调用一个工具的策略一致。
5. **温度 0，gpt-4o** — 为确保可复现性，与 tau-bench 评估设置一致。
6. **仅使用 dev/train 划分** — test 保留。所有划分都完整包含标准答案，即带精确参数的工具序列。
