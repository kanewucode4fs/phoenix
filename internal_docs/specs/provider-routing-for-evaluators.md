<a id="provider-routing-for-evaluators"></a>
# 评估器的提供商路由

<a id="problem"></a>
## 问题

**提示词会保存，配置则在外部。**

```
Prompt (saved in database) ──depends on──▶ Configuration (lives elsewhere)
                                                   │
                                                   ▼
                                            Can change independently:
                                            • Admin updates env vars
                                            • Someone deletes a custom provider
                                            • Credentials get rotated
                                            • User clears their browser
```

这是依赖管理问题，与代码依赖可能被更新或删除的库相同。无法消除依赖，只能决定如何处理。

<a id="four-things-to-keep-in-mind"></a>
## 需要同时考虑的四个方面

分析提供商配置时，需要同时考虑四个方面。它们并不独立，交互也很复杂，但有助于组织思路。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. WHAT         2. WHERE           3. HOW            4. WHEN               │
│  ─────────       ──────────         ─────────         ──────────            │
│  • Routing       • Env vars         • Interactive     • Create time         │
│  • Credentials   • Custom provider  • Scheduled       • Load time           │
│                  • Browser storage                    • Save time           │
│                  • Ephemeral                          • Run time            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

下面逐一说明。

<a id="1-what--routing-vs-credentials"></a>
### 1. 内容：路由与凭证

调用 LLM 需要两类信息：

| 组成 | 含义 | 示例 |
|-----------|------------|---------|
| **路由** | 请求发送到哪里 | `https://my-resource.openai.azure.com` |
| **凭证** | 如何认证 | API 密钥、IAM 角色、托管身份 |

不同提供商的需求不同：

| 提供商 | 路由 | 凭证 |
|----------|---------|-------------|
| OpenAI | 全局端点（内置） | API 密钥 |
| Anthropic | 全局端点（内置） | API 密钥 |
| Azure OpenAI | 每个部署单独的端点（必须配置） | API 密钥或托管身份 |
| AWS Bedrock | 区域（有默认值） | 访问密钥或 IAM 角色 |

**关键认识：** OpenAI 和 Anthropic 较简单，只需 API 密钥；Azure 和 AWS 较复杂，需要显式路由配置。

<a id="2-where--configuration-sources"></a>
### 2. 来源：配置来源

配置可来自多个位置：

| 来源 | 凭证？ | 路由？ | 存储位置 | 是否共享？ | 重载后保留？ |
|--------|-------------|----------|---------|---------|------------------|
| **临时字段** | ❌ | ✅（仅 Playground） | 内存 | ❌ | ❌ |
| **保存为默认值** | ✅ | ✅（仅 Playground） | 浏览器 localStorage | ❌ | ✅ |
| **密钥** | ✅ | ❌ | 数据库 | ✅ | ✅ |
| **自定义提供商** | ✅ | ✅ | 数据库 | ✅ | ✅ |
| **环境变量** | ✅ | ✅ | 服务端进程 | ✅ | ✅ |

**不对称之处**

| 场景 | 从前端获取凭证？ | 从前端获取路由？ |
|---------|---------------------------|------------------------|
| Playground | ✅ 是 | ✅ 是 |
| 评估器测试 | ✅ 是 | ❌ 否 |

用户可在 Playground 尝试不同端点，但评估器始终使用显式配置，即自定义提供商或环境变量。

<a id="3-how--execution-mode"></a>
### 3. 方式：执行模式

| 模式 | 用户在场？ | 浏览器可用？ | 反馈 |
|------|--------------|-------------------|----------|
| **交互式** | ✅ 是 | ✅ 是 | 即时 |
| **定时执行** | ❌ 否 | ❌ 否 | 延迟 |

**为什么这很重要：**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION MODE IMPACT                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INTERACTIVE                          SCHEDULED (future)                    │
│  ───────────                          ──────────────────                    │
│                                                                             │
│  Credentials from:                    Credentials from:                     │
│  1. Frontend (localStorage)           1. Custom provider secrets            │
│  2. Custom provider secrets           2. Environment variables              │
│  3. Environment variables                                                   │
│                                       (No frontend! No browser!)            │
│                                                                             │
│  Routing from:                        Routing from:                         │
│  1. Custom provider                   1. Custom provider                    │
│  2. Environment variables             2. Environment variables              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

交互路径可以使用浏览器存储，定时执行路径没有浏览器，因此不能使用。这限定了各模式可用的配置来源。

*说明：定时评估器尚未实现，目前全部为交互式。*

<a id="4-when--operation-timing"></a>
### 4. 时机：操作发生时间

问题常发生在“配置时”和“运行时”的时间间隔中。

**Playground 时序：**

| 操作 | 行为 | 配置来源 |
|-----------|-------------|---------------|
| 输入路由 | 用户输入端点 | 临时值，仅内存 |
| 运行 | 发起 API 调用 | 临时字段和环境变量 |
| 保存为提示词 | 创建提示词记录 | 仅保存模型名，**丢弃路由** |

