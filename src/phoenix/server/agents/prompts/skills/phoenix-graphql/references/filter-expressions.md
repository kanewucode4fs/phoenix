<a id="filter-expressions"></a>

# 筛选表达式

筛选条件是由 Phoenix 编译为 SQL 的 Python 布尔表达式。共有三种筛选语言，分别用于跨度、追踪和会话，通过参数名选择语言，各自的词汇不能混用。

| 语言 | 参数 | 保留对象 | 支持的位置 |
| --- | --- | --- | --- |
| 跨度筛选 | `filterCondition` | 单个跨度 | `Project.spans`、`Trace.spans`、项目汇总指标（`recordCount`、`tokenCountTotal`、`costSummary`、`latencyMsQuantile` 等）、Python 客户端的 `SpanQuery().where(...)`、界面跨度筛选栏 |
| 追踪筛选 | `traceFilterCondition` | 匹配追踪的所有跨度 | `Project.spans`、界面追踪筛选栏、`GET /v1/projects/{id}/traces` 的 `filter` 查询参数，以及 `client.traces.get_traces(...)`（Python）和 `getTraces({...})`（TypeScript）的 `filter` 参数 |
| 会话筛选 | `sessionFilterCondition` | 会话 | `Project.sessions`、项目汇总指标、界面会话筛选栏、`GET /v1/projects/{id}/sessions` 的 `filter` 查询参数，以及 `client.sessions.list(...)`（Python）和 `listSessions({...})`（TypeScript）的 `filter` 参数 |

`filterCondition` 和 `traceFilterCondition` 可在 `Project.spans` 中组合，得到匹配追踪内的匹配跨度。对于同时接收两者的汇总指标，`filterCondition` 与 `sessionFilterCondition` 互斥。

<a id="checking-a-condition"></a>

## 检查条件

