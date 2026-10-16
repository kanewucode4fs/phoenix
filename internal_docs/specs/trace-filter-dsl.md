<a id="trace-filter-dsl"></a>
# 追踪过滤 DSL

追踪过滤 DSL 使用简短的 Python 表达式选择追踪行，例如：

```python
error_count > 0 and any(span.span_kind == "LLM" for span in spans)
```

它与 [span 过滤 DSL](./span-filter-dsl.md) 和[会话过滤 DSL](./session-filter-dsl.md) 属于同一语言家族。上述规格定义了共享的表达式语法、类型检查、缺失值行为、大小写处理、标注访问，以及 Python 与 SQL 的对应关系。本文仅记录追踪粒度新增的能力及有意保留的差异。

核心模块：

- `src/phoenix/trace/dsl/filter.py`：共享编译器。
- `src/phoenix/trace/dsl/trace_filter.py`：追踪绑定和查询组装。
- `src/phoenix/db/trace_aggregates.py`：追踪聚合和显示根节点子查询。

<a id="scope"></a>
## 范围

`traceFilterCondition` 过滤追踪表格中的行。在本契约中，它不对项目指标、图表序列、评估汇总或计数卡片进行过滤。这些界面保留现有的项目和时间范围限定。未来若要支持跨界面过滤，必须明确引入，不能从该表格参数中推断。

<a id="api-surface"></a>
## API 接口

该语言通过 GraphQL 的 `traceFilterCondition` 参数提供，也通过 REST 的 `GET /v1/projects/{project_identifier}/traces` 上的 `filter` 查询参数提供。

<a id="trace-fields-and-aggregates"></a>
## 追踪字段和聚合

直接字段包括 `trace_id`、`start_time`、`end_time` 和 `latency_ms`。逐追踪聚合包括 span 数量、错误数量、token 数量、费用及常见 span 种类的数量。空聚合遵循共享会话粒度规则，值为 `0`。

日期时间比较值使用带明确偏移量的 ISO 8601 字符串，例如 `start_time >= "2026-07-01T00:00:00Z"` 或 `start_time >= "2026-07-01T00:00:00+00:00"`。不带时区的日期时间字面量会被拒绝。

<a id="displayed-root-contract"></a>
## 显示根节点契约

顶层 `input`、`output`、`user.id`、`metadata[...]` 和 `attributes[...]` 均从同一个代表 span 读取，该 span 是按所选根节点策略在追踪表格中显示的节点。这是“所见即所搜”规则：谓词绑定的根节点定义必须与显示行一致。词汇中没有根节点策略参数，采用默认的孤立节点感知策略。

默认从追踪的孤立节点感知根候选中选择代表节点：

1. `parent_id` 为空的 span，或
2. `parent_id` 在同一追踪中没有匹配 span 的节点。

其他追踪中存在匹配 ID，不会改变候选节点的孤立状态。`orphanSpanAsRootSpan` 为 false 时，仅考虑 `parent_id` 为空的候选。候选按 `start_time ASC, id DESC` 排序，显示并绑定首个节点。`id` 同值排序规则使具有多个候选的异常追踪也有确定结果。没有候选的追踪不具备显示根节点值。

输入、输出和属性读取采用会话粒度定义的传输键候选路径规则。因此，`input.value` 与 `{"input": {"value": ...}}` 等扁平或嵌套摄入形式会解析为相同结果，即使同时存储了 `input` 前缀键和 `input.value` 也是如此。

<a id="span-collection"></a>
## Span 集合

`spans` 包含追踪中存储的全部 span，支持 `any`、`all`、`len`、`sum`、`max` 和 `min`，包括带过滤和嵌套的推导式。`max` 和 `min` 同时接受数值和日期时间字段。按照共享语言规则，空归约结果视为缺失，与其比较为 false，显式 `is None` 检查除外。

span 的累计字段是在摄入时计算的子树汇总：

