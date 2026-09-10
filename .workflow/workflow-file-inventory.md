# 工作流必要文件与目录清单

> 本文件是 Alchemy Works 工作流自身的权威目录清单。它描述的是工作流的定义、执行能力和初始化脚手架；不描述某一项目或某一迭代产生的交付物。

## 1. 维护规则

- 修改、新增、移动或删除下表列出的工作流文件或目录时，必须在同一变更中更新本清单。
- 修改工作流行为时，除更新本清单外，还必须同步更新受影响的说明、Skill、模板、测试或 `.gitignore` 规则。
- 新条目必须先明确其用途、是否为必要项，以及是否属于可再生运行状态；可再生状态不得加入本清单的“必要项”。
- 代码评审和工作流自检应将“实现变更与本清单一致”作为检查项。

## 1.1 核心骨架保护

- 上表登记的工作流定义、Skill、模板、治理规则、脚本和测试，在产品开发期间视为只读核心骨架。
- `baseline/`、`iteration/` 和 `workspace/` 下的项目产物不属于核心骨架；`.workflow/` 下的 manifest、traceability、current-state、cache、Context Pack、task-runs 和 dashboard/index.html 是可再生运行状态，也不属于核心骨架。
- `python .workflow/workflow.py verify-workflow` 检查核心骨架是否有未提交修改；产品工作流 CLI 在发现修改时阻断。
- 核心骨架只能通过独立的 workflow-maintenance 变更修改；该变更必须同步更新本清单、说明、测试和同步脚本，并在提交后恢复产品工作流。

## 2. 必要的顶层治理文件

| 路径 | 类型 | 用途 |
|---|---|---|
| `AGENTS.md` | 治理规则 | 定义协作、审批、版本、变更与安全约束。 |
| `README.md` | 工作流总览 | 定义目录结构、阶段流程、命令和端到端使用方式。 |
| `.gitignore` | 版本控制规则 | 排除 Python 缓存和工作流可再生运行状态。 |

## 3. 必要的工作流执行与校验目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `.workflow/` | `workflow.py`、`README.md` | 工作流 CLI（含 baseline 核心流程原型与迭代按需原型门禁、文档变更后的 `refresh` 同步命令、已归档版本 Context Pack 缓存清理）及其操作说明。 |
| `.workflow/scripts/` | `stage_status.py`、`id_registry.py`、`query_id.py`、`check_links.py`、`diff_versions.py`、`sync-workflow.ps1` | 供 Agent 和维护者调用的状态、ID、链接与版本比较工具，以及向指定项目同步工作流源定义的受保护脚本。 |
| `.workflow/dashboard/` | `template.html` | 工作流仪表盘的源模板。 |
| `.workflow/tests/` | `test_workflow.py` | 工作流 CLI 的回归测试。 |

## 4. 必要的 Agent 能力目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `.agents/skills/stage-gate/` | `SKILL.md` | 阶段开始、交接与审核的门禁政策：阶段顺序、必需产物和人工审批条件。 |
| `.agents/skills/normalize-requirement/` | `SKILL.md` | 原始需求路由和规范化规则。 |
| `.agents/skills/manage-iteration/` | `SKILL.md` | 创建、发现和归档迭代的规则；下一版本创建成功后归档已 RC 完成的上一版本。 |
| `.agents/skills/prototype-design-system/` | `SKILL.md`、`references/` | 原型视觉、交互和设计令牌约束。 |
| `.agents/skills/design-specification/` | `SKILL.md` | 02-design 的架构、API、数据库字典产物与一致性检查。 |
| `.agents/skills/planning-validation/` | `SKILL.md` | 03-planning 的 TASK DAG、验收覆盖和验证计划约束。 |
| `.agents/skills/iterate-implementation/` | `SKILL.md` | 实现阶段的代码、测试和记录约束；v1.0 保留独立 `issue-fixes.md`，v1.1+ 将 Issue 记录合并入 `source-code.md`。 |
| `.agents/skills/review-release/` | `SKILL.md` | 05-review-release 的审查证据、风险、回滚和发布决策约束。 |
| `.agents/skills/workflow-governance/` | `SKILL.md` | 工作流 CLI 的唯一操作入口：索引、状态、校验、追溯、Context Pack 和任务结论。 |

## 5. 必要的跨项目模板目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `templates/` | `README.md`、`product.md`、`design.md`、`implementation.md` | 跨版本复用的产品、设计和实施文档模板。 |
| `templates/` | `Prototype.html`、`prototype-design-system.md`、`design-tokens.json` | 原型基线、视觉规范与机器可读设计令牌。 |

## 6. 必要的初始化脚手架目录

这些目录的结构和说明文件属于工作流本身；其中后续放入的需求、版本产物和业务代码不属于本清单。

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `baseline/` | `README.md`、`raw-requirement/README.md` | 项目首次立项时的基线、必需核心流程原型和原始需求入口。 |
| `iteration/` | `README.md`、`raw-requirement/README.md` | 版本化交付物及后续原始需求的入口。 |
| `workspace/` | `README.md` | 真实业务代码仓库的承载目录。 |

## 7. 明确不属于工作流必要项的内容

以下内容由项目使用工作流后输入、产生或缓存，不能被误认为工作流定义的一部分：

| 路径模式 | 分类 | 处理原则 |
|---|---|---|
| `baseline/` 下除说明和原始需求入口外的内容 | 项目基线产物 | 由具体项目维护。 |
| `baseline/raw-requirement/` 下除 `README.md` 外的文件 | 用户原始输入 | 原样保留，不由 Agent 修改。 |
| `iteration/raw-requirement/` 下除 `README.md` 外的文件 | 用户原始输入 | 原样保留，不由 Agent 修改。 |
| `iteration/v{major}.{minor}/`、`iteration/archive/` | 版本化交付物 | 属于具体项目和版本，遵循阶段审批与归档规则。 |
| `workspace/` 下除 `README.md` 外的内容 | 业务实现 | 属于被工作流驱动的产品代码、测试和配置。 |
| `.workflow/manifest.yaml`、`traceability.json`、`current-state.json`、`cache/`、`context-packs/`、`task-runs/`、`dashboard/index.html` | 可再生运行状态与审计记录 | 不属于工作流源定义；按命令生成，受 `.gitignore` 管理。 |

## 8. 一致性检查

每次工作流变更完成前，至少确认：

1. 变更涉及的必要路径已在本清单中正确登记。
2. 本清单未将项目输入、版本产物、业务代码或可再生状态误列为工作流必要项。
3. `.gitignore` 仍与“可再生运行状态”分类一致。
4. 工作流测试通过：`python .workflow/tests/test_workflow.py`。
