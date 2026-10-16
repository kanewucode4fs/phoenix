<a id="migrations"></a>

# 迁移指南

<a id="v19x-to-v2000"></a>

## v19.x 升级至 v20.0.0

从 v19.x 升级到 v20.0.0 无需手动操作，但新增的 Agent 会话持久化功能会带来一些运维影响。

<a id="agent-session-persistence"></a>

### Agent 会话持久化

与 Phoenix Agent 的对话现在会在服务器端持久化。页面重载后会话仍会保留，可在浏览器或 `phoenix-cli pxi` 终端客户端中浏览、恢复并继续对话，两者可以交替使用。终端客户端新增会话管理命令（`/new`、`/temporary`、`/sessions`、`/model`，以及用于在长会话中将较早上下文汇总为检查点的 `/compact`）。

<a id="what-changes-for-operators"></a>

### 运维人员需要关注的变化

- **新增数据库表。** 启动迁移会创建 `agent_sessions`、`agent_session_messages` 和 `agent_session_snapshots`（及其索引），用于保存对话、消息以及每个会话的 bash 状态。
- **对话受保留策略约束。** 持久化的 Agent 会话不会永久累积。默认情况下，Phoenix 会删除闲置 30 天的用户聊天，每位用户最多保留 30 条聊天，其余会在每小时清理时移除；临时聊天会在最后活动 24 小时后删除。管理员可在**设置 → 助手**中修改持久化聊天的限制（设为 0 可禁用该限制）；临时聊天的 24 小时窗口固定不变。参阅[数据保留](https://arize.com/docs/phoenix/settings/data-retention#agent-session-retention).
- **`phoenix-cli pxi` 需要匹配的服务器。** `phoenix-cli pxi` 终端客户端及其依赖的 `/v1/agent_sessions` 路由要求 Phoenix 服务器版本为 20.0.0 或更高。`phoenix-cli pxi` 20+ 会在启动时检查服务器版本，遇到旧版本时显示升级提示并退出，因此请先升级服务器，或与 CLI 同时升级。
- **旧聊天路由已弃用。** `POST /agents/server/sessions/{session_id}/chat` 仍然可用，但已在 OpenAPI 规范中标记为弃用；新集成应改用 `/v1/agent_sessions` 路由。
- **OTel `session.id` 格式已更改。** 记录的助手会话现在使用新的 `session.id` 结构，因此需要重建 `assistant_agent` 项目中基于旧结构保存的过滤器或仪表盘。

<a id="v18x-to-v1900"></a>

## v18.x 升级至 v19.0.0

<a id="built-in-oauth2-authorization-server"></a>

### 内置 OAuth2 授权服务器

启用身份验证后，Phoenix 现在会提供内置 OAuth2 授权服务器。它为 OAuth2 公共客户端提供浏览器登录，最典型的是 Phoenix CLI 中的 `px auth login`，并通过标准发现文档（`/.well-known/oauth-authorization-server` 和 `/.well-known/oauth-protected-resource`）公布自身信息。该功能默认开启，无需配置。

若运维人员不希望暴露此接口，例如部署要求仅允许 API 密钥访问，可通过新环境变量禁用：

- `PHOENIX_ENABLE_OAUTH2_AUTHORIZATION_SERVER`（默认 `true`）。设为 `false` 时，所有 `/oauth2/*` 端点及 `/.well-known/oauth-authorization-server` 发现文档都返回 `404`，受保护资源元数据也不再公布授权服务器。API 密钥、浏览器登录和基于密码的访问令牌不受影响。关闭前签发的 OAuth2 访问令牌在到期前仍有效，但其授权无法再刷新。CLI 遇到此类部署时会提示“此 Phoenix 服务器不支持 OAuth 登录；请使用 API 密钥”。禁用身份验证时，该变量无效。

保持授权服务器开启的部署还可使用以下相关配置：

- `PHOENIX_OAUTH2_DYNAMIC_CLIENT_REGISTRATION`（默认 `enabled`）控制动态客户端注册（RFC 7591）及已注册客户端可使用的重定向 URI。默认除了允许回环地址和私有用途协议，还允许 HTTPS 重定向 URI，因为实际使用的 MCP 客户端（例如 Cursor）会在标准注册中注册 HTTPS 回调，拒绝该回调会导致这些客户端无法直接使用。注册本身不会授予访问权：只有已登录用户在同意页面批准后才会签发令牌，授权码仅发送到精确匹配的已注册重定向 URI，PKCE 则将令牌交换绑定到发起流程的客户端。设为 `local_only` 可将授权码仅发送给批准用户所在机器的进程（只允许回环地址和私有用途协议），设为 `disabled` 可完全关闭动态注册。
- `PHOENIX_OAUTH2_ALLOWED_REDIRECT_HOSTS`（默认未设置）限制注册状态为 `enabled` 时 HTTPS 重定向 URI 中允许出现的主机。例如，`PHOENIX_OAUTH2_ALLOWED_REDIRECT_HOSTS=www.cursor.com` 只允许 Cursor。

CORS 说明：匿名 OAuth 接口（`/.well-known/*` 发现文档、`/oauth2/register`、`/oauth2/token` 和 `/oauth2/revoke`）使用不携带凭证的通配 CORS 响应任意来源的跨域请求，因此浏览器 OAuth 客户端无需配置即可使用。这些端点不使用 Cookie；使用 Cookie 身份验证的应用 API 仍受 `PHOENIX_ALLOWED_ORIGINS` 允许列表控制，OAuth 同意端点也仍执行严格的同源检查。

<a id="in-process-mcp-server"></a>

### 进程内 MCP 服务器

Phoenix 现在默认在 `/mcp` 挂载进程内 MCP 服务器。该端点使用 Streamable HTTP，并在启用身份验证时复用 Phoenix 现有的 Bearer 令牌验证（包括 OAuth2 授权服务器的访问令牌和 API 密钥）。禁用身份验证时，无需凭证即可访问 `/mcp`。

不希望暴露 MCP 接口的运维人员可通过以下变量禁用：

- `PHOENIX_ENABLE_MCP_SERVER`（默认 `true`）。设为 `false` 时，`/mcp` 挂载点及位于 `/.well-known/oauth-protected-resource/mcp` 的路径插入式受保护资源元数据都返回 `404`。

`/mcp` 端点现在默认提供 FastMCP 的**代码模式**工具接口：客户端看到的不再是从 `/v1` 派生的工具列表，而是发现元工具（`search`、`get_schema`、`tags`、`list_tools`）和 `execute` 工具。后者在 `pydantic-monty` 沙箱中运行模型编写的 Python，作用域内唯一的函数是 `call_tool(name, params)`。`execute` 只能调用调用者已获授权的工具，并在 Phoenix 首次使用时启动的沙箱工作子进程中运行。若要恢复此前按组限制、渐进披露的工具列表，请设置：

- `PHOENIX_ENABLE_MCP_CODE_MODE`（默认 `true`）。设为 `false` 时，`/mcp` 提供按组限制的工具接口。只有同时设置了 `PHOENIX_ENABLE_MCP_SERVER`，该变量才有效。

<a id="deployments-behind-a-reverse-proxy"></a>

### 反向代理后的部署

授权服务器和 MCP 端点对前置反向代理提出了普通 UI 与 API 流量没有的要求。直接对外暴露 Phoenix 的部署无需这些配置，其他部署应遵循：

- **设置 `PHOENIX_ROOT_URL`**（若通过子路径提供 Phoenix，还需设置 `PHOENIX_HOST_ROOT_PATH`）。OAuth2 签发者、所有发现 URL 及 MCP 401 质询均从 `PHOENIX_ROOT_URL` 派生，不使用请求的 `Host` 头，因此该设置确保部署公布的身份与客户端实际使用的 URL 一致。
- Phoenix 通过子路径提供服务时，**将主机根路径下的 `/.well-known/*` 原样转发给 Phoenix**。RFC 8414 §3 和 RFC 9728 §3.1 要求将 well-known 段放在*主机与路径之间*：若部署在 `https://example.com/phoenix`，客户端会获取 `https://example.com/.well-known/oauth-authorization-server/phoenix`；该 URL 位于主机根路径，不在代理路由到 Phoenix 的子路径中。设置 `PHOENIX_HOST_ROOT_PATH` 后，Phoenix 会为这些路径插入式文档注册匹配路由；代理只需原样转发，不要剥离或重写路径。
- **不要在匿名接口前设置代理层身份验证**：`/mcp`、`/oauth2/register`、`/oauth2/token`、`/oauth2/revoke` 和 `/.well-known/*`。OAuth 和 MCP 客户端依赖 Phoenix 自身的 `401` 响应及 `WWW-Authenticate` 头启动流程；代理若返回指向登录页或 SSO 中间页的 `302`，会使流程尚未开始便结束。这些端点无需代理验证也可安全暴露：它们不使用 Cookie，且各自验证输入（相同边界见上文 CORS 说明）。
- 在上述路径上**原样放行 `OPTIONS` 请求**。浏览器会在跨域请求前发送 `OPTIONS` 预检，规范要求预检不携带凭证；若被代理身份验证层拦截，实际请求会因含糊的 CORS 错误而失败。
- **不要缓冲 MCP 响应流，也不要使其超时。** `/mcp` 会保持长连接的 `text/event-stream` 响应，供服务器向客户端发送消息。响应缓冲（如 nginx 的 `proxy_buffering`）或过短的读写超时会悄然中断会话。
- **原样转发响应头**，尤其是 `WWW-Authenticate`、`Mcp-Session-Id` 和 `Access-Control-*` 系列。客户端会读取这三类响应头；若代理移除了用于暴露它们的 CORS 头，浏览器客户端将完全无法看到前两者。
- **保留 404 响应。** 发现客户端会探测多个候选 `/.well-known/*` URL，并依赖明确的 `404` 继续尝试下一个。代理若替换为自定义 HTML 错误页（或任何 `200` 响应），会使探测结果看起来像格式错误的发现文档，导致客户端中止，而非继续尝试。

<a id="graphql-api-keys-can-no-longer-create-api-keys"></a>

### GraphQL API 密钥不再能创建 API 密钥

截至 Phoenix 18，GraphQL 变更 `createUserApiKey` 和 `createSystemApiKey` 为向后兼容，允许通过 API 密钥验证的调用者执行：用户 API 密钥可为同一所有者签发另一个用户密钥，`ADMIN` 角色的用户密钥可签发系统密钥。这使得泄露的密钥能够在原密钥被撤销前签发长期有效的替代密钥。

从 Phoenix 19 起，这两个 GraphQL 变更会以 `Unauthorized` 错误拒绝通过 API 密钥验证的调用者，与 REST API 密钥端点（`POST /v1/user/api_keys`、`POST /v1/system/api_keys`）自引入以来执行的策略一致：

- 用户 API 密钥必须通过已验证身份的人工会话创建。
- 系统 API 密钥必须通过人工 `ADMIN` 会话或使用 `PHOENIX_ADMIN_SECRET` 创建。
- 在任一接口中，API 密钥（用户或系统）都不能创建 API 密钥。

GraphQL 模式不变，列出和撤销密钥的行为与之前完全相同，包括此前允许使用 API 密钥验证的情况。

**迁移：** 若自动化流程使用已有 API 密钥通过 GraphQL 签发新密钥，请改用以下受支持的签发方式之一：

- 在**设置 → API 密钥**中交互式创建密钥，或
- 将自动化流程验证为会话（使用用户凭证登录以获取访问令牌），或
- 对于系统密钥，使用 `PHOENIX_ADMIN_SECRET` 验证身份后调用 `POST /v1/system/api_keys`（或相应 GraphQL 变更）。

升级前创建的密钥仍然有效；仅移除了密钥创建其他密钥的能力。

<a id="v17x-to-v1800"></a>

## v17.x 升级至 v18.0.0

<a id="db-index-for-sessions-time-range"></a>

### 会话时间范围数据库索引

会话时间范围过滤器现在使用区间重叠语义（当且仅当会话在窗口内有活动时才会包含该会话）。一次迁移会重构以下索引：

- 在 `project_sessions (project_id, end_time DESC)` 上创建新过滤器依赖的复合索引 `ix_project_sessions_project_id_end_time`。
- 在实验日志表上创建四个外键索引，使删除实验或数据集不再触发顺序扫描：`ix_experiment_logs_experiment_id`、`ix_experiment_eval_logs_experiment_run_id`、`ix_experiment_eval_logs_dataset_evaluator_id` 和 `ix_experiment_task_logs_dataset_example_id`。
- 在七张表上创建 `user_id` 索引；这些表此前具有指向 `users` 且未建索引的 `ON DELETE SET NULL` 外键，因此删除用户将不再逐一顺序扫描：`span_annotations`、`trace_annotations`、`document_annotations`、`project_session_annotations`、`datasets`、`dataset_versions` 和 `experiments`。
- 删除七个冗余单列索引：其中五个索引的查询已由现有唯一索引的前导列支持（`ix_project_annotation_configs_project_id`、`ix_prompts_prompt_labels_prompt_label_id`、`ix_token_prices_model_id`、`ix_dataset_examples_dataset_id`、`ix_dataset_evaluators_dataset_id`）；`ix_dataset_examples_external_id` 没有查询单独使用它，`external_id` 查询总是限定到数据集，并由唯一索引 `(dataset_id, external_id)` 支持；`ix_project_sessions_end_time` 则由新复合索引替代（先创建再删除，因此不会出现缺少 end_time 索引的窗口）。

**滚动部署：** 所有索引创建和删除都会遵循 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true`（见下文 [v12.x 升级至 v13.0.0](#v12x-to-v1300)）。`project_sessions` 表每个会话仅占一行，因此复合索引构建很快，通常无需预先创建。迁移会在删除任何索引前验证它创建的每个索引：若先前的并发构建失败并遗留 INVALID 索引，迁移会失败并提供恢复说明（使用 `DROP INDEX CONCURRENTLY IF EXISTS <index name>` 删除无效索引后重试），而不是继续执行。

<a id="v16x-to-v1700"></a>

## v16.x 升级至 v17.0.0

<a id="agent-assistant-pxi"></a>

### Agent 助手（PXI）

Phoenix v17 推出应用内助手 **PXI**，无需离开当前页面即可帮助你调查追踪、迭代提示词并浏览 Phoenix。

若要为整个部署关闭 PXI，请设置：

```shell
PHOENIX_DISABLE_AGENT_ASSISTANT=true
```

<a id="v15x-to-v1600"></a>

## v15.x 升级至 v16.0.0

<a id="sandbox-provider-allowlist-phoenix_allowed_sandbox_providers"></a>

### 沙箱提供商允许列表（`PHOENIX_ALLOWED_SANDBOX_PROVIDERS`）

新增可选环境变量 `PHOENIX_ALLOWED_SANDBOX_PROVIDERS`，用于限制执行代码评估器时可用的沙箱提供商系列。

*未设置时，所有提供商均可用。设为 `NONE` 可禁用所有沙箱提供商。*

要限制可用沙箱集合，请将变量设为以逗号分隔的系列名称列表：

```shell
PHOENIX_ALLOWED_SANDBOX_PROVIDERS=WASM,DENO
```

可接受的值：`WASM`、`E2B`、`DAYTONA`、`VERCEL`、`DENO`、`MODAL`（不区分大小写）。列出某个系列即包含其所有语言变体，例如 `VERCEL` 同时包含 `VERCEL_PYTHON` 和 `VERCEL_TYPESCRIPT`。

<a id="sandbox-and-code-evaluator-permissions"></a>

### 沙箱与代码评估器权限

v16.0.0 新增沙箱配置和代码评估器 API 接口。启用身份验证时，对这些接口的访问由用户角色控制：

| API 接口 | 操作 | 管理员 | 成员 | 查看者 |
| --- | --- | --- | --- | --- |
| 查看代码评估器源码 | 读 | ✅ | ✅ | ✅ |
| 查看代码评估器标识 | 读 | ✅ | ✅ | ✅ |
| 查看安全沙箱标识 | 读 | ✅ | ✅ | ✅ |
| 查看后端能力元数据 | 读 | ✅ | ✅ | ✅ |
| 查看沙箱配置值 | 读 | ✅ | ✅ | ✅ |
| 查看提供商配置值 | 读 | ✅ | ✅ | ✅ |
| 创建沙箱配置 | 写 | ✅ | ❌ | ❌ |
| 更新沙箱配置 | 写 | ✅ | ❌ | ❌ |
| 删除沙箱配置 | 写 | ✅ | ❌ | ❌ |
| 更新沙箱提供商 | 写 | ✅ | ❌ | ❌ |
| 创建代码评估器 | 写 | ✅ | ✅ | ❌ |
| 局部更新代码评估器 / 重新绑定沙箱 | 写 | ✅ | ✅ | ❌ |
| 追加代码评估器版本 | 写 | ✅ | ✅ | ❌ |
| 创建 / 更新数据集代码评估器 | 写 | ✅ | ✅ | ❌ |
| 预览使用沙箱的代码评估器 | 写 | ✅ | ✅ | ❌ |

只有管理员可配置沙箱。成员和管理员可编写并预览代码评估器，查看者不可。所有读取接口均不受角色限制。禁用身份验证时，不执行角色检查。

<a id="v14x-to-v1500"></a>

## v14.x 升级至 v15.0.0

从 v14.x 升级到 v15.0.0 无需任何操作。

<a id="v13x-to-v1400"></a>

## v13.x 升级至 v14.0.0

<a id="phoenix-server-cli-phoenix--python--m-phoenixservermain"></a>

### Phoenix 服务器 CLI（`phoenix` / `python -m phoenix.server.main`）

CLI 现在要求**子命令在前**：先选择 `serve` 或 `db`，再传入对应命令的选项。在 v13.x 中，很多标志可位于子命令**之前**（例如在 `serve` 前指定 `--dev` 和 `--dev-vite-port`）；现在必须放在子命令**之后**。

**修改前：**

```shell
python -m phoenix.server.main --dev --dev-vite-port 5173 serve
phoenix --host 0.0.0.0 --port 6006 serve
```

**修改后：**

```shell
python -m phoenix.server.main serve --dev --dev-vite-port 5173
phoenix serve --host 0.0.0.0 --port 6006
```

在需要数据库的子命令上传入 `--database-url`（或使用 `PHOENIX_SQL_DATABASE_URL` / 默认值）。

```shell
python -m phoenix.server.main serve --database-url "postgresql://..."
python -m phoenix.server.main db migrate --database-url "postgresql://..."
```

`db migrate` 仍为双词子命令，没有变化：`python -m phoenix.server.main db migrate`（或 `phoenix db migrate`）。

顶层 `--help` 只显示全局用法；查看子命令选项请使用 `phoenix serve --help` 或 `phoenix db migrate --help`。

<a id="postgresql-driver-psycopg-removed"></a>

### PostgreSQL 驱动：移除 `psycopg`

已移除 `psycopg` 驱动。Phoenix 的运行时查询和迁移现在均只使用 `asyncpg` 作为 PostgreSQL 驱动。若仅为 Phoenix 安装了 `psycopg`，可将其卸载。

`pg` 扩展依赖不再包含 `psycopg`：

```shell
pip install arize-phoenix[pg]  # 仅安装 asyncpg
```

无需修改配置，`PHOENIX_SQL_DATABASE_URL` 仍使用相同的 `postgresql://` 连接字符串。

<a id="legacy-client-removed"></a>

### 移除旧版客户端

旧版 `phoenix.session.client.Client`（通过 `px.Client()` 访问）已移除。所有客户端交互现在均通过 `arize-phoenix-client` 包进行。

```shell
pip install arize-phoenix-client
```

**修改前：**

```python
import phoenix as px

client = px.Client(endpoint="http://localhost:6006")
```

**修改后：**

```python
from phoenix.client import Client

client = Client(base_url="http://localhost:6006")
```

构造参数 `endpoint` 已更名为 `base_url`。若省略，则使用环境变量或 `http://localhost:6006`。`phoenix.session.client` 模块已不存在，导入它会引发 `ModuleNotFoundError`。

<a id="client-method-changes"></a>

### 客户端方法变更

新客户端将方法组织在资源命名空间（`.spans`、`.datasets`、`.experiments`）下，不再平铺在客户端对象上。返回类型也已变化：新客户端使用从 OpenAPI 模式生成的 TypedDict，而非自定义 dataclass。

<a id="spans-and-traces"></a>

#### Span 与追踪

| 旧版（`px.Client()`）             | 新版（`phoenix.client.Client()`）                 |
| :--------------------------------- | :---------------------------------------------- |
| `client.get_spans_dataframe()`     | `client.spans.get_spans_dataframe()`            |
| `client.query_spans(query)`        | `client.spans.get_spans_dataframe(query=query)` |
| `client.get_evaluations()`         | `client.spans.get_span_annotations()`           |
| `client.log_evaluations(evals)`    | `client.spans.log_span_annotations(...)`        |
| `client.log_traces(trace_dataset)` | `client.spans.log_spans(...)`                   |

`query_spans` 方法接受作为位置参数的 `SpanQuery` 对象，可能返回单个 DataFrame 或列表。新的 `get_spans_dataframe` 接受一个 `query` 关键字参数，始终返回单个 DataFrame。若此前传入多个查询，请改为对每个查询分别调用一次 `get_spans_dataframe`，再用 pandas 合并结果。

<a id="datasets"></a>

#### 数据集

| 旧版（`px.Client()`）                    | 新版（`phoenix.client.Client()`）             |
| :---------------------------------------- | :------------------------------------------ |
| `client.get_dataset(id=..., name=...)`    | `client.datasets.get_dataset(...)`          |
| `client.get_dataset_versions(dataset_id)` | `client.datasets.get_dataset_versions(...)` |
| `client.upload_dataset(...)`              | `client.datasets.create_dataset(...)`       |

旧版 `get_dataset` 返回 `phoenix.experiments.types.Dataset` dataclass。新客户端返回具有相同概念字段（`.id`、`.examples`、`.version_id`）的 `Dataset` 对象，但其底层由生成的 API 模式中的 TypedDict 支持。

<a id="evaluations-to-annotations"></a>

#### 从评估改为标注

此前称为“评估”的概念在新客户端中统一称为“标注”。`SpanEvaluations` 和 `log_evaluations` 的替代方式如下：

**修改前：**

```python
from phoenix.trace import SpanEvaluations

px.Client().log_evaluations(SpanEvaluations(eval_name="Hallucination", dataframe=results_df))
```

**修改后：**

```python
from phoenix.client import Client

Client().spans.log_span_annotations_dataframe(
    dataframe=results_df,
    annotation_name="Hallucination",
    annotator_kind="LLM",
)
```

<a id="experiments"></a>

### 实验

实验 API 已从 `phoenix.experiments` 迁移到 `phoenix.client.experiments`。任务函数中使用的 `Example` 类型现在来自生成的 API 类型。

**修改前：**

```python
from phoenix.experiments.types import Example
from phoenix.experiments.evaluators import create_evaluator
```

**修改后：**

```python
from phoenix.client.__generated__.v1 import DatasetExample as Example
from phoenix.client.experiments import create_evaluator
```

`run_experiment` 和 `evaluate_experiment` 现在要求以关键字参数传入 `dataset`、`task` 和 `experiment`：

```python
from phoenix.client.experiments import run_experiment, evaluate_experiment

experiment = run_experiment(dataset=dataset, task=task, evaluators=[...])
experiment = evaluate_experiment(experiment=experiment, evaluators=[...])
```

<a id="removed-helper-functions"></a>

### 移除辅助函数

预定义查询辅助函数 `get_retrieved_documents`、`get_qa_with_reference` 和 `get_called_tools`（来自 `phoenix.trace.dsl.helpers`）已移除。请直接将 `SpanQuery` 与 `client.spans.get_spans_dataframe(query=...)` 配合使用。[从 Span 提取数据](https://arize.com/docs/phoenix/tracing/how-to-tracing/importing-and-exporting-traces/extract-data-from-spans)文档中的示例已更新。

<a id="removed-top-level-convenience-functions"></a>

### 移除顶层便捷函数

- `px.Client` ——改用 `from phoenix.client import Client`
- `px.log_evaluations(...)` ——改用 `client.spans.log_span_annotations(...)`
- `session.query_spans(...)` ——改用 `client.spans.get_spans_dataframe(...)`
- `session.get_evaluations(...)` ——改用 `client.spans.get_span_annotations(...)`

<a id="v1evaluations-endpoint-removed"></a>

### 移除 `/v1/evaluations` 端点

已移除 `POST /v1/evaluations` 和 `GET /v1/evaluations` REST 端点。请根据评估类型选择对应的标注 API 替代：

<a id="ingestion-post-v1evaluations-replacements"></a>

#### 写入（`POST /v1/evaluations` 的替代接口）

| 评估类型 | SDK 替代接口                                        | REST 替代接口                  |
| :-------------- | :----------------------------------------------------- | :-------------------------------- |
| span            | `client.spans.log_span_annotations_dataframe(...)`     | `POST /v1/span_annotations`       |
| trace           | `client.traces.log_trace_annotations_dataframe(...)`   | `POST /v1/trace_annotations`      |
| document        | `client.spans.log_document_annotations_dataframe(...)` | `POST /v1/document_annotations`   |

<a id="retrieval-get-v1evaluations-replacement"></a>

#### 读取（`GET /v1/evaluations` 的替代接口）

旧版 `GET /v1/evaluations` 仅返回 Span 标注，其替代方法为 `client.spans.get_span_annotations(...)`。

> **注意：** 可以通过 `GET /projects/{id}/trace_annotations` 读取追踪标注，但旧评估端点并不提供此功能，这是新增能力，并非直接替代。

**修改前：**

```python
from phoenix.trace import SpanEvaluations
import phoenix as px

px.Client().log_evaluations(SpanEvaluations(eval_name="Hallucination", dataframe=results_df))
```

**修改后（Span 标注）：**

```python
from phoenix.client import Client

Client().spans.log_span_annotations_dataframe(
    dataframe=results_df,
    annotation_name="Hallucination",
    annotator_kind="LLM",
)
```

**修改后（追踪标注）：**

```python
from phoenix.client import Client

Client().traces.log_trace_annotations_dataframe(
    dataframe=results_df,
    annotation_name="Hallucination",
    annotator_kind="LLM",
)
```

**修改后（文档标注）：**

```python
from phoenix.client import Client

Client().spans.log_document_annotations_dataframe(
    dataframe=results_df,
    annotation_name="Relevance",
    annotator_kind="LLM",
)
```

**移除依赖：** `protobuf` 不再是 Phoenix 服务器的直接依赖（仍通过 OpenTelemetry gRPC 包作为传递依赖存在）。

<a id="v12x-to-v1300"></a>

## v12.x 升级至 v13.0.0

<a id="db-index-for-session-id"></a>

### 会话 ID 数据库索引

迁移会在 `spans.attributes` 上新增会话 ID 的部分索引。在 MacBook Pro 上，估计每 100 GiB 数据需要约 200 秒。云环境可能需要更长时间，取决于实例规格和 I/O 吞吐量。

**滚动部署：** 若新实例启动并运行迁移时，已有 Phoenix 实例仍在处理流量，默认的 `CREATE INDEX` 会获取表锁并阻塞旧实例的写入。为避免此问题，请在启动新实例前设置以下环境变量：

```
PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true
```

这会使用 `CREATE INDEX CONCURRENTLY`，避免表锁，但耗时约为原来的 2～3 倍。新实例仍需等待索引构建完成才能完成启动。

**大型 PostgreSQL 数据库（数百 GiB 以上）：** 对于非常大的 `spans` 表，即使使用 `CONCURRENTLY` 也可能需要数小时。要使迁移立即完成，可在升级前（旧版本仍运行时）预先创建同名空操作索引：

步骤 1——创建空操作索引（立即完成，无需扫描表）：

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_spans_session_id
ON spans ((attributes #>> '{session,id}'))
WHERE false;
```

步骤 2——升级 Phoenix。迁移中的 `IF NOT EXISTS` 发现该索引名后会跳过创建。

步骤 3——在方便时回填真实索引（应用运行期间即可执行）：

```sql
DROP INDEX CONCURRENTLY IF EXISTS ix_spans_session_id;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_spans_session_id
ON spans (((attributes #>> '{session,id}')::varchar))
WHERE ((attributes #>> '{session,id}')::varchar) IS NOT NULL;
```

注意：在 PostgreSQL 中，索引使用 `#>>` 路径运算符（如 `attributes #>> '{session,id}'`）。使用链式箭头运算符（`attributes -> 'session' ->> 'id'`）的查询无法匹配该索引。Phoenix 内置查询层始终使用 `#>>` 形式，因此这仅影响直接对数据库运行的自定义 SQL 查询。

### Azure OpenAI v1 API

Azure OpenAI 集成现在使用 OpenAI v1 API，通过取消显式 API 版本配置来简化设置。不再需要 `api_version` 参数，版本现在由 v1 API 端点隐式处理。

此变更要求 `openai>=2.14.0`。

**参考资料**：

- [Azure OpenAI API 版本生命周期](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/api-version-lifecycle)
- [从 Azure AI Inference 迁移到 OpenAI SDK](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/model-inference-to-openai-migration)

<a id="aws-bedrock-async-client"></a>

### AWS Bedrock 异步客户端

AWS Bedrock 集成现在使用 `aioboto3` 替代 `boto3`，实现完全异步的客户端操作。若为支持 Bedrock 安装了 `boto3`，应改为安装 `aioboto3`：

```shell
pip install aioboto3
```

<a id="inferences-dimensions-embeddings-and-pointcloud-umap"></a>

### 推断、维度、嵌入与点云（UMAP）

**破坏性变更：** Phoenix 已移除模型推断、维度、嵌入及点云（UMAP）可视化，同时移除了对应 GraphQL 和 REST API。UI 不再包含 `/model`、`/dimensions` 或 `/embeddings` 路由。

<a id="v1100-to-v1200"></a>

## v11.0.0 升级至 v12.0.0

插桩辅助工具正迁移到 `openinference-instrumentation`。

修改前：

```python
from phoenix.trace import using_project

with using_project(project_name="change-project"):
    ...
```

修改后：

```python
# openinference-instrumentation>=0.1.38
from openinference.instrumentation import dangerously_using_project

with dangerously_using_project(project_name="change-project"):
    ...
```

<a id="postgresql-connection-environment-variables"></a>

### PostgreSQL 连接环境变量

**破坏性变更**：不再支持在 `PHOENIX_POSTGRES_HOST` 中指定端口号。

**修改前**：

```shell
export PHOENIX_POSTGRES_HOST=localhost:5432
```

**修改后**：

```shell
export PHOENIX_POSTGRES_HOST=localhost
export PHOENIX_POSTGRES_PORT=5432
```

**影响**：若此前在 `PHOENIX_POSTGRES_HOST` 中包含端口（如 `localhost:5432`），现在必须将主机和端口分别设置到各自的环境变量中。

<a id="v1000-to-v1100"></a>

## v10.0.0 升级至 v11.0.0

本次发布的全部变更都包含在一组新表中。祝升级顺利！

<a id="v9x-to-v1000"></a>

## v9.x 升级至 v10.0.0

本次发布会更新数据库中的 `users` 表，预计迁移会很快完成。

本次发布没有其他破坏性变更。

<a id="v8x-to-v900"></a>

## v8.x 升级至 v9.0.0

本次发布将 Span 和追踪上的所有标注迁移到支持每个实体（追踪、Span）具有多个标注值的结构，同时修改表约束。由于迁移会处理已有数据，完整迁移记录可能需要一些时间。Phoenix 会在启动时迁移数据，因此服务器启动可能较慢（取决于数据量）。请在服务能够接受短暂停机时部署 v9.0。

Phoenix 9.0 还包含项目级保留策略。默认情况下，已有项目会使用无限期保留的默认策略，因此数据不会受到影响。

> [!CAUTION]
> 此次版本升级会将所有标注迁移到新格式。迁移运行期间不要重启服务器，请确保迁移已完成。迁移中途重启服务器可能使数据库进入需要人工干预的状态。

<a id="v6x-to-v700"></a>

## v6.x 升级至 v7.0.0

<a id="python-script-to-populate-database-table-for-sessions"></a>

### 填充会话数据库表的 Python 脚本

<a id="option-i-run-the-script-via-the-installed-module"></a>

#### 方案一：通过已安装模块运行脚本

此方案假定 Phoenix 应用已执行数据库升级迁移，即会话新表已创建。手动执行升级迁移的方法见方案二。

> [!NOTE]
> 若使用 PostgreSQL 数据库，需通过 `pip install arize-phoenix[pg]` 安装 postgres 扩展依赖。

```shell
python -m phoenix.db.migrations.data_migration_scripts.populate_project_sessions
```

<a id="option-ii-run-the-script-from-the-repository-and-apply-the-up-migration-manually"></a>

#### 方案二：从仓库运行脚本（并手动执行升级迁移）。

步骤 1：克隆 Phoenix 仓库。

```shell
git clone git@github.com:Arize-ai/phoenix.git
```

步骤 2：切换到 `alembic.ini` 所在目录。

```shell
cd phoenix/src/phoenix/db/
```

步骤 3：运行 `alembic` 执行数据库 `up` 迁移，创建会话新表。

```shell
alembic upgrade head
```

步骤 4：运行脚本，根据 Span 填充会话表。

```shell
python migrations/data_migration_scripts/populate_project_sessions.py
```

<a id="environment-variables-used-by-the-script"></a>

#### 脚本使用的环境变量

SQLite 示例

```shell
export PHOENIX_SQL_DATABASE_URL=sqlite:////phoenix.db
```

PostgreSQL 示例

```shell
export PHOENIX_SQL_DATABASE_URL=postgresql://localhost:5432/postgres?username=postgres&password=postgres
```

对于 PostgreSQL，还可通过环境变量 `PHOENIX_SQL_DATABASE_SCHEMA` 设置模式。

<a id="v4x-to-v500"></a>

## v4.x 升级至 v5.0.0

Phoenix 5 引入了身份验证。默认禁用身份验证，Phoenix 的运行方式与旧版本完全一致。Phoenix 的身份验证设计尽可能灵活，可逐步采用。

启用身份验证后，所有 API 和 UI 访问都需要凭证或 API 密钥。因此会有一定停机时间，请提前规划。

Phoenix 5 还将插桩与 Phoenix 包完全解耦。所有插桩都应通过 OpenInference 包安装和运行。这样可提高插桩灵活性，并让 Phoenix 专注于核心功能。

<a id="enabling-authentication"></a>

### 启用身份验证

只需为部署设置以下两个环境变量即可开始：

```shell
export PHOENIX_ENABLE_AUTH=True
export PHOENIX_SECRET=a-sufficiently-long-secret
```

设置这些环境变量后，Phoenix 会初始化管理员登录，整个服务器都将受到保护。以管理员身份登录并创建供应用使用的系统密钥。所有 API 密钥均应使用 `Bearer` 方案，通过 `Authorization` 头添加到请求中。

更多详情请参阅[身份验证配置指南](https://arize.com/docs/phoenix/setup/authentication).

<a id="migrating-to-openinference"></a>

### 迁移到 OpenInference

若使用 Phoenix 的 `phoenix.trace` 模块为 LlamaIndex、LangChain 或 OpenAI 插桩，需要迁移到 OpenInference。OpenInference 是一组独立的包，为 Phoenix 提供插桩功能。Phoenix 5 不再支持从 `phoenix.trace` 模块为 LlamaIndex 或 LangChain 插桩。

Phoenix 现在包含 `phoenix.otel` 模块，用于简化 OpenTelemetry 配置。详情见 [`phoenix.otel` 文档](https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/setup-tracing-python)。

**修改前**

```python
from phoenix.trace.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()
```

**修改后**

```python
from openinference.instrumentation.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
```

支持的插桩完整列表见 [OpenInference](https://github.com/Arize-ai/openinference)

<a id="v3x-to-v400"></a>

## v3.x 升级至 v4.0.0

<a id="migrating-from-legacy-phoenixdataset-to-phoenixinferences"></a>

### 从旧版 `phoenix.Dataset` 迁移到 `phoenix.Inferences`

- `phoenix.Dataset` 已更名为 `phoenix.Inferences`
- `phoenix.ExampleDataset` 已更名为 `phoenix.ExampleInferences`
- 其他所有方法及相关函数和类仍位于 `phoenix` 命名空间下

<a id="old"></a>

#### 旧版

```python
from phoenix import Dataset, ExampleDataset
```

<a id="new"></a>

#### 新版

```python
from phoenix import Inferences, ExampleInferences
```

<a id="migrating-from-phoenixexperimentalevals-to-phoenixevals"></a>

## 从 `phoenix.experimental.evals` 迁移到 `phoenix.evals`

- Phoenix 已将 `evals` 模块移出实验阶段，现在可作为独立扩展依赖安装。

<a id="installing-and-using-the-evals-module"></a>

### 安装和使用 `evals` 模块

<a id="old-1"></a>

#### 旧版

```shell
pip install arize-phoenix[experimental]
```

```python
from phoenix.experimental.evals import OpenAIModel
from phoenix.experimental.evals import llm_classify

model = OpenAIModel()
```

<a id="new-1"></a>

#### 新版

```shell
pip install arize-phoenix[evals]
```

```python
from phoenix.evals import OpenAIModel
from phoenix.evals import llm_classify
```

<a id="token-counting-has-been-removed-evals"></a>

### `evals` 已移除 Token 计数

<a id="old-2"></a>

#### 旧版

```python
from phoenix.experimental.evals import OpenAIModel
from phoenix.experimental.evals import processing  # phoenix.evals 不再支持

model = OpenAIModel()
model.max_context_size  # phoenix.evals 不再支持
model.get_token_count_from_messages(...)  # phoenix.evals 不再支持
model.get_tokens_from_text(...)  # phoenix.evals 不再支持
model.get_text_from_tokens(...)  # phoenix.evals 不再支持
```

<a id="baseevalmodel-has-been-renamed-to-basemodel"></a>

### `BaseEvalModel` 已更名为 `BaseModel`

为 Phoenix 实现自定义模型封装时，请注意基类已更名。

<a id="old-3"></a>

#### 旧版

```python
from phoenix.experimental.evals.models import BaseEvalModel  # 已更名为 BaseModel
```

<a id="new-2"></a>

#### 新版

```python
from phoenix.evals.models import BaseModel
```

<a id="some-modules-in-phoenixevals-have-been-relocated-and-renamed"></a>

### `phoenix.evals` 中的部分模块已迁移并更名

<a id="old-4"></a>

#### 旧版

```python
from phoenix.experimental.evals.functions import classify, generate
from phoenix.experimental.evals.templates import default_templates, template
```

<a id="new-3"></a>

#### 新版

```python
from phoenix.evals import classify, generate
from phoenix.evals import default_templates, templates
```

<a id="v2x-to-v300"></a>

## v2.x 升级至 v3.0.0

- **v3.0.0**——Phoenix 现在仅使用 [OpenInference](https://github.com/Arize-ai/openinference) 进行插桩。OpenInference 使用 OpenTelemetry Protocol 向收集器发送追踪。

<a id="openai-tracing"></a>

### OpenAI 追踪

<a id="phoenixtracetracertracer-is-defunct-and-should-be-removed"></a>

#### `phoenix.trace.tracer.Tracer` 已失效，应移除。

<a id="old-v2x"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.exporter import HttpExporter  # 不再需要
from phoenix.trace.openai import OpenAIInstrumentor
from phoenix.trace.tracer import Tracer  # 不再支持

tracer = Tracer(exporter=HttpExporter())  # 不再支持
OpenAIInstrumentor(tracer).instrument()  # 不再支持 tracer 参数
```

<a id="new-v300"></a>

##### 新版 (v3.0.0)

```python
from phoenix.trace.openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument()
```

---

<a id="endpoint-should-be-configured-via-environment-variables-phoenix_host-phoenix_port-or-phoenix_collector_endpoint"></a>

#### 应通过环境变量 `PHOENIX_HOST`、`PHOENIX_PORT` 或 `PHOENIX_COLLECTOR_ENDPOINT` 配置端点。

<a id="old-v2x-1"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.exporter import HttpExporter  # 不再需要
from phoenix.trace.openai import OpenAIInstrumentor
from phoenix.trace.tracer import Tracer  # 不再支持

tracer = Tracer(exporter=HttpExporter(port=12345))  # 不再支持
OpenAIInstrumentor(tracer).instrument()  # 不再支持 tracer 参数
```

<a id="new-v300-1"></a>

##### 新版 (v3.0.0)

```python
import os
from phoenix.trace.openai import OpenAIInstrumentor

os.environ["PHOENIX_PORT"] = "12345"
OpenAIInstrumentor().instrument()
```

---

<a id="calling-get_spans-on-a-tracer-is-no-longer-supported-use-pxclient-to-get-the-spans-as-a-dataframe-from-phoenix"></a>

#### 不再支持在追踪器上调用 `.get_spans()`。请使用 `px.Client()` 从 Phoenix 获取 DataFrame 格式的 Span。

<a id="old-v2x-2"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.trace_dataset import TraceDataset  # 不再需要
from phoenix.trace.tracer import Tracer  # 不再支持

tracer = Tracer()  # 不再支持
TraceDataset.from_spans(tracer.get_spans())  # 不再支持
```

<a id="new-v300-2"></a>

##### 新版 (v3.0.0)

```python
import phoenix as px

px.Client().get_spans_dataframe()
```

---

<a id="llamaindex-tracing"></a>

### LlamaIndex 追踪

<a id="the-standard-way-of-instrumenting-your-llamaindex-application-remains-the-same-between-2x-and-3x"></a>

#### 在 2.x 和 3.x 中，为 LlamaIndex 应用插桩的标准方式保持一致：

```python
from llama_index import set_global_handler

set_global_handler("arize_phoenix")
```

---

<a id="user-should-not-pass-phoenix-handler-to-a-callback-manager-use-the-set_global_handler-method-above"></a>

#### 不要将 Phoenix 处理器传给回调管理器。请使用上方的 `set_global_handler` 方法。

```python
from llama_index.callbacks import CallbackManager  # 不再需要
from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler  # 不再支持

callback_handler = OpenInferenceTraceCallbackHandler()  # 不再支持
CallbackManager(handlers=[callback_handler])  # 不再支持
```

---

<a id="endpoint-should-be-configured-via-environment-variables-phoenix_host-phoenix_port-or-phoenix_collector_endpoint-1"></a>

#### 应通过环境变量 `PHOENIX_HOST`、`PHOENIX_PORT` 或 `PHOENIX_COLLECTOR_ENDPOINT` 配置端点。

<a id="old-v2x-3"></a>

##### 旧版 (v2.x)

```python
from llama_index import set_global_handler
from phoenix.trace.exporter import HttpExporter  # 不再需要

exporter = HttpExporter(host="127.0.0.1", port=6007)  # 不再支持
set_global_handler("arize_phoenix", exporter=exporter)
```

<a id="new-v300-3"></a>

#### 新版 (v3.0.0)

```python
import os
from llama_index import set_global_handler

os.environ["PHOENIX_HOST"] = "127.0.0.1"
os.environ["PHOENIX_PORT"] = "6007"
set_global_handler("arize_phoenix")
```

---

<a id="calling-get_spans-on-a-handler-is-no-longer-supported-use-pxclient-to-get-the-spans-as-a-dataframe-from-phoenix"></a>

#### 不再支持在处理器上调用 `.get_spans()`。请使用 `px.Client()` 从 Phoenix 获取 DataFrame 格式的 Span。

<a id="old-v2x-4"></a>

#### 旧版 (v2.x)

```python
from phoenix.trace.trace_dataset import TraceDataset  # 不再需要
from phoenix.trace.llama_index import OpenInferenceTraceCallbackHandler  # 不再支持

handler = OpenInferenceTraceCallbackHandler()  # 不再支持
TraceDataset.from_spans(handler.get_spans())  # 不再支持 .get_spans()
```

<a id="new-v300-4"></a>

##### 新版 (v3.0.0)

```python
import phoenix as px

px.Client().get_spans_dataframe()
```

---

<a id="langchain-tracing"></a>

### LangChain 追踪

<a id="phoenixtracelangchainopeninferencetracer-is-defunct-and-should-be-removed"></a>

#### `phoenix.trace.langchain.OpenInferenceTracer` 已失效，应移除。

<a id="old-v2x-5"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.langchain import LangChainInstrumentor, OpenInferenceTracer

tracer = OpenInferenceTracer()  # 不再支持
LangChainInstrumentor(tracer).instrument()  # 不再支持 tracer 参数
```

<a id="new-v300-5"></a>

##### 新版 (v3.0.0)

```python
from phoenix.trace.langchain import LangChainInstrumentor

LangChainInstrumentor().instrument()
```

---

<a id="endpoint-should-be-configured-via-environment-variables-phoenix_host-phoenix_port-or-phoenix_collector_endpoint-2"></a>

#### 应通过环境变量 `PHOENIX_HOST`、`PHOENIX_PORT` 或 `PHOENIX_COLLECTOR_ENDPOINT` 配置端点。

<a id="old-v2x-6"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.exporter import HttpExporter  # 不再需要
from phoenix.trace.langchain import LangChainInstrumentor, OpenInferenceTracer

tracer = OpenInferenceTracer(exporter=HttpExporter(port=12345))  # 不再支持
LangChainInstrumentor(tracer).instrument()
```

<a id="new-v300-6"></a>

##### 新版 (v3.0.0)

```python
from phoenix.trace.langchain import LangChainInstrumentor

os.environ["PHOENIX_PORT"] = "12345"
LangChainInstrumentor().instrument()
```

---

<a id="calling-get_spans-on-a-tracer-is-no-longer-supported-use-pxclient-to-get-the-spans-as-a-dataframe-from-phoenix-1"></a>

#### 不再支持在追踪器上调用 `.get_spans()`。请使用 `px.Client()` 从 Phoenix 获取 DataFrame 格式的 Span。

<a id="old-v2x-7"></a>

##### 旧版 (v2.x)

```python
from phoenix.trace.trace_dataset import TraceDataset  # 不再需要
from phoenix.trace.langchain import OpenInferenceTracer  # 不再支持

tracer = OpenInferenceTracer()  # 不再支持
TraceDataset.from_spans(tracer.get_spans())  # 不再支持 .get_spans()
```

<a id="new-v300-7"></a>

##### 新版 (v3.0.0)

```python
import phoenix as px

px.Client().get_spans_dataframe()
```

<a id="v0x-to-v100"></a>

## v0.x 升级至 v1.0.0

- **v1.0.0**——Phoenix 现在仅支持 `openai>=1.0.0` SDK。若使用较旧的 OpenAI SDK，可继续使用 `arize-phoenix==0.1.1`。不过，建议升级到最新版本的 OpenAI SDK，因为其中包含许多改进。若将 Phoenix 与 LlamaIndex 和 LangChain 一起使用，还需将这些包升级到支持 OpenAI `1.0.0` SDK 的版本（`llama-index>=0.8.64`、`langchain>=0.0.334`）。
