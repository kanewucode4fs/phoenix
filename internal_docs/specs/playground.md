<a id="playground"></a>
# Playground 交互试验场

作者：@mikeldking

作为 Phoenix 用户，我不希望每次迭代提示词都回到 IDE，也不想操心编程语言或依赖。我希望能直接使用 Phoenix 中存储的数据（span、数据集），通过提示词及其模板运行这些数据。

<a id="terminology"></a>
## 术语

- **operation（操作）**：指 LLM 的调用方式（chat、text_completion）。我们将优先支持 chat (https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/)。
- Playground 输入来源：指模板输入是“手动输入”（用户可修改）还是“数据集”。

<a id="use-cases"></a>
## 使用场景

用户可能希望通过 Playground：

- 测试提示词模板。
- LLM 重放：在 LLM span 上重放模板或提示词改动，实时调试改进效果。
- 在数据集上运行模板改动（遍历一组输入），例如提示词改动实验。
- 对模型和模板进行 A/B 测试。
- 创建评估模板：在选定的单条生产 span 或数据集上运行评估模板，测试评估并将其保存为实验。
- 生成合成数据：生成合成数据，为数据集已有数据行添加列，帮助创建测试数据。

<a id="prompt-template"></a>
### 提示词模板

作为 AI 工程师，我可能希望使用提示词 Playground，探索不同场景下的生成效果、费用和延迟等。这要求它比提供商自带的 Playground 更灵活，因为它需要统一不同提供商的 API。

作为用户，我希望运行模板并随着 token 到达查看结果，也希望这些数据以 span 形式记录，以便用于数据集和标注，例如保存满意的结果。

<a id="llm-replay"></a>
### LLM 重放

作为已经使用 Phoenix 追踪的 AI 工程师，我希望能取出一个 LLM span 重放生成过程，查看调整后的响应是否改变输出。这意味着必须能够将生成所需的全部字段从语义属性值转换到 Playground。

- LLM 提供商
- LLM 名称
- 操作类型（chat、text_completion）
- 调用参数
- 消息和角色
- 工具
- 输出 schema

需要将上述值从 span 转换为 Playground 中对应的值，以便调用。

以下是典型聊天 LLM span 的属性载荷：

```typescript
{

  llm: {
    output_messages: [
      {
        message: {
          content: "This is an AI Answer",
          role: "assistant",
        },
      },
    ],
    model_name: "gpt-3.5-turbo",
    token_count: { completion: 9.0, prompt: 1881.0, total: 1890.0 },
    input_messages: [
      {
        message: {
          content: "You are a chatbot",
          role: "system",
        },
      },
      {
        message: {
          content: "Answer me the following question. Are you sentient?",
          role: "user",
        },
      },
    ],
    invocation_parameters:
      '{"context_window": 16384, "num_output": -1, "is_chat_model": true, "is_function_calling_model": true, "model_name": "gpt-3.5-turbo"}',
  },
  openinference: { span: { kind: "LLM" } },
};
```

聊天调用将使用以下映射：

- llm.input_messages -> invocation.messages
- llm.invocation_parameters -> invocation.parameters
- llm.model_name -> invocation.model（例如 vendor + model_name）
- llm.tools -> invocation.tools
- llm.tool_selection（缺失）-> playground.tool_selection（默认为 auto）
- （待定）-> invocation.output_schema（JSON 模式的输出 schema）

<a id="ab-testing"></a>
### A/B 测试

作为 AI 工程师，我希望能创建多个 Playground，以回答以下问题：

- 提示词 A 能否产生更好的回复？
- 模型 X 能否产生更好的回复？

有时我希望 A/B 两侧的内容同步，有时则不需要。因此，界面应允许用户：

- 同步模型：用户正在调整模板或调用参数。
- 同步模板：用户正在调整模型。
- 同步输入：用户正在测试不同输入。

<a id="evaluation-template"></a>
### 评估模板

作为 AI 工程师，我希望能针对先前记录的生成结果（例如 LLM span）提问。

<a id="technical-features"></a>
## 技术功能

Playground 需要以下技术功能：

**前端**

- 在本地存储中保存凭证。
- 将 span 属性转换为 Playground 状态。

**后端**

- LLM 调用接口（GraphQL 或其他）。
- 生成期间记录 span。
- Playground 会话追踪。
- Playground 数据集调用追踪。
- 流式传输生成结果。

<a id="tracing-needs"></a>
## 追踪需求

为使 span 到 Playground 调用的转换无缝衔接，必须记录全部必要调用参数，包括：

- LLM/genai 系统，例如 openai、anthropic 等。
- 输出 schema：LLM 可以遵循 OpenAPI schema。
