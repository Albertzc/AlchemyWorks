# Nyxigen

> 倪克斯AI生成：以**双段版本号**为顶层单元的阶段化交付流水线。
> 支持 0→1 项目搭建 + 后续需求迭代；每个版本的所有阶段产物自动与 `v{major}.{minor}` 关联。

---

## 1. 项目结构

```
├── baseline/                        # 项目级常量（章程、愿景、术语、技术选型、ADR）
│   ├── 01-product-vision.md
│   ├── 02-product-charter.md
│   ├── 03-tech-stack-decision.md
│   ├── 04-glossary.md
│   ├── decisions/                   # 重大架构决策记录
│   └── raw-requirement/             # 原始需求来源（只读）
├── iteration/                       # 版本化产物（每个迭代一个目录）
│   └── v{major}.{minor}/            # 双段号；简写 v{N} = v{N}.0
│       ├── 01-product/
│       ├── 02-design/
│       ├── 03-planning/
│       ├── 04-implementation/
│       ├── 05-pull-request/
│       └── 06-rc-review-release/
├── templates/                       # 跨版本复用的文档与代码模板（已合并为 3 个）
├── workspace/                       # 真实代码仓库（Git；后端 + 前端）
├── .agents/skills/                  # 阶段化 AI Agent Skill（6 个）
└── .workflow/                       # 工作流 CLI + 状态 + 缓存
    ├── workflow.py                  # 主 CLI（纯 stdlib）
    ├── manifest.yaml                # 产物索引（自动）
    ├── traceability.json            # 稳定 ID 追溯图（自动）
    ├── cache/                       # hash 缓存
    ├── context-packs/               # TASK-scoped 上下文包
    ├── task-runs/                   # TASK 结论 JSON
    ├── dashboard/                   # 静态 HTML 仪表盘
    └── scripts/                     # 4 个 LLM 自动化脚本
```

---

## 2. 版本号规范

格式：`v{major}.{minor}`（双段号）。

| 规则 | 含义 |
|---|---|
| **首版** | `v1.0`（与首次 `iteration/` 目录同号）|
| **小迭代** | `v{major}.{minor+1}`（每次迭代**严格 +1**，不允许跳号如 `v1.2` → `v1.4`）|
| **重大变更** | `v{major+1}.0`（架构重置、新项目、技术栈变更）|
| **向后兼容** | `v{N}` 简写 = `v{N}.0`（CLI 与文件系统均接受）|
| **目录命名** | `iteration/v{major}.{minor}/` |
| **文件前缀** | `v{major}.{minor}-*.md` / `.html` |
| **归档** | RC 完成后旧版整体迁移至 `iteration/archive/v{major}.{minor}/` |

详细规则见 `AGENTS.md §17 Versioning and Archive Rules`。

---

## 3. 阶段流水线（每迭代 6 阶段）

```text
baseline/  status: Approved
        ↓ baseline-gate 校验
iteration/v{major}.{minor}/01-product/
        v{major}.{minor}-requirement.md            # 需求 + 功能规格（合并）
        v{major}.{minor}-prototype.html            # 可交互 UI 原型（人类使用）
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
iteration/v{major}.{minor}/05-pull-request/
        v{major}.{minor}-pull-request.md            # PR 摘要
        ↓ validate 05-pull-request
iteration/v{major}.{minor}/06-rc-review-release/
        v{major}.{minor}-release-notes.md            # 合并自原 3 份 RC 文档
        ↓ validate 06-rc-review-release
        ↓
iteration/archive/v{major}.{minor}/    ← 旧版整体快照（只读）
```

**关键约定**：

- 每份产物需有 `status: Approved` frontmatter 才算"通过"（否则 gate 拒绝）
- `Approved` 状态下若含占位词（`TODO` / `TBD` / `XXX` / `[待确认]` / `[未提供]` / `占位`），validate 视为 unresolved blocker
- 上游产物必须 Approved 才能作为下游阶段的正式输入

---

## 4. AI Agent Skill 体系（6 个）

| Skill | 触发场景 | 输出 |
|---|---|---|
| `baseline-gate` | 创建第一个 `iteration/` 之前 | 校验 baseline/ 完整性 + Approved |
| `normalize-requirement` | 任何新需求文档产出 | `v{major}.{minor}-requirement.md` + change_set |
| `prototype-design-system` | 01 阶段 UI 原型设计 | 视觉与组件规范参考 |
| `iterate-implementation` | 04 阶段 TASK 实施 | 源码 + 测试 + ISSUE |
| `manage-iteration` | 创建 / 归档版本 | `iteration/v{N}/` + `archive/v{N}/` |
| `workflow-governance` | 任意阶段 | 门禁 + 索引 + 追溯 + Context Pack |

