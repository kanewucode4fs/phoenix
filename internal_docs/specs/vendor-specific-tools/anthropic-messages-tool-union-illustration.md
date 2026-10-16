<a id="anthropic-messages-api-toolunionparam-variants"></a>
# Anthropic Messages API：`ToolUnionParam` 变体

本文为 `POST /v1/messages` 的 `tools`，或 Python SDK 的 `messages.create(..., tools=[...])`，提供各类可传入结构的实用 JSON 示例。它们遵循 `anthropic/types/` 下的 TypedDict 名称，与 HTTP schema 对应。可从各节示例开始，删除不需要的字段。

**术语：** **`tool_use`** 是模型请求执行工具的助手消息块，包含 `name`、`id`、`input`。**`tool_result`** 是下一条用户消息中返回该调用输出的块，携带匹配的 `tool_use_id`。**服务端工具**，如网页搜索、Bash，在 Anthropic 一侧运行；**客户端工具**由你的代码执行。

**完整联合类型**，顺序与 SDK 相同：

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_union_param.py#L27-L44)

```python
ToolUnionParam: TypeAlias = Union[
    ToolParam,
    ToolBash20250124Param,
    CodeExecutionTool20250522Param,
    CodeExecutionTool20250825Param,
    CodeExecutionTool20260120Param,
    MemoryTool20250818Param,
    ToolTextEditor20250124Param,
    ToolTextEditor20250429Param,
    ToolTextEditor20250728Param,
    WebSearchTool20250305Param,
    WebFetchTool20250910Param,
    WebSearchTool20260209Param,
    WebFetchTool20260209Param,
    WebFetchTool20260309Param,
    ToolSearchToolBm25_20251119Param,
    ToolSearchToolRegex20251119Param,
]
```

下方永久链接使用本地克隆 [anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) 的提交 `8496c50655999cbb2c871e71331996f87025e240`。升级后请在该仓库重新运行 `git rev-parse HEAD`；如需精确对应已安装版本，应替换 URL 中的哈希。

**内置工具**，如 Bash、网页搜索，每个条目包含带版本的 **`type`**，例如 `web_search_20260209`，以及必须与 API 匹配的固定 **`name`**，例如 `web_search`。**用户定义工具**（`ToolParam`）要求 **`name`** 和 **`input_schema`**；除非使用可选 `"custom"` 判别字段，否则**省略顶层 `type`**，见第 1 节示例。

许多工具共有的可选字段：`allowed_callers`、`cache_control`、`defer_loading`、`strict`。见各节说明。

---

<a id="1-toolparam-user-defined--custom-tool"></a>
## 1. `ToolParam`（用户定义或自定义工具）

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_param.py#L33)

JSON Schema 描述模型在 `tool_use` 块中生成的参数。实际使用时强烈建议提供 `description`。

```json
{
  "name": "get_weather",
  "description": "Get the current weather for a location.",
  "input_schema": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "City name" },
      "unit": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "description": "Temperature unit"
      }
    },
    "required": ["city"]
  },
  "strict": true
}
```

显式自定义判别字段，在 API 中可选，SDK 允许 `type: "custom"`：

```json
{
  "type": "custom",
  "name": "get_weather",
  "description": "Get the current weather for a location.",
  "input_schema": {
    "type": "object",
    "properties": { "city": { "type": "string" } },
    "required": ["city"]
  }
}
```

额外可选字段：`input_examples`、`defer_loading`、`allowed_callers`、`cache_control`、`eager_input_streaming`。

**要点：** 用户工具以普通 `tool_use` 块出现，由运行器执行，并必须返回 **`tool_use_id` 匹配的 `tool_result`**。希望 API 强制符合 `input_schema` 和工具名时，使用 `strict: true`，使修改真实数据或访问外部服务的处理器执行之前，`tool_use` 载荷已经格式正确。自己的代码仍需验证授权和业务规则。

---

## 2. `ToolBash20250124Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_bash_20250124_param.py#L13)

Shell/Bash 工具，`name` 和 `type` 固定。

