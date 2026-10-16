<h1 align="center" style="border-bottom: none">
    <div>
        <a href="https://phoenix.arize.com/?utm_medium=github&utm_content=header_img&utm_campaign=phoenix-client-ts">
            <picture>
                <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg">
                <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix-white.svg">
                <img alt="Arize Phoenix 标志" src="https://raw.githubusercontent.com/Arize-ai/phoenix-assets/refs/heads/main/logos/Phoenix/phoenix.svg" width="100" />
            </picture>
        </a>
        <br>
        @arizeai/phoenix-evals
    </div>
</h1>

<p align="center">
    <a href="https://www.npmjs.com/package/@arizeai/phoenix-evals">
        <img src="https://img.shields.io/npm/v/%40arizeai%2Fphoenix-evals" alt="NPM 版本">
    </a>
    <a href="https://arize-ai.github.io/phoenix/">
        <img src="https://img.shields.io/badge/docs-blue?logo=typescript&logoColor=white" alt="文档">
    </a>
    <img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=8e8e8b34-7900-43fa-a38f-1f070bd48c64&page=js/packages/phoenix-evals/README.md" />
</p>

此包提供与供应商无关的 TypeScript 评估库，可独立于任何框架或平台使用。此包仍在积极开发中，可能发生变更。

<a id="installation"></a>

## 安装

```bash
# or yarn, pnpm, bun, etc...
npm install @arizeai/phoenix-evals
```