| 需求 | `Project` 上的 GraphQL 字段 |
| --- | --- |
| 运行前验证 | `validateSpanFilterCondition(condition:)`、`validateTraceFilterCondition(condition:)`、`validateSessionFilterCondition(condition:)` → `{ isValid errorMessage }` |
| 列出可绑定名称 | `traceFilterVocabulary`、`sessionFilterVocabulary` → `{ name type category description iterableName }` |
| 跨度筛选名称 | 没有词汇字段；[跨度筛选](#span-filter)中的表格是完整清单 |

跨度筛选未返回记录，可能是名称拼错，而非没有匹配数据。在断言没有数据前，先对照词汇清单检查拼写。

<a id="syntax-shared-by-all-three-languages"></a>

## 三种语言共享的语法

<a id="operators"></a>

### 运算符

| 类别 | 接受的写法 | 拒绝的写法 |
| --- | --- | --- |
| 比较 | `==` `!=` `<` `<=` `>` `>=`；链式比较：`500 < latency_ms <= 2000` | `=` |
| 缺失值 | `is None`、`is not None` | `is null`、`null`、对其他值使用 `is` |
| 成员关系 | `x in [...]` 为精确匹配；`'text' in field` 为不区分大小写的子串匹配；支持 `not in` | 列表内的 `None`；左侧为字面量，如 `1 in [1, 2]`；`like` |
| 逻辑 | `and`、`or`、`not`、括号 | `&&`、`\|\|`、`&`、`\|`、`!` |
| 算术 | `+` `-` `*` `/` `%` | `**`、`//`、位运算符 |
| 类型转换 | `float(x)`、`int(x)`、`str(x)` | `bool(x)`、其他函数 |
| 推导式 | 对声明的集合使用 `any`、`all`、`len`、`sum`、`max`、`min`，如 `any(d.cost > 0 for d in cost_details)`；`len` 接收列表推导式 | 方法调用，如 `name.startswith(...)`；`len(name)` |

<a id="literals"></a>

### 字面量

| 类型 | 正确写法 | 错误写法 |
| --- | --- | --- |
| 字符串 | `'LLM'` 或 `"LLM"` | 不带引号的 `LLM` |
| 数字 | `100`、`0.5` | 带引号的 `'100'` |
| 布尔值 | `True`、`False` | `true`、`false` |
| 缺失值 | `None` | `null`、`nil` |
| 日期时间 | 带偏移量的 ISO 8601，如 `'2026-09-01T00:00:00Z'`、`'2026-09-01T00:00:00+00:00'` | 不带偏移量 |
| 列表 | `['LLM', 'TOOL']`，全部元素类型一致 | 混合类型、`None` 元素 |

<a id="rules-that-differ-from-python"></a>

### 与 Python 不同的规则

- 缺失值在所有比较中都不匹配，包括 `!=`。没有 `metadata['tier']` 的跨度既不匹配 `metadata['tier'] == 'premium'`，也不匹配 `metadata['tier'] != 'premium'`。应显式列出缺失情况：`metadata['tier'] != 'premium' or metadata['tier'] is None`。
- 键不存在或存储的 JSON 值为 `null` 时，`is None` 都为真。
- `and`、`or`、`not` 的每个操作数本身都必须是条件。`name == 'x' and
  metadata['flag']` 会被拒绝，应写为 `metadata['flag'] == True`。
- 整个表达式必须是条件，单独的 `True` 或单独字段会被拒绝。
- `'text' in field` 忽略大小写，`==` 和列表成员关系则精确匹配。
- 标注访问器提供 `.label`（字符串）、`.score`（数字）、`.explanation`（字符串）和 `.identifier`（字符串）。单独的访问器用于检查是否存在，例如 `annotations['quality']`。
- `.identifier` 永不缺失：未指定时，标注中的值为 `''`，应通过 `== ''` 检查，而非 `is None`。

<a id="span-filter"></a>

## 跨度筛选

<a id="root-spans"></a>

### 根跨度

没有 `traces` 连接，也没有根跨度参数。根跨度作用域通过 `filterCondition` 中的子句限定，可与其他所有条件组合。界面的追踪表使用 `spans(filterCondition: "parent_span is None", traceFilterCondition: ...)`。

| 子句 | 保留对象 | 使用场景 |
| --- | --- | --- |
| `parent_id is None` | 没有父 ID 的跨度 | 默认选择 |
| `parent_span is None` | 上述跨度，以及父跨度从未收到的孤儿跨度 | 希望获取全部顶层跨度，包括父跨度丢失的情况 |

通常每条追踪只有一个根跨度；碎片化追踪可能有多个。

<a id="vocabulary"></a>

### 词汇

此表为完整清单。任何未列出的标识符都会被视为属性路径。

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `span_id`、`trace_id`、`parent_id` | 字符串 | OpenTelemetry 十六进制 ID |
| `name` | 字符串 | 跨度名称 |
| `span_kind` | 枚举 | `'CHAIN'`、`'LLM'`、`'RETRIEVER'`、`'EMBEDDING'`、`'TOOL'`、`'AGENT'`、`'RERANKER'`、`'GUARDRAIL'`、`'EVALUATOR'`、`'PROMPT'`、`'DECISION'`、`'UNKNOWN'`；字面量会自动转为大写 |
| `status_code` | 枚举 | `'OK'`、`'ERROR'`、`'UNSET'`；字面量会自动转为大写 |
| `status_message` | 字符串 | 错误文本 |
| `latency_ms` | 数字 | |
| `start_time`、`end_time` | 日期时间 | |
| `cumulative_llm_token_count_prompt`、`cumulative_llm_token_count_completion`、`cumulative_llm_token_count_total` | 数字 | 当前跨度及其后代 |
| `llm.token_count.prompt`、`llm.token_count.completion`、`llm.token_count.total` | 数字 | 仅当前跨度 |
| `total_cost`、`prompt_cost`、`completion_cost` | 数字 | 没有费用记录时为 `0` |
| `cost_details` | 集合 | 仅可迭代；元素包含 `token_type`（字符串）、`is_prompt`（布尔值）、`cost`、`tokens`、`cost_per_token`（数字） |
| `parent_span` | 保留名称 | 只支持 `is None` / `is not None`；`parent_span.name` 被拒绝 |
| `annotations['name']` | 标注 | 跨度自身的标注；`evals['name']` 是旧别名 |
| `trace_annotations['name']` | 标注 | 该跨度所属追踪的标注 |
| `attributes[...]`、`metadata[...]`、其他带点名称 | 属性 | JSON 属性路径，读取前类型未知 |

仍接受以下旧写法：`context.span_id`、`context.trace_id`、`cumulative_token_count.prompt`、`cumulative_token_count.completion`、`cumulative_token_count.total`。

<a id="attributes"></a>

### 属性

| 写法 | 读取内容 |
| --- | --- |
| `llm.model_name`、`attributes['llm.model_name']`、`attributes['llm']['model_name']` | 同一个属性 |
| `metadata['topic']` | `attributes['metadata']['topic']` |
| `input.value`、`output.value` | 跨度输入和输出文本 |
| `input.mime_type`、`output.mime_type` | 载荷类型 |
| `attributes['tags'][0]` | JSON 数组的第一个元素 |
| `user.id` | `attributes['user']['id']` |

属性类型在读取行之前未知。与数字比较时按数字读取，与 `True` 或 `False` 比较时按布尔值读取，其他情况按文本读取。值无法转换的行会被排除，不会报错。`float(x)`、`int(x)` 和 `str(x)` 可强制按指定类型读取。

<a id="annotations"></a>

### 标注

访问器决定标注层级。使用错误层级仍可编译，但不会匹配任何内容。

| 访问器 | 匹配的标注位置 |
| --- | --- |
| `annotations['name']` | 跨度自身 |
| `evals['name']` | 跨度自身，旧别名 |
| `trace_annotations['name']` | 跨度所属的追踪 |

`trace_annotations[...]` 匹配带有标注追踪中的全部跨度。添加 `parent_id is None` 可使每条追踪返回一行。通过 `Project.spanAnnotationNames` 和 `Project.traceAnnotationNames` 发现名称。

同一名称可以对应同一跨度上的多条记录，例如每轮评审一条、每次编码会话一条，因为标注以 `(name, span, identifier)` 为键。`.identifier` 用于选中其中一条：`annotations['note'].identifier == 'coding-run:1'` 仅读取该次运行写入的记录；与 `.label` 或 `.score` 组合时，约束作用于同一条记录。

<a id="spellings-that-compile-and-match-nothing"></a>

### 能编译但匹配不到内容的写法

未知名称会回退为属性路径，因此以下情况不会报错。

| 原写法 | Phoenix 的解释 | 应改为 |
| --- | --- | --- |
| `span_kind == LLM` | 名为 `LLM` 的属性 | `span_kind == 'LLM'` |
| `parent_id == null` | 名为 `null` 的属性 | `parent_id is None` |
| `error_count > 0`、`num_spans > 3`、`token_count_total > 0` | 属性；这些名称实际属于追踪筛选 | `traceFilterCondition`，或使用 `status_code == 'ERROR'` 筛选跨度 |
| `'refund' in input`、`output is None` | `input` / `output` 属性对象 | `'refund' in input.value`、`output.value is None` |
| `annotations.q.label == 'x'` | 属性路径 `annotations.q.label` | `annotations['q'].label == 'x'` |
| `attributes.llm.model_name == 'x'` | 名为 `attributes` 的属性 | `llm.model_name == 'x'` |
| `is_root == True`、`user_id == 'u1'` | 属性 | `parent_id is None`、`user.id == 'u1'` |

<a id="examples"></a>

### 示例

```python span-filter
parent_id is None
parent_span is None
parent_id is None and status_code == "ERROR"
parent_id is None and latency_ms > 5000
span_kind == "LLM" and "gpt-4o" in llm.model_name
span_kind in ["LLM", "RETRIEVER"]
span_kind == "TOOL" and tool.name == "search"
status_code == "ERROR" and "timeout" in status_message
"refund" in input.value
"refund" in input.value or "refund" in output.value
output.value is None
metadata["topic"] == "billing"
metadata["tier"] != "premium" or metadata["tier"] is None
user.id == "u1"
float(metadata["retry_count"]) > 1
"true" in str(metadata["flag"])
attributes["tags"][0] == "urgent"
start_time > "2026-09-01T00:00:00Z" and end_time < "2026-09-02T00:00:00Z"
500 < latency_ms <= 2000
cumulative_llm_token_count_total > 10000
llm.token_count.total > 4000
total_cost > 0.01
any(d.token_type == "input" and d.tokens > 1000 for d in cost_details)
sum(d.cost for d in cost_details) > 0.01
annotations["correctness"].label == "incorrect"
annotations["hallucination"].score > 0.5
annotations["correctness"].label is None
annotations["correctness"]
annotations["note"].identifier == "coding-run:1"
annotations["note"].identifier == "coding-run:1" and annotations["note"].label == "bad"
evals["correctness"].label == "incorrect"
trace_annotations["quality"].label == "poor"
parent_id is None and trace_annotations["quality"].score < 0.5
not span_kind == "LLM"
span_kind == "LLM" and (latency_ms > 5000 or status_code == "ERROR")
```

<a id="trace-filter"></a>

## 追踪筛选

匹配整条追踪，名称严格校验：未知名称会被拒绝，并返回“是否想输入……”建议。跨度筛选名称（`span_kind`、`status_code`、`parent_id`、`input.value`）在此未知。跨度级问题应通过对 `spans` 的推导式表达。

<a id="vocabulary-1"></a>

### 词汇

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `trace_id` | 字符串 | |
| `start_time`、`end_time` | 日期时间 | |
| `latency_ms` | 数字 | |
| `num_spans`、`error_count`、`tool_span_count`、`llm_span_count` | 数字 | 汇总值；为空时为 `0`，永不为 null |
| `token_count_prompt`、`token_count_completion`、`token_count_total` | 数字 | 汇总值 |
| `prompt_cost`、`completion_cost`、`total_cost` | 数字 | 汇总值 |
| `input`、`output` | 字符串 | 根跨度的输入输出文本：`'refund' in input`、`output is None` |
| `user.id` | 字符串 | 根跨度的用户 ID，唯一支持的带点名称 |
| `metadata['k']`、`attributes['k']` | 属性 | 从根跨度读取；其他根属性可使用 `attributes["input.value"]` |
| `trace_annotations['name']` | 标注 | 此处拒绝 `annotations[...]` |
| `spans` | 集合 | 元素字段：`name`、`parent_id`、`span_kind`、`status_code`、`start_time`、`end_time`、`latency_ms`、`llm_token_count_prompt`、`llm_token_count_completion`、`llm_token_count_total`、`cumulative_error_count`、`cumulative_llm_token_count_prompt`、`cumulative_llm_token_count_completion`、`cumulative_llm_token_count_total`；关系：`parent_span`（可遍历）、`children`、`siblings`、`annotations`、`cost_details` |
| `trace_annotations`、`span_annotations` | 集合 | 元素包含 `name`、`label`、`score`、`identifier` |
| `span_cost_details` | 集合 | 元素包含 `token_type`、`is_prompt`、`cost`、`tokens`、`cost_per_token` |

根跨度读取（`input`、`output`、`user.id`、`metadata`、`attributes`）绑定到追踪表展示的代表性根跨度。推导式内部只能引用循环变量的字段。

<a id="examples-1"></a>

### 示例

```python trace-filter
error_count > 0 and latency_ms > 1000
num_spans > 10 and total_cost > 0.25
"refund" in input
output is None
user.id == "u1"
metadata["topic"] == "support"
attributes["llm.model_name"] == "gpt-4o"
trace_annotations["quality"].score < 0.5
trace_annotations["quality"].identifier == "review-2"
start_time >= "2026-07-01T00:00:00Z"
any(span.status_code == "ERROR" for span in spans)
any(span.span_kind == "LLM" and span.latency_ms > 5000 for span in spans)
any(span.parent_span is None and span.status_code == "ERROR" for span in spans)
any(span.parent_span.span_kind == "LLM" and span.span_kind == "TOOL" for span in spans)
any(annotation.label == "hallucinated" for annotation in span_annotations)
len([span for span in spans if span.span_kind == "TOOL"]) > 3
sum(detail.cost for detail in span_cost_details if detail.is_prompt) > 0.10
```

<a id="session-filter"></a>

## 会话筛选

匹配会话。一个会话是一段对话，其中每条追踪通常代表一轮。与追踪筛选一样，名称严格校验。

<a id="vocabulary-2"></a>

### 词汇

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | 字符串 | |
| `start_time`、`end_time` | 日期时间 | |
| `duration_ms` | 数字 | |
| `num_traces`、`num_traces_with_error`、`tool_span_count`、`llm_span_count` | 数字 | 汇总值，空时为 `0` |
| `token_count_prompt`、`token_count_completion`、`token_count_total` | 数字 | 汇总值 |
| `prompt_cost`、`completion_cost`、`total_cost` | 数字 | 汇总值 |
| `first_input`、`last_output` | 字符串 | 开场输入和最终输出，支持 `==`、`in`、`is None` |
| `any_input`、`any_output` | 仅支持包含判断 | `'refund' in any_input`，不能使用 `any_input == ...` |
| `user.id`、`metadata['k']`、`attributes['k']` | 属性 | 从会话的根跨度读取 |
| `session_annotations['name']` | 标注 | |
| `traces` | 集合 | 元素包含 `start_time`、`end_time`、`latency_ms` 及其自身的 `spans` |
| `spans`、`session_annotations`、`span_annotations`、`span_cost_details` | 集合 | 与追踪筛选相同 |

<a id="examples-2"></a>

### 示例

```python session-filter
num_traces > 5 and total_cost > 0.50
num_traces_with_error / num_traces > 0.2
duration_ms > 60000
"refund" in any_input
last_output is not None
session_annotations["Quality"].score <= 0.5
session_annotations["Quality"].identifier == "review-2"
any(span.status_code == "ERROR" for span in spans)
all(trace.latency_ms < 30000 for trace in traces)
any(len([span for span in trace.spans if span.span_kind == "TOOL"]) > 5 for trace in traces)
```
