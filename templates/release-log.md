# Release Log Template（发布日志）

> 跨版本复用的 05-review-release 阶段封档产物模板。**模板本身不带版本号**，被 `iteration/v{major}.{minor}/05-review-release/` 产物引用。
>
> 本模板基于实例项目的真实封档记录提炼，结构与样板对齐：`§1` 范围、`§2` 交付清单（FR/BR/AC）、`§3` ISSUE 收尾、`§4` 关键工程变更、`§5` 质量门禁终态、`§6` 下一版本交接项、`§7` 已知限制与假设（含版本关系段）、`§8` 封档清单。

## 用法

| 产物 | 路径 | 用途 |
|---|---|---|
| `v{major}.{minor}-release-log.md` | `iteration/v{major}.{minor}/05-review-release/` | RC 完成后封档说明：交付清单、ISSUE 收尾、门禁终态、下一版交接项与已知限制 |

**审批契约**：本产物**仅需文件存在**即可通过 05-review-release 阶段校验,frontmatter `status` 字段(`draft` / `In Review` / `Approved`)不参与 stage gate。换言之,审核人无需手工把 `status` 改为 `Approved`,只要把封档说明写到文件里就算交付完成。

**读者**：
- 下一迭代 `normalize-requirement`:读取 §6 交接项与 §2 交付清单,识别本轮 baseline 起点。
- `diff_versions.py`:从本文件 frontmatter `change_set.deprecated` 读取跨版本废弃 ID。
- `manage-iteration` 的 `ARCHIVED.md` 元数据引用本文件路径。
- 归档后的 `iteration/archive/v{N}/` 只读快照。

---

## 文档骨架

