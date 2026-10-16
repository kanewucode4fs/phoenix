<a id="testing-conventions"></a>

# 测试约定

<a id="real-otel-not-mocks"></a>

## 使用真实 OTel，不使用模拟

测试使用真实 OTel 组件和 Spy Span 处理器，验证实际的栈机制及全局状态管理。

**不得**模拟：

- `@opentelemetry/api`：它就是被测对象。
- `NodeTracerProvider`：使用带 Spy 处理器的真实实例。
- `globalThis[Symbol.for("opentelemetry.js.api.1")]` 处的全局状态：**必须**是真实状态。

<a id="cleanup"></a>

## 清理

每个涉及全局状态的测试都**必须**在 `afterEach` 中调用 `detachGlobalTracerProvider()`。挂载泄漏会破坏后续测试。

<a id="writing-new-tests"></a>

## 编写新测试

1. 使用 Spy 处理器（非真实导出器）创建提供程序。
2. 使用 `global: true` 调用 `register()`，或直接调用 `attachGlobalTracerProvider()`。
3. 通过 `trace.getTracer("test").startSpan("name").end()` 创建 Span。
4. 断言 `spyProcessor.onStart` 的调用次数，验证当前生效的提供程序。
5. 始终在 `afterEach` 中分离。
