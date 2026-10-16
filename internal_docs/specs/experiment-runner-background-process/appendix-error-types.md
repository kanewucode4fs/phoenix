<a id="appendix-error-types-across-llm-provider-sdks"></a>
# 附录：各 LLM 提供商 SDK 的错误类型

本附录说明 Phoenix 用于 LLM 推理的各类 Python SDK 如何呈现限流错误及其他错误。理解这些模式，是为后台实验运行器实现稳健错误检测和重试逻辑的关键。

<a id="overview"></a>
## 概述

现代 LLM SDK 都采用一种共同模式：
- **基于 HTTP 的错误**映射到具体异常类。
- **限流**通过 HTTP 429 或提供商专用代码表示。
- **Retry-After 请求头**提供退避指引。
- **暂时性与永久性错误**决定是否可以重试。

<a id="provider-specific-error-hierarchies"></a>
## 各提供商的错误层级

<a id="openai-sdk-openai"></a>
### OpenAI SDK（`openai`）

**来源**：Stainless 生成的 SDK。

```
OpenAIError (base)
└── APIError
    ├── APIConnectionError
    │   └── APITimeoutError
    ├── APIStatusError
    │   ├── BadRequestError (400)
    │   ├── AuthenticationError (401)
    │   ├── PermissionDeniedError (403)
    │   ├── NotFoundError (404)
    │   ├── ConflictError (409)
    │   ├── UnprocessableEntityError (422)
    │   ├── RateLimitError (429)          ← RATE LIMIT
    │   └── InternalServerError (5xx)
    └── APIResponseValidationError
```

**`APIStatusError` 的关键属性**：
- `status_code: int`：HTTP 状态码。
- `response: httpx.Response`：完整响应对象。
- `request_id: str | None`：来自 `x-request-id` 请求头。
- `body: object | None`：解析后的 JSON 响应体。

**检测模式**：
```python
from openai import RateLimitError

try:
    response = await client.chat.completions.create(...)
except RateLimitError as e:
    # e.status_code == 429
    # e.response.headers.get("retry-after") for backoff
    pass
```

---

<a id="anthropic-sdk-anthropic"></a>
### Anthropic SDK（`anthropic`）

**来源**：Stainless 生成的 SDK。

```
AnthropicError (base)
└── APIError
    ├── APIConnectionError
    │   └── APITimeoutError
    ├── APIStatusError
    │   ├── BadRequestError (400)
    │   ├── AuthenticationError (401)
    │   ├── PermissionDeniedError (403)
    │   ├── NotFoundError (404)
    │   ├── ConflictError (409)
    │   ├── RequestTooLargeError (413)
    │   ├── UnprocessableEntityError (422)
    │   ├── RateLimitError (429)          ← RATE LIMIT
    │   ├── ServiceUnavailableError (503) ← TRANSIENT
    │   ├── DeadlineExceededError (504)   ← TRANSIENT
    │   ├── OverloadedError (529)         ← ANTHROPIC-SPECIFIC RATE LIMIT
    │   └── InternalServerError (5xx)
    └── APIResponseValidationError
```

**Anthropic 特有说明**：
- **HTTP 529（过载）**：Anthropic 在 API 过载时使用这一非标准状态码，应按限流处理，并采用更长退避时间。
- **HTTP 503/504**：应重试的暂时性错误。

**检测模式**：
```python
from anthropic import RateLimitError, OverloadedError

try:
    response = await client.messages.create(...)
except (RateLimitError, OverloadedError) as e:
    # Both indicate capacity constraints
    pass
```

---

<a id="google-genai-sdk-google-genai"></a>
### Google GenAI SDK（`google-genai`）

**来源**：Stainless 生成的 SDK（较新版本）。

```
GeminiNextGenAPIClientError (base)
└── APIError
    ├── APIConnectionError
    │   └── APITimeoutError
    ├── APIStatusError
    │   ├── BadRequestError (400)
    │   ├── AuthenticationError (401)
    │   ├── PermissionDeniedError (403)
    │   ├── NotFoundError (404)
    │   ├── ConflictError (409)
    │   ├── UnprocessableEntityError (422)
    │   ├── RateLimitError (429)          ← RATE LIMIT
    │   └── InternalServerError (5xx)
    └── APIResponseValidationError
```

---

<a id="aws-bedrock-via-botocore"></a>
### 通过 botocore 使用 AWS Bedrock

**来源**：botocore 服务定义。

AWS 使用错误**代码**而非异常类。错误以 `botocore.exceptions.ClientError` 形式出现，响应中包含错误代码。

