<a id="design-proposal-read-replica-support-mvp"></a>

# 设计提案：只读副本支持（MVP）

<a id="problem"></a>

## 问题

Phoenix 目前使用同一个 PostgreSQL 引擎/连接池处理读取和写入。在高摄取负载下，读取密集型工作（项目页面聚合、标注名称扫描、分页和 span 树加载器）会与写入争用相同的连接池和主库资源。

用户也报告，大量拉取 span 的工作负载会降低摄取速度。这与繁重读取查询和写入路径之间争用共享连接池/主库的情况一致。

瓶颈并非经典的锁阻塞（`SELECT` 与 `INSERT`），而是：

- 连接池争用
- 主库 CPU/IO/WAL 争用
- 单节点缓存频繁更替

将只读流量路由到副本，可以隔离连接池并获得独立的缓冲区缓存，预计可降低负载下用户感知的延迟。

<a id="goals"></a>

## 目标

- 将可安全在副本执行的读取路由到只读副本。
- 所有写入均保留在主库。
- 保持未配置副本的部署向后兼容。
- 保持 SQLite 部署向后兼容（`db.read()` 和 `db()` 解析到同一个引擎）。

<a id="non-goals"></a>

## 非目标

- 本次变更不重写 SQL/查询逻辑。
- 不修改 schema。
- 不改变前端行为。
- Phoenix 不管理副本基础设施（创建、故障转移、WAL/复制槽调优）。
- 不尝试通过应用代码控制 PostgreSQL 复制内部机制。
- 不提供复制延迟监控、熔断器或客户端健康检查（由运维人员负责）。
- 不提供会话粘滞或写后固定主库（待证明确有必要后再做）。

<a id="scope-boundary-phoenix-as-db-client"></a>

## 范围边界（Phoenix 作为数据库客户端）

Phoenix 是主库/副本数据库的客户端，职责边界如下：

- **Phoenix 负责**：端点/会话路由（`read` 与 `write`）和可观测性。
- **运维人员负责**：副本创建、复制设置、延迟/复制槽/WAL 调优、故障转移编排、服务端只读强制约束以及副本健康监控。
- **约定**：运维人员应在副本角色或服务端设置 `default_transaction_read_only=on`，作为额外保护。

<a id="current-architecture"></a>

## 当前架构

<a id="dbsessionfactory"></a>

### `DbSessionFactory`

定义于 `src/phoenix/server/types.py`：

```python
class DbSessionFactory:
    def __init__(
        self,
        db: Callable[[Optional[asyncio.Lock]], AbstractAsyncContextManager[AsyncSession]],
        dialect: str,
    ):
        self._db = db
        self.dialect = SupportedSQLDialect(dialect)
        self.lock: Optional[asyncio.Lock] = None
        self.should_not_insert_or_update = False

    def __call__(self) -> AbstractAsyncContextManager[AsyncSession]:
        return self._db(self.lock)
```

<a id="session-factory-function-_db"></a>

### 会话工厂函数 `_db()`

定义于 `src/phoenix/server/app.py`：

```python
def _db(
    engine: AsyncEngine,
) -> Callable[[Optional[asyncio.Lock]], AbstractAsyncContextManager[AsyncSession]]:
    Session = async_sessionmaker(engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def factory(lock: Optional[asyncio.Lock] = None) -> AsyncIterator[AsyncSession]:
        async with contextlib.AsyncExitStack() as stack:
            if lock:
                await stack.enter_async_context(lock)
            yield await stack.enter_async_context(Session.begin())

    return factory
```

每个 `async with db() as session:` 块都是单个事务。`Session.begin()` 启动事务，此时从池中获取连接（asyncpg 在 `begin()` 时立即获取）。

<a id="construction-sites"></a>

### 构造位置

`DbSessionFactory` 在**两处**构造，而非一处：

1. **`src/phoenix/server/cli/commands/serve.py:257-266`** — 主 CLI 入口：
   ```python
   engine = create_engine(connection_str=db_connection_str, ...)
   shutdown_callbacks.extend(instrument_engine_if_enabled(engine))
   shutdown_callbacks.append(engine.dispose)
   factory = DbSessionFactory(db=_db(engine), dialect=engine.dialect.name)
   ```

2. **`src/phoenix/session/session.py:203-213`** — notebook/嵌入式入口：
   ```python
   engine = create_engine(connection_str=database_url, ...)
   shutdown_callbacks.extend(instrument_engine_if_enabled(engine))
   shutdown_callbacks.append(engine.dispose)
   factory = DbSessionFactory(db=_db(engine), dialect=engine.dialect.name)
   ```

两处都必须更新。

<a id="consumer-patterns"></a>

### 使用方模式

