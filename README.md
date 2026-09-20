# Alchemy Works (AW) — 软件开发工作流

> AlchemyWorks/ AW软件工厂：以**双段版本号**为顶层单元的阶段化交付流水线。
> 支持 0→1 项目搭建 + 后续需求迭代；每个版本的所有阶段产物自动与 `v{major}.{minor}` 关联。

---

## 第一部分：工作流框架的工作原理

本部分说明 AlchemyWorks 如何组织需求、版本、阶段产物、自动化能力和治理约束。它面向工作流维护者，也用于理解实例项目中 `.aw/` 工作流副本的运行方式。

### 1. 项目结构与所有权

```
├── baseline/                        # 实例初始化时创建：项目级常量和原始需求
│   ├── 01-product-vision.md
│   ├── 02-product-charter.md
│   ├── 03-tech-stack-decision.md
│   ├── 04-glossary.md
│   ├── decisions/                   # 重大架构决策记录
│   └── raw-requirement/             # baseline 为空时归档用户原始需求
├── iteration/                       # 实例初始化时创建：版本化产物
│   ├── raw-requirement/              # 用户原始需求集中库（只读）
│   └── v{major}.{minor}/            # 双段号；
│       ├── 01-product/
│       ├── 02-design/
│       ├── 03-planning/
│       ├── 04-implementation/
│       └── 05-review-release/
├── workspace/                       # 实例项目初始化时创建：真实代码、配置、测试与实例状态
│   ├── README.md                     # 实例当前系统功能说明（05-review-release 通过后自动生成）
│   └── workflow/                     # 实例项目状态（Git）
│       ├── manifest.yaml             # 产物索引
│       ├── traceability.json         # 稳定 ID 追溯图
│       └── current-state.json        # 恢复检查点
├── templates/                       # 初始化时复制的默认模板，实例可维护
└── .aw/                             # 实例项目中的工作流执行目录（整体忽略）
    ├── README.md                    # AlchemyWorks 工作流总览
    ├── AGENTS.md                    # 完整工作流协作规则
    ├── .agents/skills/              # 阶段化 AI Agent Skill
    └── .workflow/                  # CLI、脚本与本地运行时
        ├── workflow.py              # 主 CLI（纯 stdlib）
        ├── workflow-file-inventory.md # 工作流必要文件与目录权威清单
        ├── cache/                   # 按需生成的 context-pack 缓存
        ├── context-packs/           # 按需生成的 TASK 上下文包
        ├── task-runs/               # 按需生成的 TASK 记录
        ├── dashboard/               # 静态 HTML 仪表盘
        └── scripts/                 # 实例需要的辅助脚本
```

#### 1.1 工作流源定义与实例项目边界

本仓库既是工作流源仓库，也是一个可运行的工作流目录样例。阅读或维护时，按下面的归属判断文件是否属于工作流本身：

| 内容 | 归属 | 生成/维护方式 | 实例 Git 是否提交 |
|---|---|---|---|
| `AGENTS.md`、根 `README.md`、`.gitignore` | 工作流仓库的治理与说明；实例的 `README.md`、`.gitignore` 由实例自己拥有 | 源仓库手工维护；`init-instance` 将完整规则同时写入实例根 `AGENTS.md` 和 `.aw/AGENTS.md` | 源仓库提交；实例根 `AGENTS.md` 可按项目需要调整 |
| `.aw/.workflow/workflow.py`、`.aw/.workflow/scripts/` | 实例中的工作流定义、执行器和辅助脚本 | 源仓库维护；`sync` 映射到 `.aw/` | 实例默认忽略同步副本 |
| `.workflow/tests/` | 源仓库工作流回归测试 | 仅源仓库维护；实例初始化不复制 | 不进入实例 |
| `.aw/.agents/skills/` | 实例中的工作流能力 | 源仓库维护；`sync` 映射到 `.aw/` | 实例默认忽略同步副本 |
| `templates/` | 实例项目可维护的默认模板 | `init-instance` 首次复制；后续同步不覆盖实例修改 | 提交 |
| `baseline/` | 实例项目的 baseline 产物和用户原始输入 | `init-instance` 创建；`normalize-requirement` 起草，人工审核后进入门禁 | 提交 |
| `iteration/raw-requirement/` | 实例项目的用户原始需求 | `init-instance` 创建；用户提供，`route-requirement` 返回目标版本；Agent 只读 | 提交 |
| `iteration/v{major}.{minor}/`、`iteration/archive/` | 实例项目的版本产物和归档快照 | `init-version` 创建/归档，阶段 Skill 产出文档 | 提交 |
| `workspace/`（含 `workspace/workflow/`） | 实例项目的代码、配置、测试、功能说明和可再生追溯状态 | 初始化时生成 `workspace/README.md` 目录说明；04 阶段写入业务代码；`index`/`state`/`refresh` 生成状态；05 阶段更新功能说明 | 提交 |
| `.aw/workflow-version.yaml` | 实例本地工作流源版本信息 | `init-instance` / `sync` 写入；实例 Git 忽略 | 不提交 |

