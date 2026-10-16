<a id="vendor-specific-tools"></a>
# 提供商专用工具

<a id="summary"></a>
## 概述

Phoenix 提示词版本和 Playground 实例需要表示 LLM 提供商使用的工具定义。有些是具有共同语义结构的可移植函数工具；另一些则是提供商专用 JSON 对象，例如网页搜索、代码执行、文件搜索、计算机操作或提供商专用连接器定义。

本规格定义一个工具模型，在同一有序列表中包含两种变体：

- 函数工具：规范化、可跨提供商移植的工具定义。
- 原始工具：保留为提供商专用透传值的 JSON 工具定义。

模型保留函数工具的结构化形式，同时允许 Phoenix 无损保留和重放提供商专用定义。

<a id="goals"></a>
## 目标

- 保留提示词版本、Playground 编辑和追踪 span 中的工具定义。
- 让函数工具可跨提供商移植。
- 无需 Phoenix 理解每个提供商 schema，即可支持专用工具。
- 以 JSON 形式显示和编辑原始专用工具。
- 在 Playground 打开追踪时避免丢弃非函数工具。
- 防止原始提供商专用工具被带入不兼容的提供商或 API 变更。

<a id="non-goals"></a>
## 非目标

- Phoenix 不为所有提供商专用工具定义通用 schema。
- 不对原始专用工具进行语义验证。
- 不在提供商之间转换任意专用工具。
- 不推断外部工具连接器的凭证、认证或运行时配置。
- 不保证一个提供商接受的原始工具对另一提供商有效。

<a id="terminology"></a>
## 术语

函数工具：
具有规范化函数定义的工具，包含名称、可选描述、JSON schema 参数和可选严格性设置。

原始工具：
Phoenix 原样存储和发送的 JSON 对象，用于不适合规范化函数工具模型的提供商专用定义。

工具列表：
包含函数工具和原始工具的有序列表，顺序保持不变。

规范表示：
Phoenix 对函数工具采用的提供商无关表示。

显示表示：
Playground 编辑器中显示的函数工具提供商专用 JSON 结构。

OpenAI API 类型：
对于 OpenAI 和 Azure OpenAI，指所选 API 接口，即 Chat Completions 或 Responses。

<a id="design-principles"></a>
## 设计原则

<a id="preserve-what-phoenix-cannot-interpret"></a>
### 保留 Phoenix 无法解读的内容

工具定义是提示词可执行上下文的一部分。如果规范化会丢失字段，Phoenix 应保留原始 JSON 对象，而非丢弃或部分转换。

<a id="normalize-only-shared-semantics"></a>
### 仅规范化共享语义

函数工具具有共同的跨提供商语义结构。核心字段可移植，因此 Phoenix 可以安全规范化：

- `name`
- `description`
- `parameters`
- `strict`

提供商专用工具不具备这一性质。网页搜索或代码执行等名称相似，并不表示配置 schema 兼容。

<a id="make-provider-specific-state-explicit"></a>
### 明确提供商专用状态

原始工具是提供商专用 JSON，可以编辑、复制和删除，但 Phoenix 不将其呈现为可移植抽象。

<a id="avoid-unsafe-carryover"></a>
### 避免不安全沿用

函数工具可在提供商切换后保留，因为 Phoenix 可将其渲染为所选提供商期望的结构。原始工具不可移植，因此提供商或提供商 API 类型变化时，Phoenix 将其丢弃。

<a id="data-model"></a>
## 数据模型

<a id="python-prompt-types"></a>
### Python 提示词类型

提示词工具表示为带判别字段的工具对象列表。

