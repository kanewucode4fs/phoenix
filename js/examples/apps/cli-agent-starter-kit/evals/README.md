<a id="agent-evaluation-harness"></a>

# Agent 评测框架

Phoenix 文档助手 CLI Agent 的自动化评测框架。

<a id="quick-start"></a>

## 快速开始

```bash
# Run all evaluations
pnpm eval

# Run evaluations matching a pattern
pnpm eval terminal

# Run specific evaluation directly
pnpm eval:terminal-format
```

<a id="available-evaluations"></a>

## 可用评估

- **终端安全格式**：调用真实 Agent，验证输出不含 Markdown 语法（粗体、斜体、代码块、链接等）

<a id="project-structure"></a>

## 项目结构

```
evals/
├── evaluators/          # Evaluator definitions (camelCase)
├── datasets/            # Test datasets (camelCase)
├── experiments/         # Experiment runners (kebab-case.eval.ts)
└── utils/              # Shared utilities (camelCase)
```

<a id="creating-new-evaluators"></a>

## 创建新评估器

1. **创建评估器**，文件为 `evals/evaluators/myEvaluator.ts`:

```typescript
import { createEvaluator } from "@arizeai/phoenix-evals";

export const myEvaluator = createEvaluator(
  ({ output }: { output: string }) => {
    const score = /* compute score */;
    const label = /* determine label */;
    return { score, label, explanation: "..." };
  },
  { name: "my-evaluator", kind: "CODE", optimizationDirection: "MAXIMIZE" }
);
```

2. **创建数据集**，文件为 `evals/datasets/myExamples.ts`:

```typescript
export const myExamples = [
  {
    input: { prompt: "test" },
    output: { response: "expected" },
    metadata: { category: "test" },
  },
];
```

3. **创建实验**，文件为 `evals/experiments/my-eval.eval.ts`:

```typescript
#!/usr/bin/env tsx
import { createClient } from "@arizeai/phoenix-client";
import { createOrGetDataset } from "@arizeai/phoenix-client/datasets";
import { runExperiment } from "@arizeai/phoenix-client/experiments";

async function main() {
  const client = createClient();

  const { datasetId } = await createOrGetDataset({
    client,
    name: "my-dataset",
    description: "My dataset description",
    examples: myExamples,
  });

  await runExperiment({
    client,
    experimentName: "my-eval",
    dataset: { datasetId },
    task: async (example) => example.output.response,
    evaluators: [myEvaluator],
    logger: console,
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
```

4. **运行**： `pnpm eval my-eval` 或 `tsx evals/experiments/my-eval.eval.ts`

<a id="view-results"></a>

## 查看结果

http://localhost:6006/datasets

---

<a id="benchmarking-strategy-evaluating-the-evaluators"></a>

## 基准测试策略：评估评估器

基于 LLM 的评估器本身也是模型，也可能出错。依赖评估器判断 Agent 输出前，应先衡量其准确程度。这称为**评估器基准测试**（或“元评估”）。

<a id="the-core-idea"></a>

### 核心思路

创建**黄金数据集**，即一小组已知正确答案的人工标注示例，然后对其运行评估器，衡量其与真实标签一致的频率。经过良好校准的评估器应达到 **TPR >80% 且 TNR >80%**，之后才能放心大规模使用。

```
Golden dataset (hand-labeled)
        │
        ▼
  Benchmark experiment
  (task = run the evaluator, evaluator = exact-match vs ground truth)
        │
        ▼
  Confusion matrix  →  TPR / TNR / Accuracy
```

<a id="keeping-benchmark-experiments-separate-from-task-experiments"></a>

### 将基准实验与任务实验分开

运行普通实验时，Phoenix 将其记录在**任务数据集**（如 `cli-agent-terminal-format`）下。基准实验使用**不同的数据集**（如 `cli-agent-terminal-format-benchmark`），使两种实验历史在 Phoenix UI 中保持独立。

为支持这一点，`evals/datasets/` 中的每个数据集定义都包含两个名称：

```typescript
export const terminalFormatDataset = {
  name: "cli-agent-terminal-format", // task evaluation dataset
  description: "...",
  benchmarkName: "cli-agent-terminal-format-benchmark", // evaluator benchmark dataset
  benchmarkDescription: "Golden dataset for benchmarking ...",
  examples: terminalFormatExamples,
};
```

基准脚本创建或复用 `benchmarkName` 数据集，使每次基准运行都作为该数据集下的新实验出现，与衡量 Agent 任务的实验完全分开。

<a id="project-structure-1"></a>

### 项目结构

```
evals/
├── benchmarks/          # Benchmark runners (kebab-case.benchmark.ts)
├── datasets/            # Dataset definitions (name + benchmarkName)
├── evaluators/          # Evaluator definitions
├── experiments/         # Task experiment runners (kebab-case.eval.ts)
└── utils/               # Shared utilities (confusion matrix, stats)
```

<a id="running-a-benchmark"></a>

### 运行基准测试

```bash
# Run all benchmarks
pnpm eval:benchmark

# Run a specific benchmark directly
tsx evals/benchmarks/terminal-format.benchmark.ts
```

<a id="how-the-benchmark-experiment-works"></a>

### 基准实验的工作原理

与普通实验相比，基准实验中的角色互换：

