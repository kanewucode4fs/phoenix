<a id="running-phoenix-client-examples"></a>

# 运行 phoenix-client 示例

运行本目录中的 TypeScript 示例需要全局安装 `tsx`。`tsx` 可直接运行 TypeScript 文件，无需预先编译。

<a id="install-tsx-globally"></a>

## 全局安装 tsx

```sh
pnpm install tsx -g
```

<a id="run-an-example"></a>

## 运行示例

可使用 `tsx` 运行任意 TypeScript 示例文件：

```sh
tsx <example-file>.ts
```

例如，运行 `run_experiment.ts`：

```sh
tsx run_experiment.ts
```

<a id="run-the-eval-test-examples"></a>

## 运行评估测试示例

vitest 示例位于 [`vitest/`](./vitest)，使用 `@arizeai/phoenix-client/vitest` 子模块及 `vitest/phoenix.vitest.config.ts` 配置。

- `01-basics` … `08-acceptance-scorecard`：按编号介绍完整 API（标注、`test.each`、重复执行、跳过 / 试运行 / 聚焦、参考键别名，以及带 `direction` 的验收标准）。这些示例针对确定性的替代应用（`app.ts` / `evaluators.ts`）**完全离线**运行，无需 API 密钥。
- `sql.eval.ts`：流程相同，设置 `OPENAI_API_KEY` 时调用真实 OpenAI（否则回退到离线替代实现）。

示例导入包的构建入口（如 `@arizeai/phoenix-client/vitest/reporter`，包将其映射到 `dist/`），因此需先构建一次；刚检出时尚不存在 `dist/`：

```sh
cd js/packages/phoenix-client
pnpm build
```

然后在本地运行整个套件，不向 Phoenix 同步任何内容：

```sh
cd js/packages/phoenix-client
PHOENIX_TEST_TRACKING=false pnpm exec vitest run \
  --config examples/vitest/phoenix.vitest.config.ts
```

要将结果记录到 Phoenix 服务器，请去掉 `PHOENIX_TEST_TRACKING=false`，并设置 `PHOENIX_ENDPOINT` / `PHOENIX_API_KEY`。追加文件路径（如 `examples/vitest/01-basics.eval.ts`）可只运行单个文件。请在包根目录运行，以便 `pnpm exec` 解析工作区包和依赖。
