<a id="aurora-replica-write-forwarding-compatibility-analysis-for-phoenix"></a>

# Aurora 副本写转发：Phoenix 兼容性分析

<a id="summary"></a>

## 摘要

Aurora PostgreSQL 的[本地写转发](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-postgresql-write-forwarding-understanding.html)允许只读副本将写操作转发至写入实例。**Phoenix 从根本上不兼容此功能。**Phoenix 运行时代码和迁移均依赖 Aurora 写转发明确不支持的 SQL 功能。

若 Phoenix 连接至启用写转发的读取端点，会在 span 接收和迁移时失败：前者因 SAVEPOINT，是最频繁路径；后者在启动时执行 DDL。

**解决方案：**将 Phoenix 直接连接至 Aurora **写入端点**。写转发适用于只读副本偶尔执行轻量 DML，不适合作为主要应用工作负载。

---

<a id="what-aurora-write-forwarding-does-not-support"></a>

## Aurora 写转发不支持的功能

根据 [AWS 文档](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-postgresql-write-forwarding-limitations.html)，写转发**不支持**以下 SQL 功能：

| 类别 | 不支持的操作 |
|---|---|
| **DDL** | CREATE、ALTER、DROP，所有对象 |
| **SAVEPOINT** | 包括 PL/pgSQL 异常处理中的隐式 SAVEPOINT |
| **序列** | `nextval()`、`setval()` |
| **GRANT / REVOKE** | 全部权限管理 |
| **LOCK** | 显式表锁 |
| **TRUNCATE** | 截断表 |
| **COPY** | 批量数据加载 |
| **游标** | 使用写转发前必须关闭 |
| **SELECT INTO** | 从查询创建表 |
| **两阶段提交** | PREPARE TRANSACTION、COMMIT PREPARED、ROLLBACK PREPARED |
| **用户自定义函数/过程** | 所有 UDF 和存储过程 |
| **LISTEN / NOTIFY** | 发布订阅通知 |
| **VACUUM / ANALYZE / CLUSTER** | 维护操作 |

写转发**仅**支持基本 DML（`INSERT`、`UPDATE`、`DELETE`）、`SELECT FOR UPDATE/SHARE`、`EXPLAIN` 和 `PREPARE`/`EXECUTE`。

---

<a id="where-phoenix-hits-these-limitations"></a>

## Phoenix 遇到这些限制的位置

<a id="1-savepoint--span-ingestion-evaluations-jwt-refresh-runtime"></a>

### 1. SAVEPOINT — span 接收、评估、JWT 刷新（运行时）

Phoenix 在最频繁的代码路径广泛使用 `session.begin_nested()`，在 PostgreSQL 层发出 `SAVEPOINT` / `RELEASE SAVEPOINT`：

**`src/phoenix/db/bulk_inserter.py`** — 主要 span/追踪接收路径：

```python
async with session.begin_nested():  # ← SAVEPOINT
    await op(session)
```

```python
async with session.begin_nested():  # ← SAVEPOINT
    result = await insert_span(session, span, project_name)
```

```python
async with session.begin_nested():  # ← SAVEPOINT
    await insert_evaluation(session, evaluation)
```

**`src/phoenix/db/insertion/types.py`** — 批量插入与逐条回退：

```python
async with session.begin_nested():  # ← SAVEPOINT (bulk attempt)
    events.extend(await self._events(session, *(p.item for p in parcels)))
# on failure, retries individually:
for p in parcels:
    async with session.begin_nested():  # ← SAVEPOINT (individual retry)
        events.extend(await self._events(session, p.item))
```

**`src/phoenix/server/jwt_store.py`** — token 刷新：

```python
async with session.begin_nested():       # ← SAVEPOINT
    await self._delete_expired_tokens(session)
async with session.begin_nested():       # ← SAVEPOINT
    async for record, role in await session.stream(self._update_stmt):
```

**`src/phoenix/server/api/mutations/experiment_mutations.py`** — 删除实验：

```python
savepoint = await session.begin_nested()  # ← SAVEPOINT
```

**影响：**每次 span 接收、评估记录、JWT 刷新和实验删除都会失败。这不是边界情况，而是每次请求的默认行为。

**Phoenix 使用保存点的原因：**`begin_nested()` 模式允许捕获并重试单条记录失败，例如约束违反或序列化错误，而无需中止整个外层事务。批量插入器据此在批量失败时回退为逐条插入。没有保存点，一个错误 span 就会回滚整个批次。

