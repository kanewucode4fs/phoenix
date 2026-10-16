<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-otel">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        arize-phoenix-otel
    </div>
</h1>

<p align="center">
    <a href="https://pypi.org/project/arize-phoenix-otel/">
        <img src="https://img.shields.io/pypi/v/arize-phoenix-otel" alt="PyPI 版本">
    </a>
    <a href="https://arize-phoenix.readthedocs.io/projects/otel/">
        <img src="https://img.shields.io/badge/docs-blue?logo=readthedocs&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=packages/phoenix-otel/README.md" />
</p>

提供对 OpenTelemetry 基础能力的轻量封装，带有适合 Phoenix 的默认值。Phoenix OTEL 还提供常见 GenAI 模式的追踪装饰器。

<a id="features"></a>

## 功能

`arize-phoenix-otel` 通过以下功能简化 Phoenix 用户的 OpenTelemetry 配置：

- 为常见 OpenTelemetry 基础能力提供**适合 Phoenix 的默认值**
- 从环境变量**自动配置**
- 提供功能增强的 OTel 类**直接替代实现**
- 通过 `register()` 函数**简化追踪配置**
- GenAI 模式的**追踪装饰器**

<a id="key-benefits"></a>

## 主要优势

- **零代码改动**：启用 `auto_instrument=True` 自动为 AI 库插桩
- **适用于生产**：内置批处理和身份验证
- **Phoenix 集成**：无缝集成 Phoenix Cloud 和自托管实例
- **兼容 OpenTelemetry**：可与现有 OpenTelemetry 基础设施配合使用
- **独立于服务器版本**：与 Phoenix 服务器分别管理版本；近期任一 `arize-phoenix-otel` 均可配合任何 Phoenix 服务器版本使用，无需维护版本配对（追踪使用 OpenInference 语义约定，通过 OTLP 发送，两者均向后兼容）

这些默认值会识别你可能已设置的 Phoenix 配置环境变量：

- `PHOENIX_COLLECTOR_ENDPOINT`
- `PHOENIX_PROJECT_NAME`
- `PHOENIX_CLIENT_HEADERS`
- `PHOENIX_API_KEY`
- `PHOENIX_GRPC_PORT`

<a id="installation"></a>

## 安装

通过 `pip` 安装：

```shell
pip install arize-phoenix-otel
```

<a id="quick-start"></a>

## 快速开始

**推荐**：启用自动插桩，无需修改代码即可追踪 AI 库：

```python
from phoenix.otel import register

# Recommended: Automatic instrumentation + production settings
tracer_provider = register(
    auto_instrument=True,  # Auto-trace OpenAI, LangChain, LlamaIndex, etc.
    batch=True,  # Production-ready batching
    project_name="my-app",  # Organize your traces
)
```

完成！所有 `openinference-*` AI 库现在都会自动被追踪，并将追踪发送到 Phoenix。

**注意**：只有安装对应 OpenInference 插桩库时，`auto_instrument=True` 才生效。例如，要自动追踪 OpenAI 调用，需要安装 `openinference-instrumentation-openai`：

```bash
pip install openinference-instrumentation-openai
pip install openinference-instrumentation-langchain  # For LangChain
pip install openinference-instrumentation-llama-index  # For LlamaIndex
```

