# register() API

<a id="key-behavior-global-parameter"></a>

## 关键行为：`global` 参数

- `global: true`（默认）：将提供程序挂载到 OTel 全局状态，并将自动分离绑定到 `shutdown()`。
- `global: false`：**不**挂载提供程序。调用方可通过 `attachGlobalTracerProvider()` 手动挂载。phoenix-client 实验采用此方式。

<a id="span-processors"></a>

## Span 处理器

提供 `spanProcessors` 时直接使用这些处理器，否则由 `getDefaultSpanProcessor()` 创建基于 OTLP 的处理器。

处理器来自 `@arizeai/openinference-vercel`（`OpenInferenceBatchSpanProcessor` / `OpenInferenceSimpleSpanProcessor`），而非 `@opentelemetry/sdk-trace-base`。

<a id="environment-variable-fallbacks"></a>

## 环境变量回退

`PHOENIX_COLLECTOR_ENDPOINT` 和 `PHOENIX_API_KEY` 分别作为 `url` 和 `apiKey` 参数的回退值。显式参数始终优先。
