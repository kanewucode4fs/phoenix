<a id="google-gen-ai-sdk-google-genai-tool-and-nested-tool-types"></a>
# Google Gen AI SDK（`google-genai`）：`Tool` 及嵌套工具类型

本文提供 **`Tool`** 及其组合的嵌套类型的实用 JSON/字典结构。经过客户端规范化后，它们会传入 `models.generate_content` 及相关 API 的 `GenerateContentConfig.tools` / `tools`。

与 OpenAI 的 `ToolParam` 或 Anthropic 的 `ToolUnionParam` 不同，每个列表条目都是**一个 `Tool` 对象**，包含许多**可选**键，只需启用所需能力，例如仅 `function_declarations` 或仅 `google_search`。SDK 文档字符串逐字段注明 **Gemini API 与 Vertex AI** 支持情况，可先据此检查兼容性，再查阅所用接口的 Google 文档确认。

**模型与字典：** 请求载荷对应 **`Tool`** / **`ToolDict`**，即键相同的 Pydantic 模型和 TypedDict。

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4725-L4821)

工具列表类型为 **`ToolListUnion`**：每个条目可以是 `Tool`、被包装成函数声明的**可调用对象**，或在 MCP 可选依赖可导入时使用的 MCP 客户端类型。

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4834-L4835)