此包基于仅支持 ESM 的 [AI SDK](https://ai-sdk.dev/) v7，要求 Node.js 22.12 或更高版本（CommonJS 构建依赖通过 `require()` 加载 ESM）。请使用兼容 AI SDK v7 的模型提供商包（如 `@ai-sdk/openai` v4+）。

<a id="usage"></a>

## 用法

<a id="creating-a-classifier"></a>

### 创建分类器

本库提供 `createClassifier` 函数，可为幻觉检测、相关性评分及任意二分类/多分类任务创建自定义评估器。

```typescript
import { createClassifier } from "@arizeai/phoenix-evals/llm";
import { openai } from "@ai-sdk/openai";

const model = openai("gpt-4o-mini");

const promptTemplate = `
In this task, you will be presented with a query, a reference text and an answer. The answer is
generated to the question based on the reference text. The answer may contain false information. You
must use the reference text to determine if the answer to the question contains false information,
if the answer is a hallucination of facts. Your objective is to determine whether the answer text
contains factual information and is not a hallucination. A 'hallucination' refers to
an answer that is not based on the reference text or assumes information that is not available in
the reference text. Your response should be a single word: either "factual" or "hallucinated", and
it should not include any other text or characters.

    [BEGIN DATA]
    ************
    [Query]: {{input}}
    ************
    [Reference text]: {{reference}}
    ************
    [Answer]: {{output}}
    ************
    [END DATA]

Is the answer above factual or hallucinated based on the query and reference text?
`;

// Create the classifier
const evaluator = await createClassifier({
  model,
  choices: { factual: 1, hallucinated: 0 },
  promptTemplate: promptTemplate,
});

// Use the classifier
const result = await evaluator({
  output: "Arize is not open source.",
  input: "Is Arize Phoenix Open Source?",
  reference:
    "Arize Phoenix is a platform for building and deploying AI applications. It is open source.",
});

console.log(result);
// Output: { label: "hallucinated", score: 0 }
```

完整示例见 [`examples/classifier_example.ts`](examples/classifier_example.ts)。

<a id="pre-built-evaluators"></a>

### 预置评估器

本库包含多个常见任务的预置评估器，附带优化后的提示词，可直接与任何 AI SDK 模型配合使用。

所有预置评估器均从 `@arizeai/phoenix-evals/llm` 模块导出：

| 评估器              | 函数                              | 说明                                                                       |
| ---------------------- | ------------------------------------- | --------------------------------------------------------------------------------- |
| 忠实度           | `createFaithfulnessEvaluator`         | 检测幻觉，检查输出是否基于提供的上下文 |
| 完整性           | `createCompletenessEvaluator`         | 检查对话中每个有效用户请求是否确实完成 |
| 简洁性            | `createConcisenessEvaluator`          | 评估响应是否适度简洁                           |
| 正确性            | `createCorrectnessEvaluator`          | 检查在给定输入下，输出是否符合事实                         |
| 检索相关性    | `createRetrievalRelevanceEvaluator`   | 衡量检索信息与请求的相关程度                       |
| 拒绝回答                | `createRefusalEvaluator`              | 检测模型是否拒绝回答                                       |
| 工具调用        | `createToolInvocationEvaluator`       | 评估是否使用正确参数调用正确工具           |
| 工具选择         | `createToolSelectionEvaluator`        | 检查是否为任务选择正确工具                           |
| 工具响应处理 | `createToolResponseHandlingEvaluator` | 评估模型利用工具响应的效果                               |
| 个人身份信息检测          | `createPiiDetectionEvaluator`         | 筛查对话记录中的个人身份信息             |

```typescript
import {
  createFaithfulnessEvaluator,
  createConcisenessEvaluator,
  createCorrectnessEvaluator,
  createRetrievalRelevanceEvaluator,
  createRefusalEvaluator,
} from "@arizeai/phoenix-evals/llm";
import { openai } from "@ai-sdk/openai";

const model = openai("gpt-4o-mini");

// Faithfulness: checks if the output is grounded in the context
const faithfulnessEvaluator = createFaithfulnessEvaluator({ model });
const faithfulnessResult = await faithfulnessEvaluator.evaluate({
  input: "What is the capital of France?",
  context: "France is a country in Europe. Paris is its capital city.",
  output: "The capital of France is London.",
});
console.log(faithfulnessResult);
// Output: { label: "unfaithful", score: 0, explanation: "..." }

// Correctness: checks if the output is factually correct
const correctnessEvaluator = createCorrectnessEvaluator({ model });
const correctnessResult = await correctnessEvaluator.evaluate({
  input: "What is the capital of France?",
  output: "Paris is the capital of France.",
});
console.log(correctnessResult);
// Output: { label: "correct", score: 1, explanation: "..." }

// Retrieval Relevance: checks if retrieved information is relevant to the request
const relevanceEvaluator = createRetrievalRelevanceEvaluator({ model });
const relevanceResult = await relevanceEvaluator.evaluate({
  input: "What is the capital of France?",
  context: "Paris is the capital of France and a major European city.",
});
console.log(relevanceResult);
// Output: { label: "relevant", score: 1, explanation: "..." }
```

<a id="code-evaluators"></a>

### 代码评估器

本库还内置了用于常见分类指标的确定性（非 LLM）代码评估器：精确率、召回率和 F-beta（包括 F1）。它们从 `@arizeai/phoenix-evals/code` 模块导出，针对一批预期标签与预测标签进行计算，既支持二分类（通过 `positiveLabel`），也支持多分类（通过 `macro`/`micro`/`weighted` 平均）。

- **精确率**：所有预测为某一类别的样本中，实际属于该类的比例（`TP / (TP + FP)`）。精确率越低，误报越多。
- **召回率**：实际属于某类的所有样本中，模型成功找到的比例（`TP / (TP + FN)`）。召回率越低，漏报越多。
- **F-beta**：精确率与召回率的加权调和平均。`beta = 1`（F1，默认）赋予两者相同权重；`beta > 1` 更重视召回率（漏掉真实正例代价更高时使用，如医疗筛查）；`beta < 1` 更重视精确率（误报代价更高时使用，如垃圾邮件过滤）。

```typescript
import {
  createPrecisionEvaluator,
  createRecallEvaluator,
  createF1Evaluator,
  createPrecisionRecallFScoreEvaluators,
} from "@arizeai/phoenix-evals/code";

const f1 = createF1Evaluator();
const result = await f1.evaluate({
  expected: ["cat", "dog", "cat", "bird"],
  output: ["cat", "cat", "cat", "bird"],
});
console.log(result);
// Output: { score: 0.6 }

// Or create matching precision/recall/F-score evaluators at once
const { precision, recall, fScore } = createPrecisionRecallFScoreEvaluators({
  average: "weighted",
});
```

需要 F1 之外的 F 分数时，使用 `createFBetaEvaluator({ beta })`（例如 `beta: 2` 使召回率权重高于精确率）。`createPrecisionRecallFScoreEvaluators` 返回共享同一个选项对象的三个独立评估器（`{ precision, recall, fScore }`），各自产生单个分数，与单独的工厂函数一致。

对于多分类数据，`average` 控制如何将各类别分数合为一个数值：`"macro"`（默认）对各类赋予相同权重，适合发现稀有类别是否被忽略；`"weighted"` 按类别出现频率加权，适合更看重总体表现而非类别间均衡的情况；`"micro"` 先汇总各类别的真正例、假正例和假负例，对于单标签多分类问题，其结果等于总体准确率。

可运行教程见 [`examples/classification_metrics_example.ts`](examples/classification_metrics_example.ts)，涵盖二分类、F-beta 取舍以及三种平均策略。底层公式、精确率/召回率取舍及参考文献见[精确率 / 召回率 / F 分数文档](https://arize.com/docs/phoenix/evaluation/pre-built-metrics/precision-recall-fscore)。

> **注意：** 与上述逐行 LLM 评估器不同，这些分类指标评估器工作在批次/数据集层面：`expected`/`output` 是全部示例的完整标签序列，而非单行标签。不要将其作为逐行评估器直接接入 `runExperiment`；应先收集每行的预期/预测标签，再对完整数组调用一次 `.evaluate({ expected, output })`。

<a id="data-mapping"></a>

### 数据映射

数据结构与评估器预期不一致时，使用 `bindEvaluator` 将字段映射为评估器预期的输入格式：

```typescript
import { bindEvaluator } from "@arizeai/phoenix-evals";
import { createFaithfulnessEvaluator } from "@arizeai/phoenix-evals/llm";
import { openai } from "@ai-sdk/openai";

const model = openai("gpt-4o-mini");

type ExampleType = {
  question: string;
  context: string;
  answer: string;
};

const evaluator = bindEvaluator<ExampleType>(
  createFaithfulnessEvaluator({ model }),
  {
    inputMapping: {
      input: "question", // Map "input" from "question"
      context: "context", // Map "context" from "context"
      output: "answer", // Map "output" from "answer"
    },
  }
);

const result = await evaluator.evaluate({
  question: "Is Arize Phoenix Open Source?",
  context:
    "Arize Phoenix is a platform for building and deploying AI applications. It is open source.",
  answer: "Arize is not open source.",
});
```

映射支持简单属性（`"fieldName"`）、点号路径（`"user.profile.name"`）、数组访问（`"items[0].id"`）、JSONPath 表达式（`"$.items[*].id"`）和函数提取器（`(data) => data.customField`）。

完整示例见 [`examples/bind_evaluator_example.ts`](examples/bind_evaluator_example.ts)。

<a id="experimentation-with-phoenix"></a>

## 使用 Phoenix 进行实验

此包与 [`@arizeai/phoenix-client`](https://www.npmjs.com/package/@arizeai/phoenix-client) 无缝配合，支持实验工作流。你可以创建数据集、运行实验，并追踪评估调用以进行分析和调试。

<a id="running-experiments"></a>

### 运行实验

要结合评估运行实验，请安装 phoenix-client

```bash
npm install @arizeai/phoenix-client
```

```typescript
import { createFaithfulnessEvaluator } from "@arizeai/phoenix-evals/llm";
import { openai } from "@ai-sdk/openai";
import { createDataset } from "@arizeai/phoenix-client/datasets";
import {
  asExperimentEvaluator,
  runExperiment,
} from "@arizeai/phoenix-client/experiments";

// Create your evaluator
const faithfulnessEvaluator = createFaithfulnessEvaluator({
  model: openai("gpt-4o-mini"),
});

// Create a dataset for your experiment
const dataset = await createDataset({
  name: "faithfulness-eval",
  description: "Evaluate the faithfulness of the model",
  examples: [
    {
      input: {
        question: "Is Phoenix Open-Source?",
        context: "Phoenix is Open-Source.",
      },
    },
    // ... more examples
  ],
});

// Define your experimental task
const task = async (example) => {
  // Your AI system's response to the question
  return "Phoenix is not Open-Source";
};

// Create a custom evaluator to validate results
const faithfulnessCheck = asExperimentEvaluator({
  name: "faithfulness",
  kind: "LLM",
  evaluate: async ({ input, output }) => {
    // Use the faithfulness evaluator from phoenix-evals
    const result = await faithfulnessEvaluator({
      input: input.question,
      context: input.context,
      output: output,
    });

    return result; // Return the evaluation result
  },
});

// Run the experiment with automatic tracing
runExperiment({
  experimentName: "faithfulness-eval",
  experimentDescription: "Evaluate the faithfulness of the model",
  dataset: dataset,
  task,
  evaluators: [faithfulnessCheck],
});
```

<a id="examples"></a>

## 示例

运行示例时，使用 `pnpm` 安装依赖并运行：

```bash
pnpm install
pnpx tsx examples/classifier_example.ts
# change the file name to run other examples
```

<a id="community"></a>

## 社区

加入我们的社区，与数千名 AI 开发者交流：

- 🌍 加入我们的 [Slack 社区](https://join.slack.com/t/arize-ai/shared_invite/zt-3r07iavnk-ammtATWSlF0pSrd1DsMW7g).
- 📚 阅读 [Phoenix 文档](https://arize.com/docs/phoenix).
- 💡 在 _#phoenix-support_ 频道提问并反馈。
- 🌟 为我们的 [GitHub](https://github.com/Arize-ai/phoenix) 加星。
- 🐞 通过 [GitHub Issues](https://github.com/Arize-ai/phoenix/issues) 报告问题。
- 𝕏 在 [𝕏](https://twitter.com/ArizePhoenix) 关注我们。
- 💼 在 [LinkedIn](https://www.linkedin.com/showcase/113218220) 关注我们。
- 🗺️ 查看我们的[路线图](https://github.com/orgs/Arize-ai/projects/45)，了解未来方向。