<a id="2-ddl--all-migrations-startup"></a>

### 2. DDL — 全部迁移（启动时）

Phoenix 迁移大量使用 DDL。每个迁移都会创建表、添加列、创建索引或修改约束。全新数据库的迁移日志显示 100% 为 DDL：

```
CREATE TABLE alembic_version (...)
CREATE TABLE projects (...)
CREATE TABLE traces (...)
CREATE TABLE spans (...)
ALTER TABLE spans ADD COLUMN ...
CREATE INDEX ix_spans_session_id ...
```

**影响：**存在待运行迁移且连接通过写转发读取端点时，Phoenix 无法启动。全新数据库第一步 `CREATE TABLE alembic_version` 就会失败。已有数据库仅在结构已达 head 时启动成功，任何待执行迁移均会失败。

<a id="3-sequences--nextval--setval-ambiguous"></a>

### 3. 序列 — `nextval()` / `setval()`（存在歧义）

AWS 限制页面将“序列更新：`nextval()`、`setval()`”列为不支持。Phoenix 几乎所有表均使用 `SERIAL` 主键，而 `SERIAL` 是 `DEFAULT nextval('tablename_id_seq')` 的语法糖。

```sql
-- What Phoenix's CREATE TABLE produces:
id SERIAL NOT NULL
-- Which PostgreSQL expands to:
id integer NOT NULL DEFAULT nextval('projects_id_seq')
```

但 **AWS 文档中此限制范围存在歧义**，有两种解释：

- **（a）仅独立调用：**不支持从读取会话直接发出 `SELECT nextval('my_seq')` 或 `SELECT setval('my_seq', 100)`，但通过 `DEFAULT` 值触发 `nextval()` 的 `INSERT` 正常，因为 INSERT 转发至写入实例，在本地计算默认值。
- **（b）任何触发 nextval() 的 SQL：**包括向 SERIAL 列 INSERT 时的隐式调用。

解释（a）更可能，因为：
- `INSERT` 明确列为支持的 DML。
- 文档说明“整个语句被转发至写入数据库实例并在那里运行”，写入实例会在自身序列上计算 `nextval()`。
- 若（b）成立，此功能对几乎所有实际 PostgreSQL 应用均不可用，与 AWS 所述“读密集、偶尔需要写入的工作负载”相矛盾。

**影响：**运行时 INSERT 很可能不受影响，即解释 a。但尚未实测。若客户在 SERIAL 表上遭遇 INSERT 失败，则可证实解释 b。

<a id="4-other-limitations-to-be-aware-of"></a>

### 4. 其他需要注意的限制

- **不兼容 RDS Proxy**：根据 AWS 文档，Aurora 写转发不支持 RDS Proxy，客户不能同时使用两者。
- **LOCK 语句**：建议锁（`pg_advisory_lock` / `pg_advisory_xact_lock`）无法通过写转发工作。仅在未来使用建议锁串行化迁移时相关，参见 `internal_docs/vignettes/postgres/advisory-lock-analysis.md`。

---

<a id="could-savepoints-be-removed"></a>

## 能否移除 SAVEPOINT？

在 PostgreSQL 中，事务内任何语句失败后，事务进入**已中止状态**，后续语句均报 `current transaction is aborted, commands ignored until end of transaction block`。仅可通过 `ROLLBACK` 丢弃全部内容，或 `ROLLBACK TO SAVEPOINT` 仅丢弃失败部分恢复。这是 PostgreSQL 基础机制，不是应用选择。

<a id="what-the-savepoints-protect"></a>

### SAVEPOINT 保护的内容

| 调用位置 | 模式 | 缺失时的失败 |
|---|---|---|
| `bulk_inserter.py`，span | 每次 span 插入一个保存点 | 一个错误 span 使批次剩余全部 span 失败 |
| `bulk_inserter.py`，评估 | 每次评估一个保存点 | 一个错误评估使剩余全部评估失败 |
| `insertion/types.py` | 尝试批量 → 回退逐条 | 批量失败后事务已中止，无法逐条重试 |
| `jwt_store.py` | 删除和读取使用独立保存点 | `_delete_expired_tokens` 失败会阻止读取 token |
| `experiment_mutations.py` | 用保存点包围 DELETE...RETURNING | 发现未知 ID 时无法回滚删除 |

