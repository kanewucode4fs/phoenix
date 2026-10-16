<a id="phoenix-client-typescript-design-guidelines"></a>

# Phoenix Client（TypeScript）设计指南

<a id="code-style"></a>

## 代码风格

- 使用 TypeScript 严格模式
- 导出清晰且有类型的接口
- 遵循基于资源的 API 模式
- 保持方法简单且可组合

<a id="canonical-examples"></a>

## 规范示例

参考 `src/` 中的现有实现：

- 资源客户端遵循一致模式
- 类型定义放在独立文件中
- 清晰分离关注点

<a id="workflow"></a>

## 工作流程

1. 先定义类型
2. 实现客户端方法
3. 添加完整的 JSDoc 注释
4. 通过真实 API 调用测试
5. 更新示例
