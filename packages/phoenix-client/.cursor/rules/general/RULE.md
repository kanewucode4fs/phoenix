<a id="phoenix-client-design-guidelines"></a>

# Phoenix Client 设计指南

<a id="code-style"></a>

## 代码风格

- 遵循基于资源的 API 模式
- 为所有公共方法使用类型提示
- 保持客户端方法简单且职责集中
- 将复杂逻辑委托给辅助模块

<a id="canonical-examples"></a>

## 规范示例

参考 `src/phoenix/client/resources/` 中的现有资源模块：

- `datasets/` - 数据集操作
- `spans/` - Span 查询和标注
- `experiments/` - 实验管理

<a id="workflow"></a>

## 工作流程

1. 在 `resources/` 目录定义资源
2. 在 `types/` 目录添加类型
3. 在 `helpers/` 中为复杂逻辑创建辅助函数
4. 保持 API 接口精简直观
5. 添加完整文档字符串