**要点：** Bash 在**服务端**执行，即由 Anthropic 运行，不在你的机器上调用 shell。仅希望代码执行等特定工具调用时，可结合 `allowed_callers`。

```json
{
  "type": "bash_20250124",
  "name": "bash"
}
```

---

## 3. `CodeExecutionTool20250522Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/code_execution_tool_20250522_param.py#L13)

**要点：** 这是较旧代码执行版本。新项目优先使用较新 `type` 字符串，除非必须固定旧行为。每个请求只应包含一种代码执行工具变体。

```json
{
  "type": "code_execution_20250522",
  "name": "code_execution"
}
```

---

## 4. `CodeExecutionTool20250825Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/code_execution_tool_20250825_param.py#L13)

**要点：** 这是 Python/Bash 沙箱常用的稳定一代，Agent 方案中常与**网页搜索**或**网页获取**搭配，让模型先获取事实再计算。

```json
{
  "type": "code_execution_20250825",
  "name": "code_execution"
}
```

---

## 5. `CodeExecutionTool20260120Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/code_execution_tool_20260120_param.py#L13)

较新代码执行版本，SDK 文档字符串说明其具有 REPL 持久化和守护进程语义。

**要点：** 需要沙箱内**跨轮次状态**，如变量和已加载数据，或更丰富的 Agent 执行语义时使用。依赖前应确认模型和渠道支持，包括直接 API 与云平台的差别。

```json
{
  "type": "code_execution_20260120",
  "name": "code_execution"
}
```

---

## 6. `MemoryTool20250818Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/memory_tool_20250818_param.py#L13)

**要点：** 面向**长期**会话，模型在服务端持久化结构化记忆。但保留期、个人身份信息和删除仍是你的合规责任，不能当作免费存储。

```json
{
  "type": "memory_20250818",
  "name": "memory"
}
```

---

## 7. `ToolTextEditor20250124Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_text_editor_20250124_param.py#L13)

**要点：** `str_replace_editor` 是**旧版编辑器接口**。新构建应迁移到较新 `text_editor_*` 类型，使提示词和训练匹配当前工具行为。

```json
{
  "type": "text_editor_20250124",
  "name": "str_replace_editor"
}
```

---

## 8. `ToolTextEditor20250429Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_text_editor_20250429_param.py#L13)

**要点：** `str_replace_based_edit_tool` 是补丁式编辑的**当前默认名称**。`name` 必须与 API 预期完全一致，否则工具调用无法分派。

```json
{
  "type": "text_editor_20250429",
  "name": "str_replace_based_edit_tool"
}
```

---

## 9. `ToolTextEditor20250728Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_text_editor_20250728_param.py#L13)

添加可选 `max_characters`，限制显示文件内容时的查看长度。

**要点：** 设置 `max_characters` 限制 **read_file / view** 载荷，避免大文件挤爆上下文窗口。需要摘要或分块处理时，可结合代码执行。

```json
{
  "type": "text_editor_20250728",
  "name": "str_replace_based_edit_tool",
  "max_characters": 10000
}
```

最小示例：

```json
{
  "type": "text_editor_20250728",
  "name": "str_replace_based_edit_tool"
}
```

---

## 10. `WebSearchTool20250305Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/web_search_tool_20250305_param.py#L15)

```json
{
  "type": "web_search_20250305",
  "name": "web_search",
  "max_uses": 5,
  "allowed_domains": ["arxiv.org", "pubmed.ncbi.nlm.nih.gov"],
  "user_location": {
    "type": "approximate",
    "country": "US",
    "region": "California",
    "city": "San Francisco",
    "timezone": "America/Los_Angeles"
  }
}
```

最小示例：

```json
{
  "type": "web_search_20250305",
  "name": "web_search"
}
```

`allowed_domains` 与 `blocked_domains` 互斥。

**要点：** `max_uses` 是逐请求的**预算**，可调节费用和延迟。域名允许/阻止列表控制安全性和相关性；两者互斥，避免 API 收到矛盾路由规则。

