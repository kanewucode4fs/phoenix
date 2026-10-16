<a id="otel-context--async-boundaries"></a>

# OTel 上下文与异步边界

本文是 Phoenix playground（聊天、评估器、流式输出）中为何避免**在异步生成器清理时使用 contextvars**的统一参考，说明如何验证并据此设计。涵盖问题、CPython/asyncio 根因、两种可行修复、选择生成器端修复的原因，以及设计在代码中的应用位置。

---

<a id="1-problem-statement"></a>

## 1. 问题说明

使用 OpenTelemetry `start_as_current_span` 或任何依赖 `contextvars` 的 API 时，当前上下文保存在 contextvar 中。在**异步挂起和恢复**边界，例如 `async for chunk in stream()`，上下文可能改变：

- **生成器端：**异步生成器设置 contextvar 并获得 token 后执行 `yield`，消费者抛出异常或退出后，生成器 `finally` 可能在**不同**上下文执行。在该 `finally` 中调用 `token.reset()` 会抛出 *"Token was created in a different Context"*，或 OTel 的 "Failed to detach context"。
- **消费者端：**消费者，例如对生成器执行 `async for` 的代码，也可能通过 contextvars 附加 span；跨异步边界时，清理在不同上下文执行的风险也可能存在。

**与代码的对应关系：**

| 角色 | 代码 | 修复前是否使用 contextvars？ |
|-----------|------------------------------|--------------------------------|
| 生成器 | `chat_completion_create()` | 是，隐式当前 span |
| 消费者 | `evaluate()`，例如 LLMEvaluator | 是，`start_as_current_span` |

目标：使用通用 Python **证明**失败模式，结合 CPython 和文档理解**原因**，然后**设计**出不跨这些边界依赖 contextvars 的实现。

---

<a id="2-root-cause-cpython-and-asyncio-behavior"></a>

## 2. 根因：CPython 和 asyncio 行为

<a id="21-what-we-observe"></a>

### 2.1 观察结果

异步生成器设置 contextvar 并取得 token 后让出执行，消费者在 `async for` 期间抛出异常时，生成器 `finally` 会稍后在不同执行上下文运行，导致 `token.reset()` 抛出：

```text
ValueError: <Token ...> was created in a different Context
```

检查位于 CPython `Python/context.c`：

```c
// PyContextVar_Reset():
PyContext *ctx = context_get();   // current context (from thread state)
if (ctx != tok->tok_ctx) {       // token's context (when set() was called)
    PyErr_Format(PyExc_ValueError,
                 "%R was created in a different Context", tok);
    return -1;
}
```

因此，生成器 `finally` 运行时的当前上下文与创建 token 的上下文**不同**。

<a id="22-why-async-for-does-not-call-aclose-on-exception"></a>

### 2.2 原因：`async for` 遇到异常不会调用 `aclose()`

相关代码：`Python/compile.c`（`compiler_async_for`）和 `Python/ceval.c`（`END_ASYNC_FOR`）。

- **`async for` 结构：**`GET_AITER` → 使用 `SETUP_FINALLY`、`GET_ANEXT`、`YIELD_FROM`（await）的循环、循环体，之后是含 `END_ASYNC_FOR` 的 **except 块**。此流程**没有**调用 `iterator.aclose()`。
- **`END_ASYNC_FOR` 的行为：**异常为 `StopAsyncIteration` 时出栈并继续。对于**其他任何异常**，包括循环体中的 `RuntimeError`，仅**重新抛出**，**不会**调用 `iterator.aclose()`。因此异常后异步生成器保持打开，仅在被**终结**时关闭，例如垃圾回收。

<a id="23-how-the-generator-actually-gets-closed-finalizer"></a>

### 2.3 生成器实际如何关闭：终结器

来自 `Lib/asyncio/base_events.py`：

```python
def _asyncgen_finalizer_hook(self, agen):
    self._asyncgens.discard(agen)
    if not self.is_closed():
        self.call_soon_threadsafe(self.create_task, agen.aclose())
```

事件循环在 `run_forever()` 中注册异步生成器钩子后，异步生成器销毁时会运行**终结器**，通过创建**新** Task 调度 `agen.aclose()`：