```
DbSessionFactory
├── Context.db              → GraphQL resolvers (reads + writes via info.context.db())
├── DataLoaders             → read-heavy path, all verified read-only (self._db())
├── BulkInserter            → writes (self._db())
├── DmlEventHandler         → write-driven invalidation + annotation lookups (self._db())
├── Facilitator             → startup writes and sync (self._db())
├── JwtStore/_Store         → auth-critical mixed reads/writes (self._db())
├── Daemons                 → experiment_runner/sweeper, retention, disk monitor, model store, ...
├── REST routers            → mixed by endpoint (request.app.state.db())
└── Subscriptions           → mixed read/write flows (info.context.db())
```

<a id="key-observations-from-code-review"></a>

### 代码审查的关键发现

- **所有 DataLoader 都是只读的。** `src/phoenix/server/api/dataloaders/` 中的全部 73 个 dataloader 只使用 `session.scalar()`、`session.scalars()`、`session.stream()` 和 `session.get()`，未发现写操作。每个加载器在 `__init__` 中接收 `DbSessionFactory`，存为 `self._db`，随后调用 `async with self._db() as session:`。

- **GraphQL 查询解析器是只读的。** `src/phoenix/server/api/queries.py` 和 `src/phoenix/server/api/types/` 中的所有类型解析器都委托给 dataloader，或执行只读查询。

- **GraphQL mutation 明确执行写入。** `src/phoenix/server/api/mutations/` 中的所有文件都使用 `session.add()`、`session.delete()`、`session.commit()` 或 `session.flush()`。

- **订阅在单个会话中混合读取与写入。** `src/phoenix/server/api/subscriptions.py` 在同一事务内先读后写（例如第 287-309 行为 playground 项目先检查后插入，第 388-499 行创建实验）。这些操作必须留在主库。

- **SQLite 锁仅在 SQLite 下设置**（`app.py` 的 lifespan 函数）。对于 PostgreSQL，`self.lock` 为 `None`，因此 `_db()` 中的锁路径不起作用。锁机制与副本路由没有交互。

- **`should_not_insert_or_update` 是写入协调标志**，在请求边界处检查（REST 身份验证守卫、GraphQL 权限、gRPC 拦截器）。它位于工厂上而非会话上，仅与写入路径有关，与副本路由互不相关。

- **schema 处理已内置于 ORM 元数据。** `src/phoenix/db/models.py:633-634` 设置 `MetaData(schema=get_env_database_schema())`。设置 `PHOENIX_SQL_DATABASE_SCHEMA` 后，所有 ORM 生成的 SQL 都使用完全限定的表名（`schema.table`）。副本引擎无需单独配置 `search_path`，ORM 已将 schema 嵌入每个查询。唯一调用 `SET search_path` 的位置是 `src/phoenix/db/migrations/env.py:99`，它只在迁移期间运行（仅主库）。

- **IAM 身份验证读取全局环境变量。** `aio_postgresql_engine()` 从全局配置调用 `get_env_postgres_use_aws_iam_auth()`。如果主库使用 IAM 身份验证，创建副本引擎时也会尝试使用相同 AWS 凭证进行 IAM 身份验证。

- **`/readyz` 检查主库健康状态。** `app.py:707-715` 通过 `request.app.state.db()`（即 `__call__()` → 主库）运行 `select(1)`。这是正确的，就绪状态应反映写入路径，无需修改。

<a id="aurora-write-forwarding-incompatibility"></a>

### 与 Aurora 写入转发不兼容

`internal_docs/vignettes/postgresql/aurora-write-forwarding-analysis.md` 中已有分析说明，Phoenix 与 Aurora 写入转发根本不兼容（批量摄取使用 SAVEPOINT，迁移使用 DDL）。只读副本 URL 必须指向标准流复制副本或 Aurora 读取端点，**不能**指向启用了写入转发的 Aurora 读取端点。配置指南应说明这一点。

<a id="proposed-architecture"></a>

## 提议架构

为 `DbSessionFactory` 增加 `read()` 方法和新构造函数。沿用相同的类、模块和导入。

```
DbSessionFactory
├── .__call__()  → primary engine (always, unchanged default)
├── .read()      → replica engine when configured, else primary
├── .lock        → asyncio.Lock (SQLite only)
├── .dialect     → SupportedSQLDialect
├── .should_not_insert_or_update → bool
```

<a id="design-decisions"></a>

### 设计决策

**`__call__()` 始终路由到主库。** 这是安全的默认行为。目前每个现有调用点都使用 `db()`，并期望具有写入能力。不增加可配置的默认路由；目标是通过 `db.read()` 显式标注读取路径，而非猜测。对尚未分类的调用点，`__call__()` 是兼容迁移的回退路径。

**未配置副本时，`read()` 回退到主库。** 因此，即使在没有副本的部署中，也可以立即用 `db.read()` 标注调用点。该标注是路由提示；没有副本时不产生额外效果。

**副本故障时不自动回退。** 如果配置了副本但无法访问，读取路径请求将报错失败。运维人员应修复副本，或删除环境变量并重启。参见下文“为什么不自动回退”。