```python
class PromptToolFunctionDefinition(DBBaseModel):
    name: str
    description: str = UNDEFINED
    parameters: dict[str, Any] = UNDEFINED
    strict: bool = UNDEFINED


class PromptToolFunction(DBBaseModel):
    type: Literal["function"]
    function: PromptToolFunctionDefinition


class PromptToolRaw(DBBaseModel):
    type: Literal["raw"]
    raw: dict[str, Any]


PromptTool: TypeAlias = Annotated[
    Union[PromptToolFunction, PromptToolRaw],
    Field(..., discriminator="type"),
]


class PromptTools(DBBaseModel):
    type: Literal["tools"]
    tools: Annotated[list[PromptTool], Field(..., min_length=1)]
    tool_choice: PromptToolChoice = UNDEFINED
    disable_parallel_tool_calls: bool = UNDEFINED
```

<a id="graphql-shape"></a>
### GraphQL 结构

GraphQL API 暴露相同的两种变体。

```graphql
union PromptToolFunctionPromptToolRaw = PromptToolFunction | PromptToolRaw

type PromptTools {
  tools: [PromptToolFunctionPromptToolRaw!]!
  toolChoice: PromptToolChoice
  disableParallelToolCalls: Boolean
}

input PromptToolInput @oneOf {
  function: PromptToolFunctionDefinitionInput
  raw: JSON
}

input PromptToolsInput {
  tools: [PromptToolInput!]!
  toolChoice: PromptToolChoiceInput = null
  disableParallelToolCalls: Boolean = null
}
```

<a id="typescript-playground-types"></a>
### TypeScript Playground 类型

前端在存储状态中保持同样区分。

```typescript
type FunctionTool = {
  kind: "function";
  id: number;
  editorType: PhoenixToolEditorType;
  definition: CanonicalToolDefinition;
};

type RawTool = {
  kind: "raw";
  id: number;
  editorType: PhoenixToolEditorType;
  raw: Record<string, unknown>;
};

type Tool = FunctionTool | RawTool;

type PlaygroundInstance = {
  tools: Tool[];
  toolChoice?: CanonicalToolChoice | null;
};
```

<a id="storage-format"></a>
## 存储格式

函数工具存为结构化对象。

```json
{
  "type": "tools",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather.",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string"
            }
          },
          "required": ["city"]
        },
        "strict": true
      }
    }
  ],
  "tool_choice": {
    "type": "zero_or_more"
  }
}
```

原始工具作为 JSON 对象存于同一有序工具列表中。

```json
{
  "type": "tools",
  "tools": [
    {
      "type": "raw",
      "raw": {
        "type": "web_search",
        "search_context_size": "medium"
      }
    }
  ],
  "tool_choice": {
    "type": "zero_or_more"
  }
}
```

一个提示词可以在同一有序列表中同时包含函数工具和原始工具。

<a id="conversion-rules"></a>
## 转换规则

<a id="function-tool-to-provider-display-json"></a>
### 函数工具转为提供商显示 JSON

函数工具以规范形式存储。Playground 按所选模型提供商将其渲染为专用显示 JSON。

用户可编辑显示 JSON，随后 Phoenix 再次尝试分类：

- 可解读为函数工具时，转换为规范函数工具表示。
- 是 JSON 对象但不能解读为函数工具时，保留为原始工具。

“可解读为函数工具”意味着转换提供商显示对象时，不丢弃任何提供商包装字段。函数参数中嵌套的 JSON Schema 字段保留在规范 `parameters` 对象中，包括 Phoenix 不明确理解的关键词。包装中存在无法映射到 `name`、`description`、`parameters` 或 `strict` 的字段时，整个对象存为原始工具，而非部分规范化。

<a id="provider-display-json-to-function-tool"></a>
### 提供商显示 JSON 转为函数工具

JSON 工具对象能解读为函数工具时，Phoenix 转换为规范表示。

无法解读为函数工具时，应保留为原始工具，而非仅因提供商专用就拒绝。

分类是对称的。原先存为函数工具的内容编辑后可变成原始工具；原始工具编辑后也可变成函数工具。

OpenAI Responses 函数工具采用扁平结构，应规范化为函数工具：

```json
{
  "type": "function",
  "name": "get_weather",
  "description": "Get the current weather for a location.",
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string"
      }
    },
    "required": ["city"]
  },
  "strict": true
}
```

<a id="raw-tool-passthrough"></a>
### 原始工具透传

