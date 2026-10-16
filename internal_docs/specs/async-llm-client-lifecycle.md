<a id="async-llm-client-lifecycle-management"></a>
# 异步 LLM 客户端生命周期管理

<a id="overview"></a>
## 概述

本文说明在 Phoenix Playground 基础设施的全部 LLM 提供商客户端中，采用统一异步上下文管理器模式的理由。设计确保正确管理 HTTP 连接生命周期，并提供不依赖底层 SDK 的一致接口。

<a id="what-changed"></a>
## 变化

| 提供商 | 之前 | 之后 | 影响 |
|----------|--------|-------|--------|
| **AWS Bedrock** | boto3（阻塞 I/O） | aioboto3（异步 I/O） | **修复事件循环阻塞** |
| OpenAI | 每请求新建客户端 | 每请求新建客户端 | 无变化 |
| Azure OpenAI | 每请求新建客户端 | 每请求新建客户端 | 无变化 |
| Anthropic | 每请求新建客户端 | 每请求新建客户端 | 无变化 |
| Google GenAI | 每请求新建客户端 | 每请求新建客户端 | 无变化 |

**关键认识：** 所有提供商原本已逐请求创建新客户端，因此原本已有每请求约 20–250ms 的连接开销。本 PR 不为非 Bedrock 提供商引入新开销，只修复 Bedrock 阻塞行为。

统一工厂模式通过显式异步上下文管理器，将已有新客户端模式规范化，确保全部提供商一致清理资源。

<a id="problem-statement"></a>
## 问题说明

Phoenix Playground 支持 OpenAI、Azure OpenAI、Anthropic、Google GenAI、AWS Bedrock 等提供商，其 SDK 生命周期模式各不相同：

- **OpenAI/Azure OpenAI/Anthropic**：可同步创建，但持有的 HTTP 连接应显式关闭。
- **AWS Bedrock（boto3）**：同步客户端采用阻塞 I/O，会冻结异步事件循环。
- **Google GenAI**：同步和异步客户端分开管理生命周期。

说明：Azure OpenAI 使用相同 `AsyncOpenAI` 客户端，通过自定义 `base_url` 指向 Azure 端点，无需独立 `AsyncAzureOpenAI` 类。

<a id="why-boto3-blocks-the-event-loop"></a>
### 为什么 boto3 阻塞事件循环

boto3 流式处理中使用 `yield` 不会使其异步。`yield` 创建用于增量返回数据的生成器，但不改变底层 I/O：

```python
# boto3 (BLOCKING)
response = boto3_client.converse_stream(...)  # ← Blocks until server responds
for event in response["stream"]:  # ← Each iteration blocks waiting for next chunk
    yield event  # ← yield returns control, but NEXT iteration blocks again
```

每次网络读取都是**阻塞 socket 操作**。等待期间 asyncio 事件循环冻结，其他协程无法执行。

```
boto3:    [BLOCK 50ms][yield][BLOCK 80ms][yield][BLOCK 60ms]...
                ↑                 ↑                 ↑
           Event loop        Event loop        Event loop
           frozen            frozen            frozen

aioboto3:  [await 50ms]      [await 80ms]      [await 60ms]...
                ↓                 ↓                 ↓
           Other requests    Other requests    Other requests
           can execute       can execute       can execute
```

<a id="practical-impact"></a>
### 实际影响

**影响较小、可接受阻塞的场景：**
- 单用户本地开发。
- 并发 Bedrock 流式请求少于 5 个的生产环境。
- 只运行 Bedrock、没有其他异步工作负载的专用部署。

**影响较大、建议 aioboto3 的场景：**
- 同时 10 个以上 Bedrock 流。
- 混合异步负载，如共享事件循环的数据库查询和其他 API 调用。
- 重视尾延迟的敏感应用。

| 场景 | boto3 影响 |
|----------|--------------|
| 单流，约 100 token | 总阻塞约 3–5 秒，用户本来也在等待 |
| 5 个并发流 | 每流延迟约增加 20–50% |
| 10 个以上并发流 | 明显串行化，延迟叠加 |
| 混合负载 | Bedrock I/O 期间，数据库和 HTTP 等其他异步操作被饿死 |

