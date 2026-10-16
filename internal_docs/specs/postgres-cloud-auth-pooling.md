<a id="postgresql-cloud-authentication-and-connection-pooling"></a>

# PostgreSQL 云身份验证与连接池

本文为使用 Azure Database for PostgreSQL（采用 Microsoft Entra / 托管标识身份验证）和 AWS RDS for PostgreSQL（采用 IAM 身份验证）的开发者提供参考，说明云端签发的访问令牌如何经过 PostgreSQL 协议传递、相关 SDK 如何获取令牌，以及 SQLAlchemy 连接池如何与这些机制交互。

本文源于一个简单的问题：*如果访问令牌每 N 分钟过期一次，该怎样保证数据库连接正常工作？* 答案涉及几个相互作用的层次——PostgreSQL 线协议、云 SDK 的令牌缓存和 SQLAlchemy 连接池。人们对这些层次如何交互的一些直觉假设并不成立。本文逐层说明实际行为，帮助开发者一开始就把配置放在正确的位置。

每项非显而易见的论断都引用一手来源。推断和未经验证的论断均有明确标注。

<a id="key-facts-at-a-glance"></a>

## 关键事实速览

1. **PostgreSQL 仅在连接启动握手期间对客户端进行一次身份验证。** 在整个会话生命周期中，它不会重新验证凭证。这是 PostgreSQL 线协议的特性，同样适用于原生 PostgreSQL、Azure Database for PostgreSQL 和 AWS RDS for PostgreSQL。
2. **已经建立的 PostgreSQL 连接会在用于验证身份的访问令牌过期后继续存在。** Microsoft 和 AWS 均有明确说明。令牌过期只限制*建立新连接*，不限制既有会话的生命周期。
3. **因此，将 `pool_recycle` 对齐“令牌有效期”并不是保证正确性的必要条件。** 它的合理作用只是管理连接年龄。让它紧贴令牌有效窗口，只会造成无益的连接更替。
4. **Python 的 `azure-identity` 默认在内存中缓存令牌**，适用于 `ManagedIdentityCredential` 和其他云托管凭证。因此，通常无需在应用层缓存 Azure 令牌。
5. **AWS RDS IAM 令牌完全在本地生成**——`boto3.generate_db_auth_token()` 执行 SigV4 签名，并不发起网络调用。每个连接生成一次令牌只需微秒级时间，完全不需要缓存层。
6. **SQLAlchemy 的 `pool_pre_ping`** 在每次从池中取出连接时执行方言的 `do_ping`（asyncpg/PG 方言使用 `SELECT 1`），但会跳过新建连接。使用 `NullPool` 时，每次取用都会创建新连接，因此完全不会执行 ping。

下文将逐项展开并给出引用。

<a id="postgresql-protocol-authentication-semantics"></a>

## PostgreSQL 协议的身份验证语义

PostgreSQL 仅在开启连接的启动消息交换期间对客户端进行一次身份验证。协议没有在会话中途重新验证凭证的机制。