原始工具不进行提供商显示转换。编辑器值即存储值，存储值即发送给提供商的值。

Phoenix 可格式化 JSON 以便阅读，但不得重命名字段、删除字段或改写结构。

<a id="playground-behavior"></a>
## Playground 行为

<a id="adding-tools"></a>
### 添加工具

实例没有工具时，界面可分别提供入口：

- 函数工具：创建规范函数工具。
- 原始 JSON 工具：以小型初始对象创建原始工具。

已有工具时，新增函数工具应保留现有工具并追加新工具。界面支持时，可通过单独操作添加原始 JSON 工具。

<a id="editing-tools"></a>
### 编辑工具

所有工具均使用 JSON 编辑器。每次编辑出有效 JSON 对象时，Phoenix 重新分类：

1. 对象是支持的函数工具结构时，存为函数工具。
2. 否则，存为原始工具。

编辑前，函数工具渲染为所选提供商的显示表示；原始工具按存储的 JSON 对象渲染。

验证要求：

- 值必须是语法有效的 JSON。
- 只有 JSON 对象才能更新工具状态。
- 提供商专用语义验证交给提供商 API。

无效或非对象 JSON 不覆盖最近有效状态。编辑器应本地显示语法错误；保存和执行使用最近有效的存储值。

<a id="provider-changes"></a>
### 提供商变化

所选提供商变化时：

- 保留函数工具。
- 丢弃原始工具。
- 根据剩余函数工具重新计算工具选择。
- 支持时，将消息工具调用转换为新提供商格式。

丢弃原始工具，是因为其 JSON 结构为提供商专用。

<a id="provider-api-type-changes"></a>
### 提供商 API 类型变化

提供商有多种 API 类型且类型发生变化时，丢弃原始工具，保留函数工具。

例如，不应假定原始 OpenAI Responses API 工具对象对 Chat Completions 有效。

打开 OpenAI 或 Azure OpenAI span 或提示词版本时，如果没有显式连接配置，Phoenix 应根据工具结构推断 OpenAI API 类型。仅 Responses 支持的 `tool_search`、`namespace` 等对象意味着 Responses API。

<a id="trace-ingestion"></a>
## 追踪摄入

追踪 span 可能通过序列化 JSON 属性包含工具定义。Phoenix 应独立解析各工具。

对于每个追踪工具：

1. 解析序列化 JSON。
2. 可规范化为函数工具时，创建函数工具。
3. 是 JSON 对象但非函数工具时，创建原始工具。
4. 无法解析或不是对象时，报告该工具的解析错误。

这让“在 Playground 中打开”能够保留插桩捕获的提供商专用工具。

OpenAI Responses 的扁平 `type: "function"` 结构规范化为函数工具。Responses 专有的非函数工具保留为原始工具。

<a id="prompt-version-behavior"></a>
## 提示词版本行为

提示词版本应无损往返传递工具列表，不丢失原始工具。

必需往返路径：

- GraphQL 输入到数据库存储。
- 数据库存储到 GraphQL 输出。
- GraphQL 输出到 Playground 实例。
- Playground 实例到 GraphQL 输入。
- 在支持时，从提示词版本到 SDK 代码片段。

函数工具跨这些边界时应保持规范化。忽略格式和键顺序后，原始工具应在 JSON 数据模型层面保持等价。

<a id="evaluator-behavior"></a>
## 评估器行为

LLM 评估器用提示词工具定义结构化输出。该契约依赖规范函数参数，尤其是 `label` 和可选 `explanation` 属性。

因此，评估器提示词仅允许函数工具：

- 验证应拒绝原始工具。
- 验证应拒绝包含原始工具的混合列表。
- 评估器界面可读取提示词工具联合类型，但只能从函数工具推断输出结构。

原始工具仍支持提示词存储、Playground 执行、追踪摄入和 SDK 导出，但不能作为有效评估器输出定义。

<a id="sdk-code-snippets"></a>
## SDK 代码片段

生成 SDK 片段时：

