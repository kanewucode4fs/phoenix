<a id="experiment-execution"></a>

# 实验执行

<a id="two-phase-architecture"></a>

## 两阶段架构

实验依次运行两个阶段，每个阶段有各自的追踪提供程序：

1. **任务阶段**：提供程序使用实验的 `projectName`。
2. **评估阶段**：提供程序使用 `projectName: "evaluators"`，避免评估 Span 混入任务追踪视图。

创建评估提供程序前，**必须**彻底清理任务提供程序。两个提供程序都以 `global: false` 创建，并显式挂载/分离，绝不依赖 `register()` 内置的全局注册。

<a id="provider-ownership"></a>

## 提供程序的所有权

创建追踪提供程序的函数拥有它，并且**必须**清理它。从调用方接收提供程序的函数**不得**清理它，以便复用提供程序（例如单独调用 `evaluateExperiment()` 时可接收外部提供程序）。

<a id="consistency-across-entry-points"></a>

## 各入口保持一致

`runExperiment()`、`resumeExperiment()` 和 `resumeEvaluation()` 都遵循两阶段模式。修改追踪或生命周期逻辑时，三者**必须**一致更新。
