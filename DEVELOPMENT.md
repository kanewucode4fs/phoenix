<a id="developers-guide"></a>

# 开发者指南

> 本项目开发先阅读 [工程目录与命令入口](AGENTS.md) 和 [中文项目文档索引](docs/00-总索引.md)。本文件保留上游开发细节；日常部署使用根 Dockerfile + Compose，`scripts/docker/devops/` 是另一套开发环境。

- [开发者指南](#developers-guide)
  - [快速开始](#quickstart)
  - [配置 macOS 开发环境](#setting-up-your-macos-development-environment)
  - [测试与代码检查](#testing-and-linting)
  - [安装 pre-commit 钩子](#installing-pre-commit-hooks)
  - [贡献 Notebook](#contributing-notebooks)
  - [贡献文档](#contributing-documentation)
    - [开始使用](#getting-started)
    - [修改文档](#making-changes)
  - [构建软件包](#building-the-package)
  - [安装 Phoenix 构建产物](#installing-a-phoenix-build)
  - [在 Colab 上安装 `git` 分支](#installing-a-git-branch-on-colab)
  - [最佳实践](#best-practices)
    - [REST API](#rest-api)
      - [HTTP 方法](#http-methods)
      - [状态码](#status-codes)
      - [路径结构](#path-structure)
      - [查询参数](#query-parameters)
      - [分页](#pagination)
      - [响应格式](#response-format)
  - [Cursor / VS Code](#cursor--vs-code)
    - [调试 Python 服务器](#debugging-the-python-server)

<a id="quickstart"></a>

## 快速开始

从刚克隆的仓库启动 Phoenix 开发服务器的最快方法。各步骤详情见下文章节。

**前置条件**

- [uv](https://docs.astral.sh/uv/getting-started/installation/) （Python 环境管理）。近期的任何 0.12.x 版本均可，无需与仓库固定版本完全一致。
- [nvm](https://github.com/nvm-sh/nvm) （Node 版本管理）

```bash
# 1. 安装 Python 依赖（以可编辑模式安装 Phoenix 及所有子包）
uv sync --all-extras --all-packages

# 2. 安装固定版本的 Node.js 和 pnpm
nvm install
npm i -g pnpm@12.0.0

# 3. 安装 dekit，供 `pnpm dev` 同时运行 API 和 UI 的进程管理器
curl -fsSL https://dekit.run/install.sh | sh

# 4. 安装 JavaScript 工作区依赖并构建 Web 应用
cd js
pnpm install
pnpm build
cp app/.env.example app/.env
# 在 app/.env 中设置 PHOENIX_ENABLE_AUTH=False 以在本地禁用身份验证

# 5. 启动开发服务器（Python API + 支持热重载的前端）
cd app
pnpm dev
```

`pnpm dev` 将 API、Vite 开发服务器和追踪生成器作为 dekit 任务启动，并连接控制台。这些任务在独立运行器中运行，因此关闭终端后仍会继续：按 `q` 断开连接并保持任务运行，按 `Q` 停止全部任务，或在 shell 中运行 `dekit down`。其他 CLI 用法见 `dekit help`。

打开 [http://localhost:6006](http://localhost:6006)。若启用了身份验证，使用 **`admin@localhost`** / **`admin`** 登录，或在 `js/app/.env` 中设置 `PHOENIX_ENABLE_AUTH=False` 以跳过验证。

> **💡 提示：** 可选择使用内存数据库，让 Phoenix 每次重启都从全新状态开始：
>
> ```bash
> PHOENIX_SQL_DATABASE_URL=sqlite:///:memory: pnpm dev
> ```

要向开发服务器发送追踪，请将使用 OpenInference/OpenTelemetry 插桩的应用指向 `http://localhost:6006`（例如，设置 `PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006`）。最简追踪 Agent 的实现见 [Vercel AI SDK 追踪指南](https://arize.com/docs/phoenix/integrations/typescript/vercel/vercel-ai-sdk-tracing-js)或可运行的 [AI SDK Agent 示例](./js/examples/apps/ai-sdk-agent)。

若某一步失败，请参阅下方详细配置说明。

<a id="setting-up-your-macos-development-environment"></a>

## 配置 macOS 开发环境

建议使用虚拟环境隔离 Python 依赖。本指南使用 `uv`，你也可以选择 `conda` 等其他虚拟环境管理工具。

系统中的 `uv` 只需满足 `pyproject.toml` 中 `tool.uv.required-version` 指定的版本范围。范围下限就是 CI 使用的确切版本，`uv.lock` 应由该版本生成，因为不同 `uv` 版本可能以不同方式序列化同一锁文件。你无需安装该版本。`scripts/uv.sh` 通过 `uv tool run` 运行固定版本的 `uv`（使用缓存，不进行全局安装）；`make`、`js/app` 的 pnpm 脚本和 Playwright 测试服务器都使用此封装。修改依赖时，请使用该封装，而非直接调用 `uv`：

```bash
scripts/uv.sh add <package>   # 或：scripts/uv.sh lock
pnpm --dir js/app uv lock     # 从 pnpm 调用同一封装
```

以下命令以可编辑模式安装主包 `arize-phoenix`、所有子包及开发依赖。它使用默认的开发 Python 版本，CI 仍会测试受支持的最低版本。

```bash
uv sync --python 3.11 --all-packages
```

`packages/` 目录下的子包（`phoenix.evals`、`phoenix.otel` 和 `phoenix.client`）会通过 `uv` 工作区配置自动以可编辑模式安装。

**接下来**，安装 Web 构建依赖。

建议[通过 nvm 安装 nodejs](https://github.com/nvm-sh/nvm)，然后全局安装 `pnpm` 来管理 JavaScript 工作区依赖。

```bash
# 安装 nvm
# https://github.com/nvm-sh/nvm
# 通过 nvm 安装 node，.nvmrc 文件会自动指示 nvm 安装
# 文件中指定的版本
nvm install
# 将其设为默认版本（可选）
nvm alias default <version-that-was-installed>
# 全局安装 pnpm
npm i -g pnpm@12.0.0
```

然后在 JavaScript 工作区根目录安装依赖并构建 Web 应用：

```bash
cd js
pnpm install
pnpm build
cp app/.env.example app/.env
```

有关 Web 应用开发的更多信息，请参阅 `js/app` 目录中的 `README.md`。

<a id="testing-and-linting"></a>

## 测试与代码检查

Phoenix 使用 `sqlite` 或 `postgresql` 数据库。默认情况下，涉及持久化的测试会在两种后端上运行。请确保系统已安装 `postgresql`。

```bash
brew install postgresql
```

请配置环境，确保 `pg_config` 指向正确的二进制文件。

```bash
pg_config --bindir
```

此命令应指向通过 `homebrew` 安装的 `postgresql`；否则，请尝试创建新的 Python 环境或修改 `PATH`。

Phoenix 使用 `tox` 运行代码检查、格式化、类型检查、测试等工具。

`tox` 管理相互隔离的虚拟环境，每个环境对应一组命令。这些环境定义在 `tox.ini` 中，可通过以下命令列出：

```bash
tox list
```

运行 `tox run -e <env-name>` 可执行对应环境中的命令。例如，以下命令运行单元测试：

```bash
tox run -e unit_tests
```

默认情况下，数据库测试使用 `sqlite`。要改用 `postgresql`，请传入 `--db postgresql`；pytest-postgresql 通过 `pg_config` 查找 `pg_ctl`，也可接受 `--postgresql-exec /path/to/pg_ctl` 参数。

```bash
tox run -e unit_tests -- --db postgresql
```

通过并行执行加速单元测试：

```bash
tox r -e unit_tests -- -n auto
```

运行类型检查：

```bash
make typecheck-python
```

在 `tox list` 的输出中查找代码检查、格式化及其他工具的命令。

<a id="installing-pre-commit-hooks"></a>

## 安装 pre-commit 钩子

首先，全局安装 `pre-commit`，建议使用 `uv` 完成。

```bash
uv tool install pre-commit --with pre-commit-uv
```

然后安装项目的 pre-commit 钩子：

```bash
pre-commit install
```

安装后，`.pre-commit-config.yaml` 中配置的 pre-commit 钩子会在每次 `git commit` 前自动运行。向 `git commit` 传入 `-n` / `--no-verify` 参数可跳过这些钩子。

<a id="contributing-notebooks"></a>

## 贡献 Notebook

新增或修改 Jupyter Notebook 时，需要运行以下命令以通过 CI。

- `tox run -e ruff`: 运行格式化工具
- `tox run -e clean_jupyter_notebooks`: 移除单元格输出及 Notebook 元数据，尽量缩小差异

<a id="contributing-documentation"></a>

## 贡献文档

Phoenix 文档使用 [Mintlify](https://mintlify.com/) 构建，源文件位于 `docs/` 目录。

<a id="getting-started"></a>

### 开始使用

1. 安装 Mintlify CLI：

```sh
npm i -g mint
```

2. 运行本地开发服务器：

```bash
mint dev
```

3. 在浏览器中打开 `http://localhost:3000` 预览修改。

<a id="making-changes"></a>

### 修改文档

- 文档页面使用 MDX（支持 JSX 的 Markdown）编写。
- `docs.json` 文件控制导航及全站设置。
- 图片和其他资源应放入相应子目录。

有关 Mintlify 的格式化、组件和部署等功能详情，请参阅 [Mintlify 快速开始指南](https://www.mintlify.com/docs/quickstart)。

<a id="building-the-package"></a>

## 构建软件包

构建 Phoenix 需要构建 `app` 和 Python 包。

构建 `app` 时，进入 `js/app` 目录并运行：

```bash
pnpm run build
```

然后在仓库根目录运行：

```bash
make build-python
```

成功后，仓库根目录的 `dist` 文件夹中会生成源码分发包（tarball）和 Python `wheel`。

<a id="installing-a-phoenix-build"></a>

## 安装 Phoenix 构建产物

建议使用独立虚拟环境（如 `phoenixtest`）安装并测试上述构建产物。

从源码分发包（即 tarball）安装 Phoenix，请运行：

```bash
pip install /path/to/source/distribution/tarball.tar.gz
```

从 Python `wheel` 安装 Phoenix，需先安装 `wheel`：

```bash
pip install wheel
```

然后运行：

```bash
pip install /path/to/wheel.whl
```

（每次只应选择源码分发包或 `wheel` 中的一种安装。）

要确认一切正常，先安装 `jupyter`：

```bash
pip install jupyter
```

然后运行 `tutorials` 目录中的 Notebook。

<a id="installing-a-git-branch-on-colab"></a>

## 在 Colab 上安装 `git` 分支

以下代码在 [Colab](https://colab.research.google.com/notebooks/empty.ipynb) 中安装 `main` 分支，运行约需 3 分钟。

```jupyterpython
!npm install -g -s n
!n latest
!npm install -g -s npm@latest
%pip install git+https://github.com/Arize-ai/phoenix.git@main
```

<a id="best-practices"></a>

## 最佳实践

### REST API

- 除非 URL 另有指定，API 应使用 JSON 通信。
- API 应进行版本管理。发生不向后兼容的变更时，新路由应归入新版本。

<a id="http-methods"></a>

#### HTTP 方法

- **GET** 用于获取资源的表示。
- **POST** 用于创建新资源和子资源。
- **PUT** 用于更新已有资源。需要替换资源时使用 PUT。
- **PATCH** 用于更新已有资源。需要局部更新资源时使用 PATCH。
- **DELETE** 用于删除已有资源。

<a id="status-codes"></a>

#### 状态码

- **4xx** 客户端应用行为有误——客户端错误
- **5xx** API 行为有误——服务器错误
- **2xx** 客户端与 API 正常运行

<a id="path-structure"></a>

#### 路径结构

- 使用名词命名资源和子资源。
- 避免在路径中使用动词。
- 名词应使用复数形式；指向具体资源时，后接全局唯一标识符（如 `/datasets/:dataset_id`，其中数据集 ID 是与 GraphQL API 一致的全局唯一标识符）。

<a id="query-parameters"></a>

#### 查询参数

使用查询参数进行过滤、排序和分页。查询参数应使用 `_` 作为分隔符。

<a id="pagination"></a>

#### 分页

使用基于游标的分页。每次请求提供指向下一页结果的游标。

<a id="response-format"></a>

#### 响应格式

- 响应应为包含 `data` 键的 JSON 对象。
- 载荷内容应使用 snake_case 命名，便于转换为对象时处理。

## Cursor / VS Code

Cursor/VSCode 的推荐扩展列表位于 `.vscode/extensions.json`。
在 Cursor 中打开 Phoenix 时，系统会自动提示安装推荐扩展。
安装后，可将以下设置粘贴到 `.vscode/settings.json` 的工作区设置中，确保在单体仓库根目录打开 Phoenix 时扩展正常工作。

```json
{
  "python.languageServer": "Default",
  "mypy-type-checker.importStrategy": "fromEnvironment",
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "always"
    }
  },
  "[typescript, typescriptreact]": {
    "editor.defaultFormatter": "oxc.oxc-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.oxlint": "always"
    }
  },
  "mypy-type-checker.ignorePatterns": [".tox,.venv,js/app"],
  "javascript.preferences.importModuleSpecifier": "shortest",
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "oxc.fmt.configPath": ".oxfmtrc.jsonc",
  "oxc.path.oxfmt": "js/app/node_modules/oxfmt/bin/oxfmt",
  "oxc.path.oxlint": "js/app/node_modules/oxlint/bin/oxlint",
  "editor.defaultFormatter": "oxc.oxc-vscode",
  "editor.formatOnSave": true,
  "relay.rootDirectory": "js/app",
  "relay.pathToConfig": "js/app/relay.config.js",
  "relay.autoStartCompiler": true
}
```

> [!NOTE]
> 本仓库使用 TypeScript 7（原生编译器）编译，不再附带 `tsserver`，因此不要设置 `typescript.tsdk`。
> 若需与编译器一致的 IntelliSense，请安装 [TypeScript（原生预览版）](https://marketplace.visualstudio.com/items?itemName=TypeScriptTeam.native-preview) 扩展；否则，VS Code 内置的 TypeScript 语言服务也能正常用于编辑。
> 仍需 JS 编译器 API 的工具（openapi-typescript、typedoc、Storybook docgen）通过 `js/` 中的 `.pnpmfile.cjs` 解析 `@typescript/typescript6` 桥接包。

<a id="debugging-the-python-server"></a>

### 调试 Python 服务器

开发服务器启用了 `debugpy`，可从 VS Code 或 Cursor 连接调试器。

1. 在 `.vscode/launch.json` 中**创建启动配置**：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Phoenix Dev Server",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "justMyCode": false
    }
  ]
}
```

> **注意：** debugpy 默认端口为 5678。若通过 `DEBUGPY_PORT` 环境变量自定义端口，请同步更新启动配置中的 `port` 值。

2. 在 `js/app` 目录中**启动开发环境**：

```bash
 pnpm dev
```

这会通过 [dekit](https://dekit.run) 同时启动 Python 服务器和前端 UI（见 `js/app/dekit.yaml`）。服务器启动时，debugpy 将监听 5678 端口。

> **💡 提示：** 使用内存 SQLite 可获得全新数据库，不影响已有磁盘数据：
>
> ```bash
> PHOENIX_SQL_DATABASE_URL=sqlite:///:memory: pnpm dev
> ```
>
> **💡 提示：** 通过环境变量自定义端口：
>
> ```bash
> VITE_PORT=3000 DEBUGPY_PORT=5679 pnpm dev
> ```
>
> 环境变量在 dekit 运行器启动时生效。若运行器已启动，请先运行 `dekit down`，使新值生效。
>
> 也可添加到 `js/app/.env`：
>
> ```
> VITE_PORT=3000
> DEBUGPY_PORT=5679
> ```

3. 在任意 Python 文件的边栏（行号左侧）单击以**设置断点**。
4. **连接调试器**：

- 按 `⇧⌘D`（macOS）或 `Ctrl+Shift+D`（Windows/Linux）打开“运行和调试”面板
- 从下拉列表中选择 **"Attach to Phoenix Dev Server"**
- 按 `F5` 或单击绿色播放按钮

5. 通过 UI 或 API 向服务器发起请求，**触发代码执行**。
6. **调试**：命中断点后，使用调试工具栏逐步执行代码：

- `F10` — 单步跳过
- `F11` — 单步进入
- `F5` — 继续
- 在左侧面板检查变量，或在调试控制台中计算表达式