所有 Skill 位于 `.agents/skills/<name>/SKILL.md`，触发条件命中时自动加载。

---

## 5. 模板体系（3 个跨版本模板）

位于 `templates/`：

| 模板 | 文件 | 用途 | 派生产物 |
|---|---|---|---|
| **product** | `product.md` | 需求 + 功能规格（合并）| `v{N}-requirement.md`（FS 段落作为 FR 子项内嵌） |
| **design** | `design.md` | 架构 + API + DB（合并）| `v{N}-architecture-design.md` + `api-spec.md` + `database-dictionary.md` |
| **implementation** | `implementation.md` | 任务 DAG + 验证 + 源码 + 测试 + ISSUE（合并）| `v{N}-task-plan-dag.md` + `validation-plan.md` + `source-code.md` + `test-results.md` |

辅助文件：`Prototype.html`（UI 原型基线）+ `prototype-design-system.md`（视觉规范）+ `design-tokens.json`（设计令牌）。

模板**不带版本号**；生成实际产物时把 `v{major}.{minor}` 占位符替换为具体值。

---

## 6. 工作流 CLI（`.workflow/workflow.py`，纯 Python 标准库）

```powershell
# 索引与门禁
python .workflow/workflow.py index      --iteration v1.0       # 生成 manifest + traceability + 缓存
python .workflow/workflow.py validate   --iteration v1.0       # 校验全部 stage
python .workflow/workflow.py validate   --iteration v1.0 --stage 02-design   # 单 stage 校验

# 任务管理
python .workflow/workflow.py context    --iteration v1.0 --task TASK-API-010   # 生成/复用 TASK Context Pack
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-API-010 --result succeeded
# ↑ 默认仅追加 task-runs JSON，不触发 index/dashboard
#   --refresh-index      当任务改变了产物状态时加上
#   --refresh-dashboard  当要立即刷新仪表盘时加上

# 仪表盘
python .workflow/workflow.py dashboard  --iteration v1.0       # 渲染静态 HTML 仪表盘
```

**子命令表**：

| 子命令 | 功能 | 写入文件 |
|---|---|---|
| `index` | 全产物索引 + traceability 图 + hash 缓存 | `manifest.yaml` / `traceability.json` / `cache/index.json` |
| `validate` | stage gate 检查（无产物修改）| stderr only |
| `context` | 提取 TASK 相关章节，按 hash 复用 | `context-packs/<ver>-<task>.md` |
| `task-finished` | 追加 TASK 结论 JSON（默认轻量）| `task-runs/<ver>-<task>.json` |
| `dashboard` | 渲染静态 HTML 仪表盘 | `dashboard/index.html` |

所有命令子命令接受 `--iteration`（默认从 `iteration/` 推断最大值；不存在则返回 `v1.0`）。

---

## 7. LLM 自动化脚本（`.workflow/scripts/`）

4 个本地脚本，让 LLM 不必亲自 grep / read 多份文档：

| 脚本 | 命令示例 | 替代的 LLM 行为 |
|---|---|---|
| `stage_status.py` | `--iteration v1.0` | "v1.0 现在到哪个阶段？能进下一阶段吗？" |
| `id_registry.py` | `--iteration v1.0 --prefix FR` | "下一个可用 FR 是多少？" |
| `query_id.py` | `--id FR-005 --iteration v1.0` | "FR-005 出现在哪些文件？" |
| `check_links.py` | `--iteration v1.0` | "v1.0 文档里有断链吗？" |

所有脚本纯 stdlib，可独立运行：

```bash
python .workflow/scripts/stage_status.py --iteration v1.0
python .workflow/scripts/id_registry.py --iteration v1.0
python .workflow/scripts/query_id.py --id TASK-API-010 --iteration v1.0
python .workflow/scripts/check_links.py --iteration v1.0
```

---

## 8. 稳定 ID 与追溯

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

追溯自动从 markdown 中提取并存入 `.workflow/traceability.json`（`index` 子命令产出）。

---

## 9. 常用工作流

### 9.1 启动一个新版本（v1.0）

