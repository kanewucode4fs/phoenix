---
"@arizeai/phoenix-evals": minor
---

分类评估器（包括所有内置评估器）现在可以在 `openai.decisionModel("gpt-6-luna")` 等 AI SDK 决策模型上运行。标签来自 `experimental_decide`，标签概率（以及提供商返回时的置信度）存放在 `metadata` 中。渲染后的提示词以纯文本发送，拒绝响应会抛出 AI SDK 的 `Experimental_DecisionRefusalError`。Decide Span 现在记录决策状态、问题和答案。新增导出：`isDecisionModel` 和 `DecisionModel` 类型。

此变更替代上一版本的评估模型支持，并改变了发送给 TypeSafe 的 Jev 等评估模型的内容。这些模型现在也通过 `experimental_decide` 调用。消息提示词会拼接为纯文本，不再序列化为 JSON 状态。

`ai` 固定为 `7.0.137`，`@ai-sdk/otel` 固定为 `1.0.137`，因为决策 API 尚属实验功能，曾在补丁版本中发生变化，而且 `@ai-sdk/otel` 依赖一个确切的 `ai` 版本。使用 OpenAI 决策模型时，请使用 `@ai-sdk/openai` 4.0.89 或更高版本。早期版本收到的状态是 JSON 编码文本，而非纯文本。
