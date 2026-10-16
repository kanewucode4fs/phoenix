---
name: playground
description: 在 Phoenix 提示词 Playground 中编写、编辑或迭代提示词，包括对数据集运行实验。在调用任何 Playground `ui.*` 操作前加载，包括单次提示词改写。
summary: 在 Phoenix Playground 中编写、编辑、运行、比较和改进提示词。
---

<a id="prompt-playground"></a>

# 提示词 Playground

提示词 Playground 用于编写和优化提示词，支持两种工作方式：不使用数据集的快速手动迭代，以及结合评估器和实验的数据集提示词实验。应根据用户当前目标和已挂载的界面上下文选择工作流。

以下 Playground 动作都是 `ui.*` 操作，在 `execute_browser_action` 脚本中通过 `await ui.<operation>(input)` 调用，例如 `await ui.playground.run({})`。首次使用前，通过 `search_browser_actions` 确认准确输入结构；优先用一个小脚本串联相关步骤，避免拆成多个单次调用脚本。

<a id="workflow-create-and-iterate-without-a-dataset"></a>

## 工作流：不使用数据集的创建与迭代

用户希望起草、改写或手动改进提示词，且不涉及数据集评估循环时，使用此工作流。

1. 明确提示词要执行的任务：输入变量、预期输出结构、受众、约束，以及已有的正确或错误行为示例。
2. 如果已有 Playground 提示词，提出修改前先调用 `ui.playground.prompt.read`，获取当前消息、消息 ID、标签和修订版本。
3. 起草或修改提示词，清楚说明任务、所需上下文、输出契约和成功标准，始终直接围绕用户既定目标。
4. 修改已挂载提示词时使用 `ui.playground.prompt.edit`，让用户接受前能够查看差异。
5. 用户希望新增一个从默认提示词消息开始的比较实例时，使用 `ui.playground.instance.add`；比较方案需要保留现有提示词作为起点时，使用 `ui.playground.instance.clone`。讨论方案时使用字母标签，调用操作时传数字实例 ID。添加后，使用返回的 `addedInstance` 快照继续编辑。
6. 用户提供提示词模板变量的手动值时，使用 `ui.playground.variables.set`。
7. 用户关心偶发失败、结构化输出一致性、工具调用可靠性，或提示词是否可以保存时，运行前先使用 `ui.playground.repetitions.set`。LLM 输出不确定，应通过多次运行同一任务建立信心，而非只信任一次成功响应。
8. 只有用户要求运行、尝试、测试或比较当前提示词时，才调用 `ui.playground.run`。应将输出视为定性反馈，而非基于数据集的证据。一个脚本可以按顺序运行并读取：
   `const run = await ui.playground.run({}); if (!run.ok) return run; return await ui.playground.run.readOutput({});`
9. 运行结束后调用 `ui.playground.run.readOutput`，检查原始输出，并在需要追踪分析时获取 traceId。执行多次重复时，必须查看每次结果，再总结可信度或建议保存。
10. 只有用户明确要求保存，或确认应持久化当前提示词时，才调用 `ui.playground.prompt.save`。未保存提示词首次保存时，除非用户提供名称，否则省略 `name`，操作会根据内容生成有效 Phoenix 提示词名称。始终提供保存说明，风格应像清晰简短的 git 提交消息。将标签视为发布，用户未要求时不要提升标签。
11. 与用户共同检查输出，确定下一项具体改进，重复编辑或比较循环，直到提示词能够有效完成任务。

<a id="workflow-iterate-over-a-dataset-with-evaluators-and-experiments"></a>

## 工作流：结合评估器和实验迭代数据集

用户希望获得提示词在整个数据集上改进的证据，或使用评估器结果比较提示词方案时，使用此工作流。对数据集运行提示词本身就是实验：设计运行前就应参考 `experiments` 技能，不能只在结果返回后参考；它负责完整迭代方法，包括创建时写入什么、如何读取和比较结果、何时需要评估器。`evaluators` 技能负责设计评分评估器。此工作流只涵盖配置并启动记录运行的 Playground 操作机制。