- `self.create_task(agen.aclose())` 创建**新** `Task`。
- 每个 `Task` 在创建时捕获**当前**上下文：`self._context = contextvars.copy_context()`，位于 `Lib/asyncio/tasks.py`。
- 因此运行 `aclose()` 的任务持有终结器执行时的**当前**上下文，例如回调或循环默认上下文，**不是**原消费者任务上下文。

任务运行时使用 `context.run(callback)`，位于 `Lib/asyncio/events.py` 的 `Handle._run()`。因此生成器代码，包括 `finally`，均在该**新**任务上下文执行。于是：

- token 在**上下文 A** 创建，即生成器运行并调用 `cv.set()` 时的原消费者任务。
- 生成器 `finally` 在**上下文 B** 运行，即终结器为执行 `aclose()` 创建的任务。
- `context_get()` 返回 B，`tok->tok_ctx` 为 A → "created in a different Context"。

**汇总：**消费者异常 → `async for` 不调用 `aclose()` → 生成器稍后终结 → 终结器执行 `create_task(agen.aclose())` → 生成器 `finally` 在不同上下文的新任务中运行。

*CPython 参考路径：*`Python/context.c`（`PyContextVar_Reset`、`context_get()`）、`Python/compile.c`（`compiler_async_for`）、`Python/ceval.c`（`END_ASYNC_FOR`）、`Lib/asyncio/base_events.py`（`_asyncgen_finalizer_hook`）、`Lib/asyncio/tasks.py`（Task 的 `copy_context()`）、`Lib/asyncio/events.py`（`Handle._run()`）。

---

<a id="3-official-python-documentation"></a>

## 3. Python 官方文档

语言和标准库文档描述了此行为及修复：

- **[异步生成器函数](https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions)**，语言参考：
    异步生成器提前退出，包括 break、调用方取消或其他异常时，其异步清理会在**意外上下文**中运行，例如所依赖任务生命周期结束后，或事件循环关闭期间调用异步生成器垃圾回收钩子时。**调用方必须通过 `aclose()` 显式关闭异步生成器**，以终结生成器并将其从事件循环分离。

- **[contextlib.aclosing](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing)**，标准库：
    使用 `async with aclosing(agen):` 可确保生成器异步退出代码**在与迭代相同的上下文中**执行，使异常和上下文变量按预期工作，且退出代码不会在所依赖任务生命周期之后执行。

因此有两种避免方式：
1. **调用方：**显式关闭生成器，例如 `async with aclosing(stream): ...`。
2. **生成器：**清理时不依赖 contextvars，在 `finally` 中使用 `start_span` 和 `span.end()`，而非 `start_as_current_span`。流式客户端选择方案 2，不依赖每个消费者都使用 `aclosing()`。

---

<a id="4-empirical-testing-generic-python-no-otel"></a>

## 4. 实测（通用 Python，无 OTel）

**位置：**`internal_docs/vignettes/otel-contextvars-async/contextvars_async_gen_demo.py`，本示例。
  **从仓库根目录运行：**`uv run python internal_docs/vignettes/otel-contextvars-async/contextvars_async_gen_demo.py`，不使用 pytest，仅 asyncio 和 assert，避免干扰因素。

<a id="41-scenarios-in-run_empirical_tests"></a>

### 4.1 `run_empirical_tests()` 中的场景

| 场景 | 结果 | 经验 |
|----------|--------|--------|
| 生成器设置 token，消费者**不使用** aclosing 并抛出异常 | 生成器 `reset(token)` **失败**，"different Context" | 普通 `async for` 加异常会将生成器留给终结器，导致上下文不同。 |
| 生成器设置 token，消费者**使用** `async with aclosing(gen):` 并抛出异常 | 生成器 `reset(token)` **成功** | 同一任务中显式关闭，保持清理上下文一致。 |
| 消费者设置 token，生成器抛出异常 | 消费者 `reset(token)` **成功** | 未复现消费者 token 失效；evaluate 中避免 contextvars 属于防御措施。 |
| 正常退出，无异常 | 生成器 `reset(token)` **成功** | 失败与异常和销毁路径有关，并非每次挂起都会发生。 |

由此可知：失败可复现且与终结器相关；直接消费者使用 aclosing 时，实测可修复；场景中消费者 token 保持有效，未复现消费者端失败；问题仅发生于异常或销毁，而非每次挂起。脚本先打印演示，再运行这些断言。