**间隙：** 用户输入路由、运行成功并保存提示词，但提示词不包含使其成功的路由。

**评估器时序：**

| 操作 | 行为 | 配置来源 |
|-----------|-------------|---------------|
| 创建 | 选择提示词并配置映射 | 提示词的 custom_provider_id 或环境变量 |
| 稍后运行 | 在后台执行 | 作业运行时解析 |

**间隙：** 评估器引用某提示词创建，提示词依赖环境变量。数天后评估器运行，环境变量已经改变，行为也随之变化。

**关键认识：** Playground 在用户在场时立即验证。评估器在创建时通过测试按钮验证；路由缺失时，测试在保存前失败，从而在用户还能修复时发现配置问题。

<a id="how-the-dimensions-interact"></a>
### 各维度如何交互

以下场景展示它们之间的联系：

```
User creates prompt with Azure (WHAT: routing needed)
        │
        ├── Enters endpoint in UI field (WHERE: ephemeral)
        │         │
        │         └── Run in playground → ✅ Works (HOW: interactive)
        │         └── Save prompt → ❌ Endpoint not saved (WHEN: save discards routing)
        │
        ├── Clicks "Save as Default" (WHERE: browser localStorage)
        │         │
        │         └── New playground → ✅ Pre-filled (same browser)
        │         └── Scheduled job → ❌ No access (HOW: no browser in scheduled)
        │
        ├── Uses custom provider (WHERE: database)
        │         │
        │         └── Run in playground → ✅ Works
        │         └── Scheduled job → ✅ Works (database accessible everywhere)
        │
        └── Relies on env vars (WHERE: server process)
                  │
                  └── Playground → ✅ Works
                  └── Scheduled job → ✅ Works (same server)
                  └── Later, env vars change → ❓ RISK: config drift
```

用户用临时字段测试并成功，随后却创建使用环境变量的评估器，就会出现“Playground 可用，评估器失效”的问题。

<a id="the-policy"></a>
## 策略

<a id="resolution-order"></a>
### 解析顺序

```python
def resolve_provider_config(prompt):
    # 1. Try custom provider
    if prompt.custom_provider_id:
        provider = get_provider(prompt.custom_provider_id)
        if provider and provider.sdk == prompt.model_provider:
            return provider.config
        # Fall through if provider deleted or SDK mismatched
    
    # 2. Fall back to environment variables
    return get_config_from_env(prompt.model_provider)
```

<a id="when-to-warn-future-enhancement"></a>
### 何时警告（未来增强）

*尚未实现。如果增加主动警告，策略如下：*

| 状态 | 行为 | 是否警告？ |
|-------|--------------|----------|
| 自定义提供商存在 | 使用它 | ❌ 不警告 |
| 无提供商，简单 SDK | 使用环境变量 | ❌ 不警告 |
| 无提供商，Azure | 使用环境变量 | ✅ 警告：“正在使用服务端环境变量” |
| 无提供商，AWS | 使用环境变量 | ⚠️ 较弱警告，因为有默认区域 |
| 提供商已删除 | 回退环境变量 | ✅ 警告 |

**判断标准：** 是否有合理默认值？Azure 没有默认端点，缺失必然失败；AWS 有默认区域，通常可用；简单提供商有全局端点，只需 API 密钥。

<a id="what-we-accept"></a>
### 接受的情况

- 环境变量可能随时间变化，由管理员负责。
- 环境变量变化后提示词可能访问不同端点，警告但允许。
- 凭证失败在 API 调用时暴露，任何设计都无法避免。

<a id="what-we-reject-goals"></a>
### 不接受的情况（目标）

- 毫无提示的静默失败：可在回退模式显示横幅。
- 难懂的错误消息：应说明问题和修复方法。
- 意外删除提供商：可增加确认对话框，显示受影响资源。

<a id="ui-behavior"></a>
## 界面行为

<a id="ephemeral-fields-playground-yes-evaluator-no"></a>
### 临时字段：Playground 允许，评估器不允许

**Playground** 支持试验，用户希望快速测试不同端点，因此允许临时字段。可以添加明确警告，目前尚未实现：

```
┌─────────────────────────────────────────────────────────────────┐
│ Endpoint: https://my-resource.openai.azure.com                  │
│           ⚠️ Session only — not saved with prompt               │
└─────────────────────────────────────────────────────────────────┘
```

