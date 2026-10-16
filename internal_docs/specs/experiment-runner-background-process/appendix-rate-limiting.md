<a id="appendix-rate-limiting-architecture-and-edge-cases"></a>
# 附录：限流、架构与边界情况

> 本附录记录形成实验运行器设计的架构探索和第一性原理分析，包括限流策略、自执行作业的命令模式，以及全面的边界情况处理。

---

<a id="table-of-contents"></a>
## 目录

1. [心智模型：外卖配送](#mental-model-food-delivery-service)
2. [第一性原理](#first-principles)
3. [最小架构](#the-minimal-architecture)
4. [命令模式：自执行作业](#the-command-pattern-self-executing-jobs)
5. [两种方式：Gatekeeper 与 Advisor](#two-approaches-gatekeeper-vs-advisor)
6. [为何 Advisor 更优](#why-advisor-wins)
7. [抽象边界](#abstraction-boundaries)
8. [熔断器：网络故障处理](#circuit-breaker-network-failure-handling)
9. [边界情况](#edge-cases)
10. [实现说明](#implementation-notes)

---

<a id="mental-model-food-delivery-service"></a>
## 心智模型：外卖配送

通过类比最容易理解限流方式：

```
Restaurants      = Experiments (sources of work)
Delivery Drivers = Concurrency slots (execution capacity)
Prep Time        = Rate limit (kitchen can only make N orders/hour)
Dispatch App     = Daemon (scheduler)
Order Slip       = Job (self-contained work unit)
```

**Gatekeeper 方式**：派骑手去餐厅，饭没做好就等待。

```
Driver arrives at Restaurant A
→ "Food not ready" (429)
→ Driver waits 1 min, asks again
→ Still not ready, waits 2 min
→ Driver blocked for entire backoff

Meanwhile: Restaurant B has ready orders, but drivers are waiting at A.
```

**Advisor 方式**：饭做好才派骑手。

```
Driver asks dispatch for work
→ Dispatch checks: "Restaurant A ready?" No.
→ Dispatch checks: "Restaurant B ready?" Yes.
→ Driver sent to B, picks up immediately

Restaurant A's order queued for later when kitchen catches up.
```

**关键认识：** Advisor 中，订单（Job）包含全部所需内容，骑手只负责取送。餐厅（Experiment）决定订单何时可以配送。

| | Gatekeeper | Advisor |
|--|------------|---------|
| 等待期间骑手 | 阻塞在餐厅 | 服务其他餐厅 |
| 重试状态归属 | 骑手等待 | 餐厅排队 |
| 餐厅 B 吞吐 | 降低，骑手较少 | 完整，全部骑手可用 |

---

<a id="first-principles"></a>
## 第一性原理

以下基础认识指导整个设计。

<a id="1-the-end-to-end-principle"></a>
### 1. 端到端原则

*来自网络设计：将智能放在端点，中间保持简单。*

```
Endpoints (smart):     Experiment ←───────────────────→ LLM API
Middle (dumb):                    ←── Job ── Daemon ──→
```

| 组件 | 应有特性 | 原因 |
|-----------|-----------|-----|
| **Experiment** | 智能 | 了解任务、重试、限流和回调 |
| **Job** | 自包含 | 携带全部内容，自行报告 |
| **Daemon** | 简单 | 只分派并控制并发 |

中间层，即 Daemon 和 Job 执行，应尽量简单，智能位于边缘。

<a id="2-separation-of-constraints"></a>
### 2. 约束分离

存在**三个独立约束**：

| 约束 | 来源 | 控制机制 | 单位 |
|------------|--------|---------------|------|
| **限流** | 外部提供商 | 令牌桶 | 请求/秒 |
| **并发** | 内部资源 | 信号量 | 同时请求数 |
| **公平性** | 内部体验 | 轮询 | 下一个实验 |

它们相互**正交**，混合会造成混乱，应分别处理。

<a id="3-state-locality"></a>
### 3. 状态局部性

*状态只应存在于需要它的位置。*

| 状态 | 位置 | 原因 |
|-------|----------|-----------|
| 限流模型 | 逐提供商令牌桶 | 跨实验共享 |
| 任务队列 | Experiment | 拥有自身任务 |
| 重试队列 | Experiment | 决定重试策略 |
| 在途跟踪 | Experiment | 实验需要了解 |
| 并发计数 | 全局信号量 | 共享资源 |

**关键认识：** Job 不应保留超出执行生命周期的状态，它是临时对象。

<a id="4-work-conservation"></a>
### 4. 工作守恒

*只要有可执行的有用工作，系统就应一直做有用工作。*

```
BAD:  Slots idle while work is ready (Gatekeeper blocking)
GOOD: If any experiment has ready work, something is executing it
```

这就是 Advisor 优于 Gatekeeper 的原因：其他工作就绪时，没有槽位阻塞。

<a id="5-minimal-coordination"></a>
### 5. 最小协调

*只在必要时协调，独立事项保持独立。*

| 是否需要协调？ | 答案 |
|------------------------------|--------|
| 不同提供商的两个实验 | **否**，无共享约束 |
| 同提供商的两个实验 | **是**，共享限流 |
| 并发与限流 | **否**，约束正交 |

不同提供商实验应完全独立，唯一协调来自共享限流。

<a id="6-information-hiding"></a>
### 6. 信息隐藏

| 组件 | 需知道 | 无需知道 |
|-----------|---------------|----------------------|
| **Experiment** | 自身任务、提供商、令牌桶 | 其他实验、并发上限 |
| **Daemon** | 存在哪些实验、并发上限 | 任务详情、提供商细节 |
| **Job** | 如何执行和报告 | 其他作业、守护进程、并发 |
| **令牌桶** | 请求速率 | 请求用途 |

各组件了解越少，架构越清晰。

<a id="7-what-were-actually-scheduling"></a>
### 7. 实际调度的是什么

调度的不是任务或工作进程，而是**执行许可**。

```
Execution permit = Rate capacity ∧ Concurrency capacity
```

两道关卡都打开时，Job 才能执行：
1. **速率**：令牌桶有容量。
2. **并发**：信号量有许可。

---

<a id="the-minimal-architecture"></a>
## 最小架构

只保留本质，三个概念，不再增加。

<a id="the-three-concepts"></a>
### 三个概念

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   EXPERIMENT                                                    │
│   ══════════                                                    │
│                                                                 │
│   • Owns tasks (pending queue, retry queue, eval queue)         │
│   • Owns retry policy (max retries, backoff)                    │
│   • References shared token bucket (per provider)               │
│   • Creates self-executing Jobs                                 │
│   • Receives callbacks from Jobs                                │
│   • Handles short-circuiting (cached, invalid, etc.)            │
│                                                                 │
│   Interface:                                                    │
│     try_get_ready_job() → Job | None                            │
│     is_complete() → bool                                        │
│     cancel() → void                                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   DAEMON                                                        │
│   ══════════                                                    │
│                                                                 │
│   • Knows which experiments are running                         │
│   • Owns concurrency semaphore                                  │
│   • Enforces fairness (round-robin across experiments)          │
│   • Dispatches Jobs into execution                              │
│   • Handles graceful shutdown                                   │
│                                                                 │
│   Interface:                                                    │
│     run() → awaitable (main loop)                               │
│     shutdown() → void                                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   JOB                                                           │
│   ══════════                                                    │
│                                                                 │
│   • Self-contained (data + behavior + callbacks)                │
│   • Executes itself (Command Pattern)                           │
│   • Reports via callbacks (no return value)                     │
│   • Transient (no state survives execution)                     │
│                                                                 │
│   Interface:                                                    │
│     execute() → awaitable                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

<a id="what-is-a-job-concretely"></a>
### Job 具体是什么

**Job** 是进行一次 LLM API 调用的最小工作单元。

| Job 类型 | 定义 | 标识 |
|----------|------------|----------|
| **任务作业** | 一行数据 × 一次重复 | `(experiment_id, row_id, repetition)` |
| **评估作业** | 一个任务结果 × 一个评估器 | `(experiment_id, row_id, repetition, evaluator_id)` |

**示例：**
```
Experiment:
  - Dataset: 100 rows
  - Repetitions: 3
  - Evaluators: 2 (correctness, relevance)

Task Jobs: 100 rows × 3 reps = 300 Jobs
Eval Jobs: 300 results × 2 evaluators = 600 Jobs (if all tasks succeed)
Total: up to 900 Jobs
```

**队列中：**
```python
# Task queue: (row, repetition) pairs
_task_queue = [
    (row_1, rep_1),
    (row_1, rep_2),
    (row_1, rep_3),
    (row_2, rep_1),
    (row_2, rep_2),
    (row_2, rep_3),
    ...,
]

# Eval queue: populated as tasks complete
_eval_queue = [
    (row_1_rep_1_result, correctness_evaluator),
    (row_1_rep_1_result, relevance_evaluator),
    ...,
]
```

---

<a id="the-command-pattern-self-executing-jobs"></a>
## 命令模式：自执行作业

Job 是**命令**，即四人组设计模式：封装执行某个操作所需全部内容的对象。

<a id="taskjob-vs-evaljob"></a>
### TaskJob 与 EvalJob

任务作业和评估作业行为不同：

| 方面 | TaskJob | EvalJob |
|--------|---------|---------|
| **输入** | 数据行和重复编号 | 任务结果和评估器配置 |
| **流式输出** | 是，向界面发送数据块 | 否 |
| **输出表** | `experiment_runs` | `experiment_run_annotations` |
| **优先级** | 较低 | 较高，先评估再新任务 |

采用显式类型，提高清晰度和类型安全：

```python
@dataclass
class TaskJob:
    """
    Execute a task: one dataset row × one repetition.
    Streams chunks to UI during execution.
    """

    # Identity
    experiment_id: str
    row_id: str
    repetition: int

    # Input
    messages: list[Message]
    invocation_parameters: dict

    # Execution context
    client_factory: Callable[[], AsyncContextManager[Client]]
    is_rate_limit_error: Callable[[Exception], bool]
    timeout: float

    # Callbacks (closures over Experiment)
    on_chunk: Callable[[Chunk], Awaitable[None]]  # Required - tasks stream
    on_success: Callable[[Result], Awaitable[None]]
    on_rate_limit: Callable[[], Awaitable[None]]
    on_network_error: Callable[[Exception], Awaitable[None]]
    on_failure: Callable[[Exception], Awaitable[None]]
    on_timeout: Callable[[], Awaitable[None]]

    async def execute(self) -> None:
        """Execute task with streaming."""
        try:
            async with asyncio.timeout(self.timeout):
                async with self.client_factory() as client:
                    chunks = []
                    async for chunk in client.chat_stream(
                        self.messages, **self.invocation_parameters
                    ):
                        chunks.append(chunk)
                        await self.on_chunk(chunk)  # Stream to UI
                    result = combine_chunks(chunks)
            await self.on_success(result)
        except asyncio.TimeoutError:
            await self.on_timeout()
        except Exception as e:
            if self.is_rate_limit_error(e):
                await self.on_rate_limit()
            elif self._is_network_error(e):
                await self.on_network_error(e)
            else:
                await self.on_failure(e)


@dataclass
class EvalJob:
    """
    Execute an evaluator on a task result.
    No streaming - evaluators run silently.
    """

    # Identity
    experiment_id: str
    row_id: str
    repetition: int
    evaluator_id: str

    # Input
    task_result: str  # Output from the task
    evaluator_template: str

    # Execution context
    client_factory: Callable[[], AsyncContextManager[Client]]
    is_rate_limit_error: Callable[[Exception], bool]
    timeout: float

    # Callbacks (no on_chunk - evals don't stream)
    on_success: Callable[[EvalResult], Awaitable[None]]
    on_rate_limit: Callable[[], Awaitable[None]]
    on_network_error: Callable[[Exception], Awaitable[None]]
    on_failure: Callable[[Exception], Awaitable[None]]
    on_timeout: Callable[[], Awaitable[None]]

    async def execute(self) -> None:
        """Execute evaluator without streaming."""
        try:
            async with asyncio.timeout(self.timeout):
                async with self.client_factory() as client:
                    result = await client.chat(self._build_eval_messages())
                    parsed = self._parse_eval_result(result)
            await self.on_success(parsed)
        except asyncio.TimeoutError:
            await self.on_timeout()
        except Exception as e:
            if self.is_rate_limit_error(e):
                await self.on_rate_limit()
            elif self._is_network_error(e):
                await self.on_network_error(e)
            else:
                await self.on_failure(e)


# Type alias for dispatch - Daemon doesn't care which type
Job = TaskJob | EvalJob
```

<a id="why-this-is-powerful"></a>
### 为何有效

| 优点 | 说明 |
|---------|-------------|
| **自包含** | Job 携带全部所需信息，执行时无外部依赖 |
| **解耦** | Experiment 和 Daemon 彼此不可见，只看到 Job |
| **可测试** | 模拟回调，可独立测试 Job |
| **提供商无关** | Daemon 不区分 OpenAI、Anthropic，由 Job 处理 |
| **可重试** | 失败时 Experiment 创建新 Job，旧 Job 可回收 |

<a id="the-closure-pattern"></a>
### 闭包模式

回调是捕获 Experiment 方法的闭包：

```python
class Experiment:
    def _create_task_job(self, row_id: str, repetition: int) -> TaskJob:
        return TaskJob(
            experiment_id=self.id,
            row_id=row_id,
            repetition=repetition,
            messages=self._build_messages(row_id),
            invocation_parameters=self._invocation_parameters,
            client_factory=self._client._client_factory,
            is_rate_limit_error=self._is_rate_limit_error,
            timeout=self._timeout,
            # Callbacks close over self and task identity
            on_chunk=lambda chunk: self._handle_chunk(row_id, repetition, chunk),
            on_success=lambda result: self._handle_task_success(row_id, repetition, result),
            on_rate_limit=lambda: self._handle_rate_limit(row_id, repetition),
            on_network_error=lambda e: self._handle_network_error(row_id, repetition, e),
            on_failure=lambda e: self._handle_task_failure(row_id, repetition, e),
            on_timeout=lambda: self._handle_timeout(row_id, repetition),
        )

    def _create_eval_job(
        self, row_id: str, repetition: int, evaluator: Evaluator, task_result: str
    ) -> EvalJob:
        return EvalJob(
            experiment_id=self.id,
            row_id=row_id,
            repetition=repetition,
            evaluator_id=evaluator.id,
            task_result=task_result,
            evaluator_template=evaluator.template,
            client_factory=self._get_eval_client_factory(evaluator),  # May be different provider
            is_rate_limit_error=self._get_eval_rate_limit_error(evaluator),
            timeout=self._eval_timeout,
            # No on_chunk - evals don't stream
            on_success=lambda result: self._handle_eval_success(
                row_id, repetition, evaluator.id, result
            ),
            on_rate_limit=lambda: self._handle_eval_rate_limit(row_id, repetition, evaluator.id),
            on_network_error=lambda e: self._handle_eval_network_error(
                row_id, repetition, evaluator.id, e
            ),
            on_failure=lambda e: self._handle_eval_failure(row_id, repetition, evaluator.id, e),
            on_timeout=lambda: self._handle_eval_timeout(row_id, repetition, evaluator.id),
        )
```

Job 像写好回邮地址并贴好邮票的信封，知道完成后向哪里交付。

---

<a id="two-approaches-gatekeeper-vs-advisor"></a>
## 两种方式：Gatekeeper 与 Advisor

两者采用**相同令牌桶算法**，仅检查令牌的**时机**不同。

<a id="gatekeeper-current-playgroundratelimiter"></a>
### Gatekeeper（当前 PlaygroundRateLimiter）

在包装器内部，**调用 API 时**检查令牌：

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   DAEMON                              EXPERIMENT                │
│   ══════════                          ══════════                │
│                                                                 │
│   "any work?"  ────────────────────▶  "yes, here's a task"      │
│                                       (no rate check)           │
│                                                                 │
│   EXECUTION SLOT                                                │
│   ══════════════                                                │
│                                                                 │
│   Execute task                                                  │
│     │                                                           │
│     ▼                                                           │
│   ┌───────────────┐                                             │
│   │ Check token   │◀──── Rate check HERE (at call time)         │
│   │ bucket        │                                             │
│   └───────────────┘                                             │
│     │                                                           │
│     │ if no token: BLOCK & WAIT                                 │
│     │              (slot is idle)                               │
│     ▼                                                           │
│   LLM API                                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**问题：**
- 槽位阻塞等待令牌。
- 阻塞槽位不能服务其他实验。
- 重试循环藏在槽位内部并阻塞。

<a id="advisor-our-design"></a>
### Advisor（本设计）

在 Experiment 中，**分派时**检查令牌：

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   DAEMON                              EXPERIMENT                │
│   ══════════                          ══════════                │
│                                                                 │
│   "any work?"  ────────────────────▶  Check token bucket        │
│                                       │                         │
│                                       ▼                         │
│                                       Has capacity?             │
│                                       │                         │
│                                       ├── No  → return None     │
│                                       │                         │
│   ◀─────────────────────────────────  └── Yes → return Job      │
│                                                                 │
│   EXECUTION SLOT                                                │
│   ══════════════                                                │
│                                                                 │
│   job.execute()  ───────────────────▶  LLM API (no blocking)    │
│                                                                 │
│   if 429: job.on_rate_limit() ──────▶  Experiment requeues      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**优点：**
- 槽位从不因令牌阻塞。
- A 被限流时，槽位服务 B。
- 重试状态可见，存在实验队列。

<a id="the-key-difference"></a>
### 关键差异

| | Gatekeeper | Advisor |
|--|------------|---------|
| **谁查询令牌桶** | 执行槽位，调用时 | Experiment，分派时 |
| **槽位行为** | 可能阻塞等待 | 从不阻塞 |
| **实验接口** | 有工作吗？ | 有**可分派**工作吗？ |
| **重试位置** | 执行槽位内部，不可见 | 实验队列，可见 |

---

<a id="why-advisor-wins"></a>
## 为何 Advisor 更优

<a id="problem-1-cross-provider-throughput-loss"></a>
### 问题 1：跨提供商吞吐损失

```
Scenario:
  Exp A: OpenAI (throttled to 1 req/s)
  Exp B: Anthropic (100 req/s available)
  10 concurrent slots

Gatekeeper:
  5 slots get A tasks → block waiting for OpenAI tokens
  5 slots get B tasks → proceed
  B throughput: 50% (only 5 slots)

Advisor:
  Daemon asks A → no token → skip
  All 10 slots serve B
  B throughput: 100%
```

<a id="problem-2-retry-blocking"></a>
### 问题 2：重试阻塞

```
Scenario:
  Slot hits 429, internal retry with backoff: 1s, 2s, 4s, 8s

Gatekeeper:
  Slot blocks for entire retry sequence (15+ seconds)
  Slot does NOTHING during backoff waits

Advisor:
  Slot reports 429 → job.on_rate_limit() → freed immediately
  Experiment requeues task for later
  Slot serves other tasks during backoff
```

<a id="problem-3-cross-experiment-interference"></a>
### 问题 3：跨实验干扰

```
Scenario:
  Exp A: 1000 tasks, just hit 429, cooling down
  Exp B: 100 tasks, ready to go
  Same provider, shared slots

Gatekeeper:
  Slots on A tasks block during cooldown
  B slowed by A's throttling

Advisor:
  A says "no work ready" (no token)
  Slots serve B instead
```

<a id="when-gatekeeper-is-fine"></a>
### Gatekeeper 何时可用

| 场景 | Gatekeeper 有问题？ |
|----------|---------------------|
| 单实验、单提供商 | 很小，仅重试阻塞 |
| 每实验独占槽位 | 否，阻塞被隔离 |
| 全部实验限流程度相同 | 很小，无其他工作 |
| 无限并发槽位 | 否，阻塞不降低容量 |

**我们的场景：** 多提供商的多个实验共享槽位，Advisor 明显更优。

---

<a id="abstraction-boundaries"></a>
## 抽象边界

<a id="the-four-abstractions"></a>
### 四种抽象

| 抽象 | 实现 | 职责 |
|-------------|----------------|----------------|
| **生产者** | Experiment | 生成工作、跟踪状态、管理重试 |
| **调度器** | Daemon | 分配槽位、保证公平 |
| **执行器** | Job | 执行工作、通过回调报告 |
| **外部系统** | LLM API | 施加限流 |

<a id="where-the-token-bucket-fits"></a>
### 令牌桶的位置

令牌桶是**外部约束的模型**，不负责决策，只回答是否有容量。

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   DAEMON                         EXPERIMENT                     │
│   ══════════                     ══════════                     │
│                                                                 │
│   "any work?"                                                   │
│       │                                                         │
│       └─────────────────────────▶  try_get_ready_job()          │
│                                         │                       │
│                                         ▼                       │
│                                  ┌──────────────┐               │
│                                  │ Short-circuit│               │
│                                  │ checks       │               │
│                                  └──────┬───────┘               │
│                                         │                       │
│                                         ▼                       │
│                                  ┌──────────────┐   ┌─────────┐ │
│                                  │ Token bucket │◀──│ SHARED  │ │
│                                  │ has capacity?│   │ (per    │ │
│                                  └──────┬───────┘   │ provider│ │
│                                         │           └─────────┘ │
│                                         ▼                       │
│       ◀──────────────────────────  Job | None                   │
│                                                                 │
│                                         ▲                       │
│   JOB EXECUTION                         │ feedback              │
│   ═════════════                         │ (success/429/error)   │
│                                         │                       │
│   job.execute() ──────▶ LLM API ────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

<a id="the-experiments-composite-interface"></a>
### Experiment 的组合接口

Experiment 封装组合问题：“现在是否有可分派工作？”

```python
class Experiment:
    def try_get_ready_job(self) -> Job | None:
        """Return a ready-to-execute Job, or None."""
        
        while self._has_pending_work():
            item = self._peek_next_item()
            
            # SHORT-CIRCUITS (no LLM call needed, no token consumed)
            if item.has_cached_result():
                self._dequeue_and_record_cached(item)
                continue
            
            if not item.is_valid():
                self._dequeue_and_record_invalid(item)
                continue
            
            # RATE LIMIT CHECK (needs LLM call)
            if not self._token_bucket.has_capacity():
                return None  # Has work, but can't proceed
            
            # DISPATCH
            self._token_bucket.consume()
            return self._create_job(self._dequeue(item))
        
        return None
```

这样 Daemon 很简单，只轮询询问实验，并分派拿到的 Job。

---

<a id="circuit-breaker-network-failure-handling"></a>
## 熔断器：网络故障处理

网络故障与限流不同：

| | 限流（429） | 网络故障 |
|--|------------------|-----------------|
| 提供商状态 | 可达但忙 | 不可达 |
| 错误类型 | HTTP 429 | 连接错误、超时、DNS |
| 令牌桶有用？ | 是，调整速率 | 否，不是速率问题 |
| 范围 | 逐提供商 | 逐提供商 |
| 恢复 | 令牌再生，自动恢复 | 需要网络恢复 |

<a id="the-problem-with-naive-retry"></a>
### 简单重试的问题

```
Network goes down
→ Job 1 fails (connection error) → retry
→ Job 2 fails (connection error) → retry
→ Job 3 fails (connection error) → retry
... 100 jobs all retrying into a dead network
→ Network recovers
→ 100 retries hit simultaneously (thundering herd)
```

<a id="solution-circuit-breaker-pattern"></a>
### 方案：熔断器模式

按提供商跟踪连续失败次数，达到 N 次后断开电路：

```python
class ProviderHealthMonitor:
    """Circuit breaker for network failures. Per-provider."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30,
    ):
        self._consecutive_failures = 0
        self._circuit_open = False
        self._cooldown_until: float | None = None
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
    
    def is_healthy(self) -> bool:
        """Check if provider is healthy (circuit closed or half-open)."""
        if not self._circuit_open:
            return True
        
        # Half-open: allow one attempt after cooldown
        if time.time() >= self._cooldown_until:
            return True
        
        return False
    
    def record_success(self) -> None:
        """Provider responded. Close circuit."""
        self._consecutive_failures = 0
        self._circuit_open = False
    
    def record_network_error(self) -> None:
        """Network failure. Maybe open circuit."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._failure_threshold:
            self._circuit_open = True
            self._cooldown_until = time.time() + self._cooldown_seconds
```

<a id="unified-rate-limiter"></a>
### 统一限流器

在一个组件中组合限流与熔断：

```python
class AdaptiveRateLimiter:
    """Handles both rate limits (429) and network failures."""
    
    def __init__(self, ...):
        # Rate limiting (token bucket)
        self._token_bucket = AdaptiveTokenBucket(...)
        
        # Circuit breaker (network health)
        self._health_monitor = ProviderHealthMonitor(...)
    
    def has_capacity(self) -> bool:
        """Check both rate capacity and network health."""
        # Circuit open? (network failure)
        if not self._health_monitor.is_healthy():
            return False
        
        # Rate limited? (429)
        return self._token_bucket.available_requests() > 1
    
    def consume(self) -> None:
        """Consume a token. Call after has_capacity() returns True."""
        self._token_bucket.tokens -= 1
    
    def on_success(self) -> None:
        """Request succeeded."""
        self._health_monitor.record_success()
    
    def on_rate_limit(self) -> None:
        """Got 429."""
        self._token_bucket.on_rate_limit_error(time.time())
    
    def on_network_error(self) -> None:
        """Network failure."""
        self._health_monitor.record_network_error()
```

<a id="flow-with-circuit-breaker"></a>
### 带熔断器的流程

```
Normal operation:
  Job succeeds → rate_limiter.on_success() → circuit stays closed

Network failure:
  Job 1 fails → rate_limiter.on_network_error() → failures=1
  Job 2 fails → rate_limiter.on_network_error() → failures=2
  ...
  Job 5 fails → rate_limiter.on_network_error() → failures=5 → CIRCUIT OPENS
  
  All experiments for this provider:
  try_get_ready_job() → rate_limiter.has_capacity() → False (circuit open)
  → No jobs dispatched, no wasted retries

After cooldown (30s):
  try_get_ready_job() → rate_limiter.has_capacity() → True (half-open)
  → One job dispatched (probe)
  
  If succeeds:
    rate_limiter.on_success() → circuit closes → normal operation
  
  If fails:
    rate_limiter.on_network_error() → circuit stays open → another cooldown
```

---

<a id="edge-cases"></a>
## 边界情况

全面分析边界情况及设计如何处理。

<a id="lifecycle-edge-cases"></a>
### 生命周期边界情况

<a id="1-graceful-shutdown"></a>
#### 1. 优雅关闭

**场景：** Daemon 收到 SIGTERM，在途 Job 怎么办？

**方案：** 带超时等待在途 Job，剩余交给崩溃恢复。

```python
async def run(self):
    try:
        while not self._shutdown_requested:
            await self._dispatch_loop_iteration()
    finally:
        # Wait for in-flight jobs (with timeout)
        try:
            await asyncio.wait_for(self._wait_for_in_flight_jobs(), timeout=30)
        except asyncio.TimeoutError:
            # Timed out. Let crash recovery handle remaining.
            pass
```

**设计可应对：** ✅ 作业完成或由崩溃恢复处理。

<a id="2-cancellation"></a>
#### 2. 取消

**场景：** 用户取消实验，在途 Job 怎么办？

**方案：** 两阶段取消：标志加丢弃结果。

```python
class Experiment:
    def cancel(self) -> None:
        self._cancelled = True
        # In-flight Jobs will complete, but results ignored


class Job:
    async def _handle_success(self, task_id, result):
        if self._experiment._cancelled:
            return  # Discard result
        await self._record_success(task_id, result)
```

**设计可应对：** ✅ 在途 Job 无害地完成。

<a id="3-crash-recovery"></a>
#### 3. 崩溃恢复

**场景：** 有在途作业时进程崩溃。

**方案：** 数据库用 `claimed_by` 和 `claimed_at` 跟踪，启动时检测过期认领。

```python
# On startup
stale_threshold = timedelta(minutes=10)
stale_experiments = await db.execute(
    """
    UPDATE experiment_execution_configs
    SET claimed_by = %(my_id)s, claimed_at = NOW()
    WHERE claimed_at < NOW() - %(threshold)s
    RETURNING id
""",
    {"my_id": replica_id, "threshold": stale_threshold},
)
```

**设计可应对：** ✅ Job 临时存在，任务状态在数据库。

<a id="resource-edge-cases"></a>
### 资源边界情况

<a id="4-memory-pressure-large-dataset"></a>
#### 4. 内存压力（大型数据集）

**场景：** 实验有 1M 任务，不宜全部加载进内存。

**方案：** Experiment 内分页。

```python
class Experiment:
    def __init__(self, batch_size=1000):
        self._task_buffer = deque()  # In-memory buffer
        self._db_offset = 0
        self._batch_size = batch_size
    
    def _ensure_buffer(self) -> None:
        if not self._task_buffer and self._has_more_in_db():
            tasks = self._load_batch(self._db_offset, self._batch_size)
            self._task_buffer.extend(tasks)
            self._db_offset += len(tasks)
```

**设计可应对：** ✅ 属于 Experiment 实现细节。

<a id="5-high-throughput-fast-tasks"></a>
#### 5. 高吞吐（快速任务）

**场景：** 每秒完成 1000 任务，数据库写入不堪重负。

**方案：** Experiment 内批量写入。

```python
class Experiment:
    def __init__(self):
        self._result_buffer = []
        self._flush_task: asyncio.Task | None = None
    
    async def _handle_success(self, task_id, result):
        self._result_buffer.append((task_id, result))
        if len(self._result_buffer) >= 100:
            await self._flush_results()
    
    async def _flush_results(self):
        if self._result_buffer:
            await self._db.bulk_insert(self._result_buffer)
            self._result_buffer.clear()
```

**设计可应对：** ✅ Experiment 控制批量策略。

<a id="6-db-write-failure"></a>
#### 6. 数据库写入失败

**场景：** 作业完成，但数据库不可用。

**方案：** 任务失败，由崩溃恢复重跑，幂等写入处理重复。

```python
async def _handle_success(self, task_id, result):
    try:
        await self._write_to_db(task_id, result)
    except DBError as e:
        # Treat as failure. Task will be recovered and re-run.
        # Idempotent writes ensure no duplicates.
        logger.error(f"DB write failed for {task_id}: {e}")
        self._requeue(task_id)
```

**设计可应对：** ✅ 崩溃恢复作为通用兜底。

<a id="error-edge-cases"></a>
### 错误边界情况

<a id="7-poison-pill-always-failing-task"></a>
#### 7. 毒丸（始终失败的任务）

**场景：** 某任务触发提供商缺陷，每次失败。

**方案：** 设置逐任务最大重试次数。

```python
class Experiment:
    MAX_RETRIES = 3
    
    def _handle_failure(self, task_id, error):
        task = self._get_task(task_id)
        task.retry_count += 1
        
        if task.retry_count >= self.MAX_RETRIES:
            self._record_permanent_failure(task_id, error)
        else:
            self._requeue_with_backoff(task)
```

**设计可应对：** ✅ Experiment 控制重试策略。

<a id="8-partial-stream-failure"></a>
#### 8. 部分流失败

**场景：** 流启动，部分数据块发给界面后连接失败。

**分析：**
- 界面看到 chunk1 → chunk2 → chunk3 → [error]。
- 重试时 chunk1 → chunk2 → chunk3 → chunk4 → [success]。
- 界面可能先看到部分流，重试时再看到完整流。

**方案：** 界面跟踪任务状态，显示重试中，并处理重复流。

**设计可应对：** ✅ 但界面需处理重试语义。

<a id="9-provider-returns-invalid-response"></a>
#### 9. 提供商返回无效响应

**场景：** 返回无效 JSON、意外格式等垃圾内容。

**方案：** Job 验证响应，报告失败。

```python
class Job:
    async def execute(self):
        try:
            raw_result = await self._call_llm()
            validated = self._validate_response(raw_result)
            await self.on_success(validated)
        except ValidationError as e:
            await self.on_failure(e)
```

**设计可应对：** ✅ 在 Job 内验证。

<a id="short-circuit-edge-cases"></a>
### 短路边界情况

<a id="10-cached-result"></a>
#### 10. 缓存结果

**场景：** 任务结果已有缓存，例如先前运行。

**方案：** 限流检查前短路。

```python
def try_get_ready_job(self) -> Job | None:
    while self._task_queue:
        task = self._peek()
        
        if task.has_cached_result():
            self._dequeue()
            self._record_success(task.id, task.cached_result)
            continue  # No Job created, no token consumed
        
        # ... rest of logic
```

**设计可应对：** ✅ 缓存结果不消耗令牌。

<a id="11-invalid-input"></a>
#### 11. 无效输入

**场景：** 任务输入格式错误。

**方案：** 限流检查前短路。

```python
if not task.is_valid():
    self._dequeue()
    self._record_failure(task.id, "Invalid input")
    continue  # No Job created, no token consumed
```

**设计可应对：** ✅ 限流检查前验证。

<a id="12-empty-dataset"></a>
#### 12. 空数据集

**场景：** 实验启动时有 0 个任务。

**方案：** 立即完成。

```python
def is_complete(self) -> bool:
    return (
        not self._task_queue
        and not self._eval_queue
        and not self._in_flight
        and not self._has_more_in_db()
    )
```

**设计可应对：** ✅ 空实验立即完成。

<a id="eval-edge-cases"></a>
### 评估边界情况

<a id="13-eval-after-task-failure"></a>
#### 13. 任务失败后评估

**场景：** 任务失败，还要运行评估吗？

**方案：** 通常不运行，由 Experiment 决定。

```python
def _handle_task_success(self, task_id, result):
    self._record_result(task_id, result)
    # Queue evals
    for evaluator in self._evaluators:
        self._eval_queue.append((task_id, evaluator, result))


def _handle_task_failure(self, task_id, error):
    self._record_failure(task_id, error)
    # NO evals queued
```

**设计可应对：** ✅ Experiment 控制评估策略。

<a id="14-eval-uses-different-provider"></a>
#### 14. 评估采用不同提供商

**场景：** 任务用 OpenAI，评估用 Anthropic。

**方案：** Experiment 按提供商检查正确令牌桶。

```python
def try_get_ready_job(self) -> Job | None:
    # Evals - check EVAL's provider bucket
    if self._eval_queue:
        eval_item = self._eval_queue[0]
        bucket = self._get_bucket(eval_item.evaluator.provider)
        if bucket.has_capacity():
            bucket.consume()
            return self._create_eval_job(self._eval_queue.popleft())
    
    # Tasks - check TASK's provider bucket
    if self._task_queue:
        task = self._task_queue[0]
        bucket = self._get_bucket(self._task_provider)
        if bucket.has_capacity():
            bucket.consume()
            return self._create_task_job(self._task_queue.popleft())
    
    return None
```

**设计可应对：** ✅ Experiment 管理多个令牌桶。

<a id="timing-edge-cases"></a>
### 时间边界情况

<a id="15-clock-skew-multi-replica"></a>
#### 15. 时钟偏差（多副本）

**场景：** 不同副本时钟不同。

**方案：** 使用数据库服务端时间，而非本地时钟。

```python
# Instead of
UPDATE ... SET claimed_at = %(local_time)s

# Use
UPDATE ... SET claimed_at = NOW()  -- DB timestamp
```

**设计可应对：** ✅ 实现细节。

<a id="16-very-slow-tasks"></a>
#### 16. 极慢任务

**场景：** 复杂推理耗时超过 5 分钟。

**方案：** 每个 Job 可配置超时。

```python
job = Job(
    ...,
    timeout=300,  # 5 minutes for complex tasks
    ...
)
```

**设计可应对：** ✅ 超时可配置。

<a id="concurrency-edge-cases"></a>
### 并发边界情况

<a id="17-lost-callback-bug"></a>
#### 17. 回调丢失（缺陷）

**场景：** Job 完成，回调却抛异常。

**方案：** 回调失败属于缺陷，应明确崩溃，由崩溃恢复处理后续。

```python
async def execute(self):
    try:
        result = await self._call_llm()
    except ...:
        # Error handling
    
    # Callbacks - bugs should crash loud
    await self.on_success(result)  # If this fails, propagate
```

**设计可应对：** ✅ 崩溃恢复作为通用兜底。

<a id="summary-table"></a>
### 汇总表

| 边界情况 | 类别 | 方案 | 设计可应对 |
|-----------|----------|----------|-----------------|
| 优雅关闭 | 生命周期 | 等待加崩溃恢复 | ✅ |
| 取消 | 生命周期 | 标志加丢弃结果 | ✅ |
| 崩溃恢复 | 生命周期 | 数据库 `claimed_by`/`claimed_at` | ✅ |
| 内存压力 | 资源 | 分页 | ✅ |
| 高吞吐 | 资源 | 批量写入 | ✅ |
| 数据库写入失败 | 资源 | 失败后重新执行 | ✅ |
| 毒丸 | 错误 | 最大重试限制 | ✅ |
| 部分流 | 错误 | 界面处理重试 | ✅ |
| 无效响应 | 错误 | Job 内验证 | ✅ |
| 缓存结果 | 短路 | 限流前检查 | ✅ |
| 无效输入 | 短路 | 限流前检查 | ✅ |
| 空数据集 | 短路 | 立即完成 | ✅ |
| 失败后评估 | 评估 | Experiment 决定 | ✅ |
| 不同提供商评估 | 评估 | 多令牌桶 | ✅ |
| 时钟偏差 | 时间 | 数据库时间 | ✅ |
| 慢任务 | 时间 | 可配置超时 | ✅ |
| 回调丢失 | 并发 | 明确崩溃加恢复 | ✅ |

**设计处理了全部边界情况。**

---

<a id="implementation-notes"></a>
## 实现说明

<a id="connecting-to-current-codebase"></a>
### 与现有代码衔接

可调整现有 `PlaygroundRateLimiter` 和 `PlaygroundClient`：

<a id="token-bucket-access"></a>
#### 令牌桶访问

令牌桶已存在于 `PlaygroundRateLimiter` 内部：

```python
# Current structure
class PlaygroundRateLimiter(RateLimiter, KeyedSingleton):
    def __init__(self, singleton_key, rate_limit_error):
        super().__init__(...)
        # Token bucket is in self._throttler


# Access for Experiment
class Experiment:
    def __init__(self, client: PlaygroundClient):
        self._token_bucket = client.rate_limiter._throttler
```

<a id="unwrapping-the-client"></a>
#### 解开客户端包装

当前通过 `_alimit` 包装 API 调用。Advisor 模式应使用原始客户端：

```python
# Current (Gatekeeper): Wrapped
async with self._client_factory() as client:
    throttled_create = self.rate_limiter._alimit(client.chat.completions.create)
    await throttled_create(...)

# New (Advisor): Raw
async with self._client_factory() as client:
    await client.chat.completions.create(...)  # No wrapper
```

<a id="provider-specific-error-handling"></a>
#### 提供商专用错误处理

Job 需要分类错误，客户端知道提供商专用错误类型：

```python
class Job:
    def __init__(
        self,
        ...,
        rate_limit_error: type[Exception],  # e.g., openai.RateLimitError
    ):
        self._rate_limit_error = rate_limit_error
    
    def is_rate_limit_error(self, e: Exception) -> bool:
        return isinstance(e, self._rate_limit_error)
```

也可在客户端规范化错误：

```python
class ProviderRateLimitError(Exception):
    """Unified rate limit error."""
    pass

class PlaygroundClient:
    async def chat_stream(self, ...):
        try:
            async for chunk in self._provider_client.stream(...):
                yield chunk
        except self._provider_rate_limit_error:
            raise ProviderRateLimitError()
```

<a id="instantiation-hierarchy"></a>
### 实例化层级

理解何时创建什么，以及哪些共享：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   SINGLETON (per rate-limit-key, shared across all experiments)             │
│   ═══════════════════════════════════════════════════════════               │
│                                                                             │
│   PlaygroundRateLimiter(key)  ◄─── Created once per key, lives forever      │
│       └── _throttler: AdaptiveTokenBucket                                   │
│                                                                             │
│   Keys:                                                                     │
│     "openai"                      ◄── All OpenAI models share               │
│     "anthropic"                   ◄── All Anthropic models share            │
│     "azure_openai:gpt-4-deploy"   ◄── Per deployment (see below)            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PER EXPERIMENT (created when experiment starts)                           │
│   ═══════════════════════════════════════════════                           │
│                                                                             │
│   PlaygroundClient  ◄─── Created via get_playground_client()                │
│       ├── _client_factory: Closure (captures credentials)                   │
│       ├── model_name, provider                                              │
│       └── rate_limiter: Reference to SINGLETON                              │
│                                                                             │
│   Experiment                                                                │
│       ├── _client: PlaygroundClient                                         │
│       ├── _token_bucket: Reference to singleton's _throttler                │
│       ├── _task_queue, _eval_queue, _retry_queue                            │
│       └── create_job() method                                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PER JOB (created on demand, transient)                                    │
│   ══════════════════════════════════════                                    │
│                                                                             │
│   Job  ◄─── Created by Experiment.try_get_ready_job()                       │
│       ├── task_id, input_data                                               │
│       ├── client_factory: Reference to client's factory                     │
│       ├── is_rate_limit_error: Callable                                     │
│       ├── callbacks: Closures over Experiment                               │
│       └── execute(): Creates raw client via factory                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PER EXECUTION (created and destroyed within Job.execute())                │
│   ════════════════════════════════════════════════════════════              │
│                                                                             │
│   Raw Provider Client (e.g., AsyncOpenAI)                                   │
│       └── Created fresh: async with client_factory() as client              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**要点：**
- **凭证**在实验启动时由 `client_factory` 闭包捕获一次。
- **令牌桶**由使用相同限流键的实验共享。
- **原始客户端**逐 Job 执行新建，避免过期连接。
- **Job** 成本低，仅引用共享资源，无重初始化。

<a id="flexible-rate-limiter-keying"></a>
### 灵活限流键

当前按提供商取键，对某些场景过粗：

| 提供商 | 限流范围 | 当前键 | 更佳键 |
|----------|------------------|-------------|------------|
| OpenAI | 逐组织 | `"openai"` | `"openai"` ✅ |
| Anthropic | 逐组织 | `"anthropic"` | `"anthropic"` ✅ |
| Azure OpenAI | **逐部署** | `"azure_openai"` ❌ | `("azure_openai", deployment)` |
| 部分 API | 逐 API 密钥 | `provider` | `(provider, api_key_hash)` |

**方案：** 创建客户端时确定键。

```python
def get_rate_limiter_key(provider: str, model_name: str) -> str:
    """Determine rate limiter key based on provider's rate limit scope."""
    if provider == "azure_openai":
        # Azure rate limits are per-deployment
        return f"azure_openai:{model_name}"
    # Most providers are per-organization
    return provider


# In PlaygroundClient.__init__
self.rate_limiter = PlaygroundRateLimiter(
    get_rate_limiter_key(provider, model_name),
    rate_limit_error,
)
```

**Experiment 创建 Job 并持有客户端，因此自动使用正确令牌桶。** Job 和 Daemon 无需改动。

<a id="no-polymorphic-workers"></a>
### 不使用多态工作器

命令模式关键优势：**分派变得极简单**。

**之前，多态位于分派器：**
```python
class Dispatcher:
    def dispatch(self, work: Work) -> None:
        if work.type == "openai_task":
            client = self._openai_client
            result = await client.chat(work.messages)
            await self._db.write_task_result(work.id, result)
        elif work.type == "anthropic_task":
            client = self._anthropic_client
            result = await client.messages(work.messages)
            await self._db.write_task_result(work.id, result)
        elif work.type == "eval":
            # Different logic...
```

**之后，多态位于命令：**
```python
# Dispatcher knows NOTHING
async def dispatch(job: Job) -> None:
    await job.execute()


# All the "knowing" is in the Job, set at creation time
job = Job(
    client_factory=openai_factory,  # Knows how to get client
    messages=messages,  # Knows what to send
    on_success=write_to_db,  # Knows what to do with result
    is_rate_limit_error=is_openai_429,  # Knows how to classify errors
)
```

**反转：**

```
BEFORE:                                 AFTER:
┌─────────────────────┐                 ┌─────────────────────┐
│   SMART DISPATCHER  │                 │   DUMB DISPATCHER   │
│                     │                 │                     │
│   if openai: ...    │                 │   job.execute()     │
│   if anthropic: ... │                 │                     │
│   if eval: ...      │                 │                     │
└─────────────────────┘                 └─────────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────┐                 ┌─────────────────────┐
│     DUMB WORK       │                 │     SMART JOB       │
│     (just data)     │                 │  (data + behavior   │
│                     │                 │   + callbacks)      │
└─────────────────────┘                 └─────────────────────┘
```

<a id="the-essence-of-command-pattern"></a>
### 命令模式的本质

命令模式的基本认识：

> **将方法调用变成对象。**

这样做后：

| 不用命令 | 使用命令 |
|-----------------|--------------|
| 调用方知道调用什么 | 只调用 `execute()` |
| 调用方知道参数 | 参数在对象中 |
| 调用方知道错误处理 | 错误处理在对象中 |
| 多态在调用方 | 多态在命令 |
| 紧耦合 | 完全解耦 |

**最深层优势：**

> **让被执行的事物更智能，让执行它的事物保持简单。**

Job 正是如此：
- **Job 了解全部**：工厂、错误类型、回调、超时。
- **分派器无需了解**：只调用 `execute()`。
- **无需**按提供商类型 switch。
- **无需多态分派**逻辑。
- 所有任务、评估、重试共用**统一接口**。

四人组列出这些优势：
- 用操作参数化对象 ✅，每个 Job 携带操作。
- 排队或记录请求 ✅，Job 可排队和记录。
- 解耦调用者与接收者 ✅，Daemon 不知道 Experiment。

<a id="naming-conventions"></a>
### 命名约定

自执行工作单元曾考虑以下名称：

| 名称 | 优点 | 缺点 |
|------|------|------|
| **Job** | 简单通用，如 Celery、Sidekiq | 泛化 |
| **Task** | 直观 | 与 `asyncio.Task` 冲突 |
| **Command** | 模式名，准确 | 抽象 |
| **Errand** | 直观，如工作器跑腿 | 非正式 |

**建议：** 使用 **Job**，简单且熟悉。

---

<a id="summary"></a>
## 汇总

<a id="design-principles-validated"></a>
### 已验证的设计原则

| 原则 | 状态 |
|-----------|--------|
| 端到端：智能在边缘 | ✅ Experiment 智能，Daemon 简单 |
| 约束分离 | ✅ 速率、并发、公平正交 |
| 状态局部性 | ✅ 状态在 Experiment/数据库，不在 Job |
| 工作守恒 | ✅ Advisor 不阻塞槽位 |
| 最小协调 | ✅ 仅共享限流协调 |
| 信息隐藏 | ✅ 组件只知道所需信息 |

<a id="edge-cases-handled"></a>
### 已处理边界情况

设计处理了全部 17 个已识别边界情况：
- 生命周期：关闭、取消、崩溃恢复。
- 资源：内存、吞吐、数据库故障。
- 错误：毒丸、部分流、无效响应。
- 短路：缓存、无效、空数据。
- 评估：失败、不同提供商。
- 时间：时钟偏差、慢任务。
- 并发：回调丢失。

**设计稳健，已可实施。**

---

<a id="provider-rate-limit-reference"></a>
## 提供商限流参考

本节记录不同 LLM 提供商的限流结构，为构造令牌桶键提供依据。

<a id="summary-table"></a>
### 汇总表

| 提供商 | 限流范围 | 区分模型？ | 建议令牌桶键 |
|----------|-----------------|-----------------|------------------------|
| **OpenAI** | 逐模型、逐组织 | **是** | `(api_key, base_url, model_name)` |
| **Azure OpenAI** | 逐部署 | **是** | `(endpoint, model_name)` |
| **AWS Bedrock** | 逐模型、逐区域 | **是** | `(region, model_name, credential)` |
| **Google Gemini** | 逐模型、逐项目 | **是** | `(api_key, model_name)` |
| **Anthropic** | 逐组织 | 否，共享池 | `(api_key)` |
| **xAI (Grok)** | 逐模型 | **是** | `(api_key, model_name)` |
| **Groq** | 逐模型、逐组织 | **是** | `(api_key, model_name)` |
| **DeepSeek** | 逐账号，基于队列 | 否 | `(api_key)` |
| **Qwen (Alibaba)** | 逐账号 | 可能 | `(api_key)` |
| **Ollama** | 本地，无限制 | 不适用 | `(base_url)` |
| **Fireworks** | 逐账号，RPM | 否 | `(api_key)` |
| **Mistral** | 逐组织 | 否 | `(api_key)` |
| **Together AI** | 逐账号 | 否 | `(api_key)` |
| **Lepton** | 逐账号，RPM | 否 | `(api_key)` |
| **Cerebras** | 逐模型 | **是** | `(api_key, model_name)` |
| **Replicate** | 逐账号 | 否 | `(api_key)` |
| **Baseten** | 逐账号 | 否 | `(api_key)` |

<a id="key-takeaways"></a>
### 要点

1. **需按模型分桶：** OpenAI、Azure、Bedrock、Google、xAI、Groq、Cerebras。
2. **组织级分桶足够：** Anthropic、DeepSeek、Qwen、Fireworks、Mistral、Together、Lepton、Replicate、Baseten。
3. **无需限流：** 本地 Ollama。

主要区别在于同账号或凭证下的不同模型是有**独立配额**，因此键需包含模型，还是**共享池**，只需 API 密钥。

<a id="provider-details"></a>
### 提供商详情

各提供商限流结构、层级和来源的详细信息，见备份文件 `backup/appendix-provider-rate-limits.md`。
