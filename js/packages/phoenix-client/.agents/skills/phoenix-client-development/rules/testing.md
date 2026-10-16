<a id="testing-conventions"></a>

# 测试约定

<a id="three-test-layers"></a>

## 三个测试层次

<a id="layer-1-unit-tests-vitest"></a>

### 第 1 层：单元测试（vitest）

在模块边界模拟外部依赖。模拟 `@arizeai/phoenix-otel` 时：

- `register()` **必须**返回包含 `getTracer()`、`forceFlush()` 和 `shutdown()` 的对象。
- `attachGlobalTracerProvider()` **必须**返回 `{ detach: vi.fn() }`。
- `forceFlush()` 和 `shutdown()` **必须**返回 Promise。

追踪测试需验证：

- 每个阶段调用一次 `register()`（任务 + 评估 = 2 次），传入正确的 `projectName` 和 `global: false`。
- `setGlobalTracerProvider: true` 时，每个阶段都调用 `attachGlobalTracerProvider()`。
- 每个 `detach()` 句柄恰好调用一次（无泄漏）。

<a id="layer-2-provider-lifecycle-tests-vitest-real-otel"></a>

### 第 2 层：提供程序生命周期测试（vitest、真实 OTel）

位于 `phoenix-otel/test/register.test.ts`。使用真实 OTel 组件和 Spy Span 处理器验证基于栈的挂载/分离机制。

<a id="layer-3-integration-tests-standalone-scripts"></a>

### 第 3 层：集成测试（独立脚本）

通过 `npx tsx` 针对运行中的 Phoenix 服务器执行，**不属于** vitest 套件。

- 文件名**必须**以 `integration-` 开头。
- 不得导入 vitest；使用普通 `assert()` 辅助函数。
- **不得**使用 `console.log`（代码检查规则：`no-console`）。
- 无输出即成功；为支持 CI，在 catch 处理器中调用 `process.exit(1)`。
- 清理 OTel 全局状态： `trace.disable()`, `context.disable()`, `propagation.disable()`.

**哨兵提供程序模式**：实验前注册一个提供程序，实验后断言它仍能接收 Span，以证明挂载/分离周期恢复了原始状态。
