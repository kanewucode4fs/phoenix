<a id="phoenix-otel-reference"></a>

# Phoenix OTEL 参考文档

欢迎阅读 Phoenix OTEL 参考文档。此包提供对 OpenTelemetry 基础能力的轻量封装，带有适合 Phoenix 的默认值以及常见 GenAI 模式的追踪装饰器。`arize-phoenix-otel` 通过以下功能简化 Phoenix 用户的 OpenTelemetry 配置：

- 常见 OpenTelemetry 基础能力的 Phoenix 默认配置
- 从环境变量自动配置
- 功能增强的 OTel 类直接替代实现
- 通过 `register()` 函数简化追踪配置
- GenAI 模式的追踪装饰器

主要组件包括：

- **[注册](api/register)**：通过 `register()` 简单完成初始化和配置
- **[TracerProvider](api/provider)**：适配 Phoenix 的追踪提供程序
- **[Span 处理器](api/processors)**：批处理和简单 Span 处理器
- **[导出器](api/exporters)**：HTTP 和 gRPC Span 导出器

<a id="installation"></a>

## 安装

```bash
pip install arize-phoenix-otel
```

<a id="quick-start"></a>

## 快速开始

最简单的入门方式是使用 `register()` 函数：

```python
from phoenix.otel import register

# Simple setup with automatic instrumentation (recommended)
tracer_provider = register(auto_instrument=True)
```

只需这些即可开始在 Phoenix 中使用 OpenTelemetry！`register()` 默认使用 gRPC 将 Span 发送到 `http://localhost` 端点。设置 `auto_instrument=True` 后，会自动追踪 AI/ML 库

<a id="basic-configuration"></a>

### 基本配置

```python
from phoenix.otel import register

# Configure project name, headers, and batch processing
tracer_provider = register(
    project_name="my-llm-app", headers={"Authorization": "Bearer TOKEN"}, batch=True
)
```

<a id="automatic-instrumentation-recommended"></a>

### 自动插桩（推荐）

为以最少配置获得最佳体验，请设置 `auto_instrument=True` 启用自动插桩。这会自动为 OpenAI、Anthropic、LangChain、LlamaIndex 等常见 AI/ML 库插桩：

```python
from phoenix.otel import register

# Recommended: Enable automatic instrumentation
tracer_provider = register(
    project_name="my-llm-app",
    auto_instrument=True,  # Automatically instruments AI/ML libraries
)

# Now your OpenAI, LangChain, etc. calls are automatically traced!
import openai

client = openai.OpenAI()
response = client.chat.completions.create(  # This will be automatically traced
    model="gpt-4", messages=[{"role": "user", "content": "Hello!"}]
)
```

**注意**：只有安装对应的 OpenInference 插桩库时，`auto_instrument=True` 才生效。例如，要自动追踪 OpenAI 调用，需要安装 `openinference-instrumentation-openai`：

```bash
pip install openinference-instrumentation-openai
pip install openinference-instrumentation-langchain  # For LangChain
pip install openinference-instrumentation-llama-index  # For LlamaIndex
```

