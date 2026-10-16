<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-client">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        arize-phoenix-client
    </div>
</h1>
<p align="center">
    <a href="https://pypi.org/project/arize-phoenix-client/">
        <img src="https://img.shields.io/pypi/v/arize-phoenix-client" alt="PyPI 版本">
    </a>
    <a href="https://arize-phoenix.readthedocs.io/projects/client/">
        <img src="https://img.shields.io/badge/docs-blue?logo=readthedocs&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=packages/phoenix-client/README.md" />
</p>
Phoenix Client 提供通过 REST API 与 Phoenix 平台交互的接口，可用编程方式管理数据集、运行实验、分析追踪并收集反馈。

<a id="features"></a>

## 功能

- **REST API 接口**：与 Phoenix 的 OpenAPI REST 接口交互
- **提示词**：创建、版本管理并调用提示词模板
- **数据集**：从 DataFrame、CSV 文件或字典创建数据集并追加数据
- **实验**：运行评估并跟踪实验结果
- **评估 CI（pytest）**：将 LLM 评估作为普通 pytest 测试运行，并记录为 Phoenix 实验（`pip install "arize-phoenix-client[pytest]"`）
- **Span**：借助强大过滤能力查询和分析追踪
- **标注**：添加人工反馈和自动评估
- **评估辅助函数**：以针对 RAG 评估流程优化的格式提取 Span 数据

<a id="installation"></a>

## 安装

通过 pip 安装 Phoenix Client：

```bash
pip install arize-phoenix-client
```

<a id="getting-started"></a>

## 开始使用

<a id="environment-variables"></a>

### 环境变量

通过环境变量配置 Phoenix Client，以便在不同环境中无缝使用：

```bash
# For local Phoenix server (default)
export PHOENIX_ENDPOINT="http://localhost:6006"

# A hosted or self-hosted instance with authentication
export PHOENIX_ENDPOINT="https://phoenix.example.com"
export PHOENIX_API_KEY="your-api-key"

# Customize headers
export PHOENIX_CLIENT_HEADERS="Authorization=Bearer your-api-key,custom-header=value"
```

