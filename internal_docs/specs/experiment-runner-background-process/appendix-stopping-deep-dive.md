<a id="appendix-stopping-experiments--a-deep-dive"></a>
# 附录：停止实验——深入解析

<a id="the-problem"></a>
## 问题

实验运行器在后台处理工作。某一时刻必须停止处理。问题是：**“停止”意味着什么，应该发生什么？**

考虑以下情况后，问题便不再简单：
- 请求停止时，可能仍有进行中的工作
- 可能有多个进程相互协调
- 不同情况需要不同清理行为
- 状态存在于多个位置（内存、数据库）

---

<a id="table-of-contents"></a>
## 目录

1. [状态模型](#state-model)
2. [参与者](#the-actors)
3. [关注事项](#the-concerns)
4. [约束](#the-constraints)
5. [推导设计](#deriving-the-design)
   - [权限模型](#the-authority-model)
   - [为何不在 stop_experiment() 中更新数据库？](#why-not-put-db-update-in-stop_experiment)
6. [多副本协调](#multi-replica-coordination)
7. [并发分析](#concurrency-analysis)
   - [竞争条件](#race-conditions)
   - [边界情况](#edge-cases)
   - [设计取舍](#design-trade-offs-considered-and-rejected)
8. [不变量与保证](#invariants-and-guarantees)
   - [安全性属性](#safety-properties)
   - [活性属性](#liveness-properties)
   - [无法保证的事项](#what-we-cannot-guarantee)
   - [形式模型概述](#formal-model-summary)
   - [稳健性评估](#robustness-assessment)
9. [已知限制与边界情况](#known-limitations-and-edge-cases)
   - [所有权转移时熔断器状态丢失](#limitation-1-circuit-breaker-state-lost-on-ownership-transfer)
   - [条件更新失败时错误记录丢失](#limitation-2-error-recording-lost-on-conditional-update-failure)
   - [初始化竞争窗口](#limitation-3-initialization-race-window)
10. [总结](#summary)
11. [实现验证清单](#implementation-verification-checklist)

---

<a id="state-model"></a>
## 状态模型

实验存在于两个位置：

| 位置 | 表示的内容 | 示例 |
|----------|-------------------|----------|
| **数据库** | 持久状态、事实来源 | `claimed_at`、`claimed_by`、任务进度 |
| **内存** | 活跃处理的运行时状态 | 队列、进行中的作业、标志 |

数据库状态决定实验*是否应该*运行。内存状态表示实验*正在*运行。

**关键认识**：两者可能不同步。数据库可能显示“未运行”，而内存仍有活跃作业。这是核心挑战。

---

<a id="the-actors"></a>
## 参与者

五类参与者可以停止实验，各有不同**意图**：

<a id="1-natural-completion"></a>
### 1. 自然完成

实验完成了所有工作。

- **意图**：处理已完成。释放所有权，使实验显示为完成。
- **运行器更新数据库？**是——清除 `claimed_by` 以释放所有权。

<a id="2-circuit-breaker"></a>
### 2. 熔断器

连续失败过多说明存在系统性问题（API 不可用、网络问题）。

- **意图**：停止浪费资源，记录错误，释放所有权。
- **运行器更新数据库？**是——清除 `claimed_by` 并记录错误。

<a id="3-user-stop"></a>
### 3. 用户停止

用户在 UI 点击“停止”。

- **意图**：用户希望暂停实验，之后应可恢复。
- **运行器更新数据库？**否——mutation 在调用运行器前已清除 `claimed_by`。

<a id="4-lost-ownership-heartbeat"></a>
### 4. 失去所有权（心跳）

数据库表示我们不再拥有此实验，其他人已停止或认领它。

- **意图**：停止处理不属于我们的工作。
- **运行器更新数据库？**否——引起所有权变化的一方已经更新。

<a id="5-graceful-shutdown"></a>
### 5. 优雅关闭

服务端正在关闭。

- **意图**：干净地停止处理。不释放所有权——希望重启时恢复。
- **运行器更新数据库？**否——有意保留所有权以便重启恢复。

<a id="summary-of-intentions"></a>
### 意图汇总

| 参与者 | 是否应释放所有权？ | 运行器更新数据库？ |
|-------|--------------------------|-------------------|
| 自然完成 | 是 | 是 |
| 熔断器 | 是（并记录错误） | 是 |
| 用户停止 | 是 | 否（mutation 已完成） |
| 失去所有权 | 不适用（已经失去） | 否 |
| 优雅关闭 | 否（希望恢复） | 否 |

---

<a id="the-concerns"></a>
## 关注事项

停止时必须处理多个事项：

<a id="1-in-flight-work"></a>
### 1. 进行中的工作

请求停止时作业可能正在运行，应该如何处理？

**方案 A：立即取消**
- 作业在执行中途被取消
- 风险：数据库写入中断 → 连接池损坏

**方案 B：保护关键操作**
- 数据库写入使用 `shield=True`，即使取消后也会完成
- 作业先完成数据库写入，再发现自身已停止
- 更安全，但意味着作业可能在调用停止*之后*完成

我们采用方案 B。这意味着：
- 停止会设置标志 (`_active = False`)
- 受保护操作完成
- 已完成作业检查标志，若已停止则丢弃结果

**时间线**：
```
T0: Job starts, begins LLM call
T1: stop() called, sets _active = False, cancels scope
T2: LLM call completes (was already in flight)
T3: Job's shielded DB write completes
T4: Job calls success handler
T5: Handler checks _active → False → discards result
```

<a id="2-queued-work"></a>
### 2. 排队中的工作

队列中的待处理工作应被放弃：
- 任务队列（等待运行的任务）
- 评估队列（等待运行的评估器）
- 重试堆（等待重试的失败作业）

**清空队列为何安全**：排队工作是临时状态，源自数据库状态。数据库通过 `experiment_run` 记录跟踪已完成的运行。恢复时，运行器查询数据库找出未完成工作并重新填充队列。工作不会永久丢失，只是从事实来源重建。

<a id="3-subscribers"></a>
### 3. 订阅者

UI 客户端订阅实验进度。停止时：
- 关闭流，让客户端知道应停止轮询
- 防止客户端无限等待

<a id="4-registry"></a>
### 4. 注册表

守护进程用注册表（`_experiments` 字典）跟踪运行中的实验。停止时：
- 从注册表移除，避免守护进程继续管理
- 允许实验对象被垃圾回收

<a id="5-database-ownership"></a>
### 5. 数据库所有权

数据库跟踪运行中实验的所有者：
- `claimed_at`：认领所有权的时间（NULL = 未运行）
- `claimed_by`：拥有它的副本

释放所有权意味着设置 `claimed_by = NULL`（以及 `claimed_at = NULL`）。

---

<a id="the-constraints"></a>
## 约束

<a id="constraint-1-shielded-operations-complete-after-stop"></a>
### 约束 1：受保护操作会在停止后完成

由于数据库写入受保护，作业可能在 `stop()` 后完成。代码必须处理此情况：

```python
def on_task_success(self, result):
    if not self._active:
        return  # Stopped, discard result
    # Process result...
```

<a id="constraint-2-db-updates-are-conditional"></a>
### 约束 2：数据库更新有条件

并非所有停止都应更新数据库：
- 失去所有权：数据库已由获得所有权的一方更新
- 优雅关闭：有意保留所有权以供重启

<a id="constraint-3-multi-replica-race-conditions"></a>
### 约束 3：多副本竞争条件

多个副本可能与同一实验交互：
- 副本 B 上的用户停止运行在副本 A 的实验
- 副本 A 的心跳必须检测到变化
- 副本 A 必须停止其内存中的处理

<a id="constraint-4-idempotency"></a>
### 约束 4：幂等性

停止可能被调用多次：
- 作业完成并调用停止
- 同时用户也点击停止
- 两条路径都必须安全

---

<a id="deriving-the-design"></a>
## 推导设计

根据这些约束，设计自然形成，但仍有微妙陷阱需要避免。

<a id="the-authority-model"></a>
### 权限模型

每次停止操作都有由调用方意图决定的**权限级别**：

| 权限 | 含义 | 数据库更新 |
|-----------|---------|-----------|
| `OVERRIDE` | “无论如何，停止此实验” | 无条件 |
| `RELEASE` | “我已完成，若仍归我则释放” | 有条件 |
| `CLEANUP` | “仅清理本地状态” | 无 |

关键认识：**权限来自调用方，而非检查状态**。

| 调用方 | 权限 | 原因 |
|--------|-----------|-----|
| 用户（通过 mutation） | `OVERRIDE` | 必须尊重用户意图 |
| 自然完成 | `RELEASE` | 应归我们所有；不归我们时也安全 |
| 熔断器 | `RELEASE` | 与完成相同 |
| 心跳 | `CLEANUP` | 数据库已反映现实 |
| 优雅关闭 | `CLEANUP` | 有意保留数据库状态 |

此模型解释了为何不能根据注册表状态推断数据库行为：注册表说明*本地有什么*，而非*有权做什么*。

<a id="why-not-put-db-update-in-stop_experiment"></a>
### 为何不在 stop_experiment() 中更新数据库？

直觉设计会让 `stop_experiment()` 处理所有事：内存清理和数据库更新。可以按注册表状态分支：

```python
# FLAWED DESIGN - DO NOT USE
def stop_experiment(self, exp_id):
    exp = self._experiments.pop(exp_id, None)
    if exp:
        exp.stop()
        # In registry → we own it → conditional update
        asyncio.create_task(self._update_db_if_owned(exp_id))
    else:
        # Not in registry → cross-replica stop → unconditional update
        asyncio.create_task(self._update_db(exp_id))
```

这看似优雅：若本地有实验则使用条件更新（安全）；若没有则使用无条件更新（用于跨副本）。

**但在一个关键场景中会失败：**

```
1. A runs experiment 123 (claimed_by='A', in A's registry)
2. B claims via orphan scan (claimed_by='B') — A doesn't know yet
3. User on A clicks Stop
4. A calls stop_experiment(123)
5. A finds exp in registry → conditional update
6. Conditional: WHERE claimed_by='A' → 0 rows (B owns it!)
7. B continues running — user's Stop request was silently ignored!
```

问题是：A 的注册表中有实验（过期状态），但数据库中已不再拥有它。基于注册表的分支选择条件更新，结果失败。

**核心问题**：注册表状态与数据库所有权可能不同步。注册表说明我们*以为*拥有什么，数据库说明*实际*拥有什么。用户发起停止时，需要无条件更新来处理过期注册表状态。

<a id="the-correct-approach-caller-decides-db-update"></a>
### 正确方法：由调用方决定数据库更新

不同参与者需要不同数据库更新策略：

| 参与者 | 数据库更新类型 | 原因 |
|-------|---------------|-----|
| **用户停止** | 无条件 | 即使注册表过期也必须生效 |
| **自然完成** | 有条件 | 应归我们所有，但不归我们时也安全 |
| **熔断器** | 有条件 | 与自然完成相同 |
| **心跳** | 无 | 数据库已由获得所有权者更新 |
| **优雅关闭** | 无 | 有意保留所有权 |

mutation 必须自行执行无条件数据库更新，因为：
1. 注册表过期时也必须生效（上述场景）
2. 必须跨副本生效（实验不在本地注册表）

<a id="principle-1-separate-in-memory-cleanup-from-db-update"></a>
### 原则 1：内存清理与数据库更新分离

```python
def stop(self) -> None:
    """In-memory cleanup only. No DB update."""
    if not self._active:
        return  # Idempotent
    self._active = False
    # Cancel scopes, clear queues, close subscribers
```

原因是不同参与者需要不同数据库行为，仅凭本地状态无法推断正确行为。

<a id="principle-2-mutation-handles-its-own-db-update"></a>
### 原则 2：mutation 自行处理数据库更新

```python
# In mutation
async def stop_experiment_mutation(...):
    # Unconditional update — works regardless of which replica owns it
    await session.execute(
        update(ExperimentExecutionConfig)
        .where(experiment_id == exp_id)
        .values(claimed_by=None, claimed_at=None)
    )
    # Then do in-memory cleanup
    experiment_runner.stop_experiment(exp_id)
```

为何无条件？因为：
- 跨副本：B 停止 A 上的实验不能使用条件更新（B 不拥有它）
- 过期注册表：A 停止自身实验时，可能已经失去所有权却不知道

<a id="principle-3-internal-completion-uses-conditional-update"></a>
### 原则 3：内部完成使用条件更新

```python
async def complete_experiment(self, exp_id: int, error: str | None = None):
    """Called by natural completion / circuit breaker."""
    stmt = (
        update(ExperimentExecutionConfig)
        .where(experiment_id == exp_id)
        .where(claimed_by == self._replica_id)  # Only if we still own it
        .values(claimed_at=None, ...)
    )
```

为何有条件？自然完成时，我们*应该*拥有实验（刚刚运行完它）。但在边界情况下（网络分区期间另一副本认领它），条件更新会安全地不做任何事，避免覆盖。

<a id="principle-4-consistent-cleanup-in-stop"></a>
### 原则 4：stop() 中保持一致清理

不论调用方是谁，`stop()` 始终执行相同清理：

```python
def stop(self) -> None:
    if not self._active:
        return
    self._active = False
    
    # Cancel in-flight jobs
    for scope in self._cancel_scopes.values():
        scope.cancel()
    
    # Clear queues (release memory, prevent processing)
    self._task_queue.clear()
    self._eval_queue.clear()
    self._retry_heap.clear()
    
    # Close subscribers (signal UI)
    for stream in self._subscribers:
        stream.close()
    self._subscribers.clear()
```

<a id="the-resulting-design"></a>
### 形成的设计

```python
class RunningExperiment:
    def stop(self) -> None:
        """In-memory cleanup. Called by all stop paths."""
        if not self._active:
            return  # Idempotent
        self._active = False
        # Cancel scopes, clear queues, close subscribers
        for scope in self._cancel_scopes.values():
            scope.cancel()
        self._task_queue.clear()
        self._eval_queue.clear()
        self._retry_heap.clear()
        for stream in self._subscribers:
            stream.close()
        self._subscribers.clear()
        # NOTE: Does NOT call on_done - caller handles DB updates


class ExperimentRunner:
    def stop_experiment(self, exp_id: int) -> bool:
        """In-memory only. Called by mutation and heartbeat."""
        exp = self._experiments.pop(exp_id, None)
        if exp:
            exp.stop()
            return True
        return False

    def _on_experiment_done(self, exp_id: int, *, last_error: str | None = None) -> None:
        """Callback when experiment completes naturally or circuit breaker trips.

        Removes from registry and enqueues a done event for the task group to process.
        Uses an anyio memory stream instead of asyncio.create_task so the DB write
        happens within the task group and shutdown waits for it to complete.
        """
        self._experiments.pop(exp_id, None)
        self._done_send.send_nowait((exp_id, last_error))

    async def _process_done_events(self) -> None:
        """Drain experiment-done events and perform DB writes within the task group."""
        async for exp_id, last_error in self._done_recv:
            await self._set_experiment_stopped(exp_id, last_error=last_error)

    async def _set_experiment_stopped(self, exp_id: int, *, last_error: str | None) -> None:
        """Update DB, but only if we still own it (conditional update)."""
        if last_error:
            logger.warning(f"Experiment {exp_id} stopping with error: {last_error}")
        status = "ERROR" if last_error else "COMPLETED"
        stmt = (
            update(ExperimentExecutionConfig)
            .where(experiment_id == exp_id)
            .where(claimed_by == self._replica_id)  # CONDITIONAL
            .values(claimed_at=None, claimed_by=None, status=status, last_error=last_error)
        )
        await session.execute(stmt)
```

<a id="why-this-design-works"></a>
### 此设计为何有效

| 场景 | 发生的行为 | 结果 |
|----------|--------------|--------|
| 自然完成 | `_on_experiment_done()` 执行条件更新 | 成功（我们拥有它） |
| 熔断器 | `_on_experiment_done(error)` 执行条件更新 | 成功（我们拥有它） |
| 用户停止（同一副本，我们拥有它） | mutation 执行无条件更新 | 成功 |
| 用户停止（同一副本，已失去所有权） | mutation 执行无条件更新 | 成功（覆盖过期状态） |
| 用户停止（跨副本） | mutation 执行无条件更新 | 成功 |
| 心跳（因用户停止失去所有权） | `stop_experiment()` 仅清理内存 | 数据库已为 NULL |
| 心跳（因孤儿扫描失去所有权） | `stop_experiment()` 仅清理内存 | 数据库有新所有者，不覆盖 |
| 优雅关闭 | `_graceful_shutdown()` 调用 `stop()` | 数据库不变，重启恢复 |

---

<a id="multi-replica-coordination"></a>
## 多副本协调

<a id="how-ownership-works"></a>
### 所有权的工作方式

数据库是所有权的事实来源：
- `claimed_by`：哪个副本拥有实验
- `claimed_at`：认领时间（NULL = 未运行）

每个副本有唯一 ID。心跳定期更新 `claimed_at` 以证明存活。

<a id="detecting-lost-ownership"></a>
### 检测所有权丢失

心跳执行：
```sql
UPDATE experiment_execution_config
SET claimed_at = now()
WHERE claimed_by = 'replica-A'
  AND experiment_id IN (list of our experiments)
RETURNING experiment_id
```

如果某实验未返回，表示失去所有权。可能原因：
1. 用户已停止它 (claimed_by = NULL)
2. 另一副本认领它 (claimed_by = 'replica-B')
3. 实验已删除

所有情况下数据库都已更新，只需清理内存。

<a id="cross-replica-user-stop"></a>
### 跨副本用户停止

```
Replica A: Running experiment 123 (claimed_by = "A")
Replica B: User clicks "Stop"

1. B's mutation: UPDATE SET claimed_at=NULL, claimed_by=NULL (unconditional)
2. B's stop_experiment(123): exp not in B's registry → in-memory no-op
3. A's heartbeat: UPDATE WHERE claimed_by="A" → 123 not returned
4. A's stop_experiment(123): removes from registry, calls exp.stop()
```

B 的 mutation 执行数据库更新（无条件）。A 仅清理内存。

<a id="same-replica-user-stop-with-stale-registry"></a>
### 注册表过期时同一副本上的用户停止

```
Replica A: Running experiment 123 (claimed_by = "A", in A's registry)
Replica B: Claims via orphan scan (claimed_by = "B") — A doesn't know
User on A: Clicks "Stop"

1. A's mutation: UPDATE SET claimed_at=NULL, claimed_by=NULL (unconditional)
   → Succeeds! B's claim is overridden.
2. A's stop_experiment(123): finds exp, calls exp.stop()
3. B's heartbeat: UPDATE WHERE claimed_by="B" → 0 rows (now NULL)
4. B's stop_experiment(123): removes from registry, calls exp.stop()
```

A 的无条件更新不受过期注册表状态影响。B 通过心跳检测变化。

<a id="delete-while-running-same-replica"></a>
### 运行期间删除（同一副本）

```
Replica A: Running experiment 123 (claimed_by = "A")
User on A: Clicks "Delete"

1. A's delete mutation: stop_experiment(123) → cancels in-flight jobs
2. A's delete mutation: DELETE FROM experiments WHERE id=123 (cascades)
3. No FK violations — in-flight jobs were cancelled before the row disappeared
```

删除 mutation 在 DELETE 前调用 `stop_experiment()`，避免并发写入 `experiment_runs` 导致外键约束违反。

<a id="delete-while-running-cross-replica"></a>
### 运行期间删除（跨副本）

```
Replica A: Running experiment 123 (claimed_by = "A")
Replica B: User clicks "Delete"

1. B's delete mutation: stop_experiment(123) → not in B's registry, no-op
2. B's delete mutation: DELETE FROM experiments WHERE id=123 (cascades)
3. A: In-flight jobs try to INSERT into experiment_runs → FK violation (parent deleted)
4. A: Circuit breaker trips after ~5 consecutive FK errors → exp.stop() + _on_done()
   OR
   A: Heartbeat detects lost ownership → exp.stop()
```

**恢复**：熔断器是快速路径（约数秒）。心跳是慢速路径（最多 HEARTBEAT_INTERVAL）。两种情况下，A 都清理内存，实验已不存在。

**外键错误会产生日志噪声，但无害**：每次失败 INSERT 都由作业错误处理器捕获、记录，并计入熔断器阈值。不会发生数据损坏——实验及其运行已通过 CASCADE 删除。

**为何不分布式停止？**可以增加运行器检查的数据库级“软删除”标志，但复杂度不值得。跨副本删除运行中实验很少发生，自愈路径（熔断器 + 心跳）可在数秒内解决，无需人工干预。

<a id="stale-heartbeat-orphan-scan"></a>
### 过期心跳（孤儿扫描）

```
Replica A: Running experiment 123 (claimed_by="A", claimed_at=T0)
Replica A: Network partition, heartbeat fails for 10+ minutes

1. Replica C's orphan scan finds stale claim (claimed_at < now - 10min)
2. C: UPDATE SET claimed_by="C", claimed_at=now
3. C: Starts running experiment 123
4. A: Network recovers, heartbeat runs
5. A's heartbeat: UPDATE WHERE claimed_by="A" → 0 rows (now owned by C)
6. A: Lost ownership, calls stop_experiment(123)
```

会短暂脑裂（双方都运行实验），但：
- A 通过心跳清理内存
- 重复工作通过 upsert 处理（幂等数据库写入）

<a id="why-internal-completion-uses-conditional-update"></a>
### 内部完成为何使用条件更新

自然完成和熔断器使用条件更新：
```sql
UPDATE SET claimed_by=NULL WHERE experiment_id=123 AND claimed_by='A'
```

为何有条件（而非像用户停止那样无条件）？

1. **应归我们所有**：若刚完成实验运行，我们应该仍拥有它
2. **安全后备**：另一副本若在网络分区期间认领它，条件更新不做任何事，避免覆盖对方正在运行的实验
3. **没有用户期待**：与用户停止不同，没有用户等待确认，静默不操作可以接受

如果 C 拥有它，更新 0 行。实验继续在 C 上运行，这才正确。

<a id="why-user-stop-uses-unconditional-update"></a>
### 用户停止为何使用无条件更新

用户停止时，mutation 使用无条件更新：
```sql
UPDATE SET claimed_by=NULL WHERE experiment_id=123
```

为何无条件（而非像内部完成那样有条件）？

1. **用户期待**：用户点击停止，期待实验停止
2. **注册表过期**：处理请求的副本可能有过期状态
3. **跨副本**：请求可能到达不拥有实验的副本

若采用条件更新，用户的停止请求可能静默失败。无条件更新保证实验停止。

---

<a id="concurrency-analysis"></a>
## 并发分析

本节从分布式系统角度分析潜在竞争条件和边界情况。

<a id="race-conditions"></a>
### 竞争条件

<a id="race-1-mutation-db-update-vs-heartbeat-on-same-replica"></a>
#### 竞争 1：同一副本的 mutation 数据库更新与心跳

```
1. Mutation: UPDATE SET claimed_by=NULL (succeeds)
2. Heartbeat runs before mutation calls stop_experiment()
3. Heartbeat: sees claimed_by=NULL, thinks "lost ownership"
4. Heartbeat: calls stop_experiment() — removes from registry
5. Mutation: calls stop_experiment() — not in registry, no-op
```

**结论**：安全。内存清理由心跳而非 mutation 完成，结果相同。

<a id="race-2-two-user-stops-on-different-replicas"></a>
#### 竞争 2：不同副本上的两次用户停止

```
1. User on A clicks Stop, User on B clicks Stop (simultaneously)
2. A's mutation: UPDATE SET claimed_by=NULL — succeeds
3. B's mutation: UPDATE SET claimed_by=NULL — succeeds (idempotent)
4. Both call stop_experiment() — one finds it, one doesn't
```

**结论**：安全。两个 mutation 均成功（幂等），内存清理执行一次。

**关于冷却期**：`cooldown_until` 字段实现冷却机制，防止停止与恢复之间快速*翻转*状态。每次用户发起状态变化时，将 `cooldown_until` 设为 `now + 5s`。下一次切换被阻止，直到 `cooldown_until <= now`。此检查在 UPDATE 的 WHERE 子句中原子执行（非独立检查），以防 TOCTOU 竞争。冷却期不影响重复操作——允许连续两次停止，因为是同一操作，而非翻转。

<a id="race-3-user-stop-vs-natural-completion"></a>
#### 竞争 3：用户停止与自然完成

```
1. Experiment almost done, user clicks Stop
2. Mutation: UPDATE SET claimed_by=NULL (unconditional)
3. Completion: UPDATE SET claimed_by=NULL WHERE claimed_by='A' (conditional)
```

**结论**：安全。两次更新都令 claimed_by=NULL，顺序无关。

<a id="race-4-heartbeat-vs-user-stop-different-replicas"></a>
#### 竞争 4：心跳与用户停止（不同副本）

```
1. User on B: UPDATE SET claimed_by=NULL
2. A's heartbeat: UPDATE SET claimed_at=now WHERE claimed_by='A'
```

若用户停止先完成，心跳的 WHERE 子句失败（claimed_by 为 NULL，而非 'A'）。若心跳先完成，用户停止将其覆盖为 NULL。

**结论**：安全。两种顺序都使实验停止。

<a id="race-5-orphan-scan-vs-user-stop"></a>
#### 竞争 5：孤儿扫描与用户停止

```
1. User on A clicks Stop
2. B does orphan scan, claims experiment (simultaneously)
```

**若 A 先完成**：
- A 的 mutation：`UPDATE SET claimed_by=NULL` 成功
- B 的孤儿认领：`UPDATE ... WHERE claimed_at < cutoff` → 0 行（A 已清除）
- 结果：实验停止

**若 B 先完成**：
- B 的认领：`UPDATE SET claimed_by='B', claimed_at=now` 成功
- A 的 mutation：`UPDATE SET claimed_by=NULL` 成功（无条件）
- B 的心跳：`WHERE claimed_by='B'` → 0 行（现为 NULL）
- B 检测到失去所有权，调用 `stop_experiment()`
- 结果：实验停止

**结论**：安全。用户停止的无条件更新确保实验停止，不受竞争结果影响。

<a id="edge-cases"></a>
### 边界情况

<a id="edge-case-1-db-update-succeeds-stop_experiment-crashes"></a>
#### 边界情况 1：数据库更新成功，stop_experiment() 崩溃

```
1. Mutation: UPDATE SET claimed_by=NULL (succeeds)
2. Server crashes before stop_experiment()
3. In-memory state "lost" (server crashed)
```

**结论**：安全。崩溃清除了内存状态。重启后实验不在注册表中。

<a id="edge-case-2-stop_experiment-succeeds-db-update-fails"></a>
#### 边界情况 2：stop_experiment() 成功，数据库更新失败

```
1. Mutation: DB update fails (network error)
2. But stop_experiment() already ran (in-memory cleaned)
3. DB still says claimed_by='A'
4. Orphan scan eventually claims it
5. Another replica continues the work
```

**结论**：**有问题**。用户点击停止，但实验在其他地方继续，形成静默失败。

**缓解**：设计规定 mutation **先**更新数据库，再调用 stop_experiment()。数据库失败时向用户返回错误，不清理内存。

<a id="edge-case-3-heartbeat-latency-window"></a>
#### 边界情况 3：心跳延迟窗口

从用户停止（数据库更新）到心跳检测之间，原副本继续处理，产生“浪费”的工作。

**结论**：可接受。作业本就需要数秒，心跳频繁运行。浪费工作有界且幂等（upsert 处理重复）。

<a id="design-trade-offs-considered-and-rejected"></a>
### 设计取舍（已考虑并否决）

<a id="fencing-tokens-for-job-writes"></a>
#### 作业写入的隔离令牌

**场景**：过期副本失去所有权后仍可写入作业结果。

```
1. A claims experiment (claimed_by='A')
2. A's heartbeat fails, B claims (claimed_by='B')
3. A's network recovers, A thinks it still owns it
4. A completes a job, writes result to DB
5. Result is written even though A is stale
```

**当前实现**：作业写入采用 upsert，唯一约束为 `(experiment_id, dataset_example_id, repetition_number)`。过期副本的重复写入只是覆盖，不会损坏数据，只产生冗余工作。

**考虑的替代方案**：为作业结果写入添加 `claimed_by` 检查（隔离）：

```python
# Fencing approach (NOT implemented)
result = await session.execute(
    insert(ExperimentRun)
    .values(...)
    .on_conflict_do_update(...)
    .where(
        select(ExperimentExecutionConfig.claimed_by)
        .where(experiment_id == exp_id)
        .scalar_subquery()
        == self._replica_id
    )
)
if result.rowcount == 0:
    # We lost ownership, discard result
    return
```

**否决原因**：
1. upsert 已防止数据损坏
2. 重复工作有界（心跳间隔）
3. 隔离增加复杂度，收益极小
4. 作业写入需要额外数据库往返或子查询

**结论**：当前基于 upsert 的方法足够，接受此取舍。

---

<a id="invariants-and-guarantees"></a>
## 不变量与保证

本节形式化分析停止设计的安全性与活性属性。

<a id="safety-properties"></a>
### 安全性属性

安全性属性保证“坏事不会发生”。

<a id="s1-user-stop-completeness"></a>
#### S1：用户停止的完整性

> **若 mutation 的数据库更新成功，实验最终会在所有副本上停止。**

**证明**：
1. mutation 执行：`UPDATE SET claimed_by=NULL WHERE experiment_id=X`
2. 更新无条件，不论当前所有者是谁都成功
3. 对运行实验 X 的任意副本 R：
   - R 的心跳执行：`UPDATE SET claimed_at=now WHERE claimed_by='R' AND experiment_id IN (...)`
   - 因为 `claimed_by=NULL`（不是 'R'），不返回实验 X
   - R 检测到失去所有权，调用 `stop_experiment(X)`
   - R 从注册表移除 X，调用 `exp.stop()`
4. 因此所有副本最终停止处理 X ∎

**依赖**：心跳定期运行（活性假设）

<a id="s2-no-silent-user-stop-failure"></a>
#### S2：用户停止不会静默失败

> **若 mutation 向用户返回成功，数据库中的实验已停止。**

**证明**：
1. mutation 返回前执行数据库更新
2. 数据库更新失败时，mutation 返回错误（而非成功）
3. mutation 返回成功则说明数据库更新成功
4. 因此数据库中 `claimed_by=NULL` ∎

**推论**：结合 S1，用户收到成功表示实验将停止。

<a id="s3-internal-completion-doesnt-clobber"></a>
#### S3：内部完成不会覆盖他人所有权

> **副本 A 的自然完成/熔断器不能停止副本 B 拥有的实验。**

**证明**：
1. 内部完成使用条件更新：
   `UPDATE SET claimed_by=NULL WHERE experiment_id=X AND claimed_by='A'`
2. 若 B 拥有 X，则 `claimed_by='B'`（而非 'A'）
3. WHERE 子句失败，更新 0 行
4. B 的实验不受影响继续运行 ∎

**意义**：网络分区时 A 可能以为拥有 X，实际却归 B。此保证防止 A 覆盖 B。

<a id="s4-idempotent-stop-operations"></a>
#### S4：停止操作幂等

> **多次调用 `stop()`、`stop_experiment()` 或 `complete_experiment()` 与调用一次效果相同。**

**`stop()` 的证明**：
1. 第一次调用：`_active` 为 True → 设为 False，执行清理
2. 后续调用：`_active` 为 False → 提前返回，不操作 ∎

**`stop_experiment()` 的证明**：
1. 第一次调用：`_experiments.pop(exp_id)` 返回实验 → 清理
2. 后续调用：`_experiments.pop(exp_id)` 返回 None → 不操作 ∎

**`complete_experiment()` 的证明**：
1. 调用 `stop_experiment()`（如上所证具备幂等性）
2. 数据库更新幂等（将 NULL 设为 NULL 没有效果）∎

<a id="s5-graceful-shutdown-preserves-resumability"></a>
#### S5：优雅关闭保留可恢复性

> **优雅关闭后，实验可在重启时恢复。**

**证明**：
1. 优雅关闭仅调用 `exp.stop()`（不更新数据库）
2. `claimed_by` 保持为本副本 ID
3. `claimed_at` 变为过期（没有心跳）
4. 重启时孤儿扫描发现过期认领
5. 同一或不同副本可认领并恢复 ∎

**注意**：这是有意行为——希望实验在重启后继续存在。

**快速重启的注意事项**：若副本在 `STALE_CLAIM_TIMEOUT` 内重启，认领尚未过期，孤儿扫描找不到它。实验需等待认领过期（最坏延迟为 `STALE_CLAIM_TIMEOUT`）。这是活性取舍：优先安全（不急于回收），而非立即恢复。

<a id="liveness-properties"></a>
### 活性属性

活性属性保证“好事最终会发生”。

<a id="l1-eventual-in-memory-cleanup"></a>
#### L1：最终完成内存清理

> **若数据库中 `claimed_by=NULL`，最终所有副本的注册表都不再包含该实验。**

**证明**：
1. 令 t₀ 为 `claimed_by` 变为 NULL 的时刻
2. 令 T 为心跳间隔
3. 对注册表中有此实验的任意副本 R：
   - R 下次心跳发生于某个 t₁ ≤ t₀ + T
   - 心跳检测到所有权丢失 (claimed_by ≠ 'R')
   - R 调用 `stop_experiment()`，从注册表移除
4. 到 t₀ + T 时，所有副本均已清理 ∎

**上界**：心跳间隔（通常 30-60 秒）

<a id="l2-orphan-recovery"></a>
#### L2：孤儿恢复

> **若副本在拥有实验时崩溃，另一副本最终会认领它。**

**证明**：
1. 令 t₀ 为副本 A 崩溃时刻
2. A 的 `claimed_at` 停止更新（无心跳）
3. 令 S 为过期阈值，O 为孤儿扫描间隔
4. 在某个 t₁ ≤ t₀ + S + O：
   - 孤儿扫描发现 `claimed_at < now - S`
   - 扫描认领实验：`UPDATE SET claimed_by='B', claimed_at=now`
5. 实验在副本 B 恢复 ∎

**上界**：过期阈值 + 孤儿扫描间隔（通常 10-15 分钟）

<a id="l3-stop-propagation"></a>
#### L3：停止传播

> **用户停止会在有界时间内反映到所有副本。**

**证明**：由 S1 + L1 得出。
1. 根据 S1，数据库立即更新
2. 根据 L1，内存清理在心跳间隔内完成
3. 总传播时间 ≤ 心跳间隔 ∎

<a id="what-we-cannot-guarantee"></a>
### 无法保证的事项

<a id="no-duplicate-work-during-transitions"></a>
#### 转移期间没有重复工作

> **所有权转移期间，两个副本可能短暂处理相同工作。**

**场景**：
```
1. A owns experiment, processing job J
2. A's heartbeat fails (network partition)
3. B claims experiment via orphan scan
4. A's network recovers, A still has job J in flight
5. Both A and B may complete job J
```

**为何无法防止**：没有分布式锁或隔离令牌，就无法阻止进行中的工作完成。

**缓解**：幂等写入（upsert）确保重复完成不会损坏数据：
```sql
INSERT INTO experiment_runs (...)
ON CONFLICT (experiment_id, repetition_number, ...) 
DO UPDATE SET ...
```

<a id="instantaneous-stop"></a>
#### 立即停止

> **用户停止无法立即中止全部进行中的工作。**

**原因**：
1. 基于心跳的检测有延迟（L1 上界）
2. 受保护操作即使在取消后也会完成
3. 跨副本通信是异步的

**缓解**：对该用例可接受。作业生命周期短，结果幂等。

<a id="formal-model-summary"></a>
### 形式模型概述

| 属性 | 类型 | 保证 | 上界 |
|----------|------|-----------|-------|
| S1：用户停止完整性 | 安全性 | 停止到达所有副本 | - |
| S2：无静默失败 | 安全性 | 成功 = 数据库已更新 | - |
| S3：不覆盖他人 | 安全性 | 条件更新提供保护 | - |
| S4：幂等 | 安全性 | 多次调用 = 一次调用 | - |
| S5：可恢复性 | 安全性 | 优雅关闭保留恢复能力 | - |
| L1：内存清理 | 活性 | 最终清理 | 心跳间隔 |
| L2：孤儿恢复 | 活性 | 最终认领 | 过期阈值 + 扫描间隔 |
| L3：停止传播 | 活性 | 最终传播 | 心跳间隔 |

<a id="assumptions"></a>
### 假设

上述保证依赖：

1. **数据库可用性**：PostgreSQL 可用且一致
2. **心跳活性**：心跳任务定期运行，没有永久失败
3. **孤儿扫描活性**：孤儿扫描定期运行
4. **网络最终连通**：分区是临时而非永久的
5. **异常安全的清理操作**：`CancelScope.cancel()` 和 `MemoryObjectSendStream.close()` 不抛出异常。这些 anyio 原语按安全使用设计；若抛出异常，`stop()` 将仅完成部分清理。

任何假设被违反时，活性属性可能不成立（但安全性属性仍成立）。

---

<a id="robustness-assessment"></a>
### 稳健性评估

| 关注事项 | 状态 | 说明 |
|---------|--------|-------|
| 基本竞争条件 | **已处理** | 所有已识别竞争均安全 |
| 崩溃恢复 | **已处理** | 心跳/孤儿扫描提供最终一致性 |
| 用户停止静默失败 | **已缓解** | 先更新数据库，再清理内存 |
| 过期副本写入 | **已处理** | upsert 防止损坏；重复工作有界 |
| 抽象约束 | **较弱** | 依靠概念，而非类型强制 |

**总体**：设计适合该用例。边界情况要么以安全方式失败，要么由现有机制（心跳、孤儿扫描、幂等写入）缓解。

---

<a id="known-limitations-and-edge-cases"></a>
## 已知限制与边界情况

本节记录按设计未缓解或需要在实现中显式处理的微妙问题。

<a id="limitation-1-circuit-breaker-state-lost-on-ownership-transfer"></a>
### 限制 1：所有权转移时熔断器状态丢失

副本失去所有权时（例如网络分区 → 孤儿扫描），新副本从全新的熔断计数器开始：

```
1. A runs experiment, accumulates 3 failures (threshold is 5)
2. A's heartbeat fails, B claims via orphan scan
3. B starts fresh with 0 failures
4. Systemic issue persists → B takes another 5 failures to trigger circuit breaker
```

**影响**：对于系统性问题（API Key 错误、速率限制），这实际上使熔断前浪费的工作翻倍。

**为何未缓解**：
- 将失败次数持久化到数据库会增加复杂度和往返
- 此场景需要系统性失败与所有权转移同时发生
- 额外浪费工作有界（最多阈值的 2 倍）

**未来可能的缓解**：在 `experiment_execution_config` 中保存最近失败时间戳。新所有者可检查最近运行是否失败，并从较高计数开始。

**结论**：可接受的取舍。系统性失败相对少见，有界的额外工作优于分布式熔断状态的复杂度。

<a id="limitation-2-error-recording-lost-on-conditional-update-failure"></a>
### 限制 2：条件更新失败时错误记录丢失

调用 `complete_experiment()` 并携带错误，但条件更新失败（已失去所有权）时，错误消息被丢弃：

```python
async def complete_experiment(self, exp_id: int, error: str | None = None):
    self.stop_experiment(exp_id)
    await self._update_db_if_owned(exp_id, error)  # May affect 0 rows — error lost
```

**场景**：
```
1. A's circuit breaker fires with error "Rate limit exceeded"
2. B has already claimed the experiment (A doesn't know yet)
3. A's conditional update: WHERE claimed_by='A' → 0 rows
4. Error "Rate limit exceeded" is never recorded
5. B continues, eventually hits the same issue
```

**影响**：调试可能更困难——系统性错误首次出现时未被记录。

**为何未缓解**：
- 替代方案（无条件记录错误）可能覆盖 B 正在运行的实验
- B 最终也会遇到并记录相同错误
- 本地日志为运维人员提供审计轨迹

**实现说明**：实现应在尝试条件更新前先将错误记录到本地：

```python
async def complete_experiment(self, exp_id: int, error: str | None = None):
    if error:
        logger.warning(f"Experiment {exp_id} stopping with error: {error}")
    self.stop_experiment(exp_id)
    await self._update_db_if_owned(exp_id, error)
```

**结论**：可接受。错误信息可从日志获得；条件更新正确地优先避免覆盖活跃实验。

<a id="limitation-3-initialization-race-window"></a>
### 限制 3：初始化竞争窗口

设计假定实验停止时处于稳定状态。初始化期间存在竞争：

```
1. User starts experiment 123
2. Initialization begins (loading dataset, setting up queues)
3. User immediately clicks Stop
4. stop() is called mid-initialization
```

**建议的实现不变量**：初始化代码应在关键位置检查 `_active`：

```python
async def initialize(self):
    self._active = True  # Set early
    
    # Load dataset
    dataset = await self._load_dataset()
    if not self._active:
        return  # User stopped during load
    
    # Set up queues
    await self._setup_queues(dataset)
    if not self._active:
        return  # User stopped during setup
    
    # Begin processing
    await self._start_workers()
```

**当前实现状态**：尚未实现。当前实现不在初始化期间检查 `_active`。这意味着：
- 用户无法在初始化期间有效停止实验
- 停止仅在初始化完成后生效
- 因为初始化通常很快，因此可接受

**结论**：低优先级改进。`_active` 标志提供了机制；在初始化期间增加检查可提高响应速度，但并非关键。

<a id="summary-of-limitations"></a>
### 限制汇总

| 限制 | 严重程度 | 状态 |
|------------|----------|--------|
| 熔断器状态丢失 | 中 | 接受有界额外工作；记录日志以供调试 |
| 错误记录丢失 | 低 | 条件更新前先记录本地日志 |
| 初始化竞争窗口 | 低 | 未实现；停止在初始化后生效 |
| 初始化竞争 | 低 | 在初始化检查点检查 `_active` |

考虑分布式协调复杂度，这些限制属于可接受取舍。设计优先保证正确性（无数据损坏、不覆盖他人），而非完美的错误可见性。

---

<a id="summary"></a>
## 总结

<a id="the-core-insight"></a>
### 核心认识

停止包含两个正交维度：
1. **内存清理**——是否有本地状态需要清理？
2. **数据库更新**——调用方有什么权限？

关键认识：**权限来自调用方，而非检查状态**。

| 权限 | 调用方 | 数据库更新 |
|-----------|--------|-----------|
| `OVERRIDE` | 用户停止 | 无条件 |
| `RELEASE` | 自然完成、熔断器 | 有条件 |
| `CLEANUP` | 心跳、优雅关闭 | 无 |

注册表状态说明是否需要本地清理，不能说明应执行什么数据库操作——后者由调用方意图决定。

<a id="method-responsibilities"></a>
### 方法职责

| 方法 | 执行的工作 | 调用方 |
|--------|--------------|--------------|
| `stop()` | 内存清理 | 所有参与者 |
| `stop_experiment()` | 注册表移除 + `stop()` | mutation、心跳 |
| `_on_experiment_done()` | 注册表移除 + 条件数据库更新 | 自然完成、熔断器 |
| `_set_experiment_stopped()` | 条件数据库更新 | `_on_experiment_done()`（内部） |
| `_graceful_shutdown()` | 对所有实验调用 `stop()` | 服务端关闭 |
| mutation | 无条件数据库更新 + `stop_experiment()` | 用户停止 |

<a id="actor-summary"></a>
### 参与者汇总

| 参与者 | 内存操作 | 数据库更新 | 原因 |
|-------|-----------|-----------|-----|
| 自然完成 | `_on_experiment_done()` | 有条件 | 应归我们所有；不归我们时也安全 |
| 熔断器 | `_on_experiment_done(error)` | 有条件 | 同上 |
| 用户停止 | mutation + `stop_experiment()` | 无条件 | 注册表过期也必须有效 |
| 失去所有权 | `stop_experiment()` | 无 | 数据库已由相应方更新 |
| 优雅关闭 | `stop()` | 无 | 希望重启时恢复 |

<a id="key-properties"></a>
### 关键属性

1. **幂等**：所有方法均可安全重复调用
2. **容忍过期状态**：即使注册表与数据库不同步，用户停止仍有效
3. **竞争安全**：内部完成不会覆盖另一副本的认领
4. **一致清理**：`stop()` 始终执行相同内存清理
5. **职责明确**：mutation 负责用户停止的数据库语义，运行器负责内部完成

<a id="why-not-unify-db-updates-in-stop_experiment"></a>
### 为何不在 stop_experiment() 中统一数据库更新？

曾考虑让 `stop_experiment()` 使用分支处理全部数据库更新：
- 在注册表中 → 条件更新
- 不在注册表中 → 无条件更新

当用户在注册表过期的副本点击停止时（实验在注册表中，但已失去所有权），此方式失败。条件更新静默失败，实验继续在另一副本运行。

解决方式是：mutation 自行执行无条件更新，再调用 `stop_experiment()` 清理内存。这保证用户停止始终有效。

---

<a id="implementation-verification-checklist"></a>
## 实现验证清单

使用本节验证实现是否正确遵循设计。每项都应对照实际代码检查。

<a id="core-method-structure"></a>
### 核心方法结构

- [x] **存在 `RunningExperiment.stop()`**，仅清理内存（不更新数据库）
- [x] **`stop()` 有幂等保护**：`_active` 已为 False 时提前返回
- [x] **`stop()` 设置 `_active = False`**，早于任何清理
- [x] **`stop()` 取消所有进行中作业**，通过取消作用域实现
- [x] **`stop()` 清空所有队列**：任务队列、评估队列、重试堆
- [x] **`stop()` 关闭所有订阅流**，使 UI 客户端收到 EndOfStream
- [x] **`stop()` 不调用 `on_done()`** 或任何完成回调

- [x] **存在 `ExperimentRunner.stop_experiment(exp_id)`**，执行注册表移除 + `stop()`
- [x] **`stop_experiment()` 使用 `pop()`** 原子移除注册表条目（而非先 `get()` 再 `del`）
- [x] **`stop_experiment()` 不更新数据库**——只操作内存

- [x] **存在 `ExperimentRunner._on_experiment_done(exp_id, last_error)`**，用于内部完成
- [x] **`_on_experiment_done()` 移除注册表条目**，通过 `pop()`
- [x] **`_on_experiment_done()` 调度 `_set_experiment_stopped()`**，进行异步条件数据库更新
- [x] **`_set_experiment_stopped()` 使用条件数据库更新**：`WHERE claimed_by = self._replica_id`

<a id="mutation-user-stop"></a>
### mutation（用户停止）

- [x] **停止 mutation 执行无条件数据库更新**：`UPDATE SET claimed_by=NULL WHERE experiment_id=X AND claimed_at IS NOT NULL`（没有 `claimed_by` 条件）
- [x] **数据库更新先于 `stop_experiment()`**：数据库失败时返回错误，不清理内存
- [x] **mutation 调用 `stop_experiment()`**，在数据库更新成功后进行本地内存清理

<a id="heartbeat"></a>
### 心跳

- [x] **心跳检测所有权丢失**，依据实验未从 UPDATE RETURNING 返回
- [x] **心跳内联调用 `exp.stop()`**（直接使用 `pop()` + `stop()`，而非 `stop_experiment()`）
- [x] **心跳不为失去的实验更新数据库**——仅清理内存

<a id="graceful-shutdown"></a>
### 优雅关闭

- [x] **`_graceful_shutdown()` 调用 `stop()`**，覆盖所有实验
- [x] **优雅关闭不更新数据库**——保留所有权以供恢复
- [x] **优雅关闭等待受保护操作**，超时后才强制取消

<a id="in-flight-job-handling"></a>
### 进行中作业处理

- [x] **数据库写入使用 `shield=True`**（通过 `anyio.fail_after(timeout, shield=True)`）
- [x] **作业完成时检查 `_active`**，早于结果处理
- [x] **`_active` 为 False 时作业丢弃结果**（实验已停止）

<a id="idempotency"></a>
### 幂等性

- [x] **`stop()` 幂等**：多次调用与一次效果相同（通过 `_active` 保护）
- [x] **`stop_experiment()` 幂等**：后续调用中 `pop()` 返回 None
- [x] **`_set_experiment_stopped()` 幂等**：条件更新可安全重复

<a id="error-handling"></a>
### 错误处理

- [x] **熔断器调用 `on_done(last_error=...)`**，传入错误消息
- [x] **错误先记录到本地日志**，再执行条件数据库更新（防止更新失败）

<a id="multi-replica-safety"></a>
### 多副本安全

- [x] **条件更新使用 `claimed_by = self._replica_id`**（不硬编码）
- [x] **无条件更新（用户停止）跨副本有效**——没有 `claimed_by` 条件
- [x] **作业写入使用 upsert**，处理过期副本产生的重复工作

<a id="subscriber-cleanup"></a>
### 订阅者清理

- [x] **`stop()` 关闭订阅流**（不只是清空列表）
- [x] **流使用 `.close()` 方法关闭** (MemoryObjectSendStream)
- [x] **关闭后清空订阅者列表**，允许垃圾回收

<a id="initialization-safety"></a>
### 初始化安全

- [x] **`_active` 在 `__init__` 中设为 True**
- [ ] **初始化在关键位置检查 `_active`**（异步操作之后）——*未实现*
- [ ] **初始化提前退出**，若 `_active` 在初始化中途变为 False——*未实现*

注意：初始化安全检查目前未实现。这意味着用户无法在初始化期间停止实验，是下文记录的已知限制。

<a id="logging"></a>
### 日志

- [x] **`stop()` 被调用时记录日志**（帮助调试原因不明的停止）
- [x] **停止原因可追溯**（记录调用栈）
- [x] **记录丢弃的工作**：待处理任务、评估、重试、进行中数量

---

<a id="verification-commands"></a>
### 验证命令

要验证实现，AI 助手应：

1. **读取停止相关方法**：
   ```
   - RunningExperiment.stop()
   - ExperimentRunner.stop_experiment()
   - ExperimentRunner._on_experiment_done()
   - ExperimentRunner._set_experiment_stopped()
   - ExperimentRunner._graceful_shutdown()
   - The stop mutation in experiment_mutations.py
   - Heartbeat's lost-ownership handling (_heartbeat_loop)
   ```

2. **搜索潜在违反情况**：
   ```
   - Any DB update in stop() or stop_experiment()? (Should be none)
   - Any unconditional DB update in _set_experiment_stopped()? (Should be conditional)
   - Any conditional DB update in stop mutation? (Should be unconditional w.r.t. claimed_by)
   - Any on_done() call in stop()? (Should be none)
   ```

3. **追踪每类参与者的路径**：
   - 自然完成 → `_on_experiment_done()` → `_set_experiment_stopped()` → 条件数据库更新
   - 熔断器 → `_on_experiment_done(error)` → `_set_experiment_stopped()` → 条件数据库更新
   - 用户停止 → mutation（无条件数据库更新）→ `stop_experiment()`
   - 失去所有权 → 心跳检测 → `pop()` + `stop()` → 不更新数据库
   - 优雅关闭 → `_graceful_shutdown()` → 对全部调用 `stop()` → 不更新数据库

4. **验证不变量成立**：
   - S1：用户停止的数据库更新无条件（针对 claimed_by）
   - S3：内部完成的数据库更新有条件 (`WHERE claimed_by = self._replica_id`)
   - S4：所有停止方法具备幂等性（保护或原子操作）
   - S5：优雅关闭保留数据库状态