一句话判断：工作流负责“规则、工具、能力、模板和脚手架说明”；实例项目负责“需求输入、版本产物、业务实现、测试、功能说明和工作流生成的项目状态”。同步副本可以在实例目录中运行，但不属于实例业务提交。

#### 1.2 目录生成逻辑

实例目录应通过统一入口创建，不要手工复制目录或直接创建版本号目录：

```powershell
# 新建实例：创建 Git 仓库、实例 README、templates/、三类业务目录，随后同步工作流副本
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"

# 不传名称时，使用目标目录最后一级名称作为实例名称
python .workflow/workflow.py init-instance --directory "E:\path\to\product-a"

# 只预览，不创建目录
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a" --dry-run

# 已有实例：同步工作流源定义；不会覆盖实例 README、.gitignore、baseline/产物、iteration/产物或 workspace/内容
python .workflow/workflow.py sync --directory "E:\path\to\product-a"
```

`init-instance` 的生成顺序是：初始化实例 Git → 创建 `baseline/`、`iteration/`、`workspace/` 和默认 `templates/` 及其目录说明 README → 将完整工作流规则同时写入实例根 `AGENTS.md` 和 `.aw/AGENTS.md` → 将工作流副本同步到 `.aw/`，写入 `.aw/workflow-version.yaml`，并追加只忽略 `.aw/` 的受管 `.gitignore` 区块。实例根 `AGENTS.md` 和 `templates/` 是初始化开发的顶层可维护内容；`.aw/AGENTS.md` 是同步的工作流副本。`workspace/README.md` 在 05-review-release 通过后更新为当前系统功能说明。`init` 只用于当前工作流仓库内创建 intake 目录；`init-version` 只能在实例 baseline 门禁通过后创建版本骨架。

---

### 2. 版本号规范

格式：`v{major}.{minor}`（双段号）。

| 规则 | 含义 |
|---|---|
| **首版** | `v1.0`（与首次 `iteration/` 目录同号）|
| **小迭代** | `v{major}.{minor+1}`（每次迭代**严格 +1**，不允许跳号如 `v1.2` → `v1.4`）|
| **重大变更** | `v{major+1}.0`（架构重置、新项目、技术栈变更）|
| **目录命名** | `iteration/v{major}.{minor}/` |
| **文件前缀** | `v{major}.{minor}-*.md` / `.html` |
| **归档** | 下一连续版本创建成功后，将已 RC 完成且已自动生成 `workspace/README.md` 的上一版迁移至 `iteration/archive/v{major}.{minor}/` |

详细规则见 `AGENTS.md §17 Versioning and Archive Rules`。

初始化命令：

```powershell
python .workflow/workflow.py init          # 创建项目级目录，不创建版本
python .workflow/workflow.py init-version  # baseline 门禁通过后创建下一个版本
```

---

### 3. 阶段流水线（原始需求输入 + 5 个交付阶段）