可用插桩包的完整列表见 [OpenInference 仓库](https://github.com/Arize-ai/openinference)。

<a id="authentication"></a>

### 身份验证

```bash
export PHOENIX_API_KEY="your-api-key"
```

```python
# Or pass directly to register()
tracer_provider = register(api_key="your-api-key")
```

<a id="endpoint-configuration"></a>

### 端点配置

配置追踪发送位置：

**环境变量**（推荐）：

```bash
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance.com"
export PHOENIX_PROJECT_NAME="my-project"
```

**直接配置**：

```python
tracer_provider = register(
    endpoint="http://localhost:6006/v1/traces",  # HTTP endpoint
    protocol="grpc",  # Or force gRPC protocol
)
```

<a id="usage-examples"></a>

## 使用示例

<a id="simple-setup"></a>

### 简单配置

```python
from phoenix.otel import register

# Basic setup - sends to localhost
tracer_provider = register(auto_instrument=True)
```

<a id="production-configuration"></a>

### 生产配置

```python
tracer_provider = register(
    project_name="my-production-app",
    auto_instrument=True,  # Auto-trace AI/ML libraries
    batch=True,  # Background batching for performance
    api_key="your-api-key",  # Authentication
    endpoint="https://your-phoenix-instance.com",
)
```

<a id="manual-configuration"></a>

### 手动配置

高级用例可直接使用 Phoenix OTEL 组件：

```python
from phoenix.otel import TracerProvider, BatchSpanProcessor, HTTPSpanExporter

tracer_provider = TracerProvider()
exporter = HTTPSpanExporter(endpoint="http://localhost:6006/v1/traces")
processor = BatchSpanProcessor(span_exporter=exporter)
tracer_provider.add_span_processor(processor)
```

<a id="using-decorators"></a>

### 使用装饰器

```python
from phoenix.otel import register

tracer_provider = register()

# Get a tracer for manual instrumentation
tracer = tracer_provider.get_tracer(__name__)


@tracer.chain
def process_data(data):
    return data + " processed"


@tracer.tool
def weather(location):
    return "sunny"
```

<a id="environment-variables"></a>

## 环境变量

| 变量                     | 说明          | 示例                                      |
| ---------------------------- | -------------------- | -------------------------------------------- |
| `PHOENIX_COLLECTOR_ENDPOINT` | 追踪发送位置 | `https://your-phoenix-instance.com`          |
| `PHOENIX_PROJECT_NAME`       | 项目名称         | `my-llm-app`                                 |
| `PHOENIX_API_KEY`            | 身份验证密钥   | `your-api-key`                               |
| `PHOENIX_CLIENT_HEADERS`     | 自定义请求头       | `Authorization=Bearer token`                 |
| `PHOENIX_GRPC_PORT`          | 覆盖 gRPC 端口   | `4317`                                       |
| `PHOENIX_DISCOVER_CONFIG`    | 设为 `false` 可禁用 `.env.phoenix` 发现 | `false`        |

<a id="credential-file-discovery-envphoenix"></a>

### 凭证文件发现（`.env.phoenix`）

当参数或环境变量未提供某项配置时，`register()` 从当前工作目录开始向文件系统根目录逐级查找 `.env.phoenix`，在首个匹配处停止，并读取其中以 `PHOENIX_` 为前缀的键（dotenv 格式）：

```bash
# .env.phoenix
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
PHOENIX_API_KEY=your-api-key
```

显式参数和环境变量始终优先，文件绝不会覆盖已设置的值。设置 `PHOENIX_DISCOVER_CONFIG=false` 可完全禁用发现。

凭证（`PHOENIX_API_KEY`、`PHOENIX_CLIENT_HEADERS` 和 `OTEL_EXPORTER_OTLP_HEADERS`）与服务器位置（`PHOENIX_COLLECTOR_ENDPOINT`、`OTEL_EXPORTER_OTLP_ENDPOINT` 和 `PHOENIX_GRPC_PORT`）各自作为一组，从同一来源层级解析，避免仅在文件中设置的 gRPC 端口改写进程提供的端点。若显式或进程凭证与 `.env.phoenix` 中的端点配对，Phoenix OTel 会发出一次警告后继续，不记录凭证值。

发现结果（包括文件缺失）按工作目录缓存，持续整个进程生命周期。长期运行的进程可在创建或修改文件后调用 `phoenix.otel.settings.clear_env_file_cache()`。

<a id="coding-agent-skill"></a>

## 编码 Agent 技能

Phoenix 仓库包含 [phoenix-tracing 技能](https://github.com/Arize-ai/phoenix/tree/main/.agents/skills/phoenix-tracing)，用于指导编码 Agent（Claude Code、Cursor 等）使用 OpenInference 追踪为 LLM 应用插桩。安装方式：

```bash
npx skills add Arize-ai/phoenix --skill phoenix-tracing
```

<a id="documentation"></a>

## 文档

- **[完整文档](https://arize-phoenix.readthedocs.io/projects/otel/)** - 完整 API 参考与指南
- **[Phoenix 文档](https://arize.com/docs/phoenix)** - 详细追踪示例与模式
- **[OpenInference](https://github.com/Arize-ai/openinference)** - 面向框架的自动插桩库

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
