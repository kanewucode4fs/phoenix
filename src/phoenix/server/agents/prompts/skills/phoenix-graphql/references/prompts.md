<a id="prompt-promptversion"></a>

# 提示词与版本（Prompt、PromptVersion）

<a id="reaching-a-prompt"></a>

## 获取提示词

**不存在 `getPromptByName`**，应通过 `node(id:)` 或 `prompts(filter: PromptFilter, labelIds)` 连接获取。

<a id="prompt-fields"></a>

## Prompt 字段

- `name`、`description`、`metadata`
- `version(versionId: GlobalID, tagName: Identifier)` → `PromptVersion`：**不传参数可获取最新版本**；传入 `versionId` 或 `tagName` 可固定版本。
- `promptVersions(first, after)` → `PromptVersionConnection`
- `versionTags`、`labels`

<a id="promptversion-fields"></a>

## PromptVersion 字段

- `modelName`、`modelProvider`
- `templateType`、`templateFormat`
- `template`：联合类型 `PromptStringTemplate | PromptChatTemplate`。聊天模板提供 `messages { role content { ... } }`，字符串模板提供 `template`。
- `invocationParameters`、`tools`、`responseFormat`
- `tags`、`isLatest`、`sequenceNumber`、`previousVersion`

<a id="example"></a>

## 示例

```graphql
query LatestPrompt($id: ID!) {
  node(id: $id) {
    ... on Prompt {
      name
      version {
        modelName
        modelProvider
        template {
          ... on PromptChatTemplate { messages { role } }
          ... on PromptStringTemplate { template }
        }
      }
    }
  }
}
```
