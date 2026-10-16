<a id="tracing-and-provider-management"></a>

# 追踪与提供程序管理

<a id="route-all-global-state-through-phoenix-otel"></a>

## 所有全局状态均经由 phoenix-otel 管理

在 pnpm 工作区中，不同包可能将 `@opentelemetry/api` 解析为不同模块实例（符号链接路径不同 = 模块身份不同）。若一个包调用 `provider.register()`，另一个包通过不同导入读取全局状态，它们会看到不同状态。

所有全局追踪提供程序变更**必须**通过 `phoenix-otel` 的 `attachGlobalTracerProvider()` / `detachGlobalTracerProvider()` 完成。**绝不能**直接调用 `provider.register()`。

<a id="cleanup-sequence"></a>

## 清理顺序

`cleanupOwnedTracerProvider()` 执行： `forceFlush()` → `shutdown()` → `detach()`.

- 先 `forceFlush()`，再 `shutdown()`，否则会丢失待处理 Span。
- 在 `finally` 中调用 `detach()`；即使关闭失败，也**必须**清理全局状态。

<a id="stack-based-mount-system"></a>

## 基于栈的挂载系统

`phoenix-otel` 维护提供程序挂载栈，详情见 `phoenix-otel` 的 `rules/global-provider-lifecycle.md`。实验可临时替换用户的全局提供程序，分离时由栈自动恢复。
