# Templates

> 跨版本复用的文档与代码模板。**模板本身不带版本号**，被 `iteration/v{major}.{minor}/` 各阶段产物引用。
> 模板修改需谨慎：所有未归档的版本产物可能因模板改动而失同步。

## 清单

| 模板 | 文件 | 合并的旧模板 | 引用方 |
|---|---|---|---|
| 产品阶段（需求 + 功能规格）| `product.md` | `product-requirement.md` + `feature-specification.md` | `01-product/` |
| 设计阶段（架构 + API + DB）| `design.md` | `architecture-design.md` + `api-spec.md` + `database-dictionary.md` | `02-design/` |
| 实施阶段（任务 DAG + 验证 + 源码 + 测试 + Issue）| `implementation.md` | `task-plan-dag.md` + `validation-plan.md` + `source-code.md` + `test-results.md` + `issue-fixes.md` | `03-planning/` + `04-implementation/` |
| HTML 原型骨架 | `Prototype.html` | 原型 HTML 结构与交互基线 | `01-product/` |
| 原型设计系统 | `prototype-design-system.md` | 原型视觉与组件规范 | `01-product/` |
| 设计令牌 | `design-tokens.json` | 设计令牌机器可读值 | `01-product/` |

## 模板修改流程

```text
模板修改提议
    → 评估对未归档版本的影响
    → 同步更新未归档版本的当前产物（或标记 deprecated + 下轮重生成）
    → 在模板顶部记录变更历史
```

## 模板中的示例数据

`Prototype.html` 与 `product.md` 内的 TeamFlow 示例仅用于演示结构、组件和章节组织。**生成 `iteration/v{major}.{minor}/` 产物时必须根据实际需求替换示例数据**，不得原样照搬。

## 版本号说明

模板内所有路径引用使用 `v{major}.{minor}` 占位符（例如 `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md`）。生成实际产物时替换为具体值（如 `v1.0` / `v1.1` / `v2.0`）。

## 模板合并说明

- 三个 .md 模板（`product.md` / `design.md` / `implementation.md`）合并了原本 10 个独立模板，按"产品/设计/实施"三大阶段组织，每个产物从前置模板派生。
- 节省产物层 agent 启动时的 skill 加载 token 与目录查找时间。
- v1.1+ 增量场景下，issue-fixes 合并入 source-code.md §5 已知限制，不再单独成文。