| 普通实验                  | 基准实验                         |
| ---------------------------------- | -------------------------------------------- |
| 任务 = Agent 逻辑                 | 任务 = 运行评估器                     |
| 评估器 = 评判 Agent 输出    | 评估器 = 与真实标签精确匹配 |
| 数据集 = Agent 输入/输出对 | 数据集 = 人工标注的黄金示例       |

基准任务调用被测评估器，将其预测标签作为任务输出返回。随后，精确匹配评估器将预测与黄金数据集中 `metadata.expectedSafe` 的真实标签比较。

```typescript
// Task: run the evaluator being benchmarked
const task = async (example) => {
  const result = await evaluator.evaluate({
    input: example.input,
    output: example.output.response,
    expected: example.output,
    metadata: example.metadata,
  });
  return result.label ?? "unknown";
};

// Evaluator: compare prediction to ground truth
const exactMatchEvaluator = asExperimentEvaluator({
  name: "exact-match",
  kind: "CODE",
  evaluate: ({ output, metadata }) => {
    const expectedLabel = metadata?.expectedSafe
      ? "compliant"
      : "non_compliant";
    const match = output === expectedLabel;
    return {
      score: match ? 1 : 0,
      label: output,
      explanation: `Expected: ${expectedLabel}, Got: ${output}`,
    };
  },
});
```

<a id="creating-a-new-benchmark"></a>

### 创建新基准测试

1. 通过 `metadata` 为数据集示例**添加真实标签**：

```typescript
export const myExamples = [
  {
    input: { prompt: "..." },
    output: { response: "plain text answer" },
    metadata: { expectedLabel: "pass", category: "compliant" },
  },
  {
    input: { prompt: "..." },
    output: { response: "**markdown** answer" },
    metadata: { expectedLabel: "fail", category: "violation" },
  },
];
```

2. 为数据集定义**添加 `benchmarkName`**：

```typescript
export const myDataset = {
  name: "my-task-dataset",
  description: "Examples used to evaluate the agent task",
  benchmarkName: "my-task-dataset-benchmark",
  benchmarkDescription: "Golden dataset for benchmarking my-evaluator accuracy",
  examples: myExamples,
};
```

3. **创建基准运行器**，文件为 `evals/benchmarks/my-eval.benchmark.ts`:

```typescript
#!/usr/bin/env tsx
import { createClient } from "@arizeai/phoenix-client";
import {
  createOrGetDataset,
  getDatasetExamples,
} from "@arizeai/phoenix-client/datasets";
import {
  asExperimentEvaluator,
  runExperiment,
} from "@arizeai/phoenix-client/experiments";
import { myDataset } from "../datasets/index.js";
import { myEvaluator } from "../evaluators/index.js";
import {
  computeConfusionMatrix,
  printConfusionMatrix,
  printExperimentSummary,
} from "../utils/index.js";

async function main() {
  const client = createClient();

  const { datasetId } = await createOrGetDataset({
    client,
    name: myDataset.benchmarkName, // <-- benchmark dataset, not task dataset
    description: myDataset.benchmarkDescription,
    examples: myDataset.examples,
  });

  const { examples } = await getDatasetExamples({
    client,
    dataset: { datasetId },
  });

  const groundTruthByExampleId = new Map(
    examples.map((ex) => [ex.id, ex.metadata?.expectedLabel as string])
  );

  const exactMatchEvaluator = asExperimentEvaluator({
    name: "exact-match",
    kind: "CODE",
    evaluate: ({ output, metadata }) => {
      const expected = metadata?.expectedLabel as string;
      const predicted = typeof output === "string" ? output : "unknown";
      return {
        score: predicted === expected ? 1 : 0,
        label: predicted,
        explanation: `Expected: ${expected}, Got: ${predicted}`,
      };
    },
  });

  const experiment = await runExperiment({
    client,
    experimentName: `my-eval-benchmark-${Date.now()}`,
    dataset: { datasetId },
    task: async (example) => {
      const result = await myEvaluator.evaluate({
        output: example.output?.response ?? "",
      });
      return result.label ?? "unknown";
    },
    evaluators: [exactMatchEvaluator],
  });

  printExperimentSummary({ experiment });
  const matrix = computeConfusionMatrix({
    experiment,
    groundTruthByExampleId,
    evaluatorName: "exact-match",
    positiveLabel: "pass",
    negativeLabel: "fail",
  });
  printConfusionMatrix(matrix);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
```

<a id="reading-the-confusion-matrix"></a>

### 解读混淆矩阵

基准测试会打印混淆矩阵，包含三个关键指标：

| 指标                                     | 衡量内容                                       | 目标 |
| ------------------------------------------ | ------------------------------------------------------ | ------ |
| **TPR** （真正率 / 灵敏度） | 评估器正确识别的真实正例比例 | > 80%  |
| **TNR** （真负率 / 特异度） | 评估器正确拒绝的真实负例比例    | > 80%  |
| **准确率**                               | 总体正确率                                      | > 80%  |

TPR 较低表示评估器存在过多假负例（放过不良输出）。
TNR 较低表示评估器存在过多假正例（将良好输出标记为失败）。

<a id="phoenix-ui-two-separate-dataset-pages"></a>

### Phoenix UI：两个独立数据集页面

由于基准测试使用不同的数据集名称，Phoenix UI 会在独立页面中展示：

- **`my-task-dataset`** → 评估 Agent 任务的实验
- **`my-task-dataset-benchmark`** → 衡量评估器准确率的实验

这种分离使你能够迭代评估器（重新运行基准测试、跟踪准确率变化），同时不污染 Agent 任务实验的历史记录。