- 函数工具序列化为目标 SDK 期望的格式。
- 原始工具作为原始工具对象输出。
- 仅目标 SDK 和所选提供商支持该选择时，才输出工具选择。

目标 SDK 接受通用 `tools` 数组时，Phoenix 可直接渲染原始工具，但不应声称已经提供商验证。

TypeScript SDK 辅助函数应建模 API 工具联合类型，通过正常提供商转换路径处理函数工具，并在目标 SDK 接受原始工具对象时将其透传到载荷。

<a id="validation"></a>
## 验证

Phoenix 执行结构验证：

- 工具列表存在时，至少包含一个工具。
- 函数工具必须符合规范函数工具 schema。
- 原始工具必须为 JSON 对象。
- 工具选择结构必须有效。

Phoenix 不对原始工具执行提供商语义验证。

交给提供商的验证示例：

- 所选模型是否支持 `type: "web_search"`。
- `search_context_size` 等字段是否接受某值。
- 连接器定义是否具有有效授权。
- 工具是否兼容流式传输。

<a id="security-and-secrets"></a>
## 安全与密钥

原始工具可能包含提供商专用配置，不应作为凭证存储。

指引：

- 尽量使用 Phoenix 凭证配置。
- 界面文案不应鼓励在原始工具中嵌入 API 密钥或 bearer token。
- 提供商要求在工具定义中放凭证时，该值属于用户提供的提示词或运行时配置，应按敏感用户输入处理。
- 可能含密钥时，日志和错误应避免打印完整原始工具定义。

<a id="error-handling"></a>
## 错误处理

解析错误应明确且局部化。

建议行为：

- 编辑器中无效 JSON 本地报错，不更新存储状态。
- 编辑器中非对象 JSON 忽略，不更新存储状态。
- 追踪中无法解析的工具被省略，同时显示解析错误。
- 提供商 API 错误显示为提供商执行错误，而非 Phoenix schema 错误。

Phoenix 不应仅因工具不是函数工具，就静默丢弃有效 JSON 对象。

<a id="testing-requirements"></a>
## 测试要求

单元测试应覆盖：

- 函数工具解析和序列化。
- 原始工具解析和序列化。
- 编辑器中函数与原始工具之间对称的重新分类。
- 混合有序工具列表。
- 提供商变化时丢弃原始工具、保留函数工具。
- 提供商 API 类型变化时丢弃原始工具。
- 从 Responses 专有工具结构推断 OpenAI Responses API 类型。
- OpenAI Responses 扁平函数工具规范化。
- 追踪摄入将非函数 JSON 工具保留为原始工具。
- GraphQL 变更输入接受函数和原始工具变体。
- 提示词版本查询返回两种变体。
- SDK 片段将原始工具输出为原始对象。
- 评估器验证拒绝原始工具及函数/原始混合列表。

集成测试应覆盖：

- 创建包含原始工具的提示词版本。
- 通过 GraphQL 和客户端 API 读取同一版本。
- 在 Playground 打开包含原始提供商工具的追踪。
- 针对接受原始工具的提供商运行 Playground。

<a id="open-questions"></a>
## 待解决问题

- 界面是否应为网页搜索、代码执行等常见原始工具提供专用初始模板？
- 提供商变化导致丢弃原始工具前，Phoenix 是否应警告？
- 是否支持不改变提供商载荷的逐工具标签或描述，用于界面显示？
- SDK 片段生成在输出原始工具时是否应附注释？

<a id="acceptance-criteria"></a>
## 验收标准

- Phoenix 能保存包含函数工具、原始工具或两者的提示词版本。
- 原始工具通过 GraphQL 往返，结构不变。
- 打开含提供商专用 JSON 工具的 span 时，在 Playground 保留工具。
- 更改提供商或 API 类型时，移除原始工具、保留函数工具。
- 函数工具行为继续兼容现有提示词。
- 原始工具以 JSON 对象显示和编辑。
- 测试覆盖存储、GraphQL、Playground、追踪摄入和代码片段行为。
