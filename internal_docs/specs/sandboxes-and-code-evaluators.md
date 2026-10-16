<a id="sandboxes-and-code-evaluators"></a>

# 沙箱与代码评估器

<a id="table-of-contents"></a>

## 目录

| # | 章节 | 重点 |
|---|---|---|
| 1 | [执行摘要](#executive-summary) | 构建内容及原因 |
| 2 | [架构](#architecture) | 适配器、会话管理器、运行器 |
| 3 | [数据模型](#data-model) | 模式与可辨识联合类型 |
| 4 | [沙箱后端](#sandbox-backends) | 六种适配器及其取舍 |
| 5 | [会话管理器](#session-manager) | 池化、淘汰、重新绑定 |
| 6 | [代码评估器运行器](#code-evaluator-runner) | 执行框架、围栏协议、追踪 |
| 7 | [设计决策](#design-decisions) | 主要设计选择及依据 |
| 8 | [安全与隔离](#security--isolation) | 密钥、脱敏、SSRF、允许列表 |
| 9 | [注意事项](#caveats) | 各后端差异及已知限制 |
| 10 | [后续考虑](#future-considerations) | 暂缓的内容 |
| — | [附录：关键常量](#appendix-key-constants) | 配置值 |
| — | [附录：文件参考](#appendix-file-references) | 代码位置 |

---

<a id="executive-summary"></a>

## 执行摘要

<a id="what-we-built"></a>

### 构建了什么

两个相互配合的功能在 [#13290](https://github.com/Arize-ai/phoenix/pull/13290) 中一同发布（2026-05-21 合并）：

**代码评估器**：在 `LLM` 和 `BUILTIN` 之外新增一种评估器。用户可直接在 Phoenix 界面中用 Python 或 TypeScript 编写 `evaluate(...)` 函数，将其附加到数据集，由 Phoenix 执行并为实验运行评分和打标签。每次保存都记录版本，执行过程作为 OpenInference 跨度追踪，同一编写界面也支持针对真实数据集示例进行试运行预览。

**沙箱**：按需执行评估器代码的隔离运行时层。随功能提供六种后端：两种无需凭证的**本地**后端（Python 使用 WASM，TypeScript 使用 Deno），以及四种**托管**后端（E2B、Daytona、Vercel、Modal），每次调用都在供应商基础设施上运行。管理员可在设置页面启用供应商，保存静态加密的凭证，并将其组合为具名可复用配置。

目前这两个功能**仅提供 GraphQL 接口**：沙箱供应商及配置的增删改查、代码评估器增删改查和版本历史，都通过 Strawberry 变更操作与查询暴露。`routers/v1/` 下尚无 REST 端点，Python 和 TypeScript 客户端也没有辅助方法。

<a id="why-we-built-it"></a>

### 为什么构建

LLM 裁判评估器灵活，但不确定、费用较高，也不擅长正则、JSON 差异或评分公式等狭窄检查。客户需要**确定性**评估器，并能导入自己的库或调用外部 API；我们希望消除在本地编写 Python SDK 循环的操作阻力，让代码评估器也能像 LLM 评估器一样完成编辑、保存、运行：在 Phoenix 界面编写、试运行、附加到数据集，再通过跨度调试。

直接在 Phoenix 服务上执行任意用户代码不安全，因为代码将能访问文件系统、数据库、客户密钥和外部网络。代码评估器必须以沙箱隔离为前提。

<a id="key-files"></a>

### 关键文件

| 文件 | 用途 |
|---|---|
| [src/phoenix/server/sandbox/](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/) | 适配器注册表、六种后端、会话管理器 |
| [src/phoenix/server/sandbox/types.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/types.py) | 配置、凭证、部署模型及能力混入 |
| [src/phoenix/server/sandbox/session_manager.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/session_manager.py) | 会话池化、TTL 淘汰、重新绑定 |
| [src/phoenix/server/api/evaluators.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/evaluators.py) | `CodeEvaluatorRunner`、带围栏的结果协议 |
| [src/phoenix/server/api/mutations/sandbox_config_mutations.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/mutations/sandbox_config_mutations.py) | 供应商和配置的增删改查 |
| [src/phoenix/server/api/mutations/evaluator_mutations.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/mutations/evaluator_mutations.py) | 代码评估器和版本的增删改查 |
| [src/phoenix/db/migrations/versions/0ff41b5b118f_add_sandbox_and_code_evaluator_support.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/db/migrations/versions/0ff41b5b118f_add_sandbox_and_code_evaluator_support.py) | 数据库模式 |
| [app/src/pages/settings/sandboxes/](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/) | 设置 → 沙箱界面 |
| [app/src/components/evaluators/EditCodeEvaluatorDialogContent.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/components/evaluators/EditCodeEvaluatorDialogContent.tsx) | CodeMirror 编写对话框 |

---

<a id="architecture"></a>

## 架构

<a id="three-concepts"></a>

### 三个概念

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   SandboxAdapter (one per backend type)                                         │
│   ════════════════════════════════════                                          │
│   • Class-level metadata (display name, hosting type, capability mixins)        │
│   • Pydantic config / credentials / deployment models                           │
│   • probe_dependencies() — optional SDK import check at startup                 │
│   • build_backend(config, credentials, deployment, user_env) → SandboxBackend   │
│   • Registered iff its optional SDK is importable                               │
│   • Filtered at read-time by PHOENIX_ALLOWED_SANDBOX_PROVIDERS                  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   SandboxBackend (one per (backend_type, sandbox_config_id) per resolution)     │
│   ══════════════════════════════════════════════════════════════════════        │
│   • find_or_create_session(session_key) → opaque handle                         │
│   • execute_in_session(handle, code, timeout) → ExecutionResult                 │
│   • close_session(session_key) — idempotent teardown                            │
│   • config_fingerprint() — short digest for "did the runtime change?"           │
│   • is_session_gone(exc) — classify rebind-recoverable failures                 │
│   • Stateless backends (WASM, Deno) extend BaseNoSessionBackend                 │
│   • Cached per-batch so evaluators sharing a config share the backend object    │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   CodeEvaluatorRunner (one per evaluator, loaded with latest version source)    │
│   ════════════════════════════════════════════════════════════                  │
│   • Wraps source code in a language-specific harness                            │
│   • Applies InputMapping (literal + JSONPath) to produce kwargs                 │
│   • Executes via session manager (managed path) or direct (ephemeral path)      │
│   • Parses fenced ===PHOENIX_RESULT_BEGIN/END=== output                         │
│   • Maps result onto output configs (categorical, continuous, freeform)         │
│   • Emits OpenInference spans (evaluator → input mapping → sandbox)             │
│   • Masks provider credentials and user env-var values from spans               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

<a id="data-flow"></a>

### 数据流

```
                  ┌──────────────┐
                  │ SandboxConfig│
                  │  (admin-     │
                  │   managed    │
                  │   preset)    │
                  └──────┬───────┘
                         │ read at execute time
                         ▼
┌──────────┐  build  ┌─────────────┐  acquire  ┌──────────────────┐
│ Adapter  │────────▶│  Sandbox    │──────────▶│  Session Manager │
│ Registry │         │  Backend    │           │  (composite key) │
└──────────┘         └─────┬───────┘           └────────┬─────────┘
                           │                            │
                           │ execute_in_session         │
                           ▼                            │
                  ┌──────────────────┐                  │
                  │  Code Evaluator  │◀─────────────────┘
                  │     Runner       │  SandboxSession.execute(code)
                  │ (harness + fence │
                  │   parser)        │
                  └─────┬────────────┘
                        │ EvaluationResult
                        ▼
                  ┌─────────────┐
                  │ Annotations │
                  │   on runs   │
                  └─────────────┘

Tracing flow (mirrors the LLM evaluator span tree):
  Evaluator: <name>          (kind=evaluator, input=context)
  ├── Input Mapping          (kind=chain, output=mapped kwargs)
  └── Sandbox: <name>        (kind=tool, input=mapped kwargs, output=parsed result)
```

---

<a id="data-model"></a>

## 数据模型

迁移 `0ff41b5b118f` 创建四张新表（`languages`、`sandbox_providers`、`sandbox_configs`、`code_evaluator_code_versions`），并修改已有 `code_evaluators` 表，添加 `language`、`sandbox_config_id`、`input_mapping`、`output_configs` 列及复合外键。

<a id="languages"></a>

### `languages`

字典表包含两行初始数据：`('PYTHON')` 和 `('TYPESCRIPT')`。通过独立表，其他表可以外键引用语言值，无需将其固定为 CHECK 约束。

<a id="sandbox_providers"></a>

### `sandbox_providers`

由管理员管理，**每种后端类型一行**，`backend_type` 为主键。

| 列 | 类型 | 用途 |
|---|---|---|
| `backend_type` | 字符串（PK） | `WASM`、`E2B`、`DAYTONA`、`VERCEL`、`DENO`、`MODAL` |
| `enabled` | 布尔值 | 按后端整体停用的主开关 |
| `config` | JSON | 部署路由，如 E2B 域名、Daytona target 等 |
| `user_id` | 可空整数（FK） | 最后修改者，删除用户时 SET NULL |
| `updated_at` | 时间戳 | 最后更新时间 |

凭证**不在**此表，存放在已有的 `secrets` 表中，以凭证字段名称为键，例如 `E2B_API_KEY`。即使后端已禁用或未配置，供应商行也始终存在，确保设置界面始终有内容可显示。

<a id="sandbox_configs"></a>

### `sandbox_configs`

管理员管理的预设，**每个供应商可以有多个**。配置将语言、超时、依赖、环境变量引用和互联网访问开关组合为具名预设，供评估器作者选择。创建和编辑由 `IsAdminIfAuthEnabled` 控制；成员编写评估器时可选择现有配置，但不能创建。

| 列 | 类型 | 用途 |
|---|---|---|
| `id` | 整数（PK） | |
| `backend_type` | 字符串（FK→sandbox_providers，RESTRICT） | |
| `language` | 字符串（FK→languages，RESTRICT） | |
| `name` | 标识符（每个 `backend_type` 内 UNIQUE） | |
| `description` | 可空字符串 | |
| `config` | JSON | 特定语言的 Pydantic 配置对象 |
| `timeout` | 整数 | 每次执行的超时秒数 |
| `enabled` | 布尔值 | 单配置停用开关 |
| `user_id` | 可空整数（FK） | 最后修改者，删除用户时 SET NULL |

复合 `UNIQUE (language, id)` **不是**用于去重，而是使 `code_evaluators` 能通过 `(sandbox_config_id, language)` 建立复合外键，保证评估器与其沙箱配置的语言永远一致。

<a id="code_evaluators"></a>

### `code_evaluators`

`evaluators` 的多态子类（`kind='CODE'`）。

| 列 | 类型 | 用途 |
|---|---|---|
| `id` | 整数（PK，FK→evaluators.id CASCADE） | |
| `kind` | `'CODE'`（CHECK 约束） | |
| `language` | 字符串（FK→languages） | |
| `sandbox_config_id` | 可空整数（FK→sandbox_configs，SET NULL） | 可空，评估器可以比其沙箱存在更久 |
| `input_mapping` | JSON | `{literal_mapping: {}, path_mapping: {}}` |
| `output_configs` | JSON | 分类、连续或自由格式配置的列表 |

复合外键 `(sandbox_config_id, language) → (sandbox_configs.id, sandbox_configs.language)` 强制语言一致。

<a id="code_evaluator_code_versions"></a>

### `code_evaluator_code_versions`

源代码**不**存储在 `code_evaluators` 上，每次保存都会在此创建新行。

| 列 | 类型 | 用途 |
|---|---|---|
| `id` | 整数（PK） | 自增，按 `id` 排序 |
| `code_evaluator_id` | 整数（FK→code_evaluators，CASCADE） | |
| `user_id` | 可空整数（FK→users，SET NULL） | 保存者 |
| `source_code` | 字符串 | 代码 |
| `created_at` | 时间戳 | |

索引 `(code_evaluator_id, id)` 使获取各评估器最新版本的开销较低。“当前”版本就是给定 `code_evaluator_id` 下 `id` 最大的行，没有显式的当前版本指针。

---

<a id="sandbox-backends"></a>

## 沙箱后端

[src/phoenix/server/sandbox/](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/) 提供六种适配器。每个适配器都是小型 `SandboxAdapter` 子类，配有 Pydantic `Config`、`Credentials` 和 `Deployment` 模型。

| 后端 | 语言 | 托管方式 | 环境变量 | 互联网 | 依赖 | 会话复用 |
|---|---|---|---|---|---|---|
| **WASM** | Python | 本地 | ❌ | ❌ | ❌ | 无状态 |
| **Deno** | TypeScript | 本地 | ❌ | ❌ | ❌ | 无状态 |
| **E2B** | Python | 托管 | ✅ | ✅（布尔值） | ✅（运行时） | ✅（按元数据） |
| **Daytona** | Python、TS | 托管 | ✅ | ✅（布尔值） | ✅（运行时） | ✅（按元数据） |
| **Vercel** | Python、TS | 托管 | ✅ | ✅（布尔值） | ✅（运行时） | ⚠️ 按副本划分 |
| **Modal** | Python | 托管 | ✅ | ✅（布尔值） | ✅（构建时） | ✅（按名称） |

能力声明由结构决定：适配器配置模型组合各个混入类（`SupportsEnvVars`、`SupportsInternetAccess`、`SupportsDependencies`、`_RuntimePackageInstallation`），元数据层通过 `issubclass()` 检查推导能力标志。这意味着传输格式是事实依据：给配置添加 `SupportsEnvVars`，就会自动向 GraphQL 层和界面声明环境变量支持。

<a id="local-backends"></a>

### 本地后端

**WASM** 通过 `wasmtime` 在 Phoenix 进程内运行编译为 WebAssembly 的 CPython 3.12。每个客体实例的线性内存限制为 128 MiB（`_MAX_WASM_MEMORY_BYTES`），捕获的标准输出有上限，不能访问网络或文件系统。二进制在服务启动时通过 `_download.py` 预取并校验完整性，因此首次评估无需等待下载。一个 4 线程池在事件循环之外运行 WASM 实例，因此宿主最坏内存占用是 4×128 MiB 客体内存，再加共享的 Wasmtime 引擎与模块缓存。

**Deno** 使用明确的锁定选项（`--no-prompt --no-config --no-remote --no-npm`）启动 `deno run` 子进程，不授予任何 `--allow-*` 权限，默认拒绝 read、write、env、net、ffi、run、sys、hrtime。子进程继承**空环境**，Phoenix 进程环境不会泄漏给用户代码。并发子进程上限为 4。不支持环境变量是有意设计，因为传入这些值会重新引入环境暴露。

<a id="hosted-backends"></a>

### 托管后端

生产环境会话键（见下方[会话管理器](#session-manager)）包含管理器的 `replica_id`，因此**全部托管后端天然按副本隔离**：两个副本即使使用“相同”评估器与实验，也不会指向同一个远程沙箱。以下说明描述单个副本内部的后端行为。

**E2B** 使用 E2B 的 `AsyncSandbox`。管理器按元数据查找已有沙箱，因此同一副本内相同 `(evaluator, experiment)` 对的连续运行可复用预热沙箱。包含副本分区的键有意阻止跨副本复用。

**Daytona** 与 E2B 结构相似，使用按元数据查找的长期工作区，但同时支持 Python 和 TypeScript。私有化部署通过供应商行中的 `api_url`/`target` 路由。

**Vercel** 使用 Vercel Functions。目前 Vercel 的 `AsyncSandbox.create` 没有公开的稳定 ID 参数，即使同一副本内部，也没有按元数据查找已有沙箱的机制；只有管理器的本地跟踪能避免重复创建。会话键中的副本分区防止两个副本竞争创建“同一个”沙箱。

**Modal** 比较特殊：依赖在**构建时烘焙进 Image**，而非运行时安装，因为其计费模型鼓励复用不可变镜像。适配器**不**组合 `_RuntimePackageInstallation`，所以同时包含 `dependencies.packages` 和 `internet_access.mode='deny'` 的配置对 Modal **有效**，即使它对 E2B / Daytona / Vercel 构成矛盾。

---

<a id="session-manager"></a>

## 会话管理器

[session_manager.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/session_manager.py) 中的 `SandboxSessionManager` 是托管沙箱会话池的统一管理者。

<a id="why-pool"></a>

### 为什么需要池化

E2B / Daytona / Vercel / Modal 沙箱冷启动需要数秒。一个实验有 1,000 次运行、3 个评估器，就会产生 3,000 次调用；没有池化时，5 秒冷启动就可能耗尽全部评估超时预算。管理器在同一逻辑会话的调用之间保持沙箱预热，使相同副本、相同实验中同一评估器的全部运行使用同一个预热沙箱。

<a id="what-the-manager-owns-and-doesnt"></a>

### 管理器负责什么、不负责什么

管理器独占托管后端的池化会话，并且是唯一的关闭管理者：`SandboxSessionManager.stop()` 覆盖 `DaemonTask.stop`，等待进行中的任务结束，再通过 `close_session` 拆除每个跟踪条目。初始化层没有独立的已绑定后端缓存；管理器以 `composite_key` 为键的 `_tracked` 字典是活动会话的唯一事实来源。

无状态后端明确不在管理范围内。`acquire`、`evict_for_backend`、`evict_for_session_key`、`evict_for_provider_family` 都会在 `isinstance(backend, BaseNoSessionBackend)` 时直接短路，因此 WASM 和 Deno 请求完全绕过管理器。未来要为某种无状态后端添加类似池化的行为，必须先使其不再继承 `BaseNoSessionBackend`。

<a id="session-key-reference"></a>

### 会话键参考

运行器在 [evaluators.py:912](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/evaluators.py#L912) 构造**逻辑**会话键，定义系统视角下什么算“同一个沙箱”：

```python
session_key = f"evaluator:{evaluator_id}:exp:{experiment_id}:{replica_id}"
```

三个相互独立的维度：

| 维度 | 纳入键的原因 |
|---|---|
| `evaluator_id` | 不同评估器不应共享沙箱，依赖和环境等可能不同 |
| `experiment_id` | 不同实验各自摊销冷启动成本，并隔离影响范围 |
| `replica_id` | 跨副本并发运行不会指向同一个供应商沙箱 |

明确**不在**键中的内容：

- **`evaluator_version_id`**：保存新版本会**复用**预热沙箱。每次调用都会发送新源代码，它只是执行框架中的字符串，因此版本变化不产生冷启动开销。版本 ID 作为 `code_evaluator_version_id` 元数据附加到沙箱跨度用于审计，不参与池化。

会话管理器再追加配置指纹，构造**物理**跟踪键：

```python
composite_key = f"{session_key}#{config_fingerprint()}"
```

指纹取**影响远程运行时的配置子集**，计算 sha256 后截取 16 个字符：

- `backend_type`、`language`
- `dependencies.packages`，排序后计算
- `internet_access.mode`

环境变量的**值**被有意排除在指纹之外，轮换 API 密钥不会使预热沙箱失效。但不同后端的环境变量**注入生命周期不同**：E2B、Daytona、Deno 每次执行时注入，轮换在下次调用生效；Vercel、Modal 在会话创建时注入，因此预热会话始终持有创建时的值，直到因其他原因被丢弃。WASM 会抛出 `UnsupportedOperation`，完全不接受环境变量。环境变量的**键**同样不计入指纹。使用复合键后，迭代过程中改变配置，例如添加包或切换互联网访问，会自然产生新远程会话，无需显式失效逻辑。

管理器将此 `composite_key` 通过 `find_or_create_session` 传给后端，并用它在内部查找跟踪条目。

<a id="when-cold-starts-actually-happen"></a>

### 哪些情况真正触发冷启动

| 触发条件 | 是否冷启动 |
|---|---|
| 实验第一次评估 | 是，创建沙箱 |
| 相同评估器、实验和副本的后续评估 | 否，复用预热沙箱 |
| 保存评估器新版本 | 否，键不包含版本 |
| 同一实验使用不同评估器 | 是，`evaluator_id` 不同 |
| 同一评估器运行不同实验 | 是，`experiment_id` 不同 |
| 同一评估器和实验运行于不同副本 | 是，`replica_id` 不同 |
| 更改配置，如依赖、网络或语言 | 是，`config_fingerprint` 不同 |
| 轮换环境变量值 | 否 |
| 编写界面的预览或试运行 | 每次都是，使用临时路径，见[代码评估器运行器](#code-evaluator-runner) |

<a id="lifecycle"></a>

### 生命周期

| 参数 | 值 | 用途 |
|---|---|
| `idle_ttl_seconds` | 300 | 删除空闲超过此时长的会话 |
| `sweep_interval_seconds` | 30 | 淘汰清理任务的运行间隔 |
| `eviction_grace_seconds` | 5 | 淘汰已标记条目前的宽限期 |
| `max_sessions_per_provider` | 32 | 每个供应商的并发上限 |

清理器是随服务启动的 `DaemonTask`。正在使用的会话（refcount > 0）绝不会被淘汰；空闲超过 TTL 的会话通过 `close_session` 拆除。

> **后端实现者注意：** `close_session` 实现必须在第一次 `await` **之前同步**将会话从后端本地会话字典弹出。管理器在等待 `backend.close_session()` 前会释放对应键的锁；如果后端先等待再弹出，会出现竞争窗口，使并发 `acquire` 返回即将失效的会话。

<a id="rebind"></a>

### 重新绑定

`SandboxSession.execute()` 抛出异常时，会通过 `is_session_gone(exc)` 请求后端分类。如果为 `True`，管理器再次调用 `find_or_create_session` 重新绑定、更新句柄，并**恰好重试一次**。第二次失败封装为 `ExecutionResult`，不再次抛出。后端对分类为会话已消失的异常会重新抛出，而非封装，因此能区分“远程沙箱死亡且重建失败”和正常评估器运行时错误。

后端应倾向于**保守分类**：误判为 `True` 会触发不必要的重新绑定，误判为 `False` 则会向用户呈现过期会话错误。

重新绑定遵循现有锁顺序：`acquire` 先获取对应键锁，仅在 `_get_or_reserve` 的短暂快照临界区中获取 `_state_lock`；清理器（`_evict_matching`、`_sweep_idle`）获取 `_state_lock` 拍下跟踪条目集合快照，并在获取任何键锁**之前释放**。这种不对称是有意设计，可防止清理器等待耗时的 `find_or_create_session` 调用。任何新增的生命周期变更操作，如交换、刷新、热替换，都应遵循相同结构，不要另建锁顺序。

<a id="refusal-modes"></a>

### 拒绝模式

`acquire` 可以在调用后端前因两种原因拒绝：

- **`SessionLimitExceeded`**：达到供应商上限。运行器转为带 `error="session_limit_exceeded"` 的 `EvaluationResult`，评估行会被记录，但没有可用结果。这是有意取舍：宁可将一次评估标为失败，也不让单个客户耗尽全部沙箱容量。
- **`SessionInvalidated`**：跟踪条目正处于排空阶段，清理器在 `acquire` 与获取锁之间选中了它。运行器通过 `wait_for_drain` 等待排空结束，再重试一次。

---

<a id="code-evaluator-runner"></a>

## 代码评估器运行器

[evaluators.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/evaluators.py) 中的 `CodeEvaluatorRunner` 连接评估器记录和沙箱层。

<a id="harness"></a>

### 执行框架

用户代码定义 `evaluate(...)` 函数，运行器用对应语言的执行框架包装它，依次：

1. 拼接用户源代码。
2. 定义 `_inputs = <mapped kwargs as literal>`。
3. 调用 `_result = evaluate(**_inputs)`（Python）或 `await evaluate(_inputs)`（TypeScript）。
4. 将 `_result` 作为 JSON 打印在围栏标记之间。

Python 执行框架：

```python
<user source>

import json as _json
_inputs = {'output': '...', 'reference': '...'}
_result = evaluate(**_inputs)
print('===PHOENIX_RESULT_BEGIN===')
print(_json.dumps(_result))
print('===PHOENIX_RESULT_END===')
```

传输协议**基于标准输出**，而非函数返回值，因为不同后端呈现任意代码返回值的方式不同，但全部后端都提供标准输出。`_extract_fenced_result` 解析围栏，查找最后一个完整 `BEGIN/END` 对；有意取**最后一个**，避免用户在代码较早位置 `print()` 围栏标记而污染结果。

<a id="input-mapping"></a>

### 输入映射

`InputMapping` 包含两部分：

- `literal_mapping: {name: value}`：将参数绑定到字面量。
- `path_mapping: {name: jsonpath_expr}`：从运行时上下文提取值。

数据集评估器的运行时上下文为 `{output, reference, input, metadata}`。JSONPath 通过 `jsonpath_ng` 求值，例如 `path_mapping = {"answer": "$.output.choices[0].message.content"}` 是有效用法。运行器从源代码推导函数参数列表：Python 使用 AST，TypeScript 对 `function evaluate(...)` 和 `const evaluate = (...) =>` 使用正则。因此界面知道应在映射编辑器中暴露哪些参数槽位。

<a id="output-configs"></a>

### 输出配置

每个输出配置的结果必须匹配以下三种结构之一：

- **分类**：`{label: str, score?: float, explanation?: str}`，其中 `label` 必须匹配配置值。
- **连续**：`{score: float, explanation?: str}`，分数位于配置的最小值和最大值之间。
- **自由格式**：`{label?: str, score?: float, explanation?: str}`，不验证。

一个评估器可以有多个输出配置；函数返回列表或字典，运行器按名称将条目映射到配置。不匹配会产生单配置错误标注，而非使整个评估器统一失败，因此部分正确的评估器仍能写入其正确配置。

<a id="tracing"></a>

### 追踪

每次执行按 OpenInference 语义发出三个跨度组成的树：

| 跨度 | 类型 | 承载内容 |
|---|---|---|
| `Evaluator: <name>` | `evaluator` | 完整上下文作为输入 |
| `Input Mapping` | `chain` | 映射规格和上下文作为输入，映射后的关键字参数作为输出 |
| `Sandbox: <name>` | `tool` | 映射后的关键字参数作为输入，解析结果作为输出，后端、语言、超时作为元数据 |

这些跨度禁用 OpenTelemetry 自动记录（`record_exception=False, set_status_on_exception=False`），每个异常事件都通过 `_record_masked_exception` 显式添加，以控制进入追踪的数据。

<a id="two-execution-paths"></a>

### 两条执行路径

运行器支持**托管路径**（生产环境，通过会话管理器）和**临时路径**（预览或试运行，由后端 `execute` 在当前调用内管理生命周期）。临时路径用于防止编写界面测试面板的一次性运行污染长期会话池。

---

<a id="design-decisions"></a>

## 设计决策

<a id="adapter-pattern-over-hardcoded-backend-logic"></a>

### 使用适配器模式，而非硬编码后端逻辑

**背景**：六种后端的能力集合重叠但不完全一致。直接方案包括一个巨大的 `if backend_type == ...` 分支，或带抽象方法的策略类层级。

**决策**：采用基于 Pydantic 的适配器，通过混入类型的 `issubclass()` 检查推导能力声明。

**影响**：

- ✅ 添加第七种后端，如 CodeSandbox，只需一个文件，再在 `_try_register_adapter` 中增加一行。
- ✅ 传输格式本身就是事实来源。界面的“显示环境变量字段”标志由 `issubclass(config_model, SupportsEnvVars)` 推导，不会出现配置声称支持环境变量而适配器忽略它们的情况。
- ✅ 注册时检查可选 SDK 依赖。未安装 `e2b` 时跳过 E2B 适配器，系统其他部分仍正常工作。
- ⚠️ 能力矩阵隐含在混入组合顺序中。读者需查看 `class E2BConfig(_Config, SupportsEnvVars, SupportsInternetAccess, SupportsDependencies, _RuntimePackageInstallation)` 并理解其含义。我们接受这种方式，因为它能表达比策略类层级更宽的能力表。

<a id="two-tier-provider--config-split"></a>

### 供应商与配置两层拆分

**背景**：管理员启用 E2B 并设置 API 密钥；三位评估器作者分别需要不同配置：带 `pandas`、允许互联网、两者都不需要。

**决策**：`sandbox_providers`（每后端一行）保存凭证和部署路由；`sandbox_configs`（每供应商多个、管理员管理的预设）保存评估器级配置，包括依赖、环境变量、互联网访问和超时。两层都由管理员控制，划分依据是关注范围——供应商整体与预设层级，而非谁能修改。

**影响**：

- ✅ 作者无需查看或接触凭证，管理员不必管理每个评估器自己的预设。
- ✅ 可在供应商层整体禁用某后端，无需删除全部配置。
- ✅ `sandbox_configs.backend_type → sandbox_providers.backend_type` 上的 `ondelete="RESTRICT"` 防止管理员删除仍被配置依赖的供应商。目前供应商实际上不能删除，而是在首次保存凭证时延迟创建。
- ⚠️ 有两层 enabled 布尔开关，配置可用需要两者都为 true。

<a id="versioning-on-every-save"></a>

### 每次保存都创建版本

**背景**：历史实验中的评估器分数必须可复现。原地修改 `source_code` 会使实验标注无法解释。

**决策**：源代码保存在 `code_evaluator_code_versions`，绝不放在评估器行上。每次保存创建新版本。每个沙箱跨度通过 OpenInference 元数据携带 `code_evaluator_version_id`，可经追踪找回产生任意标注的版本。

**影响**：

- ✅ 通过追踪形成完整审计链。“为何本次得分 0.3” → 查询标注 `trace_id`，找到沙箱跨度，读取 `code_evaluator_version_id`，获取源代码。
- ✅ 回滚只需用旧版本源代码创建新版本。
- ⚠️ 版本**不是**标注行上的列，恢复需经过追踪；追踪被保留策略删除时，审计链会断裂。
- ⚠️ 版本**不属于**会话池键，见[会话管理器](#session-manager)，因此新保存会复用预热沙箱。这是合理取舍：每次调用本来就发送新源代码，而每次保存都冷启动会使迭代编写无法使用。
- ⚠️ **不支持固定实验运行时的版本。** `resolve_dataset_evaluators` 在解析时总通过 `latest_code_evaluator_versions_by_evaluator_id` 加载最新版本，因此重新运行实验会执行当前代码，而非原实验代码。虽然可经追踪恢复原代码，但若不手动用旧源代码创建新评估器，就无法再次按原代码执行。
- ⚠️ 频繁保存会生成很多行。源代码较小，我们接受此成本。

<a id="local--hosted-dichotomy"></a>

### 本地与托管两类后端

**背景**：没有第三方沙箱供应商的自行部署用户，也应能够使用代码评估器。

**决策**：Phoenix 自带两种本地后端 WASM 和 Deno，无需凭证，有意限制能力，不支持环境变量、互联网和依赖。

**影响**：

- ✅ 开箱即用：安装 Phoenix 后即可使用代码评估器执行自包含检查。
- ✅ 本地后端限制最严格，不论管理员如何选择，对不可信代码都推荐它们。
- ⚠️ 需要 `pandas` 或外部 API 的作者必须使用由管理员启用的托管后端。
- ⚠️ WASM Python 运行时基于 CPython 3.12，但移除了许多依赖操作系统层的标准库，部分 Python 习惯用法无法工作。我们接受此限制，不向 WASM 镜像预装依赖，以免二进制体积膨胀。

<a id="fenced-stdout-protocol"></a>

### 标准输出围栏协议

**背景**：运行器如何从任意后端执行的任意代码中取回 `evaluate()` 返回值？各后端不同，E2B 可返回 Python 对象，WASM 和 Deno 提供标准输出。

**决策**：用执行框架包装用户代码，将返回值编码为 JSON，放在哨兵标记 `===PHOENIX_RESULT_BEGIN===` / `===PHOENIX_RESULT_END===` 之间，从标准输出解析**最后一个**完整标记对。

**影响**：

- ✅ 适用于全部后端，无需各自的反序列化逻辑。
- ✅ 用户的 `print()` 调试输出仍可进入 `stderr` 或围栏外标准输出，并在沙箱跨度中可见。
- ⚠️ 用户代码自身打印标记字符串，例如 `print("===PHOENIX_RESULT_END===")` 时，解析器选择最后一个完整标记对。因此多余开始标记无害，但真正结果前多余结束标记可能改变围栏边界。刻意选择“最后完整标记对”而非“第一个”，就是为了容忍用户输出中的零散标记。

<a id="three-dimensional-session-pooling"></a>

### 三维会话池化

**背景**：预热沙箱需要稳定身份。键太粗，例如只有 `evaluator_id`，两个实验会争用同一沙箱；键太细，例如包含 `evaluator_version_id`，作者每次保存都会冷启动。还必须避免两个副本运行同一实验时相互干扰远程沙箱。

**决策**：逻辑会话键为 `evaluator:{id}:exp:{experiment_id}:{replica_id}`；物理跟踪键追加配置指纹：`f"{session_key}#{config_fingerprint()}"`。指纹覆盖 `backend_type`、`language`、`dependencies.packages`、`internet_access.mode`，有意排除环境变量值。

**影响**：

- ✅ 同一实验内部复用，将冷启动分摊到数千次评估。
- ✅ 副本不会争用同一个供应商沙箱，各自拥有自己的池。
- ✅ 作者迭代快：新版本使用预热沙箱，只有配置变化才冷启动。
- ✅ 影响运行时的配置改动会自动分化为新会话，无需显式调用会话失效操作。
- ✅ 轮换 API 密钥，即环境变量值，不会丢弃预热沙箱。
- ⚠️ 不跨副本共享会话，即使 E2B、Daytona、Modal 等供应商本可通过元数据发现会话。我们选择每个副本拥有其沙箱的简单方式，放弃少量容量收益。
- ⚠️ 按实验分区，意味着长期实验不会与同一评估器的独立临时试运行共享沙箱。这可以接受，因为预览本就走临时路径。

<a id="read-time-provider-allowlist"></a>

### 读取时应用供应商允许列表

**背景**：自行部署环境可能只允许特定供应商，例如采购只批准 Modal。

**决策**：`PHOENIX_ALLOWED_SANDBOX_PROVIDERS` 是逗号分隔的环境变量。不在允许列表中的适配器在从注册表**读取时**筛除，而非注册时筛除。

**影响**：

- ✅ 不支持更改环境变量后免重启生效，因为变量只读取一次；但读取时检查便于测试按用例替换环境变量。
- ✅ 不被允许的适配器仍加载 SDK 并注册，因此配置错误会表现为注册表的 `KeyError`，而非静默消失、让人困惑 E2B 去了哪里。
- ⚠️ 后端可通过两种方式禁用：部署级环境变量，或管理员级 `sandbox_providers.enabled=false`。两者适用于不同场景，我们接受此重叠。

<a id="secret-masking-over-secret-stripping"></a>

### 密钥掩码，而非直接剥离

**背景**：用户环境变量和供应商凭证需要在沙箱中使用，但不能出现在跨度、日志或错误消息里。

**决策**：以某次执行涉及的全部密钥值集合构造 `SandboxSecretMasker`。发出跨度中的每个字符串属性都经过掩码器，将密钥字面值替换为稳定的 `<redacted:N>` 标记，每个不同密钥一个索引，按最长值优先替换，避免较短前缀破坏较长密钥标记。少于 8 个字符的密钥忽略，因为与正常内容的碰撞率过高。

**影响**：

- ✅ 可捕获意外泄漏：用户代码将 `OPENAI_API_KEY` 打印到标准输出时，在进入沙箱跨度前就会被掩码。
- ✅ 递归生效：输入映射跨度、评估器跨度、异常事件堆栈都使用同一掩码器。
- ✅ 稳定 `<redacted:N>` 标记而非 `***`，使操作人员可关联多处被遮盖的是同一值，无需暴露原值。
- ⚠️ 采用字面子串匹配。密钥是非密钥值的子串时会过度遮盖。我们接受此结果，因为误报可恢复，漏报会泄漏数据。
- ⚠️ 少于 8 个字符的短密钥完全不掩码，不应存储短令牌。
- ⚠️ 掩码不能替代从源头避免把密钥写进跨度，它只是纵深防御。

<a id="catch-and-continue-on-backend-build-failures"></a>

### 后端构建失败时捕获并继续

**背景**：即使可选 SDK 已安装，也可能因 Python 环境损坏或版本不匹配而导入失败。此时应让守护任务崩溃、拒绝注册后端，还是展示友好错误？

**决策**：注册时调用一次 `probe_dependencies()`，导入失败则静默跳过注册，仅记录调试日志。之后在 `build_backend` 中发生的 `ImportError` 则被捕获并返回 `None`，由运行器转换为面向用户的“后端不可用”GraphQL 错误。

**影响**：

- ✅ 即使某个沙箱 SDK 损坏，Phoenix 仍可正常启动，系统其他部分照常工作。
- ✅ 其他后端仍可用。
- ⚠️ 用户看到“后端不可用”，而非底层导入错误，需查看服务端日志调试。这是合理取舍，另一种做法会将导入堆栈暴露到界面。

---

<a id="security--isolation"></a>

## 安全与隔离

<a id="trust-boundary"></a>

### 信任边界

用户提供的代码**始终不可信**。即使本地后端，也按代码具有恶意的假设设计：

- **WASM**：没有系统调用和网络，每实例内存上限 128 MiB，标准输出有上限，CPython 在沙箱中运行，无法读取 Phoenix 文件系统、环境或数据库。
- **Deno**：空环境，不授予任何 `--allow-*` 权限，并使用 `--no-prompt --no-config --no-remote --no-npm` 阻止交互提示、配置加载、远程模块解析和 npm 导入。读取宿主文件系统需要 `--allow-read`，我们绝不授予。

托管后端将隔离信任委托给供应商：我们信任 E2B / Daytona / Vercel / Modal 的单次执行隔离，控制哪些凭证和环境变量跨越边界，但无法控制供应商收到后如何处理。

<a id="ssrf-guard-on-deployment-urls"></a>

### 部署 URL 的 SSRF 防护

管理员可配置的 URL，包括 E2B 域名或 API URL、Daytona API URL，会按协议允许列表验证：

- `https://`：始终允许。
- `http://localhost`、`http://127.0.0.1`、`http://::1`：允许，用于开发或私有化部署。
- 其他地址，如 `http://internal-host`、`file://`、`gopher://`、`javascript:`：拒绝。

这可防止管理员被诱导设置 `E2B_API_URL=http://169.254.169.254/...`，使 Phoenix 成为 SSRF 工具。

<a id="encrypted-credential-storage"></a>

### 凭证加密存储

供应商凭证存放在已有 `secrets` 表中，使用 Phoenix 级加密密钥进行静态加密。只在执行时解密，明文直接传给沙箱 SDK，不接触 Phoenix 文件系统或持久化状态。

用户定义的环境变量**按引用存储**：`sandbox_configs.config` 对象中包含 `env_vars: {VAR_NAME: {secret_key: "..."}}`，运行器在执行时解析 secret_key 到明文。编辑沙箱配置不会向界面暴露密钥。

<a id="rbac"></a>

### 基于角色的访问控制（RBAC）

全部沙箱供应商与配置变更都由 `IsAdminIfAuthEnabled` 控制，同时应用常规的 `IsNotReadOnly`、`IsNotViewer`、`IsLocked` 防护。只有管理员能启用供应商、设置凭证或创建配置。评估器作者，即成员，只能选择已有配置，不能新建，从而防止作者悄悄创建 `internet_access=allow` 配置来向外传输数据。

---

<a id="caveats"></a>

## 注意事项

<a id="per-backend-quirks"></a>

### 各后端差异

| 后端 | 差异 | 原因 |
|---|---|---|
| WASM | 没有 `requests`、`httpx`，标准库受限 | 随包提供的 CPython-on-wasmtime 镜像中，WASI 没有完整 BSD socket 层。添加类似 Pyodide `pyfetch` 的 `fetch` 兼容层可支持 HTTP，但不在首版范围内。 |
| Deno | 不支持环境变量、互联网和依赖 | 子进程隔离是核心目标，放宽限制就破坏了本地后端的定位 |
| E2B | 首次调用冷启动约 3 秒 | 会话池化使此成本可以接受 |
| Daytona | 私有化 URL 按供应商设置，不能按配置设置 | 属于管理员级配置，不向作者暴露部署路由 |
| Vercel | 长期会话键按副本划分 | 当前 `AsyncSandbox.create` 没有稳定 ID 参数 |
| Modal | 依赖在构建时烘焙，不在运行时安装 | Modal 镜像缓存适合作为依赖安装单位，运行时安装会让每次调用重复付出成本 |

<a id="known-limitations"></a>

### 已知限制

- **尚无互联网允许列表访问。** 托管后端声明 `internet_access_capability="boolean"`，只有全部允许或全部拒绝。GraphQL 枚举（`server/api/types/SandboxConfig.py`）预留了 `InternetAccessMode.ALLOWLIST`，但后端配置模式 `InternetAccessConfig.mode: Literal["deny", "allow"]` 中没有此值，因此没有适配器接受它。
- **不支持流式输出。** 运行器在执行结束后才读取标准输出，长时间评估器即使打印进度，界面也看不到实时进展。
- **不跨实验或副本共享沙箱。** 会话键按实验和副本分区，同一评估器在独立实验中需要单独冷启动，副本从不共享远程沙箱，即使供应商支持。收益是隔离，代价是横向扩展部署中部分重复冷启动。
- **`SessionLimitExceeded` 是硬失败。** 达到供应商上限时，额外评估立即失败，不排队。32 会话上限较保守，获得客户数据后再提高。
- **不重试临时沙箱错误。** E2B 偶发返回 500 就会使评估失败。实验运行器对 LLM 评估器有重试逻辑，但尚未包装沙箱评估器，见 [experiment-runner-background-process.md](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/internal_docs/specs/experiment-runner-background-process.md)。
- **没有单次执行的 CPU 或墙钟资源预算。** 当前强制 `timeout`，默认由配置决定，但没有 CPU 秒数上限。用户可以编写忙循环，耗尽整个超时窗口。

<a id="things-that-look-like-bugs-but-arent"></a>

### 看似缺陷但属于预期的行为

- **WASM 内存上限按客体计算，不是全局上限。** 每个 Wasmtime 实例通过 `store.set_limits(memory_size=...)` 限制为 128 MiB。4 个工作线程的最坏占用是 4×128 MiB 客体内存，加共享引擎和模块缓存。
- **保存评估器新版本不会丢弃预热沙箱。** 会话键有意省略 `evaluator_version_id`，下次调用执行框架会携带新源代码。版本作为审计元数据放在沙箱跨度上，而非池键中。
- **`config_fingerprint()` 不包含环境变量键。** 给配置添加新环境变量不会丢弃预热沙箱，执行框架下次调用时读取新环境。
- **Deno 的 `secret_values` 集合为空**，即使类型层配置了环境变量。这是因为 `DenoConfig` 不组合 `SupportsEnvVars`，掩码器没有需要遮盖的内容。行为正确，但曾在代码评审时让我们意外。

---

<a id="future-considerations"></a>

## 后续考虑

**按主机限制互联网访问。** 类型系统支持，但尚无适配器实现。E2B 和 Daytona 都提供可对接的网络策略钩子。

**展示 Modal 构建缓存状态。** 依赖变化后，Modal 首次调用会重建镜像，目前用户不可见，只会看到首次评估耗时较长。应将“正在构建镜像”作为跨度属性展示。

**流式标准输出。** 许多评估器打印进度。围栏结果协议兼容流式输出，只需最后写围栏，但运行器目前仅在执行后读取标准输出。可在 `SandboxBackend.execute_in_session` 添加 `stream_to_span` 钩子。

**单次执行的 CPU 与内存预算。** 当前只有墙钟超时，资源预算可以让意外写成平方复杂度的评估器尽早失败。

**自带沙箱。** 具有内部沙箱基础设施的客户，如合规或网络隔离场景，可在源码树之外实现 `SandboxAdapter`。已有 `register_sandbox_adapter()` 函数，缺少的是元数据发现：`_build_sandbox_adapter_metadata` 硬编码六种内置适配器；还需要插件加载钩子，在启动时调用第三方代码的 `register_sandbox_adapter()`。

**放宽副本隔离。** 当前全部托管后端的会话键都包含 `replica_id`，副本从不共享远程沙箱。此前曾研究通过 E2B / Daytona / Modal 元数据发现实现确定性跨副本复用，但在当前规模，协调成本超过少量容量收益，因此暂缓。Vercel 的 `AsyncSandbox.create` 没有稳定 ID 参数，无论如何都无法参与。未来调整必须选择哪些后端加入，并接受新增的跨副本协调复杂性。

**SDK / CLI / REST 功能对齐。** 代码评估器和沙箱管理目前仅提供 GraphQL。Python 客户端没有 `create_code_evaluator(...)` 辅助方法，TypeScript 客户端没有沙箱接口，`routers/v1/` 下也没有 REST 端点。添加这些功能并不复杂，但在 GraphQL 接口稳定前暂缓。

**评估市场与模板。** 前端已有内置起始片段菜单（`codeEvaluatorTemplates.ts`）。社区示例库可让用户共享 JSON 差异、正则匹配或嵌入距离评估器。

---

<a id="appendix-key-constants"></a>

## 附录：关键常量

| 常量 | 值 | 用途 |
|---|---|---|
| `_DEFAULT_IDLE_TTL_SECONDS` | 300 | 删除超过此时长的空闲会话 |
| `_DEFAULT_SWEEP_INTERVAL_SECONDS` | 30 | 清理周期 |
| `_DEFAULT_EVICTION_GRACE_SECONDS` | 5 | 淘汰已标记条目前的宽限期 |
| `_DEFAULT_MAX_SESSIONS_PER_PROVIDER` | 32 | 每供应商并发上限 |
| `_MAX_WASM_MEMORY_BYTES` | 128 MiB | 每个 WASM 客体实例的内存，4 个线程最多为 4×128 MiB |
| Deno 最大并发子进程数 | 4 | 子进程池大小 |
| WASM 线程池线程数 | 4 | 在事件循环外执行 |
| 配置指纹长度 | 16 个字符 | sha256 前缀 |
| `ENV_PHOENIX_ALLOWED_SANDBOX_PROVIDERS` | `*` | 逗号分隔的允许列表 |


<a id="appendix-file-references"></a>

## 附录：文件参考

<a id="backend"></a>

### 后端

| 概念 | 文件 |
|---------|------|
| 适配器注册表与工厂 | [src/phoenix/server/sandbox/\_\_init\_\_.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/__init__.py) |
| 类型系统，包括配置、凭证、部署和混入 | [src/phoenix/server/sandbox/types.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/types.py) |
| 会话管理器 | [src/phoenix/server/sandbox/session_manager.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/session_manager.py) |
| WASM 后端 | [src/phoenix/server/sandbox/wasm_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/wasm_backend.py) |
| Deno 后端 | [src/phoenix/server/sandbox/deno_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/deno_backend.py) |
| E2B 后端 | [src/phoenix/server/sandbox/e2b_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/e2b_backend.py) |
| Daytona 后端 | [src/phoenix/server/sandbox/daytona_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/daytona_backend.py) |
| Vercel 后端 | [src/phoenix/server/sandbox/vercel_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/vercel_backend.py) |
| Modal 后端 | [src/phoenix/server/sandbox/modal_backend.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/modal_backend.py) |
| WASM 二进制预取 | [src/phoenix/server/sandbox/\_download.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/sandbox/_download.py) |
| `CodeEvaluatorRunner`、围栏解析器、模式推导 | [src/phoenix/server/api/evaluators.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/evaluators.py) |
| 密钥掩码器 | [src/phoenix/server/api/helpers/sandbox_redaction.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/helpers/sandbox_redaction.py) |
| 数据库模型（`SandboxProvider`、`SandboxConfig`、`CodeEvaluator`、`CodeEvaluatorVersion`） | [src/phoenix/db/models.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/db/models.py) |
| 迁移 | [src/phoenix/db/migrations/versions/0ff41b5b118f_add_sandbox_and_code_evaluator_support.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/db/migrations/versions/0ff41b5b118f_add_sandbox_and_code_evaluator_support.py) |

<a id="graphql"></a>

### GraphQL 接口

| 概念 | 文件 |
|---------|------|
| `SandboxConfig`、`SandboxProvider` 类型 | [src/phoenix/server/api/types/SandboxConfig.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/types/SandboxConfig.py) |
| `CodeEvaluator`、`CodeEvaluatorVersion` 类型 | [src/phoenix/server/api/types/Evaluator.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/types/Evaluator.py) |
| 代码评估器变更操作 | [src/phoenix/server/api/mutations/evaluator_mutations.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/mutations/evaluator_mutations.py) |
| 沙箱配置与供应商变更操作 | [src/phoenix/server/api/mutations/sandbox_config_mutations.py](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/src/phoenix/server/api/mutations/sandbox_config_mutations.py) |

<a id="frontend"></a>

### 前端

| 概念 | 文件 |
|---------|------|
| 设置 → 沙箱页面 | [app/src/pages/settings/sandboxes/SettingsSandboxesPage.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/SettingsSandboxesPage.tsx) |
| 供应商启用与凭证 | [app/src/pages/settings/sandboxes/SandboxProvidersCard.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/SandboxProvidersCard.tsx), [SandboxProviderCredentialsDialog.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/SandboxProviderCredentialsDialog.tsx) |
| 沙箱配置增删改查界面 | [app/src/pages/settings/sandboxes/SandboxConfigsCard.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/SandboxConfigsCard.tsx), [SandboxConfigDialog.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/SandboxConfigDialog.tsx) |
| 包规格验证，与后端语法保持一致 | [app/src/pages/settings/sandboxes/utils.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/pages/settings/sandboxes/utils.tsx) |
| 代码评估器编写对话框 | [app/src/components/evaluators/EditCodeEvaluatorDialogContent.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/components/evaluators/EditCodeEvaluatorDialogContent.tsx) |
| 试运行预览面板 | [app/src/components/evaluators/CodeEvaluatorTestSection.tsx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/components/evaluators/CodeEvaluatorTestSection.tsx) |
| 起始模板 | [app/src/components/evaluators/codeEvaluatorTemplates.ts](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/app/src/components/evaluators/codeEvaluatorTemplates.ts) |

<a id="documentation"></a>

### 文档

| 概念 | 文件 |
|---------|------|
| 沙箱设置指南 | [docs/phoenix/settings/sandboxes.mdx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/docs/phoenix/settings/sandboxes.mdx) |
| 代码评估器操作指南 | [docs/phoenix/evaluation/how-to-evals/code-evaluators.mdx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/docs/phoenix/evaluation/how-to-evals/code-evaluators.mdx) |
| 输出结构参考 | [docs/phoenix/evaluation/how-to-evals/code-evaluator-output-shapes.mdx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/docs/phoenix/evaluation/how-to-evals/code-evaluator-output-shapes.mdx) |
| 自行部署沙箱运行时 | [docs/phoenix/self-hosting/features/sandbox-runtimes.mdx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/docs/phoenix/self-hosting/features/sandbox-runtimes.mdx) |
| 教程：使用代码评估器运行实验 | [docs/phoenix/datasets-and-experiments/tutorial/run-experiments-with-code-evals.mdx](https://github.com/Arize-ai/phoenix/blob/150a83d9e43818938618978ed5f8cc224e08f3a5/docs/phoenix/datasets-and-experiments/tutorial/run-experiments-with-code-evals.mdx) |