1. 尚未加载数据集时，使用 `ui.playground.dataset.load`。用户指定了数据集但未指定划分，而数据集存在划分时，列出划分并询问使用其中一个还是整个数据集，之后只加载一次。
2. 运行前确保起始提示词完善，明确任务、相关变量、输出格式和一致评估所需约束。
3. 用户希望将下次数据集 Playground 运行记录、持久化或保存为实验，或希望为下次实验命名、描述、附加假设或改动变量等元数据时，运行前使用 `ui.playground.experiment.setRecording`。只有用户明确要求临时、一次性、不记录或短暂运行时，才将 `recordExperiments` 设为 false。仅当请求的记录模式或基本信息字段与公布的 `recordExperiments`、`nextExperimentScaffold` 不同时才调用。暂存的基本信息仅用于下一次运行，开始后即被消耗。此操作不同于 `ui.playground.prompt.save`，后者保存提示词版本，不保存运行结果。
4. 用户需要多次尝试来建立信心时，尤其涉及偶发失败、结构化输出或工具调用正确性时，运行前使用 `ui.playground.repetitions.set`。
5. 在数据集上运行 Playground。启用记录时，每个提示词实例在数据集上的运行都会被保存为实验，输出和评估器标注可供审查。
6. 读取实验结果并判断改动是否有效时，遵循 `experiments` 技能；创建下一个候选方案时，使用 `ui.playground.prompt.edit`、`ui.playground.instance.add` 或 `ui.playground.instance.clone`（`ui.playground.instance.add` 从默认提示词消息开始，`ui.playground.instance.clone` 从现有内容开始），然后重新运行。
7. 只有证据表明确有改进，或用户明确接受取舍后，才使用 `ui.playground.prompt.save` 保存为新版本。对未保存提示词，除非用户关心准确名称，否则操作可以直接创建 Phoenix 提示词，无需询问名称。

<a id="reading-experiment-results"></a>

### 读取实验结果

实例带有 `experimentId` 时，使用 `phoenix-gql` 读取费用和评估器分数：

```
phoenix-gql --vars '{"experimentId":"<id>"}' 'query($experimentId: ID!){ node(id:$experimentId){ ...on Experiment { runCount expectedRunCount job{status} costSummary{total{cost tokens}} annotationSummaries{annotationName meanScore count errorCount} } } }'
```

`experimentId` 只表示实验可以查询，不表示运行已结束。只有 `job.status` 为 `COMPLETED`，或 `runCount == expectedRunCount` 时，才能将汇总视为最终结果。比较重新运行的结果时，重新查询对话中的先前实验 ID，比较汇总差异。未记录运行的实验是临时实验，服务会在最后更新约 24 小时后清理；新出现的 `experimentId` 在此窗口内，但长会话中很早以前的 ID 重新查询时可能已无法解析。

<a id="workflow-author-refine-or-remove-a-function-tool"></a>

## 工作流：编写、改进或删除函数工具

用户希望模型能够从提示词调用函数或工具、改进现有签名，或删除工具时，使用此工作流。函数工具是存储在 Playground 提示词实例上的 JSON Schema 函数定义，与消息和模型配置并列，是模型运行中可“调用”的对象。

1. 开始任何操作前先调用 `ui.playground.prompt.tools.read`。结果提供当前工具列表、各工具 ID 和类型，以及 `revision` 令牌。依据现有 ID 和名称判断应更新、创建还是删除工具。
2. 用户以自然语言描述函数时，为其提出具体 JSON Schema。除非用户另有指定，参数名称默认使用小写 snake_case，结构采用 `{"type":"object","properties":{...},"required":[...]}`。
3. 使用最新 `revision` 调用 `ui.playground.prompt.tools.write`，将全部改动放在一次调用中。`tools` 是创建或更新数组：创建时省略 `id`，修改时传入已有 `id`，只修改提供的字段；`deleteToolIds` 是待删除 ID 列表。删除可以针对 `raw` 供应商工具，写入则不能。批次全部成功或全部失败：任何改动无效，例如缺失 ID、写入 `raw` 工具、同一 ID 同时创建或更新并删除，都不会应用任何内容，错误会说明原因。允许删除被强制选择的工具；工具选择会重置为 auto 并在结果中报告，应向用户说明。
4. 写入后，用简明英语概述改动，说明哪些工具被创建或更新，使用户知道在工具编辑器中查看什么。创建工具时，还应告知新 ID。
5. 用户希望在运行中使用新工具时，调用 `ui.playground.run`，再调用 `ui.playground.run.readOutput`，确认模型是否实际调用。

<a id="few-shot-examples"></a>

### 少样本示例

以下是 `ui.playground.prompt.tools.write` 的具体可运行输入结构，应作为模板，而非固定提示词。始终传入 `ui.playground.prompt.tools.read` 返回的最新 `revision`；最清晰的方式是在同一个 `execute_browser_action` 脚本中先读再写：