```
1. baseline/ 4 份文档必须已 Approved
2. 触发 baseline-gate → 通过
3. 触发 normalize-requirement（首版场景） → 生成 v1.0-requirement.md
4. 人工审核 → status: Approved
5. 进入 02-design / 03-planning / 04-implementation / 05-pull-request / 06-rc-review-release
6. RC 完成 → 生成 v1.0-iteration-changelog.md
7. 触发 manage-iteration → 归档 v1.0
```

### 9.2 启动 v1.1+ 增量迭代

```
1. 触发 normalize-requirement → 读 4 个 baseline + v1.0-requirement + v1.0-changelog
2. 输出 v1.1-requirement.md（含 change_set: added / / / deprecated）
3. 人工审核 → status: Approved
4. 触发 iterate-implementation skill（按 TASK 列表实施）
6. 每个 TASK 完成 → python .workflow/workflow.py task-finished --result succeeded
7. RC 完成 → manage-iteration 归档 v1.0
```

### 9.3 实施单个 TASK

```bash
# 1. 启动前：刷新索引 + 校验 gate + 生成 Context Pack
python .workflow/workflow.py index    --iteration v1.0
python .workflow/workflow.py validate --iteration v1.0 --stage 04-implementation
python .workflow/workflow.py context  --iteration v1.0 --task TASK-API-010

# 2. 读 .workflow/context-packs/v1.0-TASK-API-010.md（任务片段，非整篇）

# 3. 实际写代码到 workspace/

# 4. 完成：轻量记录（默认）
python .workflow/workflow.py task-finished --iteration v1.0 --task TASK-API-010 --result succeeded
# ↑ 不重跑 index/dashboard；高频操作零开销
# ↓ 偶尔才需要：
python .workflow/workflow.py task-finished ... --refresh-dashboard

# 5. 查看阶段进度
python .workflow/scripts/stage_status.py --iteration v1.0
```

### 9.4 跨版本引用查询

```bash
# "FR-005 出现在 v1.0 的哪里？"
python .workflow/scripts/query_id.py --id FR-005 --iteration v1.0
# 输出：FR-005 — found in 2 artifact(s)
#   - iteration/v1.0/01-product/v1.0-requirement.md  (FS 作为 FR 子项内嵌)
```

---

## 10. 阶段产物精简（当前状态）

| 阶段 | 产物 |
|---|---|
| 01-product | `requirement.md`（FS-XXX 作为 FR-XXX 子项内嵌）、`prototype.html` |
| 02-design | `architecture-design.md`、`api-spec.md`、`database-dictionary.md` |
| 03-planning | `task-plan-dag.md`、`validation-plan.md` |
| 04-implementation | `source-code.md`（含 ISSUE 列表）、`test-results.md` |
| 05-pull-request | `pull-request.md` |
| 06-rc-review-release | `release-notes.md` |

---

## 11. 验证检查清单

```bash
# 1. 验证当前迭代
python .workflow/workflow.py validate --iteration v1.0

# 2. 看阶段进度
python .workflow/scripts/stage_status.py --iteration v1.0

# 3. 跑单测
python -m unittest .workflow/tests/test_workflow.py

# 4. 检查断链
python .workflow/scripts/check_links.py --iteration v1.0
```

期望输出：
- `validate` → `result: PASS (0 errors, 0 warnings)`
- `stage_status` → 所有 ✅ `approved` + `Overall gate: passed`
- `unittest` → `Ran 5 tests in ... OK`
- `check_links` → `✅ all local links resolve` 或仅 warning

---

## 12. AGENTS.md 角色

`AGENTS.md` 是项目级 AI Agent 与开发者协作规则（含 §17 版本化规则、source-of-truth 优先级、TDD 标准、commit 约定等）。它是**唯一**对所有 Skill / Agent 生效的全局规则文件。详见 `AGENTS.md`。

---

## 13. License

MIT

---

## 14. ⚠️ 免责声明 / Disclaimer

> 本项目当前处于 **实验阶段**，仅供 AI 工作流自动化的学习与研究使用。
>
> **不建议、亦不应用于任何生产环境。** 项目中涉及的脚本、模板、生成的代码与文档，均按"现状"提供，不附带任何形式的明示或暗示保证。
>
> 本项目（或其衍生作品）的使用、复制、修改、分发等行为所**直接、间接、附带或偶然产生**的任何损失（包括但不限于数据丢失、业务中断、服务不可用、经济损失、知识产权纠纷等），**作者与贡献者均不承担任何责任**。
>
> 使用者需自行评估其适用性，并对其使用本项目所产生的全部后果承担完全责任。
