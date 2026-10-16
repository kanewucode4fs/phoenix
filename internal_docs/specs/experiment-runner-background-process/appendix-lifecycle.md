<a id="appendix-experiment-lifecycle"></a>
# 附录：实验生命周期

> 本文概述实验生命周期管理。包含证明和边界情况的形式化分析见下方链接的深入分析。

---

<a id="overview"></a>
## 概述

实验有三个生命周期阶段：

| 阶段 | 触发方式 | 结果 |
|-------|---------|--------|
| **启动** | 用户点击运行，或孤立扫描恢复 | 实验认领所有权，开始处理 |
| **停止** | 用户点击停止、完成、熔断器触发或崩溃 | 实验释放所有权，停止处理 |
| **恢复** | 用户点击恢复，或孤立扫描恢复 | 与启动相同（不恢复队列状态） |

---

<a id="state-machine"></a>
## 状态机

```
                    ┌─────────────┐
                    │   CREATED   │
                    │ claimed_at  │
                    │   = NULL    │
                    └──────┬──────┘
                           │ start_experiment()
                           ▼
                    ┌─────────────┐
       ┌───────────▶│   RUNNING   │◀───────────┐
       │            │ claimed_at  │            │
       │            │  = recent   │            │
       │            └──────┬──────┘            │
       │                   │                   │
  resume_mutation()        │           orphan_scan()
       │                   │                   │
       │        ┌──────────┴──────────┐        │
       │        │                     │        │
       │        ▼                     ▼        │
       │  ┌─────────────┐      ┌─────────────┐ │
       │  │   STOPPED   │      │  ORPHANED   │ │
       │  │ claimed_at  │      │ claimed_at  │ │
       │  │   = NULL    │      │   = stale   │ │
       │  └──────┬──────┘      └──────┬──────┘ │
       │         │                    │        │
       └─────────┘                    └────────┘
```

**关键认识**：运行状态由 `claimed_at` 推导：
- `claimed_at = NULL` → 未运行。
- `claimed_at = recent` → 运行中（由心跳刷新）。
- `claimed_at = stale` → 已孤立（副本崩溃）。

---

<a id="stopping-the-five-actors"></a>
## 停止：五类执行方

五类不同的执行方都可以停止实验，其意图各不相同：

| 执行方 | 意图 | 是否更新数据库？ |
|-------|-----------|-------------|
| **自然完成** | 全部工作完成，释放所有权 | 是（有条件） |
| **熔断器** | 失败过多，停止并记录错误 | 是（有条件） |
| **用户停止** | 用户希望暂停 | 否（变更操作已更新） |
| **丢失所有权** | 其他副本或用户已接管 | 否（已经更新） |
| **优雅关闭** | 服务端正在关闭，希望重启后恢复 | 否（保留所有权） |

**关键认识**：权限来自调用方，而不是通过检查状态得出。

包含竞态条件、证明和实施检查清单的详细分析见：
- **[停止机制深入分析](./appendix-stopping-deep-dive.md)**（约 1175 行）。

---

<a id="resuming-atomic-claims"></a>
## 恢复：原子认领

恢复通过 `UPDATE...WHERE...RETURNING` 原子转移所有权：

```sql
-- Only succeeds if not currently running
UPDATE experiment_execution_configs
SET claimed_at = now(), claimed_by = replica_id
WHERE id = X AND claimed_at IS NULL
RETURNING *
```

两个副本竞争恢复时，数据库串行化确保只有一个成功。

**关键认识**：恢复**不会**还原队列状态，而是重新从数据库查询未完成的运行。

包含多副本竞争、冷却机制和工作重建的详细分析见：
- **[恢复机制深入分析](./appendix-resume-deep-dive.md)**（约 705 行）。

---

<a id="quick-reference-code-patterns"></a>
## 速查：代码模式

<a id="stop-pattern"></a>
### 停止模式

