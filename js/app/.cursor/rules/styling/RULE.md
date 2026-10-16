<a id="styling"></a>

# 样式

<a id="code-style"></a>

## 代码风格

- 所有样式均使用 Emotion CSS-in-JS
- 使用 `src/GlobalStyles.tsx` 中的设计令牌和 CSS 变量
- 使用 data 属性表达组件变体
- 使用局部作用域 CSS 变量提高可读性
- 样式变量始终以 `CSS` 为后缀

<a id="canonical-example"></a>

## 规范示例

设计令牌和模式见 `src/GlobalStyles.tsx`。

<a id="workflow"></a>

## 工作流程

1. 导入 emotion 的 `css` 函数
2. 使用 GlobalStyles 中的设计令牌
3. 为变体应用 data 属性
4. 将样式与组件放在一起
