<a id="experiment-runner-background-process"></a>
# 实验运行器后台进程

<a id="table-of-contents"></a>
## 目录

| # | 章节 | 重点 |
|---|---------|-------|
| 1 | [概览](#executive-summary) | 已实现内容 |
| 2 | [架构](#architecture) | 三个概念、数据流 |
| 3 | [数据模型](#data-model) | 结构与状态机 |
| 4 | [核心组件](#core-components) | ExperimentRunner、RunningExperiment、Job |
| 5 | [设计决策](#design-decisions) | 主要选择和理由 |
| 6 | [生命周期](#lifecycle) | 启动、停止、恢复、完成 |
| 7 | [多副本协调](#multi-replica-coordination) | 心跳、所有权 |
| 8 | [错误处理](#error-handling) | 重试、失败、熔断 |
| — | [附录：关键常量](#appendix-key-constants) | 配置值 |
| — | [附录：相关文档](#appendix-related-documents) | 深入分析与参考 |

---

<a id="executive-summary"></a>
## 概览

<a id="what-we-built"></a>
### 已实现的功能

后台实验运行器具备：

- **不受界面断开影响**：浏览器关闭后实验继续。
- **崩溃恢复**：服务端重启后恢复孤立实验。
- **公平调度**：并发实验间轮询分派。
- **遵循限流**：自适应令牌桶，非阻塞检查。
- **停止/恢复**：允许中途停止，稍后恢复。
- **跨副本协调**：PostgreSQL 部署采用心跳所有权。

<a id="key-files"></a>
### 关键文件

| 文件 | 用途 |
|------|---------|
| `src/phoenix/server/daemons/experiment_runner.py` | 核心实现 |
| `src/phoenix/db/models.py`（ExperimentExecutionConfig） | 数据库结构 |
| `src/phoenix/server/api/mutations/experiment_mutations.py` | GraphQL 变更操作 |

---

<a id="architecture"></a>
## 架构

<a id="three-concepts"></a>
### 三个概念

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ExperimentRunner (Daemon Singleton)                                           │
│   ═══════════════════════════════════                                           │
│   • Experiment registry (_experiments dict)                                     │
│   • Fair dispatch (round-robin by last_served_at)                               │
│   • Concurrency control (semaphore, MAX_CONCURRENT=20)                          │
│   • Heartbeat loop (refresh claimed_at every 5 minutes)                         │
│   • Orphan recovery on startup                                                  │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   RunningExperiment (N instances, in-memory while running)                      │
│   ════════════════════════════════════════════════════════                      │
│   • Task queue (paginated from DB, batch_size=10)                               │
│   • Eval queue (from completed tasks, higher priority)                          │
│   • Retry heap (with exponential backoff)                                       │
│   • In-flight tracking                                                          │
│   • Rate limit check (queries shared token bucket)                              │
│   • UI subscriber management                                                    │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Jobs (transient, self-executing)                                              │
│   ════════════════════════════════                                              │
│   • TaskJob: One dataset example × one repetition (streams to UI)               │
│   • EvalJob: One experiment run × one evaluator (no streaming)                  │
│   • Carries: data + RunningExperiment reference + cancel_scope                  │
│   • execute(): Makes LLM call, reports results to RunningExperiment             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

<a id="data-flow"></a>
### 数据流

```
                       ┌─────────────────┐
                       │  Token Bucket   │
                       │  (per provider) │
                       └────────▲────────┘
                                │ check capacity
                                │
┌─────────────┐        ┌────────┴────┐  try_get_ready_job()  ┌──────────────┐
│ Subscribers │ stream │   Running   │◄──────────────────────│  Experiment  │
│    (UI)     │◄───────│  Experiment │                       │    Runner    │
└─────────────┘        │             │──────────────────────▶│   (daemon)   │
                       └──────▲──────┘        Job            └──────┬───────┘
                              │                                     │
                              │ reports results                     │ job.execute()
                              │ (success/rate_limit/                ▼
                              │  network_error/timeout)      ┌─────────────┐  request   ┌─────────────┐
                              └──────────────────────────────│    Job      │───────────▶│   LLM API   │
                                                             │ (TaskJob/   │◀───────────│             │
                                                             │  EvalJob)   │  response  └─────────────┘
                                                             └─────────────┘

Semaphore flow (MAX_CONCURRENT=20):
  1. Runner acquires semaphore slot
  2. Runner gets Job from RunningExperiment.try_get_ready_job()
  3. Runner spawns task: job.execute() → LLM API → reports to RunningExperiment → release semaphore
```

---

<a id="data-model"></a>
## 数据模型

<a id="experimentexecutionconfig-table"></a>
### ExperimentExecutionConfig 表

| 列 | 类型 | 用途 |
|--------|------|---------|
| `id` | int（PK，FK→experiments.id） | 与实验一对一 |
| `task_config` | JSON | 任务配置，包括提示词和模型等 |
| `status` | string | 生命周期：`RUNNING`、`COMPLETED`、`STOPPED`、`ERROR` |
| `claimed_at` | datetime? | 非空表示副本拥有，空表示无所有者 |
| `claimed_by` | string? | 所属副本 ID |
| `cooldown_until` | datetime? | 下一次允许停止/恢复的最早时间 |
| `last_error` | string? | 界面显示的错误消息 |
| `created_at` | datetime | 配置创建时间 |

**细节：**
- `status` 是权威生命周期状态，每次 UPDATE 都与 `claimed_at` 原子设置。
- `claimed_at` / `claimed_by` 跟踪副本所有权，用于心跳和孤立检测。
- `cooldown_until` 保存未来时间（`now + cooldown`），直到 `cooldown_until <= now` 才能再次切换。
- `cooldown_until` 仅在用户主动停止/恢复时设置，初始启动和孤立恢复不设置，避免阻止首次停止。
- `claimed_by` 通过 `token_hex(8)` 为每个服务端实例生成唯一副本 ID。

<a id="state-machine"></a>
### 状态机

`status` 跟踪生命周期，`claimed_at` 跟踪所有权：

```
        ┌──────────┐
        │ STOPPED  │  ← initial state (claimed_at=NULL)
        └────┬─────┘
             │ start / resume / orphan recovery
             ▼
        ┌──────────┐
        │ RUNNING  │  (claimed_at=now, heartbeat refreshes)
        └────┬─────┘
             │
      ┌──────┼──────────┐
      │      │          │
      ▼      ▼          ▼
┌──────────┐ ┌─────────┐ ┌───────┐
│COMPLETED │ │ STOPPED │ │ ERROR │
└──────────┘ └─────────┘ └───────┘
 (all work    (user       (circuit
  exhausted)   clicked     breaker)
              stop)
```

所有转换都在同一 UPDATE 中原子设置 `status` 和 `claimed_at`。

**关键认识：** 通过查询未完成工作判断是否完成。没有未完成工作就已完成，不单独设置 `completed` 状态。

<a id="whats-not-stored-and-why"></a>
### 不存储什么，以及原因

| 字段 | 不存储原因 |
|-------|----------------|
| `pending_task_ids` | 恢复时从数据库查询未完成运行 |
| `pending_eval_ids` | 恢复时查询评估未完成运行 |
| `retry_queue` | 恢复时从未完成运行重建 |
| `used_browser_credentials` | 安全考虑，全部凭证临时存在 |

**关键认识：** 恢复时重新查询数据库，无需序列化队列，大幅简化崩溃恢复。

---

<a id="core-components"></a>
## 核心组件

<a id="experimentrunner-daemon"></a>
### ExperimentRunner（守护进程）

**作用：** 管理所有运行实验的单例守护进程，在服务端整个生命周期作为后台任务运行。

**职责：**
1. **实验注册表**：内存字典映射 experiment_id → RunningExperiment。
2. **公平调度**：按 `last_served_at` 时间戳轮询。
3. **并发控制**：信号量限制全部实验的总在途作业数。
4. **心跳**：定期刷新数据库所有权认领。
5. **孤立恢复**：启动及周期扫描时认领过期实验。

**主循环：**
1. 无注册实验时等待工作事件，而非轮询。
2. 获取信号量槽位，达到最大并发则阻塞。
3. 轮询实验，寻找就绪作业。
4. 以并发任务执行作业。
5. 完成回调更新实验状态并释放槽位。

**细节：** 在寻找作业**之前**获取信号量。全部限流导致无就绪作业时，释放信号量并短暂等待后重试。

### RunningExperiment

**作用：** 单个运行实验的内存表示，仅在本副本活跃运行期间存在。

**职责：**
1. **队列管理**：任务队列、评估队列和重试堆，优先级为评估 > 重试 > 任务。
2. **限流检查**：向守护进程返回作业**前**检查令牌桶。
3. **回调处理**：处理成功、失败、限流和超时。
4. **界面流式输出**：维护订阅者列表，实时发送数据块。
5. **完成检测**：队列全空且数据库无工作时报告完成。

**队列优先级**从高到低：
1. **评估队列**：评估已完成任务，快速并维持流程。
2. **重试堆**：已可重试的作业，按 `ready_at` 排序。
3. **任务队列**：数据集新任务，从数据库每批 10 个分页加载。

**细节：** 分批加载避免大数据集耗尽内存，`_task_db_exhausted` 标记全部任务已加载。

<a id="jobs-taskjob--evaljob"></a>
### 作业（TaskJob / EvalJob）

**作用：** 自包含工作单元，执行 LLM 调用并触发回调。

| 作业类型 | 用途 | 向界面流式输出？ |
|----------|---------|----------------|
| TaskJob | 一个数据集示例 × 一次重复运行提示词 | 是 |
| EvalJob | 一个实验运行执行一个评估器 | 否 |

**生命周期：**
1. 创建时携带全部执行数据，执行期间无需外部查找。
2. 持有父 RunningExperiment 引用，以报告结果。
3. 在取消作用域内执行，便于停止时干净取消。
4. 按成功、限流、网络错误、超时或永久失败，调用 RunningExperiment 对应方法。

**细节：**
- Job 无状态，构造时传入全部上下文。
- `retry_count` 跟踪已重试次数。
- 自带超时，默认 120 秒，防止 LLM 调用挂起。
- 作业内数据库写入屏蔽取消，防止连接池损坏。

---

<a id="design-decisions"></a>
## 设计决策

<a id="advisor-pattern-for-rate-limiting"></a>
### Advisor 限流模式

**背景：** LLM 调用前需限流检查，两种方式：
- **Gatekeeper**：Job 在 `execute()` 内检查，限流则阻塞或失败。
- **Advisor**：Experiment 返回 Job 前检查。

**决策：** 使用 Advisor，在 `try_get_ready_job()` 弹出作业前检查容量。

**影响：**
- ✅ Daemon 从不阻塞等待限流。
- ✅ 轮询公平，跳过限流实验，其余继续。
- ✅ 不浪费信号量槽位。
- ⚠️ 必须不执行作业即可确定限流键。
- ⚠️ 令牌桶跨实验共享，不能逐实验独立。

<a id="round-robin-fairness"></a>
### 轮询公平性

**背景：** 多实验可并发，需防止单个独占容量。

**决策：** 按 `last_served_at` 轮询，时间较旧者优先。新实验初始化为最早的 `datetime.min`。

**机制：**
1. 按 `last_served_at` 从旧到新排序。
2. 逐实验调用 `try_get_ready_job()`。
3. 首个有就绪且不限流作业的实验获得槽位。
4. 仅实际分派时更新 `last_served_at`。

**关键行为：**

| 场景 | 行为 | 理由 |
|----------|----------|-----------|
| **新实验加入** | datetime.min 获优先 | 刚点击启动的用户立即得到反馈 |
| **实验限流** | 跳过，`last_served_at` 不变 | 不丢失轮次，下次优先检查 |
| **实验退出** | 干净移除，无扭曲 | 其余继续公平交替 |
| **同提供商不同实验** | 公平交替 | 共享令牌桶，轮询分配容量 |

**影响：**
- ✅ 机会均等，各实验按比例获得槽位。
- ✅ 工作守恒，限流不阻碍其他实验。
- ✅ 加入退出平稳，拓扑变化不扭曲公平。
- ⚠️ 新实验会暂时独占，这是体验设计。
- ⚠️ 无优先级机制，不能标记紧急。

<a id="heartbeat-based-ownership-vs-listennotify"></a>
### 心跳所有权（对比 LISTEN/NOTIFY）

**背景：** PostgreSQL 部署可多副本并行，需防止同一实验同时运行两次。

**决策：** 使用 `claimed_at` 心跳所有权，而非 PostgreSQL LISTEN/NOTIFY。

**影响：**
- ✅ 支持 SQLite、PostgreSQL 等任意数据库。
- ✅ 简单易实现和理解。
- ✅ 过期认领即崩溃副本，孤立恢复直接。
- ⚠️ 崩溃后恢复延迟 10 分钟，可接受取舍。
- ⚠️ 需每 5 分钟运行心跳。

<a id="no-queue-state-persistence"></a>
### 不持久化队列状态

**背景：** 停止或崩溃后需继续，可选：
- 序列化待处理任务、重试堆等队列状态入库。
- 恢复时查询未完成运行。

**决策：** 不持久化队列，恢复时重新查询数据库。

**影响：**
- ✅ 实现显著简化。
- ✅ 无额外队列结构复杂度。
- ✅ 幂等恢复，不存在过期队列。
- ⚠️ 可能重新查询已完成工作，由查询过滤。
- ⚠️ 丢失退避状态，作业从 backoff=0 重启。

<a id="separate-circuit-breakers-for-tasks-and-evals"></a>
### 任务和评估独立熔断器

**背景：** 提供商宕机时逐个重试浪费时间，需快速检测。

**决策：** 连续失败 5 次触发熔断，任务和评估分别设置。

**影响：**
- ✅ 失败 5 次即停，而非 5×N，快速发现故障。
- ✅ 不同提供商可独立，一方失败不终止另一方。
- ⚠️ 一次成功重置计数，这是允许恢复的设计。
- ⚠️ 不随时间自动重置，实验停止后需用户恢复。

<a id="catch-and-retry-for-background-loops"></a>
### 后台循环捕获并重试

**背景：** 心跳、孤立扫描与主分派在同一任务组，未处理异常会使整个 Daemon 崩溃。

**决策：** 循环体用 try/except 包裹，记录错误，下个周期重试。

**考虑过的替代：**

| 选项 | 行为 | 未选原因 |
|--------|----------|----------------|
| 失败时停止实验 | 心跳失败即停全部实验 | 状态复杂，实验无法推进 |
| N 次失败后崩溃 | 重试 N 次再终止 Daemon | 更复杂，丢失在途工作 |

**影响：**
- ✅ 实现简单。
- ✅ 暂时数据库错误不终止运行实验。
- ⚠️ 心跳长期失效可能脑裂，其他副本可能夺取实验。
- ⚠️ 若脑裂，孤立恢复保证最终一致。

---

<a id="lifecycle"></a>
## 生命周期

<a id="start-experiment"></a>
### 启动实验

**前提：** 配置存在，实验尚未运行。

**步骤：**
1. **原子认领**：调用方，即变更操作或孤立扫描，通过 `UPDATE ... WHERE claimed_at IS NULL`，孤立时用 `< cutoff`，原子取得所有权。
2. **重写所有权时间**：`start_experiment` 再执行无条件 UPDATE，设置 `claimed_at` 并清除 `last_error`；调用方已认领，无竞态风险。
3. **创建内存状态**：实例化带队列和回调的 RunningExperiment。
4. **注册并唤醒**：加入注册表，设置工作可用事件。

**细节：** 安全认领在**调用方**，而非 `start_experiment` 内。`start_experiment` 自身不防重复启动，依赖调用方先赢得原子认领。

<a id="stop-experiment"></a>
### 停止实验

**可停止实验的执行方：**

| 执行方 | 触发 | 需要冷却？ |
|-------|---------|-----------------|
| 用户停止按钮 | GraphQL 变更 | 是，5 秒 |
| 用户关闭浏览器 | 连接关闭 | 否 |
| 完成 | 全部工作完成 | 否 |
| 熔断器 | 连续失败 5 次 | 否 |
| 其他副本 | 检测到过期认领 | 否 |

**步骤**，单次原子 UPDATE：
1. **WHERE 约束状态与冷却**：`WHERE claimed_at IS NOT NULL AND (cooldown_until IS NULL OR cooldown_until <= now)`。
2. **原子设置全部字段**：`SET claimed_at=NULL, claimed_by=NULL, status='STOPPED', cooldown_until=now+5s`。
3. **更新 0 行时诊断**：SELECT 判断不存在、已停止（幂等）或冷却中。
4. **从注册表移除**：必须用 `pop()`，不用 `get()`，对防竞态至关重要。
5. **取消在途作业**：通过 anyio 取消作用域。

**细节：**
- RunningExperiment 的 `stop()` 不调用 `on_done`，调用方协调清理。
- 必须 `pop()` 原子移除，防心跳竞态。
- 幂等，可安全重复调用。

> **深入分析：** 见[附录：停止深入分析](./experiment-runner-background-process/appendix-stopping-deep-dive.md)。

<a id="resume-experiment"></a>
### 恢复实验

**前提：** 配置存在，当前未运行，`claimed_at` 为 NULL。

**步骤：**
1. **验证未运行**：检查 `claimed_at IS NULL`。
2. **认领并启动**：同 start_experiment。

**关键认识：** 恢复是通用的补齐缺失操作。不还原队列，而是查询数据库未完成内容并补齐。

> **深入分析：** 原子认领和多副本竞争见[附录：恢复深入分析](./experiment-runner-background-process/appendix-resume-deep-dive.md)。

<a id="work-reconstruction"></a>
### 工作重建

启动和恢复时通过两条数据库查询重建工作：

| 查询 | 查找内容 | 时机 |
|-------|---------------|-------------|
| `get_experiment_incomplete_runs_query` | 缺少成功任务运行的数据集示例 | 每轮分派，直到耗尽 |
| `get_runs_with_incomplete_evaluations_query` | 已完成但缺少附加评估器标注的运行 | 无排队或在途评估时 |

正常执行时，任务完成由 `on_task_success` **响应式**入队评估，无需查库。评估扫描（`_ensure_eval_buffer`）仅在没有在途评估时运行，结构上避免重复：此时全部响应式入队评估已写入标注。

同一设计无需特殊处理即可覆盖：

| 场景 | 任务查询结果 | 评估查询结果 |
|----------|-----------------|-----------------|
| **新启动** | 全部示例 | 无，尚无运行 |
| **崩溃恢复** | 失败或缺失任务 | 缺少标注的运行 |
| **附加新评估器** | 无，任务已完 | 全部运行 × 新评估器 |
| **新增数据集示例** | 新示例 | 无，尚无运行 |
| **错误后重试** | 出错任务 | 标注失败的运行 |

<a id="completion"></a>
### 完成

**检测：** `has_work()` 检查全部待处理来源：
- 任务队列、评估队列、重试堆、在途作业。
- `_task_db_exhausted`，数据库无未完成任务。
- `_eval_db_exhausted`，数据库无未完成评估。

`has_work()` 返回 False，实验即完成。

**步骤：**
1. 设置 `_active = False`。
2. 记录成功/失败计数汇总。
3. 调用 `on_done`，移除注册表并设置数据库状态。

---

<a id="multi-replica-coordination"></a>
## 多副本协调

<a id="heartbeat-loop"></a>
### 心跳循环

**目的：** 防止其他副本夺取本副本活跃实验。

**行为：**
- 每 5 分钟运行。
- 更新拥有的全部实验的 `claimed_at`。
- 检测丢失所有权，即内存有实验而 UPDATE 未匹配。

**丢失所有权：** 内存实验未被心跳 UPDATE 返回时，说明其他副本或用户已接管，本地停止，无需更新数据库。

**细节：** 仅更新 `claimed_by` 与当前副本 ID 一致的实验，避免误刷新非自身实验。

<a id="orphan-recovery"></a>
### 孤立恢复

**目的：** 恢复崩溃副本遗留的孤立实验。

**时机：**
1. **启动时**：立即恢复停机期间形成的孤立实验。
2. **周期性**：每 10–15 分钟带抖动扫描，捕捉其他副本遗留。

**定义：** `claimed_at IS NOT NULL` 且早于 `STALE_CLAIM_TIMEOUT`，即 10 分钟。`claimed_at IS NULL` 表示有意停止，绝不自动恢复。

**步骤：**
1. 查询孤立实验，`claimed_at IS NOT NULL AND claimed_at < cutoff`。
2. 对每个实验尝试带 WHERE 的原子认领。
3. 成功则启动。

**抖动：** 周期扫描随机增加 0–5 分钟，避免多副本同时重启惊群。

**细节：** 必须在数据库会话之外启动实验，避免嵌套事务死锁。

<a id="race-condition-prevention"></a>
### 防止竞态

| 场景 | 防护 |
|----------|------------|
| 两副本认领同一孤立实验 | 原子 `UPDATE...WHERE...RETURNING` |
| 心跳期间停止 | `stop_experiment` 先 `pop()` 移除 |
| 已运行时恢复 | 先检查 `claimed_at IS NULL` |
| 快速停止/恢复 | 用户切换冷却 5 秒，初次启动不冷却 |
| 停止后的作业回调 | 全部检查 `_active` |
| 孤立恢复死锁 | 数据库会话外启动 |

<a id="concurrency-invariants"></a>
### 并发不变量

| 不变量 | 保证机制 |
|-----------|-------------|
| 状态变化 → 从注册表移除 | 全部停止路径用 `pop()`，不用 `get()` |
| 同一行无嵌套事务 | 会话外调用 `start_experiment()` |
| 仅一副本拥有实验 | 原子 `UPDATE...WHERE...RETURNING` |
| 停止后不入队工作 | 全部回调检查 `_active` |
| 作业正常结束 | 允许在途完成，不中途终止 |

---

<a id="error-handling"></a>
## 错误处理

<a id="error-categories"></a>
### 错误分类

| 类别 | 示例 | 操作 | 重试？ |
|----------|----------|--------|--------|
| **限流** | 429、`UnavailableTokensError` | 退避入队并更新令牌桶 | 是，不限次数 |
| **暂时性** | 超时、连接错误、SQLAlchemyError | 退避入队 | 是，最多 3 次 |
| **永久性** | 400、无效 API 密钥、错误请求 | 标记失败 | 否 |

<a id="retry-policy"></a>
### 重试策略

**公式：** `backoff = base_delay × 2^(retry_count - 1)`

| 重试 | 延迟 |
|-------|-------|
| 1 | 1 秒 |
| 2 | 2 秒 |
| 3 | 4 秒 |

重试 3 次后，暂时性错误转为永久失败。

**限流处理：** 不计入重试上限，以指数退避无限入队，同时通知令牌桶降低后续请求速率。

<a id="circuit-breaker"></a>
### 熔断器

**目的：** 快速发现提供商故障，停止浪费重试。

**行为：**
- 跟踪连续失败。
- 5 次后触发。
- 一次成功重置。
- 触发时通知界面订阅者、关闭流并停止实验。

**为何分离任务与评估熔断器：** 可能使用不同提供商。评估提供商故障，不应阻止健康提供商执行任务。

<a id="ui-error-communication"></a>
### 界面错误通知

**熔断时：**
1. 向全部订阅者发送错误载荷。
2. 关闭流，客户端正常触发 EndOfStream。
3. 清空订阅者。
4. 停止实验。
5. 写入 `last_error`。

**细节：** 必须显式关闭流，仅发错误不会结束订阅。

---

## GraphQL API

<a id="experimentjob-type"></a>
### ExperimentJob 类型

`ExperimentJob` 通过 `status` 枚举暴露生命周期：

```graphql
enum ExperimentJobStatus {
  RUNNING
  COMPLETED
  STOPPED
  ERROR
}

type ExperimentJob implements Node {
  id: ID!
  experiment: Experiment!
  status: ExperimentJobStatus!
  createdAt: DateTime!
  lastError: String
}
```

`Experiment` 有可选 `backgroundJob: ExperimentJob`。客户端通过 Python SDK 提交的实验为 null；Playground 启动、服务端管理的实验非 null。

<a id="mutations"></a>
### 变更操作

- `stopExperiment(experimentId: ID!)` → `StopExperimentPayload`：带冷却保护的原子 UPDATE。
- `resumeExperiment(experimentId: ID!)` → `ResumeExperimentPayload`：带冷却保护的原子 UPDATE。
- `deleteExperiments(input: DeleteExperimentsInput!)`：DELETE 前调用 `stop_experiment()`，避免外键冲突。

---

<a id="frontend-navigation-dialog"></a>
## 前端：导航对话框

运行期间离开 Playground 时显示对话框，行为取决于是否临时实验：

<a id="ephemeral-experiments"></a>
### 临时实验

临时实验在订阅断开时停止。订阅 `finally` 块在 `is_ephemeral=True` 时调用 `stop_experiment`。

**对话框：** “离开本页将停止实验，请停留等待完成。”
- **停留**，主操作：取消导航。
- **离开**：导航离开，断开连接后停止。

<a id="non-ephemeral-experiments"></a>
### 非临时实验

通过守护进程在后台继续运行。

**对话框：** “实验将在后台继续运行。”
- **停留**：取消导航。
- **停止并删除**，危险操作：先删除再离开。
- **继续运行**，主操作：离开，守护进程继续。

---

<a id="appendix-key-constants"></a>
## 附录：关键常量

| 常量 | 值 | 用途 |
|----------|-------|---------|
| `MAX_CONCURRENT` | 20 | 全局并发槽位 |
| `POLL_INTERVAL` | 0.1s | 分派尝试间隔 |
| `MAX_CONSECUTIVE_ERRORS` | 50 | 内部连续错误达到该数停止守护进程，捕获程序缺陷 |
| `STALE_CLAIM_TIMEOUT` | 10 min | 认领过期阈值，来自配置 |
| `HEARTBEAT_INTERVAL` | 5 min | 刷新频率，`STALE_CLAIM_TIMEOUT / 2` |
| `ORPHAN_SCAN_INTERVAL` | 10 min | 扫描基础间隔，`= STALE_CLAIM_TIMEOUT` |
| `ORPHAN_SCAN_JITTER` | 0-1 min | 防惊群抖动，`STALE_CLAIM_TIMEOUT × 0.1` |
| `max_retries` | 3 | 逐作业重试上限 |
| `base_backoff_seconds` | 1.0 | 初始重试延迟 |
| `_task_batch_size` | 10 | 每次查库加载任务数 |
| `circuit_breaker_threshold` | 5 | 连续失败熔断阈值 |
| `job_timeout` | 120s (TaskJob), 60s (EvalJob) | 默认 LLM 超时 |
| `shield_timeout` | 30s | 屏蔽取消的写库超时 |

<a id="appendix-file-references"></a>
## 附录：文件参考

| 概念 | 文件 |
|---------|------|
| ExperimentRunner 守护进程 | `experiment_runner.py` |
| RunningExperiment | `experiment_runner.py` |
| TaskJob / EvalJob | `experiment_runner.py` |
| 令牌桶注册表 | `experiment_runner.py` |
| 数据库模型 | `models.py` |
| 状态类型（`Literal`） | `db/types/experiment_config.py` |
| 停止/恢复变更 | `experiment_mutations.py` |
| GraphQL ExperimentJob 类型 | `api/types/ExperimentJob.py` |
| 导航对话框 | `pages/playground/ConfirmExperimentNavigationDialog.tsx` |
| 实验表格状态列 | `pages/experiments/ExperimentsTable.tsx` |
| 操作菜单，停止/恢复 | `components/experiment/ExperimentActionMenu.tsx` |

<a id="appendix-related-documents"></a>
## 附录：相关文档

<a id="lifecycle-state-transitions"></a>
### 生命周期（状态转换）

| 文档 | 用途 | 阅读时机 |
|----------|---------|--------------|
| [生命周期](./experiment-runner-background-process/appendix-lifecycle.md) | 模式和时间线概览 | 首先阅读 |
| [停止深入分析](./experiment-runner-background-process/appendix-stopping-deep-dive.md) | 形式化分析：5 类执行方、证明和清单 | 修改停止逻辑时 |
| [恢复深入分析](./experiment-runner-background-process/appendix-resume-deep-dive.md) | 形式化分析：原子认领、冷却 | 修改恢复逻辑时 |

<a id="rate-limiting"></a>
### 限流

| 文档 | 用途 | 阅读时机 |
|----------|---------|--------------|
| [限流](./experiment-runner-background-process/appendix-rate-limiting.md) | 设计及提供商参考 | 修改限流时 |

<a id="reference-documents"></a>
### 参考文档

| 文档 | 用途 |
|----------|---------|
| [常见问题](./experiment-runner-background-process/appendix-faq.md) | 常量和架构的原因 |
| [结构设计](./experiment-runner-background-process/appendix-schema.md) | 数据库结构决策 |
| [错误类型](./experiment-runner-background-process/appendix-error-types.md) | 提供商 SDK 错误层级 |

<a id="backup-original-files"></a>
### 备份（原始文件）

原始未合并文件保留在 `experiment-runner-background-process/backup/`。