**消费者 evaluate 为何可使用 `start_as_current_span`：**消费者是异步**函数**，不是异步生成器。流抛出异常或循环中断时，异常传播，消费者的 `with` 块通过正常栈展开退出，仍在**相同**任务中。因此上下文管理器运行 `__exit__` 时，消费者 contextvar token 仍有效。实测场景 3—4 确认消费者 `reset(token)` 成功，所以 `evaluate` 可使用 `start_as_current_span`，其清理在同一任务执行。

<a id="42-what-aclosing-can-do-for-us"></a>

### 4.2 aclosing 能提供什么

- **调用方修复：**消费者使用 `async with aclosing(stream):`，再执行 `async for chunk in stream: ...` 时，break、异常或取消会使上下文管理器等待 `stream.aclose()`。生成器 `finally` 在**相同任务**和上下文运行，生成器内 contextvar token 仍有效。
- **收益：**1）同一任务中显式及时清理；2）将来若重新加入依赖上下文的清理，可保证上下文一致；3）标准库已有文档模式。
- **未依赖它的原因：**调用点有多个，包括评估器、订阅、chat_mutations 和 playground_clients。要求每个调用方使用 `aclosing()` 容易遗漏，也无法帮助旧版或第三方消费者。修复**生成器**，清理时不用 contextvars，在 `finally` 中使用 `start_span` + `span.end()`，可使流不受调用方迭代方式影响。仍可在自有调用点添加 `aclosing` 作为可选增强。

<a id="43-two-valid-fixes-clarification"></a>

### 4.3 两种有效修复（澄清）

**如果每个**通过 `async for` 遍历流的**调用点都使用 `aclosing`**，则**无需**停止在生成器中使用 `start_as_current_span`。有了 `aclosing`，生成器由消费它的同一任务关闭，`finally` 运行于相同上下文，contextvar token 保持有效。因此任一种修复都足够：

| 修复 | 做法 | 效果 |
|-----|-------------|--------|
| **调用方端** | 每个消费者使用 `async with aclosing(stream): async for ...` | 生成器 `finally` 在相同任务和上下文运行，生成器使用 `start_as_current_span` 安全。 |
| **生成器端**，当前选择 | 生成器在 `finally` 中使用 `start_span` 和 `span.end()`，不使用 `start_as_current_span` | 清理不依赖当前上下文，无论调用方是否使用 `aclosing` 均安全。 |

选择生成器端修复，使正确性不依赖所有调用方，包括未来和第三方代码，记住使用 `aclosing`。

<a id="44-why-aclosing-at-our-call-sites-was-not-enough-chain-of-generators"></a>

### 4.4 自有调用点的 aclosing 为何仍不足（生成器链）

实际中，在所有调用 `chat_completion_create` 的位置，包括订阅、chat_mutations、评估器和 playground_clients，均添加 `aclosing(stream)`，但仍出现 "Token was created in a different Context"。

**原因：**流的**消费者**往往自身也是**异步生成器**，例如订阅处理器通过 `async for chunk in stream: yield chunk` 向客户端输出。因此形成一条链：外层生成器 A（订阅）使用 `async with aclosing(stream B): async for chunk in B: yield chunk`。客户端断开或请求被放弃时，驱动 A 的任务可能被取消，A 也可能被丢弃。此后 A 仅由**终结器**关闭，终结器在**新**任务中运行 `create_task(A.aclose())`。新任务执行 A 的 `aclose()`，退出 A 的 `async with aclosing(B)` 并调用 `B.aclose()`。于是 B 从终结器任务关闭，而非原请求任务；B 的 `finally` 及 OTel detach 在错误上下文运行。

aclosing(B) 确实运行了，但它运行于 A 的 `aclose()` **内部**，而后者位于终结器任务。文档所保证的“生成器 finally 在与迭代相同的任务中运行”，对 B 而言仅相对于直接迭代 B 的代码，即 A 的函数体。A 自身被终结后，其函数体已不在原任务运行。

**要点：**若直接调用方自身是可能由终结器关闭的异步生成器，仅在直接调用点使用 aclosing 不足。该架构需要生成器端修复，使 B 的清理不使用 contextvars。

