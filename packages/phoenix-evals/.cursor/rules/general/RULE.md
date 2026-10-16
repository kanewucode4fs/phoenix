<a id="phoenix-evals-design-guidelines"></a>

# Phoenix Evals 设计指南

<a id="code-style"></a>

## 代码风格

- 使用清晰、具有描述性的函数名
- 为所有公共 API 提供完整文档字符串
- 遵循 numpy 文档字符串格式
- 包含类型提示

<a id="docstring-format"></a>

## 文档字符串格式

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description.

    Detailed description if needed.

    Parameters
    ----------
    param1 : Type1
        Description of param1
    param2 : Type2
        Description of param2

    Returns
    -------
    ReturnType
        Description of return value

    Examples
    --------
    >>> example_code()
    """
```

<a id="workflow"></a>

## 工作流程

1. 清晰设计评估器接口
2. 添加完整文档字符串
3. 包含使用示例
4. 使用多种 LLM 提供商测试