**副本引擎不使用独立锁。** 锁仅用于 SQLite 并发控制。对于 PostgreSQL（唯一涉及副本的方言），锁始终为 `None`，无需新增锁协调。

**副本引擎跳过迁移。** 只有主引擎运行 Alembic 迁移。创建副本引擎时使用 `migrate=False`，避免在只读连接上尝试 DDL。

<a id="why-no-automatic-fallback"></a>

### 为什么不自动回退

我们考虑过在 `read()` 中捕获连接错误，并在主库重试。其复杂程度超过表面所见：

1. **错误发生时机不可预测。** 配合 asyncpg 使用时，SQLAlchemy 在 `Session.begin()` 立即获取连接，因此连接拒绝错误出现在进入上下文管理器时。但陈旧连接错误（连接池创建后副本宕机）可能在查询中途、会话已经让出后出现。回退包装无法在事务中途再次让出另一个会话。

2. **上下文管理器的让出语义。** `@asynccontextmanager` 只能 `yield` 一次。要回退，需要在 `__aenter__` 时（让出之前）捕获错误并替换底层会话。这能处理连接池为空和连接被拒绝，无法处理陈旧连接上的查询中途故障。

3. **静默回退掩盖基础设施问题。** 如果读取静默回退到主库，运维人员会在没有任何信号的情况下失去连接池隔离的收益。系统仍然“能用”，但副本没有工作，主库依旧过载。

4. **运维修复很简单。** 从环境中移除 `PHOENIX_SQL_DATABASE_READ_REPLICA_URL` 并重启，这是标准的基础设施操作手册步骤。

MVP 选择显式失败。如果运维人员需要自动回退，可在后续阶段为 `read()` 增加包装，仅处理 `__aenter__` 时的错误。

<a id="configuration"></a>

## 配置

新增一个环境变量：

```
PHOENIX_SQL_DATABASE_READ_REPLICA_URL=postgresql://user:pass@replica-host:5432/phoenix
```

设置该变量且主库方言为 PostgreSQL 时，创建第二个异步引擎进行读取路由。未设置时，`read()` 回退到主库。

<a id="naming-rationale"></a>

### 命名依据

`PHOENIX_SQL_DATABASE_` 前缀与现有的 `PHOENIX_SQL_DATABASE_URL` 和 `PHOENIX_SQL_DATABASE_SCHEMA` 一致。使用 `READ_REPLICA_URL` 而非 `REPLICA_URL`，以明确用途：用于读取路由，而非通用的次要数据库。

<a id="component-based-alternative"></a>

### 按连接组件配置的替代方案

Phoenix 也支持按组件配置 PostgreSQL（`PHOENIX_POSTGRES_HOST`、`PHOENIX_POSTGRES_PORT` 等）。为保持一致，可以增加 `PHOENIX_POSTGRES_REPLICA_HOST`、`PHOENIX_POSTGRES_REPLICA_PORT` 等。不过，MVP 使用单个 URL 变量已经足够。如果运维人员有需求，之后可以增加按组件配置。

<a id="iam-auth-interaction"></a>

### 与 IAM 身份验证的交互

`aio_postgresql_engine()` 从全局配置读取 `PHOENIX_POSTGRES_USE_AWS_IAM_AUTH`。启用 IAM 身份验证时，副本引擎也使用相同凭证进行 IAM 身份验证。对于 AWS Aurora/RDS，这是正确的，因为同一 IAM 策略授予写入和读取端点的访问权限，并且两个端点上都存在该 IAM 用户。非 AWS 环境应直接在副本 URL 中包含凭证。

<a id="what-we-do-not-add"></a>

### 不增加的配置

- 不增加 `DEFAULT_SESSION_ROUTE` 标志——`__call__()` 始终路由到主库。
- 不增加 `FALLBACK_TO_PRIMARY` 标志——MVP 不自动回退。
- 不增加 `MAX_LAG_SECONDS` 或健康检查配置——延迟监控由运维人员负责。
- 不增加 `POST_WRITE_STICKINESS_SECONDS`——待具体用例确实需要时再做。

增加配置会产生测试矩阵。每个标志都会使需要考虑的部署配置数量翻倍。MVP 选择安全的默认值，只有运维人员证明需要不同的行为时，才增加配置。

<a id="startup-validation"></a>

### 启动验证

启动时，如果设置了 `PHOENIX_SQL_DATABASE_READ_REPLICA_URL`：

- 验证 URL 能解析为 PostgreSQL 连接字符串（输入错误时立即失败）。
- 验证主库方言为 PostgreSQL（SQLite 的副本路由没有意义；记录警告并忽略该环境变量）。
- 尝试连接副本进行测试（`select(1)`），记录成功/失败。失败只记录警告，不是致命错误，因为运维人员可能在副本就绪前启动 Phoenix。

<a id="dbsessionfactory-changes"></a>

## `DbSessionFactory` 变更

增加 `read()` 并修改构造函数。沿用相同的类、模块和名称。