- `cumulative_error_count` 统计该 span 及其下方的 ERROR span 数量。
- `cumulative_llm_token_count_prompt`、`...completion` 和 `...total` 汇总该 span 及其下方的 LLM token 数量。

“下方”沿同一追踪中已存储的父子边确定。OpenTelemetry span ID 冲突，或孤立节点指向存储在其他位置的 span 时，不会跨追踪推断祖先关系。

<a id="parent-and-nested-relationships"></a>
## 父级和嵌套关系

`span.parent_span` 遍历到同一追踪中已存储的直接父节点。父 ID 为空，或孤立节点的父行尚未摄入时，该值均为缺失。因此可以直接表达父节点是否存在：

```python
any(span.parent_span is None for span in spans)
any(span.parent_span is not None for span in spans)
```

已存储追踪根节点的直接子节点不同于孤立节点，写法如下：

```python
any(span.parent_span is not None and span.parent_span.parent_id is None for span in spans)
```

遍历提供父节点的普通字段，包括枚举和日期时间强制转换：

```python
any(span.parent_span.span_kind == "LLM" for span in spans)
any(span.parent_span.start_time >= "2026-07-01T00:00:00Z" for span in spans)
```

`span.children` 包含同一追踪中 `parent_id` 等于该 span 的 `span_id` 的节点。`span.siblings` 包含同一已存储父节点的其他子节点；共享悬空 `parent_id` 的两个孤立节点不是兄弟节点。`span.annotations` 和 `span.cost_details` 通过已存储 span 行 ID 关联。每个嵌套关系都同时包含所属追踪或行键，以及 OpenTelemetry 边，因此其他追踪中的标识符冲突不会将元素混入谓词。

<a id="query-lowering"></a>
## 查询降级

两条 `Project.spans` 查询路径都采用探测式降级：按追踪开始时间分页器和通用 span 列表都是有限分页查询，因此关联谓词满足限制后即可停止。聚合子查询仍受候选项目、时间范围和追踪 ID 限定。扫描式降级的归约子查询（`len`、`sum`、`max` 等）使用同样边界。量词 `any()`、`all()` 及其否定形式在两种降级中都保持关联 `EXISTS` / `NOT EXISTS` 结构，不会出现非关联 `NOT IN`。之所以避免该结构，是因为 PostgreSQL 完全不会将非关联 `NOT IN` 转换为反连接：`NOT IN` 的 NULL 语义禁止这样做。估计的反集合能放入 `work_mem × hash_mem_multiplier` 时，会留下哈希 `SubPlan`；放不下时，则为外层每行执行一次 `SubPlan`。扫描式降级仍作为辅助函数默认模式，供未来无边界的分析调用使用；两种降级都必须与 Python 参考求值器一致。扫描边界是剪枝提示，而非语义过滤器；关联探测自身不带边界，因为外层语句范围已经限定反连接，在 `NOT EXISTS` 内重复限定实测更慢。因此，只有外层语句已经选择同一追踪全集时，两种降级才一致：项目相同、`Trace.start_time` 窗口相同、候选 ID 相同。传入边界的调用方必须以相同方式限定外层语句；追踪页面通过 `Trace.start_time` 实现这一点。

过滤在选择代表根节点之前，与现有追踪分页器组合。因此，每条追踪保留一条边，并保留追踪开始时间窗口语义、游标行为和分页器重试行为。

<a id="compatibility-notes"></a>
## 兼容性说明

`parent_span` 是整个过滤语言家族统一的关系名。追踪语法没有旧版 `parent` 写法，因为该写法推出时尚不存在已存储的追踪条件。

共享推导式验证器还会拒绝因嵌套而超出允许作用域的外层元素引用。早期会话过滤构造可能接受此类表达式，再悄悄将名称绑定到内层元素。拒绝该表达式是用户可见的正确性修复：已接受的条件不再在 SQL 构造期间改变含义。