```js
const snapshot = await ui.playground.prompt.tools.read({ instanceId: 1 });
if (!snapshot.ok) return snapshot;
return await ui.playground.prompt.tools.write({
  instanceId: 1,
  expectedRevision: snapshot.output.revision,
  tools: [/* creates and updates, as in the examples below */],
});
```

**创建全新工具。** 使用不带 `id` 的一个条目。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "tools": [
    {
      "name": "get_weather",
      "description": "Look up the current weather for a city.",
      "parameters": {
        "type": "object",
        "properties": {
          "city": { "type": "string", "description": "City name, e.g. \"San Francisco\"." },
          "units": { "type": "string", "enum": ["c", "f"], "description": "Temperature units." }
        },
        "required": ["city"]
      }
    }
  ]
}
```

**一次创建多个工具。** 将所有工具放进 `tools` 数组，一次调用、一次修订检查，优于每个工具单独调用。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "tools": [
    {
      "name": "get_weather",
      "parameters": {
        "type": "object",
        "properties": { "city": { "type": "string" } },
        "required": ["city"]
      }
    },
    {
      "name": "get_forecast",
      "parameters": {
        "type": "object",
        "properties": {
          "city": { "type": "string" },
          "days": { "type": "integer" }
        },
        "required": ["city", "days"]
      }
    }
  ]
}
```

**为现有工具添加必填参数。** 传入已有 `id` 和完整的新 `parameters` 模式。采用局部修改语义，即使未改变也必须提供 `name`。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "tools": [
    {
      "id": 3,
      "name": "get_weather",
      "parameters": {
        "type": "object",
        "properties": {
          "city": { "type": "string" },
          "units": { "type": "string", "enum": ["c", "f"] }
        },
        "required": ["city", "units"]
      }
    }
  ]
}
```

**同一批次中创建一个工具并修改另一个。** 混合提供和不提供 `id` 的条目。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "tools": [
    {
      "name": "get_time",
      "parameters": {
        "type": "object",
        "properties": { "timezone": { "type": "string" } },
        "required": ["timezone"]
      }
    },
    {
      "id": 3,
      "name": "get_weather",
      "description": "Look up the current weather for a city. Returns temperature, humidity, and conditions."
    }
  ]
}
```

**通过分类选项定义返回结构化输出的工具。** 强制模型选择某个枚举标签，并可选提供解释。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "tools": [
    {
      "name": "classify_sentiment",
      "description": "Classify the sentiment of the input as positive, negative, or neutral.",
      "parameters": {
        "type": "object",
        "properties": {
          "label": {
            "type": "string",
            "enum": ["positive", "negative", "neutral"],
            "description": "The sentiment classification."
          },
          "explanation": {
            "type": "string",
            "description": "Short justification for the label."
          }
        },
        "required": ["label"]
      }
    }
  ]
}
```

**删除工具，也可在同一批次替换为新工具。** `deleteToolIds` 按 ID 删除，与 `tools` 组合可原子地删除和添加。删除可针对 `raw` 供应商工具。

```json
{
  "instanceId": 1,
  "expectedRevision": "prompt-tools-abc",
  "deleteToolIds": [3],
  "tools": [
    {
      "name": "get_forecast",
      "parameters": {
        "type": "object",
        "properties": { "city": { "type": "string" } },
        "required": ["city"]
      }
    }
  ]
}
```

<a id="things-to-avoid"></a>

### 应避免的做法

- 本轮未先调用 `ui.playground.prompt.tools.read` 就调用 `ui.playground.prompt.tools.write`，会因 `expectedRevision` 过期而被拒绝。同一个 `execute_browser_action` 脚本中先读再写，可保持修订版本最新。
- 尝试写入读取快照中 `kind` 为 `raw` 的工具。供应商透传工具，如内置 `web_search`，不能通过 PXI 编辑，应告知用户在 Playground 工具编辑器中编写。`tools` 中包含 `raw` 条目会使整批被拒绝，但可以通过 `deleteToolIds` 删除 `raw` 工具。
- 删除提示词强制选择的工具（tool_choice = specific function）是允许的，工具选择会自动重置为 auto（零次或多次），结果报告 `resetToolChoiceFrom`。必须告知用户，因为这会改变模型运行时的工具选择方式。
- 虚构工具 `id`。条目中的 `id` 及所有 `deleteToolIds` ID 必须来自读取快照，创建时则省略。不能引用同一批次中较早创建的 ID。
- 不重新读取修订版本就连续多次调用 `ui.playground.prompt.tools.write`。每次成功写入或删除都会改变修订版本，应将改动合并到一次调用。