```text
用户提供的原始需求（格式不限）
        ↓ route-requirement + normalize-requirement
baseline/ 为空 → baseline/raw-requirement/ → 起草 baseline → validate 00-baseline
baseline/ 已初始化 → iteration/raw-requirement/（route-requirement 返回目标版本）→ 起草 01-product
baseline/
        05-core-user-flow-prototype.html            # 必需：核心用户旅程交互基线
iteration/v{major}.{minor}/01-product/
        v{major}.{minor}-requirement.md            # 需求 + 功能规格（合并）
        v{major}.{minor}-prototype.html            # 仅 `prototype_required: true` 时的可交互 UI 原型
        v{major}.{minor}-iteration-changelog.md     # 仅 RC 后产出（封档说明）
        ↓ validate 01-product
iteration/v{major}.{minor}/02-design/
        v{major}.{minor}-architecture-design.md
        v{major}.{minor}-api-spec.md
        v{major}.{minor}-database-dictionary.md
        ↓ validate 02-design
iteration/v{major}.{minor}/03-planning/
        v{major}.{minor}-task-plan-dag.md
        v{major}.{minor}-validation-plan.md
        ↓ validate 03-planning
iteration/v{major}.{minor}/04-implementation/
        v{major}.{minor}-source-code.md             # 实施主记录（含 ISSUE 列表）
        v{major}.{minor}-test-results.md
        ↓ validate 04-implementation
iteration/v{major}.{minor}/05-review-release/
        v{major}.{minor}-review-release.md           # 评审、合并、发布决定与 release notes
        ↓ validate 05-review-release
        ↓ 先自动生成 workspace/README.md，再创建下一版本
iteration/archive/v{major}.{minor}/    ← 旧版整体快照（只读）
```

**关键约定**：

- 每份正式阶段产物需有 `status: Approved` frontmatter 才算"通过"（否则 gate 拒绝）；原始需求是来源材料，不要求统一格式或审批状态。`iteration/raw-requirement/` 除 README 外仅保存用户原文件，Agent 只读，不得修改、重命名或删除；`route-requirement` 输出其对应版本。
- HTML 原型还必须保留审核 frontmatter：`review_decision`、`reviewer`、`reviewed_at`、`review_notes`；只有 `status: Approved` 且 `review_decision: approved`、审核人/时间/结论齐全时，原型门禁才会通过。
- `Approved` 状态下若含占位词（`TODO` / `TBD` / `XXX` / `[待确认]` / `[未提供]` / `占位`），validate 视为 unresolved blocker
- 上游产物必须 Approved 才能作为下游阶段的正式输入
- 05-review-release 通过后，CLI 根据当前版本 requirement 自动生成 `workspace/README.md` 的 `## 当前系统功能说明`，并更新 `<!-- workflow:workspace-readme-version: v{major}.{minor} -->`；`init-version` 会在归档前再次校验，失败时不移动旧版本。
- 根目录 `README.md` 只描述共享工作流框架并校验当前 Skill / 脚本；实例版本的功能说明和版本刷新标记只维护在 `workspace/README.md`，不要求根 README 逐版本更新。
- Agent 只能创建或更新 `status: draft` / `status: In Review` 的产物，**不得**写入或修改 `status: Approved`。每个阶段完成时，Agent 必须列出待人工审核的全部必需产物及验证证据；人类手动审核并将各产物改为 `Approved` 后，才可运行该阶段的 `validate` 并开始下一阶段。

每阶段的交接闭环：`Agent 起草产物 → Agent 列出待审产物与验证证据 → 人类手动设为 Approved → validate --stage <当前阶段> 通过 → 开始下一阶段`。

---

### 4. AI Agent Skill 体系（9 个）

| Skill | 触发场景 | 输出 |
|---|---|---|
| `stage-gate` | 开始、交接或审核任一阶段 | 门禁政策：阶段顺序、必需产物与人工审批条件 |
| `normalize-requirement` | 任何新需求文档产出 | `v{major}.{minor}-requirement.md` + change_set |
| `prototype-design-system` | 01 阶段 UI 原型设计 | 视觉与组件规范参考 |
| `design-specification` | 02 阶段架构、API、数据库设计 | 三类设计产物与一致性检查 |
| `planning-validation` | 03 阶段任务与验证规划 | TASK DAG + AC/测试覆盖 |
| `iterate-implementation` | 04 阶段 TASK 实施 | 源码 + 测试 + ISSUE |
| `review-release` | 05 阶段评审与发布准备 | 评审证据 + 风险/回滚 + 发布建议 |
| `manage-iteration` | 创建 / 归档版本 | `iteration/v{N}/` + `archive/v{N}/` |
| `workflow-governance` | 任意阶段 | 唯一 CLI 操作入口：校验 + 索引 + 追溯 + Context Pack |

