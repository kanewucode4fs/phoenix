<a id="mustache-template-system-for-server-evaluators"></a>
# 服务端评估器的 Mustache 模板系统

<a id="what-we-built"></a>
## 已实现的功能

此功能为 Phoenix 服务端评估器提供完整 Mustache 模板支持，使内置分类模板能无缝处理结构化数据，并保持与 Python/TypeScript 评估库兼容。

<a id="key-capabilities"></a>
### 核心能力

1. **原生 Mustache 渲染**：用 `pystache`（Python）和 `mustache`（TypeScript）进行正确解析和渲染，替代正则占位符替换。

2. **格式化器覆盖系统**：向基础模板注入服务端专用 Mustache 片段，无需修改评估库使用的原始模板。

3. **类型感知变量提取**：区分字符串变量（`{{name}}`）与区段变量（`{{#list}}...{{/list}}`），以正确生成输入 schema。

4. **前端验证**：在 Playground 中使用原生 Mustache.js 解析器错误消息，实时验证语法。

5. **前后端一致性**：Python 和 TypeScript 使用相同变量提取方法，即简单遍历顶层 token。

---

<a id="how-we-built-it"></a>
## 实现方式

<a id="architecture-overview"></a>
### 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Template Definition Layer                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  prompts/classification_evaluator_configs/                                  │
│  ├── FAITHFULNESS_CLASSIFICATION_EVALUATOR_CONFIG.yaml  (base templates)   │
│  ├── TOOL_INVOCATION_CLASSIFICATION_EVALUATOR_CONFIG.yaml                  │
│  └── ...                                                                    │
│                                                                             │
│  prompts/formatters/server.yaml                                             │
│  └── Named Mustache snippets for structured data transformations            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Substitution Expansion Layer                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  src/phoenix/server/api/helpers/substitutions.py                           │
│                                                                             │
│  At config load time:                                                       │
│  1. Load substitution definitions from server.yaml                          │
│  2. For each message, expand {{placeholder}} → full Mustache block         │
│  3. Return expanded template ready for rendering                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Variable Extraction Layer                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Python: src/phoenix/utilities/template_formatters.py                       │
│  TypeScript: js/app/src/components/templateEditor/.../mustacheLikeTemplating.ts│
│                                                                             │
│  parse_with_types() / extractVariablesFromMustacheLike():                  │
│  1. Parse template with native Mustache parser                              │
│  2. Iterate only top-level tokens (nested tokens are encapsulated in       │
│     section children arrays, so no recursion needed)                       │
│  3. Extract top-level variables, tag as "string" or "section" type         │
│  4. For dotted paths (output.tools), extract only root (output)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Input Schema Generation                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  src/phoenix/server/api/evaluators.py :: LLMEvaluator.input_schema         │
│                                                                             │
│  For each extracted variable:                                               │
│  ├── Section variables → {} (empty schema, accepts any JSON type)          │
│  └── String variables → {"type": "string"}                                 │
│                                                                             │
│  All variables marked as required                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Input Mapping Layer                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend: js/app/src/components/evaluators/EvaluatorInputMapping.tsx         │
│  Backend:  src/phoenix/server/api/evaluators.py :: apply_input_mapping()   │
│                                                                             │
│  UI Flow:                                                                   │
│  1. Display one row per template variable from input_schema                │
│  2. User configures: path mapping (JSONPath) OR literal value              │
│  3. Mappings stored as { pathMapping: {...}, literalMapping: {...} }       │
│                                                                             │
│  Resolution Priority:                                                       │
│  1. Literal mappings (override everything)                                  │
│  2. Path mappings (JSONPath expressions against context)                   │
│  3. Direct context keys (fallback if key exists in schema but not mapped)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Template Rendering Layer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  src/phoenix/server/api/evaluators.py :: LLMEvaluator.evaluate()           │
│                                                                             │
│  Pipeline:                                                                  │
│  1. apply_input_mapping() → resolve context to template variables          │
│  2. cast_template_variable_types() → convert non-strings for string vars   │
│  3. validate_template_variables() → JSON Schema validation                 │
│  4. template_formatter.format() → pystache.render() with variables         │
│  5. Send formatted messages to LLM                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

