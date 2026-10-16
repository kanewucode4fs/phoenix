<a id="phoenix-experiment-runner"></a>

# Phoenix 实验运行器

此示例应用使用 phoenix-client 和 @clack/prompts 运行实验。

它使用本地 ollama 实例中的 `llama3.2` 模型。

<a id="setup"></a>

## 配置

<a id="requirements"></a>

### 环境要求

- [Phoenix](https://phoenix.arize.com/) 在本地 `http://localhost:6006` 运行
  - `pnpm d:up` 会启动 Phoenix
  - 在 Phoenix 的 `http://localhost:6006/datasets` 页面中，使用当前目录的 `qa-dataset.csv` 文件创建数据集
- [Ollama](https://ollama.com/) 中已安装 `llama3.2`，或在 `.env` 中配置 OpenAI 凭证
  - 如果不想使用 Ollama，可将 `.env.example` 复制为 `.env` 并填写配置值
- Node.js 20+
- pnpm

<a id="install-dependencies"></a>

### 安装依赖

```bash
pnpm install
pnpm -r build
```

这会构建单体仓库中的所有依赖及应用。

<a id="run-the-app"></a>

### 运行应用

```bash
pnpm d:up
pnpm dev
```

这会在 `http://localhost:6006` 启动 Phoenix，并以开发模式启动应用。

<a id="build-the-app"></a>

### 构建应用

```bash
pnpm d:up
pnpm build
pnpm start
```

这会启动 Phoenix、构建应用，然后运行应用。
