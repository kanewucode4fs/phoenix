<a id="arize-phoenix-app"></a>

# Arize Phoenix 应用

Phoenix 应用是一个 Web 应用，用于快速排查模型推断和 LLM 应用的问题，并开展探索性数据分析（EDA）。它由 Phoenix 服务器托管，使用 Python 运行时提供的 GraphQL API。

<a id="installation"></a>

## 安装

本应用是以 [`js/`](../) 为根目录的 pnpm 工作区中的一个包（`phoenix-ui`），通过 `workspace:*` 依赖工作区包 `@arizeai/phoenix-client` 和 `@arizeai/phoenix-evals`。

构建和开发 Web 应用前，必须通过 `pnpm`（高性能 Node 包管理器）安装依赖。[安装 pnpm](https://pnpm.io/installation) 后，在当前目录或工作区根目录 `js/` 运行以下命令安装依赖：

```shell
pnpm install --frozen-lockfile
```

注意：`--frozen-lockfile` 标志强制 `pnpm` 安装 `js/pnpm-lock.yaml` 中指定的确切版本，不会重新生成锁文件。

然后构建应用依赖的工作区包：

```shell
pnpm run build:deps
```

<a id="develop"></a>

## 开发

开发 UI 时，必须将 `app` 与后端服务器一起运行。可通过以下命令以开发模式启动应用：

**重要：** 首次运行开发服务器前，需要先构建应用：

```shell
pnpm run build
```

```shell
pnpm run dev
```

运行上述脚本前，应在本项目根目录的 `.env.example` 旁创建 `.env` 文件以配置运行环境。`.env.example` 提供了 `.env` 文件示例。

根据所开发功能涉及的流程，可调整 [package.json](./package.json) 中的 scripts 部分，使服务器提供适当的测试数据。

<a id="production"></a>

## 生产环境

Phoenix UI 会打包为由 Python 后端提供的资源包。可运行以下命令模拟该模式：

```shell
pnpm run prod
```

<a id="environment-variables"></a>

### 环境变量

可在 `.env` 文件中配置以下环境变量：

- **`PHOENIX_ENABLE_SOURCE_MAP`**: 在 Vite 构建期间启用 source map，适用于需要生产构建，同时仍希望调试 JS 资源包的场景。

<a id="authentication"></a>

### 身份验证

本地开发有两种身份验证方式：

1. **跳过身份验证：**
   - 编辑 `.env` 文件并设置：
     ```
     PHOENIX_ENABLE_AUTH=False
     ```
   - 这会禁用身份验证，允许无需登录即可访问应用。

2. **默认凭证：**
   - 如果启用了身份验证，可使用默认凭证登录：
     - **邮箱：** `admin@localhost`
     - **密码：** `admin`

<a id="build"></a>

## 构建

应用使用 `typescript` 编写，并通过 [esbuild](https://esbuild.github.io/) 和 [relay-compiler](https://relay.dev/docs/guides/compiler/) 编译高效的 `graphql` 查询。因此，构建脚本包括：

1. 使用 `esbuild` 构建 `javascript` 和 `css` 资源
2. 使用 `relay-compiler` 构建编译后的 graphql 查询
3. 构建静态资源，例如初始化服务器的静态资源目录

Web 构建确保 UI 和数据获取层相对于 GraphQL 模式均完全类型安全。应用的类型安全通过 typescript CI 流水线进行静态验证。

<a id="test"></a>

## 测试

Phoenix 应用通过 `typescript` 静态分析类型安全，通过 [oxlint](https://oxc.rs/docs/guide/usage/linter) 静态检查最佳实践（利用 `oxlint-tsgolint` 进行[类型感知代码检查](https://oxc.rs/docs/guide/usage/linter/type-aware)，通过 `.oxlintrc.json` 的 `typeAware` 选项启用），并通过 `oxfmt` 强制格式化。React Compiler 规则被配置为错误，因此每个新增编译器诊断都会使本地代码检查和 CI 失败。现有 React Compiler 无法编译的情况已在相应调用处抑制；若未记录受影响代码必须保持未编译状态的原因，不得抑制新问题。单元测试使用 [vitest](https://vitest.dev/) 框架；集成测试（例如端到端或 e2e）使用 [playwright](https://playwright.dev)。以下 `pnpm` 命令对应上述检查。

```shell
pnpm run typecheck
pnpm run lint
pnpm run fmt:check  # Or `pnpm run fmt` to fix formatting issues
pnpm test
pnpm run test:e2e
```

注意：也通过 [pre-commit](https://pre-commit.com/) 钩子强制执行格式化。

<a id="integration-tests"></a>

### 集成测试

集成测试针对以“生产”模式构建的 Phoenix 服务器运行，因此需在本地 Python 环境中安装 Phoenix。

```shell
# from the root of the repository
pip install -e .

# from the app directory
pnpm run build
pnpm run test:e2e
```

<a id="architecture"></a>

## 架构

Phoenix 应用是在 [graphql](https://graphql.org) API 之上构建的 [react](https://react.dev) 应用。API 数据获取由 [react-relay](https://relay.dev/) 管理，这是一个具有明确设计约定的数据获取和存储库。服务器与应用之间的 API 契约由当前目录根部的 `schema.graphql` 文件管理，该模式通过服务器构建脚本生成。针对该模式的查询同样通过 `relay-compiler` 编译。`relay` 允许将组件的数据需求与组件本身放在一起，使系统数据流尽可能高效、清晰。

在 [react](https://react.dev) 应用内，还通过 `react` 内置 Hook 管理额外的 `state` 和 `context`。除 `react` 内置状态管理外，还使用 [zustand](https://github.com/pmndrs/zustand) 作为中心存储，管理点云可视化的大量状态。`zustand` 提供可扩展的跨组件状态管理方式，用户交互引起局部状态变化时不会带来性能损失。

Phoenix 应用是纯客户端 SPA（单页应用），通过 [react-router](https://reactrouter.com/en/main) 完全管理页面路由。`react-router` 提供嵌套路由（如根据路径渲染 UI 的不同部分），也用于在路由变化时加载数据（参见[加载器](https://reactrouter.com/en/main/route/loader)）。

Phoenix 使用 `react-aria-components` 构建组件。Arize 还维护 `@arizeai/point-cloud`，这是基于 [threejs](https://threejs.org/) 和 [react-three-fiber](https://docs.pmnd.rs/react-three-fiber/getting-started/introduction) 构建的 3D 可视化库。

<a id="dev-tools"></a>

## 开发工具

开发 Phoenix 应用时，推荐以下浏览器扩展：

- **[Redux DevTools](https://chromewebstore.google.com/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd?hl=en&pli=1)** - 用于调试应用状态变化。适用于任何状态管理架构，包括 Phoenix 用于管理 Playground 等状态的 Zustand。

- **[React Developer Tools](https://react.dev/learn/react-developer-tools)** - 用于检查 React 组件、编辑 props 和状态，以及发现性能问题，是调试性能问题和 React Compiler 优化的重要工具。

- **[GraphQL Network Inspector](https://chromewebstore.google.com/detail/graphql-network-inspector/ndlbedplllcgconngcnfmkadhokfaaln)** - 用于检查 GraphQL 请求，支持查询批处理，有助于调试 Phoenix 应用与服务器之间的 GraphQL API 交互。

- **[Relay Developer Tools](https://chromewebstore.google.com/detail/relay-developer-tools/ncedobpgnmkhcmnnkcimnobpfepidadl)** - 用于检查 Relay 存储中的数据，以及数据如何随 GraphQL 查询和变更而变化，是调试 Phoenix 广泛使用的 React Relay 数据获取层的重要工具。