<a id="component-roles"></a>
### 组件职责

| 组件 | 职责 |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **基础模板**（`prompts/classification_evaluator_configs/*.yaml`） | 用简单占位符定义评估器提示词，评估库和服务端共用。 |
| **格式化器**（`prompts/formatters/server.yaml`） | 具名 Mustache 片段，处理工具调用、可用工具等结构化数据，服务端专用。 |
| **替换展开器**（`substitutions.py`） | 配置加载时将简单 `{{placeholder}}` 展开为完整 Mustache 区段。 |
| **模板格式化器**（`template_formatters.py`） | 解析模板，提取带类型变量，并用 pystache 渲染。 |
| **输入 schema**（`LLMEvaluator.input_schema`） | 从变量推导 JSON Schema，区段变量接受任意类型，字符串变量接受字符串。 |
| **输入映射**（`EvaluatorInputMapping.tsx`） | 将上下文字段映射到模板变量的界面组件。 |
| **验证**（`validateMustacheSections()`） | 使用原生 Mustache.js 解析器错误消息进行前端验证。 |

---

<a id="key-decisions-and-rationale"></a>
## 关键决策及理由

<a id="1-formatter-overlay-vs-modifying-base-templates"></a>
### 1. 格式化器覆盖与修改基础模板

**决策：** 建立独立替换系统，在加载时注入 Mustache 片段，而非修改基础模板。

**理由：**

- 基础模板保留简单字符串占位符（`{{input}}`、`{{output}}`），评估库无需假定数据结构即可使用。
- 服务端可为结构化 OpenAI 风格数据注入循环、条件等复杂区段。
- 模板保持易读和易维护。
- 库模板与服务端专用格式化明确分离。

**示例：**

```yaml
# Base template (simple, library-compatible)
{{available_tools}}

# After substitution expansion (server-specific)
{{#output.available_tools}}
Tool: {{function.name}}
Description: {{function.description}}
{{/output.available_tools}}
{{^output.available_tools}}
No tools available.
{{/output.available_tools}}
```

<a id="2-top-level-variable-extraction-only"></a>
### 2. 仅提取顶层变量

**决策：** 仅提取深度为 0 的变量，不提取区段内嵌套变量。

**理由：**

- `{{#section}}...{{/section}}` 内变量从区段上下文而非根上下文解析。
- 用户已提供 `output.available_tools` 时，再要求提供 `function.name` 会造成困惑。
- 符合 Mustache 语义：区段改变其子元素的上下文。

**示例：**

```mustache
{{#output.available_tools}}
  {{function.name}}   ← NOT extracted (depth 1, resolved from each tool)
{{/output.available_tools}}
{{query}}             ← EXTRACTED (depth 0)
```

<a id="3-root-variable-extraction-for-dotted-paths"></a>
### 3. 点分路径只提取根变量

**决策：** 对 `{{output.available_tools}}`，仅将 `output` 提取为必需变量。

**理由：**

- Mustache 自动遍历嵌套属性：`context["output"]["available_tools"]`。
- 用户只需提供根对象，其余由 Mustache 处理。
- 简化输入映射：将 `output` 映射到整个输出对象，而非逐个嵌套字段。

<a id="4-type-aware-schema-generation"></a>
### 4. 类型感知 schema 生成

**决策：** 区段变量（`{{#var}}`）使用空 schema，接受任意类型；字符串变量（`{{var}}`）使用 `{"type": "string"}`。

**理由：**

- 区段遍历数组或根据真值有条件渲染，需要接受任意 JSON 类型。
- 简单插值期望字符串，因此强制类型约束。
- 支持流水线自动类型转换，将字符串变量的非字符串值转为字符串。

<a id="5-native-mustache-parser-for-validation"></a>
### 5. 使用原生 Mustache 解析器验证

**决策：** 仅使用原生 Mustache.js 解析器验证模板，将异常消息直接展示给用户。

**理由：**

