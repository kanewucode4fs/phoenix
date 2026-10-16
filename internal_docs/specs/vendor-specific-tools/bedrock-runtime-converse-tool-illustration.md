<a id="amazon-bedrock-runtime--converse-tool-configuration-types-aiobotocore-bedrock-runtime"></a>
# Amazon Bedrock Runtime：`Converse` 工具配置（`types-aiobotocore-bedrock-runtime`）

用于 **`converse`** / **`converse_stream`** 的 **`toolConfig`** JSON 示例，依据 **`types_aiobotocore_bedrock_runtime`** 中的 TypedDef。字段名与 [Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html) 一致：JSON 使用 **PascalCase** 键；boto3 / aiobotocore 接受 Python `dict` 形式的同名键。

**阅读顺序：** **`toolConfig.tools`** 列出模型可调用的内容，每个条目为 **`toolSpec`**、**`systemTool`** 或 **`cachePoint`**。**`toolConfig.toolChoice`** 控制模型**是否**必须调用工具，[下文详细说明](#tool-choice-configuration-toolchoice)。附录 A 概述请求/响应循环中的 **`toolUse`** / **`toolResult`** 消息块。

**来源（已验证）：** **types-aiobotocore-bedrock-runtime 3.1.1** 包中的 **`types_aiobotocore_bedrock_runtime/type_defs.pyi`**。行号范围为近似值，升级后请在环境中打开文件确认。主要类型：`ToolConfigurationTypeDef`、`ToolTypeDef`、`ToolSpecificationTypeDef`、`ToolInputSchemaTypeDef`、`SystemToolTypeDef`、`ToolChoiceTypeDef`、`SpecificToolChoiceTypeDef`、`ConverseRequestTypeDef`。

**客户端：** `types_aiobotocore_bedrock_runtime.client.BedrockRuntimeClient` — `async def converse(self, **kwargs: Unpack[ConverseRequestTypeDef])`。

---

## `toolConfig` — `ToolConfigurationTypeDef`

```json
{
  "toolConfig": {
    "tools": [],
    "toolChoice": {}
  }
}
```

- **`tools`**：实际使用工具时必需，是 **`ToolTypeDef`** 序列，见下文。
- **`toolChoice`**：可选，类型为 **`ToolChoiceTypeDef`**。

**要点：** `toolConfig` 属于**每次 `converse` 请求**，没有服务端注册表。应在整个会话中保持工具定义稳定，否则可能缓存未命中，或 `toolUseId` 路由不一致。

---

<a id="tools--tooltypedef-one-variant-per-element"></a>
## `tools[]` — `ToolTypeDef`（每个元素一种变体）

按 API 契约，每个工具条目是一个对象，以下分支**最多包含一个**，尽管类型桩将全部分支标记为 `NotRequired`：

| 分支 | 类型桩类型 | 作用 |
|--------|-------------|------|
| `toolSpec` | `ToolSpecificationTypeDef` | 用户定义函数或 JSON-schema 工具 |
| `systemTool` | `SystemToolTypeDef` | 内置**系统**工具，类型桩中只有名称 |
| `cachePoint` | `CachePointBlockTypeDef` | 提示词缓存检查点 |

**要点：** 每个列表元素在语义上只应有一个活跃分支。发送冲突键可能被拒绝，或因序列化器而产生未定义行为。应按 AWS 提示词缓存文档建议的位置安排工具和**缓存点**，最大化复用。

### 1. `toolSpec` — `ToolSpecificationTypeDef`

- **`name`**：必填，工具名称。
- **`inputSchema`**：必填，类型为 **`ToolInputSchemaTypeDef`**。JSON Schema 位于 **`json`** 下，类型桩中可选，但真实调用必需。
- **`description`**：可选。

**要点：** 工具名必须匹配 **`[a-zA-Z0-9_-]+`**，并满足 AWS API 长度限制，避免点号和空格。模型支持 **`strict`** 时，应将其视为处理器执行副作用之前对 `input` 的 JSON Schema 强制约束。

```json
{
  "toolSpec": {
    "name": "get_weather",
    "description": "Get the current weather for a location.",
    "inputSchema": {
      "json": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "City name"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"]
          }
        },
        "required": ["city"]
      }
    }
  }
}
```

### 2. `systemTool` — `SystemToolTypeDef`

类型桩仅包含：

```python
class SystemToolTypeDef(TypedDict):
    name: str
```

结构示例：

```json
{
  "systemTool": {
    "name": "system_tool_name_per_bedrock_docs"
  }
}
```

这些类型桩**未**枚举允许的 **`name`** 值。有关系统工具（如网页搜索、依据校验）和模型支持情况，请查阅当前 [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Tool.html) 和模型文档。

**要点：** 系统工具**因模型而异**。Claude 3.5 可用的名称，在 Nova 或 Titan 中可能不存在。应按 **`modelId`** 配置 `systemTool` 白名单，而非将其视为应用全局常量。

### 3. `cachePoint` — `CachePointBlockTypeDef`

```json
{
  "cachePoint": {
    "type": "default"
  }
}
```

类型桩约 320–325 行中，`type` 为 `Literal["default"]`。

**要点：** 缓存点将提示词划分出**可复用前缀**。将其放在大型静态系统提示词和工具 JSON 之后；移动位置会改变缓存命中率和计费。

---

## `toolChoice` — `ToolChoiceTypeDef`

通常只设置以下一个键；类型桩将 `auto`、`any`、`tool` 都设为可选：

### `auto`

```json
{
  "toolChoice": {
    "auto": {}
  }
}
```

类型桩中 `auto` 为 `Mapping[str, Any]`，通常使用空对象。

**要点：** `auto` 允许模型在不需要时**跳过**工具。希望**强制**某种工具交互时，使用 `any`，但仍受模型能力限制。

### `any`

```json
{
  "toolChoice": {
    "any": {}
  }
}
```

**要点：** `any` 表示调用**某个**工具，而非调用**全部**工具。应结合 schema 设计，使至少一个工具能在没有有害副作用的情况下满足用户查询。

<a id="tool--force-a-specific-tool"></a>
### `tool`：强制指定工具

使用 **`SpecificToolChoiceTypeDef`**，其中 `name` 必须匹配已声明工具名。

**要点：** 此处 `name` 必须与 **`toolSpec.name`** 或系统工具名完全一致，拼写错误会在运行时产生难调试的 400。生产环境优先采用 `auto`，除非在测试中固定行为。

```json
{
  "toolChoice": {
    "tool": {
      "name": "get_weather"
    }
  }
}
```

---

<a id="full-minimal-converse-excerpt"></a>
## 完整的最小 `converse` 片段

```json
{
  "modelId": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "What is the weather in Seattle?"
        }
      ]
    }
  ],
  "toolConfig": {
    "tools": [
      {
        "toolSpec": {
          "name": "get_weather",
          "description": "Get weather by city.",
          "inputSchema": {
            "json": {
              "type": "object",
              "properties": {
                "city": { "type": "string" }
              },
              "required": ["city"]
            }
          }
        }
      }
    ],
    "toolChoice": {
      "auto": {}
    }
  }
}
```

**要点：** 这是最小有效结构。真实应用通常添加 **`system`**、**`inferenceConfig`** 和**防护策略**。应将 `toolConfig` 与测试过的相同 `modelId` 配套使用，因为工具 schema 并非在所有 Bedrock 模型间通用。

---

<a id="appendix-a-tooluse--toolresult-message-content-related-types"></a>
## 附录 A：`ToolUse` / `ToolResult` 消息内容（相关类型）

模型返回工具调用或应用回传结果时，**`Message`** / **`ContentBlock`** 使用独立 TypedDef，仍位于同一 `type_defs.pyi`：

**`ToolUseBlockTypeDef`**，约 625–633 行：`toolUseId`、`name`、`input`，以及可选 `type`（`ToolUseTypeType`：`"tool_use"` | `"server_tool_use"`）。

**`ToolResultBlockTypeDef`**，约 1250–1257 行：`toolUseId`、`content`（文本、JSON、图像等块的序列），以及可选 `status`（`ToolResultStatusType`：`"success"` | `"error"`）。

**要点：** **`tool_use`** 是常规路径，由**应用**执行具名工具，再返回 **`toolUseId`** 与调用一致的 **`toolResult`**。**`server_tool_use`** 表示**模型或服务端**工具路径，是否仍须发送 `toolResult` 取决于**模型**和工具，请查阅对应 `modelId` 的 AWS 工具使用文档。每个本地执行的 `tool_use` 都必须原样回传 **`toolUseId`**，否则模型无法将结果关联到调用。

助手消息示例：

```json
{
  "role": "assistant",
  "content": [
    {
      "toolUse": {
        "toolUseId": "tooluse_01ABC...",
        "name": "get_weather",
        "input": { "city": "Seattle" },
        "type": "tool_use"
      }
    }
  ]
}
```

含结果的用户消息示例：

```json
{
  "role": "user",
  "content": [
    {
      "toolResult": {
        "toolUseId": "tooluse_01ABC...",
        "content": [
          {
            "text": "{\"temp_f\": 52, \"condition\": \"cloudy\"}"
          }
        ],
        "status": "success"
      }
    }
  ]
}
```

---

<a id="appendix-b-toolusetypetype--toolresultstatustype"></a>
## 附录 B：`ToolUseTypeType` / `ToolResultStatusType`

来自 `literals.pyi`：

- **`ToolUseTypeType`**：`"server_tool_use"` | `"tool_use"`
- **`ToolResultStatusType`**：`"error"` | `"success"`

**要点：** 处理器抛出异常时映射为 `status: "error"`。与包含堆栈追踪却伪装成功的载荷相比，Claude 模型更能安全处理错误字符串。

---

<a id="tool-choice-configuration-toolchoice"></a>
## 工具选择配置（`toolChoice`）

本节将 AWS API 参考与**[前文](#toolchoice--toolchoicetypedef)**的 JSON 结构对应，包括 `auto`、`any`、`tool`。在 **`converse`** / **`converse_stream`** 中，**`toolConfig.toolChoice`** 决定模型是否可跳过工具、必须至少调用一个工具，或必须按名称调用**指定**工具。它与 **`toolConfig.tools`** 互补，分别表示选择策略和定义。

**官方文档（API 参考）**

- [`ToolChoice`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolChoice.html)：`auto`、`any` 和 `tool` 的联合，只设置一个成员。行为为：`auto` 由模型决定，默认采用；`any` 要求至少一次工具调用；`tool` 强制具名工具，该页面注明支持 Claude 3 和 Amazon Nova。
- [`ToolConfiguration`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolConfiguration.html)：`tools` 和 `toolChoice` 的父结构。
- [`Converse`](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)：包含 `toolConfig` 的顶层请求结构。

**用户指南**

- [使用 Converse API 调用工具](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use-inference-call.html)：端到端工具使用，从 `ToolChoice` API 页面链接。

**本文类型桩中的类型**

- **`ToolChoiceTypeDef`** / **`SpecificToolChoiceTypeDef`**：见本文前面的 **`toolChoice` — `ToolChoiceTypeDef`** 一节，基于 `types-aiobotocore-bedrock-runtime` **3.1.1** 快照。

**要点：** Bedrock 上强制 `tool` **受模型限制**。API 参考若注明仅某些模型家族支持 `tool`，不要依赖其他 `modelId` 支持。`any` 在发出工具调用前不生成助手文本，应据此设计交互体验。

---

<a id="summary"></a>
## 汇总

**要点：** types-aiobotocore 落后于 AWS 时，以 **API 参考**为准。通过控制台或 CLI 生成最小 `converse` 调用，比较 JSON，再更新类型桩。

| 概念 | 类型桩名称 | 关键 JSON 字段 |
|---------|-----------|-----------------|
| 整体配置 | `ToolConfigurationTypeDef` | `tools`、`toolChoice?` |
| 单个工具条目 | `ToolTypeDef` | `toolSpec` \| `systemTool` \| `cachePoint` |
| 自定义工具 | `ToolSpecificationTypeDef` | `name`、`inputSchema.json`（JSON Schema）、`description?` |
| 内置工具 | `SystemToolTypeDef` | `name` |
| 缓存标记 | `CachePointBlockTypeDef` | `type: "default"` |
| 选择 | `ToolChoiceTypeDef` | `auto` \| `any` \| `tool: { name }` |

类型桩遵循 **types-aiobotocore-bedrock-runtime 3.1.1** 捆绑的 **Bedrock Runtime** 服务模型版本。AWS 可能继续添加字段或工具名，请对照官方 **Converse** API 参考和所用 botocore/aiobotocore 版本。

---

<a id="see-also-vendor-docs"></a>
## 另请参阅（提供商文档）

模型 ID、区域和预览/Beta 标志会随时间变化，请通过下列链接确认。

- [推理调用中的工具使用](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use-inference-call.html)：`Converse` / `ConverseStream` 工具模式。
- [Converse API 参考](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)：`toolConfig`、消息和响应结构。
- [Tool（API 类型）](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Tool.html)：`toolSpec`、`systemTool`、`cachePoint`。
- [ToolSpecification](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolSpecification.html)：`name`、`inputSchema` 和可选 `strict`。
- [支持的模型和功能](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html)：逐模型的工具使用和流式支持。
- [计算机操作](https://docs.aws.amazon.com/bedrock/latest/userguide/computer-use.html)：Claude 计算机、编辑器和 Bash 工具、Beta 请求头和 `additionalModelRequestFields`。
- [`ToolChoice`（API）](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolChoice.html)：`converse` 的 `auto` / `any` / `tool`。
