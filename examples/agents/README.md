<a id="agents"></a>

# Agent 示例

这些 Agent 示例使用 [OpenInference](https://github.com/Arize-ai/openinference) 埋点，并将追踪发送至 [Phoenix](https://github.com/Arize-ai/phoenix)。每个示例通过 Agent 框架运行基准任务，生成包含 LLM 调用、工具执行和多轮对话流程的丰富追踪。

<a id="whats-inside"></a>

## 内容概览

<a id="agent-implementations"></a>

### Agent 实现

| 实现 | 框架 | 基准 | 说明 |
|---|---|---|---|
| `tau_bench_openai_agents/` | OpenAI Agents SDK | [tau-bench](https://github.com/sierra-research/tau-bench) | 多轮零售客服 Agent，包含 16 个工具、用户模拟和策略执行 |
| `tau_bench_langgraph/` | LangGraph | tau-bench | 使用不同框架执行相同零售任务，便于比较 |
| `traject_bench_langgraph/` | LangGraph | [TRAJECT-Bench](https://huggingface.co/datasets/Jnnamchi/traject-bench) | 跨多个领域的单轮并行和顺序工具调用任务 |

<a id="orchestration"></a>

### 编排

| 脚本 | 用途 |
|---|---|
| `run_scaled.py` | 在所有实现上运行批量任务，并使用 Phoenix 追踪 |

<a id="prerequisites"></a>

## 前置条件

- Python 3.11+
- `OPENAI_API_KEY` 环境变量
- 本地运行的 Phoenix（`phoenix serve` 或 Docker），用于收集追踪

<a id="setup"></a>

## 设置

```bash
cd examples/agents

# 方式 1：pip
pip install -r requirements.txt

# 方式 2：uv（推荐）
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# 启动 Phoenix
phoenix serve
```

> **说明**：tau-bench 依赖从 GitHub 安装（`tau-bench @ git+https://...`）。TRAJECT-Bench 数据集在首次运行时从 HuggingFace 下载（下载量较小，之后使用缓存）。

<a id="running-the-examples"></a>

## 运行示例

<a id="run-all-implementations"></a>

### 运行所有实现

```bash
# 运行全部三种实现（每种 20 个任务，约 10 分钟）：
python -m run_scaled

# 运行指定实现：
python -m run_scaled --implementations tau-openai tau-langgraph

# 不使用 Phoenix 追踪：
python -m run_scaled --no-phoenix
```

结果以 JSON 文件保存至 `results/scaled/`。追踪导出至 http://localhost:6006 上的 Phoenix。


<a id="run-a-single-implementation-directly"></a>

### 直接运行单个实现

```bash
# 使用 OpenAI Agents SDK 运行 tau-bench
python -m tau_bench_openai_agents.run

# 使用 LangGraph 运行 tau-bench
python -m tau_bench_langgraph

# 使用 LangGraph 运行 TRAJECT-Bench
python -m traject_bench_langgraph
```

<a id="architecture"></a>

## 架构

```
run_scaled.py
  ├── tau_bench_openai_agents/   ← OpenAI Agents SDK + 用户模拟器
  ├── tau_bench_langgraph/       ← LangGraph + 用户模拟器
  └── traject_bench_langgraph/   ← LangGraph 单轮
```

每个 Agent 实现包含：

- `agent.py` — Agent 定义和对话运行器
- `tools.py` — 与基准预期 API 匹配的工具定义
- `tasks.py` / `tasks_scaled.py` — 从基准数据集加载任务
- `phoenix_setup.py` — OpenTelemetry + Phoenix 埋点设置
- `db.py` — tau-bench 的内存数据库（零售领域状态）
- `user_sim.py` — tau-bench 多轮对话用户模拟器

<a id="tau-bench-agents"></a>

### tau-bench 智能体

tau-bench Agent 实现零售客服工作流。模拟用户（由 LLM 驱动）提出取消、退货、换货和订单修改等请求；Agent 必须验证用户身份、查询相关数据，并使用 16 个可用工具执行正确的变更。对话持续多个轮次，直到用户满意或 Agent 升级处理。

OpenAI Agents SDK 和 LangGraph 实现使用相同的工具、数据库和用户模拟器，仅 Agent 框架不同，因此适合比较框架选择如何影响追踪结构。

<a id="traject-bench-agent"></a>

### TRAJECT-Bench 智能体

TRAJECT-Bench Agent 处理来自 [TRAJECT-Bench 数据集](https://huggingface.co/datasets/Jnnamchi/traject-bench)的单轮工具调用任务。任务覆盖电商、旅行、金融、音乐等多个领域，分为两类：

- **并行**：多个独立工具调用，可按任意顺序执行
- **顺序**：工具调用具有依赖关系，前一个调用的输出作为下一个调用的输入

工具根据数据集中的工具定义为每个任务动态创建；参数与标准答案匹配时，返回预先记录的输出。

<a id="exploring-traces-in-phoenix"></a>

## 在 Phoenix 中探索追踪

运行示例后，在 http://localhost:6006 打开 Phoenix。每个实现将追踪发送至各自的项目：

| 项目名称 | 实现 |
|---|---|
| `tau-bench-openai` | tau-bench + OpenAI Agents SDK |
| `tau-bench-langgraph` | tau-bench + LangGraph |
| `traject-bench-langgraph` | TRAJECT-Bench + LangGraph |

值得查看的内容：

- **追踪视图** — 每条追踪对应一次任务执行。展开 span 树，查看 LLM → 工具调用 → LLM 循环。比较 OpenAI Agents SDK 和 LangGraph 项目的 span 嵌套结构。
- **会话** — tau-bench 追踪按会话分组，每个任务对应一个会话。每个会话展示多轮 HUMAN/AI 对话时间线。
- **Span 详情** — 点击任意 LLM span，查看完整消息历史、token 计数和模型参数。点击 TOOL span，查看传入参数和返回值。
- **并行与顺序** — 在 TRAJECT-Bench 项目中，比较并行任务（同级 TOOL span）和顺序任务（输出传入下一次调用的链式 TOOL span）。

<!-- 截图：待补充 -->
