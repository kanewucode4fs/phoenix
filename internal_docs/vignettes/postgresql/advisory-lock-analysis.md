<a id="advisory-lock-analysis"></a>

# 建议锁分析

*2026-03-03*

<a id="table-of-contents"></a>

## 目录

1. [决策](#decision)
   - [当前为何无需此锁](#why-the-lock-isnt-needed-today)
   - [PR 方案为何增加风险](#why-the-prs-approach-adds-risk)
   - [何时重新评估](#when-to-revisit)
   - [迁移编写准则](#migration-authoring-guidelines)
2. [Alembic 如何处理事务](#how-alembic-handles-transactions)
   - [两个设置](#the-two-settings)
   - [模式 1：全部迁移共用事务](#mode-1-all-migrations-in-one-transaction)
   - [模式 2：每个迁移独立事务](#mode-2-one-transaction-per-migration)
   - [模式 3：外部事务](#mode-3-external-transaction-overrides-everything)
   - [模式 1 与模式 3](#mode-1-vs-mode-3)
   - [Phoenix 使用的模式](#what-phoenix-uses)
3. [CREATE INDEX CONCURRENTLY](#create-index-concurrently)
4. [env.py 的架构调节点](#the-envpy-architectural-lever)
   - [变更](#the-change)
   - [带来的能力](#what-this-enables)
   - [发生的变化](#what-changes)
   - [与加锁方案的交互](#interaction-with-lock-approaches)
   - [是否应该更改？](#should-we-change-it)
5. [行业先例](#industry-precedent)
   - [会话级锁为何是默认选择](#why-session-level-is-the-industry-default-and-why-transaction-level-isnt)
   - [其他工具如何处理](#how-other-tools-handle-this)
   - [取舍汇总](#tradeoff-summary)
   - [对 Phoenix 的意义](#implication-for-phoenix)
6. [参考实现](#reference-implementation)
   - [事务级方案](#modified-run_migrations-in-envpy)
   - [会话级替代方案](#alternative-session-level-lock--phoenix_migration_database_url)
   - [如实评估](#honest-assessment)
7. [Schema 作用域](#schema-scoping)

---

<a id="decision"></a>

# 决策

<a id="why-the-lock-isnt-needed-today"></a>

## 当前为何无需此锁

现有迁移均大量使用 DDL。每个 `INSERT` 都与同一 `upgrade()` 函数中的 `CREATE TABLE` 配对。Phoenix 的 env.py 将全部迁移包围在单个外层事务中，参见 [Alembic 如何处理事务](#how-alembic-handles-transactions)；`CREATE TABLE` 获取 `ACCESS EXCLUSIVE`，将并发执行串行化。第二个副本的 `CREATE TABLE` 失败，事务连同 DML 一起回滚，重启后便看到数据库已达 head。

建议锁所防止的正确性问题，即对**已存在**表执行非幂等 DML，且同一迁移步骤无 DDL，在此代码库并不存在。Phoenix 既有模式为同一步骤中创建表并回填，在并发执行下结构上安全。

不加锁时，并发启动会产生 `relation "foo" already exists` 等噪声错误，但可自愈。多副本部署若需干净启动，标准做法是在 Kubernetes init container 或 Helm pre-upgrade hook 中运行迁移。

<a id="why-the-prs-approach-adds-risk"></a>

## PR 方案为何增加风险

PR 使用会话级 `pg_advisory_lock`，在 Alembic 外获取锁，传入连接前调用 `conn.commit()`。这迫使其使用会话级锁，因为该提交会释放事务级锁。另一方案是在 env.py 既有外层事务内部获取事务级锁，可避免以下风险，参见[参考实现](#reference-implementation)，但 PR 未采用。

会话级锁绑定 PostgreSQL 后端连接，而非客户端连接。两者分离时会出问题：

- **PgBouncer 事务模式，使用默认 `DISCARD ALL`：**`conn.commit()` 后，PgBouncer 将后端归还池并运行 `DISCARD ALL`，释放锁。锁静默失效。
- **PgBouncer 事务模式，不使用 `DISCARD ALL`：**锁保留在 PgBouncer 池中的空闲后端。其他副本阻塞 300 秒后超时、崩溃。集群卡住 10—60 分钟，直到 PgBouncer 关闭该后端。这比不加锁更差。
- **OOM-kill / SIGKILL，任何部署：**pod 持锁时被杀死，PostgreSQL 要等 TCP keepalive 触发才检测到连接失效；RDS 默认约 6 分钟，裸机操作系统默认最长约 2 小时。其他全部副本持续阻塞。

可通过绕过连接池的直连缓解，如 Prisma 的 `DIRECT_URL`。但 Phoenix 的运行时查询和迁移共用一个 `PHOENIX_SQL_DATABASE_URL`，因此使用 Supabase、Neon、PgBouncer sidecar 等连接池的用户，目前无法为迁移单独选择直连。

<a id="when-to-revisit"></a>

## 何时重新评估

以下任一情况发生时重新讨论：

1. **迁移向已有表添加非幂等 DML**，例如 `INSERT INTO existing_table ...` 未使用 `ON CONFLICT`，同一步骤也没有 `CREATE TABLE`。并发执行会静默产生重复数据。

事务级锁无需新增配置，可直接通过 PgBouncer 工作，参见[参考实现](#reference-implementation)。会话级锁还要求 `PHOENIX_MIGRATION_DATABASE_URL`，即类似 Prisma `DIRECT_URL` 的独立直连字符串，供连接池后方用户安全路由迁移。

具体实现参见[参考实现](#reference-implementation)；其他工具的处理背景参见[行业先例](#industry-precedent)。

<a id="migration-authoring-guidelines"></a>

## 迁移编写准则

无论是否加锁，以下约定都可保证并发迁移安全：

- **DML 与 DDL 配对。**向新建表插入数据安全，`CREATE TABLE` 会串行化该步骤。
- **独立 DML 应幂等。**对已有表执行 DML 时使用 `INSERT ... ON CONFLICT DO NOTHING` 或 `WHERE NOT EXISTS`。

---

<a id="how-alembic-handles-transactions"></a>

# Alembic 如何处理事务

Alembic 事务行为由两方面控制：传给 `context.configure()` 的设置，以及启动时是否已有打开的外部事务。两者交互较微妙，与建议锁直接相关。

<a id="the-two-settings"></a>

### 两个设置

- **`transactional_ddl`**，默认 `True`：数据库是否支持事务内 DDL。PostgreSQL 支持，MySQL 不支持。为 `True` 时，Alembic 将 DDL 包围在事务内；为 `False` 时，DDL 在事务外执行，由数据库自动提交。
- **`transaction_per_migration`**，默认 `False`：每个迁移步骤使用独立事务，或全部步骤共享事务。

<a id="mode-1-all-migrations-in-one-transaction-transaction_per_migrationfalse"></a>

### 模式 1：全部迁移共用事务（`transaction_per_migration=False`）

这是 Alembic 默认模式。全部迁移步骤在单事务执行，任一步骤失败则全部回滚。

```
BEGIN
  ├── migration 1 (DDL/DML)
  ├── migration 2 (DDL/DML)
  ├── migration 3 (DDL/DML) ── FAIL → ROLLBACK (all 3 rolled back)
  │
  └── (or if all succeed) ─── COMMIT (all 3 committed atomically)
```

<a id="mode-2-one-transaction-per-migration-transaction_per_migrationtrue"></a>

### 模式 2：每个迁移独立事务（`transaction_per_migration=True`）

每个迁移步骤独立事务，单独提交。若步骤 3 失败，步骤 1 和 2 已提交。

```
  ┌── BEGIN ── migration 1 ── COMMIT ──┐
  │                                    │
  ├── BEGIN ── migration 2 ── COMMIT ──┤  each independently committed
  │                                    │
  ├── BEGIN ── migration 3 ── FAIL ────┤  only step 3 rolls back
  │            ROLLBACK                │
  └────────────────────────────────────┘
```

**模式 2 的缺点：**

- **失败时部分应用。**5 个迁移中的第 3 个失败时，第 1、2 个已提交，无法回滚，数据库处于中间结构状态。重启后 Alembic 从第 3 个继续，因为每次提交更新了 `alembic_version`，但失败迁移必须足够幂等，才能顺利重试。
- **不兼容事务级建议锁。**`pg_advisory_xact_lock` 在事务提交时释放。模式 2 中，第 1 个迁移 `COMMIT` 后锁即释放，剩余迁移不受保护。覆盖整次运行需要会话级锁，承受 PgBouncer 风险，或使用模式 3。
- **运行期间版本可见。**每个提交步骤的 `alembic_version` 更新立即对其他连接可见。并发进程中途检查“是否到达 head”时，可能看到部分版本，并在不完整结构上运行应用。
- **无调用方控制的注入点。**与模式 1 类似，Alembic 控制每步事务。调用方无法在每个事务*内部*注入锁、会话参数等逻辑，只能在整个 `run_migrations()` 调用之前或之后处理。

模式 2 用原子性换取粒度。当单个迁移很大、希望避免长事务时有用，常见于生产 `ALTER TABLE`。Phoenix 在启动、对外服务前运行迁移，模式 1/3 的全有或全无语义更好：启动时部分结构比完整回滚后重试更难推理。

<a id="mode-3-external-transaction-overrides-everything"></a>

### 模式 3：外部事务（覆盖全部设置）

调用 `context.configure()` 时，若连接已有事务，Alembic 通过 `connection.in_transaction()` 检测并设置 `_in_external_transaction = True`，已在 Alembic 源码 `alembic/runtime/migration.py` 第 159 行验证。此后**每次** `begin_transaction()` 调用，包括每迁移调用，均返回 `nullcontext()`。Alembic 将全部事务管理交给调用方。

此模式下 `transaction_per_migration` **不生效**，全部步骤运行在调用方事务。

```
caller: connection.begin() ──► BEGIN
          │
          ├── context.configure(             MigrationContext.__init__():
          │     transaction_per_migration=     connection.in_transaction()? → Yes
          │       True,  ← IGNORED            _in_external_transaction = True
          │     ...)
          │
          ├── context.run_migrations() ───►  for each step:
          │                                    begin_transaction()
          │                                      → _in_external_transaction?
          │                                      → Yes → return nullcontext()
          │                                    run step (DDL/DML)
          │                                    (no per-step commit)
          │
caller: transaction.commit() ──► COMMIT  (all steps committed atomically)
          │
          │   (or on error:)
caller: transaction.rollback() ► ROLLBACK (all steps rolled back)
```

<a id="mode-1-vs-mode-3"></a>

### 模式 1 与模式 3

模式 1 和模式 3 的数据库行为相同，全部迁移在单事务执行。区别是**由谁控制事务**：

```
Mode 1 (Alembic controls):

  context.run_migrations()
    Alembic: BEGIN
      migration 1
      migration 2
    Alembic: COMMIT
  ← no way to inject logic inside the transaction


Mode 3 (caller controls):

  env.py: connection.begin()  ──► BEGIN
    _acquire_migration_lock()  ← caller can inject logic here
    context.run_migrations()
      migration 1
      migration 2
  env.py: transaction.commit() ──► COMMIT
```

模式 1 由 Alembic 控制事务生命周期。模式 3 由调用方控制，可在同一事务内、Alembic 前后注入获取建议锁、设置会话参数或自定义错误处理等逻辑。Phoenix 因此使用模式 3，使 env.py 显式控制事务，包括 `try`/`except`/`rollback`。

实际影响：模式 3 是事务级建议锁方案的前提，可在调用方事务内获取 `pg_advisory_xact_lock`。模式 1 无法将锁注入 Alembic 事务内部。

<a id="what-phoenix-uses"></a>

### Phoenix 使用的模式

Phoenix `env.py` 使用**模式 3**，在 `context.configure()` 前调用 `connection.begin()`，打开外部事务。虽然传入 `transaction_per_migration=True`，该设置被覆盖，全部迁移仍在单个外层事务中执行。

这很重要，因为：

1. 在外层事务内获取的 `pg_advisory_xact_lock` 覆盖整次迁移运行，不会在第一步后释放。
2. 迁移失败时，运行中全部先前步骤都会回滚，而非仅失败步骤。
3. `alembic_version` 表在事务内逐步更新，但仅在最终 `COMMIT` 后对其他连接可见。

---

<a id="create-index-concurrently"></a>

# CREATE INDEX CONCURRENTLY

Phoenix 唯一的并发索引迁移（`f1a6b2f0c9d5`）通过 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true` 环境变量**显式启用** `CONCURRENTLY`。默认在事务内普通建索引，受任何建议锁完整保护。

显式启用时，迁移在原始 psycopg 连接上调用 `dbapi_conn.commit()`，再设置 `dbapi_conn.autocommit = True`，跳出 env.py 事务。这对建议锁有两点影响：

- **事务级**锁（`pg_advisory_xact_lock`）被 `dbapi_conn.commit()` 释放；并发建索引开始前底层事务已提交，锁不再保护它。
- **会话级**锁（`pg_advisory_lock`）跨提交保留，但迁移自身位于任何事务之外，中途失败无论如何都不会回滚。

`dbapi_conn.commit()` 还会提交本次运行的全部先前迁移，之后 `_disable_autocommit()` 恢复 `autocommit = False`，将迁移运行拆为两个事务。

**设置 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true` 时，显式启用：**

```
connection.begin() ──► Transaction T1
                        │
                        ├── migration 1 ─────────────────── protected by xact lock
                        ├── migration 2 ─────────────────── protected by xact lock
                        ├── ...
                        ├── migration N-1 ───────────────── protected by xact lock
                        │
                        ├── migration N (concurrent index):
                        │     dbapi_conn.commit() ────────► T1 committed, xact lock released
                        │     autocommit = True
                        │     CREATE INDEX CONCURRENTLY ─── runs outside any transaction
                        │     autocommit = false
                        │
                       ╌╌╌  (implicit transaction boundary)
                        │
                        ├── migration N+1 ───────────────── Transaction T2 (NO lock)
                        ├── migration N+2 ───────────────── T2 (NO lock)
                        ├── ...
                        │
transaction.commit() ──► T2 committed
```

- **T1**：并发索引之前的所有迁移，由 `dbapi_conn.commit()` 提交。T1 中获取的 `pg_advisory_xact_lock` 在此释放。
- **T2**：下个迁移第一条 SQL 执行时由 psycopg 隐式启动；`autocommit = False` 后首条语句会开启隐式事务。后续迁移在此**没有**建议锁保护，由 env.py 最终 `transaction.commit()` 提交。

T2 中迁移失败时，仅回滚 T2，T1 已提交。env.py 的 SQLAlchemy `transaction` 对象不知道这种拆分，仍以为单个连续事务处于打开状态。

**未设置 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY` 时，默认：**在事务内普通建索引，不拆分事务，整次运行与参考实现图一致，单事务且始终持锁。

并发通过 `IF NOT EXISTS` 处理：两个副本同时运行相同迁移时，由 PostgreSQL 系统目录锁串行化。一个先注册索引名称，另一个通过 `IF NOT EXISTS` 看到后跳过。

`CONCURRENTLY` 的真正风险是构建中途崩溃，而非并发。失败构建会在 `pg_class` 留下 **INVALID** 索引，后续运行被 `IF NOT EXISTS` 静默跳过。索引名称存在，但查询规划器不会使用。此为 PostgreSQL `CONCURRENTLY` 固有行为，与是否存在建议锁无关。恢复需要人工介入：

```sql
-- Check for invalid indexes
SELECT indexrelid::regclass, indisvalid FROM pg_index WHERE NOT indisvalid;

-- Fix
DROP INDEX CONCURRENTLY IF EXISTS ix_spans_session_id;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_spans_session_id ...;
```

---

<a id="the-envpy-architectural-lever"></a>

# env.py 的架构调节点

Phoenix env.py 当前使用模式 3，即外部事务。这是选择，而非要求。切换至模式 2 的每迁移独立事务，会显著改变加锁取舍。

<a id="the-change"></a>

### 变更

从 env.py 移除 `connection.begin()`，让 Alembic 按步骤管理事务：

```python
# Current (Mode 3 — external transaction, transaction_per_migration has no effect)
def run_migrations(connection: Connection) -> None:
    transaction = connection.begin()
    try:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            transactional_ddl=True,
            transaction_per_migration=True,  # ← silently ignored
        )
        context.run_migrations()
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()


# Modified (Mode 2 — Alembic manages per-migration transactions)
def run_migrations(connection: Connection) -> None:
    try:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            transactional_ddl=True,
            transaction_per_migration=True,  # ← now takes effect
        )
        context.run_migrations()
    finally:
        connection.close()
```

<a id="what-this-enables"></a>

### 带来的能力

模式 2 下，在 `run_migrations()` 前获取会话级锁可以干净工作，没有边界情况：

```
engine.connect() ──────► Connection
                          │
                          ├── pg_advisory_lock(key, schema_hash) ─── lock acquired
                          │
                          ├── run_migrations()
                          │     ├── BEGIN ── migration 1 ── COMMIT   (lock survives)
                          │     ├── BEGIN ── migration 2 ── COMMIT   (lock survives)
                          │     ├── migration N (CONCURRENTLY)       (lock survives)
                          │     ├── BEGIN ── migration N+1 ── COMMIT (lock survives)
                          │     └── ...
                          │
connection.close() ──────► lock released
```

CONCURRENTLY 问题消失。模式 3 中，`dbapi_conn.commit()` 提交共享外层事务并释放 xact 锁。模式 2 没有共享外层事务，每个迁移自有事务，会话级锁独立于全部事务。

<a id="what-changes"></a>

### 发生的变化

**回滚行为。**这是主要取舍。

```
Mode 3 (current — all-or-nothing):

  BEGIN
    migration 1 ── ok
    migration 2 ── ok
    migration 3 ── FAIL → ROLLBACK (all 3 rolled back, alembic_version unchanged)
  restart: runs all 3 again


Mode 2 (modified — partial progress):

  BEGIN ── migration 1 ── COMMIT (alembic_version updated, visible to others)
  BEGIN ── migration 2 ── COMMIT (alembic_version updated, visible to others)
  BEGIN ── migration 3 ── FAIL → ROLLBACK (only 3 rolled back)
  restart: resumes from migration 3
```

- **模式 3**：全有或全无。任意位置失败都撤销全部内容。干净，但重启时重复已成功步骤，存在浪费。
- **模式 2**：保留部分进度。Alembic 从失败步骤恢复。更高效，但步骤之间数据库可能处于部分迁移状态。

部分迁移可见是 Flyway、Prisma、Django 等多数工具的标准行为。它本身并不危险，每个步骤各自保持一致，但对已有 Phoenix 部署属于行为变化。

<a id="interaction-with-lock-approaches"></a>

### 与加锁方案的交互

| | 模式 3（当前） | 模式 2（修改后） |
|---|---|---|
| 事务级锁 | 整次运行持有，但被 CONCURRENTLY 破坏 | 不可用，第一步后释放 |
| 会话级锁 | 需要直连 URL；跨 CONCURRENTLY 保留 | 需要直连 URL；跨 CONCURRENTLY 保留；**最合适** |
| 无锁 | DDL 可通过崩溃重试恢复 | DDL 可通过崩溃重试恢复；保留部分进度 |

模式 2 使会话级锁成为自然且唯一可行的建议锁方案，更容易推理，从两种方案变为一种；代价是连接池后方用户需要 `PHOENIX_MIGRATION_DATABASE_URL`。

<a id="should-we-change-it"></a>

### 是否应该更改？

不应作为添加建议锁的一部分。无论是否加锁，env.py 模式都影响全部迁移的回滚语义、`alembic_version` 可见性和错误恢复。这是更广泛架构决策，应独立评估，加锁仅是输入因素，不是驱动原因。

未来若切换模式 2，会话级锁加 `PHOENIX_MIGRATION_DATABASE_URL` 成为明确选择：无 CONCURRENTLY 边界情况、无 T1/T2 拆分、无微妙事务交互。下文模式 3 中的事务级锁参考实现将不再适用。

---

<a id="industry-precedent"></a>

# 行业先例

使用建议锁串行化迁移是行业标准，分两类：

- **事务级**（`pg_advisory_xact_lock`）：在 `COMMIT`/`ROLLBACK` 时释放。可通过 PgBouncer 事务模式，因为锁生命周期包含于单事务，正好对应 PgBouncer 保证后端连接亲和性的窗口。等待副本会阻塞，而非反复崩溃，之后检查结构历史并跳过已完成步骤，行为清晰。
- **会话级**（`pg_advisory_lock`）：跨提交保留，连接关闭时释放。锁需要跨多个事务时必需，但不兼容 PgBouncer 事务模式，因为 `COMMIT` 会使 PgBouncer 重新分配后端。

<a id="why-session-level-is-the-industry-default-and-why-transaction-level-isnt"></a>

### 会话级锁为何是行业默认选择，而事务级不是

多数迁移工具选择会话级锁，原因有三：

1. **多事务架构。**Prisma 等工具在连接生命周期中执行结构探查、目标差异比较、应用 DDL、更新版本表和验证等多项操作，跨多个事务。事务级锁在首个 `COMMIT` 释放，剩余步骤不受保护；会话级锁跨 `COMMIT` 保留。

2. **不兼容 `CREATE INDEX CONCURRENTLY`。**该 DDL 语句无法在事务内运行，而 `pg_advisory_xact_lock` 按定义位于事务内，两者互斥。支持并发建索引的工具需要会话级锁，或在并发操作前释放锁。

3. **历史惯性和简单性。**会话级锁做法直接：获取一次，关闭连接释放。事务级锁要求全部受保护工作在单事务内，限制架构。多数工具选择更简单路径，并在外部解决 PgBouncer 问题，例如 Prisma 的 `directUrl`。

Flyway 是明显例外，它在 9.1.2 专为 PgBouncer 兼容性切换至事务级锁，详情见下文。

<a id="how-other-tools-handle-this"></a>

### 其他工具如何处理

- **Flyway**，已从源码验证，通过 `postgresql.transactional.lock=true` 默认使用事务级建议锁（`pg_try_advisory_xact_lock`）。它端到端控制自身事务生命周期，使锁和全部 DDL 位于同一事务，因此 PgBouncer 无需特殊连接配置。通过 `postgresql.transactional.lock=false` 显式启用会话级锁，用于无法在事务内运行的 `CREATE INDEX CONCURRENTLY`。
- **Prisma**，已从 `prisma-engines` 的 `postgres.rs` 第 367 行验证，使用会话级 `pg_advisory_lock(72707369)`，超时 10 秒。不显式解锁，连接释放时锁随之释放。Prisma 要求迁移使用独立 `directUrl` / `DIRECT_URL` 绕过事务模式连接池。用户可通过 `PRISMA_SCHEMA_DISABLE_ADVISORY_LOCK` 完全禁用加锁。
- **Liquibase**，已从文档验证，使用表锁（`DATABASECHANGELOGLOCK`）而非建议锁，可通过连接池。但 pod 在迁移中崩溃时，行会保持锁定，直到通过 `liquibase release-locks` 或手动 `UPDATE ... SET locked = 0` 清除。
- **Django**，已从文档验证，默认不为迁移加锁，依赖崩溃重试恢复。`django-pglock` 等社区包提供通用建议锁原语，不专用于迁移。它默认使用会话级锁，但文档警告 PgBouncer 风险，并提供 `xact=True` 事务级锁，作为连接池安全替代。

<a id="tradeoff-summary"></a>

### 取舍汇总

| | 会话级（`pg_advisory_lock`） | 事务级（`pg_advisory_xact_lock`） |
|---|---|---|
| 多事务工作流 | 可用，跨提交保留锁 | 不可用，首次提交释放锁 |
| `CREATE INDEX CONCURRENTLY` | 可用，锁覆盖事务外操作 | 不可用，无法在事务内运行 |
| PgBouncer 事务模式 | 不可用，锁孤留或被释放 | 可用，锁包含于事务窗口 |
| 简单性 | 获取一次，关闭连接释放 | 要求单事务架构 |
| 使用工具 | Prisma、Django 社区包 | Flyway，自 9.1.2 起默认 |

<a id="implication-for-phoenix"></a>

### 对 Phoenix 的意义

PR 遵循 Prisma 模式，选择会话级锁。获取锁后调用 `conn.commit()` 清除事务状态，让 Alembic 干净管理事务。会话级锁不受 `COMMIT`/`ROLLBACK` 影响，持续至会话结束。

```
engine.connect() ──────► Connection
                          │
                          ├── pg_advisory_lock(key) ─────── session lock acquired
                          ├── conn.commit() ─────────────── txn cleared (lock persists)
                          │
                          ├── command.upgrade() ──► env.py
                          │     connection.begin() ──► Transaction
                          │       ├── migration 1
                          │       ├── migration 2
                          │       ├── ...
                          │     transaction.commit()
                          │
connection.close() ──────► session lock released
```

这并非唯一选项。Phoenix env.py 将全部迁移包围于单个外层事务，参见 [Alembic 如何处理事务](#how-alembic-handles-transactions)。在该外层事务内获取事务级锁（`pg_advisory_xact_lock`），即可覆盖整次迁移，提交时自动释放，属于 Flyway 模式。可直接通过 PgBouncer，无需独立 `PHOENIX_MIGRATION_DATABASE_URL`。

若重新评估，先尝试事务级方案，它覆盖当前全部迁移，包括默认非并发模式的索引迁移，且对 PgBouncer 安全。唯一边界情况是用户显式开启 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true`，跳出事务并提前释放锁。此后回退为无锁，后续迁移依赖编写准则保证安全，完整分析参见 [CREATE INDEX CONCURRENTLY](#create-index-concurrently)。

---

<a id="reference-implementation"></a>

# 参考实现

若决定添加建议锁，在当前 env.py 模式 3 下，最实用方案是在既有外层事务中获取事务级锁，即 Flyway 模式。它避免上述会话级风险，无需额外配置即可通过 PgBouncer。

```
connection.begin() ──► Transaction
                        │
                        ├── pg_advisory_xact_lock(key, schema_hash) ── lock acquired
                        │
                        ├── migration 1 ─────────────────── protected
                        ├── migration 2 ─────────────────── protected
                        ├── ...
                        ├── migration M ─────────────────── protected
                        │
transaction.commit() ──► lock released, all migrations committed atomically
```

<a id="modified-run_migrations-in-envpy"></a>

### env.py 中修改后的 `run_migrations()`

```python
from zlib import crc32
from sqlalchemy import Connection, text

_MIGRATION_LOCK_KEY = 0x50485801  # arbitrary, unique to Phoenix


def run_migrations(connection: Connection) -> None:
    transaction = connection.begin()
    try:
        _acquire_migration_lock(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            transactional_ddl=True,
            transaction_per_migration=True,
        )
        context.run_migrations()
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()


def _acquire_migration_lock(connection: Connection) -> None:
    if connection.dialect.name != "postgresql":
        return
    schema = _get_schema() or "public"
    schema_hash = crc32(schema.encode("utf-8"))
    if schema_hash > 0x7FFFFFFF:
        schema_hash -= 0x100000000  # fit into int4
    connection.execute(
        text("SELECT pg_advisory_xact_lock(:key, :schema_hash)"),
        {"key": _MIGRATION_LOCK_KEY, "schema_hash": schema_hash},
    )
```

<a id="what-this-gets-right"></a>

### 正确之处

1. **对 PgBouncer 安全** — 锁生命周期包含于单事务，正好是 PgBouncer 保证后端亲和性的窗口，无需 `PHOENIX_MIGRATION_DATABASE_URL`。
2. **对 OOM-kill 安全** — 进程死亡时 PostgreSQL 回滚事务并立即释放锁，无需等待 TCP keepalive。
3. **Schema 作用域** — 双参数形式防止不同 schema 上的独立部署互相阻塞。
4. **SQLite 不执行操作** — 通过方言检查，在 SQLite 上完全跳过加锁。

<a id="where-it-falls-short"></a>

### 不足之处

迁移显式启用 `PHOENIX_MIGRATE_INDEX_CONCURRENTLY=true` 时，锁会被破坏。并发索引迁移调用 `dbapi_conn.commit()` 跳出事务，释放 `pg_advisory_xact_lock`，并提交全部先前迁移。此后锁完全消失，并发建索引和全部后续迁移回退为无锁行为；完整事务拆分图参见 [CREATE INDEX CONCURRENTLY](#create-index-concurrently)：

- 并发索引本身安全，`IF NOT EXISTS` 处理竞态。
- 后续 DDL 迁移可通过崩溃重试恢复，第二副本失败并重试。
- 后续针对已有表的非幂等 DML **不安全**，与完全无锁风险相同。

默认未显式启用 `CONCURRENTLY` 时，锁覆盖整次运行。但此出口的存在意味着锁只能尽力保护，不是保证。

<a id="alternative-session-level-lock--phoenix_migration_database_url"></a>

### 替代方案：会话级锁 + `PHOENIX_MIGRATION_DATABASE_URL`

直连并绕过连接池的会话级锁（`pg_advisory_lock`）具有事务级方案没有的优势：**可跨 `CONCURRENTLY` 保留**。锁位于连接级，`dbapi_conn.commit()` 不会释放它。无 T1/T2 拆分、无锁失效，完整覆盖全部迁移。

这是不同取舍，并非严格更差：

| | 事务级（上文） | 会话级 + 直连 URL |
|---|---|---|
| 显式启用 `CONCURRENTLY` | 失效，锁被释放 | 保留，继续持锁 |
| PgBouncer | 可用，无需配置 | 可用，直连 URL 绕过连接池 |
| OOM-kill | 安全，事务回滚、锁释放 | 阻塞至 TCP keepalive，RDS 约 6 分钟 |
| 配置负担 | 无 | 需要 `PHOENIX_MIGRATION_DATABASE_URL` |

直连无连接池时，OOM-kill 风险低于正文所述场景：其他副本仅通过直连等待 PostgreSQL，不会污染连接池后端，也不会造成集群级死锁，类似其他“进程持有资源时死亡”的场景。

若完整覆盖比零配置更重要，使用直连 URL 的会话级方案更强。

<a id="honest-assessment"></a>

### 如实评估

迁移编写准则，即 DML 与 DDL 配对、独立 DML 幂等，是所有场景的主要安全机制，无论采用哪种锁或不加锁，也无论是否使用 `CONCURRENTLY`。建议锁为常见情况增加纵深防御，但：

- 它解决当前并不存在的问题，没有迁移对已有表执行非幂等 DML。
- 事务级方案在 `CONCURRENTLY` 边界情况下失效，回退至相同编写准则。
- 会话级方案要求额外配置（`PHOENIX_MIGRATION_DATABASE_URL`），并暴露于 OOM-kill 风险。
- 两种方案都增加未来贡献者需要理解的代码复杂度。
- 相比运行时锁，代码评审更能可靠拦截危险迁移。

这些实现仅供未来认为纵深防御值得复杂度时参考，均不应预先发布。

---

<a id="schema-scoping"></a>

# Schema 作用域

PostgreSQL 建议锁作用于数据库，而非 schema。若两个独立 Phoenix 部署通过 `PHOENIX_DATABASE_SCHEMA` 在同一数据库使用不同 schema，简单单键 `pg_advisory_lock(key)` 会不必要地使两者串行，启动时互相阻塞迁移。

可使用双参数形式 `pg_advisory_lock(key, schema_hash)` 解决，第二参数使用 schema 名称的 `crc32`。
