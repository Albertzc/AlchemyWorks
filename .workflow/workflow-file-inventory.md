# 工作流必要文件与目录清单

> 本文件是 Alchemy Works 工作流自身的权威目录清单。它描述的是工作流的定义、执行能力和初始化脚手架；不描述某一项目或某一迭代产生的交付物。

## 1. 维护规则

- 修改、新增、移动或删除下表列出的工作流文件或目录时，必须在同一变更中更新本清单。
- 修改工作流行为时，除更新本清单外，还必须同步更新受影响的说明、Skill、模板、测试或 `.gitignore` 规则。
- 新条目必须先明确其用途、是否为必要项，以及是否属于可再生运行状态；可再生状态不得加入本清单的“必要项”。
- 代码评审和工作流自检应将“实现变更与本清单一致”作为检查项。

## 1.1 核心骨架保护

- 上表登记的工作流定义、Skill、模板、治理规则、脚本和测试，在产品开发期间视为只读核心骨架。
- `baseline/`、`iteration/` 和 `workspace/` 下的项目产物不属于核心骨架；`workspace/workflow/` 下的 manifest、traceability、current-state 属于实例项目的可再生项目状态，应由实例项目 Git 管理；实例同步后的 `.aw/` 是本地工作流副本，默认整体忽略。
- `python .workflow/workflow.py verify-workflow` 检查核心骨架是否有未提交修改；产品工作流 CLI 在发现修改时阻断。
- 核心骨架只能通过独立的 workflow-maintenance 变更修改；该变更必须同步更新本清单、说明、测试和同步脚本，并在提交后恢复产品工作流。

## 2. 必要的顶层治理文件

| 路径 | 类型 | 用途 |
|---|---|---|
| `AGENTS.md` | 治理规则 | 定义协作、审批、版本、变更与安全约束。 |
| `README.md` | 工作流框架原理与实例项目使用说明 | 分别说明框架的目录、阶段、治理机制，以及实例项目的初始化、同步、开发和验证方式。 |
| `.gitignore` | 版本控制规则 | 源仓库正常跟踪工作流源文件；同步脚本只向实例项目幂等追加仅忽略 `.aw/` 的区块，不覆盖实例已有规则，也不排除 `workspace/workflow/` 下的实例状态。 |

## 3. 必要的工作流执行与校验目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `.aw/.workflow/`（源仓库为 `.workflow/`） | `workflow.py`、`README.md` | 工作流 CLI（含 baseline 核心流程原型与迭代按需原型门禁、文档变更后的 `refresh` 同步命令、05-review-release 通过后的 `workspace/README.md` 自动生成功能说明、版本归档校验、已归档版本 Context Pack 缓存清理）及其操作说明。实例中的该目录不包含回归测试。 |
| `.aw/.workflow/scripts/`（源仓库为 `.workflow/scripts/`） | `stage_status.py`、`id_registry.py`、`query_id.py`、`check_links.py`、`diff_versions.py` | 供 Agent 和维护者调用的状态、ID、链接与版本比较工具。初始化和同步包装脚本只保留在源仓库。 |
| `.aw/.workflow/dashboard/` | `template.html` | 工作流仪表盘源模板；仪表盘页面按需生成。 |
| `.workflow/tests/`（仅源仓库） | `test_workflow.py` | 工作流 CLI 的维护回归测试；实例初始化时不复制。 |

