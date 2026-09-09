# Baseline

> 0→1 阶段的项目章程产物。**整个项目周期只创建一次**，被所有版本 `iteration/v{major}.{minor}/` 引用。
> 变更通过 ADR（Architecture Decision Record）走决策流程，不进入版本号管理。

## 强制顺序

首次走版本流水线前，**必须**按以下顺序完成并标记 `status: Approved`：

| # | 文件 | 必填 | 说明 |
|---|---|---|---|
| 1 | `01-product-vision.md` | ✅ | 产品愿景：长期目标、用户定位、价值主张 |
| 2 | `02-product-charter.md` | ✅ | 项目章程：范围、边界、成功指标、关键里程碑 |
| 3 | `03-tech-stack-decision.md` | ✅ | 技术选型决议：语言、框架、存储、部署、关键依赖 |
| 4 | `04-glossary.md` | ✅ | 术语表 / 业务概念定义 |
| 5 | `05-core-user-flow-prototype.html` | ✅ | 覆盖核心角色、关键任务闭环和关键状态的可评审交互原型 |
| 6 | `decisions/ADR-*.md` | 可选 | 关键架构与产品决策记录（每次重大变更追加一条） |

`stage-gate` 会在首次创建 `iteration/v1.0/` 之前校验上述 5 个必填 baseline 产物**全部存在**且 frontmatter `status: Approved`，未通过则不允许进入版本流水线。原型可以是低保真线框、可点击流程或结构化 HTML；重点是核心用户旅程、信息架构、关键状态与权限差异可被评审，而非视觉精修。

当 `baseline/` 除正式 baseline 文档外为空时，用户原始需求进入 `baseline/raw-requirement/`，可保留其原始格式。`normalize-requirement` 基于该材料起草 baseline 文档；原始材料本身不需要 frontmatter 或 `Approved`。后续每个迭代的用户原始需求统一保存于 `iteration/raw-requirement/`；`route-requirement` 自动返回该输入对应的版本，Agent 只读原文件。

## 引用约定

- 任何 `iteration/v{N}/*.md` 的 frontmatter 可使用 `baseline_ref:` 字段引用本文档的章节。
- ADR 一旦创建**不删除**，仅追加新 ADR 覆盖或废弃旧决策。
- 任何 baseline 变更必须同步影响所有版本的当前活动产物；变更流程：

```text
Baseline 变更提议
    → ADR 起草（status: proposed）
    → 评审 + 决策（status: accepted / rejected / superseded）
    → 已发布版本中受影响的产物打 deprecated 标记
    → 新一轮版本 v{N+1} 吸收变更
```

## 与 iteration/ 的边界

| 内容 | 归属 | 版本化 |
|---|---|---|
| 愿景 / 章程 / 技术选型 / 术语 / 核心流程原型 / 原始需求 / ADR | `baseline/` | 否（项目级常量） |
| 任何阶段产物（需求、功能规格、按需原型、架构、API、数据库、代码快照、PR、RC 等） | `iteration/v{N}/` | 是（每次迭代 +1） |

## 不放代码

baseline 只装**章程与决策**类文档。代码脚手架一律进 `workspace/`，与 baseline 无关。
