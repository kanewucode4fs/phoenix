<a id="session-filter-dsl"></a>

# 会话过滤 DSL

> 本规范及其一致性测试是判断语言接受哪些形式的权威依据。**面向用户**的语法参考是公开的[过滤表达式](https://arize.com/docs/phoenix/tracing/how-to-tracing/filter-expressions)文档，它是本规范经整理的派生文档，并非第二个权威来源。接受的语法变化时，应保持两者同步。

Phoenix 按 `session_id` 将追踪分组为会话。一条追踪记录一次交互，即输入及为其生成的响应，因此会话呈现为一段对话。会话过滤 DSL 允许用户或 Agent 使用简短的 Python 表达式选择会话，例如：

```python
num_traces > 5 and any(span.status_code == "ERROR" for span in spans)
```

它是 Span 视图所用过滤语言的会话级同类语言。目前驱动会话表格的过滤、计数和过滤栏，也是会话级项目评估器（见 [online-evals.md](./online-evals.md)）将用于限定被评估会话范围的过滤词汇。

核心模块：

- `src/phoenix/trace/dsl/filter.py`：共享过滤编译器，按粒度参数化
- `src/phoenix/trace/dsl/session_filter.py`：会话绑定和查询组装
- `src/phoenix/db/session_aggregates.py`：可复用的逐会话聚合子查询

<a id="design-philosophy"></a>

## 设计理念

四项承诺塑造了这一设计。它们比任何单项功能更重要，因为它们决定语言如何演进。

<a id="one-language-family-one-flavor"></a>

### 同一语言家族，保持同一风格

Phoenix 已有 Span 过滤语言，即针对 `name`、`latency_ms`、`annotations["quality"].score` 等平铺名称的 Python 表达式。会话语言完全保留这一风格：相同的表达式语法、平铺命名方式、类型转换和标注惯用形式，以及错误消息。用户和 Agent 只需学习一次，即可在不同粒度间复用知识（此处“粒度”指过滤器运行的对象层级：Span、会话，以及未来的追踪）。跨粒度的内部一致性优先于针对单一粒度的优化。若某个构造无法与整个语言家族保持一致，就应在发布前解决这一设计问题。

这一承诺解释了为什么字符串包含判断在所有粒度都忽略大小写，而不是仅在最初需要它的粒度忽略：Span 粒度与会话粒度同步调整，使相同查询在两个视图中得到相同答案。原因见[大小写](#case-containment-ignores-it-equality-does-not)。

<a id="python-with-a-sql-backend-not-python-flavored-sql"></a>

### 使用 SQL 后端的 Python，而非 Python 风格的 SQL

过滤条件是真正的 Python，其含义由 Python 定义。未来这些表达式也将在评估器绑定中作为实际 Python 运行，因此两个执行环境必须一致。正确性规范因此是一份小型 Python 参考评估器；SQL 编译器当且仅当在每份测试数据上都与参考实现一致时才正确（见[正确性](#correctness-the-reference-evaluator)）。行为继承自 CPython，而非重新设计：空选择上的 `all()` 为真，`len([])` 为 `0`，`sum(())` 为 `0`，而 `len(...)` 接受列表推导式，不接受生成器。

要坚持这一原则，需要基于类型的接受策略，因为共享编译器在无法确定类型时会强制转换：另一侧为数字时将操作数转换为数字，把 `is` 视为 `==`，并将所有 Python 运算符交给 SQLAlchemy 处理。这是旧 Span 语言已接受的范围，仍在那里保留。但既然声明条件*就是* Python，就不能把 `session_id == 1` 解释为针对字符串数据的数值比较，也不能将 `+x` 解释为 `-x`。因此，在构建任何 SQL 前，此粒度都会为每个子表达式解析类型并拒绝不匹配形式；规则及各自原因见[语言接受哪些形式](#what-the-language-accepts)。审查发现的每项差异最终只有两种处理：实现符合规范，或在下文明确定义偏离规则。没有任何形式因疏忽而被接受，因为接受一种形式就是兼容性承诺，无论是否有人本意如此。

<a id="legislated-deviations-from-python"></a>

### 明确定义的 Python 偏离规则

过滤器无法逐行抛出异常，SQL NULL 的行为也不同于 Python 值。因此语言明确定义了一项偏离：缺失值无法通过任何比较。没有记录输入的会话、没有 Token 计数的 Span、空 `max(...)`，与任何内容比较都为假，无论操作数方向。真正缺少该值的会话应通过 `is None` 显式选择。

另一项偏离是：针对字符串搜索范围的 `in` 忽略大小写，而 Python 精确匹配（见[大小写](#case-containment-ignores-it-equality-does-not)）。两项偏离的原因相同：忠实于 Python 的行为会静默丢弃用户希望找到的行；两者也都分别在 SQL 编译器和 Python 参考实现中实现，以确保两个执行环境仍一致。其他行为均遵循 CPython。

<a id="the-vocabulary-cannot-drift-from-the-compiler"></a>

### 词汇表不得偏离编译器

语言绑定的所有内容，包括字段、聚合、可迭代对象和元素字段，都从编译器读取的同一套表提供给客户端。没有人工维护的建议列表。一个名称能编译，词汇表端点就提供它；不能编译，就不会被建议。自动补全、Agent 工具和验证都建立在这个唯一来源上。

<a id="the-language"></a>

## 语言

<a id="session-fields"></a>

### 会话字段

会话行的直接列：

| 名称 | 类型 | 含义 |
| --- | --- | --- |
| `session_id` | string | 会话标识符 |
| `start_time`, `end_time` | datetime | 最早和最晚的追踪时间戳 |
| `duration_ms` | float | 实际经过时长，单位为毫秒 |

日期时间比较值是带显式时区偏移的 ISO 8601 字符串，例如 `start_time > '2026-07-01T00:00:00+00:00'`，也可使用尾缀 `Z`。不带偏移的字面量会在验证时被拒绝（`datetime literal '…' has no timezone, add an offset (e.g. 'Z' for
UTC)`）。要求显式偏移，而不默认 UTC，是因为一般 REST 规范化会将无时区输入解释为服务器时区；同一表达式在不同地方表示不同时刻，不适合保存。

`start_time` 和 `end_time` 不是视图时间范围，这一区别容易造成误解。`timeRange` 通过与半开窗口的*区间重叠*选择候选全集：只要会话在窗口内活跃就计入，无论它提前多久开始。这两个字段则是针对会话自身边界的*时间点比较*。因此，昨天开始且仍运行的会话位于今天的 `timeRange` 内，却不满足 `start_time > '<today>'`。同时提供时以 `AND` 组合；除了已有的会话范围连接，两者均不改变聚合或推导式子查询的作用域。“最近 7 天”等相对意图应留在时间范围接口中；已保存 DSL 文本则使用绝对字面量，保持确定性。

<a id="aggregates"></a>

### 聚合

按需计算的逐会话汇总。会话没有匹配数据时，每项均为 `0`，绝不为 null：

| 名称 | 含义 |
| --- | --- |
| `num_traces` | 追踪数量 |
| `num_traces_with_error` | 包含出错 Span 的追踪 |
| `token_count_prompt`, `token_count_completion`, `token_count_total` | LLM Token 总量 |
| `prompt_cost`, `completion_cost`, `total_cost` | 成本总量 |
| `tool_span_count`, `llm_span_count` | TOOL / LLM 类型的 Span |

一条追踪就是一条追踪。每次交互开启一条追踪的插桩方式，会使 `num_traces` 近似于对话轮次数；向希望按轮次查询的用户说明这一点很有帮助。但这只是 Phoenix 不强制执行的摄取约定，因此词汇释义和此表均不将轮次数定义为该术语的含义。

<a id="root-span-access"></a>

### 访问根 Span

会话自身没有属性，因此一些名称会从会话的 Span 中读取：

- `attributes["llm.model_name"]`：访问会话*最早根 Span* 的属性，按 OTel 传输键寻址。字符串下标以点连接，因此 `attributes["llm"]["model_name"]` 表示同一键。无论摄取时如何嵌套，查询都能匹配该键。键缺失时按缺失值处理（见上文偏离规则）。
- `user.id` 和 `metadata["key"]`：对应 `attributes` 键的受支持简写。
- `first_input` / `last_output`：字符串，从会话最早和最晚的根 Span 读取。“最早”是确定性排序，不涉及角色判断：先按追踪开始时间，再按追踪 ID，最后按 Span ID。适用于“会话是否良好结束”之类检查。
- `'refund' in any_input` / `any_output`：针对会话根 Span 的 EXISTS，判断*某个*根 Span 的输入或输出是否包含文本。比首个/末个形式成本低，是“会话是否提到 X”的合适默认方式。注意搜索可作用的三个全集：所有 Span、所有根 Span（`any_*`）、单个根 Span（`first_input`、`attributes[...]`），范围依次缩小。这两项仅支持包含判断：接受针对字符串字面量的 `in` 和 `not in`，绝不接受 `==`；服务提供的词汇表将其类型标记为 `containment`，避免自动补全引导用户使用相等形式。

<a id="annotations"></a>

### 标注

`annotations["quality"].score > 0.8` 使用与 Span 语言相同的惯用形式读取会话级标注。单个 Span 的标注通过下文 `span_annotations` 可迭代对象访问。

这种写法是相对于实体的：`annotations[...]` 在这里读取 `project_session_annotation` 行，在 Span 过滤器中读取 `span_annotation` 行。这符合过滤器始终针对自身粒度的惯例，但表达式本身没有说明，因此提供的词汇表会向同时使用两种过滤器的人明确说明。

<a id="comprehensions"></a>

### 推导式

语言使用真正的 Python 推导式语法，对会话成员进行量化判断和聚合：

```python
any(span.status_code == "ERROR" for span in spans)
all(trace.latency_ms < 30000 for trace in traces)
len([span for span in spans if span.span_kind == "TOOL"]) > 3
sum(detail.tokens for detail in span_cost_details if detail.token_type == "cache_read") > 0
```

六个可调用函数接受推导式：`any`、`all`（量词），以及 `len`、`max`、`min`、`sum`（归约）。有五个可迭代对象：

| 可迭代对象 | 元素字段 |
| --- | --- |
| `spans` | `name`, `span_kind`, `status_code`, `latency_ms`, `llm_token_count_prompt`, `llm_token_count_completion`, `llm_token_count_total` |
| `traces` | `start_time`, `end_time`, `latency_ms`，以及嵌套的 `spans` 可迭代对象 |
| `session_annotations` | `name`, `label`, `score` |
| `span_annotations` | `name`, `label`, `score`（所有 Span 的标注，展开到会话范围） |
| `span_cost_details` | `token_type`, `is_prompt`, `cost`, `tokens`, `cost_per_token` |

设计说明，每项都是有意作出的选择：

- **使用推导式语法，而非辅助函数。** 曾考虑 `any_span("status_code == 'ERROR'")` 这类嵌套字符串辅助函数。最终选择推导式，因为循环变量解决了实际问题：`start_time` 同时存在于会话和追踪粒度，`trace.start_time` 没有歧义，而字符串中的裸名称有歧义。推导式也是语言模型最可靠生成的形式。
- **明确粒度名称。** 可迭代对象命名为 `spans` 和 `session_annotations`，不使用 `annotations` 等相对于上下文的名称。在推导式内始终清楚迭代对象是什么。
- **仅基于行。** 每个可迭代对象都对应现有数据库表。本版本不提供基于 JSON 的可迭代对象（消息、文档、事件）；未来可以添加，不破坏现有行为。
- **仅允许一种嵌套。** `traces` 元素公开 `trace.spans`，因此可表达逐轮次问题：`any(any(s.span_kind == "TOOL" for s in trace.spans) for trace in traces)`。嵌套到此为止，并明确报错：推导式中引用的会话级集合与正在迭代的元素无关联，因此按名称拒绝，不会编译为无法关联键的子查询。
- **使用叶级 Token 计数。** Span 元素公开逐 Span 的 `llm_token_count_*` 列，不公开 `cumulative_*` 汇总。对会话累加累计计数，会通过外层 Agent 和工具 Span 重复计算相同 Token。
- **仅允许循环变量作用域。** 推导式中，谓词可引用循环变量字段、字面量及其算术运算。目前拒绝推导式内的裸会话级名称；这是限制，并非语义选择，未来可解除。
- **按名称统计工具只有一种写法。** 统计单个工具调用次数使用推导式：`len([span for span in spans if span.name == "search"])`。先前的 `tool_span_count["search"]` 下标形式已弃用：它需要扫描观测到的工具名称来验证，从未出现的名称会静默计为 0，而不报错。重新引入下标只会为语言已有能力提供更短写法，却需要付出词汇扫描成本。
- **区分大小写的包含判断已移除，而非隐藏。** `in` 不区分大小写（见[大小写](#case-containment-ignores-it-equality-does-not)）后，无法请求精确大小写的子串匹配。这确实是能力损失，但被接受，因为文本搜索绝大多数时候是不区分大小写的问题，而从第一天就提供第二个运算符，会要求用户在真正需要之前学习额外词汇。若未来需要精确形式，可以纯增量添加，即在 `in` 旁新增独立运算符，绝不改变 `in` 的含义。

<a id="case-containment-ignores-it-equality-does-not"></a>

### 大小写：包含判断忽略，相等比较不忽略

过滤语言中所有针对字符串搜索范围的 `in` 和 `not in` 都忽略大小写，会话粒度（`any_input`、`any_output`、`first_input`、`last_output`、`session_id`、根 Span 属性读取、标注标签）和 Span 粒度（`name`、`input.value`、`status_message`、属性读取）均如此。`==` 和 `!=` 仍精确匹配，字面量列表成员判断（`span.name in ["search", "lookup"]`）也是如此，因为它是集合测试，而非文本搜索。因此，`'refund' in first_input` 能找到以 `REFUND please` 开始的会话，但 `first_input == 'refund please'` 不能。

原因在于此语言替代的界面。会话表格此前有独立的不区分大小写子串搜索框；若直接改为 DSL 而不调整行为，会悄然缩小用户可找到的内容。搜索文本时，人们想表达的是“提到这个”，而非“必须完全这样拼写”；静默漏掉 `REFUND` 的过滤器看起来像坏了，而非更精确。它在 PostgreSQL 编译为 `ILIKE`，在 SQLite 对两个操作数应用 `text_lower`，与原搜索机制相同，因此非 ASCII 和通配符字面量行为保持不变。

**Span 粒度也已同步调整，这是对已发布语言的行为变更。** Span 粒度的 `in` 和 `not in` 此前精确匹配，现在也忽略大小写，因此已保存的 `'timeout' in output.value` 过滤器开始匹配写作 `Timeout` 的 Span。使用 `in` 的已保存 Span 过滤器返回相同行或更多行，绝不会更少；使用 `not in` 的返回相同行或更少行，绝不会更多。选择接受此变化，是因为用户在会话和 Span 视图间切换时，相同外观的查询会得到两个不同答案，而不区分大小写的答案才是人们搜索文本时的意图。该行为由共享编译器绑定中的标志控制，各粒度设置一致，因此始终是统一决策，而非各粒度自行形成的习惯。未来在 `in` 旁新增精确大小写运算符，在两个粒度仍都是纯增量变化。

<a id="what-the-language-accepts"></a>

### 语言接受哪些形式

每个项都有类型：文本、数字、时间戳、条件，或用于根 Span 读取的*属性值*（直到读取行时才知道其存储类型）。条件只有类型正确才被接受。以下规则构成完整策略。每条规则存在的原因都是：其他形式会被编译成与其 Python 写法不同的含义。

- **条件必须是条件。** 包括比较、量词，以及对它们应用 `and`/`or`/`not`。裸数字不是过滤器，`not num_traces` 也不表示“没有追踪”：数字真值是 Python 规则，SQL 没有等价形式，PostgreSQL 会直接拒绝。
- **比较操作数类型匹配。** `session_id == 1` 是错误，不是要求将会话 ID 当作数字读取。属性值可以与任何内容比较，因为它实际可能是任意类型；时间戳与 ISO 字面量比较，这是语言已有的写法。`True`/`False` 只与布尔类型项比较。
- **`is` 和 `is not` 仅接受 `None`。** CPython 的 `is` 判断对象身份，列比较无法表达这一含义。将其视为 `==` 会使同一表达式的两种写法都偏离 Python。
- **`<`、`<=`、`>`、`>=` 只排序数字和时间戳，不排序文本。** SQLite 按字节值排序文本，PostgreSQL 按数据库排序规则排序，因此文本排序在两个后端含义不同。同样的理由也拒绝对文本使用 `max`/`min`；若未来显式定义排序规则，可同时解除两项限制。
- **算术只允许数字上的 `+ - * / %`。** `//`、`**`、`<<`、`>>`、`&`、`|`、`^`、`@` 和 `~` 在降级转换前就被拒绝，不等到 SQLAlchemy 内部失败；一元 `+` 按 Python 定义保持值不变。属性值的存储类型未知，进行算术时必须显式使用 `float(...)`。
- **字面量为文本、数字、`True`/`False` 和 `None`。** 拒绝字节、复数、`Ellipsis`、大到溢出为无穷的浮点字面量，以及文本字面量中的 NUL。最后一项是因为 PostgreSQL 拒绝文本值中的 NUL，而 SQLite 会存储它，接受就会使同一过滤器在不同部署中含义不同。
- **`in` 搜索文本，或在字面量列表中查找值。** 搜索范围是文本或属性值，查找项是文本字面量；列表只包含同一类型字面量。以列为查找项（`session_id in first_input`）属于跨列子串搜索，是可考虑的功能，但成本尚未设计，因此现在拒绝，为未来保留空间。
- **接受空集合。** `x in []` 始终为假，`x not in ()` 始终为真，与 Python 完全一致，且 SQLAlchemy 的空集重写可移植。两者都通过实际执行语句测试，而非偶然继承。
- **尚不接受集合字面量。** `x in {'a', 'b'}` 是惯用 Python 写法，缺失它确实不够顺手，目前只是推迟而非解决：未来允许一种已拒绝写法是纯增量变化，撤回一种已接受写法则不是。
- **`float(...)` 和 `str(...)` 转换属性值；不存在 `int(...)`。** 只有 SQLite 与 PostgreSQL 结果一致时才允许转换。拒绝已确定类型的文本、数字、时间戳和条件；例如整数值浮点数在 SQLite 渲染为 `1.0`，在 PostgreSQL 渲染为 `1`，转成文本会静默选出不同会话。根 Span 属性仍可转换，因为读取行前不知道存储类型。两种数值转换共享同一降级实现，因此 `int(1.9)` 会按 `1.9` 比较，与写法承诺相反。未来可以有意实现截断。
- **严格解析名称，包括点号名称。** `user.id` 是唯一接受的点号简写；`usr.id` 是拼写错误，不是任意属性请求。开放的点号回退会悄然绕过其他名称提供的“你是否想输入”保护，而 `attributes["usr.id"]` 能无歧义表达相同意图。
- **归约只处理数字。** `sum(span.name for span in spans)` 在累加文本，SQLite 会强制转换为零，PostgreSQL 则拒绝。此问题实际想要的是计数：`len([...])`。
- **推导式只迭代一个集合。** 唯一嵌套是 `traces` 元素声明的 `trace.spans`；在下一层作用域引用会话级集合没有可关联对象，因此按名称拒绝。推导式内的会话级*项*也会被拒绝，并在错误中指出作用域，因为同一写法在外部可用。
- **名称必须按词汇表的写法拼写。** Python 解析器会对标识符进行 NFKC 规范化，因此全角 `ｓｅｓｓｉｏｎ＿ｉｄ` 否则会解析为 `session_id`，相当于解析器定义词汇表端点无法提供的别名，违反上文防漂移承诺。下标键是数据，保留原始拼写。条件外围空白会被规范化，因此前导空格不会导致 `IndentationError`。

这些拒绝规则固定在接受/拒绝语料库（`test_session_filter_semantics.py`）中，未来修改项必须在这里说明合理性。语料库中的已接受形式会针对真实数据库执行，不只渲染；其行集语义由差异测试套件验证。

<a id="semantics-of-missing-values-precisely"></a>

### 缺失值的精确语义

缺失值偏离规则具体如下。两个执行环境均实现每一条：

- 与缺失值比较，两个方向都为假。
- `all(P for x in IT)` 将字段缺失的元素视为反例。SQL 中反例检查编译为 `P IS NOT TRUE`，绝不使用 `NOT P`，因为三值逻辑下 `NOT NULL` 仍为 NULL，会静默通过。
- 空选择上的 `all()` 为真（继承 Python；结构上无需额外处理，即空集上的 `NOT EXISTS`）。
- 空选择上的 `len` 和 `sum` 为 `0`（继承 Python）。
- 空选择上的 `max`/`min` 是*缺失值*，因此与其任何比较都为假。Python 在这里抛异常，但过滤器不能，因此采用偏离规则。拒绝改为合并到 `0`，否则 `max(...) < 5` 会毫不犹豫地匹配完全没有合格 Span 的会话。
- 归约跳过被归约字段缺失的元素，与 SQL 聚合语义一致。

<a id="compilation"></a>

## 编译

<a id="one-compiler-parameterized-per-grain"></a>

### 一个编译器，按粒度参数化

只有一个过滤编译器。每个粒度提供绑定对象，按类型声明标量名称、聚合名称、标注关系和可迭代对象。Span 语言和会话语言使用同一机制配合不同绑定，从而保持风格一致。会话绑定在验证时拒绝未知名称，并根据绑定词汇表给出“你是否想输入”的建议。

<a id="comprehensions-become-subqueries-over-the-element-table"></a>

### 推导式转换为元素表上的子查询

验证器在解析后的语法树上将允许的表达式形态列入白名单。随后预处理将每个推导式提取为占位名称，并记录其所需内容：种类（`any`、`sum` 等）、可迭代对象、循环变量、可选 `if` 子句和嵌套推导式。查询时，每条记录以下述两种降级形式之一针对元素表构建子查询。

在 probe 降级形式下，子查询关联到会话行：

- `any(...)` → `EXISTS (SELECT 1 … WHERE predicate)`
- `all(...)` → `NOT EXISTS (SELECT 1 … WHERE predicate IS NOT TRUE)`
- `len`/`sum` → 关联标量 `COUNT`/`SUM`，合并空值为 `0`
- `max`/`min` → 关联标量，空选择保留 NULL

在 scan 降级形式下，每条记录最外层的推导式改为不关联，使一次元素表扫描同时为所有会话回答问题：

- `any(...)` → `session_id IN (SELECT session_key … WHERE predicate)`
- `len`/`sum` → 按会话分组的 `(session_key, aggregate)` 子查询，LEFT JOIN 到会话行，通过 `COALESCE(…, 0)` 读取
- `max`/`min` → 相同的分组子查询，直接读取，使空集保持 NULL

`all(...)` 是例外：两种降级形式都保留关联 `NOT EXISTS` 结构。不关联形式 `session_id NOT IN (SELECT session_key … WHERE predicate IS NOT
TRUE)` 将所有不满足测试的元素放入排除集合。当谓词有选择性，也就是用户真正过滤时，该集合通常占元素表的大部分。这么大的集合上的 `NOT IN` 会退化到超过语句超时，而关联形式则计划为逐会话的反连接探测。在 300 万 Span 语料库（过滤项目中有 10 万会话）上实测：排除集合形式超过 90 秒语句超时，关联形式在远低于一秒内返回；对于几乎处处为真的谓词，即排除集合形式的最佳情形，两者在同一数量级内。关联形式也不受 `NOT IN` 的 NULL 陷阱影响：`Trace.project_session_rowid` 可空，`NOT IN` 集合中只要有一个 NULL 就会清空整个结果，而 NULL 键只会无法匹配关联。

两种降级形式在构造上保持一致。没有匹配元素的会话不在 `any` 集合中，且不存在 `all` 反例，正是真空真规则；`len` 和 `sum` 合并为 `0`；`max` 和 `min` 保持 NULL，因此无法通过任何比较。

只有最外层推导式改变形态。嵌套推导式仍关联到包围它的元素，外层子查询已将该元素限定到会话。两种降级形式下，内部谓词都依据可迭代对象自身绑定编译，因此继承顶层条件的类型转换、大写转换和错误行为。

<a id="two-lowerings-chosen-by-access-pattern"></a>

### 根据访问模式选择两种降级形式

所有超出会话行的构造，包括聚合、推导式、根 Span 访问，都会编译为两种物理形态之一。由调用方选择，因为编译器不知道传入语句是否带 `LIMIT`，而这正是问题的全部：

- **probe**：每个候选会话行使用一个子查询。带 `LIMIT` 的语句找到足够匹配行后即可停止，因此只需为返回的行付出成本。
- **scan**：对元素表或追踪表扫描一次，并连接一次。必须访问所有会话的语句需要这种方式，因为没有提前退出的收益。

已发布的分派方式由此确定：

| 语句 | 降级形式 | 原因 |
|---|---|---|
| 不访问标注、按已索引列排序的分页 | direct + probe | 找到足够匹配行后 `LIMIT` 停止 |
| 按聚合列排序的分页 | direct + scan，复用排序子查询 | 排序前必须为每个会话物化该聚合，已不存在提前退出收益 |
| 计数、摘要加载器，以及所有读取标注的条件 | rowid subquery + scan | 无可供退出的 `LIMIT`，或需要去重 |

“Direct”指将谓词直接应用到被分页的语句。替代方式是包裹为 `session_id IN (SELECT DISTINCT …)`，这会将逐会话工作移到该语句外，使数据库在 `LIMIT` 看到任何行之前，先为项目每个会话评估条件。在 10 万会话上实测，包裹查询单页约 2543 毫秒，直接应用约 2 毫秒。读取标注的条件仍保留包装：会话标注在 `(name, project_session_id, identifier)` 上唯一，因此同一会话同一名称可有多行，包装中的 `DISTINCT` 负责合并。编译器引入的其他内容至多为每个会话贡献一行：量词及 `any_input`/`any_output` 谓词是不会添加行的 `EXISTS` 或 `IN` 谓词；分组聚合和归约子查询在构造上保证每会话一行；根 Span 输入/输出和 `attributes[...]` 则是每会话取排名第一行的窗口，按会话 ID 外连接。

选择性是这种分派无法获知的因素。条件不匹配任何内容的分页永远无法填满 `LIMIT`，因此 probe 降级会遍历整个项目，此时不如 scan：实测为 243 毫秒对 117 毫秒。这是有意的取舍：罕见情况约慢 2 倍，常见情况约快 100 倍。

基准测试框架位于 `scripts/perf/session_filter_perf.py`。每个测量查询都从下述两个接口构建，因此会跨构造类别、访问模式和选择性，报告服务器实际运行的查询形态。

<a id="two-seams-one-per-access-pattern"></a>

### 两个接口，分别对应一种访问模式

服务器使用方仅通过 `src/phoenix/server/session_filters.py` 中两个函数访问此语言，语言细节不会越过它们泄露到外部。

`get_filtered_session_rowids_subquery(...)` 在项目和时间范围限定下生成匹配会话行 ID 集合。使用方以单个 `IN` 子句应用它：会话计数和项目级摘要加载器（记录数、标注摘要、延迟分位数、成本摘要）都只接收这个不透明子查询。

`apply_session_filter_to_page(...)` 接收调用方正在分页的语句，并返回应用条件后的语句：安全时直接应用，读取标注时经由 rowid 子查询。会话列表是唯一使用方。

之所以拆分，是因为分页是唯一需要保护提前退出的访问模式，保护它就需要将语句而非行 ID 集合交给编译器。两个接口对相同条件返回相同会话，使过滤后的计数与列表保持一致。时间范围限定同样共享，采用区间重叠：会话区间与窗口相交就匹配，与会话表格时间范围行为相同，因此在窗口边缘也一致。

<a id="correctness-the-reference-evaluator"></a>

## 正确性：参考评估器

`tests/unit/trace/dsl/session_filter_reference.py` 直接在内存测试会话上执行完整语言，独立实现缺失值比较失败规则，并为 `and`/`or`/`not` 使用三值逻辑。差异测试将相同数据写入数据库，并对每个（测试数据、条件）组合断言：编译 SQL 选出的会话与参考实现完全相同。

参考实现有意保持独立，而不是移植编译器。两个独立实现的一致才是证据，共享错误需要被独立犯两次。语料覆盖偏离规则产生的边界：空集上的 `all`、空 `max`/`min`、两种量词及每种归约下缺失的元素字段、`if` 子句过滤、每种可迭代对象，以及追踪→Span 嵌套。也包含大小写规则，这是语言没有直接继承 CPython 的一处：仅大小写不同的包含用例，以及必须保持精确匹配的相等和列表成员形式。

参考实现也建模根 Span 名称及 `annotations[...]`，这些地方最受缺失值规则影响，也是仅声明规则并不等于实际执行的地方。`first_input` 和 `last_output` 读取根 Span 窗口两端；对应一端没有记录时为缺失值，因此 `not in` 和 `==` 排除这些会话。`any_input` 和 `any_output` 则对所有根 Span 作存在判断，因此 `'x' not in any_input` 会*匹配*完全没有输入的会话。两者都通过包含无根 Span、无输入，以及输入不应归入任一形式的子 Span 的数据固定行为。

`annotations["q"]` 编译为外连接，因此同一名称有多行的会话会产生多个候选行，只要其中任何一行满足整个条件便匹配。参考实现为每个引用名称绑定一行，并尝试所有组合来建模。这使一个不变量可被直接检查：在名称重复、分数及标签为 null、标注缺失时，`annotations["q"].score > 0.9` 与 `any(a.name == "q" and a.score > 0.9 for a in session_annotations)` 选择相同会话，尽管前者降级为别名连接，后者降级为 `EXISTS`。此不变量仅覆盖*肯定*形式。`annotations["q"].score is None` 有意也匹配完全没有 `q` 标注的会话，因为外连接贡献一个空行，而量词写法不匹配。因此两种惯用形式在此回答不同问题，语料库会固定差异，而非掩盖它。

<a id="api-surface"></a>

## API 接口

语言通过 GraphQL 提供，也作为 `GET /v1/projects/{project_identifier}/sessions` 的 `filter` 查询参数通过 REST 提供。GraphQL 中由 `Project` 的四个字段承载：

```graphql
sessions(..., sessionFilterCondition: String): ProjectSessionConnection!
sessionCount(timeRange: TimeRange, sessionFilterCondition: String): Int!
validateSessionFilterCondition(condition: String!): ValidationResult!
sessionFilterVocabulary: [FilterVocabularyTerm!]!
```

项目的 Span 和追踪粒度摘要字段（`recordCount`、`traceCount`、`costSummary`、延迟分位数、标注摘要）也有 `sessionFilterCondition` 参数，使这些数值可重新限定到过滤后的会话。同时接收 Span 过滤器和会话过滤器的字段，会拒绝同时传入两者的请求，因为粒度互斥，不可组合。

会话侧栏展示的会话粒度统计也接收此参数（`sessionAnnotationSummary`、`averageSessionDurationMs`、`averageTracesPerSession`、`sessionDurationMsQuantile`）。参数覆盖如此广泛正是因为它们：会话搜索框移除后，DSL 是唯一表格过滤器，无法跟随它的统计就会与屏幕行不一致。每项都通过与 `sessionCount` 相同的辅助函数限定范围，因此侧栏与表格始终描述相同会话，侧栏会话数也兼作页面匹配数。

**发布说明。**

- **Span 过滤器现在不区分大小写匹配文本。** 针对字符串的 `in` 和 `not in`，包括 `'timeout' in output.value`、`'search' in name`、所有属性或标注标签读取，都忽略大小写，与会话过滤器一致。使用 `in` 的已保存 Span 过滤器返回相同行或更多行，绝不更少；使用 `not in` 的返回相同行或更少行，绝不更多。`==` 和 `!=` 仍精确匹配。
- **`sessionFilterCondition` 是表达式，不是子串。** 变更前已有此参数的七个 Span/追踪粒度字段，原本将其视为会话输入/输出的子串。纯文本输入不再按子串匹配；请写为 `'text' in any_input or 'text' in any_output`。

<a id="the-compile-boundary"></a>

### 编译边界

调用方无需先验证即可访问这些解析器，因此所有编译会话过滤器的接口，包括会话连接、计数、摘要并行调用、四个会话粒度统计和 `validateSessionFilterCondition` 本身，都经过 `phoenix/server/session_filters.py` 中同一编译路径。编译器无法使用的表达式以 `BadRequest` 返回；规划器和数据库失败不是调用方的错，仍为服务器错误。验证采用相同路径，使 `isValid` 真实可靠：当且仅当解析器会拒绝表达式时报告无效。

<a id="validation"></a>

### 验证

`validateSessionFilterCondition` 编译条件并按 SQLite 和 PostgreSQL 两种方言渲染 SQL；任一失败都返回 `isValid: false` 及错误消息。渲染发现的是*生成*失败，而非*执行*失败；例如布尔值转数字可在两种方言渲染，在 SQLite 运行，但在 PostgreSQL 失败。因此 `isValid: true` 表示“能编译和渲染”，不表示“能在两个后端执行”。曾暴露此差距的形式（量词当数字、NUL 字面量、混合 `IN` 列表）现在在到达渲染前就被接受策略拒绝，这缩小而非消除了差距：本节承诺的始终是生成。`ValidationResult` 还携带 `warnings` 列表，是有效与无效之间的第三种通道。条件能编译但引用项目中从未观测到的标注名称时，会同时返回有效和警告：过滤器仍应用，警告列出观测到的替代名称。警告存在是因为动态名称不能作为错误，标注可能只是尚未到达。

检查引用名称无需枚举项目全部名称：验证只按项目范围查询表达式中的名称是否存在，仅在已确认未知名称、需要说明时才获取建议列表。列表有上限，因为警告会在屏幕阅读器实时区域朗读，所以只列出最接近的几个观测名称，而非项目所有标注。

<a id="vocabulary"></a>

### 词汇表

`sessionFilterVocabulary` 为每个可绑定名称返回一个项：

```graphql
type FilterVocabularyTerm {
  name: String!          # exactly as written in an expression
  type: String!          # string | number | datetime | boolean | iterable
  description: String!
  category: String!      # session | aggregate | attribute | annotation | iterable | element
  iterableName: String   # set on element fields, e.g. "spans" for spans.latency_ms
}
```

静态项及其类型来自编译器自身绑定表，具体落实防漂移承诺。构建时强制每个绑定都有说明，因此新名称不能在没有文档的情况下发布。三个手写项（`attributes[...]`、`user.id`、`metadata["key"]`）即使在空项目中也会说明属性访问形式。

两组项由数据派生：

- **观测到的属性。** 服务器扫描项目最近开始的 1000 个会话的最早根 Span，即编译器读取的同一 Span，并为每个属性键提供一个项。无论摄取时如何嵌套，键都使用规范 OTel 写法（`attributes["llm.model_name"]`），避免同一键出现为两项。嵌套写法在编译器中仍是可接受的同义形式，但不提供为词汇项。扫描有边界，因为它服务于发现，而非正确性：未列出的键手动输入仍可正常过滤。仅限制行数不能说明成本，因为扫描读取整个属性块，因此还设置字节预算。
- **观测到的标注。** 每个观测到的标注名都提供为可直接使用的 `annotations["name"].score` 和 `.label` 项，来自与属性相同的近期会话窗口，使词汇表遵循同一份契约，而非两份。

应明确说明这一统一契约带来的后果，因为用户会注意到：只有旧会话携带的名称，在存在 1000 个更新会话后会从建议中消失。它并未失效，手动输入仍与过去完全一样地过滤。词汇表帮助发现，不承诺完整性。

<a id="the-filter-bar"></a>

## 过滤栏

会话表格提供代码编辑器式过滤字段，这是唯一搜索入口。旧子串搜索框及其专用查询路径已移除，因为语言已能表达这些搜索（`session_id == '...'`、`'refund' in any_input`），而两个入口回答同一问题可能不一致。字段本身与粒度无关：会话层注入词汇表、片段、循环变量名和验证调用，因此未来追踪粒度可直接复用组件。

<a id="discovery"></a>

### 发现

输入联想是一个分区排序列表：先是近期搜索，然后是建议（片段），再是会话字段、聚合、集合、属性和标注。用户尚未输入、仅浏览时，列表最多显示五个片段和三十个字段。集合有意排在数据派生的属性和标注分区之前：核心语言必须在上限内保留，随用户数据增长的分区更适合被截断。

片段遵循两条规则。每个片段插入即有效：占位符包含可运行的示例值，绝不留空，因为填空前就报错的条件看起来像故障，而非邀请编辑。每个片段还需介绍其他片段未覆盖的内容。浏览上限内保留的五个片段各展示一种构造：文本搜索、聚合、量词、归约、嵌套推导式。

文本搜索必须拥有一个位置，不靠碰巧入选。这是已移除搜索框原本服务的查询，因此进入会话表格寻找旧字段的用户，无需先了解语言就应找到替代形式。片段同时搜索输入和输出，因为原搜索框匹配任一侧。排序与入选是两套机制：数组位置决定哪些片段进入上限，下拉列表则在分区内按字母排序已入选项，因此搜索片段带有补全加权，以排在该组首位。

<a id="writing-comprehensions"></a>

### 编写推导式

补全可感知推导式作用域。在 `for` 子句的可迭代对象位置，提供普通集合名称；在推导式主体内，提供循环变量的元素字段，始终带限定前缀（`span.latency_ms`，绝不使用编译器会拒绝的裸字段）；刚输入 `any(` 时，提供完整推导式主体。接受集合也感知位置：顶层会插入完整可运行骨架 `any(span.latency_ms > 1_000 for span in spans)`，并选中示例谓词，方便直接覆盖输入。

作用域检测器必须使用文本启发式，而非解析：编辑中的推导式不是有效 Python，因此在补全最需要发挥作用时，恰好不存在语法树。无法识别的集合名称只会降级为普通补全。

<a id="validation-in-the-loop"></a>

### 输入过程中的验证

用户输入时，字段通过 GraphQL 验证字段进行防抖验证。错误和警告以字段内单个徽标展示，消息置于提示浮层；输入联想仍是字段自行打开的唯一浮动窗口，错误不会与下拉列表争夺空间。推导式错误在对应构造下显示波浪线；由于服务器错误不含字符偏移，这只是尽力定位。只有通过验证的条件才应用到表格；编辑中的文本保存在独立状态中，无效表达式不会到达服务器。验证请求失败本身也会显示为错误，避免看似正常的字段静默丢弃过滤器。

近期搜索按项目持久化到浏览器存储。只有用户停留在某条件上数秒后，该条件才进入历史；过滤器实时应用，因此停留时间用于区分用户真正想要的搜索和输入过程中的中间状态。

<a id="future-work"></a>

## 后续工作

- **追踪粒度。** 此语言家族设计为可扩展成相同风格的追踪过滤语言；编译器已按粒度参数化。
- **推导式内的会话名称。** 解除仅允许循环变量的限制，使谓词能比较元素字段与会话字段。
- **基于 JSON 的可迭代对象。** 在访问模式稳定后，将消息、文档和事件作为可迭代对象。
- **Span 元素的累计 Token 字段。** 作为增量能力，用于确实需要汇总的树结构问题。
- **Python 执行。** 在评估器绑定中将相同表达式作为实际 Python 运行，以参考评估器语义为契约。
- **词汇表基准测试。** 现有框架衡量过滤执行，但没有衡量向过滤栏提供内容的词汇表解析器。它需要独立脚本：可配置不同项目规模层级下的不同标注名称数量、属性载荷大小和叶路径基数，报告冷运行与热运行中解码的行数和载荷字节数。
