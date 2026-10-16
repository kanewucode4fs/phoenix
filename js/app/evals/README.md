<a id="evals"></a>

# 评测

这些 Vitest 测试套件通过 [Phoenix 实验](https://arize.com/docs/phoenix)衡量提示词质量。由于会调用真实 LLM，因此与单元测试分开存放。运行方式：

```bash
pnpm eval  # records experiments to PHOENIX_HOST (default http://localhost:6006)
```

<a id="ai-query-evalsaiquery"></a>

## AI 查询（`evals/aiQuery`）

针对 `src/components/filter/ai/buildAIQueryPrompt.ts` 中过滤 DSL 提示词的爬山优化测试框架，使用过滤字段实际发布的生产 DSL 进行测试：

- `spanFilterPrompt.eval.ts`：使用 `src/pages/project/spanFilterDSL.ts` 中的 Span DSL
- `sessionFilterPrompt.eval.ts`：使用 `src/pages/project/sessionFilterDSL.ts` 中的会话 DSL，依托词汇表项目提供的过滤词汇
- `traceFilterPrompt.eval.ts`：使用 `src/pages/project/traceFilterDSL.ts` 中的追踪 DSL，依托词汇表项目提供的过滤词汇
- `experimentRunFilterPrompt.eval.ts`：使用 `src/pages/experiment/experimentRunFilterDSL.ts` 中的实验运行 DSL
- `spanFilterIntent.eval.ts`：评测 Span DSL 的语义忠实度。对现象的请求（“响应中存在道歉”）必须转换为搜索该现象在数据中留下的文本（`'sorry' in output.value`），而不是照搬请求中的词语（`'apology' in input.value`）

正确性提示词套件为 `googleModels.ts` 中的每个模型评分：每个模型翻译套件用例文件中的请求；若规范化后精确匹配，或裁判模型认为表达式等价，该用例即判定正确。意图套件没有可接受表达式列表，因为查询扩展没有唯一正确答案；其裁判改为根据现象描述、预期字段和示例表达形式评分。只有套件的受控通过率（`filter_correct`，意图套件则为 `intent_captured`）超过模型阈值时，套件才通过；随着提示词改进，应提高这些阈值。

会话和追踪提示词套件需要 `PHOENIX_HOST` 指向的 Phoenix 中有一个指定名称的项目：`PHOENIX_EVAL_VOCABULARY_PROJECT`（默认 `"default"`）。它们使用该项目的运行时词汇表，与过滤字段提供的词汇表相同。

Gemma 模型用于模拟默认的浏览器设备端模型（Gemma 是 Gemini Nano 对应的开放模型家族，与浏览器 Prompt API 一样，它将系统提示词合并到第一轮用户消息中）；flash-lite 层级用于模拟提供商最小的托管模型。

向 Phoenix 记录结果时，每次 AI SDK 调用（生成及裁判）均通过 `telemetry.ts` 追踪；每次实验运行的追踪都会在测试任务 Span 下展示 LLM Span。

<a id="environment"></a>

### 环境

| 变量 | 用途 |
| --- | --- |
| `GOOGLE_GENERATIVE_AI_API_KEY`（或 `GEMINI_API_KEY`） | 必填；未设置时跳过套件 |
| `PHOENIX_HOST` / `PHOENIX_API_KEY` | 将运行记录为实验的位置，默认 http://localhost:6006; 设置 `PHOENIX_TEST_TRACKING=false` 可试运行而不记录 |
| `PHOENIX_EVAL_VOCABULARY_PROJECT` | 会话/追踪套件获取过滤词汇表的项目，名称必须精确匹配；默认 `"default"` |

变量从 `js/app/.env` 读取（shell 变量优先）。