所有 Skill 位于 `.agents/skills/<name>/SKILL.md`，触发条件命中时自动加载。

### 原型生成工具路由

进入 `01-product` 生成或修改 HTML 原型前，先执行原型预览工具检查：

- 仅当 baseline 核心流程原型或某版本 `prototype_required: true` 时：Codex 必须使用 `visualize` 插件进行交互预览或关键交互检查，再生成项目内的 HTML 原型。预览插件不可用时暂停并引导用户安装/启用。
- 其他 Agent：在需要生成原型时，先搜索功能等价的交互可视化或原型预览插件，记录替代工具后再生成；找不到替代工具时暂停并请求用户处理。
- 工具预览是原型生成的前置验证，不替代正式阶段产物；阶段记录必须写明实际使用的工具、检查结果和阻断原因（如有）。

---

### 5. 模板体系（3 个跨版本模板）

位于 `templates/`：

| 模板 | 文件 | 用途 | 派生产物 |
|---|---|---|---|
| **product** | `product.md` | 需求 + 功能规格（合并）| `v{N}-requirement.md`（FS 段落作为 FR 子项内嵌） |
| **design** | `design.md` | 架构 + API + DB（合并）| `v{N}-architecture-design.md` + `api-spec.md` + `database-dictionary.md` |
| **implementation** | `implementation.md` | 任务 DAG + 验证 + 源码 + 测试 + ISSUE（合并）| `v{N}-task-plan-dag.md` + `validation-plan.md` + `source-code.md` + `test-results.md` |

辅助文件：`Prototype.html`（UI 原型基线）+ `prototype-design-system.md`（视觉规范）+ `design-tokens.json`（设计令牌）。

模板**不带版本号**；生成实际产物时把 `v{major}.{minor}` 占位符替换为具体值。

---

### 6. 工作流 CLI（`.workflow/workflow.py`，纯 Python 标准库）

> §3 是阶段产物清单，本节是**端到端流程图**——把 baseline gate、5 个 stage gate、横切的 index/dashboard/ID 注册，以及"未通过 → 修产物"的回路一次性画出来。

```mermaid
flowchart TD
    Start([用户原始需求]) --> Intake{baseline/ 除 README 外为空?}
    Intake -- 是 --> Bfix[归档到 baseline/raw-requirement<br/>起草 baseline 文档]
    Bfix --> B0[00-baseline 全部 Approved?]
    B0 -- 否 --> Bfix
    Intake -- 否 --> R0["按 manifest 版本路由<br/>iteration/raw-requirement/（只读）"]
    B0 -- 是 --> R0
    R0 --> S1

    S1["01-product<br/>requirement.md (含FS)<br/>prototype_required 决策<br/>prototype.html（仅 true）"]
    S2["02-design<br/>architecture-design.md<br/>api-spec.md<br/>database-dictionary.md"]
    S3["03-planning<br/>task-plan-dag.md<br/>validation-plan.md"]
    S4["04-implementation<br/>source-code.md (ISSUE 列表)<br/>test-results.md<br/>每 TASK: context → 实施 → task-finished"]
    S5["05-review-release<br/>review-release.md<br/>评审 / 合并 / 发布"]
    Arch([创建下一版本后封档上一版<br/>archive/vN/ + iteration-changelog.md])

    S1 -- 人工审核 → Approved<br/>validate 01 --> S2
    S2 -- 人工审核 → Approved<br/>validate 02 --> S3
    S3 -- 人工审核 → Approved<br/>validate 03 --> S4
    S4 -- 人工审核 → Approved<br/>validate 04 --> S5
    S5 -- 人工审核 → Approved<br/>生成 changelog、保持活动 --> Arch

    subgraph X[横切动作 - 不构成线性阶段]
        X1["index → manifest.yaml<br/>+ traceability.json<br/>"]
        X2["dashboard →<br/>dashboard/index.html"]
        X3["LLM 脚本: stage_status<br/>id_registry / query_id<br/>check_links / diff_versions"]
    end
    S1 -.改产物后.-> X1
    S4 -.TASK 完成.-> X1
    S5 -.改产物后.-> X1
    X1 -.-> X2

    S1 -.validate 拒绝.-> R1[修产物 / 人工审核] --> S1
    S2 -.validate 拒绝.-> R2[修产物] --> S2
    S3 -.validate 拒绝.-> R3[修产物] --> S3
    S4 -.validate 拒绝.-> R4[修产物 / 重跑测试] --> S4
    S5 -.validate 拒绝.-> R5[修复评审 / 发布产物] --> S5

    classDef gate fill:#fff7e6,stroke:#d48806,stroke-width:1px;
    class S1,S2,S3,S4,S5 gate;
```