```markdown
---
document_type: release-log
version: <v{N+1}.0.0>
status: draft                # 本产物不参与 stage gate 的 Approved 校验;draft/In Review 均可
owner: Tech Lead
last_updated: YYYY-MM-DDTHH:MM:SS±HH:MM # Codex client local time
base_version: <上一已批准迭代,如 v1.3>
change_set:                  # 供 diff_versions.py 读取 deprecated 列表
  deprecated: [FR-XXX, ...]
baseline_ref:
  - baseline/03-tech-stack-decision.md
---

# <产品> v{major}.{minor} Release Log（封档说明）

> v{major}.{minor} RC-complete（05-review-release 已 Approved）后的封档记录。本记录说明本版本的范围、变更、ISSUE 收尾、对下一版本的交接项,以及与上一已批准版本 baseline 的关系。
> 配套:`v{major}.{minor}-requirement.md`(范围与 FR/BR)、`v{major}.{minor}-source-code.md`(实施记录)、`v{major}.{minor}-review-release.md`(评审与发布决定)、`v{major}.{minor}-test-results.md`(测试结果)。

## 1. 范围概览

| 维度 | 内容 |
|---|---|
| 业务范围 | <新增功能需求数 + 体验优化数 + 已废弃需求数(列出 FR/BR 编号)> |
| 工作流范围 | <TASK 总数 + 编号范围,如 TASK-API-401\~405> |
| 涉及模块 | <后端 N 个源码文件 + M 个测试文件;前端 ...> |
| 数据库 | <无 schema 变更 / 有 schema 变更(列出)> |
| 兼容性 | <向后兼容 / 破坏性变更(列出影响面)> |

## 2. 功能交付清单

### 2.1 新增功能(FR-XXX / YYY)

| ID | 标题 | TASK | 验收 |
|---|---|---|---|
| FR-XXX | <标题> | TASK-XXX-NNN | AC-XXX ✅ |
| FR-YYY | <标题> | TASK-YYY-NNN | AC-YYY ✅ |

### 2.2 体验优化(FR-XXX\~YYY)

| ID | 标题 | TASK | 验收 |
|---|---|---|---|
| FR-XXX | <标题> | TASK-XXX-NNN | AC-XXX ✅ |

### 2.3 业务规则(BR-XXX\~YYY)

| ID | 标题 | 说明 |
|---|---|---|
| BR-XXX | <标题> | <一句话说明边界/口径> |

### 2.4 验收标准(AC-XXX\~YYY)

| AC | 描述 | 集成测试 | 结果 |
|---|---|---|---|
| AC-XXX | <描述> | `<test_file.py>(N 个)` | ✅ |
| AC-YYY | <描述> | `<spec.ts>(M 个)` | ✅ |

## 3. ISSUE 收尾

| ISSUE | 类别 | 最终状态 |
|---|---|---|
| ISSUE-V{major}.{minor-1}-NN | <类别> | ✅ 本版本已修复:<简述>;或 ⏳ 交接至 v{N+1}:<理由> |

<本版本是否新增遗留 ISSUE>。

## 4. 关键工程变更

| 维度 | 变更 | 影响 |
|---|---|---|
| <模块/子系统> | <文件 + 改动要点> | <业务/性能/安全影响> |
| <模块/子系统> | <...> | <...> |

## 5. 质量门禁终态

| 检查 | 命令 | 结果 |
|---|---|---|
| <后端/前端 lint/format/type/unit/integration/e2e/build> | `<实际执行命令>` | ✅ <通过项摘要> |
| 工作流一致性 | `python .aw/.workflow/workflow.py preflight --iteration v{major}.{minor}` | ✅ passed;<产物数> |

## 6. v{N+1}+ 交接项

按优先级排列:

| 优先级 | 内容 | 来源 |
|---|---|---|
| 高/中/低 | <交接事项> | <实施期识别 / preflight 提示 / 业务方反馈> |

## 7. 已知限制与假设

| 类型 | 内容 |
|---|---|
| 已知限制 | <限制项,如仅支持 X 不支持 Y> |
| 已知限制 | <...> |
| 假设 | <假设项,如后端使用 SQLite,MySQL 兼容性未经 CI 验证> |
| 假设 | <...> |

### 7.1 版本关系与归档路径

```text
v{major}.{minor-1} (RC-complete YYYY-MM-DD,已归档至 iteration/archive/v{major}.{minor-1}/)  ← baseline
v{major}.{minor} (RC-complete YYYY-MM-DD) ← 当前版本,下一连续版本创建时归档
v{major}.{minor+1} (待创建)
```

按 AGENTS.md §17:

- 本版本作为 active iteration 保留在 `iteration/v{major}.{minor}/`。
- 当 `python .aw/.workflow/workflow.py init-version` 创建下一版本时,会触发「前一连续版本归档」动作,将 `iteration/v{major}.{minor}/` 整体迁移到 `iteration/archive/v{major}.{minor}/`。
- 归档前会再次校验实例 `workspace/README.md` 已刷新到本版本(包含 `<!-- workflow:workspace-readme-version: v{major}.{minor} -->` 标记)。
- 本文件随版本归档迁入 `iteration/archive/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md`,归档目录只读,不得修改。

## 8. 封档清单

- [x] 01-product:`v{major}.{minor}-requirement.md` Approved
- [x] 02-design:`v{major}.{minor}-architecture-design.md` / `v{major}.{minor}-api-spec.md` / `v{major}.{minor}-database-dictionary.md` Approved
- [x] 03-planning:`v{major}.{minor}-task-plan-dag.md` / `v{major}.{minor}-validation-plan.md` Approved
- [x] 04-implementation:`v{major}.{minor}-source-code.md` / `v{major}.{minor}-test-results.md` Approved
- [x] 05-review-release:`v{major}.{minor}-review-release.md` Approved
- [x] 05-review-release:`v{major}.{minor}-release-log.md`(**本文件,仅需存在,无需 Approved**)
- [x] 实例 README:根 `README.md` 已由工作流刷新至 v{major}.{minor}

***

**v{major}.{minor} RC 完成,本封档说明保留至下一版本创建后自动迁移至 `iteration/archive/v{major}.{minor}/05-review-release/v{major}.{minor}-release-log.md`。**
```

---

## 模板修改流程

详见 `templates/README.md` §模板修改流程。

修改本模板时需注意:

1. **审批契约**:`status` 字段保留(与其他模板 frontmatter 对称),但**不参与 stage gate 的 Approved 校验**。若改为强制 `Approved`,会破坏当前 `validation_report()` 的 carve-out 逻辑,需同步修改 `.workflow/workflow.py` 与 `.workflow/tests/test_workflow.py`。
2. **章节数量**:当前 8 节是基于真实封档记录的提炼。新增章节需评估是否与 §2 交付清单或 §5 门禁终态重复。
3. **change_set**:仅 `deprecated` 子键被 `diff_versions.py` 读取;`added` / `modified` 由 `normalize-requirement` 从 `requirement.md` 读取,不要在本文件重复声明以避免双源不一致。