- **简单性**：单一验证路径比多层正则回退更易维护和推理。
- **遵循规范**：原生解析器正确处理注释、分隔符变化等全部边界情况。
- **错误信息足够明确**：如 `Unclosed section "foo" at 13`，足以帮助用户定位修复。
- **避免正则脆弱性**：自定义正则解析器难以穷尽验证，且可能偏离规范。

**取舍：** 所有解析失败都作为错误，不区分警告和错误。用户尚在输入未完成区段时，也可能看到错误横幅。为简化代码，此代价可接受。

<a id="6-frontendbackend-parity-for-variable-extraction"></a>
### 6. 前后端变量提取一致

**决策：** Python 和 TypeScript 都只提取顶层变量，产生相同结果。

**理由：**

- 前端需要知道输入映射界面应显示哪些变量。
- 后端生成权威 input_schema。
- 结果不同会导致界面显示错误变量或遗漏变量。

**实现说明：** 两个实现都采用同一简单方法：

- **Python**：只遍历 pystache 解析树顶层节点。
- **TypeScript**：只遍历 Mustache.parse() 顶层 token。

两个解析器都将嵌套 token（区段内部）封装到区段 token 的子数组。因此，简单遍历顶层数组自然只提取顶层变量，无需递归或深度跟踪。

---

<a id="variable-identification-and-input-mapping-flow"></a>
## 变量识别和输入映射流程

<a id="how-the-ui-identifies-required-variables"></a>
### 界面如何识别必需变量

```
┌──────────────────────────────────────────────────────────────────┐
│  User edits template in Playground                               │
│  "You are evaluating {{input}}\n{{#output.tools}}..."           │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  extractVariablesFromMustacheLike() in frontend                  │
│                                                                  │
│  1. Mustache.parse() → array of top-level tokens                 │
│  2. For each token [type, value] in array:                       │
│     - If type is "#", "^", "name", "&", or "{"                  │
│       → add getRootVariableName(value) to set                    │
│  3. Return: ["input", "output"]                                  │
│                                                                  │
│  Note: Nested tokens inside sections are in children arrays,     │
│  so iterating the top-level array naturally filters them out.    │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  EvaluatorInputMapping component renders                         │
│                                                                  │
│  For each variable:                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  input    [Path ▼] [$.attributes.input.value          ▼]  │ │
│  │  output   [Literal] [__________________________]          │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  Mapping stored in evaluator state                               │
│                                                                  │
│  {                                                               │
│    pathMapping: { "input": "$.attributes.input.value" },        │
│    literalMapping: { "output": "custom value" }                 │
│  }                                                               │
└──────────────────────────────────────────────────────────────────┘
```

