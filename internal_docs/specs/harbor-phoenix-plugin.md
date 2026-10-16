<a id="phoenix-plugin-for-harbor-design-specification"></a>
# Phoenix Harbor 插件：设计规范

ATIF 已实现。OTLP 处于规划阶段，插件尚不接受它。

<a id="contents"></a>
## 目录

- [概述](#1-summary)
- [目标与边界](#2-goals-and-boundaries)
- [数据模型](#3-data-model)
- [插件设计](#4-plugin-design)
- [追踪模式](#5-trace-modes)
- [评估分数](#6-evaluation-scores)
- [身份与故障处理](#7-identity-and-failure-handling)
- [配置](#8-configuration)
- [实现范围](#9-implementation-scope)
- [后续工作](#10-future-work)
- [兼容性假设](#11-compatibility-assumptions)

---

<a id="1-summary"></a>
## 1. 概述

Phoenix Harbor 插件将 Harbor 评估作业记录到 Phoenix。Harbor 运行 Agent 和验证器。Phoenix 存储任务、实验运行、分数和追踪，供团队跨 Agent、模型、尝试和时间比较结果。

插件会：

- 根据 Harbor 任务推导 Phoenix 数据集
- 为作业中的每个 Agent 和模型创建一个 Phoenix 实验
- 将每个 Harbor 试验记录为一次实验运行
- 将 Harbor 的聚合奖励和基础设施状态存为稠密评估分数
- 将其他任务级和步骤级奖励存为稀疏诊断分数
- 在 ATIF 追踪成功时，将每次运行关联到一条 ATIF 追踪

ATIF 是默认模式，需要已保存的轨迹，无需实时 Agent 插桩。规划中的 OTLP 设计独立于当前实现，见 §5。

插件使用现有的 ATIF 转换和父节点重设辅助函数，无需修改 Phoenix 服务端。

<a id="2-goals-and-boundaries"></a>
## 2. 目标与边界

<a id="goals"></a>
### 目标

- 通过 `harbor run --plugin arize-phoenix` 一条命令完成设置。
- 支持任何满足所选追踪模式要求的 Harbor 数据集和 Agent。
- 保留 Harbor 的任务、逻辑试验、Agent、模型和奖励身份。
- 展示可跨 Agent 和模型比较的结果。
- 长时间运行的作业中断时保留已完成结果。
- 无法设置必需的 Phoenix 记录时，在消耗试验计算资源之前停止。
- 使重复摄取保持幂等。

<a id="boundaries"></a>
### 边界

- Harbor 运行 Agent 和验证器。Phoenix 不重新运行这些实验，也不选择 Harbor 任务。
- Harbor 验证器仍是奖励的权威来源。插件不计算第二个聚合奖励。
- 数据集样本 `output` 保持为空对象。Harbor 的解决方案是生成最终状态的可执行方式，而非参考回答。
- 插件接受一个 Harbor 数据集或仅包含直接任务的作业，拒绝混合这两种来源的作业。单个直接任务获得带命名空间的合成数据集名称；多个直接任务必须显式配置 `dataset` 插件设置。
- 插件不为 Harbor 的环境设置、Agent 设置或验证器阶段包装 span。试验和步骤 span 根据保存的最终结果构建。
- 不提供事后摄取命令。

<a id="3-data-model"></a>
## 3. 数据模型

| Harbor 概念 | Phoenix 概念 | 映射 |
| ----------------------------- | --------------------------- | ----------------------------------------------------------------- |
| 数据集 | 数据集 | 根据 Harbor 推导名称；可覆盖 |
| 任务 | 数据集样本 | 输入包含任务 ID、名称和指令；其他字段置于元数据 |
| 任务摘要 | 数据集样本元数据 | 完整 Harbor 任务摘要 |
| 解析后的任务快照 | 数据集版本 | 完整同步的任务集 |
| 作业 × Agent × 模型 | 实验 | 每个 Agent 和模型对应一个实验 |
| 逻辑试验 | 实验运行 | 每次计划中的任务尝试对应一次运行 |
| 计划中的尝试 | 重复 | 确定性的重复编号 |
| 试验或步骤异常 | 运行错误 | 与验证器奖励分开保存 |
| 试验 `reward` | 稠密评估 | 存储在行为评估已完成的运行上 |
| 基础设施状态 | 稠密 `infra_ok` 评估 | 存储在每次已记录的最终运行上 |
| 步骤奖励 | 稀疏评估 | 命名为 `<step_name>.<reward_key>` |
| ATIF 轨迹 | 追踪 | 追踪成功时关联到实验运行 |

一个 Harbor 任务集合使用一个 Phoenix 数据集。普通作业直接映射其唯一配置的 Harbor 数据集。仅包含直接任务的作业将解析后的任务集映射到合成 Phoenix 数据集。不得混合已配置的数据集和直接任务，也不得接受多个已配置的数据集。

从解析后的 `DatasetConfig` 推导数据集名称：

| Harbor 输入 | 分类 | 推导的数据集名称 |
| --- | --- | --- |
| 本地路径 (`--path`) | `is_local()` | 解析后的目录基本名称 |
| 注册表裸名称 (`--dataset <name>`) | `is_registry()` | 所选裸名称 |
| 已发布的包 (`--dataset <org>/<name>`) | `is_package()` | 所选 `<org>/<name>` |
| 仓库来源（`--repo` 配合 `--dataset`） | `is_repo()` | 解析后的注册表元数据名称 |
| 单个直接任务（`--path`、包或 Git 任务） | 直接任务 | `harbor-task/<declared task name>` |

本地数据集只暴露其目录名称。推导名称后，验证所有解析后的任务具有相同来源。

可选的 `dataset` 设置覆盖推导出的名称，但不改变单一集合规则。对于多个直接任务，此设置是必需的，并声明完整解析后的任务集是一个合成数据集快照。采用完整更新语义，因此后续作业若使用相同名称但任务集不同，会创建新版本，其样本与后续作业完全一致。

拒绝重复的任务 ID。Phoenix 使用任务 ID 标识样本和运行，重复 ID 会使独立任务合并。

每个任务成为如下结构的 Phoenix 数据集样本：

```json
{
  "id": "<stable Harbor task ID>",
  "input": {
    "task_id": "<Harbor task ID>",
    "task_name": "<Harbor task name>",
    "instruction": "<task instruction>"
  },
  "output": {},
  "metadata": {
    "task_digest": "<full Harbor task digest>",
    "task_source": "<resolved Harbor task source>",
    "task_type": "<Harbor task type>",
    "task_version": "<Harbor task version or null>",
    "task_config": {}
  }
}
```

对于多步骤任务，`input` 还包含按顺序排列的步骤名称和指令：

```json
{
  "steps": [
    {
      "name": "<step name>",
      "instruction": "<step instruction>"
    }
  ]
}
```

`input` 仅放入识别和执行任务所需的字段。任务摘要、来源、类型、版本和已脱敏的任务配置放入 `metadata`。保持 `output` 为空，因为 Harbor 检查环境状态，而非参考回答。

每次作业开始时，同步完整任务集。以 Harbor 任务 ID 作为稳定的外部样本 `id`。Phoenix 返回单独的 `node_id`；保存它以记录实验运行。

任务摘要涵盖解决方案、环境、测试和步骤。完整任务集未变时，Phoenix 复用当前数据集版本。添加、删除或修改任务都会创建新版本。

`on_job_start` 时尚不存在作业锁。兼容性适配器根据解析后的配置、试验配置和任务下载在内存中构建它，然后读取任务摘要。

<a id="4-plugin-design"></a>
## 4. 插件设计

插件位于 `arize-phoenix-client` 中，模块为 `phoenix.client.harbor`，并在 Harbor 的 `harbor.plugins` 入口点组中注册 `arize-phoenix`。仅在选中插件时导入 Harbor。

该包有三个主要组件：

1. Harbor 兼容性适配器将解析后的任务和试验计划读入内部模型。它是唯一访问 Harbor 私有作业计划字段的组件，并在摄取开始前验证这些字段。
2. 记录器将该模型映射到 Phoenix 数据集、实验、运行、评估和追踪链接。
3. 作业插件将 Harbor 生命周期钩子连接到记录器，并在必需的 Phoenix 记录失败时停止作业。

该包支持 Harbor `>=0.21.0` 的普通作业，在运行时检查必需能力。不支持重新评分和来源作业计划。

Phoenix 版本要求取决于功能：

| 要求 | 最低版本 | 状态 |
| --- | --- | --- |
| 实验/运行/评估记录 | `arize-phoenix-client>=2.10.0` | 已发布 |
| 稳定的外部数据集样本 ID | Phoenix 服务端 `>=15.0` | 已发布 |
| ATIF 追踪查询和重放验证 (§5) | Phoenix 服务端 `>=13.9` | 已发布；仅针对 ATIF 模式的最低版本 |

只有 ATIF 模式使用的追踪 ID 过滤器要求 Phoenix 服务端 `>=13.9`。

<a id="job-start"></a>
### 作业开始

在 `on_job_start` 时，插件会：

1. 解析完整任务和试验计划；
2. 同步完整数据集样本快照；
3. 为每个有效 Agent 和模型配置恢复或创建一个实验。恢复时匹配保存的 Harbor 作业 ID 和 Agent 身份摘要。其他作业可能在重放之间为同一数据集创建新版本，因此恢复的实验仍固定到原始版本。新实验使用当前数据集版本；
4. 读取各实验由服务端分配的项目名称；
5. 为每个试验推导稳定的重复编号。

插件无法在作业开始时列出物理尝试。Harbor 之后才创建重试，试验 UUID 在构建试验时才存在。重试处理确定尝试为最终尝试后，插件根据保存的最终结果创建 ATIF 身份。规划中的 OTLP 尝试身份必须在 Harbor 构建每次物理尝试后创建。

必须先创建样本再创建实验，因为 Phoenix 实验创建时会固定到一个数据集版本。

<a id="trial-end"></a>
### 试验结束

Harbor 可能在启动重试前为失败尝试发出 END 事件。事件不包含尝试编号，也不说明是否为最终尝试。兼容性适配器重建此判断：统计每个逻辑试验的 START 事件，并按以下顺序应用 Harbor 的 `RetryConfig` 规则：exclude、include，最后是 `max_retries`。

`RetryConfig` 是公开的，但此判断逻辑属于 Harbor 的私有行为。契约测试覆盖已安装的 Harbor 版本，E2E 目标默认使用最低受支持版本。不要为将被重试的尝试写入 Phoenix 或 ATIF 数据。最终尝试保留该逻辑试验预先计算的重复编号。

此逻辑有三个限制：

- 只有顶层 `TrialResult.exception_info` 会触发重试。仅在 `StepResult` 上发现的失败为最终结果，必须摄取。
- `CancelledError` 永远不可重试。
- Harbor 可能在保存中间结果后、启动重试前崩溃。恢复时，Harbor 可能将该结果视为完成。插件无法检测或修复此情况。

每个逻辑试验最终结束时，插件会：

1. 在 `trace_mode="atif"` 时构建并上传 ATIF 追踪；
2. 有追踪 ID 时解析它；
3. 写入实验运行及其输出、计时、追踪链接和错误状态；
4. 写入 Harbor 发出的稠密和稀疏评估分数。

插件在每个试验结束时流式记录结果，以提供实时进度，并在作业提前停止时保留已完成工作。

<a id="job-end"></a>
### 作业结束

`on_job_end` 记录完成消息。必需数据在试验结束时写入，因为 Harbor 会抑制作业结束钩子的错误。

<a id="5-trace-modes"></a>
## 5. 追踪模式

插件接受 `atif` 和 `null`；`null` 禁用追踪。它不会自动检测追踪，也不会将 ATIF 与实时 span 合并。`otlp` 已规划但尚未实现。

| 行为 | `atif`（默认） | `otlp`（推迟） |
|---|---|---|
| 需要 Agent 插桩 | 否；Agent 必须生成 ATIF | 是；标准 OpenTelemetry 插桩即可 |
| 试验期间实时可用 | 否；试验结束时上传 | 是 |
| 沙箱端点和凭证 | 不需要 | 需要 |
| 沙箱的网络访问 | 不需要 | 需要 |
| 目标位置 | 实验的 Phoenix 项目 | 实验的 Phoenix 项目 |
| 运行关联 | 根据 Harbor 作业和最终试验 ID 确定性生成 | 回报或关联查询；见 §5.2 |
| 插件拥有的试验级根节点 | 有 | 需等待 Harbor 运行时钩子 |

<a id="atif-mode"></a>
### ATIF 模式

转换器支持 ATIF v1.0 至 v1.7。Harbor 加载器也会按已安装的 Harbor 轨迹模型验证文件。不支持 ATIF v1.8 音频字段。

ATIF 模式使用包内现有的纯转换和公共父节点辅助函数。插件需要在上传前取得 span，以检查确定性 ID、修复部分上传，并仅在 Phoenix 接受全部缺失 span 后关联运行。

包内纯转换辅助函数会：

- 验证并转换一个或多个轨迹；
- 返回 span 而不上传；
- 保留 ATIF v1.7 子 Agent 扁平化和有效外部引用；
- 上传前拒绝重复 span ID、无法解析的父节点、跨追踪父子链接和环；
- 将每个独立轨迹根节点重新挂到一个由 Harbor 拥有的试验根节点下。

转换层不使用客户端。Harbor 专用的发现、规范化、确定性身份和上传修复行为保留为插件私有实现。

子 Agent 引用同时提供嵌入 ID 和文件路径时，优先采用嵌入匹配，以便只转换一次子 Agent。文件和嵌入文档都会跟随续接，且仍位于原始文档调用者下方。角色目录和引用文件必须解析到试验目录内部，包括存在符号链接时。每个引用文件还必须位于其角色目录内。拒绝 URL 和绝对引用。

追踪反映 Harbor 结构：试验 → 步骤 → Agent 轨迹。插件创建一个确定性的 CHAIN 根节点 `harbor.trial <task id>`，并将所有 span 发送到实验的 Phoenix 项目。多步骤试验按 `step_results` 顺序，为每个已尝试步骤创建一个 `harbor.step <index> <step name>` CHAIN span，该步骤轨迹置于其下；单步骤试验直接将轨迹挂到根节点下。步骤 span 的输入是步骤指令，输出是步骤的验证器奖励，自身异常使其状态为 `ERROR`。根节点在与实验运行错误和 `infra_ok` 相同的失败条件下标为 `ERROR`：任何顶层或步骤异常，即便 Harbor 同时记录了验证器奖励。原生恢复只加载最后的累积快照，因此较早步骤保留 `harbor.step` span，但其下没有轨迹。

轨迹中，每个新的 Agent 步骤代表 Agent 循环的一次迭代，并成为 CHAIN span。LLM、TOOL 和被引用子 Agent 的工作挂在该迭代下；匹配的 `source_call_id` 将子 Agent 的父节点细化为其 TOOL 调用。复制的上下文属于提示词历史，不创建重复执行 span。

Harbor 拥有的 span 保留 `harbor.` 前缀。轨迹 span 使用以下名称：

| Span | 类型 | 名称 |
| --- | --- | --- |
| 试验 | CHAIN | `harbor.trial <task id>` |
| 步骤（仅多步骤） | CHAIN | `harbor.step <index> <step name>` |
| 轨迹根节点 | AGENT | `<agent name>`；续接添加 ` (continuation N)` |
| 轮次（仅多轮） | AGENT | `turn N` |
| Agent 循环迭代 | CHAIN | `iteration N` |
| 上下文管理 | CHAIN | `compaction N` |
| 操作性系统步骤（例如交接） | CHAIN | `system event N` |
| LLM 调用 | LLM | `<model name>`；轨迹未指定模型时为 `LLM` |
| 工具调用 | TOOL | `<tool name>` |

序号统计相同标签的新操作步骤，不受交错影响；生成方的 `step_id` 作为 `atif.step_id` 留在元数据中。用户消息从不占用序号。连续的用户或系统上下文消息不开启新轮次；只有 Agent 活动之后的用户消息才开启一轮。

轨迹中的每个 span 都携带 `metadata.agent_name`，步骤下的每个 span 都携带 `metadata.harbor.step_index` 和 `metadata.harbor.step_name`。

轨迹提供 `input.value` 和 `output.value` 时，每个 AGENT 和 CHAIN span 都携带它们。迭代输入为之前的用户或系统消息，或上次迭代的观察结果。输出为步骤消息加上未被任何工具调用认领的观察结果；若步骤仅发出工具调用，则输出为工具结果。只有显式的 `source_call_id` 才将结果与工具配对；该调用的多个结果按顺序保留。只有 LLM span 携带 `llm.*` 属性。轨迹的 `final_metrics` 保留在根 span 的 `metadata.final_metrics` 中，避免 Phoenix 累积 token 计数重复。

LLM 输入是重建的 ATIF 上下文，并非精确的提供方请求。每个 LLM span 携带 `metadata.atif.input_source = "reconstructed"`。ATIF 来源 `user`、`system`、`agent` 分别映射到消息角色 `user`、`system`、`assistant`。转换器不解析提供方原生消息，也不解释工具参数键。没有匹配调用 ID 的反馈作为带 `after_step_id` 的 `observation` 条目保留在 `input.value` 中，不推断角色或工具关联。多模态工具结果在重建输入和序列化工具输出中保留内容部分。不读取或上传媒体字节。`llm_call_count: 0` 的 Agent 步骤即便未调用工具仍获得迭代 CHAIN，且不创建合成 LLM span。

ATIF 时间戳表示时点事件。一次迭代从前一个新事件持续到自身事件。仅当请求测量数量与新 LLM 步骤数量完全一致时，Harbor 才使用 `agent_result.metadata.api_request_times_msec` 丰富 Terminus 轨迹。单个文档使用其声明的步骤顺序。续接图和子 Agent 图要求每个新 LLM 步骤都有时间戳，以按时间合并请求；否则跳过丰富处理，避免测量错位。转换器不解释生成方专用的延迟指标。经过测量的 LLM span 在来源区间内使用 Harbor 请求时长。未测量的 LLM 和 TOOL 调用是零时长事件；转换器不推断工具串行、并行或耗时。同一时刻的事件保留精确 ATIF 时间戳。转换器先列出未测量的 LLM，再按声明的数组顺序列出其工具调用，但该顺序不表示工具串行执行。上传前，Harbor 适配器反转缺失 span 批次。Phoenix 按 FIFO 插入批次，并按行 ID 降序返回追踪 span；其稳定的开始时间排序因此能在时间完全相同时恢复转换器的因果顺序和声明顺序。修复中断的前缀上传时使用同样的反转及过滤规则。缺失或非单调时钟会折叠，而不生成合成时长。

对于每个内存中的轨迹，插件会：

- 根据保存的最终试验身份、角色、步骤、文件和嵌入索引设置 `trajectory_id`；
- 将 `session_id` 设置为每个试验一个值 (`harbor:<trace_id>`)，使试验显示为包含一条追踪的单个 Phoenix 会话。生成方原始的 `trajectory_id` 和 `session_id` 保留在轨迹根 span 的 Agent 元数据中。

它不会修改源文件。

始终设置这两个值。Agent 可能省略 `trajectory_id`、跨步骤复用 `session_id`，或使用常量会话 ID。生成方的这些选择都不应导致独立试验合并。

即使设置了 `trajectory_id`，插件仍必须为 `session_id` 添加命名空间。Phoenix 解析 `session_id` 对应的会话时不按项目过滤，否则常量值可能把无关试验分组到同一会话。

两个 ID 必须全局唯一，且跨重放稳定。追踪 ID 来自 Harbor 作业 ID 和保存的最终试验 UUID，`session_id` 来自追踪 ID。每个 `trajectory_id` 还包含角色、步骤名称、源路径和嵌入位置。

确定性 ID 不会使 span 上传自动具备幂等性。Phoenix 有两个重要摄取行为：

- 任一 span ID 已存在时，Phoenix 拒绝整个请求。不要再次发送已存在的 span。
- Phoenix 会静默丢弃单个请求中重复的 span ID。验证请求中的所有 ID 唯一。

上传前查询预期 span ID，仅发送缺失 span。Phoenix 报告所有缺失 span 已入队后立即关联运行。span 在 Phoenix 批量插入间隔内变为可查询。成功的实验运行不可变。成功运行若记录时没有追踪，后续重放也仍然没有追踪。在 `atif` 模式下，此查询要求 Phoenix 服务端 `>=13.9`。

<a id="planned-otlp-mode"></a>
### 规划中的 OTLP 模式

本节描述推迟到后续实现的行为，仍作为规划中的 OTLP 契约。

OTLP 有三个独立功能：

1. 项目路由；
2. 适配器辅助的追踪到运行关联；
3. 插件拥有的逐试验追踪身份，受 Harbor 能力阻塞。

Harbor 不创建 OpenTelemetry span，由 Agent 创建。每个 Agent 有一个共享环境 `AgentConfig.env`，Harbor 构建 Agent 时复制它。

<a id="51-project-routing"></a>
#### 5.1 项目路由

用户通过 Harbor 的逐 Agent 环境（`--agent-env`，或作业配置文件中各 Agent 的 `env:` 块）提供导出器端点、凭证和项目。Phoenix 根据 `openinference.project.name` 资源属性或 HTTP 的 `x-project-name` 头路由。

在 `on_job_start` 时，插件依据配置的项目和端点检查各 Agent 环境。值缺失或不同时停止，并给出修复所需的精确参数。

逐 Agent 路由需要作业配置文件。CLI 会把同一个 `--agent-env` 值应用到所有 Agent。

**不要**在 `on_job_start` 修改 `job.config.agents[*].env`。Harbor 会将改动保存到试验配置，包括所有凭证。之后的 `resume` 会因保存配置与计划不同而失败。

沙箱使用网络允许列表时，必须通过 Harbor 的 Agent 主机允许列表参数加入 Phoenix 主机。

<a id="52-tracerun-linkage"></a>
#### 5.2 追踪→运行关联

同时使用两种机制：

- **回报。**适配器将自身追踪 ID 添加到 Harbor Agent 上下文元数据。应与现有元数据合并，而非替换。注意：非空元数据会禁用 Harbor 自动生成的 token 和成本字段。
- **关联查询。**适配器将 `harbor.trial.id` 添加为 **span** 属性。插件在实验项目中查询该最终试验 UUID。

两种机制都要求 Phoenix 拥有的适配器。适配器可从上下文读取试验 UUID，为所有步骤创建一条确定性追踪，并回报追踪 ID。

关联键必须是 span 属性。Phoenix 会丢弃除项目名称外的全部 OTLP **资源**属性。此外，Harbor 在 CLI 设置后才创建作业 UUID，因此只有用户提供的作业标签可以是静态值。

根 span 由适配器创建，因此插件只有在试验运行后才知道追踪 ID，无法在作业开始时验证关联。

<a id="53-plugin-owned-per-trial-context"></a>
#### 5.3 插件拥有的逐试验上下文

通用 OTLP 需要一个能在 Agent 构建前注入试验根节点的 Harbor 钩子。实现此模式前，检查受支持的 Harbor 版本是否提供满足以下约束的钩子：

- Harbor 在构建试验时创建试验 UUID，因此作业开始时不可用；
- 并发试验共享同一个 `AgentConfig`，逐试验修改会产生竞争；
- 试验开始钩子在 Agent 复制环境后运行。

运行时覆盖钩子必须在 Agent 构建前运行，且不改变保存的配置、作业锁或恢复检查。在最低 Harbor 版本包含此能力前，OTLP 支持仅限 §5.1 和 §5.2。启动检查时说明此限制。

<a id="54-consequences-that-hold-in-every-otlp-variant"></a>
#### 5.4 所有 OTLP 变体共同的影响

插件在子 span 之后发送预先构建的根节点。Phoenix 支持任意到达顺序，但**第一个** span 决定追踪所属项目。Agent 发送任何 span 前，项目路由必须正确。

根节点状态描述基础设施是否成功，而非行为奖励。子节点错误仍计入根节点错误数。

每次重试都有新试验 UUID，并发出独立追踪。仅将最终尝试关联到实验运行。较早追踪仍留在同一项目中且不关联。项目级指标（例如 token 成本）包含所有尝试。

Harbor 在 span 发出后才决定是否重试，Phoenix 之后无法移动 span。较早追踪仍可用于调试。

添加 `harbor.trial.id` 作为 **span** 属性，使用户能找到未关联追踪。适配器无法添加尝试编号，因为只有 Harbor 试验队列知道它。

多追踪运行不在范围内。Phoenix 每次实验运行显示一条追踪，因此在运行输出中加入额外追踪 ID 没有用处。

<a id="6-evaluation-scores"></a>
## 6. 评估分数

Harbor 可为每个任务使用不同验证器，因此并非每个分数都对整个数据集有意义。插件将分数分为稠密汇总指标和稀疏诊断指标。

<a id="behaviorally-completed"></a>
### 行为评估已完成

当 Harbor 生成验证器结果时，运行即为**行为评估已完成**。插件按精确的 Harbor 键记录每个奖励。只有验证器结果包含字面 `reward` 键，才生成名为 `reward` 的 Phoenix 评估。

| Harbor 最终状态 | 顶层异常 | 步骤异常 | 行为评估已完成 | 运行错误 | `reward` | `infra_ok` |
| --- | --- | --- | --- | --- | --- | --- |
| 成功 | 无 | 无 | 是 | 否 | Harbor 聚合值 | 1 |
| 行为得分为零 | 无 | 无 | 是 | 否 | `0` | 1 |
| 单步骤 Agent 或验证器失败 | 存在 | 不适用 | 否 | 是 | 不写入 | 0 |
| 已评分的多步骤异常 | 通常无 | 存在 | 是，若存在最终验证器结果 | 是 | Harbor 聚合值 | 0 |
| 没有验证器结果的多步骤异常 | 无或存在 | 存在 | 否 | 是 | 不写入 | 0 |
| 取消 | `CancelledError` | 部分 | 否 | 是 | 不写入 | 0 |

异常状态和行为评估完成情况彼此独立。运行可以保留验证器奖励，同时携带运行错误、`infra_ok = 0` 和 `ERROR` 追踪根节点。

只有 Harbor 发出 `reward` 键时才存在该分数。插件不会将唯一的其他名称值提升为它，也不从其他键推导聚合值。使用者必须在计算跨任务汇总前检查 `reward` 覆盖率。

| 分数 | 覆盖范围 | 用途 |
|---|---|---|
| `reward` | 仅 Harbor 发出时 | Harbor 约定的行为分数；适合跨任务汇总 |
| `infra_ok` | 每次已尝试的运行 | 基础设施成功率 |
| `<reward_key>` | 仅 Harbor 发出时 | 试验级验证器奖励或诊断 |
| `<step_name>.<reward_key>` | 仅 Harbor 发出时 | 任务内步骤级诊断 |

规则：

- 从 `step_results` 和最终验证器结果读取分数。
- 检查顶层结果及每个步骤结果的异常。任一异常都设置运行错误和 `infra_ok = 0`。无异常的零奖励保持 `infra_ok = 1`。
- 将每个最终验证器奖励存为 `<reward_key>`，每个步骤奖励存为 `<step_name>.<reward_key>`。即使验证器只发出一个值，也不要从其他键推导 `reward`。
- 为多步骤任务的每个试验级奖励评估添加 `multi_step_reward_strategy`。将 Harbor 省略的默认值解析为 `mean`；保留显式的 `final`。不向步骤级分数、`infra_ok` 或单步骤奖励添加此元数据。
- 写入前拒绝空白或重复步骤名称，并在提取时检测其余生成名称冲突。
- 按原始数值量纲存储步骤奖励。
- 将基础设施失败与行为失败分开。
- 不添加内置 `all_steps_passed` 或 `tool_calls` 分数。任务可在有用时发出专用分数。
- 将 Harbor 最终试验 ID、token 使用量和成本存入紧凑且 JSON 安全的运行 `output` 封装。Phoenix 公共运行 API 没有运行元数据参数。在输出 schema 能表示多步骤计时且不破坏旧插件版本写入的不可变运行复用之前，推迟阶段计时。

Phoenix 可从追踪计算 token 成本和延迟。使用者可根据保存的奖励计算通过率、pass^k、置信区间和发布门禁。

<a id="7-identity-and-failure-handling"></a>
## 7. 身份与故障处理

<a id="stable-identity"></a>
### 稳定身份

| 对象 | 稳定键 |
|---|---|
| 数据集 | 解析后的 Harbor 数据集身份或显式覆盖 |
| 样本 | 数据集内任务 ID |
| 样本版本 | 完整 Harbor 任务摘要 |
| 实验 | Harbor 作业 ID 和有效 Agent/模型配置；固定到创建时的数据集版本 |
| 运行 | 实验、样本和重复编号（从 1 开始） |
| 评估 | 运行和评估名称 |
| ATIF 追踪 | Harbor 作业 ID 和保存的最终试验 UUID |
| OTLP 尝试追踪，规划中 | 根据 Harbor 作业和物理试验尝试身份确定性生成 |

一个 Harbor 作业是跨全部已配置 Agent 和模型的一次执行。具有 N 个 Agent/模型配置的作业在一个数据集上创建 N 个实验。

作业 ID 区分各次执行。同一基准的两次执行必须创建不同实验，否则运行会使用相同 `(experiment, example, repetition)` 键。成功的 Phoenix 运行不可更改，因此第二次执行的每次运行都会冲突。Phoenix 通过同一数据集上的独立实验表示随时间的比较。

Harbor 不暴露逻辑重复编号。作业开始时，适配器按顺序遍历试验计划，按 `(experiment identity, task ID)` 统计重复次数。绝不要使用完成顺序。物理重试保持相同逻辑重复编号，尽管每次重试获得新试验 UUID。

重复编号从 1 开始，因为 Phoenix 拒绝零。将实验的 `repetitions` 值设为 Harbor 配置的尝试次数。Phoenix 使用该值生成运行缺失和完整性报告。

此键仅在任务 ID 和实验身份唯一时有效。写入 Phoenix 前拒绝重复。

Agent 和模型身份包含可读名称及影响行为的配置稳定摘要。摘要排除调度和日志字段，包含环境变量名称但不含其值。摘要不同的配置必须创建不同实验，即使显示名称相同。

追踪 ID 必须全局唯一。Phoenix 将 span 加入具有该 ID 的已有追踪，包括其所属项目。ID 冲突可能静默地将 span 发到错误项目。

<a id="idempotent-replay-and-resume"></a>
### 幂等重放与恢复

仅有一个进程摄取 Harbor 作业时，插件支持重放和恢复：

- 使用稳定的外部任务 ID 同步完整数据集快照；
- 根据不可变身份元数据查找实验：零个匹配时创建，一个匹配时复用，多于一个时失败并列出所有匹配 ID；
- 按 Phoenix 样本 `node_id` 和重复编号预加载实验运行；
- 检查保存的最终试验 ID、结果和追踪 ID 后，复用匹配的成功运行；
- 重试或升级失败运行；
- 按运行和评估名称 upsert 所有预期评估。

Phoenix 无法在服务端按元数据过滤实验。插件必须列出数据集的所有实验并在本地过滤。此工作量随实验数增长。服务端身份过滤器或幂等键属于后续工作。

创建运行返回 `409` 时，获取并验证运行。不要未经检查存储数据就忽略冲突。这也能从创建运行后、写完所有评估前的崩溃中恢复。

成功运行不可变。代码尝试更新没有存储错误的运行时，Phoenix 返回 `409`。只有错误运行可更新。成功运行若具有不同试验 ID 或追踪 ID，须失败并显示两个值。插件无法修复它。

通过实验读取 API 返回的评估具有占位 ID。不要用它们查找存储行。按 `(run, evaluation name)` upsert。

先查找再创建实验不是原子操作。每个 Harbor 作业只运行一个摄取器。跨进程或机器并发摄取需要 Phoenix 服务端幂等能力，不在范围内。

<a id="failure-policy"></a>
### 故障策略

选择 Phoenix 插件即要求 Phoenix 记录成功，以避免为无法记录的作业消耗计算资源。用户希望不使用 Phoenix 运行 Harbor 时，可省略插件。

- 在 `on_job_start` 验证数据集身份、Harbor 兼容性、Phoenix 连接和初始写入。抛出明确错误，在试验计算开始前停止作业。
- 插件配置 HTTPX 内置重试，以处理建立连接时的 `ConnectError` 和 `ConnectTimeout`。它不自行重试 HTTP 响应或其他传输错误。除已处理的运行冲突恢复路径外，任何仍失败的运行或评估写入都会抛出错误并停止作业。已完成 Phoenix 记录仍可用，Harbor 会持久保存最终试验结果以供恢复。
- ATIF 发现、转换和上传尽力而为。缺失或无效文件产生警告；有效根节点仍可贡献追踪。构建或上传失败时，记录没有追踪的运行和评估。追踪失败不改变运行错误或 `infra_ok`。成功运行若无追踪，重放时也不能补上关联。
- 保留一个最终失败标志。置位后，在 Harbor 取消兄弟试验期间，使后续试验结束回调不执行任何操作。
- 将每个顶层和步骤异常记录到运行错误，并设置 `infra_ok = 0`。保留 Harbor 在异常同时生成的全部验证器奖励，不将异常改写为 `reward = 0`。追踪根节点的 `ERROR` 状态和状态消息使用同一收集的异常列表。
- 不摄取 Harbor 将重试的尝试。在 Harbor 暴露最终尝试事件前，按逻辑试验名称统计 START 事件并应用 Harbor 重试规则。

适配器在运行时检查能力。设定 Harbor 最低版本，不设上限。测试最低版本、最新稳定版和 Harbor `main`。仅针对已知的已发布不兼容问题添加临时上限。

<a id="8-configuration"></a>
## 8. 配置

通过 Harbor 的 `--plugin-kwarg` 选项传入设置。

| 键 | 默认值 | 用途 |
|---|---|---|
| `dataset` | 根据 Harbor 推导 | 覆盖 Phoenix 数据集名称 |
| `endpoint` | `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix 端点 |
| `api_key` | `PHOENIX_API_KEY` | Phoenix 认证 |
| `trace_mode` | `atif` | 当前：`atif` 或 `null`；规划：`atif`、`otlp` 或 `null` |
| `experiment_name` | 未设置 | 单 Agent 配置作业的精确名称 |
| `experiment_name_template` | `{job.name} · {agent.name} · {agent.model}` | 实验命名 |

实验名称必须能在 Phoenix 比较视图中区分 Agent/模型配置。`{job.name}` 默认为 Harbor 时间戳。两个配置仍同名时，附加简短配置摘要。仅技能、环境或关键字参数不同时可能出现此情况。

规划中的 OTLP 模式不注入导出器配置。用户通过 Harbor 逐 Agent 环境提供端点、凭证和 `openinference.project.name`，插件在作业开始时验证它们 (§5.1)。

<a id="9-implementation-scope"></a>
## 9. 实现范围

<a id="included"></a>
### 包含

- Harbor 插件入口点和兼容性适配器
- 一个配置的 Harbor 数据集，或具有无歧义合成名称的纯直接任务作业
- 基于摘要版本管理的数据集和样本 upsert
- 每个 Agent 和模型对应一个实验
- 具有确定性重复编号的流式实验运行
- 稠密聚合分数和稀疏步骤级分数
- 包内纯 ATIF 转换和 Harbor 专用追踪构建
- ATIF 追踪转换和实验运行关联
- 单步骤及多步骤任务的一条试验级 ATIF 追踪
- 安全的续接和子 Agent 图遍历
- 确定性的部分上传修复
- 数据集、实验、运行或评估写入失败时停止作业；ATIF 失败时警告
- 插件读取的 Harbor API 的契约测试，以及接受 Harbor 版本覆盖的 E2E 目标

<a id="deferred"></a>
### 推迟

- OTLP 项目路由和适配器辅助的追踪到运行关联 (§5.1 和 §5.2)
- 单次物理重试尝试的归属
- 事后摄取命令
- Harbor 生命周期和验证器包装 span
- 关联已插桩验证器独立发出的追踪
- Phoenix 原生 pass^k 和重复聚合汇总
- 多追踪运行，以及除每次运行一条追踪外的任何 `trace_layout` 变体

<a id="acceptance-criteria"></a>
### 验收标准

1. 公共多步骤 Harbor 任务无需修改 Phoenix 服务端，即可创建含运行、稠密分数、步骤分数和可点击 ATIF 追踪的 Phoenix 实验。
2. 双 Agent 作业在一个数据集上创建两个实验，支持并排比较。
3. 顺序重放或恢复不创建重复数据集版本、实验、成功运行、评估或追踪。若多个实验匹配，作业以明确错误失败。
4. 修改任务会创建新数据集版本，各实验保持固定到正确版本。
5. Phoenix 配置无效或端点不可用时，在试验开始前停止 Harbor。之后失去端点会停止作业，而已流式记录到 Phoenix 的运行仍可用。
6. 用户可根据保存的未经缩放的步骤奖励识别失败步骤。
7. 推迟的 OTLP 模式实现后，端点或项目缺失或无效会在试验计算前停止作业。错误显示需添加的精确参数。
8. 推迟的 OTLP 模式实现后，Phoenix 拥有的多步骤 OTLP 适配器为最终尝试创建一条追踪。插件通过回报关联，关联查询作为后备。

标准 8 仅涵盖 Phoenix 拥有的适配器。第三方 Agent 的通用 OTLP 仍受阻塞 (§5.3)。

<a id="10-future-work"></a>
## 10. 后续工作

可能的后续事项：

- 用于读取解析后的任务、试验分配和尝试编号的公共 Harbor API
- 更多多步骤奖励聚合方式
- 感知步骤的验证事件
- 用于回填和调试的事后摄取命令
- 已插桩验证器的追踪链接
- Phoenix 原生跨重复聚合
- 追踪与外部试验 ID 之间更丰富的链接
- 服务端实验身份过滤器或幂等键
- 部分接受 span 或 span upsert

<a id="11-compatibility-assumptions"></a>
## 11. 兼容性假设

Harbor 和 Phoenix 变化时，需要对以下行为进行兼容性检查：

| 假设 | 依据 | 假设错误的风险 |
| --- | --- | --- |
| Harbor 私有作业计划属性保持稳定结构 | 契约测试针对已安装版本运行；E2E 默认 0.21.0 | Harbor 重构破坏摄取 |
| START 计数和公共重试设置能识别最终尝试 | 源码推导的行为，由插件测试覆盖；并非公共契约 | 插件写入中间尝试或跳过最终尝试 |
| 试验结束钩子错误会停止作业并取消兄弟试验 | 源码审阅和隔离钩子测试；未在容器作业中测试 | 记录可能无法在失败时停止 |
| Agent 省略 `trajectory_id`；步骤共享 `session_id`；部分会话 ID 为常量 | Harbor v0.18.0 源码和示例 | 始终设置两个 ID 来处理 |
| 多步骤任务保存步骤局部轨迹，或在原生恢复下保存累积快照 | 加载器测试和 Claude Code E2E 用例 | 步骤轨迹可能缺失或父节点错误 |
| 所有 ATIF Agent 遵循上述身份行为 | 从 28 个 Agent 中抽查约 10 个，外加共享基类 | 始终为 `session_id` 加命名空间来处理 |
| Phoenix 拒绝包含已有 span ID 的批次，并静默丢弃批内重复项 | 已在 Phoenix 源码验证 | 重放失败或丢失 span |

已知缺口：Harbor 若在保存中间尝试后、启动重试前崩溃，恢复可能将该尝试视为完成。插件无法修复此情况。Harbor 应暴露最终尝试事件。
