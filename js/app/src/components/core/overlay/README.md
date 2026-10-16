<a id="overlay"></a>

# 叠加层

本模块包含显示在 Phoenix UI 上方的所有界面：模态框、抽屉、弹出层、菜单（通过 `Popover`），以及承载它们的应用框架。模块按自包含方式设计：不导入任何应用代码，应用也只通过 `index.ts` 导入它。请将其视为仓库内维护的独立包。

本文档的交互式配套示例位于 Storybook（`stories/design-system/overlays/Stacking.mdx`，标题为“叠加层堆叠与模态行为”）。

<a id="the-model"></a>

## 模型

每个叠加层都需要回答两个独立问题：

1. **模态行为**：该界面打开时，用户能否继续使用页面其他部分？（一种*交互契约*）
2. **堆叠**：该界面与其他界面重叠时，哪一个绘制在上方？（一种*绘制顺序*）

两者相互独立，绝不能根据其中一个推导另一个。

<a id="modality-three-tiers"></a>

### 模态行为：三个层级

| 层级 | 组件 | 阻止交互的范围 | 用途 |
| --- | --- | --- | --- |
| 1——视口模态 | `ViewportModalOverlay` + `ViewportModal` | 仅应用视口。助手侧栏仍可交互。绝不使用 `aria-modal`。 | 表单、编辑器等用户可能需要助手协助的内容 |
| 2——窗口模态 | `ModalOverlay` + `Modal`（原生 React Aria） | 所有区域，包括侧栏 | 破坏性操作确认、必须先处理的决策 |
| 非模态 | `Popover`、`Drawer`、菜单 | 不阻止任何区域，但用于关闭的按压事件会被**消费**，绝不穿透 | 菜单、选择器、可边工作边查阅的面板、详情抽屉 |

<a id="the-frame"></a>

### 框架

应用渲染一次 `OverlayFrameProvider`，并在其视口内渲染：

- `DrawerPlane`：`Drawer` 的 Portal 目标；视口模态框打开时不可交互。
- `ViewportModalPlane`：`ViewportModalOverlay` 的 Portal 目标。
- `ViewportPortal`：将 React Aria Portal（Toast）重新安置到视口中。
- 为每个必须被视口模态框阻止的区域设置 `inert={useOverlayFrame()?.isViewportBlocked || undefined}`（框架决定*是否阻止*；宿主决定*哪些区域*，因为只有宿主了解布局）。
- 为必须在层级 1 之上保持可交互的控件（助手侧栏开关）设置 `{...viewportModalInteractionExemptProps}`。这里有意不使用 React Aria 的 `data-react-aria-top-layer`，因为后者也会使该元素免受层级 2 阻止。

平面只是纯粹的 Portal 目标：设置 `pointer-events: none`，不参与布局，几何信息由宿主通过 `className`/`css` 提供。其余行为（z-index、inert 行为、注册）由本模块负责。

<a id="stacking-bands-not-numbers"></a>

### 堆叠：使用层带而非数值

绘制顺序来自应用级 z-index 令牌阶梯（由宿主定义，见“令牌契约”）。`Popover` 通过 `stacking` 属性获取层带；嵌套弹出层至少使用其父层的层带（此限制沿 React Context 传递，因此可跨越 Portal）。只允许请求两个层带：`app-floating` 用于应被模态框覆盖的持久面板式界面，`app-portaled-overlay`（默认）用于可轻触关闭的临时界面。其他阶梯位置属于固定自身层带的专用组件；如果允许弹出层请求这些位置，调用处就能把临时界面绘制到 Toast 上方。

如果嵌套叠加层被遮挡，说明组合方式或层带分配有误。绝不能使用原始 z-index 数值修补。

<a id="dismissal"></a>

### 关闭

- 层级 1 和层级 2 参与 React Aria 的叠加层栈，因此 Escape 和外部按压会从顶层向下处理，先处理其上方打开的菜单和弹出层。（`ViewportModal` 通过 `useOverlay` 调用加入栈，见该处注释。）
- `Drawer` 位于该栈*之外*（它不是 React Aria 叠加层）：其文档级 Escape 监听器改由框架的 `isViewportBlocked` 保护。
- 非模态弹出层/菜单主动启用 `closeOnInteractOutside`：用于关闭的按压事件会被消费，避免激活底层元素。这提供与模态底层遮罩相同的保证，但不锁定滚动，也不在整个应用上执行 aria 隐藏。见 `outsideInteraction.ts`。

<a id="polyfill-ledger"></a>

## 兼容补丁清单

本模块有意保留了针对 react-aria 的三处补丁。每处实现都注明上游链接和移除条件，概述如下：

| 兼容补丁 | 原因 | 移除条件 |
| --- | --- | --- |
| 区域范围的模态行为（`ViewportModal.tsx`、`frame.tsx`） | RA 模态行为固定作用于整个窗口；`ariaHideOutside` 的 `root` 选项未贯通 Hook/RAC（adobe/react-spectrum#8784 未修复即关闭，#8796 未合并，#7743/#7954 尚未关闭） | RA 提供区域模态行为后，统一使用 RAC `Modal` |
| 消费非模态叠加层的外部按压（`outsideInteraction.ts`） | `usePopover` 将 `isDismissable: !isNonModal` 写死；非模态 RAC 弹出层既不在外部按压时关闭，也不保护底层元素 | RA 允许非模态弹出层选择可关闭且消费事件的行为 |
| 模拟触发器状态（`triggerState.ts`） | RAC 通过 `OverlayTriggerStateContext` 连接 `Dialog` 的 `close`/`slot="close"`；不由 RAC 管理的叠加层必须自行提供该上下文 | RA 提供公开方式来提供叠加层关闭上下文 |

<a id="token-contract"></a>

## 令牌契约

宿主应用必须定义以下 CSS 自定义属性（Phoenix 中位于 `GlobalStyles.tsx`）：

- `--global-z-index-local-raised`、`--global-z-index-local-overlay`
- `--global-z-index-app-floating`、`--global-z-index-app-portaled-overlay`、
  `--global-z-index-app-modal-backdrop`、`--global-z-index-app-modal`
- 界面样式使用的设计令牌（`--global-background-color-*`、
  `--global-border-color-*`、`--global-rounding-*`、`--global-dimension-*`、
  `--global-modal-width-*`、`--global-popover-*`、`--global-overlay-*`、
  `--focus-ring-*`）

<a id="extending"></a>

## 扩展

- **新增阻塞界面** → 首先确定层级。层级 2 使用原生 RAC。层级 1：通过 `ViewportModalOverlay` Portal 到 `ViewportModalPlane`，或遵循其结构（向框架注册，使用 `useOverlay` 加入叠加层栈，用 `FocusScope` 限制焦点范围）。
- **新增非模态界面** → 基于 `Popover` 构建（自带层带和事件消费）；若是锚定框架的面板，则遵循 `Drawer`（Portal 到平面，使用 `createDismissTriggerState` 连接 RAC 关闭行为，并以 `isViewportBlocked` 保护所有全局快捷键）。
- **新增堆叠需求** → 向宿主阶梯添加令牌，仅当弹出层必须请求该层带时，才在 `stacking.ts` 中添加层带。绝不使用原始数值。