```bash
# 索引与门禁
python .workflow/workflow.py index      --iteration v1.0       # 生成 manifest + traceability + 缓存
python .workflow/workflow.py --project-root 'E:\path\to\instance-project' index --iteration v1.0 # 从框架仓库操作实例项目
python .workflow/workflow.py state      --iteration v1.0 --refresh # 刷新并显示恢复工作所需的最小状态
python .workflow/workflow.py refresh    --iteration v1.0 --stage 02-design # 文档变更后：索引、刷新状态并运行门禁
python .workflow/workflow.py resume     --json                   # 新会话首选：只输出最小恢复状态
python .workflow/workflow.py preflight  --iteration v1.0 --json  # 本地门禁、DAG、覆盖率检查
python .workflow/workflow.py validate   --iteration v1.0       # 校验全部 stage
python .workflow/workflow.py validate   --iteration v1.0 --stage 02-design   # 单 stage 校验

# 任务管理
python .workflow/workflow.py context    --iteration v1.0 --task TASK-API-010   # 生成/复用 TASK Context Pack
python .workflow/workflow.py context    --iteration v1.0 --task TASK-API-010 --compact --max-chars 12000
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-API-010 --result succeeded
# ↑ 默认仅追加 task-runs JSON，不触发 index/dashboard
#   --refresh-index      当任务改变了产物状态时加上
#   --refresh-dashboard  当要立即刷新仪表盘时加上

# 已归档版本的可再生 Context Pack / 缓存清理（默认预览；不删除 TASK 审计记录）
python .workflow/workflow.py cleanup --iteration v1.0
python .workflow/workflow.py cleanup --iteration v1.0 --execute

# 仪表盘
python .workflow/workflow.py dashboard  --iteration v1.0       # 渲染静态 HTML 仪表盘
python .workflow/workflow.py verify-workflow                 # 检查工作流核心文件是否被修改
```

**子命令表**：

| 子命令 | 功能 | 写入文件 |
|---|---|---|
| `index` | 全产物索引 + traceability 图 + 恢复检查点 | `workspace/workflow/manifest.yaml` / `traceability.json` / `current-state.json` |
| `state` | 刷新或读取当前阶段、阻塞项、下一动作和 Context Pack | `workspace/workflow/current-state.json` |
| `refresh` | 文档变更后依次执行 `index`、`state --refresh` 和 `validate`；首个失败即停止 | 同 `index` / `state`，并输出门禁结果 |
| `resume` | 输出新会话所需的最小恢复 JSON | stdout |
| `preflight` | 本地执行门禁、TASK DAG 和 AC/TASK 覆盖率检查 | stdout / JSON |
| `review-pack` | 生成人工审核证据摘要，不修改审批状态 | stdout / JSON |
| `validate` | stage gate 检查（无产物修改）| stdout + exit code |
| `context` | 提取 TASK 相关章节，去重、限长并按 hash 复用 | `context-packs/<ver>-<task>.md` |
| `cleanup` | 预览或清理已归档版本的 Context Pack 与缓存键；`--execute` 才删除 | `context-packs/` + `cache/context-packs.json` |
| `task-finished` | 写入最新 TASK 结论并保留历史记录 | `task-runs/<ver>-<task>.json` + `task-runs/history/*.json` |
| `dashboard` | 渲染静态 HTML 仪表盘 | `dashboard/index.html` |

所有命令子命令接受 `--iteration`（默认从 `iteration/` 推断最大值；不存在则返回 `v1.0`）。