**评估器**是生产产物，临时字段会立即丢失，因此完全不显示。可增加警告横幅和自定义提供商入口，目前尚未实现：

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ Using server environment variables                           │
│                                                                 │
│ This evaluator will use AZURE_OPENAI_ENDPOINT from the server.  │
│ For reliable execution, select a custom provider.               │
│                                                                 │
│ [Select Custom Provider ▼]                                      │
└─────────────────────────────────────────────────────────────────┘
```

<a id="save-as-default-and-the-evaluator-test-button"></a>
### “保存为默认值”与评估器测试按钮

**“保存为默认值”保存全部内容，包括路由。** 这是有意设计，以方便 Playground 迭代。用户输入一次端点并保存后，可在不同浏览器会话中自动填充。

保存在 localStorage 的路由不会传递给评估器，后者使用自定义提供商或环境变量。这可以接受，因为**评估器编辑器的测试按钮是验证关卡**。

```
Playground                              Evaluator Editor
──────────                              ────────────────

User enters endpoint                    User selects prompt
     │                                       │
     ▼                                       ▼
Runs → works ✅                         Clicks "Test" → ?
     │                                       │
     ▼                                       ├── Custom provider set → ✅
"Save as Default"                            ├── Env vars configured → ✅
(saves to localStorage                       └── Neither → ❌ Fails immediately
 for convenience)                                 │
     │                                            ▼
     ▼                                  User sees error, can attach
"Save as Prompt"                        custom provider right there
(no routing saved)
```

**为何可行：**
- Playground 保持便利，无需每次会话重新输入端点。
- 测试按钮在创建评估器这一恰当时机暴露路由问题。
- 测试失败时，用户正在评估器编辑器中，可以直接修复。
- 不会带来虚假的安全感：用户确实验证了评估器可用。

<a id="error-messages-recommendation"></a>
### 错误消息（建议）

暴露错误时，应让用户知道如何处理：

```
Azure OpenAI endpoint not configured.

To fix this:
  1. Set AZURE_OPENAI_ENDPOINT environment variable, or
  2. Select a custom Azure provider in the model menu
```

不要只说“配置错误”，应说明哪里错了、如何修复。

<a id="sdk-modification-block-incompatible-changes"></a>
## SDK 修改：阻止不兼容变更

**问题：** 是否允许创建后更改自定义提供商的 SDK？

**答案：** 阻止不兼容变更，允许兼容变更。

| 变更 | 是否允许？ | 原因 |
|--------|----------|--------|
| OpenAI ↔ Azure | ✅ 是 | 同一 SDK 家族，仅路由变化 |
| OpenAI → Anthropic | ❌ 否 | 调用参数不同 |
| 任意类型 → Bedrock | ❌ 否 | 完全不同的 SDK |

**为何阻止而非警告：**
- 没有合理用例；管理员需要不同 SDK 时，应创建新提供商。
- 调用参数以未规范化形式存储，切换 SDK 会导致静默行为变化。
- 不应因管理员改变提供商用途而破坏已有提示词。
- 替代方式简单：创建新提供商，逐个更新提示词。

<a id="the-users-mental-model"></a>
## 用户心智模型

正确使用所需理解的内容：

1. **凭证：** 每个浏览器输入一次，本地保存，随请求发送。
2. **路由：** 来自自定义提供商或服务端配置，不存储在提示词中。
3. **自定义提供商：** 显式、稳定、共享，是配置复杂提供商的规范方式。
4. **提示词：** 保存模型名和提供商引用，不保存配置详情。

**简单提供商：** 输入 API 密钥即可。

**复杂提供商：** 创建自定义提供商，或依赖管理员配置的环境变量。

<a id="whos-responsible-for-what"></a>
## 职责分工

| 角色 | 职责 |
|-------|-----------------|
| **管理员** | 确保环境变量适合当前部署 |
| **用户** | 为自身场景选择合适提供商 |
| **系统** | 创建时通过测试按钮验证，运行时明确报错 |

**契约：** 使用环境变量意味着信任管理员；需要显式控制时，使用自定义提供商。

**验证流程：** 用户创建评估器 → 点击测试 → 缺少路由时立即失败，并提供可操作错误 → 用户在保存前修复。不存在静默失败。

<a id="edge-cases"></a>
## 边界情况

**问：自定义提供商凭证失效怎么办？**

提示词运行时以 401/403 失败。与环境变量情况相同，但更易诊断：错误指向具名提供商，而非泛指环境变量。

**问：用户通过环境变量创建提示词后，管理员又创建自定义提供商，会怎样？**

不会变化。提示词的 `custom_provider_id = NULL` 表示使用环境变量。新提供商不会追溯关联已有提示词。

**问：相同模型名在不同端点含义不同怎么办？**

Azure 确实存在该风险：两个提供商的 gpt-4 部署可能实际使用不同模型。系统信任配置，不进行语义验证。

**问：保存的提示词究竟保证什么？**

| 方面 | 是否保证？ |
|--------|-------------|
| 模型名相同 | ✅ 是 |
| SDK 相同 | ✅ 是，不兼容变更被阻止 |
| 端点相同 | ❌ 否 |
| 凭证相同 | ❌ 否 |
| LLM 行为相同 | ❌ 否，提供商可更新模型 |

**坦率的答案：** 保证非常有限。只有外部依赖不变时，提示词才保持相同行为，这是能做到的最好程度。