<a id="45-why-the-framework-stack-strawberry-starlette-asgi-matters"></a>

### 4.5 框架栈（Strawberry、Starlette、ASGI）为何相关

aclosing 不是因为 Strawberry、Starlette 或 ASGI 层“破坏”它而失效。我们确实正确地用 aclosing 包围流 B：执行 `async for chunk in stream` 的代码是订阅解析器，并运行 `async with aclosing(stream): ...`。细节在**更上一层**。

流的**消费者**是订阅解析器，即向客户端让出数据块的**异步生成器** A。迭代该解析器的是框架，即位于 Starlette/ASGI 之上的 Strawberry 订阅传输层。客户端断开或请求结束时，该层通常**不会**对订阅解析器调用 `aclosing`，而是丢弃解析器，之后再终结。因此：

- **我们**通过 aclosing 关闭流 B；迭代 B 的代码是解析器 A。
- **框架**不通过 aclosing 关闭解析器 A，而是将其留待垃圾回收和终结。
- 终结器在新任务中运行 `A.aclose()`，进而运行我们的 `aclosing(B).__aexit__`，使 B 在错误上下文关闭。

下层框架栈之所以相关，是因为它**决定谁迭代订阅**，且**不**保证迭代器，即解析器，在相同任务关闭，而不是因为它破坏 aclosing。解析器往往留给终结器，因此流最终从终结器任务关闭。无论框架如何关闭订阅，或根本不关闭，均需要生成器端修复，使 B 清理不依赖 contextvars。

---

<a id="5-testing-strategy"></a>

## 5. 测试策略

1. **先使用通用 Python** — 仅用 `contextvars` 和异步生成器，不用 OTel，证明挂起加异常后 token 可失效，从而获得可泛化的 Python 知识。
2. **映射至架构** — 生成器为流式 LLM 客户端，消费者为评估器或订阅处理器。设计为生成器从不使用 `start_as_current_span`，而在 `finally` 中使用 `start_span` 并手动 `span.end()`，使清理不触及 contextvars。
3. **应用测试** — 现有测试，例如 `test_playground_clients.py`、评估器测试、chat_mutations/subscriptions，验证生成器端修复产生预期追踪，且没有 "Failed to detach context" 或 token 错误。

---

<a id="6-design-decisions-summary"></a>

## 6. 设计决策（汇总）

| 组件 | 决策 | 原因 |
|-----------|----------|-----------|
| **playground_clients.py** 的 `chat_completion_create` | 在 `finally` 使用 `tracer.start_span(...)` 和 `span.end()`，不使用 `start_as_current_span`。 | 已证明：由其他任务关闭时，生成器 contextvar token 可能在 `finally` 失效，避免在生成器中附加 contextvars。 |
| **evaluators.py** | 正常使用 `start_as_current_span`；evaluate 是异步函数而非异步生成器，清理在同一任务运行。 | 消费者 token 保持有效，参见 §4.1；evaluate 没有生成器端风险。 |
| **subscriptions.py / chat_mutations.py** | 消费流的调用点使用 aclosing；`chat_completion_create` 的生成器端修复使流即使在订阅解析器终结时也安全。 | 纵深防御；生成器清理不依赖 contextvars。 |

---

<a id="7-references"></a>

## 7. 参考资料

- **Phoenix 代码：**`src/phoenix/server/api/helpers/playground_clients.py`、`src/phoenix/server/api/evaluators.py`、`src/phoenix/server/api/subscriptions.py`、`src/phoenix/server/api/mutations/chat_mutations.py`。
- **通用演示：**`internal_docs/vignettes/otel-contextvars-async/contextvars_async_gen_demo.py`，从仓库根目录运行：`uv run python internal_docs/vignettes/otel-contextvars-async/contextvars_async_gen_demo.py`。
- **应用测试：**`tests/unit/server/api/helpers/test_playground_clients.py`、`test_evaluators.py`，以及启用追踪的完整聊天和订阅流程测试。
- **CPython**，本地 cpython 克隆中的路径：`Python/context.c`、`Python/compile.c`、`Python/ceval.c`、`Lib/asyncio/base_events.py`、`Lib/asyncio/tasks.py`、`Lib/asyncio/events.py`。
- **官方文档：**[异步生成器函数](https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions)、[contextlib.aclosing](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing)。