从工作流框架仓库操作实例项目时，将 `--project-root '<instance-project-root>'` 放在子命令之前。框架代码、Skills 和默认模板从框架根目录读取；实例模板位于实例根目录 `templates/`。产品文档和实例状态写入实例项目的 `workspace/workflow/`，本地运行数据写入实例项目的 `.aw/.workflow/`。同步到实例项目后，可以使用 `.aw/.workflow/workflow.py`，省略 `--project-root`。

产品开发期间，工作流核心文件默认为只读。源仓库中的 `AGENTS.md`、工作流说明、`.workflow/workflow.py`、`.workflow/scripts/`、`.workflow/tests/`、`.agents/skills/` 和源仓库 `templates/`，以及实例中的对应 `.aw/` 执行路径，被修改且未提交时，工作流 CLI 会阻断；实例根 `AGENTS.md` 和 `templates/` 属于项目内容，可由实例维护。通过 `verify-workflow` 检查后，必须在独立的工作流维护变更中完成提交。`baseline/`、`iteration/`、`workspace/` 以及 `workspace/workflow/manifest.yaml`、`workspace/workflow/traceability.json`、`workspace/workflow/current-state.json` 属于实例项目内容，不受核心骨架保护；实例项目中的 `.aw/` 是同步框架和本地运行目录，默认不纳入 Git。

工作流生成的 `generated_at`、`checked_at`、`recorded_at` 和 Context Pack 时间均使用执行 Codex 客户端的本地时区，并保留 ISO 8601 偏移量。

---

### 7. LLM 自动化脚本（`.workflow/scripts/`）

5 个本地脚本，让 LLM 不必亲自 grep / read 多份文档：

| 脚本 | 命令示例 | 替代的 LLM 行为 |
|---|---|---|
| `stage_status.py` | `--iteration v1.0` | "v1.0 现在到哪个阶段？能进下一阶段吗？" |
| `id_registry.py` | `--iteration v1.0 --prefix FR` | "下一个可用 FR 是多少？" |
| `query_id.py` | `--id FR-005 --iteration v1.0` | "FR-005 出现在哪些文件？" |
| `check_links.py` | `--iteration v1.0` | "v1.0 文档里有断链吗？" |
| `diff_versions.py` | `--from v1.0 --to v1.1` | "v1.0 → v1.1 改了哪些 ID？哪些 deprecated？" |

所有脚本纯 stdlib，可独立运行：

```bash
python .workflow/scripts/stage_status.py --iteration v1.0
python .workflow/scripts/id_registry.py --iteration v1.0
python .workflow/scripts/query_id.py --id TASK-API-010 --iteration v1.0
python .workflow/scripts/check_links.py --iteration v1.0
```

### 8. 稳定 ID 与追溯

通过 9 类前缀保证跨版本稳定：

| 前缀 | 含义 | 例 |
|---|---|---|
| `FR-NNN` | 功能需求 | `FR-001` |
| `BR-NNN` | 业务规则 | `BR-005` |
| `NFR-NNN` | 非功能需求 | `NFR-030` |
| `FS-NNN` | 功能规格（v1.0+ 并入 requirement 作为 FR 子项；不再独立成文）| `FS-001` |
| `API-NNN-NNN` | API 端点 | `API-PROJ-001` |
| `TBL-NNN-NNN` | 数据表 | `TBL-USER-001` |
| `TASK-NNN-NNN` | 实施任务 | `TASK-API-010` |
| `AC-NNN` | 验收标准 | `AC-007` |
| `ISSUE-NNN` | Issue 记录 | `ISSUE-014` |

追溯自动从 markdown 中提取并存入 `workspace/workflow/traceability.json`（`index` 子命令产出）。

---

### 9. 阶段产物精简（当前状态）

| 阶段 | 产物 |
|---|---|
| 01-product | `requirement.md`（FS-XXX 作为 FR-XXX 子项内嵌，含 `prototype_required` 决策）；`prototype.html` 仅在该决策为 `true` 时必需 |
| 02-design | `architecture-design.md`、`api-spec.md`、`database-dictionary.md` |
| 03-planning | `task-plan-dag.md`、`validation-plan.md` |
| 04-implementation | `source-code.md`（含 ISSUE 列表）、`test-results.md` |
| 05-review-release | `review-release.md`（评审、合并、发布决定、release notes） |