下方永久链接使用本地克隆 [googleapis/python-genai](https://github.com/googleapis/python-genai) 的提交 `b2629a44d389370af16e9ad68af676bb565eb9b9`。升级 `google-genai` 后，应在该仓库运行 `git rev-parse HEAD`，或查看已安装的 `google/genai/types.py`，并按需更新行号锚点。

---

<a id="tool--top-level-keys-optional-unless-noted"></a>
## `Tool`：顶层键（除非注明，否则可选）

| 键 | 嵌套类型（Python） | SDK 说明（简写） |
|-----|----------------------|-------------------|
| `function_declarations` | `list[FunctionDeclaration]` | 客户端执行函数 |
| `google_search` | `GoogleSearch` | 模型内 Google 搜索 |
| `google_maps` | `GoogleMaps` | 地图依据支持 |
| `url_context` | `UrlContext` | URL 上下文检索 |
| `file_search` | `FileSearch` | 语义文件搜索存储，SDK 不支持 Vertex AI |
| `code_execution` | `ToolCodeExecution` | 模型代码执行，SDK 不支持 Gemini API |
| `enterprise_web_search` | `EnterpriseWebSearch` | Vertex AI Search / Sec4，SDK 不支持 Gemini API |
| `retrieval` | `Retrieval` | 外部或 Vertex 检索，SDK 不支持 Gemini API |
| `google_search_retrieval` | `GoogleSearchRetrieval` | 通过 Google 搜索提供依据 |
| `parallel_ai_search` | `ToolParallelAiSearch` | Parallel.ai，SDK 不支持 Gemini API |
| `computer_use` | `ComputerUse` | 计算机操作及自动函数声明 |
| `mcp_servers` | `list[McpServer]` | 基于 HTTP 的 MCP，SDK 不支持 Vertex AI |

**要点：** SDK 字段文档字符串是最快的 **Gemini 与 Vertex** 兼容性筛选方式。如果注明不支持 Gemini API，就不要基于该键设计可移植功能。一个 `Tool` 组合许多键在 JSON 上有效，但可能在特定接口运行时失败。

---

## 1. `function_declarations` — `FunctionDeclaration`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4276)

OpenAPI 风格声明。**`parameters`**（SDK `Schema`）与 **`parameters_json_schema`** **互斥**；**`response`** 与 **`response_json_schema`** 同样互斥。

以下示例采用 SDK 风格 `Schema` 字典，`type` 值如 `OBJECT`、`STRING`、`INTEGER`；见仓库中的 `google/genai/tests/transformers/test_t_tool.py`：

```json
{
  "function_declarations": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a location.",
      "parameters": {
        "type": "OBJECT",
        "properties": {
          "city": {
            "type": "STRING",
            "description": "City name"
          },
          "unit": {
            "type": "STRING",
            "enum": ["celsius", "fahrenheit"]
          }
        },
        "required": ["city"]
      }
    }
  ]
}
```

另一种单对象参数写法采用 **JSON Schema**，与 `parameters` 互斥：

```json
{
  "function_declarations": [
    {
      "name": "register_user",
      "description": "Register a user.",
      "parameters_json_schema": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "age": { "type": "integer" }
        },
        "additionalProperties": false,
        "required": ["name", "age"],
        "propertyOrdering": ["name", "age"]
      }
    }
  ]
}
```

可选字段：用于输出 schema 的 `response` / `response_json_schema`；以及 `behavior`，用于 Bidi，按 SDK 文档字符串可能仅支持 Vertex。

**要点：** `parameters`（枚举式 `Schema`）与 `parameters_json_schema` 必须**二选一**，API 无法合并。输出 schema（`response*`）可为下游解析器提供带类型的工具输出，无需第二次模型调用。

---

## 2. `google_search` — `GoogleSearch`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4175)

启用搜索；省略 **`search_types`** 时默认为网页搜索。嵌套的 `web_search` / `image_search` 是空标记对象，模型中为 `pass`。

```json
{
  "google_search": {
    "search_types": {
      "web_search": {},
      "image_search": {}
    }
  }
}
```

默认写法，隐式使用网页搜索：

```json
{
  "google_search": {}
}
```

可选嵌套字段包括 `blocking_confidence`、`exclude_domains`、`time_range_filter`，后者包含 ISO 日期时间 `start_time` / `end_time`。请核对 SDK 文档字符串和 Google 文档，**并非**所有接口都支持全部字段。

**要点：** 响应包含 **`groundingMetadata`**，包括查询、网页分块和引用区间。应在界面中呈现，以提高可信度并便于调试。`image_search` 会影响多模态搜索费用和延迟；仅默认网页搜索已足够时，可省略 `search_types`。

---

## 3. `google_maps` — `GoogleMaps`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L3427)

```json
{
  "google_maps": {
    "enable_widget": true
  }
}
```

可选 `auth_config`，SDK 文档字符串注明 Gemini API 不支持。

**要点：** 地图依据支持最适合**查询中涉及地点**的任务，如营业时间、路线和附近地点。产品支持交互地图界面时，`enable_widget` 与之对应。Gemini API 没有 `auth_config` 时，应仅按**公开**地图数据处理。

---

## 4. `url_context` — `UrlContext`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4624)

载荷为空，只要该字段存在即启用工具。

**要点：** 检查响应中的 **`url_context_metadata`**，了解实际检索的 URL，以及使用缓存还是实时获取。适合与 `google_search` 搭配，让模型先**发现**链接，再**深入阅读**其中几个。

```json
{
  "url_context": {}
}
```

---

## 5. `file_search` — `FileSearch`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4036)

```json
{
  "file_search": {
    "file_search_store_names": [
      "fileSearchStores/my-file-search-store-123"
    ],
    "top_k": 8,
    "metadata_filter": "optional-filter-expression"
  }
}
```

**要点：** File Search 是**托管 RAG**。前期需要配置存储和导入，以省去分块和嵌入管道。`metadata_filter` 可按租户或文档类型限定范围，无需每个客户单独建存储。

---

## 6. `code_execution` — `ToolCodeExecution`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4221)

类型定义中为空对象。

```json
{
  "code_execution": {}
}
```

SDK 文档字符串注明：**Gemini API 不支持**。

**要点：** SDK 中该字段用于 **Vertex / AI Studio** 类接口。如果应用调用**面向消费者的 Gemini API**，应省略 `code_execution` 或运行时检测能力，否则可能导致请求错误。

---

## 7. `enterprise_web_search` — `EnterpriseWebSearch`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4244)

```json
{
  "enterprise_web_search": {
    "exclude_domains": ["example.com"],
    "blocking_confidence": "BLOCK_HIGH_AND_ABOVE"
  }
}
```

SDK 文档字符串注明：**Gemini API 不支持**。`blocking_confidence` 在 SDK 中采用 `PhishBlockThreshold`。

**要点：** 这是 Vertex 上的**企业 / Sec4** 网页搜索路径，合规和计费不同于消费者 Gemini。`exclude_domains` 可简单限制已知恶意或不符合品牌要求的域名，以控制滥用。

---

## 8. `retrieval` — `Retrieval`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L3990)

定义 Vertex 风格检索。选择 **`vertex_ai_search`**、**`vertex_rag_store`** 或 **`external_api`** 之一，各自在 `types.py` 有独立嵌套结构。

最小占位结构：

```json
{
  "retrieval": {
    "vertex_ai_search": {}
  }
}
```

SDK 文档字符串注明：**Gemini API 不支持**。

**要点：** `vertex_ai_search`、`vertex_rag_store` 和 `external_api` 是**三种不同架构**。应选一个分支，按其设计认证和延迟预期，不要全部填写并期望 API 自动合并。

---

## 9. `google_search_retrieval` — `GoogleSearchRetrieval`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4567)

```json
{
  "google_search_retrieval": {
    "dynamic_retrieval_config": {
      "mode": "MODE_DYNAMIC",
      "dynamic_threshold": 0.3
    }
  }
}
```

SDK 中 `mode` 为 `DynamicRetrievalConfigMode`。

**要点：** 动态检索即按需搜索。模型对简单问题**过度检索依据**时，提高 `dynamic_threshold`；对需要最新信息的事实查询跳过搜索时，降低该值。

---

## 10. `parallel_ai_search` — `ToolParallelAiSearch`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4588)

```json
{
  "parallel_ai_search": {
    "api_key": "optional-parallel-ai-key",
    "custom_configs": {
      "source_policy": {
        "include_domains": ["google.com", "wikipedia.org"],
        "exclude_domains": ["example.com"]
      },
      "fetch_policy": {
        "max_age_seconds": 3600
      }
    }
  }
}
```

SDK 文档字符串注明：**Gemini API 不支持**。

**要点：** 需要 **Parallel.ai** 凭证并在 Vertex 启用。应将其作为可选企业集成，而非 `google_search` 的默认替代。`fetch_policy.max_age_seconds` 在信息新鲜度和缓存命中率间取舍。

---

## 11. `computer_use` — `ComputerUse`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L3173)

`environment` 使用 `Environment`，例如 `ENVIRONMENT_BROWSER`。

**要点：** 启用 `computer_use` 还会为界面操作**注入预定义函数声明**。客户端必须实现实际自动化循环：截图 → 模型 → 操作。`excluded_predefined_functions` 可从已声明能力中移除支付等高风险操作。

```json
{
  "computer_use": {
    "environment": "ENVIRONMENT_BROWSER",
    "excluded_predefined_functions": ["some_predefined_action"]
  }
}
```

---

## 12. `mcp_servers` — `McpServer` + `StreamableHttpTransport`

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4692) (`McpServer`) · [源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4639) (`StreamableHttpTransport`)

