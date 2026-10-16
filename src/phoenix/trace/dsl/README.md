本 Phoenix 模块使用 Python 的 `ast` 模块。以下代码片段简要介绍 `ast` 的用法。

<a id="abstract-syntax-tree-ast"></a>

# 抽象语法树（AST）

任何 Python 表达式都可以解析为 AST，再转换为另一个 AST。新的 AST 随后可以编译回 Python 表达式，并在运行时求值。

```python
import ast
```

<a id="constant"></a>

# 常量
https://docs.python.org/3/library/ast.html#ast.Constant

```python
print(ast.dump(ast.parse("None", mode="eval").body, indent=4))
print(ast.dump(ast.parse("1", mode="eval").body, indent=4))
print(ast.dump(ast.parse("'xyz'", mode="eval").body, indent=4))
```

<a id="output"></a>

### 输出
```python
Constant(value=None)
Constant(value=1)
Constant(value="xyz")
```

<a id="name"></a>

# 名称
https://docs.python.org/3/library/ast.html#ast.Name

```python
print(ast.dump(ast.parse("xyz", mode="eval").body, indent=4))
```

<a id="output-1"></a>

### 输出
```python
Name(id="xyz", ctx=Load())
```

<a id="compilation-and-evaluation"></a>

# 编译与求值
https://docs.python.org/3/library/functions.html#compile

```python
parsed = ast.parse("xyz", mode="eval")
compiled = compile(parsed, filename="", mode="eval")

eval(compiled, {"xyz": 42})
```

<a id="output-2"></a>

### 输出
```python
42
```

<a id="attribute"></a>

# 属性
https://docs.python.org/3/library/ast.html#ast.Attribute

```python
print(ast.dump(ast.parse("llm.token_count.completion", mode="eval").body, indent=4))
```

<a id="output-3"></a>

### 输出
```python
Attribute(
    value=Attribute(value=Name(id="llm", ctx=Load()), attr="token_count", ctx=Load()),
    attr="completion",
    ctx=Load(),
)
```

<a id="subscript"></a>

# 下标
https://docs.python.org/3/library/ast.html#ast.Subscript

```python
print(
    ast.dump(
        ast.parse("attributes[['llm', 'token_count', 'completion']]", mode="eval").body, indent=4
    )
)
```

<a id="output-4"></a>

### 输出
```python
Subscript(
    value=Name(id="attributes", ctx=Load()),
    slice=List(
        elts=[Constant(value="llm"), Constant(value="token_count"), Constant(value="completion")],
        ctx=Load(),
    ),
    ctx=Load(),
)
```

筛选器的标注访问器按实体划分作用域。追踪筛选器使用 `trace_annotations["name"]`，会话筛选器使用 `session_annotations["name"]`，跨度筛选器保留 `annotations["name"]`、`evals["name"]` 和 `trace_annotations["name"]`。可通过 `.score`、`.label` 或 `.explanation` 读取访问器；单独使用下标则检查是否存在。

<a id="translation-of-attribute-to-subscript"></a>

# 将属性访问转换为下标访问
https://docs.python.org/3/library/ast.html#ast.NodeTransformer

```python
class Translator(ast.NodeTransformer):
    def visit_Attribute(self, node):
        path = []
        while isinstance(node, ast.Attribute):
            path.append(node.attr)
            node = node.value
            if isinstance(node, ast.Name):
                path.append(node.id)
                break
        return ast.Subscript(
            value=ast.Name(id="attributes", ctx=ast.Load()),
            slice=ast.List(
                elts=[ast.Constant(value=p) for p in reversed(path)],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        )


parsed = ast.parse("llm.token_count.completion", mode="eval")
translated = Translator().visit(parsed)
print(ast.unparse(translated))
```

<a id="output-5"></a>

### 输出
```python
attributes[["llm", "token_count", "completion"]]
```
