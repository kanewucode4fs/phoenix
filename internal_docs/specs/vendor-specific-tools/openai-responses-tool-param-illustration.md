<a id="openai-responses-api-toolparam-variants"></a>
# OpenAI Responses API：`ToolParam` 变体

本文为 Responses API `tools` 数组中各类可传入结构提供实用 JSON 示例。它们遵循 Python SDK（`openai/types/responses/`）中的 TypedDict 名称，与 HTTP schema 对应。可从各节示例开始，删除不需要的字段。

**阅读顺序：** 每个编号章节描述模型可调用的一**类工具**。**`tool_choice`** 是独立请求字段，见[下文](#tool-choice-configuration-tool_choice)，控制模型**是否**必须使用工具或优先选择**哪类**工具，而非工具定义本身。

**完整联合类型**，顺序与 SDK 相同：

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L311-L327)

```python
ToolParam: TypeAlias = Union[
    FunctionToolParam,
    FileSearchToolParam,
    ComputerToolParam,
    ComputerUsePreviewToolParam,
    WebSearchToolParam,
    Mcp,
    CodeInterpreter,
    ImageGeneration,
    LocalShell,
    FunctionShellToolParam,
    CustomToolParam,
    NamespaceToolParam,
    ToolSearchToolParam,
    WebSearchPreviewToolParam,
    ApplyPatchToolParam,
]
```

---

## 1. `FunctionToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/function_tool_param.py#L11)

定义模型可调用的函数。核心字段为 `type`、`name`、`parameters`、`strict`、`description`。可设置 `defer_loading`，让工具稍后通过工具搜索加载，见下方 **`ToolSearchToolParam`**。

**要点：** `strict: true` 使 OpenAI 对函数参数应用**更严格的 JSON Schema 检查**，得到更可预测、易解析的 `tool_calls`。设计 `parameters` 时应明确必填字段和枚举。各工具的 `name` 应**跨轮次稳定**，让后续消息匹配先前调用。

```json
{
  "type": "function",
  "name": "get_weather",
  "description": "Get the current weather for a location.",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "City name" },
      "unit": { "type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius" }
    },
    "required": ["city"]
  },
  "strict": true
}
```

---

## 2. `FileSearchToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/file_search_tool_param.py#L49)

搜索已上传文件，即向量存储。要求 `type` 和 `vector_store_ids`。

**要点：** `hybrid_search` 权重在稠密嵌入和词汇匹配之间取舍；提高 `score_threshold` 可减少噪声，但返回分块可能更少。多个语料库共用向量存储时，应使用元数据过滤器，避免模型取到其他租户文件。

```json
{
  "type": "file_search",
  "vector_store_ids": ["vs_abc123", "vs_def456"],
  "max_num_results": 20,
  "ranking_options": {
    "ranker": "default-2024-11-15",
    "score_threshold": 0.7,
    "hybrid_search": {
      "embedding_weight": 0.7,
      "text_weight": 0.3
    }
  }
}
```

最小示例：

```json
{
  "type": "file_search",
  "vector_store_ids": ["vs_abc123"]
}
```

---

<a id="3-computer-use-tools"></a>
## 3. 计算机操作工具

SDK 提供**两种**计算机相关工具，`type` 判别字段不同，应选择匹配集成的类型。

### `ComputerToolParam` (`type`: `"computer"`)

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/computer_tool_param.py#L10)

最小计算机工具标记，类型自身不包含显示或环境字段。

**要点：** 仅需**通用计算机操作能力**标志时使用，与产品在该 JSON 之外管理的环境设置配套。希望工具定义显式包含显示尺寸时，优先用 `computer_use_preview`。

```json
{
  "type": "computer"
}
```

### `ComputerUsePreviewToolParam` (`type`: `"computer_use_preview"`)

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/computer_use_preview_tool_param.py#L10)

预览流程，显式指定显示和环境。

**要点：** `"computer"` 是 SDK 中的最小能力标志；`"computer_use_preview"` 则固定**显示几何参数及操作系统/浏览器环境**，影响截图坐标系和操作安全。

```json
{
  "type": "computer_use_preview",
  "display_width": 1920,
  "display_height": 1080,
  "environment": "mac"
}
```

`environment` 为 `"windows"`、`"mac"`、`"linux"`、`"ubuntu"`、`"browser"` 之一。

---

## 4. `WebSearchToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/web_search_tool_param.py#L51)

网页搜索，类型为 `web_search` 或 `web_search_2025_08_26`。

