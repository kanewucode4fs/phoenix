<a id="running-phoenix-evals-examples"></a>

# 运行 phoenix-evals 示例

运行本目录中的 TypeScript 示例需要全局安装 `tsx`。`tsx` 可直接运行 TypeScript 文件，无需预先编译。

<a id="install-tsx-globally"></a>

## 全局安装 tsx

```sh
pnpm install tsx -g
```

<a id="run-an-example"></a>

## 运行示例

可使用 `tsx` 运行本目录中任意 TypeScript 示例文件：

```sh
tsx <example-file>.ts
```

例如，运行 `classification_example.ts`：

```sh
tsx classification_example.ts
```

运行命令时请确保位于 `examples` 目录，或提供示例文件的正确相对路径。