```python
class DbSessionFactory:
    def __init__(
        self,
        db: Callable[[Optional[asyncio.Lock]], AbstractAsyncContextManager[AsyncSession]],
        dialect: str,
        read_db: Optional[
            Callable[[Optional[asyncio.Lock]], AbstractAsyncContextManager[AsyncSession]]
        ] = None,
    ):
        self._db = db
        self._read_db = read_db or db
        self.dialect = SupportedSQLDialect(dialect)
        self.lock: Optional[asyncio.Lock] = None
        self.should_not_insert_or_update = False

    def __call__(self) -> AbstractAsyncContextManager[AsyncSession]:
        return self._db(self.lock)

    def read(self) -> AbstractAsyncContextManager[AsyncSession]:
        return self._read_db(self.lock)
```

<a id="what-changes"></a>

### 改动内容

- **构造函数：**`db` 参数不变；新增可选的 `read_db` 参数。只有两处构造位置（`serve.py`、`session.py`）调用该构造函数。
- **新方法：**配置副本时，`read()` 路由到副本引擎，否则路由到主库。
- **`__call__()` 不变。** `db()` 继续路由到主库。

<a id="what-doesnt-change"></a>

### 保持不变的内容

- 类名、模块、导入均相同。
- `read_db` 默认为 `db`，因此未配置副本时，`read()` 与 `__call__()` 完全相同。SQLite 部署不受影响。
- `.lock`、`.dialect`、`.should_not_insert_or_update` 均不变。

<a id="engine-wiring"></a>

## 引擎接入

在 `serve.py`（及 `session.py`）中，引擎创建从：

```python
engine = create_engine(connection_str=db_connection_str, migrate=True, ...)
shutdown_callbacks.extend(instrument_engine_if_enabled(engine))
shutdown_callbacks.append(engine.dispose)
factory = DbSessionFactory(db=_db(engine), dialect=engine.dialect.name)
```

改为：

```python
primary_engine = create_engine(connection_str=db_connection_str, migrate=True, ...)
shutdown_callbacks.extend(instrument_engine_if_enabled(primary_engine))
shutdown_callbacks.append(primary_engine.dispose)

replica_engine = None
replica_url = get_env_read_replica_url()  # new config function
if replica_url and SupportedSQLDialect(primary_engine.dialect.name) is SupportedSQLDialect.POSTGRESQL:
    replica_engine = create_engine(connection_str=replica_url, migrate=False, ...)
    shutdown_callbacks.extend(instrument_engine_if_enabled(replica_engine))
    shutdown_callbacks.append(replica_engine.dispose)

factory = DbSessionFactory(
    db=_db(primary_engine),
    read_db=_db(replica_engine) if replica_engine else None,
    dialect=primary_engine.dialect.name,
)
```

<a id="create_engine-with-migratefalse"></a>

### 使用 `migrate=False` 的 `create_engine`

当 `migrate=False` 时，`aio_postgresql_engine()`（`engines.py:201-202`）立即返回配置好的引擎，不创建迁移引擎，也不运行 Alembic。除此之外，该引擎与主引擎完全相同，包括连接参数、SSL 配置、JSON 序列化器和 IAM 身份验证处理。

<a id="schema-handling"></a>

### schema 处理

副本引擎无需特殊的 schema 配置。Phoenix 在 ORM 元数据层设置 schema（`models.py:634: MetaData(schema=get_env_database_schema())`），使 SQLAlchemy 在所有生成的 SQL 中使用完全限定的表名。唯一的 `SET search_path` 调用位于迁移执行器（`migrations/env.py:99`）中，而它不会在副本上运行（`migrate=False`）。

<a id="considerations"></a>

### 注意事项

- **关闭时必须释放两个引擎。** 将 `replica_engine.dispose` 与主引擎一起添加到关闭回调。lifespan 函数中现有的关闭模式（`app.py:695-697`）会遍历全部回调。

- **两个引擎都必须接入埋点。** `instrument_engine_if_enabled()`（`app.py:960+`）为引擎附加 OpenTelemetry 追踪。副本引擎也应调用它，使查询遥测覆盖两个连接池。返回的清理回调同样必须注册到关闭流程。

- **连接池容量。** 每个引擎拥有独立的 SQLAlchemy 连接池（默认：`QueuePool`，`pool_size=5`、`max_overflow=10`）。两个引擎默认最多共 30 个连接（每个引擎 15 个）。运维人员可以通过 URL 参数按引擎调整（例如 `?pool_size=10&max_overflow=20`）。文档应说明，总最大连接数 = 主库连接池 + 副本连接池。

- **`_db()` 工厂函数可以原样复用。** 它接收引擎，返回会话工厂可调用对象，无需修改。

- **`session.py`（notebook 入口）可能不需要副本支持。** notebook 入口用于本地开发（通常使用 SQLite）。但为保持一致，应接受相同的 `db`/`read_db` 构造参数。在 notebook 环境设置 `PHOENIX_SQL_DATABASE_READ_REPLICA_URL` 后便可工作；未设置则没有额外效果。