## 4. 必要的 Agent 能力目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `.aw/.agents/skills/stage-gate/`（源仓库为 `.agents/skills/stage-gate/`） | `SKILL.md` | 阶段开始、交接与审核的门禁政策：阶段顺序、必需产物和人工审批条件。 |
| `.aw/.agents/skills/normalize-requirement/` | `SKILL.md` | 原始需求路由和规范化规则。 |
| `.aw/.agents/skills/manage-iteration/` | `SKILL.md` | 创建、发现和归档迭代的规则；下一版本创建成功后归档已 RC 完成的上一版本。 |
| `.aw/.agents/skills/prototype-design-system/` | `SKILL.md`、`references/` | 原型视觉、交互和设计令牌约束。 |
| `.aw/.agents/skills/design-specification/` | `SKILL.md` | 02-design 的架构、API、数据库字典产物与一致性检查。 |
| `.aw/.agents/skills/planning-validation/` | `SKILL.md` | 03-planning 的 TASK DAG、验收覆盖和验证计划约束。 |
| `.aw/.agents/skills/iterate-implementation/` | `SKILL.md` | 实现阶段的代码、测试和记录约束；v1.0 保留独立 `issue-fixes.md`，v1.1+ 将 Issue 记录合并入 `source-code.md`。 |
| `.aw/.agents/skills/review-release/` | `SKILL.md` | 05-review-release 的审查证据、风险、回滚和发布决策约束。 |
| `.aw/.agents/skills/workflow-governance/` | `SKILL.md` | 工作流 CLI 的唯一操作入口：索引、状态、校验、追溯、Context Pack 和任务结论。 |

## 5. 必要的跨项目模板目录

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `templates/` | `README.md`、`product.md`、`design.md`、`implementation.md` | 初始化时复制到实例根目录，作为可由实例项目维护的默认模板。 |
| `templates/` | `Prototype.html`、`prototype-design-system.md`、`design-tokens.json` | 原型基线、视觉规范与机器可读设计令牌。 |

## 6. 必要的初始化脚手架目录

这些目录属于实例项目，不是 AlchemyWorks 源仓库的工作流产物。`init-instance` 创建目录和说明文件；`sync` 不同步这些目录。

| 路径 | 必需内容 | 用途 |
|---|---|---|
| `baseline/` | `README.md`、`raw-requirement/README.md` | 项目首次立项时的基线、必需核心流程原型和原始需求入口。 |
| `iteration/` | 实例初始化创建 | 版本化交付物及后续原始需求的入口。 |
| `workspace/` | `README.md` | 实例项目真实业务代码、测试、配置和当前系统功能说明；05-review-release 通过后更新其功能说明。 |

## 7. 明确不属于工作流必要项的内容

以下内容由项目使用工作流后输入、产生或缓存，不能被误认为工作流定义的一部分：

| 路径模式 | 分类 | 处理原则 |
|---|---|---|
| `baseline/` 下除说明和原始需求入口外的内容 | 项目基线产物 | 由具体项目维护。 |
| `baseline/raw-requirement/` 下除 `README.md` 外的文件 | 用户原始输入 | 原样保留，不由 Agent 修改。 |
| `iteration/raw-requirement/` 下除 `README.md` 外的文件 | 用户原始输入 | 原样保留，不由 Agent 修改。 |
| `iteration/v{major}.{minor}/`、`iteration/archive/` | 版本化交付物 | 属于具体项目和版本，遵循阶段审批与归档规则。 |
| `workspace/` 下的内容 | 业务实现与实例文档 | 属于被工作流驱动的产品代码、测试、配置和项目自行维护的功能说明。 |
| `workspace/workflow/manifest.yaml`、`traceability.json`、`current-state.json` | 实例项目状态与审计索引 | 不属于工作流源定义；由选定的实例项目根目录生成，属于实例项目版本控制内容，不受 `.gitignore` 管理。 |
| `.aw/` | 同步后的框架文件与本地可再生运行状态 | 可以存在于实例目录供本地运行，但不属于实例项目业务提交；同步脚本默认将其加入实例 `.gitignore`。 |
| `.aw/workflow-version.yaml` | 同步版本元数据 | 由 `init-instance` / `sync` 写入，记录工作流 ref 和 commit；实例项目不提交。 |

## 8. 一致性检查

每次工作流变更完成前，至少确认：

1. 变更涉及的必要路径已在本清单中正确登记。
2. 本清单未将项目输入、版本产物、业务代码或可再生状态误列为工作流必要项。
3. 同步脚本追加的忽略区块只排除 `.aw/`；`templates/`、`baseline/`、`iteration/`、`workspace/` 和 `workspace/workflow/` 保持可提交。
4. 工作流测试通过：`python .workflow/tests/test_workflow.py`。
