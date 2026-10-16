<a id="charting"></a>

# 图表

<a id="style-guide"></a>

## 风格指南

- 使用 recharts 作为图表库
- 应用 `src/components/chart/defaults.tsx` 中的默认值，确保风格一致
- 在 `src/GlobalStyles.tsx` 中按语义定义图表颜色

<a id="canonical-example"></a>

## 规范示例

图表实现示例见 `src/components/chart/`。

<a id="workflow"></a>

## 工作流程

1. 导入 recharts 组件
2. 应用 `defaults.tsx` 中的默认值
3. 使用 GlobalStyles 中的语义颜色变量
4. 遵循现有图表组件模式