<a id="routing-policy"></a>

## 路由策略

基本规则：如果会话可能在事务的任何时刻修改数据，使用 `db()`（默认写入路径）。

<a id="what-makes-a-callsite-safe-for-dbread"></a>

### 调用点安全使用 `db.read()` 的条件

以下四个条件必须全部成立：

1. 整个 `async with db.read() as session:` 块只使用读操作：`session.scalar()`、`session.scalars()`、`session.stream()`、`session.get()`、`session.execute(select(...))`，以及执行只读 SQL 的 `session.connection().run_sync()`。
2. 不使用 ORM 修改方法：没有 `session.add()`、`session.add_all()`、`session.delete()`、`session.flush()`，也没有带脏状态的 `session.commit()`。
3. 块内调用的辅助函数不执行写入（例如 `insert_on_conflict`、upsert 辅助函数）。
4. 调用点可以容忍最终一致性（副本延迟通常不到一秒，但没有上限）。

<a id="what-must-stay-on-db-primary"></a>

### 必须保留在 `db()`（主库）的操作

- 所有 `INSERT`、`UPDATE`、`DELETE` 和 DDL。
- 所有 ORM 修改操作。
- 混合先读后写事务（例如 `subscriptions.py:287-309` 中的先检查后插入模式）。
- 身份验证/令牌路径——正确性要求主库一致性。
- 读取前一个请求刚写入的数据，且陈旧数据会造成用户可见错误的任何路径。
- `begin_nested()` / SAVEPOINT 用法（仅存在于写入路径：`bulk_inserter.py`、`insertion/types.py`、`jwt_store.py`、`experiment_mutations.py`）。

<a id="why-transport-method-is-insufficient"></a>

### 为什么不能只看传输方法

`POST /v1/spans` 是只读的（它是查询 DSL 端点）。`GET /oauth2/{idp_name}/tokens` 会执行写入。应按数据库行为分类，而非 HTTP 方法。

<a id="callsite-migration-what-changes-and-what-doesnt"></a>

## 调用点迁移：改动与保留内容

<a id="callsites-to-annotate-with-dbread-mvp-scope"></a>

### 使用 `db.read()` 标注的调用点（MVP 范围）

这些候选项价值最高、风险最低：查询量大、已验证只读，且可以容忍最终一致性。

<a id="graphql-dataloaders"></a>

#### GraphQL DataLoader

全部 73 个 dataloader 都已验证为只读。它们是流量最高的读取路径（为每个 GraphQL 字段解析执行批量查询）。

**当前接入方式：**在 `app.py:762+` 中，`get_context()` 将完整工厂传给每个 DataLoader：

```python
DataLoaders(
    span_by_id=SpanByIdDataLoader(db),
    project_by_name=ProjectByNameDataLoader(db),
    # ... 70+ more ...
)
```

每个加载器保存 `self._db = db`（类型为 `DbSessionFactory`），并调用 `async with self._db() as session:`。

**迁移方式：**每个加载器将内部调用从 `self._db()` 改为 `self._db.read()`：

```python
# Before (in each DataLoader's _load_fn):
async with self._db() as session:
    ...

# After:
async with self._db.read() as session:
    ...
```

**无需修改类型提示。** DataLoader 已将参数标注为 `db: DbSessionFactory`。该类现在具有 `read()`，因此调用 `self._db.read()` 是类型安全的。

**差异规模：**73 个加载器文件各修改一行（`self._db()` → `self._db.read()`），属于机械式查找替换。

<a id="graphql-query-resolvers"></a>

#### GraphQL 查询解析器

`src/phoenix/server/api/types/` 中的一些类型解析器直接调用 `info.context.db()`（不经过 DataLoader），应改为 `info.context.db.read()`。

查找方式：在 `src/phoenix/server/api/types/` 和 `src/phoenix/server/api/queries.py` 中搜索 `info.context.db()`。修改前应逐个验证调用点为只读。

<a id="rest-read-only-endpoints-tier-1"></a>

#### REST 只读端点（第 1 级）

每个端点都已通过代码审查验证为只读（不含 `session.add`、`session.delete`、`session.flush`、`session.commit` 或写入 SQL）：

