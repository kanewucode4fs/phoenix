<a id="agent-framework-analysis"></a>

# Agent 框架分析

本项目展示如何使用多个不同框架定义同一个 Agent：

- 纯代码（即不使用框架）
- LangGraph
- LlamaIndex Workflows

更多框架示例正在开发中；如果你希望看到某个框架，欢迎告诉我们！

<a id="prerequisites"></a>

## 前置条件

该 Agent 需要与 Phoenix 项目交互，因此你需要一个包含追踪的 Phoenix 项目。
如果还没有 Phoenix 项目，建议在运行 Agent 前先运行此快速开始教程：https://github.com/Arize-ai/phoenix/blob/main/tutorials/quickstarts/tracing_quickstart_openai.ipynb

你还需要一个 OpenAI API 密钥。

<a id="setup"></a>

## 配置

运行前，请设置以下环境变量：

- OPENAI_API_KEY=""
- PHOENIX_API_KEY=""
- PHOENIX_CLIENT_HEADERS="api_key="
- PHOENIX_COLLECTOR_ENDPOINT=""

安装 requirements.txt 文件中列出的包。

运行 download_traces_from_px.py 脚本，从 Phoenix 下载追踪并保存到本地 SQLite 数据库。

如果尚未启动 Phoenix 实例，请先启动。确保 PHOENIX_COLLECTOR_ENDPOINT 环境变量指向正确的端点。只有连接到 Phoenix 云端实例时，才需要 PHOENIX_API_KEY 和 PHOENIX_CLIENT_HEADERS 环境变量。

<a id="running-the-agent"></a>

## 运行 Agent

有三个不同的 Agent 可供选择，每个都有各自的 `main.py` 文件。运行你想使用的那个文件，即可启动 Agent 聊天界面。

<a id="background-on-the-code"></a>

## 代码背景

除各 Agent 的 `main.py` 和 `router.py` 文件外，它们还使用以下公共文件：

- `utils/instrument.py`：包含根据所用 Agent 为各框架插桩的代码。
- `utils/database.py`：包含连接本地 SQLite 数据库的代码。
- `prompt_templats/`：包含各 Agent 的提示词模板。
- `skills/`：包含纯代码 Agent 和 llama-index Agent 的技能。LangGraph Agent 在自身目录中有独立技能集，因为它需要略有不同的技能结构。
