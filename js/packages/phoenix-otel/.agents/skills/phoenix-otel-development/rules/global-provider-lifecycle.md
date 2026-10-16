<a id="global-tracer-provider-lifecycle"></a>

# 全局追踪提供程序生命周期

<a id="the-pnpm-module-identity-problem"></a>

## pnpm 模块身份问题

在 pnpm 工作区中，导入 `@opentelemetry/api` 的包可能解析到不同模块实例（符号链接路径不同 = 模块身份不同）。若 `phoenix-otel` 调用 `provider.register()`（SDK 的导入），而 `phoenix-client` 通过自身导入读取全局状态，它们会看到不同状态。

所有全局状态变更**必须**经过 `register.ts` 中的 `setGlobalProvider()`，它使用本模块自身的 OTel API 导入。**绝不能**直接调用 `provider.register()`。

<a id="stack-based-mount-system"></a>

## 基于栈的挂载系统

`attachGlobalTracerProvider()` 将挂载项压入栈，`detach()` 将其移出。首次挂载时，将已有全局状态捕获为基础快照；栈清空时恢复该快照。

分离非栈顶挂载项是安全的，但不会立即生效：挂载项会移除，而全局状态保持不变，直到栈顶挂载项分离。

<a id="auto-detach-on-shutdown"></a>

## 关闭时自动分离

以 `global: true` 调用 `register()` 时，`shutdown()` 自动调用 `detach()`。幂等标志确保分离至多执行一次。

使用 `global: false` 时（如 phoenix-client 实验），不应用此绑定，由调用方显式管理挂载。

<a id="invariants"></a>

## 不变量

1. 每次 `attachGlobalTracerProvider()` **必须**有对应的 `detach()`（显式调用或通过关闭触发）。
2. 所有挂载项分离后，**必须**将全局状态恢复为基础快照。
3. 全局状态**只能**通过本模块的 OTel API 导入设置，绝不能通过 `provider.register()`。
4. 乱序分离**不得**破坏全局状态，应静默忽略。
5. 基础快照仅捕获一次（首次挂载时），栈清空时清除。
