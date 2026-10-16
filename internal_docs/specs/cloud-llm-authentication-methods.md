<a id="cloud-llm-authentication-methods"></a>
# 云端 LLM 认证方法

本文是集成云托管大语言模型（LLM）时认证模式的完整技术参考，重点介绍 Azure OpenAI 和 AWS Bedrock。

<a id="table-of-contents"></a>
## 目录

1. [概览](#executive-summary)
2. [Azure OpenAI 认证](#azure-openai-authentication)
   - [认证方法概览](#azure-authentication-methods-overview)
   - [API 密钥认证](#azure-api-key-authentication)
   - [Azure AD token 提供器（服务主体）](#azure-ad-token-provider-service-principal)
   - [DefaultAzureCredential（默认凭证）](#defaultazurecredential-default-credentials)
   - [SDK 实现详情](#azure-sdk-implementation-details)
3. [AWS Bedrock 认证](#aws-bedrock-authentication)
   - [认证方法概览](#aws-authentication-methods-overview)
   - [访问密钥认证](#access-keys-authentication)
   - [默认凭证链](#aws-default-credential-chain)
   - [SDK 实现详情](#aws-sdk-implementation-details)
4. [Phoenix 实现](#phoenix-implementation)
   - [数据模型](#data-model)
   - [客户端工厂模式](#client-factory-pattern)
5. [生产就绪评估](#production-readiness-assessment)
6. [未来考虑](#future-considerations)
7. [参考资料](#references)

---

<a id="executive-summary"></a>
## 概览

Phoenix 为 Azure OpenAI 支持三种认证方式，为 AWS Bedrock 支持两种：

| 提供商 | 认证方式 | 场景 | 生产就绪 |
|----------|-------------|----------|------------------|
| **Azure OpenAI** | `api_key` | 使用 API 密钥的简单部署 | ✅ |
| **Azure OpenAI** | `ad_token_provider` | 使用客户端密钥的服务主体 | ✅ |
| **Azure OpenAI** | `default_credentials` | 托管身份、Azure CLI、环境变量 | ✅ |
| **AWS Bedrock** | `access_keys` | 显式 IAM 凭证 | ✅ |
| **AWS Bedrock** | `default_credentials` | IAM 角色、环境变量、配置文件 | ✅ |

这些方法覆盖 80% 以上实际部署场景。用户分配托管身份、跨账号角色扮演等高级模式，可按客户需求添加。

---

<a id="azure-openai-authentication"></a>
## Azure OpenAI 认证

<a id="azure-authentication-methods-overview"></a>
### Azure 认证方法概览

Azure OpenAI 支持三种主要认证机制，分别适用于不同部署场景：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AZURE OPENAI AUTHENTICATION FLOW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐    │
│  │   API Key    │    │  Service         │    │  DefaultAzureCredential │    │
│  │              │    │  Principal       │    │                         │    │
│  └──────┬───────┘    └────────┬─────────┘    └────────────┬────────────┘    │
│         │                     │                           │                 │
│         ▼                     ▼                           ▼                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐    │
│  │ api-key      │    │ Bearer token     │    │ Chained credential      │    │
│  │ header       │    │ from AAD         │    │ providers               │    │
│  └──────┬───────┘    └────────┬─────────┘    └────────────┬────────────┘    │
│         │                     │                           │                 │
│         └─────────────────────┴───────────────────────────┘                 │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Azure OpenAI       │                                  │
│                    │  Endpoint           │                                  │
│                    └─────────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

<a id="azure-api-key-authentication"></a>
### Azure API 密钥认证

最简单的认证方法。可在 Azure Portal 为 Azure OpenAI 资源生成 API 密钥。

**适用场景：**
- 快速原型和开发。
- 不集成 Azure AD 的简单部署。
- 可妥善管理密钥轮换的场景。

**环境变量：**
- `AZURE_OPENAI_API_KEY`：API 密钥。
- `AZURE_OPENAI_ENDPOINT`：资源端点，例如 `https://my-resource.openai.azure.com`。

**SDK 行为：**

OpenAI Python SDK 的 `AzureOpenAI` 客户端按以下顺序检查凭证：

```python
# From openai-python src/openai/lib/azure.py lines 192-201
if api_key is None:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")

if azure_ad_token is None:
    azure_ad_token = os.environ.get("AZURE_OPENAI_AD_TOKEN")

if api_key is None and azure_ad_token is None and azure_ad_token_provider is None:
    raise OpenAIError(
        "Missing credentials. Please pass one of `api_key`, `azure_ad_token`, "
        "`azure_ad_token_provider`, or the `AZURE_OPENAI_API_KEY` or "
        "`AZURE_OPENAI_AD_TOKEN` environment variables."
    )
```

> **来源：** [openai/openai-python `azure.py` L192-201](https://github.com/openai/openai-python/blob/722d3fffb82e9150a16da01e432b70d126ca5254/src/openai/lib/azure.py#L192-L201)

<a id="azure-ad-token-provider-service-principal"></a>
### Azure AD token 提供器（服务主体）

适合需要显式服务主体凭证进行 Azure AD 认证的生产负载。

**适用场景：**
- 服务间认证的生产部署。
- CI/CD 流水线。
- 需要显式凭证管理的场景。
- 多租户应用。

**必需凭证：**
- `tenant_id`：Azure AD 租户 ID。
- `client_id`：应用或客户端 ID。
- `client_secret`：客户端密钥值。
- `scope`：OAuth scope，默认 `https://cognitiveservices.azure.com/.default`。

**工作原理：**

`azure-identity` 的 `ClientSecretCredential` 向 Azure AD 认证并返回 token：

```python
# From azure-sdk-for-python azure/identity/_credentials/client_secret.py line 9
class ClientSecretCredential(ClientCredentialBase):
    """Authenticates as a service principal using a client secret."""
```

> **来源：** [Azure/azure-sdk-for-python `client_secret.py` L9](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/identity/azure-identity/azure/identity/_credentials/client_secret.py#L9)

`get_bearer_token_provider` 包装凭证，提供返回 bearer token 的可调用对象：

```python
# From azure-sdk-for-python azure/identity/_bearer_token_provider.py lines 17-46
def get_bearer_token_provider(credential: TokenProvider, *scopes: str) -> Callable[[], str]:
    """Returns a callable that provides a bearer token.

    It can be used for instance to write code like:

        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        credential = DefaultAzureCredential()
        bearer_token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )

        # Usage
        request.headers["Authorization"] = "Bearer " + bearer_token_provider()
    """
    policy = BearerTokenCredentialPolicy(credential, *scopes)

    def wrapper() -> str:
        request = _make_request()
        policy.on_request(request)
        return request.http_request.headers["Authorization"][len("Bearer ") :]

    return wrapper
```

> **来源：** [Azure/azure-sdk-for-python `_bearer_token_provider.py` L17-46](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/identity/azure-identity/azure/identity/_bearer_token_provider.py#L17-L46)

<a id="defaultazurecredential-default-credentials"></a>
### DefaultAzureCredential（默认凭证）

对于需要无需修改代码即可跨环境运行的生产负载，这是推荐方式。

**适用场景：**
- Azure 上的生产部署，如虚拟机、App Service、AKS、Functions。
- 使用 Azure CLI 认证的本地开发。
- 使用 Azure Workload Identity 的 Kubernetes。
- 需要环境无关代码的场景。

**凭证链顺序：**

`DefaultAzureCredential` 依次尝试这些来源，遇到首个成功项即停止：

```python
# From azure-sdk-for-python azure/identity/_credentials/default.py lines 60-82
class DefaultAzureCredential(ChainedTokenCredential):
    """A credential capable of handling most Azure SDK authentication scenarios.

    The identity it uses depends on the environment. When an access token is needed,
    it requests one using these identities in turn, stopping when one provides a token:

    1. A service principal configured by environment variables.
       See EnvironmentCredential for more details.
    2. WorkloadIdentityCredential if environment variable configuration is set
       by the Azure workload identity webhook.
    3. An Azure managed identity. See ManagedIdentityCredential for more details.
    4. On Windows only: a user who has signed in with a Microsoft application,
       such as Visual Studio.
    5. The identity logged in to Visual Studio Code with the Azure Resources extension.
    6. The identity currently logged in to the Azure CLI.
    7. The identity currently logged in to Azure PowerShell.
    8. The identity currently logged in to the Azure Developer CLI.
    9. Brokered authentication (Windows WAM) if azure-identity-broker is installed.
    """
```

> **来源：** [Azure/azure-sdk-for-python `default.py` L60-82](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/identity/azure-identity/azure/identity/_credentials/default.py#L60-L82)

**EnvironmentCredential 环境变量：**

凭证链首个提供器 `EnvironmentCredential` 检查服务主体凭证：

```python
# From azure-sdk-for-python azure/identity/_credentials/environment.py lines 24-48
class EnvironmentCredential:
    """A credential configured by environment variables.

    This credential is capable of authenticating as a service principal using
    a client secret or a certificate. Configuration is attempted in this order:

    Service principal with secret:
      - AZURE_TENANT_ID: ID of the service principal's tenant
      - AZURE_CLIENT_ID: the service principal's client ID
      - AZURE_CLIENT_SECRET: one of the service principal's client secrets
      - AZURE_AUTHORITY_HOST: authority of a Microsoft Entra endpoint

    Service principal with certificate:
      - AZURE_TENANT_ID: ID of the service principal's tenant
      - AZURE_CLIENT_ID: the service principal's client ID
      - AZURE_CLIENT_CERTIFICATE_PATH: path to a PEM or PKCS12 certificate file
      - AZURE_CLIENT_CERTIFICATE_PASSWORD: (optional) password of the certificate
      - AZURE_CLIENT_SEND_CERTIFICATE_CHAIN: (optional) send public certificate chain
    """
```

> **来源：** [Azure/azure-sdk-for-python `environment.py` L24-48](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/identity/azure-identity/azure/identity/_credentials/environment.py#L24-L48)

**托管身份：**

在 Azure 基础设施上运行时，`ManagedIdentityCredential` 自动检测宿主环境：

```python
# From azure-sdk-for-python azure/identity/_credentials/managed_identity.py lines 48-71
class ManagedIdentityCredential:
    """Authenticates with an Azure managed identity in any hosting environment
    which supports managed identities.

    This credential defaults to using a system-assigned identity. To configure
    a user-assigned identity, use one of the keyword arguments.

    :keyword str client_id: a user-assigned identity's client ID or, when using
        Pod Identity, the client ID of a Microsoft Entra app registration.
    :keyword identity_config: a mapping {parameter_name: value} specifying a
        user-assigned identity by its object or resource ID.
    """
```

> **来源：** [Azure/azure-sdk-for-python `managed_identity.py` L48-71](https://github.com/Azure/azure-sdk-for-python/blob/f7ef11846bd79d4cb36349b2d917a7b92f1fc03a/sdk/identity/azure-identity/azure/identity/_credentials/managed_identity.py#L48-L71)

<a id="azure-sdk-implementation-details"></a>
### Azure SDK 实现详情

**OpenAI Python SDK Azure 客户端：**

`AzureOpenAI` 接受三种互斥认证选项：

```python
# From openai-python src/openai/lib/azure.py lines 151-171
def __init__(
    self,
    *,
    api_version: str | None = None,
    azure_endpoint: str | None = None,
    azure_deployment: str | None = None,
    api_key: str | Callable[[], str] | None = None,
    azure_ad_token: str | None = None,
    azure_ad_token_provider: AzureADTokenProvider | None = None,
    # ... other parameters
) -> None:
    """Construct a new synchronous azure openai client instance.

    This automatically infers the following arguments from their corresponding
    environment variables if they are not provided:
    - `api_key` from `AZURE_OPENAI_API_KEY`
    - `azure_ad_token` from `AZURE_OPENAI_AD_TOKEN`
    - `api_version` from `OPENAI_API_VERSION`
    - `azure_endpoint` from `AZURE_OPENAI_ENDPOINT`
    """
```

> **来源：** [openai/openai-python `azure.py` L151-171](https://github.com/openai/openai-python/blob/722d3fffb82e9150a16da01e432b70d126ca5254/src/openai/lib/azure.py#L151-L171)

**关键认识：** `api_key` 接受 `Callable[[], str]`，允许传入 token 提供器函数。Phoenix 因此能将 `get_bearer_token_provider` 与 OpenAI 客户端集成。

---

<a id="aws-bedrock-authentication"></a>
## AWS Bedrock 认证

<a id="aws-authentication-methods-overview"></a>
### AWS 认证方法概览

AWS 在所有 SDK 中使用标准化凭证提供器链：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AWS CREDENTIAL PROVIDER CHAIN                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Priority Order (first match wins):                                         │
│                                                                             │
│  1. Explicit credentials passed to client/session                           │
│     └── aws_access_key_id, aws_secret_access_key, aws_session_token         │
│                                                                             │
│  2. Environment variables                                                   │
│     └── AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN         │
│                                                                             │
│  3. Shared credentials file (~/.aws/credentials)                            │
│     └── [default] or [profile_name] sections                                │
│                                                                             │
│  4. AWS config file (~/.aws/config)                                         │
│     └── [profile profile_name] sections                                     │
│                                                                             │
│  5. AssumeRole provider (if role_arn configured in profile)                 │
│     └── Cross-account access, federated identity                            │
│                                                                             │
│  6. Container credentials (ECS, EKS)                                        │
│     └── AWS_CONTAINER_CREDENTIALS_RELATIVE_URI                              │
│                                                                             │
│  7. Instance metadata service (EC2, Lambda)                                 │
│     └── IAM role attached to instance/function                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

<a id="access-keys-authentication"></a>
### 访问密钥认证

显式 IAM 凭证，适用于需要直接管理凭证的情况。

**适用场景：**
- 使用 IAM 用户凭证的 CI/CD。
- 使用 STS 临时凭证的跨账号访问。
- IAM 角色不可用的场景。
- 测试和开发。

**必需凭证：**
- `aws_access_key_id`：IAM 访问密钥 ID。
- `aws_secret_access_key`：IAM 私有访问密钥。
- `aws_session_token`：可选，临时凭证会话 token。

**SDK 行为：**

botocore 的 `EnvProvider` 从环境变量读取凭证：

```python
# From botocore/credentials.py lines 1185-1194
class EnvProvider(CredentialProvider):
    METHOD = "env"
    CANONICAL_NAME = "Environment"
    ACCESS_KEY = "AWS_ACCESS_KEY_ID"
    SECRET_KEY = "AWS_SECRET_ACCESS_KEY"
    # The token can come from either of these env var.
    # AWS_SESSION_TOKEN is what other AWS SDKs have standardized on.
    TOKENS = ["AWS_SECURITY_TOKEN", "AWS_SESSION_TOKEN"]
    EXPIRY_TIME = "AWS_CREDENTIAL_EXPIRATION"
    ACCOUNT_ID = "AWS_ACCOUNT_ID"
```

> **来源：** [boto/botocore `credentials.py` L1185-1194](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/credentials.py#L1185-L1194)

<a id="aws-default-credential-chain"></a>
### AWS 默认凭证链

推荐用于生产负载，可自动从环境发现凭证。

**适用场景：**
- 带 IAM 角色的 EC2 实例。
- Lambda 函数。
- 带任务角色的 ECS 任务。
- 使用 IRSA，即服务账号 IAM 角色的 EKS Pod。
- 使用 AWS CLI 配置档案的本地开发。

**凭证链实现：**

```python
# From botocore/credentials.py lines 113-152
env_provider = EnvProvider()
container_provider = ContainerProvider()
instance_metadata_provider = InstanceMetadataProvider(
    iam_role_fetcher=InstanceMetadataFetcher(
        timeout=metadata_timeout,
        num_attempts=num_attempts,
        user_agent=session.user_agent(),
        config=imds_config,
    )
)

profile_provider_builder = ProfileProviderBuilder(session, cache=cache, region_name=region_name)
assume_role_provider = AssumeRoleProvider(
    load_config=lambda: session.full_config,
    client_creator=_get_client_creator(session, region_name),
    cache=cache,
    profile_name=profile_name,
    credential_sourcer=CanonicalNameCredentialSourcer(
        [env_provider, container_provider, instance_metadata_provider]
    ),
    profile_provider_builder=profile_provider_builder,
)

pre_profile = [
    env_provider,
    assume_role_provider,
]
profile_providers = profile_provider_builder.providers(
    profile_name=profile_name,
    disable_env_vars=disable_env_vars,
)
post_profile = [
    OriginalEC2Provider(),
    BotoProvider(),
    container_provider,
    instance_metadata_provider,
]
providers = pre_profile + profile_providers + post_profile
```

> **来源：** [boto/botocore `credentials.py` L113-152](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/credentials.py#L113-L152)

**AssumeRole 提供器：**

用于跨账号访问或角色链：

```python
# From botocore/credentials.py lines 1535-1548
class AssumeRoleProvider(CredentialProvider):
    METHOD = "assume-role"
    ROLE_CONFIG_VAR = "role_arn"
    WEB_IDENTITY_TOKE_FILE_VAR = "web_identity_token_file"
    # Credentials are considered expired (and will be refreshed) once the total
    # remaining time left until the credentials expires is less than the
    # EXPIRY_WINDOW.
    EXPIRY_WINDOW_SECONDS = 60 * 15
```

> **来源：** [boto/botocore `credentials.py` L1535-1548](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/credentials.py#L1535-L1548)

<a id="aws-sdk-implementation-details"></a>
### AWS SDK 实现详情

Phoenix 使用 `aioboto3` 异步创建 Bedrock 客户端：

```python
# Explicit credentials
session = aioboto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token,
    region_name=region_name,
)

# Default credential chain
session = aioboto3.Session(region_name=region_name)
```

> **来源：** [aio-libs/aioboto3](https://github.com/aio-libs/aioboto3/blob/37216db0083e28511c4d82931855f8af2b1b102b/aioboto3/session.py)

<a id="aws-bearer-token-authentication-unsupported"></a>
### AWS bearer token 认证（不支持）

AWS Bedrock 支持通过 `AWS_BEARER_TOKEN_BEDROCK` 环境变量进行 bearer token 认证。但由于 botocore token 解析系统的架构限制，**目前不支持显式透传 bearer token**。

<a id="the-problem"></a>
#### 问题

`aws_access_key_id`、`aws_secret_access_key`、`aws_session_token` 等凭证可显式传给 `Session()`，bearer token 却没有对应参数：

```python
# ✅ Credentials CAN be passed explicitly
session = aioboto3.Session(
    aws_access_key_id="AKIA...",
    aws_secret_access_key="secret",
    aws_session_token="token",  # Optional
)

# ❌ Bearer tokens CANNOT be passed explicitly
session = aioboto3.Session(
    bearer_token="my-bearer-token",  # No such parameter exists!
)
```

<a id="root-cause-hardwired-token-resolution"></a>
#### 根因：固定的 token 解析

botocore 在 `create_client()` 内部解析 bearer token，没有显式 token 注入点：

```python
# From botocore/session.py lines 847-1042
@with_current_context()
def create_client(
    self,
    service_name,
    region_name=None,
    # ... many parameters, but NO bearer_token parameter
):
    # ...
    auth_token = self.get_auth_token()  # <-- Hardwired call
    # ...
    client = client_creator.create_client(
        # ...
        auth_token=auth_token,  # <-- Passed internally, not configurable
    )
```

> **来源：** [boto/botocore `session.py` L847-1042](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/session.py#L847-L1042)

`get_auth_token()` 使用仅含两个提供器的 token 链：

```python
# From botocore/tokens.py lines 46-51
def create_token_resolver(session):
    providers = [
        ScopedEnvTokenProvider(session),  # Reads AWS_BEARER_TOKEN_BEDROCK
        SSOTokenProvider(session),  # Reads from SSO cache files
    ]
    return TokenProviderChain(providers=providers)
```

> **来源：** [boto/botocore `tokens.py` L46-51](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/tokens.py#L46-L51)

`ScopedEnvTokenProvider` 专门查找 `AWS_BEARER_TOKEN_{SERVICE}` 环境变量：

```python
# From botocore/utils.py lines 3616-3628
def get_token_from_environment(signing_name, environ=None):
    if not isinstance(signing_name, str) or not signing_name.strip():
        return None

    if environ is None:
        environ = os.environ
    env_var = _get_bearer_env_var_name(signing_name)
    return environ.get(env_var)


def _get_bearer_env_var_name(signing_name):
    bearer_name = signing_name.replace("-", "_").replace(" ", "_").upper()
    return f"AWS_BEARER_TOKEN_{bearer_name}"
```

> **来源：** [boto/botocore `utils.py` L3616-3628](https://github.com/boto/botocore/blob/52799594121c562b4e293bc10aef49b49b037864/botocore/utils.py#L3616-L3628)

<a id="why-this-matters"></a>
#### 影响

此限制意味着：

1. **无法接受前端 bearer token**：不能通过客户端创建流水线传入用户 token。
2. **无法在自定义提供商中存储 bearer token 以供使用**：即使保存在数据库，也无机制注入。
3. **仅支持环境变量**：只有服务端设置 `AWS_BEARER_TOKEN_BEDROCK` 才能使用。

<a id="potential-workarounds-not-recommended"></a>
#### 潜在替代方法（不推荐）

| 替代方法 | 问题 |
|------------|---------|
| 临时设置环境变量 | 并发服务端存在竞态 |
| 注入自定义 token 提供器 | 需要猴子补丁修改 botocore 内部 |
| 派生 botocore/aiobotocore | 维护负担 |

<a id="current-status"></a>
#### 当前状态

目前只有服务端环境已设置 `AWS_BEARER_TOKEN_BEDROCK` 时才支持 AWS Bedrock bearer token 认证。没有 botocore 上游修改，通过界面或 API 显式配置不可行。

---

<a id="phoenix-implementation"></a>
## Phoenix 实现

<a id="data-model"></a>
### 数据模型

Phoenix 采用带判别字段的联合类型表示认证方式：

```python
class AuthenticationMethodApiKey(BaseModel):
    model_config = ConfigDict(frozen=True, str_min_length=1, str_strip_whitespace=True)
    type: Literal["api_key"] = "api_key"
    api_key: str = Field(..., description="API key")


class AuthenticationMethodDefaultCredentials(BaseModel):
    """
    Authentication method that delegates to the SDK's default credential chain.

    For AWS: boto3 credential chain (IAM role, env vars, ~/.aws/credentials)
    For Azure: DefaultAzureCredential (Managed Identity, Azure CLI, env vars)
    """

    model_config = ConfigDict(frozen=True)
    type: Literal["default_credentials"] = "default_credentials"
```

**Azure 认证联合类型：**

```python
# Discriminated union with Pydantic
AzureOpenAIAuthenticationMethod = Annotated[
    AuthenticationMethodApiKey
    | AuthenticationMethodAzureADTokenProvider
    | AuthenticationMethodDefaultCredentials,
    Field(discriminator="type"),
]
```

**AWS 认证联合类型：**

```python
# Discriminated union with Pydantic
AWSBedrockAuthenticationMethod = Annotated[
    AWSBedrockAuthenticationMethodAccessKeys | AuthenticationMethodDefaultCredentials,
    Field(discriminator="type"),
]
```


<a id="client-factory-pattern"></a>
### 客户端工厂模式

Phoenix 使用工厂模式创建新客户端，并正确处理凭证：

**Azure OpenAI 使用 DefaultAzureCredential：**

```python
elif method.type == "default_credentials":
    # Use DefaultAzureCredential for Managed Identity, Azure CLI, env vars, etc.
    try:
        from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
    except ImportError:
        raise ImportError(
            "Azure identity package not installed. Run: pip install azure-identity"
        )
    scope = "https://cognitiveservices.azure.com/.default"
    default_cred = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(default_cred, scope)

    def create_client_with_default_cred() -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=token_provider,
            base_url=base_url,
            default_headers=merged_headers,
        )

    return create_client_with_default_cred
```


**AWS Bedrock 使用默认凭证：**

```python
elif method.type == "default_credentials":
    # Use boto3 default credential chain (IAM role, env vars, ~/.aws/credentials)
    session = aioboto3.Session(region_name=region_name)

    def create_client_with_env() -> "AbstractAsyncContextManager[BedrockRuntimeClient]":
        client_context = session.client(
            service_name="bedrock-runtime",
            endpoint_url=endpoint_url,
        )
        return _bedrock_client_with_headers(client_context, headers)

    return create_client_with_env
```


---

<a id="production-readiness-assessment"></a>
## 生产就绪评估

<a id="coverage-analysis"></a>
### 覆盖分析

| 场景 | Azure | AWS | 状态 |
|----------|-------|-----|--------|
| CLI 认证的本地开发 | ✅ `default_credentials` | ✅ `default_credentials` | 已覆盖 |
| 简单 API 密钥部署 | ✅ `api_key` | 不适用 | 已覆盖 |
| 显式服务主体 | ✅ `ad_token_provider` | ✅ `access_keys` | 已覆盖 |
| EC2/虚拟机 IAM 角色 | ✅ `default_credentials` | ✅ `default_credentials` | 已覆盖 |
| ECS/EKS 任务角色 | ✅ `default_credentials` | ✅ `default_credentials` | 已覆盖 |
| Lambda 执行角色 | ✅ `default_credentials` | ✅ `default_credentials` | 已覆盖 |
| Azure App Service 托管身份 | ✅ `default_credentials` | 不适用 | 已覆盖 |
| 用户分配托管身份 | ⚠️ 部分 | 不适用 | 待补齐 |
| 跨账号角色扮演 | 不适用 | ⚠️ 未显式提供 | 待补齐 |
| 证书认证 | ❌ 不支持 | 不适用 | 待补齐 |

<a id="gaps-and-future-considerations"></a>
### 不足和未来考虑

**1. 用户分配托管身份（Azure）**

目前 `DefaultAzureCredential` 默认使用系统分配身份。支持用户分配身份需暴露 `managed_identity_client_id`：

```python
# Would require:
DefaultAzureCredential(managed_identity_client_id="client-id-of-user-assigned-mi")
```

**2. 跨账号角色扮演（AWS）**

当前 `default_credentials` 依赖配置档案实现角色扮演。显式支持需要：

```python
# Would require STS client and role ARN:
sts_client.assume_role(
    RoleArn="arn:aws:iam::ACCOUNT:role/RoleName", RoleSessionName="phoenix-session"
)
```

**3. 自定义 scope（Azure）**

当前 scope 硬编码为 `https://cognitiveservices.azure.com/.default`。对 Azure OpenAI 正确，但其他 Azure AI 服务可能需参数化。

<a id="security-best-practices"></a>
### 安全最佳实践

| 实践 | 实现状态 |
|----------|----------------------|
| 代码中不含密钥 | ✅ 在数据库加密存储 |
| 凭证隔离 | ✅ `without_env_vars()` 防止环境变量泄漏 |
| 最小权限 | ⚠️ 用户负责，需文档 |
| 凭证轮换 | ⚠️ 支持但不强制 |
| 审计日志 | ⚠️ 未实现 |

---

<a id="future-considerations"></a>
## 未来考虑

<a id="short-term-improvements"></a>
### 短期改进

1. **添加 `managed_identity_client_id` 参数**，支持 Azure 用户分配身份。
2. **说明最小权限 IAM 策略**，用于 AWS Bedrock 访问。
3. **保存时验证凭证**，提前发现错误配置。

<a id="medium-term-improvements"></a>
### 中期改进

1. **显式角色扮演支持**，面向 AWS 跨账号场景。
2. **证书认证**，用于 Azure 服务主体。
3. **凭证健康检查**，检测即将过期或无效凭证。

<a id="long-term-considerations"></a>
### 长期考虑

1. **密钥保管库集成**，如 HashiCorp Vault、AWS Secrets Manager、Azure Key Vault。
2. **自动轮换凭证**。
3. **凭证使用审计日志**。

---

<a id="references"></a>
## 参考资料

<a id="official-documentation"></a>
### 官方文档

- [Azure Identity Python 客户端库](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)
- [DefaultAzureCredential 使用指引](https://learn.microsoft.com/en-us/azure/developer/python/sdk/authentication/credential-chains)
- [AWS SDK 凭证配置](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html)
- [AWS IAM 最佳实践](https://aws.amazon.com/iam/resources/best-practices/)

<a id="sdk-source-code"></a>
### SDK 源码

- [openai/openai-python](https://github.com/openai/openai-python) - `722d3fffb82e9150a16da01e432b70d126ca5254`
- [Azure/azure-sdk-for-python](https://github.com/Azure/azure-sdk-for-python) - `f7ef11846bd79d4cb36349b2d917a7b92f1fc03a`
- [boto/botocore](https://github.com/boto/botocore) - `52799594121c562b4e293bc10aef49b49b037864`
- [aio-libs/aioboto3](https://github.com/aio-libs/aioboto3) - `37216db0083e28511c4d82931855f8af2b1b102b`