SDK 文档字符串注明：**Vertex AI 不支持**。

**要点：** Gemini API 上的 MCP 使用**可流式 HTTP** 传输，服务端必须可靠实现 MCP 协议；超时过短会表现为模型工具调用停滞。上述 SDK 类型中 Vertex AI 不支持该键，因此同时面向 Gemini API 和 Vertex 时，必须**分支构造 `Tool` 载荷**。

```json
{
  "mcp_servers": [
    {
      "name": "my-mcp-server",
      "streamable_http_transport": {
        "url": "https://api.example.com/mcp",
        "headers": {
          "Authorization": "Bearer token"
        },
        "timeout": "30s",
        "sse_read_timeout": "60s",
        "terminate_on_close": true
      }
    }
  ]
}
```

---

<a id="appendix-a-tooltype-server-side-tool-call-discrimination"></a>
## 附录 A：`ToolType`（区分服务端工具调用）

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L806-L820)

枚举 **`ToolType`** 映射服务端工具种类，例如：

- `GOOGLE_SEARCH_WEB` / `GOOGLE_SEARCH_IMAGE` → `Tool.google_search`
- `URL_CONTEXT` → `Tool.url_context`
- `GOOGLE_MAPS` → `Tool.google_maps`
- `FILE_SEARCH` → `Tool.file_search`

用于 **`ToolCall`** / **`ToolResponse`**，不用于请求 `Tool` 定义自身。

**要点：** 调试调用错误工具时，应比较**请求** `Tool` 键与**响应** `ToolType`。服务端执行的工具表现为专用枚举值，而非自定义 `function_declarations` 名称。

---

<a id="appendix-b-toolconfig-shared-across-tools-in-the-request"></a>
## 附录 B：`ToolConfig`（请求内工具共享）

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4939-L4970)