<a id="consequences-without-proper-lifecycle-management"></a>
### 生命周期管理不当的后果

- 负载下连接池耗尽。
- 长期运行应用资源泄漏。
- 连接池耗尽导致 `APITimeoutError`，流式场景尤其明显。

<a id="why-aioboto3-requires-async-context-managers"></a>
### 为什么 aioboto3 要求异步上下文管理器

OpenAI/Anthropic SDK 可同步创建客户端，之后选择关闭；aioboto3 的要求更严格，并推动了本设计：

1. **异步创建客户端**：aioboto3 的 `session.client()` 返回 [`ClientCreatorContext`](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/session.py#L26-L36)，而非客户端本身。只有进入异步上下文管理器（`async with`）后，实际客户端才可用，因为凭证解析、端点发现和 HTTP 会话配置都是[异步操作](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/session.py#L133-L259)。

2. **aiohttp 需显式清理**：aiohttp 的 [`__del__`](https://github.com/aio-libs/aiohttp/blob/957d5ba18224b10d428f3ed7fe450ffc2c2978ca/aiohttp/client.py#L421-L431) 对未关闭会话仅发出 `ResourceWarning`，不实际关闭连接。未调用 [`__aexit__`](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/httpsession.py#L109-L115) 会保留 TCP 连接。连接器[默认上限为 100](https://github.com/aio-libs/aiohttp/blob/957d5ba18224b10d428f3ed7fe450ffc2c2978ca/aiohttp/connector.py#L254)，未关闭客户端最终导致新请求阻塞等待可用连接并超时。

3. **Session 与客户端生命周期**：boto3 可[无限期持有客户端](https://github.com/boto/boto3/blob/43f6f80eb6c93d085b98a6d2eba74fe498e460f5/boto3/session.py#L337-L339)。aioboto3 中，客户端 HTTP 会话[绑定上下文管理器作用域](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/client.py#L639-L644)，退出时[设置 `_sessions = None`](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/httpsession.py#L114-L115)，导致后续 API 调用失败。

这些约束意味着不能简单包装 aioboto3 来套用 OpenAI/Anthropic 模式。因此，我们让所有提供商都采用 aioboto3 的上下文管理器模式，以确保一致且正确的资源清理。

<a id="design-decision-unified-factory-pattern"></a>
## 设计决策：统一工厂模式

所有提供商都使用返回异步上下文管理器的工厂可调用对象。工厂通过闭包捕获所需配置，逐请求创建新客户端：

```python
ClientT = TypeVar("ClientT")

class PlaygroundClient(ABC, Generic[ClientT]):
    _client_factory: Callable[[], AsyncContextManager[ClientT]]
    
    async def chat_completion_create(self, ...):
        async with self._client_factory() as client:  # client is typed as ClientT
            # Provider-specific logic using client
            ...

# Subclasses specify their client type
class OpenAICompatibleClient(PlaygroundClient["AsyncOpenAI"]): ...
class AnthropicClient(PlaygroundClient["AsyncAnthropic"]): ...
class GoogleClient(PlaygroundClient["GoogleAsyncClient"]): ...
class BedrockClient(PlaygroundClient["BedrockRuntimeClient"]): ...
```

<a id="factory-implementations-by-provider"></a>
### 各提供商工厂实现

| 提供商 | 工厂实现 |
|----------|------------------------|
| OpenAI | `lambda: AsyncOpenAI(api_key=api_key, ...)` |
| Azure OpenAI | `lambda: AsyncOpenAI(api_key=api_key, base_url=azure_base_url, ...)` |
| Anthropic | `lambda: AsyncAnthropic(api_key=api_key, ...)` |
| Google GenAI | `lambda: Client(api_key=api_key).aio` |
| AWS Bedrock | `lambda: session.client("bedrock-runtime", ...)` |

说明：Azure OpenAI 复用 `AsyncOpenAI`，使用自定义 `base_url`（例如 `https://{endpoint}/openai/v1/`）。这比已弃用 `AsyncAzureOpenAI` 更简洁，并兼容作为 `api_key` 传入的 Azure AD token 提供器，要求 openai>=1.106.0。

<a id="consumption-pattern"></a>
### 使用模式

全部提供商采用相同方式：

```python
async def chat_completion_create(self, messages, tools, **params):
    async with self._client_factory() as client:
        # For OpenAI/Azure/Anthropic: Wrap httpx client for instrumentation
        client._client = _HttpxClient(client._client, self._attributes)

        # Provider-specific API calls
        response = await client.chat.completions.create(...)  # OpenAI / Azure OpenAI
        response = await client.messages.stream(...)  # Anthropic
        response = await client.models.generate_content_stream(...)  # Google
        response = await client.converse_stream(...)  # Bedrock
```

<a id="benefits"></a>
### 优点

| 方面 | 新客户端模式 |
|--------|---------------------|
| **一致性** | 全部提供商相同 |
| **资源清理** | 上下文管理器自动完成 |
| **凭证刷新** | 支持 IAM 角色，见[附录：凭证刷新](#appendix-aws-credential-refresh) |
| **简单性** | 无需包装类 |
| **插桩** | 逐请求即时应用 |
| **类型安全** | 泛型基类保证 `client` 类型正确 |

<a id="alternative-considered-thread-pool-workaround"></a>
### 考虑过的替代：线程池变通

如果 aioboto3 不可行，可在线程池运行 boto3 以释放事件循环：

```python
from starlette.concurrency import run_in_threadpool

# Runs boto3 in thread, doesn't block event loop
await run_in_threadpool(boto3_client.converse_stream, ...)
```

**为何仍选择 aioboto3：**

| 方面 | 线程池 + boto3 | aioboto3 |
|--------|---------------------|----------|
| 事件循环阻塞 | 否，在线程运行 | 否，真正异步 |
| 线程消耗 | 每并发请求一个线程 | 无 |
| 复杂度 | 同步异步混合 | 纯异步 |
| 扩展性 | 受线程池大小限制 | 随异步事件循环扩展 |

对多数用户，boto3 阻塞可以接受，但 aioboto3 是异步服务端正确的架构选择。

<a id="technical-appendix-sdk-client-lifecycle-details"></a>
## 技术附录：SDK 客户端生命周期详情

本节提供各 SDK 异步上下文管理器实现的详细代码引用。

### OpenAI SDK

OpenAI Python SDK 包装 httpx，实现异步上下文管理器协议。

**上下文管理器实现：**
[openai-python/src/openai/_base_client.py#L1428-L1437](https://github.com/openai/openai-python/blob/d3e632171c7842abf97b26379f564531d80ad096/src/openai/_base_client.py#L1428-L1437)

```python
async def __aenter__(self: _T) -> _T:
    return self


async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    exc_tb: TracebackType | None,
) -> None:
    await self.close()
```

**关闭方法（释放 httpx 连接）：**
[openai-python/src/openai/_base_client.py#L1421-L1426](https://github.com/openai/openai-python/blob/d3e632171c7842abf97b26379f564531d80ad096/src/openai/_base_client.py#L1421-L1426)

```python
async def close(self) -> None:
    """Close the underlying HTTPX client.

    The client will *not* be usable after this.
    """
    await self._client.aclose()
```

### Anthropic SDK

Anthropic SDK 与 OpenAI 共享相同基类架构，两者都使用 httpx。

**上下文管理器实现：**
[anthropic-sdk-python/src/anthropic/_base_client.py#L1533-L1542](https://github.com/anthropics/anthropic-sdk-python/blob/2eb941512885bdea844cb46e3f93b60ffa51973b/src/anthropic/_base_client.py#L1533-L1542)

```python
async def __aenter__(self: _T) -> _T:
    return self


async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    exc_tb: TracebackType | None,
) -> None:
    await self.close()
```

**关闭方法：**
[anthropic-sdk-python/src/anthropic/_base_client.py#L1526-L1531](https://github.com/anthropics/anthropic-sdk-python/blob/2eb941512885bdea844cb46e3f93b60ffa51973b/src/anthropic/_base_client.py#L1526-L1531)

```python
async def close(self) -> None:
    """Close the underlying HTTPX client.

    The client will *not* be usable after this.
    """
    await self._client.aclose()
```

### Google GenAI SDK

Google GenAI SDK 提供独立同步和异步客户端，并显式管理生命周期。

**异步上下文管理器：**
[python-genai/google/genai/client.py#L248-L257](https://github.com/googleapis/python-genai/blob/48f8256202a9ea3abfb7790fa80fcbf68e541131/google/genai/client.py#L248-L257)

```python
async def __aenter__(self) -> "AsyncClient":
    return self


async def __aexit__(
    self,
    exc_type: Optional[Exception],
    exc_value: Optional[Exception],
    traceback: Optional[TracebackType],
) -> None:
    await self.aclose()
```

**异步关闭方法：**
[python-genai/google/genai/client.py#L218-L246](https://github.com/googleapis/python-genai/blob/48f8256202a9ea3abfb7790fa80fcbf68e541131/google/genai/client.py#L218-L246)

```python
async def aclose(self) -> None:
    """Closes the async client explicitly.

    However, it doesn't close the sync client, which can be closed using the
    Client.close() method or using the context manager.
    ...
    """
    await self._api_client.aclose()

    if self._has_nextgen_client:
        await self._nextgen_client.close()
```

### aioboto3/aiobotocore (AWS Bedrock)

aioboto3 的客户端创建是异步的，并涉及凭证解析，因此需要本质不同的模式。

**aioboto3 Session（继承 boto3，替换为异步 botocore）：**
[aioboto3/aioboto3/session.py#L22-L58](https://github.com/terrycain/aioboto3/blob/37216db0083e28511c4d82931855f8af2b1b102b/aioboto3/session.py#L22-L58)

```python
class Session(boto3.session.Session):
    """
    A session stores configuration state and allows you to create service
    clients and resources.
    """
    def __init__(self, ...):
        if botocore_session is not None:
            self._session = botocore_session
        else:
            # Create a new default session
            self._session = aiobotocore.session.get_session()
```

**ClientCreatorContext（包装异步客户端创建）：**
[aiobotocore/aiobotocore/session.py#L26-L36](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/session.py#L26-L36)

```python
class ClientCreatorContext:
    def __init__(self, coro):
        self._coro = coro
        self._client = None

    async def __aenter__(self) -> AioBaseClient:
        self._client = await self._coro
        return await self._client.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)
```

**AioBaseClient 上下文管理器（管理 HTTP 会话）：**
[aiobotocore/aiobotocore/client.py#L639-L644](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/client.py#L639-L644)

```python
async def __aenter__(self):
    await self._endpoint.http_session.__aenter__()
    return self


async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self._endpoint.http_session.__aexit__(exc_type, exc_val, exc_tb)
```

**HTTP 会话生命周期（清理 aiohttp 连接器）：**
[aiobotocore/aiobotocore/httpsession.py#L104-L115](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/httpsession.py#L104-L115)

```python
async def __aenter__(self):
    assert self._sessions is None
    self._sessions = {}
    return self


async def __aexit__(self, exc_type, exc_val, exc_tb):
    assert self._sessions is not None, "Session was never entered"
    self._sessions.clear()
    await self._exit_stack.aclose()
    # Make _sessions unusable once context is exited
    self._sessions = None
```

<a id="why-aioboto3-differs-from-openaianthropic"></a>
### aioboto3 为什么不同于 OpenAI/Anthropic

| 方面 | OpenAI/Anthropic | aioboto3 |
|--------|------------------|----------|
| 创建客户端 | 同步 | 异步，包括凭证解析等 |
| HTTP 库 | httpx | aiohttp |
| 连接管理 | 内部、惰性 | 显式，通过上下文管理器 |
| 凭证处理 | 静态 API 密钥 | 可过期，如 IAM 角色、STS token |

aioboto3 强制使用上下文管理器，原因是：

1. **异步创建客户端**：凭证解析、端点发现和连接建立是异步操作，不能在 `__init__` 中完成。

2. **aiohttp 需显式清理**：httpx 可在垃圾回收时清理，而 aiohttp 连接池必须显式关闭。

3. **凭证刷新**：对于 IAM 角色，新客户端可获取刷新后的凭证，见[附录：凭证刷新](#appendix-aws-credential-refresh)。

<a id="boto3-vs-aiobotocore-code-level-comparison"></a>
### boto3 与 aiobotocore：代码级比较

**botocore（同步）——阻塞 socket 读取：**
[botocore/response.py#L92-L110](https://github.com/boto/botocore/blob/82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26/botocore/response.py#L92-L110)

```python
def read(self, amt=None):
    """Read at most amt bytes from the stream."""
    try:
        chunk = self._raw_stream.read(amt)  # ← Blocking urllib3 socket read
    except URLLib3ReadTimeoutError as e:
        raise ReadTimeoutError(endpoint_url=e.url, error=e)
    # ...
    return chunk
```

`self._raw_stream.read()` 会阻塞整个 Python 线程，因此也阻塞 asyncio 事件循环，直到 socket 数据到达。

**boto3 Session.client()——直接返回客户端：**
[boto3/session.py#L337-L339](https://github.com/boto/boto3/blob/43f6f80eb6c93d085b98a6d2eba74fe498e460f5/boto3/session.py#L337-L339)

```python
return self._session.create_client(service_name, **create_client_kwargs)
```

boto3 的 `Session.client()` 立即同步返回客户端。底层 `botocore.session.create_client()` 创建使用阻塞 urllib3 连接的同步客户端。

**aiobotocore Session.create_client()——包装在异步上下文管理器中：**
[aiobotocore/session.py#L129-L130](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/session.py#L129-L130)

```python
def create_client(self, *args, **kwargs):
    return ClientCreatorContext(self._create_client(*args, **kwargs))
```

aiobotocore 将异步客户端创建包装在 `ClientCreatorContext` 中，要求使用 `async with`。实际创建在 `_create_client()` 中异步执行，位于 133–259 行，包括异步凭证解析。

**aiobotocore（异步）——非阻塞 await：**
[aiobotocore/response.py#L52-L75](https://github.com/aio-libs/aiobotocore/blob/93af53a8cd8faead9747561abcff4f6631afa732/aiobotocore/response.py#L52-L75)

```python
async def read(self, amt=None):
    """Read at most amt bytes from the stream."""
    try:
        chunk = await self.__wrapped__.content.read(  # ← Non-blocking aiohttp read
            amt if amt is not None else -1
        )
    except asyncio.TimeoutError as e:
        raise AioReadTimeoutError(endpoint_url=self.__wrapped__.url, error=e)
    # ...
    return chunk
```

`await` 将控制权交回事件循环。底层 aiohttp 使用 asyncio future：

[aiohttp/streams.py#L342-L361](https://github.com/aio-libs/aiohttp/blob/957d5ba18224b10d428f3ed7fe450ffc2c2978ca/aiohttp/streams.py#L342-L361)

```python
async def _wait(self, func_name: str) -> None:
    # ...
    waiter = self._waiter = self._loop.create_future()  # ← Create asyncio future
    try:
        with self._timer:
            await waiter  # ← Yield to event loop until data arrives
    finally:
        self._waiter = None
```

[aiohttp/streams.py#L402-L428](https://github.com/aio-libs/aiohttp/blob/957d5ba18224b10d428f3ed7fe450ffc2c2978ca/aiohttp/streams.py#L402-L428)

```python
async def read(self, n: int = -1) -> bytes:
    # ...
    while not self._buffer and not self._eof:
        await self._wait("read")  # ← Suspends coroutine, other tasks can run
    return self._read_nowait(n)
```

关键差别：`await self._wait("read")` 挂起协程并将控制权返回事件循环。socket 回调收到数据后完成 future，协程再恢复。等待期间，处理其他请求的协程可以执行。

<a id="appendix-aws-credential-refresh"></a>
## 附录：AWS 凭证刷新

AWS 凭证有两种形式，刷新行为不同：

<a id="decision-logic"></a>
### 判断逻辑

判断位于 [`botocore/session.py#L961-L986`](https://github.com/boto/botocore/blob/82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26/botocore/session.py#L961-L986)：

```python
if aws_access_key_id is not None and aws_secret_access_key is not None:
    # Explicit credentials → static Credentials (no refresh)
    credentials = botocore.credentials.Credentials(
        access_key=aws_access_key_id,
        secret_key=aws_secret_access_key,
        token=aws_session_token,
    )
else:
    # No explicit creds → use credential resolver chain
    # This may return RefreshableCredentials for IAM roles
    credentials = self.get_credentials()
```

<a id="static-credentials-explicit"></a>
### 静态凭证（显式）

向会话传入显式凭证时：

```python
session = aioboto3.Session(
    aws_access_key_id="AKIA...",
    aws_secret_access_key="...",
    aws_session_token="...",  # Optional, for temporary credentials
)
```

使用 botocore 的 [`Credentials`](https://github.com/boto/botocore/blob/82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26/botocore/credentials.py#L340-L355) 类，仅存储这些值：

```python
class Credentials:
    """Holds the credentials needed to authenticate requests."""
    def __init__(self, access_key, secret_key, token=None, ...):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token
```

**不会自动刷新。** 凭证过期后，API 调用以 `ExpiredTokenException` 失败。

<a id="refreshable-credentials-iam-roles"></a>
### 可刷新凭证（IAM 角色）

对于 IAM 角色，包括 EC2 实例配置文件、ECS 任务角色和 Lambda 执行角色，botocore 使用 [`RefreshableCredentials`](https://github.com/boto/botocore/blob/82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26/botocore/credentials.py#L388-L439)：

```python
class RefreshableCredentials(Credentials):
    """Knows how to refresh itself."""
    def __init__(self, ..., expiry_time, refresh_using, ...):
        self._refresh_using = refresh_using  # Callback to fetch new credentials
        self._expiry_time = expiry_time
        self._advisory_refresh_timeout = 15 * 60  # 15 min before expiry
        self._mandatory_refresh_timeout = 10 * 60  # 10 min before expiry
```

每次访问凭证时，都会调用 [`_refresh()`](https://github.com/boto/botocore/blob/82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26/botocore/credentials.py#L566-L594) 方法：

```python
def _refresh(self):
    if not self.refresh_needed(self._advisory_refresh_timeout):
        return  # Credentials still valid, no refresh needed
    
    # Acquire lock and refresh
    if self._refresh_lock.acquire(False):
        try:
            self._protected_refresh(is_mandatory=...)
        finally:
            self._refresh_lock.release()
```

<a id="implications-for-phoenix"></a>
### 对 Phoenix 的影响

Phoenix 自定义提供商配置存储数据库中的**显式凭证**，属于静态值，不会自动刷新。用户配置的临时 STS token 过期后，必须手动更新存储凭证。

使用 **IAM 角色**的部署，例如在 EC2/ECS 上使用实例配置文件运行 Phoenix，从环境解析凭证并自动刷新。但自定义提供商的 `without_env_vars("AWS_*")` 隔离意味着 IAM 角色凭证仅用于**内置提供商**，不用于自定义配置。

<a id="references"></a>
## 参考资料

- [boto3](https://github.com/boto/boto3) @ `43f6f80eb6c93d085b98a6d2eba74fe498e460f5`
- [botocore](https://github.com/boto/botocore) @ `82f7c427d516c22db1c7cf5c6cf3d48ad2e50e26`
- [OpenAI Python SDK](https://github.com/openai/openai-python) @ `d3e632171c7842abf97b26379f564531d80ad096`
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) @ `2eb941512885bdea844cb46e3f93b60ffa51973b`
- [Google GenAI Python SDK](https://github.com/googleapis/python-genai) @ `48f8256202a9ea3abfb7790fa80fcbf68e541131`
- [aioboto3](https://github.com/terrycain/aioboto3) @ `37216db0083e28511c4d82931855f8af2b1b102b`
- [aiobotocore](https://github.com/aio-libs/aiobotocore) @ `93af53a8cd8faead9747561abcff4f6631afa732`
- [aiohttp](https://github.com/aio-libs/aiohttp) @ `957d5ba18224b10d428f3ed7fe450ffc2c2978ca`