可用插桩包的完整列表见 [OpenInference 仓库](https://github.com/Arize-ai/openinference)。

**生产提示**：生产部署请设置 `batch=True`，在发送到收集器前对 Span 批处理以提升性能。Span 在后台导出，不会阻塞应用：

```python
tracer_provider = register(
    auto_instrument=True,
    batch=True,  # Recommended for production - exports spans in background
)
```

<a id="authentication"></a>

## 身份验证

如果设置了 `PHOENIX_API_KEY` 环境变量，`register()` 会自动为每个 Span 载荷添加 `authorization` 头。

```python
# Set environment variable
# export PHOENIX_API_KEY=your-api-key

from phoenix.otel import register

tracer_provider = register()  # Automatically uses API key for auth
```

<a id="endpoint-configuration"></a>

## 端点配置

有两种收集器端点配置方式：

<a id="using-environment-variables"></a>

### 使用环境变量

如果设置 `PHOENIX_COLLECTOR_ENDPOINT` 环境变量，`register()` 会自动尝试通过 gRPC 向 Phoenix 服务器发送 Span。

```bash
export PHOENIX_COLLECTOR_ENDPOINT=https://your-phoenix.com:6006
```

```python
from phoenix.otel import register

tracer_provider = register()
```

<a id="specifying-the-endpoint-directly"></a>

### 直接指定端点

传入 `endpoint` 参数时，**必须指定完整端点**。例如，通过 HTTP 向本地主机导出 Span 时，请使用 Phoenix HTTP 收集器端点：`http://localhost:6006/v1/traces`。默认 gRPC 端点则不同：`http://localhost:4317`。

```python
from phoenix.otel import register

# HTTP endpoint
tracer_provider = register(endpoint="http://localhost:6006/v1/traces")

# Custom gRPC endpoint
tracer_provider = register(endpoint="http://localhost:9999", protocol="grpc")
```

无论指定何种端点，均可用 `protocol` 参数强制指定 OTLP 传输协议。有效协议为："http/protobuf" 和 "grpc"。

<a id="drop-in-replacement-for-otel-primitives"></a>

## 直接替代 OTel 基础组件

需要更精细的追踪配置时，可用 Phoenix OTEL 封装直接替代 OpenTelemetry 基础组件：

```python
from opentelemetry import trace as trace_api
from phoenix.otel import HTTPSpanExporter, TracerProvider, SimpleSpanProcessor

tracer_provider = TracerProvider()
span_exporter = HTTPSpanExporter(endpoint="http://localhost:6006/v1/traces")
span_processor = SimpleSpanProcessor(span_exporter=span_exporter)
tracer_provider.add_span_processor(span_processor)
trace_api.set_tracer_provider(tracer_provider)
```

<a id="simplified-configuration-with-endpoint-inference"></a>

### 通过端点推断简化配置

封装提供适合 Phoenix 的默认值，大幅简化 OpenTelemetry 配置过程。可向 `TracerProvider`、`SimpleSpanProcessor` 或 `BatchSpanProcessor` 传入专用 `endpoint` 关键字参数，以自动推断使用哪个 `SpanExporter`：

```python
from phoenix.otel import TracerProvider

# Automatically configures the appropriate span exporter
tracer_provider = TracerProvider(endpoint="http://localhost:4317")
```

<a id="span-processors"></a>

## Span 处理器

<a id="multiple-span-processors"></a>

### 多个 Span 处理器

`phoenix.otel` TracerProvider 自动创建默认 Span 处理器，将 Span 发送到 Phoenix 收集器端点。默认情况下，添加新 Span 处理器会替换这个自动创建的处理器。

要同时保留默认处理器和新处理器，请传入 `replace_default_processor=False`：

```python
from phoenix.otel import TracerProvider, BatchSpanProcessor

# TracerProvider automatically creates a default processor
tracer_provider = TracerProvider()

# This replaces the default processor (default behavior)
tracer_provider.add_span_processor(BatchSpanProcessor())

# This keeps the default processor and adds another one
tracer_provider.add_span_processor(BatchSpanProcessor(), replace_default_processor=False)
```

<a id="batch-processing"></a>

### 批处理

```python
from phoenix.otel import TracerProvider, BatchSpanProcessor

tracer_provider = TracerProvider()
batch_processor = BatchSpanProcessor()
tracer_provider.add_span_processor(batch_processor)
```

<a id="custom-grpc-endpoints"></a>

### 自定义 gRPC 端点

```python
from phoenix.otel import TracerProvider, BatchSpanProcessor, GRPCSpanExporter

tracer_provider = TracerProvider()
batch_processor = BatchSpanProcessor(
    span_exporter=GRPCSpanExporter(endpoint="http://custom-endpoint.com:6789")
)
tracer_provider.add_span_processor(batch_processor)
```

<a id="resource-configuration"></a>

## 资源配置

```python
from opentelemetry import trace as trace_api
from phoenix.otel import Resource, PROJECT_NAME, TracerProvider

tracer_provider = TracerProvider(resource=Resource({PROJECT_NAME: "my-project"}))
trace_api.set_tracer_provider(tracer_provider)
```

<a id="advanced-configuration"></a>

## 高级配置

`register()` 和 `TracerProvider` 均接收标准 OpenTelemetry `TracerProvider` 的全部同类关键字参数，可配置自定义 ID 生成器、采样、Span 限制等高级功能。

```python
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from phoenix.otel import register, TracerProvider

# Configure directly with register()
tracer_provider = register(
    project_name="my-app",
    id_generator=AwsXRayIdGenerator(),  # AWS X-Ray compatible IDs
    sampler=TraceIdRatioBased(0.1),  # Sample 10% of traces
)

# Or configure TracerProvider directly
tracer_provider = TracerProvider(
    project_name="my-app", id_generator=AwsXRayIdGenerator(), sampler=TraceIdRatioBased(0.5)
)
```

<a id="environment-variables"></a>

## 环境变量

此包识别以下 Phoenix 专用环境变量进行自动配置：

- `PHOENIX_COLLECTOR_ENDPOINT`: 收集器端点 URL（如 `https://your-phoenix.com:6006`）
- `PHOENIX_PROJECT_NAME`: Span 项目名称（如 `my-llm-app`）
- `PHOENIX_API_KEY`: 用户或系统密钥
- `PHOENIX_GRPC_PORT`: 覆盖 gRPC 端口（默认 4317）
- `PHOENIX_CLIENT_HEADERS`: 附加请求头（如 `Authorization=Bearer token,custom-header=value`）

<a id="environment-variable-examples"></a>

### 环境变量示例

```bash
# Local Phoenix server (default)
export PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"

# Remote Phoenix instance with API key
export PHOENIX_API_KEY="your-api-key"
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance.com"
export PHOENIX_PROJECT_NAME="production-app"

# Custom Phoenix instance with authentication
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance.com"
export PHOENIX_API_KEY="your-api-key"
export PHOENIX_CLIENT_HEADERS="Authorization=Bearer your-api-key,custom-header=value"

# Override default gRPC port
export PHOENIX_GRPC_PORT="9999"
```

设置这些环境变量后，`register()` 和 Phoenix OTEL 组件会自动使用它们进行配置。

<a id="using-decorators"></a>

## 使用装饰器

Phoenix 提供便捷的装饰器，简化手动插桩。配置追踪器后，可通过简单装饰器为函数插桩：

```python
from phoenix.otel import register

tracer_provider = register(project_name="my-project")
tracer = tracer_provider.get_tracer(__name__)


@tracer.chain
def process_data(input_text: str) -> str:
    return f"Processed: {input_text}"


result = process_data("hello world")  # This call will be traced
```

<a id="openinference-span-kinds"></a>

### OpenInference Span 类型

Phoenix 装饰器支持多种 Span 类型，对应常见 AI 应用模式：

- **链**：用于顺序操作和工作流
- **Agent**：用于自主 AI Agent
- **工具**：用于函数调用和工具使用
- **LLM**：用于语言模型交互
- **检索器**：用于检索操作
- **嵌入**：用于生成嵌入

<a id="chains"></a>

### 链

使用 `@tracer.chain` 追踪顺序操作和工作流：

<a id="using-decorators-1"></a>

#### 使用装饰器

```python
@tracer.chain
def process_document(document: str) -> str:
    # Process the document
    processed = document.upper()
    return processed


# Call the decorated function
result = process_document("hello world")
```

<a id="using-context-managers"></a>

#### 使用上下文管理器

```python
def process_document_manual(document: str) -> str:
    with tracer.start_as_current_span("process_document", openinference_span_kind="chain") as span:
        span.set_input(document)
        processed = document.upper()
        span.set_output(processed)
        return processed
```

<a id="agents"></a>

### Agent

使用 `@tracer.agent` 追踪自主 AI Agent：

<a id="using-decorators-2"></a>

#### 使用装饰器

```python
@tracer.agent
def ai_agent(query: str) -> str:
    # Agent logic here
    response = f"Agent response to: {query}"
    return response
```

<a id="using-context-managers-1"></a>

#### 使用上下文管理器

```python
def ai_agent_manual(query: str) -> str:
    with tracer.start_as_current_span("ai_agent", openinference_span_kind="agent") as span:
        span.set_input(query)
        response = f"Agent response to: {query}"
        span.set_output(response)
        return response
```

<a id="tools"></a>

### 工具

使用 `@tracer.tool` 追踪函数调用和工具使用：

<a id="using-decorators-3"></a>

#### 使用装饰器

```python
@tracer.tool
def get_weather(city: str) -> str:
    # Simulate weather API call
    return f"Weather in {city}: Sunny, 75°F"


@tracer.tool
def search_database(query: str) -> list:
    # Simulate database search
    return [f"Result 1 for {query}", f"Result 2 for {query}"]
```

<a id="using-context-managers-2"></a>

#### 使用上下文管理器

```python
def get_weather_manual(city: str) -> str:
    with tracer.start_as_current_span("get_weather", openinference_span_kind="tool") as span:
        span.set_input(city)
        weather = f"Weather in {city}: Sunny, 75°F"
        span.set_output(weather)
        return weather
```

<a id="llms"></a>

### LLM

使用 `@tracer.llm` 追踪带自定义输入/输出处理的语言模型交互：

<a id="using-decorators-with-processing-functions"></a>

#### 使用带处理函数的装饰器

```python
from typing import Dict, List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from opentelemetry.util.types import AttributeValue

openai_client = OpenAI()


def process_input(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: Optional[float] = None,
    **kwargs,
) -> Dict[str, AttributeValue]:
    """Process input parameters for LLM span attributes."""
    return {
        "llm.input_messages": [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ],
        "llm.model_name": model,
        "llm.temperature": temperature,
    }


def process_output(response: ChatCompletion) -> Dict[str, AttributeValue]:
    """Process LLM response for span attributes."""
    message = response.choices[0].message
    return {
        "llm.output_messages": [{"role": message.role, "content": message.content}],
        "llm.token_count.prompt": response.usage.prompt_tokens if response.usage else 0,
        "llm.token_count.completion": response.usage.completion_tokens if response.usage else 0,
    }


@tracer.llm(
    process_input=process_input,
    process_output=process_output,
)
def invoke_llm(
    messages: List[ChatCompletionMessageParam],
    model: str,
    temperature: Optional[float] = None,
) -> ChatCompletion:
    response = openai_client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
    )
    return response


# Use the decorated function
response = invoke_llm(
    messages=[{"role": "user", "content": "Hello, world!"}], model="gpt-4", temperature=0.7
)
```

<a id="using-context-managers-for-llms"></a>

#### 为 LLM 使用上下文管理器

```python
from opentelemetry.trace import Status, StatusCode


def invoke_llm_manual(messages, model, temperature=None):
    with tracer.start_as_current_span("llm_call", openinference_span_kind="llm") as span:
        # Set input attributes
        span.set_attributes(
            {
                "llm.input_messages": [
                    {"role": msg["role"], "content": msg["content"]} for msg in messages
                ],
                "llm.model_name": model,
                "llm.temperature": temperature,
            }
        )

        try:
            response = openai_client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
            )

            # Set output attributes
            message = response.choices[0].message
            span.set_attributes(
                {
                    "llm.output_messages": [{"role": message.role, "content": message.content}],
                    "llm.token_count.prompt": response.usage.prompt_tokens if response.usage else 0,
                    "llm.token_count.completion": response.usage.completion_tokens
                    if response.usage
                    else 0,
                }
            )
            span.set_status(Status(StatusCode.OK))
            return response

        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR))
            raise
```

<a id="retrievers-and-embeddings"></a>

### 检索器与嵌入

使用 `@tracer.retriever` 和 `@tracer.embedding` 追踪检索和嵌入操作：

```python
@tracer.retriever
def search_documents(query: str, limit: int = 10) -> List[str]:
    # Simulate document retrieval
    return [f"Document {i} matching '{query}'" for i in range(limit)]


@tracer.embedding
def generate_embedding(text: str) -> List[float]:
    # Simulate embedding generation
    return [0.1, 0.2, 0.3, 0.4, 0.5]
```

<a id="additional-features"></a>

### 其他功能

<a id="suppress-tracing"></a>

#### 暂停追踪

使用 `suppress_tracing()` 上下文管理器临时禁用追踪：

```python
from phoenix.otel import suppress_tracing

with suppress_tracing():
    # This function call will not be traced
    result = my_function("input")
```

<a id="adding-context-attributes"></a>

#### 添加上下文属性

使用 `using_attributes()` 为 Span 添加上下文属性：

```python
from phoenix.otel import using_attributes

with using_attributes(session_id="123", user_id="user456"):
    # All spans created within this context will have these attributes
    result = my_function("input")
```

更多详细示例和高级用法见 [Phoenix 追踪文档](https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/instrument-python)。

<a id="api-reference"></a>

## API 参考

```{toctree}
:maxdepth: 2

api/register
api/provider
api/processors
api/exporters
api/settings
```

<a id="external-links"></a>

## 外部链接

- [Phoenix 主文档](https://arize.com/docs/phoenix)
- [Python 参考文档](https://arize-phoenix.readthedocs.io/)
- [GitHub 仓库](https://github.com/Arize-ai/phoenix)
- [PyPI 软件包](https://pypi.org/project/arize-phoenix-otel/)