| 端点 | 处理器位置 | 验证 |
|---|---|---|
| `POST /v1/spans`（查询 DSL） | `routers/v1/spans.py:459-529` | `session.run_sync(query)`——只读 pandas/Arrow |
| `GET /v1/projects/{id}/spans` | `routers/v1/spans.py:761-940` | `session.stream(stmt)`——游标分页 |
| `GET /v1/projects/{id}/spans/otlpv1` | `routers/v1/spans.py` | 与上面相同，采用 OTLP 格式 |
| `GET /v1/projects/{id}/traces` | `routers/v1/traces.py:91-249` | `session.scalars()`、`session.execute()` |
| `GET /v1/projects/{id}/sessions` | `routers/v1/sessions.py:278-354` | `session.scalars()` + 批量加载 trace |
| `GET /v1/sessions/{id}` | `routers/v1/sessions.py:145-166` | `session.get()`、`session.scalars()` |
| `GET /v1/projects/{id}/span_annotations` | `routers/v1/span_annotations.py` | 只读分页 |
| `GET /v1/projects/{id}/trace_annotations` | `routers/v1/trace_annotations.py` | 只读分页 |
| `GET /v1/projects/{id}/session_annotations` | `routers/v1/session_annotations.py` | 只读分页 |

这些端点使用 `request.app.state.db()`，改为 `request.app.state.db.read()`。

**注意：**`POST /v1/spans` 是价值最高的目标。Phoenix 客户端的 `get_spans_dataframe()` 由此端点支持，用户报告的主要争用来源正是通过该端点大量拉取 span 的工作负载。

<a id="background-daemon-single-candidate"></a>

#### 后台守护进程（单个候选项）

- `src/phoenix/server/daemons/generative_model_store.py`——定期读取参考数据。将 `self._db()` 改为 `self._db.read()`。该守护进程已经接收 `DbSessionFactory`，只需调用不同的方法。

<a id="callsites-that-stay-on-db-no-change-needed-for-mvp"></a>

### 保留在 `db()` 的调用点（MVP 无需改动）

这些位置目前使用路由到主库的 `db()`，无需改动：

- `src/phoenix/server/api/mutations/` 中的所有 GraphQL mutation
- `src/phoenix/server/api/subscriptions.py`（单个事务内混合读写）
- `src/phoenix/db/bulk_inserter.py`（使用 `begin_nested()` / SAVEPOINT）
- `src/phoenix/db/insertion/types.py`（使用 SAVEPOINT 回退的批量插入）
- `src/phoenix/db/facilitator.py`
- `src/phoenix/server/jwt_store.py`（使用 `begin_nested()`）
- `src/phoenix/server/dml_event_handler.py`
- `src/phoenix/server/daemons/experiment_runner.py`（认领/心跳/持久化，均为写入）
- `src/phoenix/server/daemons/experiment_sweeper.py`
- `src/phoenix/server/retention.py`
- `src/phoenix/server/daemons/span_cost_calculator.py`
- `src/phoenix/server/api/builtin_evaluator_sync.py`
- `src/phoenix/server/daemons/db_disk_usage_monitor.py`（控制阻止插入的标志，必须反映主库状态）
- `src/phoenix/server/app.py::Scaffolder`（启动时读写）
- `GET /readyz`（必须反映主库写入路径健康状态）
- `GET /oauth2/{idp_name}/tokens`（创建用户/令牌）
- 所有 `/auth/*` 端点

<a id="callsites-to-defer-classify-later-after-mvp"></a>

### 暂缓的调用点（MVP 后再分类）

这些操作是只读的，但流量较低，或紧邻更容易感知陈旧数据的写入流程：

- 数据集读取/导出端点（`/v1/datasets*`、CSV/JSONL 下载）
- 提示词/项目列表端点（`/v1/prompts*`、`/v1/projects*`）
- 实验读取/导出端点（`/v1/experiments*`）
- `GET /v1/users`、`GET /v1/user`
- `GET /v1/annotation_configs`、`GET /v1/annotation_configs/{id}`

无需急于处理，待 MVP 稳定后再迁移。

<a id="risks-and-mitigations"></a>

## 风险与缓解措施

<a id="risk-accidental-write-on-replica-session"></a>

### 风险：副本会话意外写入

标注为 `db.read()` 却实际执行写入的调用点，会在运行时收到 PostgreSQL 只读事务错误（如果运维人员在副本上设置了 `default_transaction_read_only=on`），或来自流复制副本自身的复制冲突/错误。

**缓解措施（纵深防御）：**
1. **代码审查**——全部第 1 级调用点均已验证为只读（参见上表）。
2. **写入路径检查**——CI grep 检查会标记使用 `db.read()` 的文件中的写入模式。
3. **运维配置**——副本角色/服务端的 `default_transaction_read_only=on` 提供数据库层强制约束。这是最强的保护措施，可捕获代码审查和静态检查无法发现的错误路由。

**剩余风险：**如果运维人员未在可写备用库上设置只读模式，而 Phoenix 错误路由了写入，该写入可能在备用库成功。对标准流复制副本而言，这会造成复制冲突（副本会被提升为独立实例，或拒绝该写入）。Aurora 读取端点默认拒绝写入，除非显式启用写入转发。风险较低，但应记录在文档中。

<a id="risk-replica-unavailable"></a>

### 风险：副本不可用

副本引擎的连接池无法连接，或返回已失效连接。

**行为：**读取路径请求返回 500 错误，写入路径请求不受影响。