**限流错误代码**（来自 `botocore/retries/standard.py`）：
```python
_THROTTLED_ERROR_CODES = [
    "Throttling",
    "ThrottlingException",
    "ThrottledException",
    "RequestThrottledException",
    "TooManyRequestsException",
    "ProvisionedThroughputExceededException",
    "TransactionInProgressException",
    "RequestLimitExceeded",
    "BandwidthLimitExceeded",
    "LimitExceededException",
    "RequestThrottled",
    "SlowDown",
    "PriorRequestNotComplete",
    "EC2ThrottledException",
]
```

**Bedrock 特有错误**（来自服务模型）：
| 错误 | 说明 | 是否可重试 |
|-------|-------------|-----------|
| `ThrottlingException` | 请求速率超限 | 是（需退避） |
| `ServiceQuotaExceededException` | 账号配额超限 | 否（需提高配额） |
| `ModelTimeoutException` | 模型推理超时 | 可能 |
| `ModelErrorException` | 模型返回错误 | 否 |
| `ModelNotReadyException` | 模型正在预热 | 是（需退避） |
| `ServiceUnavailableException` | 服务暂时不可用 | 是 |
| `InternalServerException` | 内部错误 | 是 |

**暂时性错误代码**（来自 `botocore/retries/standard.py`）：
```python
_TRANSIENT_ERROR_CODES = [
    "RequestTimeout",
    "RequestTimeoutException",
    "PriorRequestNotComplete",
]

_TRANSIENT_STATUS_CODES = [500, 502, 503, 504]
```

**检测模式**：
```python
from botocore.exceptions import ClientError

try:
    response = await bedrock_client.invoke_model(...)
except ClientError as e:
    error_code = e.response.get("Error", {}).get("Code", "")
    if error_code in ["ThrottlingException", "TooManyRequestsException"]:
        # Rate limited
        pass
    elif error_code == "ServiceQuotaExceededException":
        # Quota exceeded - not retryable
        pass
```

---

<a id="azure-sdk-azure-core"></a>
### Azure SDK（`azure-core`）

**来源**：Azure Core 库。

```
AzureError (base)
├── ServiceRequestError
│   └── ServiceRequestTimeoutError
├── ServiceResponseError
│   └── ServiceResponseTimeoutError
└── HttpResponseError
    ├── DecodeError
    │   └── IncompleteReadError
    ├── ResourceExistsError
    ├── ResourceNotFoundError
    ├── ClientAuthenticationError
    ├── ResourceModifiedError
    ├── ResourceNotModifiedError
    ├── TooManyRedirectsError
    └── ODataV4Error
```

**Azure OpenAI 特有行为**：
Azure OpenAI 包装了 OpenAI SDK，因此错误类型为 `openai.RateLimitError`，但可能包含 Azure 专用请求头。

**检测模式**：
```python
from azure.core.exceptions import HttpResponseError

try:
    response = await client.complete(...)
except HttpResponseError as e:
    if e.status_code == 429:
        # Rate limited
        pass
```

---

<a id="retry-after-header-handling"></a>
## Retry-After 请求头处理

所有 Stainless 生成的 SDK（OpenAI、Anthropic、Google GenAI）都实现了相同的 `retry-after` 解析逻辑：

```python
def _parse_retry_after_header(response_headers):
    # 1. Try non-standard `retry-after-ms` header (milliseconds)
    retry_ms = response_headers.get("retry-after-ms")
    if retry_ms:
        return float(retry_ms) / 1000
    
    # 2. Try `retry-after` as seconds (integer or float)
    retry_header = response_headers.get("retry-after")
    try:
        return float(retry_header)
    except (TypeError, ValueError):
        pass
    
    # 3. Try `retry-after` as HTTP date
    retry_date = email.utils.parsedate_tz(retry_header)
    if retry_date:
        return email.utils.mktime_tz(retry_date) - time.time()
    
    return None
```

**SDK 行为**：
- `retry-after` 在 0–60 秒之间时，SDK 遵循该值。
- 否则采用指数退避。
- 默认最大退避时间通常为 20–60 秒。

---

<a id="error-classification-matrix"></a>
## 错误分类矩阵