> “要开始会话，前端先连接服务器并发送启动消息。[…] 随后服务器发送适当的身份验证请求消息，前端必须回复适当的身份验证响应消息（例如密码）。除 GSSAPI、SSPI 和 SASL 外，所有身份验证方法都至多包含一次请求和一次响应。[…] 前端收到 AuthenticationOk 后，连接便进入正常查询处理阶段。”
>
> — [PostgreSQL 文档，54.2 消息流程](https://www.postgresql.org/docs/current/protocol-flow.html)

本文其他结论都基于这一事实。它同样适用于原生 PostgreSQL、Azure Database for PostgreSQL 和 AWS RDS for PostgreSQL——无论客户端如何生成凭证，这三者的服务端都实现相同的 PostgreSQL 线协议。从服务端看，云端签发的令牌就是密码；服务端在启动握手期间检查一次，此后不再使用它。

<a id="azure-database-for-postgresql-with-managed-identity"></a>

## 使用托管标识的 Azure Database for PostgreSQL

<a id="end-to-end-flow"></a>

### 端到端流程

当 Azure 上运行的客户端（例如 App Service、AKS pod，或使用系统分配托管标识的 VM）希望通过 Entra 身份验证连接 Azure Database for PostgreSQL 时：

1. 客户端向 `azure-identity` 请求作用域为 `https://ossrdbms-aad.database.windows.net/.default` 的访问令牌。在 Python 中通常使用 `DefaultAzureCredential().get_token(scope)`。
2. `azure-identity` 解析凭证链。在已部署的 Azure 环境中，通常最终使用 `ManagedIdentityCredential`，它会向 Azure 实例元数据服务（IMDS）的 `http://169.254.169.254/metadata/identity/oauth2/token` 发起 HTTP 请求。
3. IMDS 返回包含 JWT 和 `expires_on` Unix 时间戳的 `AccessToken`。SDK 将其缓存在内存中。
4. 客户端以 JWT 作为密码参数打开 PostgreSQL 连接（例如 `asyncpg.connect(...)`）。PG 服务端在启动握手期间通过 Microsoft Entra 验证 JWT。
5. 此后，该连接就是普通的 PostgreSQL 会话，不再使用令牌。

<a id="token-lifetimes"></a>

### 令牌有效期

Microsoft 官方文档区分 Azure PostgreSQL 作用域的两类令牌：

> “用户令牌的有效期最长为 1 小时。系统分配托管标识的令牌有效期最长为 24 小时。”
>
> — [Azure Database for PostgreSQL 的 Microsoft Entra 身份验证](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-azure-ad-authentication)

常被引用的“60 分钟”适用于用户令牌路径。使用系统分配托管标识的服务端和 AKS 工作负载所获取的令牌，有效期最长为 **24 小时**。文档规定的上限分别为 1 小时（用户令牌）和 24 小时（系统分配托管标识令牌）。

Microsoft Entra **不支持**为托管标识服务主体配置令牌有效期策略，因此应将托管标识令牌的有效期视为由服务控制：

> “不支持为托管标识服务主体配置令牌有效期。”
>
> — [Microsoft 标识平台中的可配置令牌有效期](https://learn.microsoft.com/en-us/entra/identity-platform/configurable-token-lifetimes)

<a id="server-behavior-on-token-expiry"></a>

### 令牌过期时的服务端行为

结合 Microsoft 官方产品文档和协议语义可知，令牌有效性在登录/建立连接时检查，而不会对已经建立的会话进行定期复查：

> “被删除的 Microsoft Entra 用户仍可登录，直到令牌过期（自令牌签发起最长 60 分钟）。”
>
> — [Azure Database for PostgreSQL 的 Microsoft Entra 身份验证](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-azure-ad-authentication)

此外，Microsoft 针对 Flexible Server 的支持指导指出，没有可在访问令牌过期时终止会话的内置参数（参见“来源”中链接的 Microsoft Q&A 讨论）。

上述引用从撤销用户的角度描述行为——关键细节是，撤销后仍能继续访问，唯一限制是“直到令牌过期”，这确认令牌仅在*新登录发生的时刻*起作用。既有会话仍会继续存在。

<a id="token-caching-in-azure-identity-for-python"></a>

### Python azure-identity 的令牌缓存

`azure-identity` 默认为 `ManagedIdentityCredential`（同步和异步版本）及大多数其他云托管凭证提供内存令牌缓存。应用代码反复调用 `get_token` 时，会收到缓存令牌，直到令牌临近过期，SDK 才会透明地刷新它。

> “令牌缓存是 Azure Identity 库提供的一项功能，使应用可以在内存中缓存令牌（默认），或在磁盘上缓存令牌（需主动启用）。[…] 内存缓存默认激活。”
>
> — [azure-identity Python README——令牌缓存](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#token-caching)

`uv.lock` 锁定版本的 TOKEN_CACHING.md 文档明确将 `ManagedIdentityCredential` 列入默认在内存中缓存令牌的凭证：

> “以下凭证支持内存令牌缓存：AuthorizationCodeCredential、AzurePipelinesCredential、ClientAssertionCredential、CertificateCredential、ClientSecretCredential、DeviceCodeCredential、EnvironmentCredential、InteractiveBrowserCredential、**ManagedIdentityCredential**、OnBehalfOfCredential、WorkloadIdentityCredential。”
>
> — [azure-identity TOKEN_CACHING.md（1.25.1）](https://github.com/Azure/azure-sdk-for-python/blob/azure-identity_1.25.1/sdk/identity/azure-identity/TOKEN_CACHING.md)

使 `ManagedIdentityCredential` 正确缓存令牌的修复于 `1.6.0b3`（2021 年 4 月）发布。该凭证在 `1.18.0b1`（2024 年 7 月）中基于 MSAL 重新实现：

> “1.6.0b3（2021-04-06）：ManagedIdentityCredential 能够正确缓存令牌。”
>
> “1.18.0b1（2024-07-16）：同步 ManagedIdentityCredential 已更新为使用 MSAL 处理大多数底层托管标识实现。”
>
> — [azure-identity CHANGELOG.md](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/identity/azure-identity/CHANGELOG.md)

Phoenix 在 `pyproject.toml` 中约束 `azure-identity >= 1.18.0`（这是本文通过阅读源码验证过的最低版本，参见下一节）。当前 `uv.lock` 解析为 `1.25.3`。使用现代 `azure-identity` 的代码可以在每次建立新连接时调用一次 `credential.get_token(scope)`，并依赖 SDK 去重底层 IMDS 往返请求。

<a id="how-the-async-cache-is-wired-verified-by-reading-the-installed-source"></a>

#### 异步缓存如何串联（已通过阅读安装的源码验证）

异步 `ManagedIdentityCredential` 并非独立实现——它通过共同基类与同步版本共享缓存机制。调用链如下（基于 Phoenix 虚拟环境中安装的 azure-identity 1.25.3）：

1. `azure.identity.aio._credentials.managed_identity.ManagedIdentityCredential` 是一层轻量包装，根据环境变量选择具体的内部凭证。在未设置特殊环境变量的典型 AKS/VM 部署中，它构造 `ImdsCredential`（第 112 行）。
2. `azure.identity.aio._credentials.imds.ImdsCredential` 继承 `GetTokenMixin`，并实现两个抽象方法：`_acquire_token_silently` 返回 `self._client.get_cached_token(*scopes, **kwargs)`（第 68 行），`_request_token` 则实际请求 IMDS HTTP 端点（第 89 行）。
3. `azure.identity.aio._internal.get_token_mixin.GetTokenMixin._get_token_base` 是公开的 `get_token` 工作流程。它先调用 `_acquire_token_silently` 检查缓存（第 122 行），再调用 `get_refresh_status(token, self._last_request_time)`（第 125 行），仅在状态为 `REQUIRED`（第 126-130 行）或 `RECOMMENDED`（第 131-138 行）时调用 `_request_token`。对于 `RECOMMENDED`，刷新失败会被静默吞掉，并保留缓存令牌。
4. `azure.identity._internal.managed_identity_client.ManagedIdentityClientBase` 是同步和异步托管标识客户端共享的基类。它默认构造 MSAL 的 `self._cache = TokenCache()`（第 37 行），在每次成功获取令牌后调用 `self._cache.add(...)`（第 89 行），而 `get_cached_token` 会在 MSAL `TokenCache` 中查找未过期且同时遵守 `expires_on` 和 `refresh_on` 的令牌（第 96-120 行）。

异步 `AsyncManagedIdentityClient` 继承 `ManagedIdentityClientBase`（没有重写缓存管理），因此缓存实例、缓存查找逻辑以及先查缓存再刷新的控制流程，与同步路径实际使用的是同一套代码。

还针对 `azure-identity == 1.18.0`（首个使用 MSAL 处理托管标识的稳定版本）阅读了相同的五个文件。其结构完全相同：`ImdsCredential` 是同一个类，采用相同的缓存查找方式；`AsyncManagedIdentityClient` 继承相同的 `ManagedIdentityClientBase`；基类在构造函数中实例化 `msal.TokenCache()`；`_process_response` 在每次成功获取后加入缓存；`get_cached_token` 同时遵守 `expires_on` 和 `refresh_on`。差异只有 1.18.0 到 1.25.3 之间加入的风格细化：刷新决策辅助方法从返回 `bool` 的 `_should_refresh()` 改名为返回枚举的 `get_refresh_status()`，且 `_acquire_token_silently` 开始转发 kwargs，以支持基于 claims 跳过缓存。这些变化都不改变“缓存命中 → 可能刷新，失败时平滑回退”的核心语义。

**结论：针对托管标识的异步 `DefaultAzureCredential().get_token()` 与同步版本采用完全相同的令牌缓存方式，至少自 `azure-identity == 1.18.0` 起便如此。** 应用在每次新建数据库连接时调用它，首次调用之后都会收到缓存令牌实例，直到 SDK 判断需要刷新；届时 SDK 会透明地处理刷新，并在刷新失败时回退到仍有效的缓存令牌。应用层缓存无法提供任何 SDK 尚未实现的额外行为。

如果应用代码选择删除自己的令牌缓存包装并依赖 SDK 行为，经过验证的安全最低版本约束为 **`azure-identity >= 1.18.0`**——本文通过阅读源码验证的就是这一版本。更早版本可能也能工作（最初的缓存修复于 `1.6.0b3`、2021 年 4 月发布），但本文没有通过源码验证这些版本。

<a id="imds-server-side-caching-and-rate-limits"></a>

### IMDS 服务端缓存与速率限制

除 SDK 层缓存之外，提供托管标识令牌的 Azure 实例元数据服务自身也执行服务端缓存，并实施速率限制：

> “托管标识的后端服务会按资源 URI 维护约 24 小时的缓存。”
>
> — [Microsoft Learn：在虚拟机上使用托管标识获取访问令牌](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token)

> “对于每台 VM，托管标识类别的请求上限为每秒 20 个请求和 5 个并发请求。”
>
> — [虚拟机的 Azure 实例元数据服务](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service)

如果以某种方式绕过 SDK 缓存，在高频循环中为每个连接调用 IMDS，20 RPS / 5 并发的上限才会起作用。存在 SDK 缓存时（默认如此），应用代码在正常使用下不会接近这个限制。

<a id="implementation-pattern"></a>

### 实现模式

对于新建的 Azure 托管标识代码库，最小可用实现如下：

```python
from azure.identity.aio import DefaultAzureCredential

credential = DefaultAzureCredential()  # construct once, reuse for the process


async def open_connection() -> asyncpg.Connection:
    token = await credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    return await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=token.token,
        database=database,
        ssl="require",
    )
```

这些就足够了。SDK 在多次调用间将令牌缓存在内存中，IMDS 执行服务端缓存，最终的 JWT 仅在握手时使用，而通过该连接创建器建立的池连接会在令牌过期后继续存在。

凭证应跨调用复用，因为构造 `DefaultAzureCredential` 并非简单操作（它会探测凭证链中的每个凭证来源），所以通常将它作为与进程同寿命的单例。

<a id="aws-rds-for-postgresql-with-iam-authentication"></a>

## 使用 IAM 身份验证的 AWS RDS for PostgreSQL

<a id="end-to-end-flow-1"></a>

### 端到端流程

当客户端希望通过 IAM 身份验证连接 AWS RDS for PostgreSQL 时：

1. 客户端通过 `boto3.client("rds").generate_db_auth_token(DBHostname=..., Port=..., DBUsername=...)` 请求 boto3 生成身份验证令牌。这是**客户端本地的 SigV4 签名操作**——boto3 使用进程中已加载的 AWS 凭证构建并签署预签名 URL。签名计算对请求字节的规范表示执行 HMAC-SHA256；此特定函数调用内部没有 HTTP 流量（已阅读安装包中的 `botocore/signers.py:559` 验证，该处调用 `_request_signer.generate_presigned_url(...)` 并直接返回 URL）。AWS 凭证本身通常已提前从主机本地元数据服务（EC2 IMDSv2、ECS 任务元数据或 EKS pod 标识端点）加载，并缓存在 boto3 `Session` 中；稳态下，从此调用点看不到凭证引导路径。它与 Azure 流程的对应关系见下方比较部分。
2. 客户端使用生成的令牌作为密码参数打开 PostgreSQL 连接。RDS 在启动握手期间验证 SigV4 签名。此验证**并非**在 RDS 本地完成：SigV4 使用对称模型（HMAC），而 RDS 不持有客户的密钥，因此验证会经过 AWS 内部 IAM 机制重新计算并比较签名，再检查 IAM 主体是否拥有目标数据库用户资源上的 `rds-db:connect` 权限。这次往返的成本由 RDS 而非应用承担，客户端无法看到。
3. 此后，该连接就是普通的 PostgreSQL 会话，不再使用令牌。

<a id="token-lifetime-and-connection-persistence"></a>

### 令牌有效期与连接持久性

AWS 文档明确指出，RDS IAM 令牌只在身份验证时起作用：

> “生成身份验证令牌后，其有效期为 15 分钟，之后便会过期。如果尝试使用已过期的令牌连接，连接请求会被拒绝。”
>
> — [AWS RDS 用户指南：通过 IAM 身份验证连接数据库实例](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.html)

> “令牌仅用于身份验证，不影响已经建立的会话。”
>
> — [AWS RDS 用户指南：MariaDB、MySQL 和 PostgreSQL 的 IAM 数据库身份验证](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)

15 分钟的窗口仅限制*打开*新连接。在 T=0 签署的令牌不能用于在 T+16min 打开新连接，必须重新生成。但只要会话在 15 分钟窗口内成功完成握手，就能在令牌过期后无限期继续存在。

<a id="why-no-per-token-caching-is-needed-at-the-application-level"></a>

### 为什么应用层无需逐令牌缓存

由于 `generate_db_auth_token` 只针对 boto3 已缓存的凭证执行本地 HMAC 计算（此特定函数调用中没有 HTTP 流量，参见上文端到端流程），每次调用的延迟成本并不值得通过缓存消除。每次调用只需微秒级时间，与对几百字节计算哈希处于同一数量级。在应用层为 `generate_db_auth_token` 包装缓存，只会增加复杂性和令牌过期失效的故障模式，没有可衡量的收益。

技术栈更底层确实存在另一层缓存：`generate_db_auth_token` 用来签名的 AWS 凭证，从主机本地元数据服务获取后，会缓存在 boto3 `Session` 中，并在过期前于后台刷新。该缓存由 botocore 提供，应用代码无需重新实现。

因此，自然的模式是在每次打开新连接时重新调用 `generate_db_auth_token`。此时令牌刚刚生成，asyncpg 握手所需时间远短于 15 分钟有效窗口，令牌也不会闲置在内存中等待过期。

<a id="security-model"></a>

### 安全模型

由于令牌只是 SigV4 预签名 URL，其安全属性来自 SigV4 以及一些 RDS 特有绑定，概括如下：

- **签名证明持有 AWS 凭证。** SigV4 使用 HMAC-SHA256，密钥由 AWS 秘密访问密钥派生。秘密密钥始终留在客户端；RDS 通过 AWS 内部 IAM 机制验证签名。
- **签名绑定特定资源。** 它涵盖主机名、端口、AWS 区域、操作（`connect`）和数据库用户名。为 `alice@db1.region-A` 签署的令牌无法重放到 `bob@db2.region-B`，甚至也无法用于 `bob@db1.region-A`。
- **签名具有时限。** 预签名 URL 中 15 分钟的 `X-Amz-Expires` 窗口限制了被盗令牌可用于打开*新*连接的时间。（如上所述，它不影响已经建立的会话。）
- **必须使用 TLS。** RDS IAM 身份验证要求连接采用 SSL/TLS；没有 TLS，预签名 URL 会在传输中暴露，路径上的攻击者便能在 15 分钟窗口内重放它。下方实现模式中的 `ssl="require"` 参数强制执行这一要求。
- **IAM 权限边界。** 有效签名是必要条件，但还不够：IAM 主体还必须拥有特定数据库用户资源上的 `rds-db:connect` 权限。签署有效令牌本身不会授予任何访问权限；IAM 授权会单独检查。

在此模型中，是否缓存令牌不是安全方面的选择。持有缓存令牌的任何进程都可以在其 15 分钟窗口内复用它，其内存暴露特征与任何等同密码的秘密相同。不采用缓存层的原因是上述成本考量，而非安全性；反而，逐连接重新生成令牌能尽量缩短其内存暴露窗口。

<a id="implementation-pattern-1"></a>

### 实现模式

对于新建的 AWS RDS IAM 代码库，最小可用实现如下：

```python
import asyncpg
import boto3

rds_client = boto3.client("rds")  # construct once, reuse for the process


async def open_connection() -> asyncpg.Connection:
    token = rds_client.generate_db_auth_token(
        DBHostname=host,
        Port=port,
        DBUsername=user,
    )
    return await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=token,
        database=database,
        ssl="require",
    )
```

这些就足够了。无需令牌缓存、有效性跟踪或过期缓冲——每个新连接都会在握手时获得刚签署的令牌。

<a id="how-aws-and-azure-compare"></a>

## AWS 与 Azure 的比较

读完上面两节，很容易认为两者的架构根本不同——Azure 必须“从 IMDS 获取令牌”，而 AWS“在本地生成”。这种说法在狭义技术细节上正确，但在架构层面容易误导。两个云平台都从主机本地元数据服务引导获取凭证，只是在不同层次缓存不同的对象。

<a id="the-architectural-difference-bearer-tokens-vs-signing-keys"></a>

### 架构差异：持有者令牌与签名密钥

两个云平台使用不同的凭证模型：

**Azure 托管标识基于持有者令牌。** 应用提交给资源（Azure DB for PostgreSQL、Storage、Key Vault 等）的对象*就是*凭证——由 Microsoft Entra 签署、限定到特定资源的 JWT（本例中为 `https://ossrdbms-aad.database.windows.net/.default` 作用域）。应用不持有可用于派生该令牌的任何加密材料；令牌必须由 Azure 基础设施签发。位于 `169.254.169.254` 的 IMDS 是主机本地的信任边界，让 VM/AKS pod 能够声明“我是分配给此资源的托管标识”，并获得证明这一身份的 JWT。

**AWS IAM 基于 HMAC 签名密钥。** 应用*持有*的是 AWS 访问密钥 ID + 秘密访问密钥（以及可选的会话令牌）。它们不会直接提交给 AWS 服务；应用使用它们为每个需要发起的请求计算 SigV4 签名。秘密密钥始终留在客户端，只有逐请求签名会发送出去。RDS 通过 AWS 内部 IAM 服务重新计算签名来验证它（引用见 AWS 部分“端到端流程”第 2 步）。

“Azure 发起网络调用获取令牌”与“AWS 在本地执行等价操作”的不对称，实际上是“Azure 缓存你要提交的*令牌*”与“AWS 缓存你用来签名的*签名密钥*”之间的不对称。

<a id="aws-also-has-a-metadata-service-call"></a>

### AWS 也会调用元数据服务

使用 IAM 角色运行的 EC2 实例、ECS 任务或 EKS pod 在启动时并不内置 AWS 凭证。boto3 启动时通过凭证链解析凭证，在这些环境下，最终会调用主机本地元数据服务（EC2 IMDSv2 使用恰好与 Azure 相同的 `169.254.169.254` 地址，ECS/EKS 则使用各自的等价端点）。该调用返回临时 AWS 凭证，典型会话有效期以小时计。boto3 将这些凭证缓存在 `Session` 中，并在它们过期前于后台刷新。

因此，稳态下每个连接的情况如下：

| | AWS RDS IAM | Azure 托管标识 |
|---|---|---|
| 是否网络调用主机本地元数据服务 | 是——在 boto3 会话引导时获取 AWS 凭证 | 是——首次调用 `get_token()` 时获取 JWT |
| 元数据调用返回什么 | 临时 AWS 签名密钥（通常有数小时有效期） | 限定到一个资源的持有者令牌（系统分配 MI 最长 24 小时） |
| 缓存对象可在本地用于什么 | 为任何 AWS 服务签署任意数量的 SigV4 请求 | 在 JWT 过期前，将同一 JWT 提交给接受该作用域的任何资源 |
| 缓存已预热时每个*新连接*的成本 | 仅本地 HMAC 签名（微秒级） | 仅缓存 JWT 查找（无 I/O） |
| SDK 何时从元数据刷新 | 在数小时有效窗口结束前于后台刷新凭证 | 临近过期时移除缓存，随后在下一次 `get_token` 时重新调用 IMDS |

稳态下，**两个云平台都不会为每个连接发起网络调用**。它们都通过应用代码看不到的 SDK 层缓存，在多次打开连接之间摊销元数据服务往返成本。

<a id="why-the-aws-api-feels-synchronous-and-azure-does-not"></a>

### 为什么 AWS API *感觉*是同步的，而 Azure 不是

原因有三个，与架构相比，它们更多取决于 SDK 边界的位置：

1. **boto3 凭证刷新发生在 `generate_db_auth_token` 调用路径之外。** 调用 `generate_db_auth_token(...)` 时看不到网络活动，是因为 boto3 `Session` 已缓存了之前（或后台）刷新获取的有效凭证。如果凭证尚未加载或已经过期，boto3 会在该调用内部阻塞等待刷新，但稳态下不会如此。`azure-identity` 的 `get_token` 具有相似结构：缓存已预热时立即返回，感觉完全在本地执行；缓存未预热时则阻塞等待 IMDS 调用。
2. **AWS 暴露签名原语，Azure 暴露令牌原语。** SigV4 允许用户代码持有秘密密钥并在本地生成逐请求签名，因此 SDK 边界是“给我一个已签名的字符串”。Azure 刻意不暴露类似原语——用户代码只能看到 JWT，而 `get_token` 返回的也是 JWT。Microsoft 选择将所有加密材料保留在 IMDS 边界之后，使用户代码永远不直接处理密钥材料。这是缩小攻击面的取舍，并非架构上的必然。
3. **逐请求签名与可复用令牌让生命周期感觉不同。** SigV4 为每次调用生成新签名，因此很自然地称为“本地计算”。Azure 的 `get_token` 生成可复用令牌，因此很自然地称为“获取”。两种描述都准确，只是强调同一整体生命周期的不同部分。

<a id="what-the-symmetry-means-for-application-code"></a>

### 这种对称性对应用代码意味着什么

使用任一云平台的代码都面临以下结论：

- **两个云 SDK 都已实施正确的缓存**——boto3 缓存 AWS 凭证（过期前刷新），azure-identity 缓存 JWT（临近过期时刷新，刷新失败时平滑回退；参见上文已验证的源码阅读部分）。
- **两种情况下，应用代码都无需自己的缓存层。** 对 AWS 而言，每次调用的签名成本是微秒级。对 Azure 而言，每次调用的缓存查找成本也是微秒级。为任一函数增加应用层包装都会增加复杂性，却没有可衡量的收益。
- **`pool_recycle` 与两个云平台的令牌机制均无关。** 它控制 SQLAlchemy 池中的连接年龄，而非令牌的新鲜程度——参见下一节。

<a id="connection-pooling-with-cloud-auth"></a>

## 云身份验证下的连接池

将 SQLAlchemy 连接池放在上述云身份验证连接创建器之前时，需要关注两个池配置：`pool_recycle` 和 `pool_pre_ping`。常见做法是让 `pool_recycle` 与令牌有效期对齐，假设池连接会在其原始令牌过期后失效。实际并不会如此，参见上文协议部分。本节逐项说明这些配置的实际作用，方便选择正确的默认值。

<a id="pool_pre_ping"></a>

### `pool_pre_ping`

当 `pool_pre_ping=True` 时，SQLAlchemy 在每次从池中取出连接时调用方言的 `do_ping` 实现，以验证连接是否仍然存活。asyncpg/PG 方言的 `do_ping` 继承自 `DefaultDialect`，执行一次 `cursor.execute(SELECT 1)` 往返：

```python
def do_ping(self, dbapi_connection: DBAPIConnection) -> bool:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(self._dialect_specific_select_one)
    finally:
        cursor.close()
    return True
```

— Phoenix 安装版本中的 `sqlalchemy/engine/default.py:750-756`

如果 ping 失败（网络重置、服务端断开连接等），SQLAlchemy 会使连接失效，通过连接创建器打开新连接，再将新连接交给调用方。该检查**每次从池中取出连接时执行一次**——即每个 `engine.begin()` 或 `async with AsyncSession() as session` 块执行一次，并非每执行一条语句就检查一次。

刚创建的连接会**明确跳过** ping。在 `sqlalchemy/pool/base.py` 中，`_invoke_creator` 创建新 DBAPI 连接后会立即将 `_ConnectionRecord.fresh` 设为 `True`（第 898 行），而池的取用路径会在运行 ping 前检查 `if not connection_is_fresh`（第 1302-1303 行）：

```python
if pool._pre_ping:
    if not connection_is_fresh:
        ...  # do the ping
```

这意味着全新的连接——即连接创建器生成的连接——首次从池中取出时绝不会承担 ping 成本。

`pool_pre_ping` 适合检测以下情况：

- 上游负载均衡器、NAT 网关或 PgBouncer 因空闲超时而断开连接。
- 服务端故障转移和维护重启。
- DBA 主动终止会话。
- 短暂的 TCP 重置。

<a id="pool_recycle"></a>

### `pool_recycle`

`pool_recycle=N` 表示，在从池中取出连接时，SQLAlchemy 会丢弃任何年龄超过 N 秒的池连接，并打开新连接替代。它**基于年龄**，而非存活状态——无论连接是否仍然存活，都会在达到实际时间上限时触发。

对于云身份验证连接池，常见配置是将 `pool_recycle` 设为“略短于令牌有效期”，让连接池在令牌过期前完成更替。根据协议部分，这种对齐并非保证正确性所必需：令牌仅在握手时起作用，既有会话不受令牌过期影响。**`pool_recycle` 是连接维护配置，而非令牌有效性配置。** 合理值通常为几十分钟：既足够长，避免池中连接频繁更替，又足够短，限制单个连接可能老化的程度。

让 `pool_recycle` 紧贴令牌窗口（例如 AWS IAM 使用 14 分钟），会降低连接池的实际收益：每个连接每小时更替多次，每次都支付完整的 TCP + TLS + PG 启动成本，在持续负载下削弱已预热连接池的优势。

<a id="nullpool"></a>

### `NullPool`

`NullPool` 是一种特殊的池实现，每次取用时都通过连接创建器打开新连接，归还时立即释放，完全不保留连接。结合上述“新连接跳过 ping”的行为，这意味着 **`pool_pre_ping` 和 `pool_recycle` 对 `NullPool` 引擎均不起作用**：每个连接都是新建的，因此跳过 ping；也没有长期存活的连接可供 `pool_recycle` 按年龄淘汰。

对于一次性迁移执行器等短期辅助引擎，`NullPool` 是合适的选择，其中每个连接都短暂使用后立即丢弃。此类引擎可以省略 `pool_pre_ping` 和 `pool_recycle`，因为它们不起作用。

<a id="cost-of-pool_pre_ping-under-load"></a>

### 负载下 `pool_pre_ping` 的成本

预先 ping 会在每次从池中取出连接时增加一次往返。这一成本是否显著，取决于工作负载每个请求会取用多少次连接。每次数据库调用都开启一个短事务的应用模式（例如将每个查询包装在独立 `async with session` 块中的 GraphQL 解析器），会为每次调用支付 ping 成本。整个请求期间持有单个会话的工作负载，则每个请求只支付一次。

这一成本几乎总是值得支付。对于任何面向用户的系统，另一种结果——让已被静默断开的连接在执行首条查询时向调用方抛出 `ConnectionResetError`——都比一次不到一秒的 ping 更糟。

<a id="common-assumptions-and-what-is-actually-true"></a>

## 常见假设与实际行为

对于云身份验证令牌如何与 PostgreSQL 及连接池交互，一些直觉假设在上述协议语义下并不成立。下表列出最常见的假设及其对应的实际行为。

| 假设 | 实际行为 |
|---|---|
| “访问令牌过期时，池中的连接会开始失效。” | 只在握手时检查令牌。既有连接可以在令牌过期后无限期继续存在。 |
| “需要让 `pool_recycle` < 令牌有效期，才能保持连接池有效。” | `pool_recycle` 不刷新令牌，只打开新连接。既有连接无需新令牌。有用的 `pool_recycle` 是连接维护上限，与令牌窗口无关。 |
| “需要自己编写令牌缓存，避免每个连接都获取令牌。” | 对 Azure：`azure-identity`（同步和异步）默认已通过 MSAL 的 `TokenCache` 在内存中缓存，经阅读源码验证。对 AWS：令牌生成是本地 SigV4 签名操作，每次调用只需微秒级时间，缓存只会增加复杂性，没有可衡量的收益。 |
| “应将 `pool_recycle` 设为令牌有效期。” | 令牌有效期与连接池维护互不相关。应根据允许单个连接存活多久来选择 `pool_recycle`，而非依据令牌过期时间。 |
| “如果打开连接时 IAM/MI 令牌还剩 14 分钟有效期，该连接就只能存活 14 分钟。” | 连接会随底层 TCP 会话一直存活，与历史上使用过的任何令牌无关。 |
| “AWS RDS 会在 IAM 令牌过期时关闭会话。” | AWS 在三个独立位置说明，令牌过期不会影响已经建立的会话。 |
| “需要为 Azure 令牌缓存设置几分钟的刷新缓冲，以处理重试。” | 刷新重试的理由不适用，因为 (a) SDK 缓存透明地处理刷新，且 (b) 若代码层缓存未在刷新失败时回退到旧令牌，加大缓冲也没有收益。 |

<a id="event-loop-affinity-of-azureidentityaio-credentials"></a>

## `azure.identity.aio` 凭证的事件循环亲和性

`azure.identity.aio.DefaultAzureCredential`（以及它在 Azure 托管环境中最终解析出的内部 `ManagedIdentityCredential` / `ImdsCredential`）采用异步传输：首次调用 `get_token(scope)` 时，它会延迟构造基于 `azure.core.pipeline.transport.AioHttpTransport` 的 `AsyncPipeline`，后者又会打开 `aiohttp.ClientSession`。`aiohttp.ClientSession` 绑定到**创建时正在运行的事件循环**；从另一个循环复用它（包括原循环此后已关闭的情况），会在会话内部首次 await 时抛出 `RuntimeError: Event loop is closed`。

构造 `DefaultAzureCredential()` 本身不会绑定循环。绑定发生在首次 `await credential.get_token(...)`、实例化管道时。因此，在同步上下文中（尚不存在任何循环时）构造凭证没有问题，直到某个循环对它调用 `get_token`，将凭证的传输固定到该循环。

对于先运行一次短期 `asyncio.run(...)`（例如迁移执行器），随后运行长期循环（例如 Web 服务），并在两者间共享同一凭证实例的任何应用，这一点都很重要。顺序如下：

1. 主线程/进程在同步上下文中构造一个 `DefaultAzureCredential`，此时尚未绑定任何循环。
2. 短期循环 A 启动（通常是在工作线程中通过 `asyncio.run` 执行一次性任务），调用 `credential.get_token(scope)`，凭证的 aiohttp 会话被延迟创建并绑定到循环 A。
3. 循环 A 完成工作，由 `asyncio.run` 清理并关闭。
4. 长期循环 B 启动。应用代码对同一凭证调用 `credential.get_token(scope)`。凭证复用缓存的 aiohttp 会话，它仍绑定到现已关闭的循环 A。会话内下一次网络读写会抛出 `RuntimeError: Event loop is closed`。

本文前面描述的 `ManagedIdentityCredential` / `ImdsCredential` MSAL `TokenCache` 与此问题互不相关。`TokenCache` 位于 `ManagedIdentityClientBase` 实例中，存储*令牌字节*；aiohttp `ClientSession` 位于凭证内部的管道上，具有循环亲和性的是它。即使命中已预热的 `TokenCache`，每次调用仍会经过管道的传输层——参见 `azure/identity/aio/_internal/get_token_mixin.py` 中的 `GetTokenMixin._get_token_base`，连仅命中缓存的调用也通过异步管道路由。因此，“令牌已缓存”并不能避免调用访问可能已经失效的 aiohttp 会话。

<a id="symptom-runtimeerror-event-loop-is-closed-on-pool-connection-open-in-phoenix"></a>

### 症状：Phoenix 从连接池打开连接时出现 `RuntimeError: Event loop is closed`

在类似 Phoenix 的环境中，此问题表现为：一个 `DefaultAzureCredential` 实例通过单个异步连接创建器闭包，在迁移引擎和主引擎之间共享。迁移引擎通过 [src/phoenix/db/migrate.py](src/phoenix/db/migrate.py) 的 `migrate_in_thread` → `asyncio.run(run())` 在工作线程中运行，为迁移期间创建并随后关闭一个新循环。当迁移首次从池中取出连接而触发创建器时，凭证的 aiohttp 会话便绑定到这个临时循环。迁移完成后，`asyncio.run` 关闭循环并返回，但凭证仍存在——闭包持有凭证，而主引擎又持有闭包。

之后，uvicorn 启动长期服务循环，主连接池打开第一个实际连接。创建器调用 `credential.get_token(scope)`，azure-identity 将调用路由到缓存管道，管道交给绑定在已关闭迁移循环上的 aiohttp 会话，调用随即抛出 `RuntimeError: Event loop is closed`。由于错误出现在 SQLAlchemy 打开池连接的路径中，看起来像连接池错误，而非凭证错误。

`TokenCache` 层缓存无法绕过这一故障，因为每次 `get_token` 调用的缓存查找仍然经过异步管道（参见上一段）。

<a id="why-this-does-not-bite-the-aws-path"></a>

### 为什么 AWS 路径不受此问题影响

[src/phoenix/db/aws_auth.py](src/phoenix/db/aws_auth.py) 在每个连接的 `async_creator` 内打开一个*全新*的 `session.client("rds")` 异步上下文。`aioboto3.Session()` 本身是没有 aiohttp 状态的配置对象，而每个 `session.client(...)` 都会为该 `async with` 块的存续期间构建一个绑定事件循环的新 botocore 客户端栈。AWS 闭包捕获的长期对象（`aioboto3.Session`）没有事件循环亲和性；具有循环亲和性的部分（RDS 客户端内部的 aiohttp 客户端栈）在每次调用内创建并销毁，因此始终在当前运行的循环上创建和结束。AWS 路径因此可以正确配合基于 `asyncio.run` 的迁移执行器，无需额外处理。

<a id="fix"></a>

### 修复

[src/phoenix/db/azure_auth.py](src/phoenix/db/azure_auth.py) 暴露单个高层入口 `create_azure_engine(url, connect_args, **engine_kwargs) -> AsyncEngine`，自行创建 `DefaultAzureCredential`，将异步连接创建器接入 `sqlalchemy.ext.asyncio.create_async_engine`，并对返回引擎的 `dispose` 方法执行猴子补丁（实例级而非类级），使 `await engine.dispose()` 也会 `await` `credential.close()`。凭证、创建器和释放钩子全部私有地保留在闭包中，调用方只能看到 `AsyncEngine`。[src/phoenix/db/aws_auth.py](src/phoenix/db/aws_auth.py) 暴露形态相同的 `create_aws_engine`，但没有释放补丁（aioboto3 没有需要清理的循环亲和状态）。

[src/phoenix/db/engines.py](src/phoenix/db/engines.py) 在 `aio_postgresql_engine` 的 `use_azure` 分支中调用 `create_azure_engine` **两次**——分别用于主引擎和迁移引擎，使每个引擎拥有自己的 `DefaultAzureCredential` 实例。迁移引擎的凭证绑定到 `migrate_in_thread` 中临时的 `asyncio.run(...)` 循环，而 `migrate.py` 已有的 `await engine.dispose()` 调用（在同一循环内、`asyncio.run` 将其销毁前运行）会在拥有 aiohttp 会话的循环上关闭凭证。主引擎的凭证在首次使用时正常绑定到 uvicorn 循环，并通过 [src/phoenix/server/cli/commands/serve.py](src/phoenix/server/cli/commands/serve.py) 中已有的 `shutdown_callbacks.append(primary_engine.dispose)` 机制关闭。AWS 分支也为保持对称而调用 `create_aws_engine` 两次，尽管两个引擎可以安全复用同一个会话。

释放方法的猴子补丁作用于实例级（`engine.__dict__`，通过正常属性查找遮蔽类方法），而非类级。它假设 SQLAlchemy 始终通过 `engine.dispose(...)` 而非 `type(engine).dispose(engine)` 调用 `dispose`，Phoenix 锁定版本确实如此；如果未来 SQLAlchemy 改为通过类调用，就会静默绕过补丁并泄漏凭证。

曾考虑另一种方案：在 `async_creator` 内延迟创建按循环区分的凭证，只要 `asyncio.get_running_loop()` 与缓存的循环不同就重建凭证。这种方式可为未来在新循环下运行的任意调用方自动恢复，但无法干净地关闭迁移循环的凭证：等创建器发现循环已变化时，迁移循环早已关闭，无法再 `await credential.close()`。它会在每次进程启动时向 stderr 输出一次 `Unclosed client session` 警告，这种噪声日后可能掩盖真实错误。双凭证方案能够在各自循环上干净关闭两个凭证，因此最终选择了它。

<a id="phoenix-implementation-notes"></a>

## Phoenix 实现说明

Phoenix 代码库在以下位置实现两条身份验证路径：

- [src/phoenix/db/azure_auth.py](src/phoenix/db/azure_auth.py)——`create_azure_engine(url, connect_args, **engine_kwargs)` 构建配置完整、通过 Azure 托管标识验证身份的 `AsyncEngine`。每次调用都创建新的 `DefaultAzureCredential`，将异步创建器接入 SQLAlchemy，并修补 `engine.dispose`，使清理过程也会在 await `dispose` 的循环上关闭底层凭证。凭证始终保留在闭包中。关于为什么不能简单地在迁移循环与服务循环之间共享凭证，参见上文“`azure.identity.aio` 凭证的事件循环亲和性”。
- [src/phoenix/db/aws_auth.py](src/phoenix/db/aws_auth.py)——`create_aws_engine(url, connect_args, **engine_kwargs)` 构建配置完整、通过 AWS RDS IAM 验证身份的 `AsyncEngine`。为每个连接生成新令牌，没有缓存层，符合推荐模式。无需释放补丁：aioboto3 每次调用的 `session.client("rds")` 上下文都会在每个连接中创建并销毁其 aiohttp 栈，因此没有任何循环亲和状态跨调用存活。
- [src/phoenix/db/engines.py](src/phoenix/db/engines.py)——接入两个云引擎工厂和普通密码分支。每个非迁移分支都使用 `pool_pre_ping=True`。托管标识、AWS IAM 和静态密码分支的 `pool_recycle` 均使用 `_POOL_RECYCLE_SECONDS`（55 分钟）。迁移引擎使用 `NullPool`，省略这两个配置。`use_azure` 分支调用 `create_azure_engine` 两次（分别用于主引擎和迁移引擎），使每个引擎都有自己的凭证，绑定到最终使用它的循环。

<a id="open-questions-and-unverified-claims"></a>

## 待解问题与未经验证的论断

本文特意不将以下事项断言为事实：

1. **AWS RDS 身份验证插件内部机制。** 本文只主张这一*行为*：已通过 IAM 验证身份的既有会话会在令牌过期后继续存在。本文不对 RDS 在服务端如何实现 IAM 身份验证作任何断言（是否存在 `rdsauthproxy` 组件、验证发生在进程内还是边车中等），因为引用来源均未验证这些细节，且它们不是本文结论成立的必要条件。
2. **精确的区域内延迟数值。** “Azure 区域内延迟为 1–3 ms”或“asyncpg 握手不到一秒”等说法只是直觉，并非测量结果。没有基准测试时，不应在代码注释中引用它们。

<a id="sources"></a>

## 来源

PostgreSQL：

- [PostgreSQL 文档，54.2 消息流程](https://www.postgresql.org/docs/current/protocol-flow.html)
- [PostgreSQL 文档，20.5 密码身份验证](https://www.postgresql.org/docs/current/auth-password.html)

Azure：

- [Azure Database for PostgreSQL 的 Microsoft Entra 身份验证](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-azure-ad-authentication)
- [Microsoft 标识平台中的可配置令牌有效期](https://learn.microsoft.com/en-us/entra/identity-platform/configurable-token-lifetimes)
- [Microsoft Q&A：自动终止 Azure PostgreSQL Flexible Server 中访问令牌已过期的会话](https://learn.microsoft.com/en-us/answers/questions/2242405/automating-session-termination-for-expired-access)
- [Microsoft Learn：在虚拟机上使用托管标识获取访问令牌](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token)
- [虚拟机的 Azure 实例元数据服务](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service)
- [azure-identity Python README——令牌缓存](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#token-caching)
- [azure-identity TOKEN_CACHING.md（1.25.1）](https://github.com/Azure/azure-sdk-for-python/blob/azure-identity_1.25.1/sdk/identity/azure-identity/TOKEN_CACHING.md)
- [azure-identity CHANGELOG.md](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/identity/azure-identity/CHANGELOG.md)
- [在 azure-identity 中启用令牌缓存（Issue #26177）](https://github.com/Azure/azure-sdk-for-python/issues/26177)

AWS：

- [AWS RDS 用户指南：通过 IAM 身份验证连接数据库实例](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.html)
- [AWS RDS 用户指南：MariaDB、MySQL 和 PostgreSQL 的 IAM 数据库身份验证](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html)
- [用于 API 请求的 AWS Signature Version 4](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv.html)
- [AWS API 请求签名的组成部分](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-signing-elements.html)
- [generate-db-auth-token——AWS CLI 命令参考](https://docs.aws.amazon.com/cli/latest/reference/rds/generate-db-auth-token.html)
- `botocore/signers.py:515-566`——`generate_db_auth_token` 源码（直接阅读 `.venv/lib/python3.10/site-packages/botocore/signers.py`）。

SQLAlchemy：

- 安装包中的 `sqlalchemy/pool/base.py` 和 `sqlalchemy/engine/default.py`，位于 `.venv/lib/python3.10/site-packages/sqlalchemy/`（直接阅读，而非通过网页文档）。

azure-identity 源文件（直接阅读 `.venv/lib/python3.10/site-packages/azure/identity/`）：

- `aio/_credentials/managed_identity.py`——异步 `ManagedIdentityCredential` 包装，根据环境选择内部凭证。
- `aio/_credentials/imds.py`——异步 `ImdsCredential`，实现 `_acquire_token_silently`（缓存查找）和 `_request_token`（IMDS HTTP 调用）。
- `aio/_internal/get_token_mixin.py`——`GetTokenMixin._get_token_base`，所有异步凭证共享的先查缓存再刷新控制流程。
- `aio/_internal/managed_identity_client.py`——`AsyncManagedIdentityClient`，继承同步/异步共享基类。
- `_internal/managed_identity_client.py`——`ManagedIdentityClientBase`，持有 MSAL `TokenCache`，并实现 `get_cached_token` 和 `_process_response`（加入缓存的路径）。