下方**[工具选择配置](#tool-choice-configuration-toolconfig--function_calling_config)**一节链接官方文档，并展开 **`function_calling_config`** 的模式和白名单。本附录集中展示完整 **`ToolConfig`** 结构。

来自 `ToolConfig` / `ToolConfigDict`：

```json
{
  "function_calling_config": {
    "mode": "AUTO",
    "allowed_function_names": ["get_weather"],
    "stream_function_call_arguments": false
  },
  "retrieval_config": {
    "lat_lng": { "latitude": 37.7749, "longitude": -122.4194 },
    "language_code": "en-US"
  },
  "include_server_side_tool_invocations": true
}
```

`mode` 为 `FunctionCallingConfigMode`。SDK 文档字符串注明部分嵌套字段仅支持 Vertex。

**要点：** `function_calling_config` 适用于请求中**全部**工具。`allowed_function_names` 是演示和生产金丝雀的低成本安全约束。`include_server_side_tool_invocations` 可在响应 `Content` 中**记录** Google 托管工具步骤，用于审计。

---

<a id="tool-choice-configuration-toolconfig--function_calling_config"></a>
## 工具选择配置（`ToolConfig` / `function_calling_config`）

Gemini API 中，函数式工具的**选择策略**位于 **`tool_config`**（REST）/ **`ToolConfig`**（SDK）下，尤其是 **`function_calling_config`**。它与 `tools` 列表互补：`tools` 描述声明；`function_calling_config.mode` 及相关字段决定模型是否可省略调用、必须调用某个工具，或遵循该请求的其他调用规则。

**官方文档**

- [函数调用](https://ai.google.dev/gemini-api/docs/function-calling)：概述；**函数调用模式**锚点为 [function_calling_mode](https://ai.google.dev/gemini-api/docs/function-calling#function_calling_mode)。
- [生成内容（REST）/ `toolConfig`](https://ai.google.dev/api/generate-content)：请求字段 `toolConfig`，另见该页面链接的 **`ToolConfig`** schema。

**Python SDK（永久链接）**

- **`FunctionCallingConfigMode`** 枚举（`AUTO`、`ANY`、`NONE`、`VALIDATED` 等）：[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L302-L314)
- **`FunctionCallingConfig`** / **`FunctionCallingConfigDict`**：[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4905-L4932)
- **`ToolConfig`** / **`ToolConfigDict`**，包含 `function_calling_config`、`retrieval_config`、`include_server_side_tool_invocations`：[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4939-L4970)

**要点：** 模式是**请求全局设置**。若每个工具需要不同行为，应拆分为独立 `generate_content` 调用，或收窄 `allowed_function_names`。托管工具，如 `google_search`、`url_context`，仍在响应中体现为工具调用，应将 `include_server_side_tool_invocations` 与可观测方案配套使用。

---

<a id="summary"></a>
## 汇总

[源码](https://github.com/googleapis/python-genai/blob/b2629a44d389370af16e9ad68af676bb565eb9b9/google/genai/types.py#L4725-L4821)

**要点：** 希望缓存或计费语义不同时，优先使用**独立 `Tool` 列表条目**，例如一个工具字典对应 `google_search`，另一个对应 `function_declarations`，避免难以针对各接口分析的巨型字典。

- **一个 `Tool` 对象**包含许多可选键，只组合所用 API 接口支持的能力。
- **用户定义工具** → `function_declarations`，使用 `FunctionDeclaration` + `Schema` 或 `parameters_json_schema`。
- **内置工具** → 上述 `google_search`、`google_maps`、`url_context`、`file_search`、`code_execution` 等。
- **唯一事实来源：** [googleapis/python-genai](https://github.com/googleapis/python-genai) 中的 `google/genai/types.py`，永久链接见上。行号随版本变化，升级后需重新检查已安装包或更新链接中的提交哈希。

---

<a id="see-also-vendor-docs"></a>
## 另请参阅（提供商文档）

Gemini API 与 Vertex AI 对工具和字段的支持不同；价格与模型支持也会变化，请通过下列链接确认。

- [使用 Google 搜索提供依据](https://ai.google.dev/gemini-api/docs/google-search)：`google_search` 工具、引用和 `groundingMetadata`。
- [URL 上下文](https://ai.google.dev/gemini-api/docs/url-context)：`url_context` 工具、已获取 URL 和 `url_context_metadata`。
- [文件搜索（Gemini API）](https://ai.google.dev/gemini-api/docs/file-search)：托管 RAG 和文件搜索存储，另见[介绍文章](https://blog.google/technology/developers/file-search-gemini-api)。
- [依据支持 API（Vertex AI）](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/grounding)：Vertex 依据支持和企业搜索接口。
- [通过 Google 搜索提供依据（Vertex）](https://cloud.google.com/vertex-ai/generative-ai/docs/grounding-with-search)：Vertex 的搜索和地图式依据支持。
- [函数调用](https://ai.google.dev/gemini-api/docs/function-calling)：`toolConfig` 和调用模式（`#function_calling_mode`）。