| 提供商 | 限流 | 暂时性错误（重试） | 永久性错误（中止） |
|----------|------------|-------------------|-------------------|
| **OpenAI** | `RateLimitError` (429) | `InternalServerError` (5xx), `APITimeoutError` | `BadRequestError`, `AuthenticationError`, `NotFoundError` |
| **Anthropic** | `RateLimitError` (429), `OverloadedError` (529) | `ServiceUnavailableError` (503), `DeadlineExceededError` (504), `InternalServerError` | `BadRequestError`, `AuthenticationError`, `NotFoundError` |
| **Google GenAI** | `RateLimitError` (429) | `InternalServerError` | `BadRequestError`, `AuthenticationError`, `NotFoundError` |
| **AWS Bedrock** | `ThrottlingException`, `TooManyRequestsException` | `ServiceUnavailableException`, `ModelNotReadyException`, 5xx | `ValidationException`, `AccessDeniedException`, `ModelErrorException` |
| **Azure** | HTTP 429 | `ServiceResponseError`, HTTP 5xx | `ClientAuthenticationError`, `ResourceNotFoundError` |

---

<a id="implementation-recommendations"></a>
## 实施建议

<a id="1-generic-rate-limit-detection"></a>
### 1. 通用限流检测

```python
def is_rate_limit_error(e: Exception) -> bool:
    """Detect rate limiting across all providers."""
    # Check exception class name
    error_name = type(e).__name__.lower()
    if "ratelimit" in error_name or "throttl" in error_name:
        return True

    # Check for Anthropic OverloadedError
    if "overloaded" in error_name:
        return True

    # Check HTTP status code
    status_code = getattr(e, "status_code", None)
    if status_code == 429:
        return True

    # Check botocore ClientError
    if hasattr(e, "response"):
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in BOTO_THROTTLE_CODES:
            return True

    return False
```

<a id="2-generic-transient-error-detection"></a>
### 2. 通用暂时性错误检测

```python
def is_transient_error(e: Exception) -> bool:
    """Detect transient errors that should be retried."""
    # Timeouts are always transient
    if "timeout" in type(e).__name__.lower():
        return True

    # Connection errors are transient
    if "connection" in type(e).__name__.lower():
        return True

    # 5xx errors are typically transient
    status_code = getattr(e, "status_code", None)
    if status_code and 500 <= status_code < 600:
        return True

    # Anthropic 529 (Overloaded)
    if status_code == 529:
        return True

    return False
```

<a id="3-extract-retry-after-duration"></a>
### 3. 提取 Retry-After 时长

```python
def get_retry_after_seconds(e: Exception) -> float | None:
    """Extract retry-after duration from error response."""
    response = getattr(e, "response", None)
    if response is None:
        return None

    headers = getattr(response, "headers", {})

    # Try retry-after-ms first
    if retry_ms := headers.get("retry-after-ms"):
        try:
            return float(retry_ms) / 1000
        except ValueError:
            pass

    # Try retry-after
    if retry_after := headers.get("retry-after"):
        try:
            return float(retry_after)
        except ValueError:
            pass

    return None
```

<a id="4-exponential-backoff"></a>
### 4. 指数退避

未提供 `retry-after` 请求头时：

```python
def calculate_backoff(attempt: int, base: float = 1.0, max_backoff: float = 60.0) -> float:
    """Calculate exponential backoff with jitter."""
    import random

    delay = min(base * (2**attempt), max_backoff)
    jitter = random.uniform(0, delay * 0.25)
    return delay + jitter
```

---

<a id="phoenix-integration"></a>
## Phoenix 集成

Phoenix 当前使用 `PlaygroundRateLimiter` 类：
1. 接受提供商专用的 `rate_limit_error` 类。
2. 使用自适应令牌桶，最多重试 3 次。
3. 通过锁协调并发请求。

对于后台实验运行器，我们应该：
1. 使用上述通用检测函数以覆盖更多情况。
2. 存在 `retry-after` 请求头时提取其值。
3. 按实验实施限流，而非全局限流。
4. 区分限流（退避后重试）与永久性错误（中止任务）。

---

<a id="references"></a>
## 参考资料

- [OpenAI Python SDK - `_exceptions.py`](https://github.com/openai/openai-python/blob/722d3fffb82e9150a16da01e432b70d126ca5254/src/openai/_exceptions.py)
- [Anthropic Python SDK - `_exceptions.py`](https://github.com/anthropics/anthropic-sdk-python/blob/9b5ab24ba17bcd5e762e5a5fd69bb3c17b100aaa/src/anthropic/_exceptions.py)
- [Google GenAI SDK - `_exceptions.py`](https://github.com/googleapis/python-genai/blob/8d7c74d4579408714f4c9a5cc40d4772e670fae5/google/genai/_interactions/_exceptions.py)
- [botocore - `retries/standard.py`](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/retries/standard.py)
- [Azure Core - `exceptions.py`](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/core/azure-core/azure/core/exceptions.py)
