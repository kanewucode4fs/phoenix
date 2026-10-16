<a id="design-mcp-analytics-sql-surface"></a>
# 设计：MCP 分析 SQL 接口

<a id="problem"></a>
## 问题

Phoenix 通过 GraphQL API 和 REST API 暴露数据，两者只能回答固定问题。Agent 若被问到没人预料的分析问题——“本周该项目中哪个模型的 p95 延迟最差”“哪些提示词产生最多重试”——便无法直接得到答案。它可以分页读取 span 自行聚合，但要付出大量往返请求和相应上下文成本，或者只能放弃。

数据库能够直接回答这些问题。缺少的是让 Agent 提问的方式，同时不赋予它读取不该查看的表、运行永不结束的语句，或返回超出上下文窗口数据的能力。

<a id="goals"></a>
## 目标

- 让 Agent 用 SQL 表达分析问题并获得答案。
- 限制单条语句能读取的数据、消耗的资源和返回的内容。
- 充分描述 schema，使有能力的模型第一次就能写出正确 SQL。
- 让描述足够精简，避免 schema 发现占据调用方 token 预算的大部分。

<a id="non-goals"></a>
## 非目标

- **不构成保密边界。**见[威胁模型](#threat-model)。
- 不支持写入、DDL 或事务控制。
- 不支持跨数据库或联合查询。
- 除引擎本身的优化外，不代表调用方优化查询。
- 不缓存结果。
- 不支持存储或命名查询。

<a id="correctness-who-authored-the-behaviour"></a>
## 正确性：行为由谁定义

此接口的正确性问题几乎总以同样形式出现：调用方得到意外结果，或两个后端对同一语句给出不同答案，需要判断是否为缺陷。一个问题可以定论：产生结果的行为由谁定义。本接口定义的行为由我们保证正确；引擎定义的行为属于引擎，调用方有权依赖其文档。

|  | 本接口定义的行为 | 引擎定义的行为 |
|---|---|---|
| **语句的含义** | 我们改变了含义，因此由我们修复 | 引擎存在差异，因此原样传递差异 |
| **可使用的能力** | 概念由我们定义，因此两后端必须一致 | 能力不同，因此能运行的后端允许，其他后端拒绝并提供可行写法 |

以下四条规则都是对该问题的应用，每条附有它所裁决的案例。

- **答案必须回答原本提出的问题。**可以自由重写语句——展开星号、替换派生列、注入限制——但不得使结果表达不同于调用方 SQL 的含义。*案例：*SQLGlot 将调用方的 `json_extract` 渲染为 `->`，返回 JSON 文本而非值，导致 `MAX` 按字典序比较。是我们的流水线改变了含义，因此由我们修复。
- **本接口创造的概念必须只有一种含义。**`latency_ms` 和 `graphql_node_id` 在别处不存在，没有规范定义它们，包外也无法检查。*案例：*`latency_ms` 在每个后端计算不同数字。它按定义属于我们的责任，因为我们创造的概念有两个实现，除相互一致外没有其他依据。
- **引擎行为原样传递。***案例：*`->>` 在 SQLite 返回带类型的值，在 PostgreSQL 返回文本，因此对数值 JSON 路径执行 `max`，一个返回 `130000`，另一个返回 `'9'`。两个引擎都符合规范，因此我们既不调和也不拒绝；结果注记会在影响排序的提取未强制转换时警告。
- **能力可以不同，但拒绝必须能指导修正。***案例：*SQLite 语法没有 `percentile_cont(...) WITHIN GROUP`。缺口属于引擎，因此 PostgreSQL 允许该结构，SQLite 拒绝并在消息中指出 `percentile(x, p)`。

<a id="threat-model"></a>
## 威胁模型

这个决定最深刻地影响其余设计，而代码最初对此表述错误。

**任何能访问 MCP 挂载点的调用方都可使用此接口。**它读取遥测、数据集和实验。Phoenix 已允许任何已认证用户通过 GraphQL 读取全部这些数据：恰好只有四个查询带 `IsAdmin`——`users`、`user_api_keys`、`oauth2_grants`、`system_api_keys`——这些表都不在此允许列表中；而 `projects` 及其可到达的全部内容都没有权限类。

因此，之前的 ADMIN/SYSTEM 检查*对这些数据比旁边的 API 更严格*，禁止 SQL 读取同一调用方能用 GraphQL 获取的数据。该检查已移除。

约束此接口的是**能力，而非身份**：

| 限制项 | 值 |
|---|---|
| 语句 | 一条只读语句：`SELECT`、`UNION`、`INTERSECT`、`EXCEPT` |
| 行数 | 默认 500，最大 5000 |
| 字节 | 每行 256 KiB，每响应 4 MiB |
| 截止时间 | 30 s（PostgreSQL 使用 `statement_timeout`，SQLite 使用进度处理器） |
| 并发 | PostgreSQL 4 个并发，SQLite 1 个；队列深度 8 |

此设计防御的对手是**困惑或被引导的模型**，而非企图获取其他途径无法获得数据的恶意用户。以上每项控制都限制影响范围，没有一项用于限制调用方无法从其他地方取得的信息。

由此产生两个有意的结果：

- **表是数据边界。**允许列表中表的每个物理列都可查询；通过不把某表加入允许列表，排除其数据。见[物理 schema 与筛选配置](#decision-physical-schema-comes-from-packaged-ddl-curation-from-typed-python)。
- **争用是剩余风险。**SQLite 执行宽度为 1，因此一个慢查询会让其余分析请求串行等待直至截止时间。许可在解析前获取，所以接纳和重写也要等待。行数、字节和截止时间限制每个查询，但不限制争用。

本设计**不**处理另一问题：`spans.attributes` 和 `spans.events` 包含被追踪应用写入的文本，通常来自该应用的最终用户。结果返回给模型，而同一 MCP 服务端中该模型拥有被标为破坏性的工具。此处没有将返回行标记为不可信内容。这一缺口记录在[开放问题](#open-questions)。

<a id="architecture"></a>
## 架构

语句经过六个阶段：一个负责解析，两个是策略门禁，一个负责转换，一个生成实际执行文本，最后一个将结果交给引擎自身的兜底机制。

```
caller SQL
   │
   ├─ 1. parse            SQLGlot, one statement; SELECT or set operation
   ├─ 2. admission        allowlist over the parsed tree
   ├─ 3. rewrite          star expansion, derived columns, timestamp
   │                      arithmetic and literals, JSON canonicalisation,
   │                      schema qualification, limit injection
   ├─ 4. post-rewrite     relations and schema qualification re-checked
   ├─ 5. render           the tree is generated back into SQL text
   │
   └─ 6. execution        SQLite: authorizer callback
                          PostgreSQL: EXPLAIN plan gate
```

调用方文本只在阶段 1 读取一次，之后不再读取。其后每个阶段都操作语法树。数据库执行的语句在阶段 5 从该树生成，因此数据库从未看见调用方键入的原文。阶段 5 无条件执行：不存在原样透传语句文本的路径；这种路径也没有实际意义，因为限制注入和 schema 限定适用于每条语句。

<a id="a-statement-end-to-end"></a>
### 一条语句的完整流程

以下是真实追踪，而非示意。调用方提交：

```sql
SELECT latency_ms FROM spans WHERE name = 'chat'
```

`latency_ms` 是虚拟列，因此被替换为特定方言的表达式。整个替换表达式加括号，保证其绑定位置与列完全一致：

```sql
SELECT (EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) AS latency_ms
FROM spans WHERE name = 'chat'
```

随后 schema 限定根据连接解析 `spans`，限制注入追加 `row_limit + 1`，以检测截断而非假定未截断。PostgreSQL 收到的字符串如下：

```sql
SELECT (EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) AS latency_ms
FROM public.spans
WHERE name = 'chat'
LIMIT 501
```

五个处理步骤未改变此语句。它没有 `*`，因此星号展开无事可做；没有节点 ID，没有与时间戳字面量比较，没有两个时间戳相减，JSON 规范化又仅限 SQLite。封装报告了实际触发的三个步骤。

最后一个代码块不同于调用方提交的字符串，它从树打印而来，而非编辑调用方文本。本设计依赖的每项属性——存在限制、仅出现允许列表关系——都是树的属性；执行语句具有这些属性，只因为它从该树打印生成。由此产生的结论记录在[对解析树应用允许列表](#decision-allowlist-the-parsed-tree-not-the-statement-text)。

<a id="stage-2--admission"></a>
### 阶段 2 — 接纳

只检查解析树，绝不检查文本。四个维度采用**允许列表**：节点类、各方言的函数类和名称、关系、强制转换目标。基础表列是第五个正向目录：对请求方言，每个引用必须命名来自打包 DDL 资源的物理列，或适用的虚拟覆盖列。未知名称在执行前被拒绝，并提供相近物理列和虚拟列名称作为修正建议。

查询局部关系有所不同。CTE、子查询、输出别名或表值函数定义自己的列，因此不能按基础表资源验证这些名称。若某作用域还包含这类来源，只要该来源可能投影出该名称，就允许未限定引用；已限定的基础表引用仍采用失败即拒绝的策略。

标识符匹配遵循目标引擎。SQLite 标识符不区分大小写。PostgreSQL 将未加引号标识符折叠为小写，保留加引号拼写，因此 DDL 加载器保留哪些物理列带引号。拒绝 `NATURAL JOIN`，因为物理 schema 演变时其隐式键会变化。也拒绝整行和复合字段引用，使策略继续基于显式列推理。

<a id="stage-3--rewrite"></a>
### 阶段 3 — 重写

按以下顺序进行九次处理。顺序是正确性的关键，并非偶然：

1. **星号展开** — 将 `*` 替换为有序的物理 DDL 列，随后附加适用的虚拟覆盖列。必须首先进行，因为它会*生成* `latency_ms` 和 `graphql_node_id` 供后两步解析；倒置顺序会将它们未替换地发送给引擎。
2. **`latency_ms`** — 替换为各方言专用表达式。
3. **`graphql_node_id`** — 在谓词中解码，在投影中构建，使用限定器逐引用解析类型。相等、`IN` / `NOT IN`、`= ANY` / `= ALL`、`IS [NOT] DISTINCT FROM` 转换为主键整数比较。模式或范围不是节点 ID，因此 `LIKE` 和 `BETWEEN` 保持投影形式。
4. **时间戳相减**（仅 SQLite）— 将 `end_time - start_time` 通过 `unixepoch` 重写，防止引擎进行文本算术。
5. **时间戳字面量** — 将与时间戳列比较的字面量重新输出为后端能正确比较的格式。PostgreSQL 自行解析字面量，因此实际上只影响 SQLite；两种方言都会在 `notes` 中记录裸日期被按 UTC 解读。
6. **JSON 规范化**（仅 SQLite）— 将访问器重写为部署的表达式索引所用写法。
7. **PostgreSQL 动态 JSON 提取** — sqlglot<=30.15.0 的临时修复。键不是字面路径时，SQLGlot 将 `jsonb -> expr` 渲染为 `json_extract_path`，而 PostgreSQL 的 `json_extract_path` 接受 `json`，不接受 `jsonb`。这些节点转换为 `jsonb_extract_path` / `jsonb_extract_path_text`。字面键（`attributes -> 'llm'`）仍渲染为 `->`。此步骤不重新结合链式 `a -> b.c -> d`（见[开放问题 3](#open-questions)）。sqlglot 固定版本超过 30.16.0 时移除此步骤 (tobymao/sqlglot#8063)。
8. **Schema 限定** — 为允许列表中的关系添加解析出的 PostgreSQL schema 限定。
9. **限制注入** — `row_limit + 1`，以检测截断而非假定未截断。

<a id="stage-4--post-rewrite-check"></a>
### 阶段 4 — 重写后检查

验证重写树仅引用允许列表关系，且若存在 schema 限定符，须为表实际所在 schema。

**这严格弱于接纳检查**，且无法与其等同：重写会有意生成接纳策略拒绝的 SQL——以匿名函数形式出现的 `encode` 和 `convert_to`。实际保证是“没有出现新关系”，而非“仍可接纳”。这一已知弱点记录在[开放问题](#open-questions)。

<a id="stage-6--engine-backstops"></a>
### 阶段 6 — 引擎兜底

SQLite 授权回调和 PostgreSQL `EXPLAIN` 计划门禁看到的是渲染*之后*的语句，与接纳检查看到的内容不同：`json_extract(x, path)` 输出为 `->` 运算符，调用方从未指定的函数也以 SQL 名称出现。

**两者并不等价。**SQLite 授权器拒绝出现在任何位置的非允许列表函数。计划门禁检查关系和集合返回节点，并从 `ProjectSet` 表达式*文本*读取标量函数名称——这无法区分函数和关键字，也完全看不到普通标量调用。因此，接纳函数策略若有漏洞，SQLite 有第二层保护，PostgreSQL 没有。

<a id="design-decisions"></a>
## 设计决策

<a id="decision-capability-is-per-backend-divergence-in-answers-is-not"></a>
### 决策：能力按后端区分，答案差异不由接口制造

函数策略是声明差异的并集，而非交集。除 35 个可移植节点类外，每个后端都获得自身能力——SQLite 的 `percentile`、`julianday`、`json_each`，PostgreSQL 的有序集聚合和 JSONB 接口。为对称而将接口限制到较弱引擎，会从两者删除实际能力。

JSON 接口范围由数据所在位置决定，而非可移植性。本部署几乎所有数据都在 `spans.attributes`，因此读取文档内部几乎就是它的主要查询用途；两个后端均可使用自身尽可能完整的 JSON 词汇，只要操作纯粹且受所读文档大小约束。PostgreSQL 包含键存在性（`?`、`?|`、`?&`）、包含关系（`@>`、`<@`）、路径测试（`@?`、`jsonb_path_exists`、`jsonb_path_match`）、路径查询、键枚举及大小、渲染和构造函数。SQLite 使用 json1 对应能力：`json_array_length`、`json_valid`、`json_pretty`、`json`、`json_quote`、`json_array`、`json_object` 和两个分组聚合。

凡两个后端均能表达的能力，两者都允许。聚合为单个文档在 PostgreSQL 是 `jsonb_agg` 和 `jsonb_object_agg`，在 SQLite 是 `json_group_array` 和 `json_group_object`；四者都会放大，将 N 行折叠为随 N 增长的单元格，并沿用 `group_concat` 已确立的条件：每单元格字节限制拒绝过大结果，截止时间限制工作量。

也允许生成修改后的副本：PostgreSQL 的 `jsonb_set`、`jsonb_insert`、`#-`，SQLite 的 `json_set`、`json_insert`、`json_replace`、`json_remove`、`json_patch`。它们均不写入，每个都返回受输入大小约束的新文档，与 `jsonb_strip_nulls` 属于同类操作；在大成员触及每单元格字节上限前删除它，是此接口有理由支持的用法。

剩下的才是引擎表达能力的真实差异。SQLite 没有键存在性或包含运算符，也没有 SQL/JSON 路径函数，因此通过 `json_extract(...) IS NOT NULL` 和 `json_each` 提问。此类拒绝记录在语料中，因为未声明的不对称与缺口无法区分。

手工维护集合的缺口在有人写出遗漏语句前不可见；拒绝消息指向解析器类，而非调用方写的内容：`?` 报告 `jsonb_contains`，但它不是 PostgreSQL 对应函数；`@?` 报告 `j_s_o_n_b_path_exists`，而这个名称根本不存在。`sql_names()` 没有运算符的函数拼写，因此回退到类名的 snake_case。静默缺口和无法指导修正的消息都属于[开放问题 1](#open-questions)。

哪些差异可接受，由[行为由谁定义](#correctness-who-authored-the-behaviour)决定。这条规则的两个结果尤其影响本策略。

本接口创造的概念须承担完全一致的责任，因为无人能对照规范检查它。拒绝是可恢复的，悄然出现不同数字则不是。

引擎语义不由我们调和，尝试调和比保留更糟。让两后端 `->>` 一致，意味着覆盖数据库文档行为，或降低已能完成有用工作的后端能力。影响排序的操作若使用未经转换的 JSON 提取，执行封装会警告；存在真实表达式索引时，完整详情 schema 也公布精确索引写法。

因此，不对称是决策，并按决策记录。`admission_corpus.py` 为每种方言各记录一次同一语句，附结果与原因。未声明的不对称按定义就是 bug，因为无法与缺口区分。

<a id="decision-allowlist-the-parsed-tree-not-the-statement-text"></a>
### 决策：对解析树而非语句文本应用允许列表

文本级过滤会被注释、空白、大小写、unicode 和嵌套结构绕过。先解析使策略与引擎读取同一产物，因为引擎运行的语句从策略检查过的树打印生成。

代价是依赖 SQLGlot 解析忠实，而此依赖比乍看更重大。不忠实解析不会使策略与引擎脱节：两者都来自树，仍保持一致；它会使两者与**调用方**脱节，因为调用方文本在阶段 1 被丢弃，此后不再查阅。

下游无法检测它，原因有二。每项下游检查都读同一棵错误树，流水线中没有第二意见。而在错误树上往返也稳定：解析、渲染再解析会返回原树，因此自洽性检查仍通过。

此依赖带来两项做法：接纳阶段拒绝不认识的节点类，而非忽略；`admission_corpus.py` 记录每个曾漏过的结构。两者都无法覆盖被顺利解析为错误形状的结构，见[开放问题 3](#open-questions)。

<a id="decision-rewrite-the-statement-rather-than-reject-what-needs-rewriting"></a>
### 决策：重写语句，而非拒绝需要重写的内容

调用方请求 `latency_ms`，是在询问 schema 宣告支持的问题。拒绝并解释正确表达式会多耗一次往返，还假定模型能写对。替换只需一次交互。

代价是执行语句可能表达调用方未提出的含义。针对这些步骤有两项缓解措施：替换表达式整体加括号，保证绑定位置与列完全一致；活性测试针对已植入数据行而非空表执行每个允许结构。

两项缓解都触及不到含义变化的另一个来源：解析本身。处理步骤的正确性只能与输入树相当。若树已误表调用方语句，忠实重写也会得到误表原意的语句，而上述两项缓解都会报告成功。见[开放问题 3](#open-questions)。

<a id="decision-the-schema-is-ddl-not-json"></a>
### 决策：schema 使用 DDL，而非 JSON

在 `brief` 级别，`describeSqlSchema` 返回仅含注释的表目录。在 `detailed` 和 `full` 级别，它选择请求方言的打包 `CREATE TABLE` 语句并追加 `--` 筛选配置注释。由于调用方 SQL 必须使用未限定表名，`CREATE TABLE` 和 `REFERENCES` 语法中的 PostgreSQL `public.` 限定被移除；物理语句其余内容原样保留。

- **实测：**比等价 JSON 目录使用更少 token，后者对每列重复 `name`/`type`/`nullable`。随着渲染器加入约束和列注记，数值也发生变化；`ddl.py` 保存当前测量值，本文有意不重复，因为同一测量的两份副本会漂移，且都无法说明比较对象。
- **结构：**JSON 类型是抽象，DDL 不是。方言资源直接报告 `start_time` 在 SQLite 为 `TIMESTAMP`，在 PostgreSQL 为 `TIMESTAMP WITH TIME ZONE`，调用方编写比较或强制转换时需要知道这些。
- **原生：**这就是调用方写回的形式。

物理 DDL 无法提供的筛选配置——领域、粒度、虚拟列声明、时间列标签、提升列指引和语义列注记——随注释一起传递。虚拟列是注释，并非物理 `CREATE TABLE` 成员；重写使它们在查询中表现为列。

保留原始外键，因此所选表可能描述指向分析允许列表外表的引用。目标提供有用的物理上下文，并不授予查询权限：前言说明可查询表由全局允许列表定义，接纳阶段拒绝该目标。渲染结果返回前会先解析，因为看似 DDL 的文本仍可能无效，而调用方将它当作文字说明，无法辨别。

<a id="decision-the-schema-is-text-the-result-is-a-dict"></a>
### 决策：schema 返回文本，结果返回 dict

两个工具返回不同结构，因为消费方式不同。

`describeSqlSchema` 返回文字说明，没有程序解析，因此 JSON 包装不增加读者会使用的结构，却会对这份大多由换行组成的文档中的每个换行转义——`detailed` 级别为 174 token，约 7%。`output_schema=None` 还会禁用结构化镜像；对文字说明而言，该镜像只是逐字重复文本块。

`executeSql` 返回 dict，因此结果集作为数据到达，而不是需要解析的内容。

**关于重复。**MCP 的 `CallToolResult` 包含必需的 `content` 列表和可选的 `structuredContent`，同时发出两者是惯例：文本块供所有客户端读取，结构化视图供理解它的客户端使用。这不是浪费，而且在此接口实际使用的路径中完全没有成本——见[消费模型](#consumption-model)。

<a id="decision-the-result-envelope-carries-only-what-varies"></a>
### 决策：结果封装只携带可变内容

所有不可能取第二个值的字段都已移除。拆分之前，单行结果共 696 字节，其中行占 53 字节，401 字节不可能变化：硬编码报告所有领域可用的 `availability` 映射、字面 `read_only: true`、字节上限以及每次调用逐字重复的 `consistency` 注记。

这些是接口属性，因此改由 `describeSqlSchema` 携带——每次调用该工具出现一次，而调用方调用它的频率远低于运行查询。

<a id="decision-every-physical-column-of-an-allowlisted-table-is-queryable"></a>
### 决策：允许列表表的所有物理列均可查询

允许列表筛选表而非列。表一旦获准，其方言 DDL 资源中的每个物理列都会被公布、被接纳检查接受并纳入 `SELECT *`；适用虚拟覆盖列追加在物理列之后。因此，显示属性和指向非允许列表表的外键值可见，尽管引用表本身仍不可查询。

这使 schema 教学、接纳和星号展开共用一个目录。未知基础表列按失败即拒绝处理；迁移添加物理列时，重新生成的资源落地后有意将其加入接口。真正应排除的数据必须存于未列入允许列表的表。

<a id="decision-no-default-time-window"></a>
### 决策：不提供默认时间窗口

早期版本在调用方未提供窗口时注入最近七天窗口。它无法约束有意绕过的调用方，因为只需一个参数便可绕过；对其他调用方，它报告成功却回答不同问题。约二十五次冷启动 Agent 运行中，每个调用方都发现并绕过它，因此它谁也没保护，却让所有人多付一次往返。

行数和字节上限限制答案；截止时间限制工作量。

<a id="decision-reads-avoid-the-writer-by-two-different-routes"></a>
### 决策：读取通过两条不同路径避开写入器

Phoenix 增加了专用 SQLite 只读引擎（`mode=ro`，队列池），使读取不再排在写入器唯一的 `StaticPool` 连接后。实测 `NullPool` 为 490 语句/s，队列池为 3,879/s，因此使用池，而非每次读取建立连接。

此接口通过 `db.read()` 在 PostgreSQL 执行路径和目录读取中使用它——包括索引反射、引擎版本和 schema 解析。

**SQLite `executeSql` 有意不这样做。**它为每条语句打开自己的 `sqlean.connect(...?mode=ro)`，因为限制查询的授权回调和进度处理器属于连接级，生命周期不能超出查询：池化连接会使下个调用方继承它们，或者在查询中途移除它们。`mode=ro` 也在打开时固定，之后无法施加。此处放弃池不会损失什么，因为 SQLite 执行宽度为 1，无论如何同一时间只有一条语句执行。

池化路径不保证读到自身写入，`DbSessionFactory.read` 已说明——对 PostgreSQL 副本原本就不保证。

<a id="decision-physical-schema-comes-from-packaged-ddl-curation-from-typed-python"></a>
### 决策：物理 schema 来自打包 DDL，筛选配置来自带类型的 Python

`src/phoenix/db/ddl/` 下生成的 PostgreSQL 和 SQLite schema 资源随 Phoenix 打包，是运行时物理 `CREATE TABLE` 文本及有序列名的来源。加载器索引确定性的 `-- Table: <name>` 段，要求恰好一条匹配的 `CREATE TABLE`，提取列而不让语句经过 SQLGlot 往返，保留带引号标识符语义，并返回每种方言的不可变目录。允许列表表缺失或虚拟列与物理列名称不区分大小写地冲突时，加载分析允许列表失败。

生成器仍位于 `scripts/ddl/`。`make schema-ddl` 重新生成两个规范资源，验证加载器能消费它们，并比较两种方言的表、有序列、显式索引和命名约束漂移。CI 运行该目标后要求 Git diff 干净，因此改变物理 schema 的迁移必须更新已检入资源。

索引不同：`full` 详情从 `pg_get_indexdef` 或 `sqlite_master.sql` 实时读取，因为表达式索引定义是部署事实，调用方必须复现精确写法。`brief` 和 `detailed` 不读取实时目录。

不可变的 `manifest.py` 模块仅提供策略和筛选配置：表/领域允许列表、粒度、时间列标签、虚拟列声明、提升列指引和语义列注记。`graphql_node_id` 适用性还从代码中的 GraphQL 类型映射推导。即使原始物理外键指向非允许列表表，它们也保留在 DDL 中；接纳仍应用全局表允许列表。

PostgreSQL schema 根据连接解析而非假定，遵循 [#14172](https://github.com/Arize-ai/phoenix/pull/14172) 为数据库用量统计确立的规则：环境变量已设置则使用它，否则使用未限定的 `projects` 引用所解析到的 schema。不使用 `current_schema()`，因为它报告 `CREATE` 将落入何处，而非表位于何处——迁移后 `search_path` 增加前置条目时两者会分离。执行和完整详情索引反射使用相同解析，因此公布的表索引属于查询实际读取的关系。

筛选配置字段仍手工编写。`time_column` 是渲染为注释的教学标签，不注入或改变查询窗口。`grain`、提升列指引和列注记也只影响 schema 教学。

<a id="consumption-model"></a>
## 消费模型

此接口的 token 计量取决于客户端调用方式，默认方式并非直觉所想。

在 **MCP 代码模式**（默认）下，模型不接收工具结果。它编写调用 `call_tool(...)` 的 Python，得到**反序列化 dict**，只有该代码返回的内容进入模型上下文。中间结果在沙箱内部过滤和聚合。

对五次编排的 `executeSql` 调用实测：

| | |
|---|---|
| 沙箱内部获取的封装 | 11,522 字节 |
| 进入模型上下文的内容 | 约 200 字节 |

因此 `content`/`structuredContent` 重复在这里不可见：代码看不到任何一种表示，只看到 dict。每次调用的封装大小远不如每个结果都直接呈现时重要——这解释了 `executeSql` 为何返回结构化数据而非文本，也解释了为何仍值得精简封装：确实*会*呈现结果的调用方要为每个字段付费。

若客户端直接渲染每个工具结果，两份表示都会计费。`describeSqlSchema` 上的 `output_schema=None` 针对此情况。

<a id="testing-strategy"></a>
## 测试策略

此接口最主要的缺陷类型是**多层策略之间存在转换器，每层各自验证，却从不相互验证**。因此测试套件检验目录、策略、重写和引擎兜底之间的一致性，而非仅隔离测试各组件：

- **接纳语料** (`admission_corpus.py`) — 每个曾漏过的结构对应一项，记录现在必须产生的结果。在测试持续通过的同时放宽允许列表，是削弱它最廉价的方式。
- **活性** — 每个允许结构都针对已植入数据行执行，并必须返回它们。针对空表执行只能验证解析器与授权器一致，无法验证结构是否正确计算。
- **节点覆盖** — 固定可达的非 `Func` 表达式类，因为多次绕过来自表象不符的类。
- **DDL 资源** — 加载器测试覆盖标记分隔段、精确 `CREATE TABLE` 提取、有序和带引号列、不可变性，以及排除后续索引语句。`make schema-ddl` 验证两个生成资源、比较逻辑结构，CI 拒绝任何重新生成差异。
- **文档与执行器对照** — 对每个表，将 `SELECT *` 展开结果与当前方言资源的有序物理列加适用虚拟覆盖列比较。代表性物理列（含显示字段和接口外外键字段）提交接纳检查；未知名称必须被拒绝并获得有用建议。
- **渲染 DDL 可解析** — 每种详情级别和方言在返回前都先解析。测试还固定详细输出以所选物理资源开头、虚拟覆盖列保持注释形式，以及原始外键可描述非允许列表目标。

将每个公布列、外键和 `CHECK` 字面量提交执行器尚未自动化。完整详情索引属于实时部署数据，因此测试改为固定公布其表达式所用的解析器临时修复。读者不应假定 CI 能捕获未来每个文档与引擎不匹配。

<a id="seeing-it-run"></a>
### 查看实际运行

下面两段代码均可整段粘贴到 MCP Inspector。接口通过[代码模式](#consumption-model)驱动，因此一次调用是返回工具反序列化 dict 的 Python，而非待填写表单。

值得调用 `full` 详情的 `describeSqlSchema`，因为只有 `full` 读取实时目录。表 DDL 仍来自打包方言资源；实时读取提供部署索引：

```python
return await call_tool(
    "describeSqlSchema",
    {
        "tables": ["spans"],
        "detail": "full",
    },
)
```

它返回带筛选配置注释的 `spans` DDL、编写 JSON 运算符的前言规则，以及渲染为 `CREATE INDEX` 的部署表达式索引。应仔细阅读索引部分。只有查询逐字符重复索引表达式，表达式索引才可用，因此这些写法是要求而非建议；未见过它们的调用方无法猜测多种等价形式中哪一种被建了索引。

然后 `executeSql` 可提出固定 API 无法回答的问题，因为其维度事先未知——按模型统计尾延迟，其中模型名称是 JSON 路径而非列：

```python
return await call_tool(
    "executeSql",
    {
        "sql": """
        SELECT attributes #>> '{llm,model_name}' AS model,
               count(*) AS calls,
               round(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 1) AS p95_ms
        FROM spans
        WHERE attributes ? 'llm'
        GROUP BY model
        HAVING count(*) > 5
        ORDER BY p95_ms DESC
    """
    },
)
```

此语句有四点值得注意，每点都对应本文其他位置记录的决策。

`attributes #>> '{llm,model_name}'` 是 `describeSqlSchema` 为索引路径公布的完整写法，包括强制转换——也就是没有转换，因为路径字面量无需转换。`attributes ? 'llm'` 是键存在性测试，PostgreSQL 允许而 SQLite 不支持，属于[已声明的不对称](#decision-capability-is-per-backend-divergence-in-answers-is-not)，而非缺口。此处允许 `percentile_cont(...) WITHIN GROUP`，SQLite 则拒绝并在消息中指出 `percentile(x, p)`。而 `latency_ms` 根本不是物理列。

最后一点在答案中可见。封装报告 `applied.rewrites` 为 `latency_ms`、`schema_qualification`、`limit_injection`：虚拟列被替换为方言专用表达式，`spans` 根据连接解析，并追加 `row_limit + 1` 以检测答案截断，而非假定未截断。

<a id="open-questions"></a>
## 开放问题

按对设计的影响程度排序。

1. **一项策略，十处枚举，四套词汇。**“允许运行哪些计算”写在十处，用 SQLGlot 类、调用方写法、SQLite 授权器名称和 PostgreSQL 计划标识符表达。没有集合从另一个集合推导；一致性靠测试维护，代码注释记录了四处差异。生成的能力表可使缺失单元在导入时失败。

2. **结果没有标记为不可信内容**，尽管它们将受攻击者影响的文本传入持有破坏性工具的模型。

3. **SQLGlot 将 PostgreSQL JSON 运算符解析为访问器，而非二元运算符。**`->`、`->>`、`#>`、`#>>` 和 `?` 位于 SQLGlot 的 `COLUMN_OPERATORS` 中，因此绑定在最高优先级，且右操作数解析不一致。PostgreSQL 将它们放在“其他运算符”层，低于算术，与 `||` 同级。四种分组会出错：

| 输入 | SQLGlot 构建结果 | PostgreSQL 原意 |
   |---|---|---|
   | `a #>> b::text[]` | `CAST(a #>> b AS TEXT[])` | `a #>> CAST(b AS TEXT[])` |
   | `a -> b[1]` | `(a -> b)[1]` | `a -> b[1]` |
   | `a -> b.c -> d` | `a -> (b.c -> d)` | `(a -> b.c) -> d` |
   | `a -> b + 1` | `(a -> b) + 1` | `a -> (b + 1)` |

缺陷在解析中，因此下游检查无法恢复含义，往返也不暴露它——解析、渲染再解析返回同一棵错误树。第二和第四行渲染后的文本与调用方原文逐字符相同，因此 PostgreSQL 依据自身优先级重新解析，调用方原意偶然得以保留，而非设计保证。第一和第三行将错误分组渲染为 `CAST` 或 `JSON_EXTRACT_PATH` 调用，引擎无法重新解释。

加括号可解决全部四种情况。带括号操作数位于 `Paren` 节点下，作为整体绑定，因此 `a #>> ('{a,b}'::text[])`、`a -> ('a'[1])`、`a -> (b.c) -> d`、`a -> (1 + 1)` 都按 PostgreSQL 解读方式解析和渲染。四者均已在 PostgreSQL 17 验证。

已实施三项缓解。`catalog.py` 从公布的索引写法中移除冗余强制转换，因为 `pg_get_indexdef` 为 JSON 路径表达式索引输出 `'{a,b}'::text[]`；移除后的形式仍使用同一索引，已通过 `EXPLAIN` 验证。schema 前言预先说明括号规则，让调用方在写 SQL 前而非遭拒后才了解。接纳直接拒绝第一行，因为有意的 `CAST(a #>> b AS text[])` 也产生相同树——这是将提取字符串解析为数组字面量的有效语句——解析后无法区分两种解读。静默选择任一种都会回答调用方未提出的问题，因此拒绝消息改为指出两种无歧义写法。

尚未覆盖的是在第二至第四行不遵循前言的调用方。第二和第四行仍渲染为与原文相同的文本，因此 PostgreSQL 恢复含义。第三行不会：`a -> b.c -> d` 渲染为结合性已错误固定的 `JSON_EXTRACT_PATH` 调用，返回错误值却不报告任何问题。

固定版本为 30.14.0/30.15.0 时，曾研究在 Phoenix 中重新结合第三行，最终否决。其结构与第一行同样有歧义：`json_extract_path(a, json_extract_path(b, c))` 解析为相同嵌套，而调用方可能确实有此意。只能通过未文档化的解析器内部机制区分——由运算符语法构建的节点与函数调用节点具有不同 args——依赖这些内部细节进行改变语义的重写，得不偿失。

已向上游报告：<https://github.com/tobymao/sqlglot/issues/8035>。修复通过 [#8063](https://github.com/tobymao/sqlglot/pull/8063) 在 sqlglot 30.16.0 落地，将 JSON 运算符移到 Postgres 的二元运算符优先级层。该版本中上述每行及 `col -> k` 均以中缀形式往返。Phoenix 固定为 `sqlglot==30.15.0`（三天等待），因此保留缓解措施。搜索 `WORKAROUND sqlglot<=30.15.0` 可找到相关位置；固定版本超过 30.16.0 时移除。对 `a #>> b::text[]` 的接纳拒绝也可移除，因为修正后的解析器能区分它原本要分开的两种解读。允许列表中的 `jsonb_extract_path` 不是临时修复——调用方确实会写它。

4. **计划门禁和 SQLite 授权器并非等价兜底**（见[阶段 6](#stage-6--engine-backstops)）。

<a id="references"></a>
## 参考资料

- 实现：`src/phoenix/server/mcp/sql/`
- 测试：`tests/unit/server/mcp/sql/`
- 相关：[读取副本路由](./pg-read-replica-routing.md)