<a id="possible-alternatives-with-tradeoffs"></a>

### 可选替代方案及取舍

1. **每个 span 独立事务。**将 `begin_nested()` 替换为每个 span 独立 `async with self._db() as session:`，完全消除保存点。但 N 个独立事务比含 N 个保存点的单事务需要更多往返和开销。批量插入器每轮处理数百 span，可能造成明显性能回退。

2. **更广泛使用 `ON CONFLICT`。**若主要失败为约束违反，例如重复键、外键违反，`INSERT ... ON CONFLICT DO NOTHING` 可直接避免错误，无需保存点。无法处理全部错误类型，例如序列化失败和数据类型错误，但可减少常见情况的保存点使用。需要审计每条插入路径，了解实际错误。

3. **插入前预校验数据。**在错误 span/评估到达数据库前过滤明显问题。限制相同，无法预测竞态和序列化错误等所有失败。

4. **针对 `jwt_store.py`** — 两个保存点很可能可改为独立事务。先删除再读取似乎不要求原子性；删除失败后可跳过读取，在下个周期重试。

<a id="bottom-line"></a>

### 结论

部分保存点可以减少，例如 jwt_store 和更广泛的 ON CONFLICT，但批量插入器每 span 一个保存点是可靠数据接收的正确模式，无法在不损失性能或可靠性的前提下移除。即使移除全部 SAVEPOINT，迁移 DDL 仍不受支持，客户仍需连接写入端点。

<a id="why-this-isnt-fixable-at-the-application-level"></a>

## 为什么无法在应用层修复

1. **保存点**是可靠批量接收的正确模式，参见上文。替代方案存在，但牺牲性能或可靠性。
2. **DDL**是数据库迁移的固有部分，没有避开 DDL 的迁移工具。
3. **单连接字符串。**Phoenix 使用同一个 `PHOENIX_SQL_DATABASE_URL` 进行运行时查询和迁移。即使运行时移除 SAVEPOINT，迁移仍需写入端点。支持分流，即迁移至写入实例、运行时至启用写转发的读取实例，需要第二个连接字符串和显著架构变更，收益不足以匹配成本，因为直连写入实例可彻底解决问题。

---

<a id="recommendation"></a>

## 建议

**将 Phoenix 直接连接至 Aurora 写入端点。**这是唯一受支持配置。

```
# Correct: writer endpoint
PHOENIX_SQL_DATABASE_URL=postgresql://user:pass@my-cluster.cluster-xxxx.us-east-1.rds.amazonaws.com:5432/phoenix

# Incorrect: reader endpoint with write forwarding
PHOENIX_SQL_DATABASE_URL=postgresql://user:pass@my-cluster.cluster-ro-xxxx.us-east-1.rds.amazonaws.com:5432/phoenix
```

Aurora 写转发面向只读副本偶尔执行简单 DML 的应用，例如读密集报表服务更新“last_seen”时间戳。它既不是为使用 DDL 和保存点的主要应用负载设计，也无法支持此类负载。

若目标是读取扩展，标准 Aurora 模式为：
- Phoenix 使用**写入端点**，处理所有写入和要求强一致性的读取
- 独立只读报表、分析负载使用**读取端点**，例如查询追踪的 Grafana 仪表盘

Phoenix 自身不支持读写分流，全部查询经配置的 `PHOENIX_SQL_DATABASE_URL`，因此将其指向读取端点没有收益。

---

<a id="aurora-product-disambiguation"></a>

## Aurora 产品区分

Amazon 在 Aurora 品牌下提供多种兼容 PostgreSQL 的产品。本分析专门针对启用本地写转发的 **Aurora PostgreSQL**。具体如下：

| 产品 | 写转发 | 是否受本分析影响 |
|---|---|---|
| **Aurora PostgreSQL**，标准版 | 可选功能，默认关闭 | 是，启用写转发时 |
| **Aurora PostgreSQL Limitless Database** | 不适用，分布式写入 | 否，架构完全不同 |
| **Aurora DSQL** | 不适用，无服务器分布式 SQL | 需单独考虑兼容性，不支持 PostgreSQL 扩展，事务 DDL 有限 |

若客户使用标准 Aurora PostgreSQL，且未显式启用 `EnableLocalWriteForwarding`，则写转发关闭，本分析不适用，其问题可能有其他根因。
