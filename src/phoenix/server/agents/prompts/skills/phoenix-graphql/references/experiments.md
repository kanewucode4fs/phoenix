<a id="experiment-experimentrun"></a>

# 实验与实验运行（Experiment、ExperimentRun）

实验是对数据集中每个示例运行一次提示词或流水线。

<a id="reaching-an-experiment"></a>

## 获取实验

**不存在 `getExperimentById`**，应通过 `node(id:)`、`Dataset.experiments` 或 `compareExperiments` 获取 `Experiment`。

`Dataset.experiments` 默认按从新到旧排序并分页，因此**用户看到的实验编号**（从 1 开始、按从旧到新顺序生成的 `sequenceNumber`）未必位于第一页，较小编号反而离第一页最远。**不要**读取第一页后猜测，应精确解析编号：

- `experiments(sequenceNumbers: [Int!])`：只返回指定 `sequenceNumber` 的实验，无需分页。用户按编号指明实验时优先使用，例如“比较实验 5 和 7” → `sequenceNumbers: [5, 7]`。
- `experiments(sort: {col: sequenceNumber | createdAt, dir: asc | desc})`：重新排序连接，例如 `{col: sequenceNumber, dir: asc}` 可使序号 `1..N` 位于第一页。

报告获取到的实验前，确认其 `sequenceNumber` 与用户要求的编号一致。

```graphql
query ExperimentsByNumber($datasetId: ID!, $sequenceNumbers: [Int!]!) {
  node(id: $datasetId) {
    ... on Dataset {
      experiments(sequenceNumbers: $sequenceNumbers) {
        edges { node { id name sequenceNumber } }
      }
    }
  }
}
```

<a id="experiment-fields"></a>

## Experiment 字段

- `name`、`description`、`sequenceNumber`、`repetitions`、`isEphemeral`
- `dataset`、`datasetVersion`、`project`
- `runs(first, after, sort: ExperimentRunSort)`：**只能向前分页**，没有 `last`/`before`
- `runCount`、`expectedRunCount`
- `errorRate`、`averageRunLatencyMs`、`costSummary`、`costDetailSummaryEntries`
- `annotationSummaries { annotationName meanScore minScore maxScore count errorCount }`

<a id="experimentrun-fields"></a>

## ExperimentRun 字段

- `output`、`latencyMs`、`error`、`startTime`、`endTime`
- `annotations(first, after)`：连接，节点包含 `name`、`label`、`score`、`explanation`
- `example { id revision { input output metadata } }`：本次运行执行的数据集示例。**不存在** `datasetExample` 字段，`input`/`output`/`metadata` 位于 `example.revision`，不在 `example` 本身。

<a id="comparison"></a>

## 比较

比较候选方案时，优先使用 `compareExperiments(baseExperimentId: GlobalID!, compareExperimentIds: [GlobalID!]!, first, after, filterCondition)`，而非分别获取每个实验的运行。相关接口包括 `experimentRunMetricComparisons(baseExperimentId, compareExperimentIds)` 和 `validateExperimentRunFilterCondition(condition, experimentIds)`。

<a id="examples"></a>

## 示例

注意：如果实验来自通过 `execute_browser_action` 驱动的 Playground 运行，应优先使用 `playground.experiment.readResults` 界面操作，而非手写以下查询；该操作一次调用就返回相同的“分数加失败项”结构。

仅获取指标：

```graphql
query ExperimentMetrics($id: ID!) {
  node(id: $id) {
    ... on Experiment {
      name
      sequenceNumber
      runCount
      errorRate
      averageRunLatencyMs
      annotationSummaries { annotationName meanScore count errorCount }
    }
  }
}
```

带逐次运行输入、输出的评分结果，用于回答“哪些示例失败，以及为什么”；通过 jq 在客户端按 `annotations`/`error` 筛选：

```graphql
query ExperimentResults($id: ID!) {
  node(id: $id) {
    ... on Experiment {
      id name runCount expectedRunCount errorRate averageRunLatencyMs
      job { status }
      costSummary { total { cost tokens } }
      annotationSummaries { annotationName meanScore count errorCount }
      runs(first: 50) {
        edges { node {
          id output latencyMs error
          annotations { edges { node { name label score explanation } } }
          example { id revision { input output metadata } }
        } }
      }
    }
  }
}
```