<a id="how-input-mapping--mustache-are-combined-at-evaluation-time"></a>
### 评估时如何组合输入映射与 Mustache

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Context (from dataset example or span)                                     │
│  {                                                                          │
│    "attributes": {                                                          │
│      "input": { "value": "What is 2+2?" },                                 │
│      "output": { "value": "4", "tools": [...] }                            │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  apply_input_mapping()                                                      │
│                                                                             │
│  Input:                                                                     │
│    - input_schema: { properties: { input: {type: string}, output: {} } }   │
│    - pathMapping: { "input": "$.attributes.input.value" }                  │
│    - literalMapping: { "output": "override" }                              │
│    - context: (above)                                                       │
│                                                                             │
│  Process:                                                                   │
│    1. Apply path mappings: input = jsonpath(context, "$.attributes...")    │
│    2. Apply literal mappings: output = "override"                          │
│    3. Fallback: any schema key not mapped but present in context           │
│                                                                             │
│  Output:                                                                    │
│    { "input": "What is 2+2?", "output": "override" }                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  cast_template_variable_types()                                             │
│                                                                             │
│  For each variable with type: "string" in schema:                          │
│    If value is not a string → convert to string                            │
│                                                                             │
│  Section variables (empty schema) pass through unchanged                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  validate_template_variables()                                              │
│                                                                             │
│  jsonschema.validate(variables, input_schema)                              │
│  - Ensures all required variables present                                   │
│  - Validates types match schema                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  template_formatter.format()                                                │
│                                                                             │
│  pystache.render(template, variables)                                       │
│                                                                             │
│  Template: "Evaluate: {{input}}"                                            │
│  Variables: { "input": "What is 2+2?" }                                    │
│  Result: "Evaluate: What is 2+2?"                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

<a id="error-handling-and-ui-feedback"></a>
## 错误处理和界面反馈

<a id="template-validation-errors-surfaced-in-playground-ui"></a>
### 模板验证错误（显示在 Playground 界面）

原生 Mustache.js 解析器检测错误，并直接展示给用户：

| 错误类型 | 示例 | 原生解析器消息 |
| --------------------------- | --------------------------------- | ------------------------------------ |
| **区段未闭合** | `{{#items}}...`，无 `{{/items}}` | `Unclosed section "items" at 13` |
| **闭合标签不匹配** | `{{#items}}...{{/item}}` | `Unclosed section "items" at 13` |
| **闭合标签无对应起始标签** | `{{/items}}` 没有起始标签 | `Unopened section "items" at 0` |
| **Mustache 语法无效** | 其他解析错误 | 解析器专用错误消息 |

全部验证错误以红色横幅显示。原生消息包含位置信息，便于定位。

<a id="runtime-errors-during-evaluation"></a>
### 运行时错误（评估期间）

| 错误 | 原因 | 处理 |
| ------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------- |
| 缺少必需变量 | 输入映射未提供全部变量 | `validate_template_variables` 抛出 `ValueError`，评估失败并在结果中记录错误 |
| 类型不匹配 | 变量不符合 schema 类型 | `validate_template_variables` 抛出 `ValueError` |
| Mustache 渲染错误 | 模板存在运行时问题 | 抛出 `TemplateFormatterError`，评估失败 |

---

<a id="edge-cases"></a>
## 边界情况

<a id="handled"></a>
### 已处理

1. **区段点分路径**：`{{#output.available_tools}}` 正确提取 `output` 为必需变量。

2. **嵌套区段**：区段内部变量不提取为顶层要求。

3. **反向区段**：正确处理 `{{^items}}No items{{/items}}`，提取 `items`。

4. **不转义变量**：`{{{html}}}` 和 `{{& html}}` 均可用，提取 `html`。

5. **标签中的空白**：`{{ name }}` 与 `{{name}}` 行为相同。

6. **注释**：提取时忽略 `{{! comment }}`。

7. **输入映射点分键**：`output.value` 等键为 react-hook-form 正确转义。

8. **禁用 HTML 转义**：Mustache 通常转义 HTML；提示词模板中禁用此行为。

<a id="unhandled--known-limitations"></a>
### 未处理或已知限制

1. **Playground 结构化输入执行**：模板可采用 Mustache 语法，但尚不支持在 Playground 中以对象或数组等结构化输入执行，仅字符串变量值可执行，应在后续 PR 处理。

2. **前端区段变量类型推断**：前端提取名称，但不区分区段和字符串类型，依赖后端 input_schema 提供类型信息。

3. **动态分隔符变化**：Mustache 支持改变分隔符（`{{=<% %>=}}`），但未使用或测试。

4. **局部模板**：当前模板不使用 Mustache 局部模板（`{{> partial}}`）。

5. **数据中的点分键**：若数据键本身包含点，例如 `{"input.query": "hello world"}`，模板 `{{input.query}}` **不能**工作。Mustache 将点作为嵌套遍历路径分隔符，因此查找 `context["input"]["query"]`，而非 `context["input.query"]`。

   这是标准 Mustache 规范限制，不存在访问字面含点键的转义语法（`{{input\.query}}`）或方括号写法（`{{input["query"]}}`）。Mustache.js 维护者明确拒绝增加此功能，因为会与现有嵌套属性语法冲突。

   **替代方法：** 将数据重构为嵌套对象（`{"input": {"query": "hello world"}}`），或避免键名使用点，改用下划线（`{"input_query": "hello world"}`）。

   说明：本次变更前也不支持，这是 Mustache 解析的固有行为。

---

<a id="handling-optional-nested-fields"></a>
## 处理可选嵌套字段

一个常见问题：`tool_calls` 等可选嵌套字段可能存在，也可能不存在，会如何处理？

<a id="input-mapping-vs-mustache-responsibilities"></a>
### 输入映射与 Mustache 的职责

| 层级 | 职责 | 验证 |
| -------------------------------------------------------------- | -------------------------------- | ----------------------------------------------- |
| **顶层变量**（`output`、`input`） | 输入映射必须提供 | JSON Schema 验证为**必需** |
| **嵌套字段**（`output.messages`、`messages[].tool_calls`） | Mustache 渲染时处理 | **不验证**，由 Mustache 平稳处理 |

<a id="example-optional-tool_calls"></a>
### 示例：可选 `tool_calls`

给定有时包含 `tool_calls` 的数据：

```json
{"output": {"messages": [
  {"role": "assistant", "content": "Hello", "tool_calls": [...]},
  {"role": "assistant", "content": "World"}  // no tool_calls
]}}
```

`server.yaml` 格式化器通过普通和反向区段处理：

```mustache
{{#output.messages}}
Message: {{role}}: {{content}}
{{#tool_calls}}
- {{function.name}}({{function.arguments}})
{{/tool_calls}}
{{^tool_calls}}
No tools called.
{{/tool_calls}}
{{/output.messages}}
```

- `{{#tool_calls}}...{{/tool_calls}}`：仅在 `tool_calls` 存在且真值为真时渲染。
- `{{^tool_calls}}...{{/tool_calls}}`：`tool_calls` 缺失、为 `null`、`false` 或空数组时渲染。

<a id="key-points"></a>
### 要点

1. **无需为可选嵌套字段设置 `None` 默认值**，Mustache 区段会平稳处理缺失、null 和空值。

2. **必须提供顶层变量**：模板使用 `{{output}}` 或 `{{#output.messages}}` 时，必须通过输入映射提供 `output`。

3. **可选数据使用区段**：可能缺失的嵌套字段始终包装在 `{{#field}}...{{/field}}` 中，不要直接裸引用 `{{field}}`。

4. **反向区段用于回退**：使用 `{{^field}}...{{/field}}` 在字段缺失时渲染备用内容。

---

<a id="open-questions"></a>
## 待解决问题

1. **界面是否区分区段与字符串变量？**
   - 当前二者采用相同输入映射界面。
   - 区段变量接受任意 JSON 类型，可能让预期字符串输入的用户困惑。

2. **是否在配置加载时验证替换展开？**
   - 当前替换缺失仅记录警告，不失败。
   - 可以更严格，提前发现配置错误。

3. **前端提取是否也返回类型信息？**
   - 可支持更丰富界面，例如表明变量需要数组。
   - 当前依赖服务端 GraphQL 响应中的 input_schema。

---

<a id="files-changed-key-components"></a>
## 改动文件（关键组件）

### Python

- `src/phoenix/utilities/template_formatters.py`：基于 pystache 的核心 Mustache 解析和渲染。
- `src/phoenix/server/api/helpers/substitutions.py`：替换展开逻辑。
- `src/phoenix/server/api/evaluators.py`：输入 schema 生成、输入映射和评估流水线。
- `prompts/formatters/server.yaml`：具名 Mustache 片段定义。
- `prompts/classification_evaluator_configs/*.yaml`：带可选替换的评估器模板。

### TypeScript

- `js/app/src/components/templateEditor/language/mustacheLike/mustacheLikeTemplating.ts`：前端 Mustache 解析、变量提取和验证。
- `js/app/src/components/evaluators/EvaluatorInputMapping.tsx`：输入映射界面。
- `js/app/src/pages/playground/PlaygroundChatTemplate.tsx`：带验证横幅的模板编辑器。

<a id="dependencies-added"></a>
### 新增依赖

- `pystache`（Python）：原生 Mustache 渲染。
- `mustache`（TypeScript）：已有依赖，版本 4.2.0。
