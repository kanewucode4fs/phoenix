# Phoenix TS

用于与 Phoenix 交互及评估 LLM 应用的 TypeScript 包。

<a id="app"></a>

## 应用

### [app](./app/)

Phoenix Web 应用（工作区包 `phoenix-ui`）。它通过 `workspace:*` 使用 `@arizeai/phoenix-client` 和 `@arizeai/phoenix-evals`。前端开发流程见 [app/README.md](./app/README.md) 及仓库根目录的 [DEVELOPMENT.md](../DEVELOPMENT.md)。

<a id="packages"></a>

## 软件包

### [phoenix-client](./packages/phoenix-client/)

提供与 Phoenix 应用交互的客户端及工具。

<a id="examples"></a>

## 示例

### [notebooks](./examples/notebooks/)

一组 Deno Jupyter Notebook，展示如何使用 JavaScript 与 Phoenix 交互。

### [phoenix-experiment-runner](./examples/apps/phoenix-experiment-runner/)

使用 phoenix-client 和 @clack/prompts 交互式运行实验的示例应用。

<a id="development-guide"></a>

## 开发指南

以下说明如何配置 JS 单体仓库的工具。

## PNPM

本仓库通过 [pnpm 工作区](https://pnpm.io/workspaces)管理为单体仓库。按照以下步骤配置环境：

<a id="1-install-pnpm-if-you-dont-have-it"></a>

### 1. 安装 pnpm（如果尚未安装）

```sh
npm install -g pnpm@12.0.0
```

<a id="2-install-all-dependencies-for-all-packages"></a>

### 2. 为所有包安装全部依赖

在仓库根目录运行：

```sh
pnpm install
```

这会为单体仓库中的所有包安装依赖。

<a id="3-run-scripts-across-all-packages"></a>

### 3. 跨所有包运行脚本

可使用 pnpm 的递归模式，在所有包中运行脚本（如构建、代码检查、测试和格式化）：

```sh
pnpm run -r build      # Build all packages
pnpm run -r lint       # Lint all packages
pnpm run -r test       # Run tests for all packages (if defined)
pnpm run -r fmt:check  # Check formatting for all packages
```

### Changesets

本仓库管理的包通过 changeset 跟踪变更。Changeset 与语义化提交类似，会描述代码库的修改；不过，changeset 通过向 `.changeset` 目录提交文件来跟踪所有包的变更。如果修改了某个包，应通过以下命令为其创建 changeset：

```sh
pnpm changeset
```

并将其提交到 PR 中。

Changeset 表达了以指定的语义化版本增量类型发布一组包的意图，并附上变更摘要。

PR 合并后，GitHub Actions 会创建发布 PR。发布 PR 合并后，所有有变更的包都会将新版本发布到 npm。

Changeset 的详细说明见[官方文档](https://github.com/changesets/changesets)。