**要点：** 带版本的 `type` 字符串，即 `web_search` 与 `web_search_2025_08_26`，跟踪 **API 随时间变化的行为**；应坚持使用与模型共同验证过的变体。`filters.allowed_domains` 限制结果域名，影响费用、延迟和相关性；答案需要地区信息时，添加 `user_location`。

```json
{
  "type": "web_search",
  "search_context_size": "medium",
  "filters": {
    "allowed_domains": ["pubmed.ncbi.nlm.nih.gov", "arxiv.org"]
  },
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
  "type": "web_search"
}
```

---

## 5. `Mcp`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L114)

模型上下文协议：连接远程 MCP 服务端。要求 `type: "mcp"`、`server_label`，以及 `server_url` 或 `connector_id` 之一。

```json
{
  "type": "mcp",
  "server_label": "my-mcp-server",
  "server_url": "https://mcp.example.com",
  "server_description": "Optional description of the MCP server.",
  "allowed_tools": ["tool_a", "tool_b"],
  "require_approval": "always",
  "authorization": "Bearer <token>",
  "headers": {
    "X-Custom-Header": "value"
  }
}
```

使用服务连接器，选择固定 `connector_id` 值之一：

```json
{
  "type": "mcp",
  "server_label": "gmail",
  "connector_id": "connector_gmail",
  "require_approval": "never"
}
```

`connector_id` 示例：`connector_dropbox`、`connector_gmail`、`connector_googlecalendar`、`connector_googledrive`、`connector_microsoftteams`、`connector_outlookcalendar`、`connector_outlookemail`、`connector_sharepoint`。

`allowed_tools`：工具名称数组，或过滤对象 `{ "read_only": true }` / `{ "tool_names": ["a", "b"] }`。

`require_approval`：`"always"`、`"never"` 或过滤对象。

**要点：** 应用负责 `authorization` 的 **OAuth token** 及刷新，API 不会替你完成认证界面。MCP 暴露大量服务端工具时，`require_approval` 与 `allowed_tools` 是实现**最小权限**的主要控制手段。

---

## 6. `CodeInterpreter`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L213)

运行 Python 代码。要求 `type: "code_interpreter"` 和 `container`，后者为容器 ID 字符串或配置对象。

```json
{
  "type": "code_interpreter",
  "container": "container_abc123"
}
```

使用容器配置，包括文件 ID、内存和网络策略：

```json
{
  "type": "code_interpreter",
  "container": {
    "type": "auto",
    "file_ids": ["file-abc", "file-def"],
    "memory_limit": "4g",
    "network_policy": { "type": "disabled" }
  }
}
```

`network_policy` 可为 `{ "type": "disabled" }` 或 `{ "type": "allowlist", "allowed_domains": ["https://api.example.com"] }`。

**要点：** 传入**容器 ID** 字符串可跨轮次复用文件和安装状态；`type: "auto"` 与 `file_ids` 更适合带上传输入的一次性运行。应将 `network_policy` 作为出站边界；面对不可信提示词，`disabled` 是默认安全选择。

---

## 7. `ImageGeneration`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L241)

生成或编辑图像，类型为 `image_generation`。

```json
{
  "type": "image_generation",
  "model": "gpt-image-1",
  "action": "auto",
  "size": "1024x1024",
  "quality": "high",
  "output_format": "png",
  "background": "auto",
  "moderation": "auto",
  "input_fidelity": "low",
  "output_compression": 100,
  "partial_images": 0
}
```

最小示例：

```json
{
  "type": "image_generation"
}
```

使用蒙版编辑：

```json
{
  "type": "image_generation",
  "action": "edit",
  "input_image_mask": {
    "file_id": "file-xyz",
    "image_url": "data:image/png;base64,..."
  }
}
```

**要点：** `partial_images` 用于**流式**局部预览。SDK 说明 `input_fidelity` 与部分 `model` 值存在相互约束，应验证所用图像模型组合。`input_image_mask` 编辑需要蒙版与基础图像正确配对，否则会浪费生成。

---

## 8. `LocalShell`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L304)

在本地环境执行 shell 命令，仅要求 `type`。

**要点：** 这意味着**命令在你的信任边界内执行**，例如开发机器或运行器。应像对用户影响的字符串执行 `eval` 一样对待，沙箱、白名单和审计日志比托管代码解释器更重要。

```json
{
  "type": "local_shell"
}
```

---

## 9. `FunctionShellToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/function_shell_tool_param.py#L17)