**运维修复：**
1. 修复副本（重启、检查复制延迟、检查网络）。
2. 或移除 `PHOENIX_SQL_DATABASE_READ_REPLICA_URL` 并重启 Phoenix，将所有读取路由到主库。

**为什么不自动回退：**参见上文“为什么不自动回退”。自动回退复杂且会掩盖基础设施问题。如果运维人员证明确有需求，未来阶段可能增加主动启用的回退。

<a id="risk-stale-reads-cause-user-visible-confusion"></a>

### 风险：陈旧读取造成用户困惑

用户创建项目后立即进入项目页面，但由于副本尚未同步，项目没有出现。

**评估：**MVP 通过限定范围缓解此风险。第 1 级涵盖批量数据获取（span、trace、session），其中不到一秒的陈旧通常不可感知，因为用户查询的是历史数据，而非刚创建的数据。风险最高的流程（项目创建、标注创建、实验创建）在 MVP 中不会路由到副本。如果第 2 级流程中的陈旧数据成为问题，届时可以增加请求级粘滞，但不应凭设想提前实现。

<a id="risk-mixed-readwrite-transaction-misclassified"></a>

### 风险：混合读写事务分类错误

目前只读的调用点，未来可能在某个 PR 中加入写入，而作者并不知道它位于读取路径。

**缓解措施：**
1. **CI 静态检查**——基于 grep 的检查会标记使用 `db.read()` 的文件/函数中的写入模式（`session.add`、`session.delete`、`session.flush`、`session.commit`、`insert(`、`update(`、`delete(`）。使用简单 shell 脚本，不开发自定义静态分析器，以低成本捕获常见情况。
2. **显式调用点信号**——读取代码使用 `db.read()`，写入代码使用 `db()`。开发者向 DataLoader 加入写入时，会看到 `self._db.read()`，理解该会话走读取路由。`.read()` 调用是代码审查中可见的标记。
3. **运行时失败**——如果副本设置了 `default_transaction_read_only=on`，写入会立即失败并给出明确错误，不会静默成功。

<a id="risk-connection-pool-sizing"></a>

### 风险：连接池容量

两个引擎意味着两个连接池。默认总最大连接数 = 30（每个引擎 15：`pool_size=5` + `max_overflow=10`）。

**评估：**这对大多数部署没有问题。文档应说明，运维人员需要设置副本的 `max_connections`，以容纳额外连接池。无需修改应用代码，即可通过 URL 查询参数按引擎调整连接池参数。

<a id="risk-sessionpy-notebook-entrypoint-divergence"></a>

### 风险：`session.py`（notebook）入口分化

notebook 入口的引擎设置与 CLI 入口对应。如果只更新一处，构造函数签名不匹配会造成运行时错误。

**缓解措施：**第 1 阶段更新两个位置，测试套件覆盖两个入口。

<a id="migration-plan"></a>

## 迁移计划

<a id="phase-1-add-api-surface-no-routing-change"></a>

### 第 1 阶段：增加 API 接口（不改变路由）

1. 更新 `src/phoenix/server/types.py` 中的 `DbSessionFactory`：为构造函数增加可选 `read_db` 参数，增加 `read()` 方法。
2. 更新两处构造位置（`serve.py`、`session.py`），配置副本时传入 `read_db=...`。
4. 存在 `PHOENIX_SQL_DATABASE_READ_REPLICA_URL` 时创建副本引擎。
5. 为副本引擎接入埋点，并注册释放回调。
6. 增加启动验证（URL 解析检查、方言检查、可选测试连接）。
7. 保持 `__call__()` 路由到主库。`read()` 已存在，但尚无调用方。所有行为不变。
8. 按现有环境变量惯例，在 `config.py` 中增加带文档字符串的 `get_env_read_replica_url()`。
9. 类中已有 `should_not_insert_or_update`，无需修改使用方。

**验证：**全部现有测试通过。尚无调用点使用 `read()`。副本引擎存在但未使用。

<a id="phase-2-annotate-tier-1-read-paths"></a>

### 第 2 阶段：标注第 1 级读取路径

1. 更新 DataLoader 的 `_load_fn` 方法，调用 `self._db.read()`，替代 `self._db()`。
2. 将调用 `info.context.db()` 的 GraphQL 类型解析器改为调用 `info.context.db.read()`。
3. 更新第 1 级 REST 端点，使用 `request.app.state.db.read()`。
4. 更新 `generative_model_store.py`，使用 `self._db.read()`。
5. 增加会话路由计数器指标（读取与写入）。

**验证：**路由逻辑单元测试通过，写入路径检查通过。手动测试确认，第 1 级端点在配置副本 URL 时能够端到端工作。

<a id="phase-3-stabilize-and-extend"></a>

### 第 3 阶段：稳定并扩展

1. 在生产部署中监控读写路由指标。
2. 根据运维人员反馈迁移第 2 级端点。
3. 仅在具体生产问题要求时，才增加配置（严格失败模式、自动回退、粘滞）。