---

## 第二部分：实例项目使用说明

本部分面向实例项目的开发者，说明如何初始化、同步和使用工作流。实例项目的业务内容位于 `baseline/`、`iteration/`、`workspace/` 和根目录 `templates/`；同步到 `.aw/` 的框架副本仅作为本地执行环境，不属于实例业务提交。

### 1. 初始化与同步工作流

实例初始化和工作流同步的唯一实现入口是 Python CLI：

```text
python .workflow/workflow.py init-instance --name "Product A" --directory "E:\path\to\product-a"
python .workflow/workflow.py sync --directory "E:\path\to\target-project"
```

使用 `--dry-run` 预览操作，只有确认目标项目存在有意修改时才使用 `--allow-dirty`。下方 PowerShell 脚本仅作为 Windows 兼容包装器。

从本仓库根目录执行以下命令，可以按实例名称和目录创建新的实例项目：

```powershell
.\.workflow\scripts\init-instance.ps1 -InstanceName 'Product A' -TargetRoot 'E:\path\to\product-a'
# 省略 -InstanceName 时使用目标目录名称
.\.workflow\scripts\init-instance.ps1 -TargetRoot 'E:\path\to\product-a'
```

初始化命令会创建实例 Git 仓库、实例 `README.md`、`AGENTS.md`、`templates/`、`baseline/`、`iteration/` 和 `workspace/`，然后同步工作流定义。可使用 `--workflow-version <tag|branch|commit>` 指定工作流版本；预览使用 PowerShell 的 `-WhatIf`。

已有实例项目则使用以下命令同步工作流源定义：

```powershell
.\workflow\scripts\sync-workflow.ps1 -TargetRoot 'E:\path\to\target-project'
```

该脚本仅同步 `workflow-file-inventory.md` 规定的共享规则、CLI 和 Skills 到实例 `.aw/`，并向根目录 `templates/` 补充缺失的默认模板；不会覆盖实例项目的 `README.md`、根 `AGENTS.md`、`templates/` 或 `.gitignore`，也不会复制项目的 `baseline/`、`iteration/`、`workspace/` 内容或运行状态。同步后会在实例 `.gitignore` 中幂等维护仅包含 `.aw/` 的工作流忽略区块，`workspace/workflow/` 和 `templates/` 状态仍可提交。目标项目可以有不相关的修改；只有同步路径发生重叠时默认拒绝执行，确认需要覆盖时才使用 `-AllowDirtyTarget`，预览可使用 `-WhatIf`。

### 2. 常用工作流

#### 2.1 启动一个新版本（v1.0）

```
1. 用户提供原始需求；`route-requirement` 发现 baseline 为空并返回 `baseline/raw-requirement/`
2. 归档原始材料，触发 normalize-requirement 起草 4 份 baseline 文档和核心流程原型
3. 人工审核 baseline → `validate --stage 00-baseline`
4. 创建 `iteration/v1.0/` 骨架；`route-requirement` 返回该原始需求的目标版本，原文件保留在 `iteration/raw-requirement/`
5. 触发 normalize-requirement → 生成 v1.0-requirement.md
6. 人工审核 → status: Approved
7. 进入 02-design / 03-planning / 04-implementation / 05-review-release
8. RC 完成 → 自动生成 `workspace/README.md`，写入 v1.0 功能并更新版本标记；生成 v1.0-iteration-changelog.md；v1.0 保持活动状态，直至 v1.1 创建成功后归档
```

#### 2.2 启动 v1.1+ 增量迭代

```
1. 用户提供原始需求；`route-requirement` 从 manifest.yaml（缺失时目录发现）解析目标版本
2. 确认上一版本已通过 05-review-release 且已自动生成 `workspace/README.md`；创建目标版本骨架后，CLI 自动归档上一版本；将原始材料原样保存到 `iteration/raw-requirement/`，并以 `route-requirement` 返回的目标版本归一化
3. 触发 normalize-requirement → 读项目基线、原始需求、上一版 requirement 与 changelog
4. 输出对应版本 requirement.md（含 change_set: added / modified / deprecated）
5. 人工审核 → status: Approved
6. 触发 iterate-implementation skill（按 TASK 列表实施）
7. 每个 TASK 完成 → python .workflow/workflow.py task-finished --result succeeded
8. RC 完成 → 自动生成 `workspace/README.md`，写入本版本功能并更新版本标记；生成本版本 changelog 并保持活动状态；下一个版本创建成功时归档本版本
```