Shell 工具，可用于远程容器或本地。类型为 `shell`，`environment` 可选。

```json
{
  "type": "shell"
}
```

使用自动容器：

```json
{
  "type": "shell",
  "environment": {
    "type": "container_auto",
    "memory_limit": "4g",
    "network_policy": { "type": "disabled" }
  }
}
```

使用本地环境：

```json
{
  "type": "shell",
  "environment": {
    "type": "local"
  }
}
```

引用已有容器：

```json
{
  "type": "shell",
  "environment": {
    "type": "container_reference",
    "container_id": "container_abc123"
  }
}
```

**要点：** `container_auto` 按会话模式启动隔离环境；`container_reference` 连接已有容器，便于更快热复用；`local` 在宿主机运行，适合重视延迟且接受风险取舍的情况。

---

## 10. `CustomToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/custom_tool_param.py#L12)

支持可选输入格式的自定义工具，要求 `type: "custom"` 和 `name`。

```json
{
  "type": "custom",
  "name": "my_custom_tool",
  "description": "Optional description.",
  "format": { "type": "text" }
}
```

使用语法格式：

```json
{
  "type": "custom",
  "name": "structured_tool",
  "description": "Accepts input matching a grammar.",
  "format": {
    "type": "grammar",
    "syntax": "lark",
    "definition": "root: WORD+\n%import common.WORD"
  }
}
```

`format.syntax`：`"lark"` 或 `"regex"`。

**要点：** 自定义工具可接受**非 JSON 或语法约束**输入，例如 DSL。模型仍返回匹配 `format` 的结构化载荷，执行器应在执行副作用前验证。

---

## 11. `WebSearchPreviewToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/web_search_preview_tool_param.py#L36)

预览版网页搜索，类型为 `web_search_preview` 或 `web_search_preview_2025_03_11`。可选 `search_content_types` 控制结果种类，如文本和/或图像。包含 `user_location` 时，SDK 将该嵌套对象的 `type: "approximate"` 标为**必填**。

```json
{
  "type": "web_search_preview",
  "search_context_size": "medium",
  "search_content_types": ["text", "image"],
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
  "type": "web_search_preview"
}
```

**要点：** 预览变体适合试验，或集成明确面向**某个日期版本的工具行为**。仅需文本片段时，`search_content_types` 可避免支付图像搜索费用。

---

## 12. `ApplyPatchToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/apply_patch_tool_param.py#L10)

允许模型应用统一差异补丁，创建、更新或删除文件，仅要求 `type`。

**要点：** 应将补丁视为自动 PR：在**干净 Git worktree** 或副本中应用，运行测试，冲突时拒绝。模型可能生成畸形或重叠补丁块。适合有人工或 CI 评审的编码 Agent，不适合不经检查直接写入生产。

```json
{
  "type": "apply_patch"
}
```

---

## 13. `NamespaceToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/namespace_tool_param.py#L31)

将 `function` 和 `custom` 工具分组到一个命名空间，使调用可限定范围，例如 `crm.lookup_contact`。要求 `type`、`name`、`description` 和 `tools`。

**要点：** 合并多产品或团队工具时，命名空间减少**工具名冲突**。路由器应端到端接受限定名称，包括日志、指标和分派器。

```json
{
  "type": "namespace",
  "name": "crm",
  "description": "Customer records: search contacts and update deals.",
  "tools": [
    {
      "type": "function",
      "name": "lookup_contact",
      "description": "Find a contact by email.",
      "parameters": {
        "type": "object",
        "properties": {
          "email": { "type": "string" }
        },
        "required": ["email"]
      },
      "strict": true
    },
    {
      "type": "custom",
      "name": "import_note",
      "format": { "type": "text" }
    }
  ]
}
```

---

## 14. `ToolSearchToolParam`

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_search_tool_param.py#L11)

用于**延迟加载**工具的配置：模型可稍后通过托管或客户端执行的工具搜索发现函数。适用时与单个工具的 `defer_loading` 配套。

最小示例：

```json
{
  "type": "tool_search"
}
```

带小型参数 schema 的客户端执行搜索：

```json
{
  "type": "tool_search",
  "execution": "client",
  "description": "Search tools registered by this client.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "What to search for" }
    },
    "required": ["query"]
  }
}
```

`execution`：`"server"` 或 `"client"`。

**要点：** `execution: "client"` 时，由**你的代码**搜索延迟工具目录，仅返回待加载子集，应规划此路径的延迟和认证。`execution: "server"` 将发现工作移到托管侧，需检查模型和账号支持。

