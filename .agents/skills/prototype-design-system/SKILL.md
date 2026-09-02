---
name: prototype-design-system
description: Use when creating or reviewing HTML prototypes. Defines visual language, tokens, components, responsive behavior, and accessibility baseline. Authoritative values live in templates/design-tokens.json.
---

# Prototype Design System

## Purpose

为 HTML Prototype 提供统一、可复用、可检查的视觉和交互规范。

具体颜色、字体、间距、圆角数值以 `templates/design-tokens.json` 为准。

## Required References

开始生成或修改原型前，**必须**读取：

- `templates/design-tokens.json`
- `templates/prototype-design-system.md`（如项目确认后存在）
- `templates/Prototype.html`（结构与交互基线）

路径与版本解耦 —— design system 是**模板级常量**，不属于任何版本。

## Design Rules

### Visual Language

- 默认采用简洁、明亮、企业级 SaaS 风格。
- 页面背景、内容面板、文字、边框和状态色必须来自设计令牌。
- 不得在 CSS 中随意新增未定义的颜色、字号、圆角或阴影。
- 品牌主题变化应通过修改令牌完成。

### Typography

- 使用令牌中的字体栈。
- 明确的标题、正文、辅助文字层级。
- 重要信息不能只依靠颜色表达。
- 文本过长时应定义截断、换行或展开行为。

### Layout

- 使用统一的间距单位。
- 内容区、侧边栏、顶部导航、操作区职责清晰。
- 支持桌面和窄屏展示。

### Components

优先复用：

- Button: primary / secondary / danger / disabled / loading
- Input: default / focus / error / disabled
- Card: 标题 / 内容 / 操作区
- Table / List: 空状态 / 加载 / 无结果
- Badge / Status: 语义化状态色
- Modal / Drawer: 确认 / 取消 / 提交 / 关闭
- Toast / Alert: 成功 / 警告 / 错误 / 信息

### Interaction States

每个可操作页面至少考虑：

- 初始展示
- 加载
- 空数据
- 搜索无结果
- 表单校验失败
- 操作成功反馈
- 操作失败反馈
- 危险操作确认

## CSS Contract

1. 在 `:root` 中声明设计令牌对应的 CSS Custom Properties。
2. 组件样式优先引用 `var(--token-name)`。
3. 避免大面积内联样式。
4. 分组组织：页面结构 / 组件样式 / 交互状态。
5. 保持 HTML、CSS、JS 可读，方便人工调整。

## Accessibility Baseline

- 交互元素使用语义化 HTML。
- 表单控件必须有可见或可关联标签。
- 键盘焦点必须可见。
- 颜色对比度满足常规阅读要求。
- 图标按钮提供 `aria-label` 或可见文本。
- 不得用颜色作为唯一的成功/失败/状态表达方式。

## Review Checklist

- [ ] 页面使用统一的主题令牌。
- [ ] 没有出现未定义的随意颜色和字体。
- [ ] 标题、正文、辅助文字层级清晰。
- [ ] Button / Input / Card / Table 组件风格一致。
- [ ] 已覆盖空 / 加载 / 错误 / 成功状态。
- [ ] 关键操作在桌面和窄屏下都可理解。
- [ ] 键盘焦点、表单标签、图标替代文本存在。

## Notes

- 本 Skill 是模板级规范，**不绑定到具体版本**。
- `templates/prototype-design-system.md` 与 `templates/design-tokens.json` 是同一规范的两份表达；如项目另行提供项目级 design system，应在 baseline 的 ADR 中记录决策。