#### 2.3 实施单个 TASK

```bash
# 1. 启动前：本地生成最小恢复状态
python .workflow/workflow.py resume --json

# 2. 启动任务前：本地 preflight + 校验 gate + 生成紧凑 Context Pack
python .workflow/workflow.py index    --iteration v1.0
python .workflow/workflow.py preflight --iteration v1.0 --json
python .workflow/workflow.py validate --iteration v1.0 --stage 04-implementation
python .workflow/workflow.py context  --iteration v1.0 --task TASK-API-010 --compact --max-chars 12000

# 2. 读 .workflow/context-packs/v1.0-TASK-API-010.md（任务片段，非整篇）

# 3. 实际写代码到 workspace/

# 4. 完成：轻量记录（默认）
#    task-finished 要求 Context Pack 已存在，否则拒绝写入完成记录
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-API-010 --result succeeded --auto-refresh
# ↑ 不重跑 index/dashboard；高频操作零开销
# ↓ 偶尔才需要：
python .workflow/workflow.py task-finished ... --refresh-dashboard

# 5. 查看阶段进度
python .workflow/scripts/stage_status.py --iteration v1.0
```

#### 2.4 跨版本引用查询

```bash
# "FR-005 出现在 v1.0 的哪里？"
python .workflow/scripts/query_id.py --id FR-005 --iteration v1.0
# 输出：FR-005 — found in 2 artifact(s)
#   - iteration/v1.0/01-product/v1.0-requirement.md  (FS 作为 FR 子项内嵌)
```

#### 2.5 跨版本 ID diff

```bash
# "v1.0 → v1.1 改了哪些 ID？哪些 FR 被废弃了？"
python .workflow/scripts/diff_versions.py --from v1.0 --to v1.1
# 输出：4 个 bucket: added / modified / removed / deprecated
# - 当有 deprecated ID 时脚本返回 exit 2（便于 CI gate 拦截）
# - --json 输出完整结构（含每个 modified ID 的 added_in / removed_from）
```

---

### 3. 验证检查清单

```bash
# 1. 验证当前迭代
python .workflow/workflow.py validate --iteration v1.0

# 2. 看阶段进度
python .workflow/scripts/stage_status.py --iteration v1.0

# 3. 跑单测
python -m unittest discover -s .workflow/tests -p test_workflow.py

# 4. 检查断链
python .workflow/scripts/check_links.py --iteration v1.0
```

期望输出：
- `validate` → `result: PASS (0 errors, 0 warnings)`
- `stage_status` → 所有 ✅ `approved` + `Overall gate: passed`
- `unittest` → `Ran 5 tests in ... OK`
- `check_links` → `✅ all local links resolve` 或仅 warning

---

### 4. AGENTS.md 角色

`AGENTS.md` 是项目级 AI Agent 与开发者协作规则（含 §17 版本化规则、source-of-truth 优先级、TDD 标准、commit 约定等）。它是**唯一**对所有 Skill / Agent 生效的全局规则文件。详见 `AGENTS.md`。

---

### 5. License

MIT

---

### 6. ⚠️ 免责声明 / Disclaimer

> 本项目当前处于 **实验阶段**，仅供 AI 工作流自动化的学习与研究使用。
>
> **不建议、亦不应用于任何生产环境。** 项目中涉及的脚本、模板、生成的代码与文档，均按"现状"提供，不附带任何形式的明示或暗示保证。
>
> 本项目（或其衍生作品）的使用、复制、修改、分发等行为所**直接、间接、附带或偶然产生**的任何损失（包括但不限于数据丢失、业务中断、服务不可用、经济损失、知识产权纠纷等），**作者与贡献者均不承担任何责任**。
>
> 使用者需自行评估其适用性，并对其使用本项目所产生的全部后果承担完全责任。