---

<a id="tool-choice-configuration-tool_choice"></a>
## 工具选择配置（`tool_choice`）

`tools` 定义模型可调用的**内容**；同一 Responses 请求中的 **`tool_choice`** 定义模型**如何**选择，例如自由选择、必须使用工具、强制特定函数、强制某种内置工具，或限定白名单。

**官方文档**

- [创建响应](https://platform.openai.com/docs/api-reference/responses/create)：请求体在 `tools` 旁包含 `tool_choice`。
- [函数调用](https://platform.openai.com/docs/guides/function-calling)：Responses API 的工具及选择模式。
- [使用工具](https://platform.openai.com/docs/guides/tools?api-mode=responses)：内置工具及其与函数工具的交互。

**Python SDK（永久链接）**

- 创建参数中的请求字段 **`tool_choice`**： [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/response_create_params.py#L222-L227)
- **`ToolChoice` 联合类型**，包括选项字符串、`allowed_tools`、托管 `type`、`function`、MCP、custom、shell、apply_patch 等: [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/response_create_params.py#L313-L322)
- 简写字面量 **`"none"` / `"auto"` / `"required"`**: [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_choice_options.py#L7)
- **白名单**对象 `type: "allowed_tools"`，包含 `mode` + `tools`: [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_choice_allowed_param.py#L11-L38)
- **强制函数** `type: "function"` + `name`: [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_choice_function_param.py#L10-L17)
- 通过 `type` **强制内置工具**，例如 `file_search`、`web_search_preview`、`code_interpreter` 等: [源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_choice_types_param.py#L10-L43)

**要点：** **`tool_choice`** 控制**允许或要求模型调用哪些工具**；函数或相关类型的 **`strict`** 控制**参数验证严格程度**。两者相互独立。**响应**可能包含 **`parallel_tool_calls`**，为 true 时，单次助手轮次可包含多个工具调用；客户端应处理每个响应零次、一次或多次调用。

---

<a id="summary-type-discriminator"></a>
## 汇总：`type` 判别字段

[源码](https://github.com/openai/openai-python/blob/58184ad545ee2abd98e171ee09766f259d7f38cd/src/openai/types/responses/tool_param.py#L311-L327)

**要点：** 内置工具通过表中 `type` 字符串标识。用户定义的**函数**工具用 `type: "function"`；**自定义**工具用 `type: "custom"`。遥测中应记录工具 `type` 和 `name`，将行为、计费和延迟关联到正确工具定义。

| `type` 值 | Python 类型（SDK） |
|--------------|---------------------|
| `function` | `FunctionToolParam` |
| `file_search` | `FileSearchToolParam` |
| `computer` | `ComputerToolParam` |
| `computer_use_preview` | `ComputerUsePreviewToolParam` |
| `web_search` / `web_search_2025_08_26` | `WebSearchToolParam` |
| `mcp` | `Mcp` |
| `code_interpreter` | `CodeInterpreter` |
| `image_generation` | `ImageGeneration` |
| `local_shell` | `LocalShell` |
| `shell` | `FunctionShellToolParam` |
| `custom` | `CustomToolParam` |
| `namespace` | `NamespaceToolParam` |
| `tool_search` | `ToolSearchToolParam` |
| `web_search_preview` / `web_search_preview_2025_03_11` | `WebSearchPreviewToolParam` |
| `apply_patch` | `ApplyPatchToolParam` |

---

<a id="see-also-vendor-docs"></a>
## 另请参阅（提供商文档）

官方行为、价格和模型可用性会随时间变化，请通过下列链接确认。

- [结构化模型输出](https://developers.openai.com/docs/guides/structured-outputs)：JSON Schema / `strict` 工具和可靠性。
- [Responses API 新工具和功能](https://openai.com/index/new-tools-and-features-in-the-responses-api/)：内置工具和 MCP 能力的产品概览。
- [文件搜索](https://developers.openai.com/api/docs/guides/tools-file-search)：向量存储、混合搜索和元数据过滤。
- [网页搜索](https://developers.openai.com/api/docs/guides/tools-web-search)：引用、搜索模式和依据支持行为。
- [远程 MCP](https://platform.openai.com/docs/guides/tools-remote-mcp)：连接器、OAuth 和服务端 URL 工具。
- [创建响应](https://platform.openai.com/docs/api-reference/responses/create)：在 `tools` 旁包含 `tool_choice`。