<a id="gate-between-phase-1-and-phase-2"></a>

### 第 1 阶段与第 2 阶段之间的准入条件

在生产启用读取路由前：
- `DbSessionFactory` 路由逻辑单元测试通过。
- 写入路径检查通过（使用 `.read()` 的文件中没有写入模式）。
- 人工审查确认第 1 级调用点没有写操作（已完成，参见验证表）。
- 手动测试：启动 Phoenix，将副本 URL 指向有效只读端点；确认第 1 级查询成功，写入路径不受影响。
- 手动测试：启动 Phoenix，将副本 URL 指向不可访问主机；确认读取路径失败并给出明确错误，写入路径不受影响。

<a id="testing-strategy"></a>

## 测试策略

<a id="unit-tests"></a>

### 单元测试

- 同时具有两个引擎的 `DbSessionFactory`：`read()` 返回副本会话，`__call__()` 返回主库会话。
- `read_db=None` 的 `DbSessionFactory`：`read()` 回退到主库（与 `__call__()` 使用相同会话）。
- 无论 `read_db` 为何，`__call__()` 始终返回主库会话。
- `read()` 方法在同时具有两个引擎以及 `read_db=None` 回退时均正常工作。

<a id="write-path-lint"></a>

### 写入路径检查

一个执行以下步骤的 CI 脚本：

1. 识别包含 `.read()` 会话调用的文件（例如 `self._db.read()`, `db.read()`, `request.app.state.db.read()`）。
2. 在这些文件中搜索写入模式： `session\.add`, `session\.delete`, `session\.flush`, `\.commit\(`, `\binsert\(`, `\bupdate\(`, `\bdelete\(`.
3. 发现任何匹配项便失败。

这无法捕获经由辅助函数执行的写入，但能以低成本发现常见模式。

<a id="why-no-ci-integration-tests-for-routing"></a>

### 为什么不为路由编写 CI 集成测试

现有集成测试基础设施为每个测试包使用随机 schema、16 个并行工作进程，以及硬编码凭证（`tests/integration/conftest.py:88`）。增加只读数据库角色，需要在迁移完成后、首次读取查询前，动态授予每个 schema 的权限；对于 MVP 范围，这涉及不小的 fixture 改动。

**接受的风险：**没有针对只读数据库运行 `db.read()` 路径的集成测试时，分类错误的调用点（尽管经过审查，实际仍会写入）只有在运维人员部署配置了副本的 Phoenix 时才会失败。受影响端点将在生产返回 500 错误，直到该调用点重新归类为 `db()`。风险仅限第 1 级端点，它们均已验证为结构简单的只读查询（带分页的 SELECT，没有条件写入或辅助函数副作用）。

**接受原因：**另一种方案（改造测试基础设施）与风险不成比例。更强的保护是副本上的 `default_transaction_read_only=on`，这是 Postgres 层的强制约束，会拒绝任何写入并返回 `ERROR: cannot execute INSERT in a read-only transaction`。它能在生产中立即捕获错误路由并给出明确错误，也覆盖 CI 无法发现的情况（例如动态分派或辅助函数中的写入）。我们在运维文档中强烈建议此设置。

如果实践中出现错误路由，可在之后增加路由集成测试。

<a id="observability-mvp"></a>

## 可观测性（MVP）

- **会话路由计数器：**每次调用 `db.read()` 或 `db()` 时递增 Prometheus 计数器，并按路由标记。这让运维人员了解主库与副本之间的流量分布。
- **启动结构化日志：**创建副本引擎时，以 INFO 级别记录副本引擎 URL（隐藏密码），让运维人员确认配置。
- **标准 SQLAlchemy 连接池指标：**如果两个引擎都调用 `instrument_engine_if_enabled`，现有池遥测（取用时间、池大小、溢出）会自动覆盖副本连接池。

MVP 后再做：按路由区分的端点延迟直方图、回退计数器（增加回退后）、延迟跟踪。

<a id="open-questions"></a>

## 待解问题

1. 最终是否应在副本故障时提供自动回退主库？如果提供，应主动启用还是默认启用？
2. 是否应增加按组件配置副本（`PHOENIX_POSTGRES_REPLICA_HOST` 等），以与主库配置一致？
3. 写入路径检查应作为 pre-commit 钩子，还是仅作为 CI 检查？

<a id="what-this-does-not-change"></a>

## 本提案不改变的内容

- 不改变查询语义。
- 不修改 schema。
- 不改变 SQLite 行为（`db.read()` 和 `db()` 解析到相同引擎）。
- 不改变 `should_not_insert_or_update` 行为（写入协调标志，与副本路由互不相关）。
- 不改变 `lock` 机制（仅 SQLite 使用；副本仅适用于 PostgreSQL）。
- 不改变 `/readyz`（已经通过 `__call__()` 检查主库）。
- 不改变 gRPC 摄取路径（全部写入，全部在主库）。
