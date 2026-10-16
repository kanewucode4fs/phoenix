<a id="appendix-resuming-experiments--a-deep-dive"></a>
# 附录：恢复实验深入分析

<a id="overview"></a>
## 概述

已停止实验可以恢复。问题是：**恢复意味着什么，有哪些边界情况？**

看似简单，直到考虑以下问题：

**挑战：**
- 多个副本可能同时尝试恢复，如用户双击、负载均衡路由。
- 孤立实验需自动恢复，如副本崩溃。
- 必须从数据库状态重建工作。
- 即使实验已运行，恢复也必须安全。

**方案**，本文将分析：
- 原子认领防止重复恢复。
- 冷却防止快速停止/恢复抖动。
- 根据数据库重建工作，保证正确性。

---

<a id="table-of-contents"></a>
## 目录

1. [状态模型](#state-model)
2. [执行方](#the-actors)
3. [竞态问题](#the-race-condition-problem)
4. [原子认领模式](#the-atomic-claim-pattern)
5. [多副本恢复分析](#multi-replica-resume-analysis)
6. [工作重建](#work-reconstruction)
7. [冷却机制](#cooldown-mechanism)
8. [不变量和保证](#invariants-and-guarantees)
9. [已知限制](#known-limitations)
10. [汇总](#summary)
11. [实现验证清单](#implementation-verification-checklist)

---

<a id="state-model"></a>
## 状态模型

实验能否恢复，由数据库状态决定：

| 字段 | 含义 | 允许恢复？ |
|-------|---------|-----------------|
| `claimed_at = NULL` | 未运行 | 是 |
| `claimed_at = recent` | 运行中，心跳活跃 | 否 |
| `claimed_at = stale` | 孤立，副本崩溃 | 是，通过孤立扫描 |

**关键认识：** 数据库是唯一事实来源。不检查数据库，副本无法知道实验是否真正运行。`claimed_at` 时间戳结合心跳提供存活检测。

<a id="experiment-lifecycle-states"></a>
### 实验生命周期状态

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

---

<a id="the-actors"></a>
## 执行方

两类执行方可恢复实验：

<a id="1-user-resume-via-mutation"></a>
### 1. 用户恢复（通过变更操作）

用户在界面点击恢复，变更操作：
1. 检查冷却，防止快速切换。
2. 原子认领实验（`WHERE claimed_at IS NULL`）。
3. 开始内存处理。

```python
# Atomic claim: only succeeds if not currently running
stmt = (
    update(ExperimentExecutionConfig)
    .where(experiment_id == exp_id)
    .where(claimed_at.is_(None))  # Only if stopped
    .values(claimed_at=now, claimed_by=replica_id, status="RUNNING", cooldown_until=now + cooldown)
    .returning(ExperimentExecutionConfig)
)
```

<a id="2-orphan-scan-automatic-recovery"></a>
### 2. 孤立扫描（自动恢复）

后台守护进程定期扫描孤立实验：
1. 查找 `claimed_at < cutoff`，即过期实验。
2. 原子认领（`WHERE claimed_at < cutoff`）。
3. 恢复处理。

```python
# Atomic claim: only succeeds if still stale
claim_stmt = (
    update(ExperimentExecutionConfig)
    .where(experiment_id == exp_id)
    .where(claimed_at < cutoff)  # Only if still stale
    .values(claimed_at=now, claimed_by=replica_id)
    .returning(experiment_id)
)
```

<a id="why-these-are-different"></a>
### 两者为何不同

| 方面 | 用户恢复 | 孤立扫描 |
|--------|-------------|-------------|
| 触发 | 用户操作 | 自动 |
| 条件 | `claimed_at IS NULL` | `claimed_at < cutoff` |
| 设置 `cooldown_until` | 是（`now + 5s`） | 否，不应阻碍用户 |
| 清除 `last_error` | 是 | 是 |

**重要：** 孤立扫描**不**设置 `cooldown_until`，确保用户可立即停止自动恢复实验，不受冷却阻碍。

---

<a id="the-race-condition-problem"></a>
## 竞态问题

<a id="scenario-double-click-resume"></a>
### 场景：双击恢复

```
User double-clicks "Resume" button rapidly
Request 1 hits Replica A
Request 2 hits Replica B (load balancer)
```

没有保护时，两个副本可能：
1. 都读取 `claimed_at = NULL`，认为可安全恢复。
2. 都写入 `claimed_at = now`。
3. 都开始处理，产生重复工作！

<a id="scenario-user-resume-vs-orphan-scan"></a>
### 场景：用户恢复与孤立扫描

```
1. Experiment 123 was running on Replica A
2. A crashes, claim becomes stale
3. User on Replica B clicks "Resume" 
4. Replica C's orphan scan finds experiment 123
5. Both B and C try to resume simultaneously
```

<a id="scenario-multiple-orphan-scanners"></a>
### 场景：多个孤立扫描器

```
Replicas A, B, C all run orphan scan around the same time
All find experiment 123 is orphaned
All try to claim it
```

---

<a id="the-atomic-claim-pattern"></a>
## 原子认领模式

方案是**原子条件更新**，不用先读后写：

```python
# WRONG: Race condition (time-of-check to time-of-use)
config = await session.get(ExperimentExecutionConfig, exp_id)
if config.claimed_at is None:  # Check
    config.claimed_at = now  # Write - but someone else might have claimed!
```

采用带 WHERE 的原子 UPDATE：

```python
# CORRECT: Atomic claim
stmt = (
    update(ExperimentExecutionConfig)
    .where(experiment_id == exp_id)
    .where(claimed_at.is_(None))  # Condition in WHERE, not separate check
    .values(claimed_at=now, claimed_by=replica_id)
    .returning(ExperimentExecutionConfig)
)
result = await session.execute(stmt)
updated = result.scalar_one_or_none()

if updated is None:
    # Atomic operation failed - someone else claimed it (or already running)
    ...
```

**原理：** 数据库原子执行 UPDATE。两个副本同时执行时：
- 都发送 `UPDATE ... WHERE claimed_at IS NULL`。
- 数据库通过行锁串行化。
- 首个成功，设置 `claimed_at = now`。
- 第二个 WHERE 不满足，因为 claimed_at 已非 NULL。
- 第二个更新 0 行，知道竞争失败。

---

<a id="multi-replica-resume-analysis"></a>
## 多副本恢复分析

<a id="race-1-user-double-click-on-same-replica"></a>
### 竞争 1：同副本用户双击

```
1. User clicks Resume (Request 1)
2. User clicks Resume again (Request 2) - same replica
```

**时间线：**
```
Request 1: UPDATE SET claimed_at=now WHERE claimed_at IS NULL → 1 row
Request 2: UPDATE SET claimed_at=now WHERE claimed_at IS NULL → 0 rows
```

**结果：**
- 请求 1 成功，启动实验。
- 请求 2 得到 `updated_config = None`。
- 请求 2 检查已运行：`config.claimed_at IS NOT NULL` → 是。
- 请求 2 返回 `resumed=True`，幂等成功。

**结论：** 安全。一次认领成功，另一次幂等返回成功。

<a id="race-2-user-double-click-on-different-replicas"></a>
### 竞争 2：不同副本用户双击

```
1. User clicks Resume (Request 1 → Replica A)
2. User clicks Resume (Request 2 → Replica B) - load balancer split
```

**时间线：**
```
A: UPDATE SET claimed_at=now WHERE claimed_at IS NULL → 1 row
B: UPDATE SET claimed_at=now WHERE claimed_at IS NULL → 0 rows
```

**结果：** 与竞争 1 相同，原子 UPDATE 确保仅一个获胜。

**结论：** 安全，数据库串行化防止重复认领。

<a id="race-3-user-resume-vs-orphan-scan"></a>
### 竞争 3：用户恢复与孤立扫描

```
Replica A: User clicks Resume
Replica B: Orphan scan finds stale experiment
```

**情况 A：用户先成功：**
```
A: UPDATE SET claimed_at=T1 WHERE claimed_at IS NULL → 1 row
B: UPDATE SET claimed_at=T2 WHERE claimed_at < cutoff → 0 rows (claimed_at=T1, not stale)
```
- A 认领成功。
- B 的 WHERE 不满足，T1 是最近时间，不小于 cutoff。

**情况 B：孤立扫描先成功：**
```
B: UPDATE SET claimed_at=T1 WHERE claimed_at < cutoff → 1 row
A: UPDATE SET claimed_at=T2 WHERE claimed_at IS NULL → 0 rows (claimed_at=T1, not NULL)
```
- B 认领成功。
- A 的 WHERE 不满足，claimed_at 不再为 NULL。
- A 检查是否已运行，是则返回 `resumed=True`。

**结论：** 安全，两种顺序都恰好认领一次。

<a id="race-4-multiple-orphan-scanners"></a>
### 竞争 4：多个孤立扫描器

```
Replicas A, B, C all run orphan scan
All find experiment 123 with stale claimed_at
```

**时间线：**
```
A: UPDATE SET claimed_at=T1 WHERE claimed_at < cutoff → 1 row
B: UPDATE SET claimed_at=T2 WHERE claimed_at < cutoff → 0 rows (T1 > cutoff)
C: UPDATE SET claimed_at=T3 WHERE claimed_at < cutoff → 0 rows (T1 > cutoff)
```

**结果：** 首个扫描器获胜，其余更新 0 行并记录 "claimed by another replica"。

**结论：** 安全，原子更新将竞争认领串行化。

<a id="race-5-resume-during-graceful-shutdown"></a>
### 竞争 5：优雅关闭期间恢复

```
1. User clicks Resume on Replica A
2. A is in graceful shutdown (hasn't released claims yet)
```

**时间线：**
```
A.mutation: UPDATE SET claimed_at=now WHERE claimed_at IS NULL
```

**实验位于 A 的优雅关闭流程时：**
- `claimed_at` 仍有值，关闭保留所有权。
- WHERE 不满足 → `updated_config = None`。
- 变更操作检查已运行，是 → `resumed=True`。

**A 关闭之后：**
- 认领过期。
- 孤立扫描最终重新认领。

**结论：** 安全。恢复平稳失败，孤立扫描负责恢复。

---

<a id="work-reconstruction"></a>
## 工作重建

<a id="the-key-insight"></a>
### 关键认识

恢复**不**还原内存队列状态，而是重新查询数据库中的未完成工作。

```python
# Called during initialization of RunningExperiment
stmt = get_experiment_incomplete_runs_query(
    experiment,
    dialect,
    cursor_example_rowid=offset,
    limit=batch_size,
)
```

<a id="what-incomplete-means"></a>
### 未完成的含义

以下情况视为运行未完成：
1. **缺失**：此示例与重复编号组合不存在 `experiment_run`。
2. **失败**：存在 `experiment_run` 记录，但有错误。

查询找出全部 `successful_count < repetitions` 的示例。

<a id="why-database-derived-work-is-safe"></a>
### 为什么从数据库推导工作是安全的

**场景：** 实验处理中停止，部分作业完成，部分未完成。

```
Before stop:
- Jobs 1-5: Completed (in DB)
- Jobs 6-8: In-flight (processing)
- Jobs 9-20: Queued (in memory)

After stop:
- Jobs 1-5: Still in DB (completed)
- Jobs 6-8: Lost (never wrote to DB due to shield timeout or cancellation)
- Jobs 9-20: Lost (memory cleared)

On resume:
- Query: "Find incomplete runs"
- Result: Jobs 6-20 (no successful run record)
- Queued for processing: Jobs 6-20
```

**关键：** 作业 6–8 停止时可能部分完成。更新或插入写入会处理：
- 作业 6 结果已写入：查询不包含它，因为已完成。
- 结果未写入：查询包含它，将重新执行。

<a id="duplicate-work-protection"></a>
### 重复工作保护

写入采用带唯一约束的更新或插入：

```sql
INSERT INTO experiment_runs (experiment_id, dataset_example_id, repetition_number, ...)
ON CONFLICT (experiment_id, dataset_example_id, repetition_number)
DO UPDATE SET ...
```

同一作业因竞态或恢复执行两次时，第二次仅覆盖写入，不造成损坏，只产生冗余工作。

---

<a id="cooldown-mechanism"></a>
## 冷却机制

<a id="purpose"></a>
### 目的

防止快速停止/恢复抖动浪费工作：

```
T0: User clicks Stop
T1: Experiment stops, 10 jobs cancelled
T2: User clicks Resume (immediately)
T3: Experiment resumes, re-queues 10 jobs
T4: User clicks Stop (oops, wrong button)
T5: Experiment stops, 10 jobs cancelled again
...
```

<a id="implementation"></a>
### 实现

将冷却检查合入原子 UPDATE 的 WHERE，防止 TOCTOU 竞态：

```python
# In resume mutation — single atomic UPDATE with cooldown in WHERE:
stmt = (
    update(ExperimentExecutionConfig)
    .where(experiment_id == exp_id)
    .where(claimed_at.is_(None))
    .where(or_(cooldown_until.is_(None), cooldown_until <= now))
    .values(
        claimed_at=now,
        claimed_by=replica_id,
        status="RUNNING",
        cooldown_until=now + EXPERIMENT_TOGGLE_COOLDOWN,
    )
)
# If 0 rows: SELECT to diagnose (not found, already running, or cooldown active)
```

<a id="what-sets-cooldown_until"></a>
### 哪些操作设置 `cooldown_until`

| 操作 | 设置 `cooldown_until`？ | 原因 |
|-----------|----------------------|-----|
| 用户停止 | 是（`now + 5s`） | 启用冷却 |
| 用户恢复 | 是（`now + 5s`） | 启用冷却 |
| 自然完成 | 否 | 内部操作 |
| 熔断器 | 否 | 内部操作 |
| 孤立扫描认领 | 否 | 不应阻碍用户 |
| 初始启动 | 否 | 不应阻碍首次停止 |

**关键：** 孤立扫描不设置 `cooldown_until`，确保：
- 自动恢复实验可以立即停止。
- 用户在崩溃恢复后保留完整控制。

<a id="cooldown-vs-idempotency"></a>
### 冷却与幂等

冷却仅作用于**相反**操作，即停止→恢复、恢复→停止。

重复操作，即恢复→恢复、停止→停止，由幂等处理：
- 运行中恢复 → 已运行，幂等返回。
- 已停止时停止 → 已停止，幂等返回。

---

<a id="invariants-and-guarantees"></a>
## 不变量和保证

<a id="safety-properties"></a>
### 安全性质

<a id="s1-single-owner"></a>
#### S1：单一所有者

> **任何时刻，一个实验最多归一个副本所有。**

**证明：**
1. 带 WHERE 的原子 UPDATE 建立所有权。
2. WHERE 确保仅前提成立才成功。
3. 数据库串行化同一行的并发 UPDATE。
4. 多副本竞争时仅一个 UPDATE 成功。∎

<a id="s2-no-lost-resume"></a>
#### S2：恢复不会丢失

> **变更操作原子认领成功后，实验将在该副本启动。**

**证明：**
1. 认领成功后调用 `start_experiment()`。
2. `start_experiment()` 创建 RunningExperiment 并加入注册表。
3. 实验开始处理。∎

**说明：** `start_experiment()` 崩溃时，`claimed_at` 有值但实际未运行，形成孤立状态，由扫描恢复。

<a id="s3-idempotent-resume"></a>
#### S3：幂等恢复

> **同一实验的多个恢复请求，最终恰好产生一个运行实例。**

**证明：**
1. 首请求认领成功，启动实验。
2. 后续认领失败，claimed_at 不再为 NULL。
3. 变更操作检查运行中则返回成功。
4. 一个实例运行，所有请求成功。∎

<a id="s4-resume-correctness"></a>
#### S4：恢复正确性

> **恢复实验恰好处理未完成工作，无重复、无遗漏。**

**证明：**
1. 工作来自 `get_experiment_incomplete_runs_query()`。
2. 返回 `successful_count < repetitions` 的示例。
3. 已完成有 `experiment_run` 记录，不返回。
4. 未完成无记录或有错误记录，会返回。
5. 更新或插入处理竞态，不损坏数据。∎

<a id="liveness-properties"></a>
### 活性性质

<a id="l1-orphan-recovery"></a>
#### L1：孤立恢复

> **拥有实验的副本崩溃后，其他副本最终将恢复它。**

**证明：**
1. 崩溃副本停止心跳。
2. `claimed_at` 无更新，变为过期。
3. 扫描发现 `claimed_at < cutoff`。
4. 认领并恢复。∎

**上限：** `STALE_CLAIM_TIMEOUT + ORPHAN_SCAN_INTERVAL`，通常 10–15 分钟。

<a id="l2-cooldown-expiry"></a>
#### L2：冷却到期

> **已停止实验最终可恢复，因为冷却会到期。**

**证明：**
1. 停止设置 `cooldown_until = now + 5s`。
2. 5 秒后，`cooldown_until <= now`。
3. 恢复 WHERE 通过。∎

**上限：** `EXPERIMENT_TOGGLE_COOLDOWN`，5 秒。

<a id="what-we-cannot-guarantee"></a>
### 无法保证的事项

<a id="no-duplicate-work-during-transition"></a>
#### 过渡期没有重复工作

恢复时，若旧运行器处于优雅关闭：
- 旧运行器可能完成部分受屏蔽保护的作业。
- 新运行器可能重新入队相同尚未写库的作业。
- 两者都可能写结果。

**缓解：** 更新或插入安全处理重复写入。

<a id="instant-resume"></a>
#### 即时恢复

无法即时恢复，因为：
1. 原子认领需数据库往返。
2. 工作重建需数据库查询。
3. `start_experiment()` 存在初始化开销。

---

<a id="known-limitations"></a>
## 已知限制

<a id="limitation-1-stale-cooldown-state-after-crash"></a>
### 限制 1：崩溃后残留冷却状态

这**不是**冷却本身的问题，冷却是解决方案。边界情况是崩溃恢复后冷却状态意外保留。

**场景：**
1. T0 停止，设置 `cooldown_until = T0 + 5s`。
2. T0 + 2 秒服务端崩溃。
3. T0 + 3 秒重启。
4. 用户立即尝试恢复。
5. 数据库仍有 `cooldown_until = T0 + 5s`，只过去 3 秒。
6. 因冷却拒绝恢复，出乎预期。

**影响：** 轻微体验问题，再等 2 秒。

**未缓解原因：**
- 很少见，需活跃交互时崩溃。
- 启动时清除 `cooldown_until` 可能重新允许冷却要防止的快速切换滥用。
- 5 秒等待很短。

<a id="limitation-2-orphan-scan-delay"></a>
### 限制 2：孤立扫描延迟

孤立恢复延迟明显：
- `STALE_CLAIM_TIMEOUT`：10 分钟，需等认领过期。
- `ORPHAN_SCAN_INTERVAL`：5 分钟，扫描频率。
- 最差 15 分钟后恢复。

**影响：** 崩溃后实验可能卡住至多 15 分钟。

**未缓解原因：**
- 更短超时会误认领仍运行的实验。
- 更频繁扫描浪费资源。
- 在恢复时间与安全性间取舍。

**替代方案：** 用户可立即手动恢复，无需等待孤立扫描。

<a id="limitation-3-evaluator-state-not-preserved"></a>
### 限制 3：不保留评估器内部状态

保存评估器配置，但不保存内部状态，例如 LLM 客户端连接池：

```
Before crash: Evaluator has warm connection pool, cached auth tokens
After resume: Evaluator creates fresh connections, re-authenticates
```

**影响：** 恢复时性能略有下降，前几个作业可能更慢。

**未缓解原因：** 序列化连接状态复杂且易错。

<a id="summary-of-limitations"></a>
### 限制汇总

| 限制 | 严重程度 | 状态 |
|------------|----------|--------|
| 崩溃后残留冷却 | 低 | 罕见，等待几秒 |
| 孤立扫描延迟 | 中 | 接受取舍，可手动恢复 |
| 评估器状态丢失 | 低 | 接受性能代价 |

---

<a id="summary"></a>
## 汇总

<a id="the-core-insight"></a>
### 核心认识

恢复是**原子所有权转移**：
1. 带 WHERE 的原子 UPDATE 保证单一所有者。
2. 数据库串行化防止竞态。
3. 幂等响应处理重复请求。

<a id="the-atomic-claim-pattern"></a>
### 原子认领模式

```sql
-- User resume: claim if stopped
UPDATE SET claimed_at=now, claimed_by=replica_id
WHERE experiment_id=X AND claimed_at IS NULL

-- Orphan scan: claim if stale
UPDATE SET claimed_at=now, claimed_by=replica_id
WHERE experiment_id=X AND claimed_at < cutoff
```

两种模式都：
- 使用原子 UPDATE，不单独先读后写。
- 在 WHERE 包含条件。
- 检查 RETURNING 发现竞争失败。

<a id="multi-replica-safety"></a>
### 多副本安全

| 场景 | 行为 | 结果 |
|----------|--------------|--------|
| 同副本双击 | 第二个 UPDATE 因 claimed_at 改变失败 | 幂等成功 |
| 不同副本双击 | 数据库串行化，一方获胜 | 幂等成功 |
| 用户与孤立扫描 | 先执行者获胜 | 单一所有者 |
| 多个孤立扫描器 | 先执行者获胜 | 单一所有者 |

<a id="work-reconstruction"></a>
### 工作重建

- 恢复从数据库查询未完成运行，而非缓存。
- 更新或插入处理竞态重复工作。
- 熔断器状态丢失，为可接受取舍。

---

<a id="implementation-verification-checklist"></a>
## 实现验证清单

<a id="atomic-claim-user-resume"></a>
### 原子认领（用户恢复）

- [x] **使用带 WHERE 的 UPDATE**，而非先读后写。
- [x] **WHERE 包含 `claimed_at IS NULL`**。
- [x] **使用 RETURNING** 检测认领成功。
- [x] **已运行时幂等返回成功**。
- [x] **设置 `cooldown_until`** 启用冷却。
- [x] **冷却检查放在 WHERE**，不单独 SELECT，防止 TOCTOU。

<a id="atomic-claim-orphan-scan"></a>
### 原子认领（孤立扫描）

- [x] **使用带 WHERE 的 UPDATE**，而非先读后写。
- [x] **WHERE 包含 `claimed_at < cutoff`**。
- [x] **使用 RETURNING** 检测成功。
- [x] **不设置 `cooldown_until`**，允许用户立即控制。
- [x] **成功认领清除 `last_error`**。

<a id="cooldown"></a>
### 冷却

- [x] **在 UPDATE WHERE 中原子执行冷却约束**，不单独检查。
- [x] **`cooldown_until > now` 时拒绝**。
- [x] **成功恢复设置 `cooldown_until = now + 5s`**。

<a id="work-reconstruction"></a>
### 工作重建

- [x] **从数据库查询未完成运行**，而非缓存。
- [x] **使用 `get_experiment_incomplete_runs_query()`**。
- [x] 大型数据集**支持分页**。

<a id="multi-replica-safety"></a>
### 多副本安全

- [x] 原子 UPDATE **保证单一所有者**。
- [x] **竞争失败者平稳返回**，幂等或记录日志。
- [x] **孤立扫描加入抖动**，避免惊群。

<a id="error-handling"></a>
### 错误处理

- [x] **恢复时清除 `last_error`**，重新开始。
- [x] **记录认领失败**以便调试。
- [x] **start_experiment() 失败**留下孤立实验，由扫描恢复。

---

<a id="verification-commands"></a>
## 验证命令

验证实现：

1. **阅读恢复相关方法：**
   ```
   - resume_experiment mutation (experiment_mutations.py)
   - _resume_orphaned() method
   - start_experiment() method
   - get_experiment_incomplete_runs_query()
   ```

2. **搜索原子认领模式：**
   ```
   - All resume paths use UPDATE with WHERE (not read-then-write)
   - WHERE clause includes ownership condition
   - RETURNING used to detect success
   ```

3. **跟踪竞争场景：**
   ```
   - User double-click → atomic claim serializes
   - User vs orphan scan → first wins
   - Multiple orphan scanners → first wins
   ```

4. **验证不变量：**
   ```
   - S1: Atomic UPDATE ensures single owner
   - S3: Idempotent response for duplicate requests
   - L1: Orphan scan eventually recovers crashed experiments
   ```