`PHOENIX_ENDPOINT` 是基础 URL，也是客户端的规范配置。若应用也导出追踪，请为 OTel SDK 设置 `PHOENIX_COLLECTOR_ENDPOINT`，通常使用相同值。仅设置 `PHOENIX_COLLECTOR_ENDPOINT` 时，客户端会据此推断基础 URL。 完整列表见[环境](https://arize.com/docs/phoenix/environments)。

<a id="credential-file-discovery-envphoenix"></a>

### 凭证文件发现（`.env.phoenix`）

当参数或环境变量未提供某项配置时，客户端从当前工作目录开始向文件系统根目录逐级查找 `.env.phoenix`，在首个匹配处停止，并读取其中以 `PHOENIX_` 为前缀的键（dotenv 格式）：

```bash
# .env.phoenix
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_API_KEY=your-api-key
```

显式参数和环境变量始终优先，文件绝不会覆盖已设置的值。设置 `PHOENIX_DISCOVER_CONFIG=false` 可完全禁用发现。

凭证（`PHOENIX_API_KEY` 和 `PHOENIX_CLIENT_HEADERS`）与服务器位置（`PHOENIX_ENDPOINT` 及其回退变量）各自作为一组，从同一来源层级解析。若显式或进程凭证与 `.env.phoenix` 中的端点配对，客户端会发出一次警告后继续，不记录凭证值。

发现结果（包括文件缺失）按工作目录缓存，持续整个进程生命周期。长期运行的进程可在创建或修改文件后调用 `phoenix.client.utils.config.clear_env_file_cache()`。

<a id="client-initialization"></a>

### 初始化客户端

客户端自动读取环境变量，也可以显式覆盖：

```python
from phoenix.client import Client, AsyncClient

# Automatic configuration from environment variables
client = Client()

client = Client(base_url="http://localhost:6006")  # Local Phoenix server

# Remote instance with API key
client = Client(base_url="https://your-phoenix-instance.com", api_key="your-api-key")

# Custom authentication headers
client = Client(
    base_url="https://your-phoenix-instance.com", headers={"Authorization": "Bearer your-api-key"}
)

# Asynchronous client (same configuration options)
async_client = AsyncClient()
async_client = AsyncClient(base_url="http://localhost:6006")
async_client = AsyncClient(base_url="https://your-phoenix-instance.com", api_key="your-api-key")
```

<a id="resources"></a>

## 资源

Phoenix Client 按对应 Phoenix 平台主要功能的资源组织能力，各资源提供管理不同数据类型的专用方法：

<a id="prompts"></a>

### 提示词

管理提示词模板及版本：

```python
from phoenix.client import Client
from phoenix.client.types import PromptVersion

client = Client()

content = """
You're an expert educator in {{ topic }}. Summarize the following article
in a few concise bullet points that are easy for beginners to understand.

{{ article }}
"""

prompt = client.prompts.create(
    name="article-bullet-summarizer",
    version=PromptVersion(
        messages=[{"role": "user", "content": content}],
        model_name="gpt-4o-mini",
    ),
    prompt_description="Summarize an article in a few bullet points",
)

# Retrieve and use prompts
prompt = client.prompts.get(prompt_identifier="article-bullet-summarizer")

# Format the prompt with variables
prompt_vars = {
    "topic": "Sports",
    "article": "Moises Henriques, the Australian all-rounder, has signed to play for Surrey in this summer's NatWest T20 Blast. He will join after the IPL and is expected to strengthen the squad throughout the campaign.",
}
formatted_prompt = prompt.format(variables=prompt_vars)

# Make a request with your Prompt using OpenAI
from openai import OpenAI

oai_client = OpenAI()
resp = oai_client.chat.completions.create(**formatted_prompt)
print(resp.choices[0].message.content)
```

<a id="datasets"></a>

### 数据集

管理评估数据集及示例，用于实验和评估：

```python
from phoenix.client import Client
import pandas as pd

client = Client()

# List all available datasets
datasets = client.datasets.list()
for dataset in datasets:
    print(f"Dataset: {dataset['name']} ({dataset['example_count']} examples)")

# Get a specific dataset with all examples
dataset = client.datasets.get_dataset(dataset="qa-evaluation")
print(f"Dataset {dataset.name} has {len(dataset)} examples")

# Convert dataset to pandas DataFrame for analysis
df = dataset.to_dataframe()
print(df.columns)  # Index(['input', 'output', 'metadata'], dtype='object')

# Create a new dataset from dictionaries
dataset = client.datasets.create_dataset(
    name="customer-support-qa",
    dataset_description="Q&A dataset for customer support evaluation",
    inputs=[
        {"question": "How do I reset my password?"},
        {"question": "What's your return policy?"},
        {"question": "How do I track my order?"},
    ],
    outputs=[
        {
            "answer": "You can reset your password by clicking the 'Forgot Password' link on the login page."
        },
        {"answer": "We offer 30-day returns for unused items in original packaging."},
        {"answer": "You can track your order using the tracking number sent to your email."},
    ],
    metadata=[
        {"category": "account", "difficulty": "easy"},
        {"category": "policy", "difficulty": "medium"},
        {"category": "orders", "difficulty": "easy"},
    ],
)

# Create dataset from pandas DataFrame
df = pd.DataFrame(
    {
        "prompt": ["Hello", "Hi there", "Good morning"],
        "response": [
            "Hi! How can I help?",
            "Hello! What can I do for you?",
            "Good morning! How may I assist?",
        ],
        "sentiment": ["neutral", "positive", "positive"],
        "length": [20, 25, 30],
    }
)

dataset = client.datasets.create_dataset(
    name="greeting-responses",
    dataframe=df,
    input_keys=["prompt"],  # Columns to use as input
    output_keys=["response"],  # Columns to use as expected output
    metadata_keys=["sentiment", "length"],  # Additional metadata columns
)
```

<a id="traces"></a>

### 追踪

获取项目追踪，可选择过滤和排序：

```python
from phoenix.client import Client

client = Client()

# Get the latest 100 traces
traces = client.traces.get_traces(project_identifier="my-llm-app")
for trace in traces:
    print(f"Trace {trace.trace_id}: {trace.status} ({trace.latency_ms}ms)")

# Filter by time range
from datetime import datetime, timedelta

traces = client.traces.get_traces(
    project_identifier="my-llm-app",
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now(),
    sort="latency_ms",
    order="desc",
    limit=50,
)

# Include full span details
traces = client.traces.get_traces(
    project_identifier="my-llm-app",
    include_spans=True,  # caution: can increase response size significantly
    limit=10,
)

# Filter by session
traces = client.traces.get_traces(
    project_identifier="my-llm-app",
    session_id="my-session-id",
)
```

**异步用法：**

```python
from phoenix.client import AsyncClient

async_client = AsyncClient()

traces = await async_client.traces.get_traces(
    project_identifier="my-llm-app",
    limit=50,
)
```

| 参数              | 类型                                    | 默认值 | 说明                                          |
| ---------------------- | --------------------------------------- | ------- | ---------------------------------------------------- |
| `project_identifier`   | `str`                                   | —       | 项目名称或 ID，**必填**                    |
| `start_time`           | `datetime \| None`                      | `None`  | 追踪开始时间下界（包含）             |
| `end_time`             | `datetime \| None`                      | `None`  | 追踪开始时间上界（不包含）            |
| `sort`                 | `"start_time" \| "latency_ms" \| None`  | `None`  | 排序字段（服务器默认为 `"start_time"`）       |
| `order`                | `"asc" \| "desc" \| None`              | `None`  | 排序方向（服务器默认为 `"desc"`）         |
| `include_spans`        | `bool`                                  | `False` | 包含每条追踪的完整 Span 详情             |
| `session_id`           | `str \| Sequence[str] \| None`          | `None`  | 按会话 ID 或 GlobalID 过滤               |
| `limit`                | `int`                                   | `100`   | 返回追踪的最大数量                   |
| `timeout`              | `int \| None`                           | `60`    | 请求超时秒数                           |

> **注意：** 要求 Phoenix 服务器 >= 13.15.0。

<a id="spans"></a>

### Span

从项目中查询 Span 和标注，用于自定义评估和标注流程：

```python
from phoenix.client import Client
from phoenix.client.types.spans import SpanQuery
from datetime import datetime, timedelta

client = Client()

# Get spans as pandas DataFrame for analysis
spans_df = client.spans.get_spans_dataframe(
    project_identifier="my-llm-app",
    limit=1000,
    query=SpanQuery().where("parent_id is None"),  # Only top-level spans
    start_time=datetime.now() - timedelta(hours=24),
)

# Get span annotations as DataFrame
annotations_df = client.spans.get_span_annotations_dataframe(
    spans_dataframe=spans_df,  # Use spans from previous query
    project_identifier="my-llm-app",
    include_annotation_names=["relevance", "accuracy"],  # Only specific annotations
    exclude_annotation_names=["note"],  # Exclude UI notes
)
```

<a id="annotations"></a>

### 标注

为 Span 添加标注，用于评估、用户反馈和自定义标注流程：

```python
from phoenix.client import Client

client = Client()

# Add a single annotation with human feedback
client.spans.add_span_annotation(
    span_id="span-123",
    annotation_name="helpfulness",
    annotator_kind="HUMAN",
    label="helpful",
    score=0.9,
    explanation="Response directly answered the user's question",
)

# Bulk annotation logging for multiple spans
annotations = [
    {
        "name": "sentiment",
        "span_id": "span-123",
        "annotator_kind": "LLM",
        "result": {"label": "positive", "score": 0.8},
    },
    {
        "name": "accuracy",
        "span_id": "span-456",
        "annotator_kind": "HUMAN",
        "result": {"label": "accurate", "score": 0.95},
    },
]
client.spans.log_span_annotations(span_annotations=annotations)
```

<a id="sessions"></a>

### 会话

获取并标注对话会话：

```python
from phoenix.client import Client

client = Client()

# List sessions for a project
sessions = client.sessions.list(project_name="my-llm-app")
for session in sessions:
    print(f"Session: {session['session_id']}")

# Get conversation turns for a session
turns = client.sessions.get_session_turns(session_id="my-session-id")
for turn in turns:
    print(f"Input: {turn.get('input', {}).get('value')}")
    print(f"Output: {turn.get('output', {}).get('value')}")

# Add a session-level annotation
client.sessions.add_session_annotation(
    session_id="my-session-id",
    annotation_name="user-satisfaction",
    label="satisfied",
    score=0.9,
    annotator_kind="HUMAN",
)
```

<a id="experiments"></a>

### 实验

在数据集上运行任务并评估输出：

```python
from phoenix.client import Client

client = Client()

# Get an existing dataset to run the experiment on
dataset = client.datasets.get_dataset(dataset="my-dataset")


# Define a task function
def my_task(example):
    # Your LLM call or business logic here
    return f"Result for: {example['input']['question']}"


# Run an experiment
experiment = client.experiments.run_experiment(
    dataset=dataset,
    task=my_task,
    experiment_name="my-experiment",
)

# Retrieve an existing experiment
ran_experiment = client.experiments.get_experiment(experiment_id="my-experiment-id")
for run in ran_experiment["task_runs"]:
    print(f"Output: {run['output']}, Error: {run['error']}")
```

除批量 `run_experiment` 循环外，还可以通过 `log_run` 和 `log_evaluation` 逐个提交运行和评估。它们是 pytest 插件所依赖的增量基础能力，适用于逐步产生结果而非一次性生成全部结果的使用方：

```python
from datetime import datetime, timezone

# Record a single run against an existing experiment and example
run = client.experiments.log_run(
    experiment_id="my-experiment-id",
    dataset_example_id="my-example-id",
    output="the task output",
    start_time=datetime.now(timezone.utc),
    end_time=datetime.now(timezone.utc),
)

# Attach an evaluation (annotation) to that run
client.experiments.log_evaluation(
    experiment_run_id=run["id"],
    name="exact_match",
    annotator_kind="CODE",
    score=1.0,
    label="correct",
)
```

两个方法在 `AsyncClient` 上均提供相同签名的可等待协程。

<a id="eval-ci-pytest"></a>

### 评估 CI（pytest）

将 LLM 评估编写为普通 pytest 测试，并将每个标记测试记录为 Phoenix 实验中的一次运行，使控制 PR 是否通过的同一套测试也在 Phoenix 中积累结果历史。安装 `pytest` 扩展依赖，并用 `@pytest.mark.phoenix` 标记测试：

```bash
pip install "arize-phoenix-client[pytest]" pytest
```

```python
import pytest
from phoenix.client.pytest import evaluate, log_evaluation, log_output


@pytest.mark.phoenix(dataset="qa-suite")
@pytest.mark.parametrize("question,expected", [("2+2?", "4")], ids=["arithmetic"])
def test_answers(question, expected):
    result = my_app(question)
    log_output(result)
    log_evaluation(name="exact_match", score=float(result == expected))
    assert result == expected
```

标记选项、环境变量和 CI 配置示例见[使用 pytest 进行评估 CI 的指南](https://arize.com/docs/phoenix/datasets-and-experiments/how-to-experiments/eval-ci-with-pytest)。

<a id="projects"></a>

### 项目

管理用于组织 AI 应用数据的 Phoenix 项目：

```python
from phoenix.client import Client

client = Client()

# List all projects
projects = client.projects.list()
for project in projects:
    print(f"Project: {project['name']} (ID: {project['id']})")

# Filter server-side by a case-insensitive substring of the project name
support_projects = client.projects.list(name_contains="support")

# Create a new project
new_project = client.projects.create(
    name="Customer Support Bot",
    description="Traces and evaluations for our customer support chatbot",
)
print(f"Created project with ID: {new_project['id']}")
```

<a id="documentation"></a>

## 文档

- **[完整文档](https://arize-phoenix.readthedocs.io/projects/client/)** - 完整 API 参考与指南
- **[Phoenix 文档](https://arize.com/docs/phoenix)** - Phoenix 主文档
- **[GitHub 仓库](https://github.com/Arize-ai/phoenix)** - 源代码和示例

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g).
- 💡 在 _#phoenix-support_ 频道提问并反馈。
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星。
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)，了解未来方向。
