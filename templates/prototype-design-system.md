---
document_type: prototype-design-system
version: 1.0.0
status: draft
theme: enterprise-light
owner: Product Owner / Design Owner
last_updated: YYYY-MM-DD
---

# HTML Prototype 设计系统模板

> 本文档与同目录的 `Prototype.html` 共同构成 HTML 原型生成标准。`Prototype.html` 规定页面骨架、组件结构和交互基线；本文档规定视觉、版式和交互表现；`references/design-tokens.json` 提供可机器读取的具体令牌值。

## 1. 设计目标

- 产品气质：简洁、专业、可信、易操作。
- 主要使用场景：桌面端 SaaS，兼容窄屏浏览。
- 核心原则：清晰的信息层级、稳定的交互反馈、低认知负担。

## 2. 主题配置

| 项目 | 当前值 | 备注 |
|---|---|---|
| 主题名称 | enterprise-light | 可替换为品牌主题或暗色主题 |
| 主色 | #2563EB | 主要操作和选中状态 |
| 页面背景 | #F8FAFC | 页面级背景 |
| 内容面板 | #FFFFFF | 卡片、表格和弹窗 |
| 正文颜色 | #0F172A | 主要信息 |
| 辅助文字 | #64748B | 描述和次要信息 |
| 边框颜色 | #E2E8F0 | 分割线和控件边框 |
| 字体 | Inter / system-ui | 以 design-tokens.json 为准 |

## 3. 版式规范

- 页面最大宽度：1440px。
- 内容最大宽度：1200px。
- 基础间距单位：4px。
- 常用圆角：8px。
- 顶部导航高度：64px。
- 桌面到窄屏断点：768px。

## 4. 组件规范

### Button

- Primary：主流程唯一主要动作。
- Secondary：次要动作。
- Danger：删除、归档等危险动作。
- 所有按钮需要有 hover、focus、disabled 状态。

### Form

- 每个控件需要关联标签。
- 必填项需要明确标识。
- 校验失败时在控件附近展示原因。
- 提交中需要展示 loading 状态并避免重复提交。

### List / Table

- 支持标题、辅助说明、操作区和数据区域。
- 必须定义空状态、无结果状态和错误状态。
- 行操作应保持位置和文案一致。

### Feedback

- 成功：绿色语义，但同时使用文字或图标。
- 警告：橙色语义，并说明需要采取的动作。
- 错误：红色语义，并提供可理解的错误原因。

## 5. 原型约束

- Prototype 使用模拟数据，不连接生产数据。
- 所有页面均应从需求和功能规格中追踪而来。
- 颜色、字体、间距和圆角统一引用 `design-tokens.json`。
- 生成时必须以 `Prototype.html` 作为结构与交互参考，不得从历史 Prototype 或临时页面派生。
- 模板中的产品名称、业务文案和示例数据仅用于说明结构，必须依据已确认的 Product Requirement 和 Feature Specification 替换。
- 原型中发现的视觉调整记录在本文档的变更记录中。

## 6. 人工确认项

- [ ] 页面风格符合产品定位。
- [ ] 主色、字体和信息层级符合预期。
- [ ] 核心组件样式已确认。
- [ ] 桌面端和窄屏端布局已确认。
- [ ] 空、加载、错误和成功状态已确认。

## 7. 变更记录

| 版本 | 日期 | 修改人 | 修改内容 |
|---|---|---|---|
| 1.0.0 | YYYY-MM-DD | Design Owner | 初始设计系统 |