---

## 11. `WebSearchTool20260209Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/web_search_tool_20260209_param.py#L15)

字段与 `web_search_20250305` 相同，`type` 版本字符串不同。

**要点：** Anthropic 发布所需搜索行为或引用改动时，应升级 `type`。较新模型可能**要求**较新字符串，请检查对应模型 ID 的工具使用文档。

```json
{
  "type": "web_search_20260209",
  "name": "web_search",
  "max_uses": 5,
  "blocked_domains": ["example-spam.com"],
  "user_location": {
    "type": "approximate",
    "country": "US"
  }
}
```

---

## 12. `WebFetchTool20250910Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/web_fetch_tool_20250910_param.py#L15)

为模型获取 URL 内容，可选 `citations` 和域名限制。

```json
{
  "type": "web_fetch_20250910",
  "name": "web_fetch",
  "max_uses": 10,
  "max_content_tokens": 80000,
  "allowed_domains": ["docs.anthropic.com"],
  "citations": { "enabled": true }
}
```

最小示例：

```json
{
  "type": "web_fetch_20250910",
  "name": "web_fetch"
}
```

**要点：** `max_content_tokens` 防止单个大页面占满提示词；需要追溯获取片段时，启用 `citations`。优先采用**网页搜索 → 筛选 URL → 网页获取**，而非抓取整个开放网络。

---

## 13. `WebFetchTool20260209Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/web_fetch_tool_20260209_param.py#L15)

结构与 `web_fetch_20250910` 相同，更新了 `type`。

**要点：** 配置项与 `20250910` 相同。模型或文档要求较新版本时迁移 `type` 字符串；行为差异在服务中，不在类型桩中。

```json
{
  "type": "web_fetch_20260209",
  "name": "web_fetch",
  "blocked_domains": ["malicious.example"],
  "max_content_tokens": 50000
}
```

---

## 14. `WebFetchTool20260309Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/web_fetch_tool_20260309_param.py#L15)

可选字段与其他 `web_fetch_*` 工具相同，采用 `type: "web_fetch_20260309"`。新增 **`use_cache`**：用户需要最新内容时，例如快速变化的页面，设为 `false`；默认在可用时使用缓存。

最小示例：

```json
{
  "type": "web_fetch_20260309",
  "name": "web_fetch"
}
```

对此工具绕过缓存：

```json
{
  "type": "web_fetch_20260309",
  "name": "web_fetch",
  "use_cache": false,
  "max_uses": 5
}
```

**要点：** 仅当新鲜度优先于费用时，如实时仪表板、事故页面，才优先设置 `use_cache: false`。默认缓存能在同一会话重复访问相同 URL 时减少重复获取。

---

## 15. `ToolSearchToolBm25_20251119Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_search_tool_bm25_20251119_param.py#L13)

对已注册工具集进行 BM25 搜索，用于延迟加载或大型工具列表。`type` 可以是带版本字符串，或别名 `tool_search_tool_bm25`。

```json
{
  "type": "tool_search_tool_bm25_20251119",
  "name": "tool_search_tool_bm25"
}
```

```json
{
  "type": "tool_search_tool_bm25",
  "name": "tool_search_tool_bm25"
}
```

**要点：** BM25 偏好与查询的**词汇**重合。工具名和描述包含独特关键词时效果好，仅细微元数据不同的工具则不太适合。

---

## 16. `ToolSearchToolRegex20251119Param`

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_search_tool_regex_20251119_param.py#L13)

```json
{
  "type": "tool_search_tool_regex_20251119",
  "name": "tool_search_tool_regex"
}
```

```json
{
  "type": "tool_search_tool_regex",
  "name": "tool_search_tool_regex"
}
```

**要点：** 工具能按前缀、领域等**可预测模式命名**，或 BM25 漏掉短缩写时，正则搜索表现突出。应保持正则简单，昂贵模式会增加延迟。

---

<a id="appendix-a-tool_choice-not-part-of-toolunionparam"></a>
## 附录 A：`tool_choice`（不属于 `ToolUnionParam`）