```python
def stop(self) -> None:
    """In-memory cleanup only. No DB update."""
    if not self._active:
        return  # Idempotent
    self._active = False
    
    # Cancel in-flight jobs
    for scope in self._cancel_scopes.values():
        scope.cancel()
    
    # Clear queues
    self._task_queue.clear()
    self._eval_queue.clear()
    self._retry_heap.clear()
    
    # Close subscriber streams
    for stream in self._subscribers:
        stream.close()
    self._subscribers.clear()
```

<a id="resume-pattern-atomic-claim"></a>
### 恢复模式（原子认领）

```python
# Atomic claim - only succeeds if not running
stmt = (
    update(ExperimentExecutionConfig)
    .where(experiment_id == exp_id)
    .where(claimed_at.is_(None))  # Only if stopped
    .values(claimed_at=now, claimed_by=replica_id)
    .returning(ExperimentExecutionConfig)
)
result = await session.execute(stmt)
if result.scalar_one_or_none() is None:
    # Already running (race condition handled)
    return
```

<a id="completion-detection"></a>
### 完成检测

```python
def is_done(self) -> bool:
    if not self._active:
        return len(self._in_flight) == 0  # Just drain

    return (
        len(self._task_queue) == 0
        and len(self._eval_queue) == 0
        and len(self._retry_heap) == 0
        and len(self._in_flight) == 0
        and self._task_db_exhausted
    )
```

---

<a id="timelines"></a>
## 时间线

<a id="stop-timeline"></a>
### 停止时间线

```
t=0: User clicks Stop
     └─ Mutation: UPDATE SET claimed_at=NULL (unconditional)
     └─ daemon.stop_experiment(id)
     └─ experiment._active = False
     └─ Queues cleared, 3 jobs still in-flight

t=1: Job1 completes → on_success() → _active=False → discard result
t=2: Job2 completes → on_success() → _active=False → discard result
t=3: Job3 completes → on_success() → _active=False → discard result
     └─ _in_flight now empty
     └─ Experiment object GC'd
```

<a id="resume-timeline"></a>
### 恢复时间线

```
t=0: User clicks Resume
     └─ Mutation: atomic claim (UPDATE WHERE claimed_at IS NULL)
     └─ Claim succeeds
     └─ start_experiment() creates RunningExperiment

t=1: Query incomplete runs from DB
     └─ Find tasks where successful_count < repetitions
     └─ Populate task queue

t=2: Dispatch loop resumes
     └─ Jobs dispatched in priority order
```

<a id="completion-timeline"></a>
### 完成时间线

```
t=0: Last TaskJob completes
     └─ on_success() writes result
     └─ Queues EvalJobs for this task
     └─ _check_completion() → not done (evals pending)

t=1: Last EvalJob completes
     └─ on_success() writes annotation
     └─ _check_completion() → done!
         └─ All queues empty ✓
         └─ No more in DB ✓

t=2: Finalization
     └─ on_done() callback
     └─ DB: claimed_at = NULL (conditional update)
     └─ Registry: experiment removed
     └─ Memory: Experiment object GC'd
```

---

<a id="invariants"></a>
## 不变量

| 不变量 | 保证方式 |
|-----------|-------------|
| 一个实验只归一个副本所有 | 原子 `UPDATE...WHERE...RETURNING` |
| 状态变化 → 从注册表移除 | 所有停止路径都使用 `pop()` |
| 已停止实验不将工作加入队列 | 所有回调检查 `_active` |
| 恢复幂等 | 已运行时返回成功 |
| 工作永不丢失 | 恢复查询数据库，而非缓存状态 |

---

<a id="related-deep-dives"></a>
## 相关深入分析

| 文档 | 行数 | 内容 |
|----------|-------|---------|
| [停止机制深入分析](./appendix-stopping-deep-dive.md) | ~1175 | 五类执行方的形式化分析、竞态条件、证明和实施检查清单 |
| [恢复机制深入分析](./appendix-resume-deep-dive.md) | ~705 | 原子认领、冷却机制、工作重建和多副本安全性 |
