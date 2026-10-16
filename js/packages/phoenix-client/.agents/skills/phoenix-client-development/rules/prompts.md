<a id="prompt-apis"></a>

# 提示词 API

<a id="select-prompts-with-a-selector-not-a-bare-string"></a>

## 使用选择器而非裸字符串选择提示词

`src/prompts/` 中的辅助函数在 `prompt` 键下接收**选择器对象**，绝不接收裸标识符字符串。`getPrompt` 通过 `PromptSelector`（`{ promptId }` | `{ name }` | `{ versionId }` | `{ tag, name }`）确立了这一约定，新辅助函数也遵循此约定。调用形式为 `{ prompt: { name: "x" } }`，明确 `"x"` 是*哪种类型*的标识。

`src/types/prompts.ts` 中有两个选择器联合类型，根据操作对象选择：

| 联合类型              | 成员                       | 用途                                             |
| ------------------ | ----------------------------- | ----------------------------------------------- |
| `PromptSelector`   | id, name, versionId, tag+name | 解析到提示词**版本**的操作 |
| `PromptIdentifier` | `{ promptId }` \| `{ name }`  | 针对**提示词本身**的操作             |

REST `{prompt_identifier}` 路径段接受 `PromptIdentifier`。使用 `src/utils/` 中的 `resolvePromptIdentifier()` 解析它，不要在调用处内联读取选择器。

<a id="guard-version-selectors-at-runtime"></a>

## 在运行时拦截版本选择器

仅靠 TypeScript 无法阻止向 `PromptIdentifier` 参数传入版本选择器：`GetPromptByTagSelector` 在结构上可赋值给 `GetPromptByNameSelector`，因此 `{ name, tag }` 变量会通过类型检查，并悄然将范围扩展到整个提示词。所以 `resolvePromptIdentifier()` 会在运行时拒绝 `versionId` 和 `tag`。必须保留这一检查；对破坏性操作而言，这关系到究竟只删除原本意指的某个版本，还是删除全部内容。

<a id="known-inconsistency"></a>

## 已知不一致

`updatePrompt` 早于此约定，仍接收 `promptIdentifier: string`。新辅助函数不要模仿它。若修改其签名，应新增受支持的 `prompt` 形式，并弃用 `promptIdentifier`，不要破坏现有调用方。

<a id="version-gate-new-routes"></a>

## 为新路由设置版本限制

提示词路由陆续出现在多个服务器版本中。向 `src/constants/serverRequirements.ts` 添加 `RouteRequirement`（路由首次发布的版本必须从 `CHANGELOG.md` 确认，不得猜测），并在请求前调用 `ensureServerCapability()`，使旧服务器返回明确错误提示，而非 404。