`tools` 定义模型可用的**内容**；同一 `POST /v1/messages` 请求中的 **`tool_choice`** 定义**是否**必须使用工具及采用**哪种**模式。它**不是** `ToolUnionParam` 成员。

| `tool_choice` 结构 | 效果（通俗说明） |
|---------------------|-------------------------|
| `{ "type": "auto" }` | 模型可回复纯文本**或**调用工具，为默认式行为。 |
| `{ "type": "any" }` | 模型**必须**至少调用一个工具，不可仅回复文本。 |
| `{ "type": "none" }` | 模型**不得**使用工具。 |
| `{ "type": "tool", "name": "…" }` | 模型必须使用 **`name`** 匹配的工具，该工具必须存在于 `tools`。 |

`auto`、`any` 和 `tool` 可选 **`disable_parallel_tool_use`**。为 `true` 时，限制单次助手轮次的工具调用数量，精确语义见 API 参考。

**官方文档**

- [创建消息](https://docs.claude.com/claude/reference/messages_post)：请求体说明 `tool_choice`，包括 `ToolChoiceAuto`、`ToolChoiceAny`、`ToolChoiceTool`、`ToolChoiceNone` 和 `disable_parallel_tool_use`。
- [并行工具使用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)：在一个用户轮次返回多个 `tool_result` 块，以及组合 `disable_parallel_tool_use` 与 `tool_choice`。

**Python SDK（永久链接）**

- **`ToolChoiceParam` 联合类型**: [源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_choice_param.py#L15)
- **`ToolChoiceAutoParam`** (`type: "auto"`, 可选 `disable_parallel_tool_use`): [源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_choice_auto_param.py#L10)
- **`ToolChoiceAnyParam`** (`type: "any"`): [源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_choice_any_param.py#L10)
- **`ToolChoiceNoneParam`** (`type: "none"`): [源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_choice_none_param.py#L10)
- **`ToolChoiceToolParam`** (`type: "tool"`, 必需 `name`): [源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_choice_tool_param.py#L10)

**JSON 示例**，对应 `ToolChoiceParam` 结构：

```json
{ "type": "auto" }
```

```json
{ "type": "any" }
```

```json
{ "type": "none" }
```

```json
{ "type": "tool", "name": "get_weather" }
```

需要时，在 `type` 所在对象内添加 `"disable_parallel_tool_use": true`，允许用于 `auto`、`any` 和 `tool`。

**要点：** 模型发出**多个** `tool_use` 块时，应返回**一条用户消息**，其 `content` 为每个 `tool_use_id` 列出一个 `tool_result`，见[并行工具使用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)。并行调用可能竞争共享状态时，使用 `disable_parallel_tool_use`。`tool: { name }` 适合**测试或固定流水线**；开放式聊天优先使用 `auto`。

---

<a id="appendix-b-beta-only-betatoolunionparam-extras"></a>
## 附录 B：仅 Beta 的 `BetaToolUnionParam` 扩展

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/beta/beta_tool_union_param.py#L33-L56)

SDK 的 `beta_tool_union_param.py` 在稳定联合类型上增加旧工具版本，如 `bash_20241022`、`text_editor_20241022`，以及**计算机操作**和 **MCP 工具集**。按 Anthropic 文档，它们需要对应 Beta API 功能和请求头。

**要点：** Beta 工具**不能**与稳定工具互换，受请求头、模型白名单和组织设置控制。应置于功能开关后发布，并在 Anthropic 升级 Beta 版本字符串时重新测试。

**计算机操作，示例：`BetaToolComputerUse20251124Param`：**

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/beta/beta_tool_computer_use_20251124_param.py#L13)

```json
{
  "type": "computer_20251124",
  "name": "computer",
  "display_width_px": 1920,
  "display_height_px": 1080,
  "display_number": 0,
  "enable_zoom": true
}
```

**要点：** 显示宽高影响**截图分辨率和点击坐标**，数值错误会导致操作错位。应将 `enable_zoom` 视为能力位，它可能改变模型规划界面导航的方式。

**MCP 工具集（`BetaMCPToolsetParam`）：**

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/beta/beta_mcp_toolset_param.py#L15)

```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "my-server",
  "default_config": { "enabled": true, "defer_loading": false },
  "configs": {
    "some_tool": { "enabled": true, "defer_loading": true }
  }
}
```

**要点：** `default_config` 与逐工具 `configs` 可将大型 MCP 工具**延迟**至引用时加载。遵循用户工具 `defer_loading` 的模式，让只有已启用路径访问服务端。

---

<a id="summary-discriminating-type-toolunionparam"></a>
## 汇总：判别字段 `type`（`ToolUnionParam`）

[源码](https://github.com/anthropics/anthropic-sdk-python/blob/8496c50655999cbb2c871e71331996f87025e240/src/anthropic/types/tool_union_param.py#L27-L44)

**要点：** 内置工具**同时**需要带版本的 `type` 和精确固定的 `name`。只记录 `name` 会漏掉解释行为变化的版本，例如 `web_search_20250305` 与 `web_search_20260209`。

| `type` 值 | Python 参数（代表类型） | 固定 `name`（如有） |
|--------------|-------------------------------|------------------------|
| *（省略或 `"custom"`）* | `ToolParam` | *（你的工具名）* |
| `bash_20250124` | `ToolBash20250124Param` | `bash` |
| `code_execution_20250522` | `CodeExecutionTool20250522Param` | `code_execution` |
| `code_execution_20250825` | `CodeExecutionTool20250825Param` | `code_execution` |
| `code_execution_20260120` | `CodeExecutionTool20260120Param` | `code_execution` |
| `memory_20250818` | `MemoryTool20250818Param` | `memory` |
| `text_editor_20250124` | `ToolTextEditor20250124Param` | `str_replace_editor` |
| `text_editor_20250429` | `ToolTextEditor20250429Param` | `str_replace_based_edit_tool` |
| `text_editor_20250728` | `ToolTextEditor20250728Param` | `str_replace_based_edit_tool` |
| `web_search_20250305` | `WebSearchTool20250305Param` | `web_search` |
| `web_search_20260209` | `WebSearchTool20260209Param` | `web_search` |
| `web_fetch_20250910` | `WebFetchTool20250910Param` | `web_fetch` |
| `web_fetch_20260209` | `WebFetchTool20260209Param` | `web_fetch` |
| `web_fetch_20260309` | `WebFetchTool20260309Param` | `web_fetch` |
| `tool_search_tool_bm25_20251119` / `tool_search_tool_bm25` | `ToolSearchToolBm25_20251119Param` | `tool_search_tool_bm25` |
| `tool_search_tool_regex_20251119` / `tool_search_tool_regex` | `ToolSearchToolRegex20251119Param` | `tool_search_tool_regex` |

联合成员和版本字符串随 SDK 发布变化，请将已安装包与 `tool_union_param.py` 或上述永久链接比较。

---

<a id="see-also-vendor-docs"></a>
## 另请参阅（提供商文档）

官方行为、价格及各工具可用渠道（API 或云平台）会随时间变化，请通过下列链接确认。

- [创建消息（API 参考）](https://docs.claude.com/claude/reference/messages_post)：包含请求体中的 `tool_choice` 和 `tools`。
- [工具使用原理](https://console.anthropic.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)：`tool_use` / `tool_result` 循环和消息结构。
- [并行工具使用](https://console.anthropic.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)：批量 `tool_result` 块和 `disable_parallel_tool_use`。
- [工具组合](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-combinations)：支持的组合和平台注意事项。
- [网页搜索工具](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-search-tool)：引用、域名和版本管理。
- [网页获取工具](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-fetch-tool)：获取 URL 正文，常与网页搜索搭配。
- [代码执行工具](https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution-tool)：沙箱、版本（`code_execution_*`）和限制。
- [工具搜索工具](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)：BM25 / 正则延迟工具加载。
