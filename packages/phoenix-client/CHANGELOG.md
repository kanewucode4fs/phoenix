<a id="changelog"></a>

# 更新日志

## [3.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v3.4.0...arize-phoenix-client-v3.5.0) (2026-09-08)


<a id="features"></a>

### 新功能

* 新增 MiniMax 提供方集成 ([#14310](https://github.com/Arize-ai/phoenix/issues/14310)) ([7e01ce7](https://github.com/Arize-ai/phoenix/commit/7e01ce703b3830447ebdf641ccbb95089778e810))
* **client:** 为 Harbor 插件新增 ATIF 追踪 ([#15715](https://github.com/Arize-ai/phoenix/issues/15715)) ([30dccec](https://github.com/Arize-ai/phoenix/commit/30dccec0744d55612366aa3d444eb7dc12f7831b))
* **client:** 为 Python 和 TypeScript 客户端 get_traces 新增错误和延迟过滤器 ([c839254](https://github.com/Arize-ai/phoenix/commit/c83925478204259eca8e6709fd8c1a3c20f2f7e1))


<a id="bug-fixes"></a>

### 问题修复

* **annotations:** 校验所有配置的 ID 列，而非仅首列 ([#15877](https://github.com/Arize-ai/phoenix/issues/15877)) ([7654185](https://github.com/Arize-ai/phoenix/commit/76541854a8936bf95ffb3ed959085d4f6a92a53b))
* **ci:** 格式化客户端文档，并跳过 fork PR 评论 ([10915f5](https://github.com/Arize-ai/phoenix/commit/10915f5a1de5f4fac51265293f496e8ebc74ce1a))


<a id="documentation"></a>

### 文档

* **phoenix-client:** 修正 create_dataset 文档字符串，将 dataset_name 改为实际参数 name ([#15950](https://github.com/Arize-ai/phoenix/issues/15950)) ([397088a](https://github.com/Arize-ai/phoenix/commit/397088a263e0d999c3912cd85adc05166cbf69a2))

## [3.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v3.3.0...arize-phoenix-client-v3.4.0) (2026-09-03)


<a id="-breaking-changes"></a>

### ⚠ 不兼容变更

* **server:** GET /v1/model_providers 不再返回自定义提供方或 `next_cursor`，内置条目公开 `provider`，替代 `kind` + `provider_key`。自定义提供方移至 GET /v1/custom_model_providers。该端点尚未发布，因此不会影响任何已发布客户端。

<a id="features-1"></a>

### 新功能

* **agents:** 新增使用用户提供的 token 提交 GitHub issue 的 PXI 工具 ([#15780](https://github.com/Arize-ai/phoenix/issues/15780)) ([e3b3dd5](https://github.com/Arize-ai/phoenix/commit/e3b3dd55ae45db7e73329b8ad33331af7fc26389))
* **app:** 新增 Z.ai 作为内置 GLM 模型提供方 ([#15857](https://github.com/Arize-ai/phoenix/issues/15857)) ([58b7017](https://github.com/Arize-ai/phoenix/commit/58b7017284e2f7b4391397ce2080cb67a23e066c))
* **client:** 新增提示词删除 ([#15736](https://github.com/Arize-ai/phoenix/issues/15736)) ([5610755](https://github.com/Arize-ai/phoenix/commit/5610755353a1c05a90868232de22995942653085))
* **client:** 在 Phoenix 中记录 Harbor 作业 ([#15547](https://github.com/Arize-ai/phoenix/issues/15547)) ([f7c6cb3](https://github.com/Arize-ai/phoenix/commit/f7c6cb3bee3b3d4447ac649aa54022ce2d157a70))
* **client:** 将 Harbor 奖励记录为 Phoenix 评估 ([#15600](https://github.com/Arize-ai/phoenix/issues/15600)) ([822d7cb](https://github.com/Arize-ai/phoenix/commit/822d7cbb6ee605e4aaf663410f801f6949e15298))
* **prompts:** 新增 REST 提示词版本创建功能 ([#13846](https://github.com/Arize-ai/phoenix/issues/13846)) ([dbf15e9](https://github.com/Arize-ai/phoenix/commit/dbf15e93922bb62c99cce56e6bfe94e8e5590701))
* **server:** 新增 GET /model_providers REST 端点 ([#15561](https://github.com/Arize-ai/phoenix/issues/15561)) ([59c247a](https://github.com/Arize-ai/phoenix/commit/59c247a19f868f157da511b1feca0338adef28e3))
* **server:** 新增 PATCH /projects/{project_identifier}/retention ([#15410](https://github.com/Arize-ai/phoenix/issues/15410)) ([8ffd938](https://github.com/Arize-ai/phoenix/commit/8ffd9389946a3a7a54f476f17fc3b20efa3260d3))


<a id="bug-fixes-1"></a>

### 问题修复

* **atif:** 将系统子 Agent 关联至输出的父 span ([#15585](https://github.com/Arize-ai/phoenix/issues/15585)) ([22ee343](https://github.com/Arize-ai/phoenix/commit/22ee34342f2264c1f9fa5053464dfdc36843d9e4))
* **client:** 根据 sys.platform 缩小环境文件所有权检查范围 ([#15927](https://github.com/Arize-ai/phoenix/issues/15927)) ([96e8805](https://github.com/Arize-ai/phoenix/commit/96e88059c3aa2d936b56435440f5f5e99a346b70))
* **playground:** 保留 Anthropic 和 Bedrock 的工具选择及 strict 设置 ([#15683](https://github.com/Arize-ai/phoenix/issues/15683)) ([5464de4](https://github.com/Arize-ai/phoenix/commit/5464de456a5488f461e1f9316c90ec1a0f35a286))
* 升级至 anthropic SDK v1 ([#15588](https://github.com/Arize-ai/phoenix/issues/15588)) ([b28cf94](https://github.com/Arize-ai/phoenix/commit/b28cf94fcd37afeacfd059b4a01e7ad38327e483))


<a id="performance-improvements"></a>

### 性能改进

* **agents:** 使系统提示词保持静态，并将 UI 状态移至轮次中 ([#15541](https://github.com/Arize-ai/phoenix/issues/15541)) ([31fafc5](https://github.com/Arize-ai/phoenix/commit/31fafc5fee359b038fcd75c515584a40fcfa2ea8))


<a id="miscellaneous-chores"></a>

### 其他维护

* 发布 arize-phoenix-client 3.4.0 ([f8561dc](https://github.com/Arize-ai/phoenix/commit/f8561dc165fb83acd58abd33642d1e12e1b71ef2))

## [3.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v3.2.0...arize-phoenix-client-v3.3.0) (2026-08-22)


<a id="features-2"></a>

### 新功能

* **pxi:** 默认启用 phoenix-gql 变更，并在手动模式下审批 ([#15415](https://github.com/Arize-ai/phoenix/issues/15415)) ([391d0dd](https://github.com/Arize-ai/phoenix/commit/391d0ddaa6aa2ec9bdda152ec6dd16ea585abb87))

## [3.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v3.1.0...arize-phoenix-client-v3.2.0) (2026-08-14)


<a id="features-3"></a>

### 新功能

* **server:** 新增 POST /traces/transfer ([#15363](https://github.com/Arize-ai/phoenix/issues/15363)) ([5c38cc7](https://github.com/Arize-ai/phoenix/commit/5c38cc7ff2398569da3bbb23aa9a384ad73a0134))

## [3.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v3.0.0...arize-phoenix-client-v3.1.0) (2026-08-11)


<a id="features-4"></a>

### 新功能

* 新增 Agent 会话持久化 ([#14143](https://github.com/Arize-ai/phoenix/issues/14143)) ([986f6a6](https://github.com/Arize-ai/phoenix/commit/986f6a6fdaeda70d83e2d91f150f9b01d9b8406f))


<a id="miscellaneous-chores-1"></a>

### 其他维护

* 发布 arize-phoenix-client 3.1.0 ([#15348](https://github.com/Arize-ai/phoenix/issues/15348)) ([85e0855](https://github.com/Arize-ai/phoenix/commit/85e0855c7120d2894653b802b42a74c073dc77cc))

## [3.0.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.13.0...arize-phoenix-client-v3.0.0) (2026-08-11)


<a id="-breaking-changes-1"></a>

### ⚠ 不兼容变更

* **client:** 将 google-generativeai 格式化器替换为 google-genai ([#15085](https://github.com/Arize-ai/phoenix/issues/15085))

<a id="features-5"></a>

### 新功能

* 新增提示词元数据更新 REST 端点 ([#13731](https://github.com/Arize-ai/phoenix/issues/13731)) ([244ef9c](https://github.com/Arize-ai/phoenix/commit/244ef9c7e0da3f60c5e800dc25c26c826ebc3c3f))
* **agents:** 将 PXI 追踪移至服务端 ([#14215](https://github.com/Arize-ai/phoenix/issues/14215)) ([ea40aea](https://github.com/Arize-ai/phoenix/commit/ea40aea40a1ad8f0a5abe1b9c2172973aa339aa3))
* **api:** 新增设置实验标签的 REST 端点 ([#15237](https://github.com/Arize-ai/phoenix/issues/15237)) ([c892873](https://github.com/Arize-ai/phoenix/commit/c8928738d8a9cd70875e01852306de7060febf5d))
* **api:** 公开数据集示例的来源 span ([#13814](https://github.com/Arize-ai/phoenix/issues/13814)) ([e0cf022](https://github.com/Arize-ai/phoenix/commit/e0cf0229c95ba43c33f66ed7040cf6e79e894b37))
* **api:** 新增用户和系统 API 密钥 REST 增删改查 ([257a77d](https://github.com/Arize-ai/phoenix/commit/257a77d5812916ff575f9b494dbdbd8534e8b14c))
* **api:** 以统一权限模型提供用户和系统 API 密钥 REST 增删改查 ([50cc3db](https://github.com/Arize-ai/phoenix/commit/50cc3db8e8a1e692f1758d232100a2489837ea89))
* **client:** 为 Python 和 TypeScript 客户端 get_spans 新增 span_ids 过滤器 ([#14697](https://github.com/Arize-ai/phoenix/issues/14697)) ([df7057a](https://github.com/Arize-ai/phoenix/commit/df7057ab12639e7333f755ced1fc3f36af5a054e))
* **client:** 将 google-generativeai 格式化器替换为 google-genai ([#15085](https://github.com/Arize-ai/phoenix/issues/15085)) ([5cf9829](https://github.com/Arize-ai/phoenix/commit/5cf9829c4398d784c004c9c976cd7b6739f2aa99))
* **client:** 支持更新提示词描述和元数据 ([#15191](https://github.com/Arize-ai/phoenix/issues/15191)) ([90729f3](https://github.com/Arize-ai/phoenix/commit/90729f3f51f25f50fbd920d2117d0eee4c85db8e))
* **dsl:** 分析根 span 作用域，避免重复应用 ([#14598](https://github.com/Arize-ai/phoenix/issues/14598)) ([aa9254e](https://github.com/Arize-ai/phoenix/commit/aa9254e4fb34a772e1fd8fc3e9882ba405a8448f))
* **js:** 将 PHOENIX_ENDPOINT 设为 API 访问的规范环境变量 ([e90ba00](https://github.com/Arize-ai/phoenix/commit/e90ba00110ac4cb9717e7f341aa81c9d418d1420))
* **pytest:** 为 pytest 插件新增评估器追踪隔离和实验元数据 ([#14613](https://github.com/Arize-ai/phoenix/issues/14613)) ([d81ee21](https://github.com/Arize-ai/phoenix/commit/d81ee219cb57e5035b535691710256d0561cd66c))
* **server:** 新增数据集划分创建、更新和删除 REST 端点 ([#14046](https://github.com/Arize-ai/phoenix/issues/14046)) ([b4d9b19](https://github.com/Arize-ai/phoenix/commit/b4d9b19e6c681cedcf627fc27dc48f13c7320b73))
* **server:** 新增使用服务端凭证、兼容 OpenAI 的 v1/chat/completions 代理 ([#14980](https://github.com/Arize-ai/phoenix/issues/14980)) ([6ab57db](https://github.com/Arize-ai/phoenix/commit/6ab57dbfe042fc4cc82e291cbbb7ced9940d4400))
* **ui:** 将根 span 作用域移入过滤条件 ([#14599](https://github.com/Arize-ai/phoenix/issues/14599)) ([a4a2a78](https://github.com/Arize-ai/phoenix/commit/a4a2a787e1e7d937557fa14fd724c87b34f44585))


<a id="bug-fixes-2"></a>

### 问题修复

* **agents:** 从系统提示词中移除浏览器时钟以保留提示词缓存 ([#14362](https://github.com/Arize-ai/phoenix/issues/14362)) ([c5dbb20](https://github.com/Arize-ai/phoenix/commit/c5dbb2034961ab99eefb67eaf8bcc9cf77a6a97f))
* **client:** 沿整个变量链解析 API 基础 URL ([7d98162](https://github.com/Arize-ai/phoenix/commit/7d981621c387a7ce7f93de645cd0f66ef5d7f3a4))
* 消除 Python 和接入流程中剩余的端点变量易错用法 ([ed90e0e](https://github.com/Arize-ai/phoenix/commit/ed90e0edf16fe7dfe3e6d0c5ae0925a3457daf18))
* **evals:** 将 AsyncExecutor 超时计入 max_retries ([#14361](https://github.com/Arize-ai/phoenix/issues/14361)) ([90eee08](https://github.com/Arize-ai/phoenix/commit/90eee082b9e357a6669df29bc926a68f731fbc43))
* **phoenix-client:** 为 README 浅色和深色主题提供正确标志版本 ([8fd355a](https://github.com/Arize-ai/phoenix/commit/8fd355a2268030ffa2b8cf013deeb2a6d933bb23))


<a id="documentation-1"></a>

### 文档

* **client:** 停止在 Python 客户端 README 中逐项列出端点回退 ([95e8282](https://github.com/Arize-ai/phoenix/commit/95e82826b46917a2d92eafc27e1581148f204963))
* 补齐评估、追踪、playground 和软件包的少量功能文档缺口 ([e5764b3](https://github.com/Arize-ai/phoenix/commit/e5764b348eeaca2d824638264b9d929c5a730c5a))
* 将包文档中的 app.phoenix.arize.com 替换为通用占位符 ([23deebc](https://github.com/Arize-ai/phoenix/commit/23deebcc2ff045297d86be44b9b6291bf0461151))
* 精简端点文档，仅保留原位修正 ([0f6aa07](https://github.com/Arize-ai/phoenix/commit/0f6aa07cdc8084189e58d0ec686df3ec2fc7e60c))

## [2.13.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.12.0...arize-phoenix-client-v2.13.0) (2026-07-12)


<a id="features-6"></a>

### 新功能

* **client:** 为 Python 客户端 projects.list() 新增 name_contains 过滤器 ([#14132](https://github.com/Arize-ai/phoenix/issues/14132)) ([fa79dc0](https://github.com/Arize-ai/phoenix/commit/fa79dc0f249a5a8a205521af79b7c7946d814d9c))，关闭 [#14034](https://github.com/Arize-ai/phoenix/issues/14034)
* 新增 Phoenix 环境文件 ([#14188](https://github.com/Arize-ai/phoenix/issues/14188)) ([c0ab6a9](https://github.com/Arize-ai/phoenix/commit/c0ab6a9715bd8050094f8ac4135c7fa5d556c453))
* **sdk:** 各处均接受 PHOENIX_PROJECT_NAME 和 PHOENIX_PROJECT ([#14167](https://github.com/Arize-ai/phoenix/issues/14167)) ([1e7d9fc](https://github.com/Arize-ai/phoenix/commit/1e7d9fc3cd21aca4f221884b963ab20404c70eaf))

## [2.12.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.11.0...arize-phoenix-client-v2.12.0) (2026-07-03)


<a id="features-7"></a>

### 新功能

* **api:** 支持通过 REST 向项目分配标注配置 ([#14028](https://github.com/Arize-ai/phoenix/issues/14028)) ([83d3cef](https://github.com/Arize-ai/phoenix/commit/83d3cef5e5f4bfef2399ca6cb52f208673b9036b))
* **server:** 新增数据集标签 REST 端点 ([#14024](https://github.com/Arize-ai/phoenix/issues/14024)) ([67f84ba](https://github.com/Arize-ai/phoenix/commit/67f84ba8e2b65aaa74684a9633167eb4343acbb6))


<a id="bug-fixes-3"></a>

### 问题修复

* 异步客户端使用相同超时策略 ([#13796](https://github.com/Arize-ai/phoenix/issues/13796)) ([fc0e5f8](https://github.com/Arize-ai/phoenix/commit/fc0e5f8f7f7999c1211d5d7fe012bd5270ad9e92))


<a id="documentation-2"></a>

### 文档

* 补齐 2026-06-24→07-01 审计发现的文档缺口 ([#14015](https://github.com/Arize-ai/phoenix/issues/14015)) ([337a622](https://github.com/Arize-ai/phoenix/commit/337a622496ed43aae186b09ce488954c3fb27ad4))

## [2.11.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.10.0...arize-phoenix-client-v2.11.0) (2026-06-30)


<a id="features-8"></a>

### 新功能

* **ui:** 在项目设置中新增标注汇总 ([#13850](https://github.com/Arize-ai/phoenix/issues/13850)) ([05582a1](https://github.com/Arize-ai/phoenix/commit/05582a132f5400bdaf7451c0e954df286ee09a81))


<a id="bug-fixes-4"></a>

### 问题修复

* 在 create_dataset 和 add_examples_to_dataset 中保留生成器输入 ([#13791](https://github.com/Arize-ai/phoenix/issues/13791)) ([c629b70](https://github.com/Arize-ai/phoenix/commit/c629b70cd4771918f0b185261793683b16739419))


<a id="documentation-3"></a>

### 文档

* **phoenix-client:** 纠正 create_evaluator 二元组评分器文档 ([#13939](https://github.com/Arize-ai/phoenix/issues/13939)) ([f123759](https://github.com/Arize-ai/phoenix/commit/f123759e80d729102a584759d6f7c2d07fa7b044))

## [2.10.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.9.0...arize-phoenix-client-v2.10.0) (2026-06-26)


<a id="features-9"></a>

### 新功能

* 新增直接服务端 Agent 端点 ([#13896](https://github.com/Arize-ai/phoenix/issues/13896)) ([6e93f93](https://github.com/Arize-ai/phoenix/commit/6e93f93d0f1c608b2f3f612f9cf9f5abc792cf1e))
* **agents:** 新增会话上下文 ([#13727](https://github.com/Arize-ai/phoenix/issues/13727)) ([031975c](https://github.com/Arize-ai/phoenix/commit/031975ccbe60e50967d8f192b6dfe6ca6de1daa7))
* **agents:** 新增实验编辑和评估技能 ([#13704](https://github.com/Arize-ai/phoenix/issues/13704)) ([50b376e](https://github.com/Arize-ai/phoenix/commit/50b376e1d833e69bff2ae4a5e0251d68f33e3af4))
* **phoenix-client:** 新增评估 CI 的 pytest 插件 ([#13874](https://github.com/Arize-ai/phoenix/issues/13874)) ([6ebe82c](https://github.com/Arize-ai/phoenix/commit/6ebe82cb900d90fdd1fd6d6afc82bf8e76ec82ea))
* **pxi:** 新增提示词路由上下文 ([#13834](https://github.com/Arize-ai/phoenix/issues/13834)) ([4524f82](https://github.com/Arize-ai/phoenix/commit/4524f829eea23afb016c8c77e30cd5066a11957f))

## [2.9.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.8.0...arize-phoenix-client-v2.9.0) (2026-06-11)


<a id="features-10"></a>

### 新功能

* 新增 playground 重复运行工具 ([#13656](https://github.com/Arize-ai/phoenix/issues/13656)) ([ad4a659](https://github.com/Arize-ai/phoenix/commit/ad4a65993d83564a47692bb79db494a88112853e))
* **agents:** 新增用户可调用的技能菜单 ([#13670](https://github.com/Arize-ai/phoenix/issues/13670)) ([4f6cb6e](https://github.com/Arize-ai/phoenix/commit/4f6cb6e388e8ade433bb2088592aa391916fdb4b))
* **pxi:** 新增 playground 实验记录工具 ([#13678](https://github.com/Arize-ai/phoenix/issues/13678)) ([15912cb](https://github.com/Arize-ai/phoenix/commit/15912cb5787c9fa11ba7e35ade1ea40868139290))


<a id="bug-fixes-5"></a>

### 问题修复

* **client:** 按节点 GlobalID 记录和解析实验示例 ([#13702](https://github.com/Arize-ai/phoenix/issues/13702)) ([0347f22](https://github.com/Arize-ai/phoenix/commit/0347f2203947d95b6b3ddf66835b256540229fb0))

## [2.8.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.7.0...arize-phoenix-client-v2.8.0) (2026-06-08)


<a id="-breaking-changes-2"></a>

### ⚠ 不兼容变更

* 新增沙箱和代码评估器 ([#13290](https://github.com/Arize-ai/phoenix/issues/13290))

<a id="features-11"></a>

### 新功能

* 新增 PXI playground 模型切换工具 ([#13499](https://github.com/Arize-ai/phoenix/issues/13499)) ([ad2013a](https://github.com/Arize-ai/phoenix/commit/ad2013a2103681501d53827417094c0a68cfe03e))
* **agents:** 新增 span 标注工具 ([#13502](https://github.com/Arize-ai/phoenix/issues/13502)) ([4c8262c](https://github.com/Arize-ai/phoenix/commit/4c8262ca60b1abcb19d000f9f8477ba30b6cf5e1))
* **agents:** 在可用时启用提供方原生 Web 搜索和获取 ([#13333](https://github.com/Arize-ai/phoenix/issues/13333)) ([41eb4fc](https://github.com/Arize-ai/phoenix/commit/41eb4fcb0721107bf22f19ff5c7121a5e7620f67))
* **agents:** 在工具调用提供方元数据上记录工具执行环境 ([#13277](https://github.com/Arize-ai/phoenix/issues/13277)) ([ef421e5](https://github.com/Arize-ai/phoenix/commit/ef421e5af20289214b9e77b30d4c45709e0b3da6))
* **pxi:** 支持编写代码评估器 ([#13397](https://github.com/Arize-ai/phoenix/issues/13397)) ([cef8f13](https://github.com/Arize-ai/phoenix/commit/cef8f131dcca2e3c81b5f83bca403959c0d7b95f))
* 新增沙箱和代码评估器 ([#13290](https://github.com/Arize-ai/phoenix/issues/13290)) ([e294d93](https://github.com/Arize-ai/phoenix/commit/e294d939fb6c5fbbcca0c3460334dd08f1b3b43e))


<a id="bug-fixes-6"></a>

### 问题修复

* **client:** 丢弃 Google top_k，不再映射至 OpenAI top_logprobs ([#13640](https://github.com/Arize-ai/phoenix/issues/13640)) ([f98e856](https://github.com/Arize-ai/phoenix/commit/f98e8568164120b44d3983fa3c096b692c560f83))


<a id="miscellaneous-chores-2"></a>

### 其他维护

* 发布 arize-phoenix-client 2.8.0 ([#13390](https://github.com/Arize-ai/phoenix/issues/13390)) ([eff1c2a](https://github.com/Arize-ai/phoenix/commit/eff1c2af08e35f5b3f3f2f9f83039fcdbb3e4bb9))

## [2.7.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.6.0...arize-phoenix-client-v2.7.0) (2026-05-15)


<a id="features-12"></a>

### 新功能

* **agents:** 新增 /agents/{agent_id}/sessions/{session_id}/summary 端点 ([#13095](https://github.com/Arize-ai/phoenix/issues/13095)) ([419c3a0](https://github.com/Arize-ai/phoenix/commit/419c3a06978abce8f611569228438929f8e7b995))
* **agents:** 新增带确认的 Playground 操作工具 ([#13093](https://github.com/Arize-ai/phoenix/issues/13093)) ([37dc417](https://github.com/Arize-ai/phoenix/commit/37dc417f8880a101b34a41f8d2ea3f58099df6c2))
* **agents:** 移除 v1 /chat 路由及相关代码 ([#13140](https://github.com/Arize-ai/phoenix/issues/13140)) ([71ceeb3](https://github.com/Arize-ai/phoenix/commit/71ceeb3fa68ceac509e0cd38bb3497c0737774c0))
* **app:** 根据 OpenAPI schema 为前端 REST 调用添加类型 ([#13060](https://github.com/Arize-ai/phoenix/issues/13060)) ([590669d](https://github.com/Arize-ai/phoenix/commit/590669d1a68f48b3af7b7d1b5666f854d0465b63))
* 限制 Agent 会话保留时间 ([#13220](https://github.com/Arize-ai/phoenix/issues/13220)) ([1c28249](https://github.com/Arize-ai/phoenix/commit/1c282498eced055454b254359d148a82087ecbbd))
* **client:** 支持上传 ATIF v1.7 轨迹 ([#13107](https://github.com/Arize-ai/phoenix/issues/13107)) ([17f2ec2](https://github.com/Arize-ai/phoenix/commit/17f2ec275ba239d6e2e8ab4ccc92753c74020159))
* **phoenix-client:** 新增 TS 追踪标注、明确备注语义并审计技能 ([#12923](https://github.com/Arize-ai/phoenix/issues/12923)) ([2993b04](https://github.com/Arize-ai/phoenix/commit/2993b04a30554a752322b44a677721ae9ded91cc))
* **rest-api:** 在 span、追踪和会话载荷中包含 token 计数 ([#12926](https://github.com/Arize-ai/phoenix/issues/12926)) ([c0c0edb](https://github.com/Arize-ai/phoenix/commit/c0c0edba49f039c1ab893a3cbd51d48b2782de4c))
* 为开放编码和主轴编码工作流提供带会话标签的标识符 ([#13083](https://github.com/Arize-ai/phoenix/issues/13083)) ([6dceb10](https://github.com/Arize-ai/phoenix/commit/6dceb101b6409cb50e90baeb83e1e7c1784745e1))
* 支持厂商透传工具 ([#12533](https://github.com/Arize-ai/phoenix/issues/12533)) ([41e8fe0](https://github.com/Arize-ai/phoenix/commit/41e8fe0272752882d888d782b5023bcdf0e08ac8))


<a id="documentation-4"></a>

### 文档

* 在 X/Bluesky 旁新增 LinkedIn 社交链接 ([#12993](https://github.com/Arize-ai/phoenix/issues/12993)) ([5d14f23](https://github.com/Arize-ai/phoenix/commit/5d14f23598202c062530466a9dbdc9a1a033d6c8))

## [2.6.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.5.0...arize-phoenix-client-v2.6.0) (2026-04-29)


<a id="-breaking-changes-3"></a>

### ⚠ 不兼容变更

* 新增数据集 upsert ([#11860](https://github.com/Arize-ai/phoenix/issues/11860))

<a id="features-13"></a>

### 新功能

* **api:** 新增会话备注端点 ([#12902](https://github.com/Arize-ai/phoenix/issues/12902)) ([187df7e](https://github.com/Arize-ai/phoenix/commit/187df7e8abf20b3a6c3e851bcde373229d0e7f05))
* **client:** 按服务器版本限制 v15 数据集上传参数 ([#12934](https://github.com/Arize-ai/phoenix/issues/12934)) ([e381885](https://github.com/Arize-ai/phoenix/commit/e3818859ee858f5e67d32968633a5d0467801026))
* 新增数据集 upsert ([#11860](https://github.com/Arize-ai/phoenix/issues/11860)) ([9575738](https://github.com/Arize-ai/phoenix/commit/957573865202d2ee49c21eb1c73265760e07f2f9))
* 扩充数据库提示词类型以支持调用参数 ([#12855](https://github.com/Arize-ai/phoenix/issues/12855)) ([1499ca9](https://github.com/Arize-ai/phoenix/commit/1499ca956de972ba523d57e7af49b84e693f895a))


<a id="miscellaneous-chores-3"></a>

### 其他维护

* **client:** 将 release-please 版本设为 2.6.0 ([#12930](https://github.com/Arize-ai/phoenix/issues/12930)) ([883a4eb](https://github.com/Arize-ai/phoenix/commit/883a4eb9a9b9df88576473092f80eaaff66a9bdb))

## [2.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.4.0...arize-phoenix-client-v2.5.0) (2026-04-25)


<a id="features-14"></a>

### 新功能

* 为 Phoenix CLI 新增追踪备注 REST 端点 ([#12710](https://github.com/Arize-ai/phoenix/issues/12710)) ([ed66c02](https://github.com/Arize-ai/phoenix/commit/ed66c02805ef17d9dcd812f998a62d66cb611f83))

## [2.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.3.1...arize-phoenix-client-v2.4.0) (2026-04-22)


<a id="features-15"></a>

### 新功能

* **client:** 向实验评估器透传 trace_id ([#12692](https://github.com/Arize-ai/phoenix/issues/12692)) ([648b6e1](https://github.com/Arize-ai/phoenix/commit/648b6e19e18fbb2a74e89424d3331ea79ce42e4d))
* **rest-api:** 为 GET /v1/spans 新增类型感知属性过滤 ([#12524](https://github.com/Arize-ai/phoenix/issues/12524)) ([c0badfa](https://github.com/Arize-ai/phoenix/commit/c0badfaa0a5f71a7415f339459d5977df77fb619))


<a id="documentation-5"></a>

### 文档

* 新增 ATIF 轨迹导入文档 ([#12631](https://github.com/Arize-ai/phoenix/issues/12631)) ([ef9e6cc](https://github.com/Arize-ai/phoenix/commit/ef9e6cc12dfe54136f2f90b83718f7b98bb2597c))
* 修复 phoenix.client.experiments 文档和教程 ([#12645](https://github.com/Arize-ai/phoenix/issues/12645)) ([9ce9e18](https://github.com/Arize-ai/phoenix/commit/9ce9e1859d5712f992bdae830385f11ccca022be))

## [2.3.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.3.0...arize-phoenix-client-v2.3.1) (2026-04-07)


<a id="-breaking-changes-4"></a>

### ⚠ 不兼容变更

* **evals:** 弃用 evals 1.0 并移除旧版 experiments 模块 ([#12239](https://github.com/Arize-ai/phoenix/issues/12239))

<a id="features-16"></a>

### 新功能

* **evals:** 弃用 evals 1.0 并移除旧版 experiments 模块 ([#12239](https://github.com/Arize-ai/phoenix/issues/12239)) ([15e6415](https://github.com/Arize-ai/phoenix/commit/15e6415105ce4757de905172cbd0e07215d38990))


<a id="miscellaneous-chores-4"></a>

### 其他维护

* 发布 2.3.1 ([#12572](https://github.com/Arize-ai/phoenix/issues/12572)) ([a33630d](https://github.com/Arize-ai/phoenix/commit/a33630d1913c2c43a6d2f3c39056ea11a2de8bee))

## [2.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.2.0...arize-phoenix-client-v2.3.0) (2026-04-03)


<a id="features-17"></a>

### 新功能

* 新增 ATIF 转追踪轨迹工具 ([#12414](https://github.com/Arize-ai/phoenix/issues/12414)) ([28ecfe0](https://github.com/Arize-ai/phoenix/commit/28ecfe023f3d94f97afa36b7161f80e1d316cc39))

## [2.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.1.0...arize-phoenix-client-v2.2.0) (2026-04-01)


<a id="features-18"></a>

### 新功能

* 新增 GET /v1/user 端点和 phoenix-rest-api 技能 ([#12274](https://github.com/Arize-ai/phoenix/issues/12274)) ([b5188ea](https://github.com/Arize-ai/phoenix/commit/b5188ea92eeb76ed0155e999b8fa0fc00519f32c))
* 新增 Python 3.14 支持（Windows 除外） ([#12475](https://github.com/Arize-ai/phoenix/issues/12475)) ([50c08e3](https://github.com/Arize-ai/phoenix/commit/50c08e3ff4e41c0693e92b7d3de7dbc41384fad1))
* **client:** 为 Python 和 TypeScript 客户端新增 get_traces 方法 ([#12245](https://github.com/Arize-ai/phoenix/issues/12245)) ([7d3f4ac](https://github.com/Arize-ai/phoenix/commit/7d3f4aca8d5bc3e6df3e5a4f69332fa8ffcc274d))
* **server:** 新增密钥管理 REST 端点 ([#12429](https://github.com/Arize-ai/phoenix/issues/12429)) ([39f68cf](https://github.com/Arize-ai/phoenix/commit/39f68cf5449a5df04e4b8901975c01bbf76e93fc))


<a id="documentation-6"></a>

### 文档

* **evals:** 弃用 evals 1.0 文档 ([#12123](https://github.com/Arize-ai/phoenix/issues/12123)) ([b0dc90f](https://github.com/Arize-ai/phoenix/commit/b0dc90f445a25ba74ddc86e0cc8bcdf721260344))
* 根据最新能力更新所有软件包 README ([#12315](https://github.com/Arize-ai/phoenix/issues/12315)) ([b4ded15](https://github.com/Arize-ai/phoenix/commit/b4ded157987e0ce6fcbf749bf48225d9408313c2))
* 根据近期功能更新软件包 README ([#12259](https://github.com/Arize-ai/phoenix/issues/12259)) ([d204898](https://github.com/Arize-ai/phoenix/commit/d204898cf63b48604e82403c1c6056fbb72fb860))

## [2.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.0.1...arize-phoenix-client-v2.1.0) (2026-03-18)


<a id="features-19"></a>

### 新功能

* **client:** 为 getSpans 新增 span 过滤参数 ([#12203](https://github.com/Arize-ai/phoenix/issues/12203)) ([91949d7](https://github.com/Arize-ai/phoenix/commit/91949d7aa63acff7110ec79518d9ad9ce711e277))

## [2.0.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v2.0.0...arize-phoenix-client-v2.0.1) (2026-03-14)


<a id="bug-fixes-7"></a>

### 问题修复

* **client:** 根据能力要求限制服务器版本 ([#12122](https://github.com/Arize-ai/phoenix/issues/12122)) ([9769f90](https://github.com/Arize-ai/phoenix/commit/9769f906ae0caef8e19f88e25e0ea545ee399d72))

## [2.0.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.31.0...arize-phoenix-client-v2.0.0) (2026-03-11)


<a id="-breaking-changes-5"></a>

### ⚠ 不兼容变更

* **client:** 已移除 `client.annotations`。改用 `client.spans`。

<a id="features-20"></a>

### 新功能

* 新增 Cerebras、Fireworks、Groq 和 Moonshot 一等支持提供方 ([#11938](https://github.com/Arize-ai/phoenix/issues/11938)) ([df94203](https://github.com/Arize-ai/phoenix/commit/df94203fa621bae9928d96249382380aa4be5443))
* 在 playground 中新增 Perplexity 和 Together AI 内置提供方 ([#11952](https://github.com/Arize-ai/phoenix/issues/11952)) ([aeefe19](https://github.com/Arize-ai/phoenix/commit/aeefe1970405c7fcb48254dce92dcfc1824fcaa3))
* 为客户端 getSpans 方法新增 trace_ids 参数 ([#11945](https://github.com/Arize-ai/phoenix/issues/11945)) ([6d896e3](https://github.com/Arize-ai/phoenix/commit/6d896e32ce1d4ed2038342ae67d678de2163e8f0))
* **client:** 为 Python 和 TypeScript 客户端新增会话对话 API ([#11974](https://github.com/Arize-ai/phoenix/issues/11974)) ([83b7f68](https://github.com/Arize-ai/phoenix/commit/83b7f68782b4994a741244c478d5d561e4817bcb))
* **client:** 向 JS 和 Python 客户端传递 parent_id 过滤器 ([#11975](https://github.com/Arize-ai/phoenix/issues/11975)) ([d951320](https://github.com/Arize-ai/phoenix/commit/d951320f704545a516ccd63d2acbc88a35685491))
* **client:** 移除已弃用的 `client.annotations` 模块 ([#11983](https://github.com/Arize-ai/phoenix/issues/11983)) ([6203c31](https://github.com/Arize-ai/phoenix/commit/6203c31fc59579dfbe927d47ca0d03d162d7fb77))
* **server:** 新增 DELETE 会话 API  ([#11976](https://github.com/Arize-ai/phoenix/issues/11976)) ([d4a865a](https://github.com/Arize-ai/phoenix/commit/d4a865ae6bc1511b2b433b408de2f75bf71abc7b))

## [1.31.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.30.0...arize-phoenix-client-v1.31.0) (2026-03-06)


<a id="features-21"></a>

### 新功能

* **client:** 为 Python 客户端 SDK 新增会话获取方法 ([#11879](https://github.com/Arize-ai/phoenix/issues/11879)) ([3669813](https://github.com/Arize-ai/phoenix/commit/3669813c7486b128d8858de6ef1cffa3e8d5c020))
* **client:** 为 sessions API 新增超时和 list_sessions 别名 ([#11897](https://github.com/Arize-ai/phoenix/issues/11897)) ([a4befc0](https://github.com/Arize-ai/phoenix/commit/a4befc0f6bfe3a0641eca58eb2f35226ec54f4d6))

## [1.30.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.29.1...arize-phoenix-client-v1.30.0) (2026-03-02)


<a id="features-22"></a>

### 新功能

* 新增会话 REST API 的 GET 端点 ([#11724](https://github.com/Arize-ai/phoenix/issues/11724)) ([2a1f148](https://github.com/Arize-ai/phoenix/commit/2a1f14846cec30bb9b892114f3510e740154bcc0))

## [1.29.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.29.0...arize-phoenix-client-v1.29.1) (2026-02-24)


<a id="bug-fixes-8"></a>

### 问题修复

* 新增删除实验后删除项目的参数 ([#11569](https://github.com/Arize-ai/phoenix/issues/11569)) ([57b7576](https://github.com/Arize-ai/phoenix/commit/57b7576408bc21b46ea03009f741c9ebb0a55ca1))
* 更新 JS 和 Python 软件包的 README 片段 ([#11479](https://github.com/Arize-ai/phoenix/issues/11479)) ([76de803](https://github.com/Arize-ai/phoenix/commit/76de8039d86e81cf3a1749aef3da0128977aa4e7))
* 更新 Slack 邀请链接 ([#11612](https://github.com/Arize-ai/phoenix/issues/11612)) ([316833e](https://github.com/Arize-ai/phoenix/commit/316833e629baf1b9185d7c712d8816b927d69a96))

## [1.29.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.28.1...arize-phoenix-client-v1.29.0) (2026-02-13)


<a id="features-23"></a>

### 新功能

* 新增数据集评估器 ([5f47820](https://github.com/Arize-ai/phoenix/commit/5f4782012537d533570184a6ce1e005e9945d8bf))
* 新增数据集评估器 ([cf0e09a](https://github.com/Arize-ai/phoenix/commit/cf0e09a82a5e44c9df26619c6372d2474a289b49))

## [1.28.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.28.0...arize-phoenix-client-v1.28.1) (2026-02-09)


<a id="bug-fixes-9"></a>

### 问题修复

* 为 log_spans_dataframe 新增时区校验 ([#11283](https://github.com/Arize-ai/phoenix/issues/11283)) ([45a07bb](https://github.com/Arize-ai/phoenix/commit/45a07bb37c81dfd993d36172adc20ecbf01f9937))

## [1.28.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.27.2...arize-phoenix-client-v1.28.0) (2026-01-21)


<a id="features-24"></a>

### 新功能

* 新增 FaithfulnessEvaluator 并弃用 HallucinationEvaluator ([#10962](https://github.com/Arize-ai/phoenix/issues/10962)) ([fc8b1b5](https://github.com/Arize-ai/phoenix/commit/fc8b1b5eaeadbd4e23ed684f0f2286f5a55d00a2))
* 新增 span_id_key 以将数据集示例关联至追踪 ([#10942](https://github.com/Arize-ai/phoenix/issues/10942)) ([01eb1fb](https://github.com/Arize-ai/phoenix/commit/01eb1fbaa7ac029f044842d683f35c3fb21da627))

## [1.27.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.27.1...arize-phoenix-client-v1.27.2) (2026-01-08)


<a id="bug-fixes-10"></a>

### 问题修复

* DataFrame 使用整数索引时，使用 context.span_id 列 ([#10861](https://github.com/Arize-ai/phoenix/issues/10861)) ([607558d](https://github.com/Arize-ai/phoenix/commit/607558dff70500eee53d00f369936d4f5dce2db7))

## [1.27.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.27.0...arize-phoenix-client-v1.27.1) (2025-12-16)


<a id="bug-fixes-11"></a>

### 问题修复

* 更新 OpenAI 的 `reasoning_effort` 选项 ([#10620](https://github.com/Arize-ai/phoenix/issues/10620)) ([5132ce4](https://github.com/Arize-ai/phoenix/commit/5132ce4743d2e9aa0dd509b1c277f1eb800345aa))

## [1.27.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.26.0...arize-phoenix-client-v1.27.0) (2025-12-11)


<a id="features-25"></a>

### 新功能

* 为 Python 客户端新增 span 备注函数 ([#10521](https://github.com/Arize-ai/phoenix/issues/10521)) ([ddeff2b](https://github.com/Arize-ai/phoenix/commit/ddeff2b08cdedd18a6b1fccc090ab495849be598))
* 新增 span 备注端点 ([#10508](https://github.com/Arize-ai/phoenix/issues/10508)) ([727cb23](https://github.com/Arize-ai/phoenix/commit/727cb234f822b992c2fa2a44f0f85d35a7de13a2))
* 支持轻量目录访问协议（LDAP） ([#10420](https://github.com/Arize-ai/phoenix/issues/10420)) ([f6aff97](https://github.com/Arize-ai/phoenix/commit/f6aff97b9a563f3f3f87a9b5b8d969152bb4ba47))

## [1.26.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.25.0...arize-phoenix-client-v1.26.0) (2025-11-25)


<a id="features-26"></a>

### 新功能

* **splits:** 允许在数据集上传时分配划分 ([#10353](https://github.com/Arize-ai/phoenix/issues/10353)) ([cb45336](https://github.com/Arize-ai/phoenix/commit/cb45336da7ed2016760de11772afd12e9d46f262))

## [1.25.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.24.0...arize-phoenix-client-v1.25.0) (2025-11-24)


<a id="features-27"></a>

### 新功能

* 新增评估辅助函数，便于获取 RAG span  ([#10341](https://github.com/Arize-ai/phoenix/issues/10341)) ([0c409ad](https://github.com/Arize-ai/phoenix/commit/0c409adf9eb5a61772ca2b9a7038ee31567f6964))

## [1.24.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.23.0...arize-phoenix-client-v1.24.0) (2025-11-19)


<a id="features-28"></a>

### 新功能

* 将客户端许可改为 Apache 2.0 ([#10332](https://github.com/Arize-ai/phoenix/issues/10332)) ([ee6f6ee](https://github.com/Arize-ai/phoenix/commit/ee6f6ee15deca45430aff2732fb5ac7253d82522))

## [1.23.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.22.0...arize-phoenix-client-v1.23.0) (2025-11-12)


<a id="features-29"></a>

### 新功能

* 支持实验重试 ([#10179](https://github.com/Arize-ai/phoenix/issues/10179)) ([e05fbe9](https://github.com/Arize-ai/phoenix/commit/e05fbe9f3279a5b872cb7cc905a58e6e6aa397a3))

## [1.22.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.21.0...arize-phoenix-client-v1.22.0) (2025-11-05)


<a id="features-30"></a>

### 新功能

* 将示例绑定至评估器 ([#9036](https://github.com/Arize-ai/phoenix/issues/9036)) ([04d2708](https://github.com/Arize-ai/phoenix/commit/04d270843a0e1c35aa8c55e78ee5d3adb6baabc8))
* 为提示词新增元数据 ([#10097](https://github.com/Arize-ai/phoenix/issues/10097)) ([0c92232](https://github.com/Arize-ai/phoenix/commit/0c92232a91679d1b8146167a26aecd20326fce9c))
* 按划分查询示例 ([#9762](https://github.com/Arize-ai/phoenix/issues/9762)) ([e698c9f](https://github.com/Arize-ai/phoenix/commit/e698c9f573e8022eff28c4cc4591c65ab5b39109))
* 支持恢复实验和评估 ([#9994](https://github.com/Arize-ai/phoenix/issues/9994)) ([557865c](https://github.com/Arize-ai/phoenix/commit/557865c60b08dee5b09912bd09dfd2593231f713))


<a id="bug-fixes-12"></a>

### 问题修复

* 为不存在的提示词返回明确错误消息，替代 HTTP 404 ([#9931](https://github.com/Arize-ai/phoenix/issues/9931)) ([b31be10](https://github.com/Arize-ai/phoenix/commit/b31be10220d02dc63dfd0027efdd627f30178812))
* **client:** 放宽 create_dataset 方法输入类型 ([#9995](https://github.com/Arize-ai/phoenix/issues/9995)) ([02dc536](https://github.com/Arize-ai/phoenix/commit/02dc53652eb7463be47728fb983e4aee8c5215c1))


<a id="documentation-7"></a>

### 文档

* **client:** 修复 get_dataset 文档字符串 ([#9728](https://github.com/Arize-ai/phoenix/issues/9728)) ([2d330f1](https://github.com/Arize-ai/phoenix/commit/2d330f1ff8ca45f0c462c9050723bbae6e792fd7))
* 迁移至 client.spans.log_ ([#9757](https://github.com/Arize-ai/phoenix/issues/9757)) ([aecb5fb](https://github.com/Arize-ai/phoenix/commit/aecb5fbbfb1ae6938b8d91ac0a1ff6f3a51113a9))
* 将 main 同步至文档 ([65a68f4](https://github.com/Arize-ai/phoenix/commit/65a68f4c05635e76068b2c85b2929b4d13ca2668))

## [1.21.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.20.0...arize-phoenix-client-v1.21.0) (2025-09-29)


<a id="features-31"></a>

### 新功能

* 新增用于添加追踪和会话标注的客户端方法 ([#9369](https://github.com/Arize-ai/phoenix/issues/9369)) ([e9b29ef](https://github.com/Arize-ai/phoenix/commit/e9b29ef0b50eb30c64d7e3c557d6264d5652d3fc))


<a id="documentation-8"></a>

### 文档

* 新增会话 API 文档 ([#9697](https://github.com/Arize-ai/phoenix/issues/9697)) ([d72e867](https://github.com/Arize-ai/phoenix/commit/d72e867a0971e608816c774816c845908f3b69bd))

## [1.20.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.19.1...arize-phoenix-client-v1.20.0) (2025-09-26)


<a id="features-32"></a>

### 新功能

* 支持重复运行 ([#9657](https://github.com/Arize-ai/phoenix/issues/9657)) ([0365f7f](https://github.com/Arize-ai/phoenix/commit/0365f7f3c72fc53b39d275f24d48426b7c547933))


<a id="bug-fixes-13"></a>

### 问题修复

* 实验追踪遵循 OITracer 配置 ([#9640](https://github.com/Arize-ai/phoenix/issues/9640)) ([f08b212](https://github.com/Arize-ai/phoenix/commit/f08b212f6d9857d25c19daeaec833227ef2061f1))

## [1.19.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.19.0...arize-phoenix-client-v1.19.1) (2025-09-19)


<a id="bug-fixes-14"></a>

### 问题修复

* **client:** 确保打印的 URL 适用于代理 URL ([#9552](https://github.com/Arize-ai/phoenix/issues/9552)) ([9135531](https://github.com/Arize-ai/phoenix/commit/9135531c75c6f7199145a1794648088b1c7b0d75))

## [1.19.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.18.2...arize-phoenix-client-v1.19.0) (2025-09-17)


<a id="features-33"></a>

### 新功能

* 兼容 Experiments&lt;-&gt;Evals 2.0 ([#9442](https://github.com/Arize-ai/phoenix/issues/9442)) ([90e4dbc](https://github.com/Arize-ai/phoenix/commit/90e4dbc08e63ee707f3ab7e42dc5146ad6054e82))

## [1.18.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.18.1...arize-phoenix-client-v1.18.2) (2025-09-11)


<a id="bug-fixes-15"></a>

### 问题修复

* **experiments:** 确保 repetitions 为正整数 ([#9479](https://github.com/Arize-ai/phoenix/issues/9479)) ([1b71c66](https://github.com/Arize-ai/phoenix/commit/1b71c666e88853de8bf40eec39ab634a8658f439))

## [1.18.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.18.0...arize-phoenix-client-v1.18.1) (2025-09-10)


<a id="bug-fixes-16"></a>

### 问题修复

* **client:** 处理文档标注 DataFrame 的多重索引 ([#9464](https://github.com/Arize-ai/phoenix/issues/9464)) ([042ff39](https://github.com/Arize-ai/phoenix/commit/042ff39dc21682454520bdd3b8575ad429add3e5))
* 补充弃用文档字符串中缺失的版本 ([#9453](https://github.com/Arize-ai/phoenix/issues/9453)) ([bb5ff83](https://github.com/Arize-ai/phoenix/commit/bb5ff83f847631b4ad071836e8dd7bddaafef3ab))

## [1.18.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.17.1...arize-phoenix-client-v1.18.0) (2025-09-04)


<a id="features-34"></a>

### 新功能

* 在 run_experiment 中分页获取实验运行 ([#9370](https://github.com/Arize-ai/phoenix/issues/9370)) ([8882afc](https://github.com/Arize-ai/phoenix/commit/8882afc2eb1901ffaad0bc9057eb65e1ec3bc337))

## [1.17.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.17.0...arize-phoenix-client-v1.17.1) (2025-09-04)


<a id="bug-fixes-17"></a>

### 问题修复

* 保持实验任务函数 example 参数向后兼容 ([#9374](https://github.com/Arize-ai/phoenix/issues/9374)) ([9dd3b8c](https://github.com/Arize-ai/phoenix/commit/9dd3b8cf09198fc611fb4ce1c6781afdfd07a0dc))

## [1.17.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.16.0...arize-phoenix-client-v1.17.0) (2025-09-03)


<a id="features-35"></a>

### 新功能

* 新增记录文档标注的方法 ([#9352](https://github.com/Arize-ai/phoenix/issues/9352)) ([26808b7](https://github.com/Arize-ai/phoenix/commit/26808b795a1333c40e79a62742a9ff0b631cd064))


<a id="documentation-9"></a>

### 文档

* 修复文档标注的文档字符串 ([#9367](https://github.com/Arize-ai/phoenix/issues/9367)) ([5a149f2](https://github.com/Arize-ai/phoenix/commit/5a149f23983725579939ee36ce358f659b0ef5bd))
* 修复文档字符串末尾逗号 ([#9339](https://github.com/Arize-ai/phoenix/issues/9339)) ([292cace](https://github.com/Arize-ai/phoenix/commit/292cace00b1fcb399bff2f6936a7715fa012ebe9))
* 修复标注文档字符串 ([#9337](https://github.com/Arize-ai/phoenix/issues/9337)) ([e1c713a](https://github.com/Arize-ai/phoenix/commit/e1c713a11e614b225f222493d8286b63e7a23452))

## [1.16.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.15.3...arize-phoenix-client-v1.16.0) (2025-08-30)


<a id="features-36"></a>

### 新功能

* 使 `get_spans_dataframe` 按 span 从新到旧或从旧到新排序 ([#9173](https://github.com/Arize-ai/phoenix/issues/9173)) ([2bf5819](https://github.com/Arize-ai/phoenix/commit/2bf58194ae6be3e63d08c64ccf71a96b1e20dfdf))
* **client:** 重新导出类型以改进开发体验 ([#9330](https://github.com/Arize-ai/phoenix/issues/9330)) ([3713355](https://github.com/Arize-ai/phoenix/commit/37133552a24cab98c7c9d8eb680f80be3c3df2bf))
* 处理新 OpenAI 工具类型 ([#9175](https://github.com/Arize-ai/phoenix/issues/9175)) ([d6c2559](https://github.com/Arize-ai/phoenix/commit/d6c25590d11668cb2529a2173d8e3ea1df67a14e))


<a id="documentation-10"></a>

### 文档

* 为所有 README 新增文档链接 ([#9322](https://github.com/Arize-ai/phoenix/issues/9322)) ([b0b671b](https://github.com/Arize-ai/phoenix/commit/b0b671bbabf05279ea7254e2b92972725a7a86b6))
* 为 API 参考中缺失的 phoenix.Client 方法添加明确文档 ([#8976](https://github.com/Arize-ai/phoenix/issues/8976)) ([6cd0b1f](https://github.com/Arize-ai/phoenix/commit/6cd0b1f84f8aacd1fa2a88c31c61638c0b391818))
* **client:** 修复 Python 客户端文档 ([#9317](https://github.com/Arize-ai/phoenix/issues/9317)) ([d94835a](https://github.com/Arize-ai/phoenix/commit/d94835aad129216fdb7d480a70aa2a501e615a8e))
* 统一文档字符串 ([#9324](https://github.com/Arize-ai/phoenix/issues/9324)) ([00dcea9](https://github.com/Arize-ai/phoenix/commit/00dcea97aac7a8165395bfaefe52f771feadca2d))
* 修复 Python 客户端文档 ([#9160](https://github.com/Arize-ai/phoenix/issues/9160)) ([bbe1300](https://github.com/Arize-ai/phoenix/commit/bbe130056dd531128a04db53a2e635df41284d7a))

## [1.15.3](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.15.2...arize-phoenix-client-v1.15.3) (2025-08-15)


<a id="bug-fixes-18"></a>

### 问题修复

* **experiments:** 数据集版本 ID 不应可选 ([#9074](https://github.com/Arize-ai/phoenix/issues/9074)) ([ec83174](https://github.com/Arize-ai/phoenix/commit/ec831742aa2cc22453922a7acf61775e4bbe5b29))
* **experiments:** 实验运行评估出错时 result 应允许为空 ([#9065](https://github.com/Arize-ai/phoenix/issues/9065)) ([fc5c303](https://github.com/Arize-ai/phoenix/commit/fc5c30310b804157f5472a2e2599ca34e0a03a46))

## [1.15.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.15.1...arize-phoenix-client-v1.15.2) (2025-08-14)


<a id="bug-fixes-19"></a>

### 问题修复

* **experiments:** 已运行实验应包含项目名称 ([#9076](https://github.com/Arize-ai/phoenix/issues/9076)) ([03dd8de](https://github.com/Arize-ai/phoenix/commit/03dd8deeee5fc26991df5b39f6f0adf29676557e))
* **experiments:** 实验任务 span 名称应简短 ([#9079](https://github.com/Arize-ai/phoenix/issues/9079)) ([589e96d](https://github.com/Arize-ai/phoenix/commit/589e96d040d571c28b03cf393ed20d405dd895bb))

## [1.15.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.15.0...arize-phoenix-client-v1.15.1) (2025-08-13)


<a id="bug-fixes-20"></a>

### 问题修复

* **experiments:** span 结束后记录结束时间 ([#9070](https://github.com/Arize-ai/phoenix/issues/9070)) ([7961d43](https://github.com/Arize-ai/phoenix/commit/7961d43d9b3002d769be11f06605790d01ca5820))


<a id="documentation-11"></a>

### 文档

* 在 run_experiment 文档字符串中补充客户端配置 ([#9032](https://github.com/Arize-ai/phoenix/issues/9032)) ([41384be](https://github.com/Arize-ai/phoenix/commit/41384be0e7e65d55285899b54033b269c4c3cc22))

## [1.15.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.14.2...arize-phoenix-client-v1.15.0) (2025-08-07)


<a id="features-37"></a>

### 新功能

* **playground:** 支持 gpt-5 ([#8985](https://github.com/Arize-ai/phoenix/issues/8985)) ([8711bde](https://github.com/Arize-ai/phoenix/commit/8711bdecfeee479c480a1acebf32ebc1b11461cb))
* 为 Python phoenix-client 新增删除 span 方法 ([#8944](https://github.com/Arize-ai/phoenix/issues/8944)) ([c7a0a1a](https://github.com/Arize-ai/phoenix/commit/c7a0a1a9fa63a659f86c5675ef913168df8962bf))
* 在顶层客户端模块重新导出实验工具 ([#8953](https://github.com/Arize-ai/phoenix/issues/8953)) ([1f9a9cb](https://github.com/Arize-ai/phoenix/commit/1f9a9cb8d9ac3bf63db05a8541e5826e099a153b))


<a id="bug-fixes-21"></a>

### 问题修复

* 更新 notebook，使用新客户端 ([#8891](https://github.com/Arize-ai/phoenix/issues/8891)) ([6ebbfb4](https://github.com/Arize-ai/phoenix/commit/6ebbfb4d6a9bfb40cf7a7d6a8db1464b4d931bd0))

## [1.14.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.14.1...arize-phoenix-client-v1.14.2) (2025-08-05)


<a id="bug-fixes-22"></a>

### 问题修复

* 从客户端文档字符串移除实验评估器引用 ([#8933](https://github.com/Arize-ai/phoenix/issues/8933)) ([3a45871](https://github.com/Arize-ai/phoenix/commit/3a45871775494496b1993d816a3a9fd26630e51e))

## [1.14.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.14.0...arize-phoenix-client-v1.14.1) (2025-07-30)


<a id="bug-fixes-23"></a>

### 问题修复

* 统一 schema `str` 类型与运行时 `datetime` 类型 ([#8862](https://github.com/Arize-ai/phoenix/issues/8862)) ([f7a2403](https://github.com/Arize-ai/phoenix/commit/f7a24031e147f86d07e8f4832e72fb33839a03fc))

## [1.14.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.13.2...arize-phoenix-client-v1.14.0) (2025-07-29)


<a id="features-38"></a>

### 新功能

* 为 Python 客户端数据集新增 list 方法 ([#8815](https://github.com/Arize-ai/phoenix/issues/8815)) ([559863c](https://github.com/Arize-ai/phoenix/commit/559863cfb2d3c5d1e496e39f4c9619bac27f0891))

## [1.13.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.13.1...arize-phoenix-client-v1.13.2) (2025-07-18)


<a id="bug-fixes-24"></a>

### 问题修复

* 允许执行器在后台线程运行 ([#8628](https://github.com/Arize-ai/phoenix/issues/8628)) ([6fb4f42](https://github.com/Arize-ai/phoenix/commit/6fb4f4265e71671c661dcf3e67a5085598d9a252))

## [1.13.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.13.0...arize-phoenix-client-v1.13.1) (2025-07-16)


<a id="bug-fixes-25"></a>

### 问题修复

* dry_run 模式下不访问实验评估 API ([#8606](https://github.com/Arize-ai/phoenix/issues/8606)) ([b8c77fb](https://github.com/Arize-ai/phoenix/commit/b8c77fb2d2d397e13f55aec86b978be2bd9dbfa6))

## [1.13.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.12.0...arize-phoenix-client-v1.13.0) (2025-07-16)


<a id="features-39"></a>

### 新功能

* 为 phoenix-client 新增 experiments 模块 ([#8375](https://github.com/Arize-ai/phoenix/issues/8375)) ([3df0326](https://github.com/Arize-ai/phoenix/commit/3df032627e8ce52a96e8d6dcd626f7641d0cb011))
* 为客户端 Datasets 新增序列化和反序列化方法 ([#8453](https://github.com/Arize-ai/phoenix/issues/8453)) ([1dcb304](https://github.com/Arize-ai/phoenix/commit/1dcb304f1415edfa12a07ff152a1ebe82a3de8c0))
* 增强实验功能 ([#8591](https://github.com/Arize-ai/phoenix/issues/8591)) ([2ba7953](https://github.com/Arize-ai/phoenix/commit/2ba79535c07069939ac33d660172c50a434bda54))

## [1.12.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.11.0...arize-phoenix-client-v1.12.0) (2025-07-03)


<a id="features-40"></a>

### 新功能

* 新增 Bedrock playground 客户端 ([#7918](https://github.com/Arize-ai/phoenix/issues/7918)) ([15d7e7a](https://github.com/Arize-ai/phoenix/commit/15d7e7aaa36913e3bb76777653fb29c8f6297340))

## [1.11.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.10.0...arize-phoenix-client-v1.11.0) (2025-06-19)


<a id="features-41"></a>

### 新功能

* 为客户端和 REST API 新增 `log_spans` ([#8005](https://github.com/Arize-ai/phoenix/issues/8005)) ([5a838ab](https://github.com/Arize-ai/phoenix/commit/5a838abf587db2ae707e39b1eca9d93c0c83323d))
* 为 Phoenix 客户端新增数据集方法 ([#7931](https://github.com/Arize-ai/phoenix/issues/7931)) ([4a5aa39](https://github.com/Arize-ai/phoenix/commit/4a5aa39b90adfb9896f336db7998bcde7c481bf8))
* **auth:** 支持登出 ([#7985](https://github.com/Arize-ai/phoenix/issues/7985)) ([63128c5](https://github.com/Arize-ai/phoenix/commit/63128c5328222147fe5c5103d8dd3576d5534bc2))
* 缺少 PHOENIX_COLLECTOR_ENDPOINT 时读取 OTEL_EXPORTER_OTLP_ENDPOINT ([#8095](https://github.com/Arize-ai/phoenix/issues/8095)) ([4cb7e4c](https://github.com/Arize-ai/phoenix/commit/4cb7e4c2cd3b43ee3334c717dc4499634ca12135))
* 拆分 Phoenix client 和 evals 文档 ([#7948](https://github.com/Arize-ai/phoenix/issues/7948)) ([e569b68](https://github.com/Arize-ai/phoenix/commit/e569b6802ab9e31cb230a30dbc08f60d7e28e993))


<a id="documentation-12"></a>

### 文档

* 改进 Read the Docs 的命名和结构 ([#8009](https://github.com/Arize-ai/phoenix/issues/8009)) ([76a4b92](https://github.com/Arize-ai/phoenix/commit/76a4b9282ff8476757ee1c0b3c85a7767208795b))

## [1.10.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.9.0...arize-phoenix-client-v1.10.0) (2025-06-04)


<a id="features-42"></a>

### 新功能

* 为 Phoenix 客户端新增 `get_spans` ([#7688](https://github.com/Arize-ai/phoenix/issues/7688)) ([8b48176](https://github.com/Arize-ai/phoenix/commit/8b481762c188e3191a8e0bb2ffd295a7ee3fdfb8))
* 支持 Ollama ([#7846](https://github.com/Arize-ai/phoenix/issues/7846)) ([4c52db4](https://github.com/Arize-ai/phoenix/commit/4c52db40da6b7772487cc6d288cf69d5944812a1))


<a id="bug-fixes-26"></a>

### 问题修复

* GET /span_annotations 不返回备注 ([#7830](https://github.com/Arize-ai/phoenix/issues/7830)) ([52c2c06](https://github.com/Arize-ai/phoenix/commit/52c2c06028815d0982172925e2d31705f49e0fe3))

## [1.9.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.8.0...arize-phoenix-client-v1.9.0) (2025-05-31)


<a id="features-43"></a>

### 新功能

* **admin:** 新增用户 REST API ([#7314](https://github.com/Arize-ai/phoenix/issues/7314)) ([c7bcc36](https://github.com/Arize-ai/phoenix/commit/c7bcc36b8469e76db3038f53859e24c7bb5da000))
* 在 playground 中新增 xAI ([#7808](https://github.com/Arize-ai/phoenix/issues/7808)) ([5dd53be](https://github.com/Arize-ai/phoenix/commit/5dd53be2ee697dd1b2c482df58d718d00ae892eb))

## [1.8.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.7.0...arize-phoenix-client-v1.8.0) (2025-05-29)


<a id="features-44"></a>

### 新功能

* 在 Playground 中新增 DeepSeek ([#7675](https://github.com/Arize-ai/phoenix/issues/7675)) ([b162720](https://github.com/Arize-ai/phoenix/commit/b162720325c7fe7c20cda75feb161b4646127cf8))

## [1.7.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.6.0...arize-phoenix-client-v1.7.0) (2025-05-21)


<a id="features-45"></a>

### 新功能

* 新增每小时 span 计数时间序列的 GraphQL 查询 ([#6997](https://github.com/Arize-ai/phoenix/issues/6997)) ([fe6a80a](https://github.com/Arize-ai/phoenix/commit/fe6a80aaa939ebe445af04c17e46b2c29080bc60))

## [1.6.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.5.0...arize-phoenix-client-v1.6.0) (2025-05-14)


<a id="features-46"></a>

### 新功能

* **api:** 公开实验路由 ([#7543](https://github.com/Arize-ai/phoenix/issues/7543)) ([7882615](https://github.com/Arize-ai/phoenix/commit/7882615fb22c487833b76c784edda668921e21db))


<a id="bug-fixes-27"></a>

### 问题修复

* 允许 context.span_id 作为列名 ([#7368](https://github.com/Arize-ai/phoenix/issues/7368)) ([ba1b9eb](https://github.com/Arize-ai/phoenix/commit/ba1b9eba9ce55b6644d46cd3f6436d29ccf2f304))

## [1.5.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.4.0...arize-phoenix-client-v1.5.0) (2025-05-09)


<a id="features-47"></a>

### 新功能

* 为客户端新增 `get_span_annotations_dataframe` ([#7366](https://github.com/Arize-ai/phoenix/issues/7366)) ([94c0c02](https://github.com/Arize-ai/phoenix/commit/94c0c029dee31e017da112cf1f5db36127cedf1b))
* 为客户端新增 span 标注 POST 方法 ([#7359](https://github.com/Arize-ai/phoenix/issues/7359)) ([218cc63](https://github.com/Arize-ai/phoenix/commit/218cc63cac84d48477d5359cc31aaf6ccca7f8bf))


<a id="bug-fixes-28"></a>

### 问题修复

* **annotations:** 确保标注配置响应类型嵌套于 data 键下 ([#7443](https://github.com/Arize-ai/phoenix/issues/7443)) ([145dba3](https://github.com/Arize-ai/phoenix/commit/145dba3978a2ae542a5b5d0e56098e3b0f019a6c))
* 修复转义字符情况下的格式问题 ([#7407](https://github.com/Arize-ai/phoenix/issues/7407)) ([3c0ab8b](https://github.com/Arize-ai/phoenix/commit/3c0ab8b33fdb3d97639fb5863643c3c32fe2d3af))
* 改进客户端语义 2 ([#7484](https://github.com/Arize-ai/phoenix/issues/7484)) ([11656a1](https://github.com/Arize-ai/phoenix/commit/11656a1aad9b31434ee7f97715fc3d8a9ebe6228))

## [1.4.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.3.0...arize-phoenix-client-v1.4.0) (2025-05-02)


<a id="features-48"></a>

### 新功能

* 为 Phoenix 客户端新增 `SpanQuery` DSL 和 `get_spans_dataframe` ([#7071](https://github.com/Arize-ai/phoenix/issues/7071)) ([ee56e9a](https://github.com/Arize-ai/phoenix/commit/ee56e9a9bf9e13c8793bd4a3b915ef083f679f2a))


<a id="documentation-13"></a>

### 文档

* **client:** 为客户端新增通用规则 ([#7290](https://github.com/Arize-ai/phoenix/issues/7290)) ([ba79347](https://github.com/Arize-ai/phoenix/commit/ba793476c46a6e9a3a203448ef06a3b46f9f8486))

## [1.3.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.2.1...arize-phoenix-client-v1.3.0) (2025-04-09)


<a id="features-49"></a>

### 新功能

* 允许在项目端点 REST 路径中使用项目名称作标识符 ([#7064](https://github.com/Arize-ai/phoenix/issues/7064)) ([8ccf2d7](https://github.com/Arize-ai/phoenix/commit/8ccf2d761100cefb2afc5a2d70690f9a5d15483e))
* 新增项目增删改查 REST API ([#7006](https://github.com/Arize-ai/phoenix/issues/7006)) ([b30c7ff](https://github.com/Arize-ai/phoenix/commit/b30c7ff65ee418c225d54a6fd00d4f7f29ad84e8))

## [1.2.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.2.0...arize-phoenix-client-v1.2.1) (2025-04-05)


<a id="documentation-14"></a>

### 文档

* 改进标题样式 ([#7044](https://github.com/Arize-ai/phoenix/issues/7044)) ([9151104](https://github.com/Arize-ai/phoenix/commit/9151104bd4aa69380849a441e3556a3adfa604ca))

## [1.2.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.1.0...arize-phoenix-client-v1.2.0) (2025-04-03)


<a id="features-50"></a>

### 新功能

* 新增列出或创建提示词版本标签的 REST 端点 ([#6984](https://github.com/Arize-ai/phoenix/issues/6984)) ([959622d](https://github.com/Arize-ai/phoenix/commit/959622d335274a0cb59dbf6b78e94fe6f3613bd3))


<a id="documentation-15"></a>

### 文档

* 无主题（GITBOOK-1087） ([6fa5fd7](https://github.com/Arize-ai/phoenix/commit/6fa5fd71cdf57a9a5a7efc3e2822ad57497f3b5a))
* 无主题（GITBOOK-1090） ([024c49f](https://github.com/Arize-ai/phoenix/commit/024c49fe57487ee816317f798ec648331a866ae4))
* 无主题（GITBOOK-1099） ([b4357e3](https://github.com/Arize-ai/phoenix/commit/b4357e324a9444704fbf85370c193ef2ee59495f))

## [1.1.0](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.0.3...arize-phoenix-client-v1.1.0) (2025-03-07)


<a id="features-51"></a>

### 新功能

* 为 Python 客户端新增 Anthropic thinking 配置参数 ([#6659](https://github.com/Arize-ai/phoenix/issues/6659)) ([d03d57e](https://github.com/Arize-ai/phoenix/commit/d03d57e0efaedcba4731caa18b74db35f9b104f1))

## [1.0.3](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.0.2...arize-phoenix-client-v1.0.3) (2025-02-27)


<a id="bug-fixes-29"></a>

### 问题修复

* 为 Phoenix 客户端新增 README ([#6604](https://github.com/Arize-ai/phoenix/issues/6604)) ([5ad7b0e](https://github.com/Arize-ai/phoenix/commit/5ad7b0eb5e87d0da3566b6f4a8f048aa9fabb1d1))

## [1.0.2](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.0.1...arize-phoenix-client-v1.0.2) (2025-02-24)


<a id="bug-fixes-30"></a>

### 问题修复

* 在 OpenAI 参数校验中新增 max_completion_tokens ([#6550](https://github.com/Arize-ai/phoenix/issues/6550)) ([c99ee6f](https://github.com/Arize-ai/phoenix/commit/c99ee6fe69bc0ebde8d0fe018044f796142fcdc9))
* **client:** 更新 Python 客户端 SDK 辅助函数以适配 anthropic 0.47 ([#6551](https://github.com/Arize-ai/phoenix/issues/6551)) ([4abbd0d](https://github.com/Arize-ai/phoenix/commit/4abbd0dbe941009245d06a95329426e34df90ed9))

## [1.0.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v1.0.0...arize-phoenix-client-v1.0.1) (2025-02-19)


<a id="bug-fixes-31"></a>

### 问题修复

* 更新 Phoenix 客户端版本 ([#6465](https://github.com/Arize-ai/phoenix/issues/6465)) ([3fede08](https://github.com/Arize-ai/phoenix/commit/3fede08024ff5e7e013717d07a1d94f2cb965a60))

## [0.2.0-alpha.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v0.1.0-alpha.1...arize-phoenix-client-v0.2.0-alpha.1) (2025-02-19)


<a id="features-52"></a>

### 新功能

* 客户端获取最新提示词版本 ([#6167](https://github.com/Arize-ai/phoenix/issues/6167)) ([e5226ff](https://github.com/Arize-ai/phoenix/commit/e5226ff5993d271359807b5544fea6cfaef83b6d))
* **prompts:** 为 OpenAI 和 Anthropic 提示词新增客户端辅助函数 ([#6109](https://github.com/Arize-ai/phoenix/issues/6109)) ([4083257](https://github.com/Arize-ai/phoenix/commit/4083257aabcc371b465752bb6153ec1f4fbcba79))
* **prompts:** 为 Python 客户端 SDK 辅助函数的 OpenAPI schema 新增工具选择 ([#6291](https://github.com/Arize-ai/phoenix/issues/6291)) ([20c8bef](https://github.com/Arize-ai/phoenix/commit/20c8bef27adb7b0d6efafcf22c3189d3c29af973))
* **prompts:** 为提示词端点新增 POST 方法 ([#6347](https://github.com/Arize-ai/phoenix/issues/6347)) ([77eab0c](https://github.com/Arize-ai/phoenix/commit/77eab0cc3251a0f50c077149d985a87cadb2d0f8))
* 为客户端新增 OpenAI SDK 响应格式支持 ([#6282](https://github.com/Arize-ai/phoenix/issues/6282)) ([a9d9a49](https://github.com/Arize-ai/phoenix/commit/a9d9a49f9f91e0c99a08ae92e716cbc0887346cb))


<a id="bug-fixes-32"></a>

### 问题修复

* **client:** 从 SDK 辅助函数中排除空工具列表 ([#6203](https://github.com/Arize-ai/phoenix/issues/6203)) ([e3e5ea3](https://github.com/Arize-ai/phoenix/commit/e3e5ea324fcdcb5d12279f5d29e837d895898f5f))
* **client:** 处理 Azure OpenAI 调用参数 ([#6450](https://github.com/Arize-ai/phoenix/issues/6450)) ([b11a604](https://github.com/Arize-ai/phoenix/commit/b11a60432c084314d65549bbdea56c2e3441d4e0))
* **prompts:** 规范化工具 ([#6220](https://github.com/Arize-ai/phoenix/issues/6220)) ([42a31ad](https://github.com/Arize-ai/phoenix/commit/42a31adca6c25068e94decb437ff79b187f85903))
* **prompts:** 新增提示词调用参数 ([#6309](https://github.com/Arize-ai/phoenix/issues/6309)) ([c0e2998](https://github.com/Arize-ai/phoenix/commit/c0e2998e8b56ffb5276d671d8d9654c2494eaaf7))
* **prompts:** 重命名 Google 提供方 ([#6452](https://github.com/Arize-ai/phoenix/issues/6452)) ([2ecac95](https://github.com/Arize-ai/phoenix/commit/2ecac9527ec3d718bdb75d21596ef1ee3b0b9d6b))
* **prompts:** 新增 SQLAlchemy 类型 ([#6177](https://github.com/Arize-ai/phoenix/issues/6177)) ([d6614b6](https://github.com/Arize-ai/phoenix/commit/d6614b6494f4e7a29212559bb8275edef2b80601))

## [0.1.0-alpha.1](https://github.com/Arize-ai/phoenix/compare/arize-phoenix-client-v0.1.0-alpha.0...arize-phoenix-client-v0.1.0-alpha.1) (2025-01-07)


<a id="features-53"></a>

### 新功能

* 为 `arize-phoenix-client` 创建初始 Python 包骨架 ([#5934](https://github.com/Arize-ai/phoenix/issues/5934)) ([00fd25d](https://github.com/Arize-ai/phoenix/commit/00fd25d98e949a428b0f702882866beaaba43e45))
