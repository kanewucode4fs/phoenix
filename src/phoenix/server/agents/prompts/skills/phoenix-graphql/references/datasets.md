<a id="dataset-datasetexample"></a>

# 数据集与示例（Dataset、DatasetExample）

<a id="reaching-a-dataset"></a>

## 获取数据集

**不存在 `getDatasetByName`**，应通过 `node(id:) { ... on Dataset { ... } }` 或 `datasets(filter: DatasetFilter, sort)` 连接获取。

<a id="dataset-fields"></a>

## Dataset 字段

- `name`、`description`、`metadata`
- `exampleCount(datasetVersionId)`
- `examples(datasetVersionId, splitIds, first, after, filter: String, filterIds)` → `DatasetExampleConnection`
- `versions(first, after, sort)` → `DatasetVersionConnection`
- `splits`、`labels`
- `experiments(first, after, filterCondition, filterIds)`、`experimentCount`

注意事项：

- **版本参数在所有位置均为 `datasetVersionId`**，不是 `versionId`；省略时获取最新版本。
- `examples` 有两个不同的筛选参数：`filter: String` 用于对输入、输出、元数据进行自由文本搜索，`filterIds: [GlobalID!]` 用于按成员 ID 查询。
- `experiments` 使用 `filterCondition: String`，不是 `filter`。

<a id="datasetexample-fields"></a>

## DatasetExample 字段

- `externalId`
- `revision(datasetVersionId) { input output metadata revisionKind }`：`input`/`output`/`metadata` 为 `JSON`；`revisionKind` 为 `CREATE`/`PATCH`/`DELETE`。
- `span`
- `datasetSplits`
- `experimentRuns(experimentIds, first, after)`

<a id="example"></a>

## 示例

```graphql
query DatasetExamples($id: ID!, $first: Int = 20) {
  node(id: $id) {
    ... on Dataset {
      name
      exampleCount
      examples(first: $first) {
        edges { node { id externalId revision { input output metadata } } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```
