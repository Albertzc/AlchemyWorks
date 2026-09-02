# Implementation Template (merged: task-plan-dag + validation-plan + source-code + test-results + issue-fixes)

> 跨版本复用的实施阶段文档模板。**模板本身不带版本号**，被 `iteration/v{major}.{minor}/04-implementation/` 产物引用。
> 本文件合并了旧 5 个模板（task-plan-dag + validation-plan + source-code + test-results + issue-fixes），按 7 节结构组织。

## 用法

| 产物 | 路径 | 备注 |
|---|---|---|
| `v{major}.{minor}-task-plan-dag.md` | `iteration/v{major}.{minor}/03-planning/` | 03 阶段任务 DAG |
| `v{major}.{minor}-validation-plan.md` | 同 03-planning | 验证矩阵（与 task-plan 一一对应）|
| `v{major}.{minor}-source-code.md` | `iteration/v{major}.{minor}/04-implementation/` | 实施主记录（含 ISSUE 列表）|
| `v{major}.{minor}-test-results.md` | 同 04-implementation | 实际测试数据 |
| `v{major}.{minor}-issue-fixes.md` | **v1.1+ 取消**，并入 source-code.md §5 | — |

> **v1.1+ 优化**：issue-fixes 章节并入 source-code.md §5 已知限制，减少产物数量。

---

## 产物 1：task-plan-dag.md（03-planning）

```markdown
---
document_type: task-plan-dag
version: 1.0.0
status: draft
owner: Tech Lead
last_updated: YYYY-MM-DD
base_version: <上一已批准迭代，如 v1.0>
---

# 任务计划 DAG

> 把架构拆解为可并行执行的任务节点。一条任务 = 一个稳定 ID + 一个 PR 工作单元。

## 1. 文档信息
## 2. 任务 ID 命名（前缀表 SETUP-DATA-CONN-STEP-RUN-API-UI-INT-TEST-DOC）
## 3. 任务 DAG 总览（mermaid 或 ASCII）
## 4. 任务节点（每节一个 TASK）
   - 目标 / 前置 / 输出物 / 完成条件 / 负责人 / 工时 / 风险
## 5. 关键里程碑
## 6. 风险与依赖
## 7. 变更记录
```

---

## 产物 2：validation-plan.md（03-planning）

```markdown
---
document_type: validation-plan
version: 1.0.0
status: draft
owner: QA / Tech Lead
last_updated: YYYY-MM-DD
---

# 验证计划

## 1. 文档信息
## 2. 验证层级（Format / Lint / Type / Unit / Integration / E2E / Build / Security）
## 3. 任务级验证矩阵（TASK-ID | 单测 | 集成 | E2E | 验证要点）
## 4. 关键场景验证（Given / When / Then）
## 5. 回归策略
## 6. 验证产物（test-results / issue-fixes 路径）
## 7. 变更记录
```

---

## 产物 3：source-code.md（04-implementation 主记录）

> v1.1+ 起，issue-fixes 内容合并到本文件 §5 "已知限制 / Issue 列表"。

```markdown
---
document_type: source-code-summary
version: 1.0.0
status: draft
owner: Tech Lead
last_updated: YYYY-MM-DD
---

# <产品> v{major}.{minor} Source Code Summary

## 1. 交付范围（TASK 列表 + ✅/⚠️/❌）
## 2. 关键设计决策（实施层）
   - 配置与启动
   - 数据层
   - 抽象层
   - Step 系统
   - 编排器
   - 加密
   - 错误分类
## 3. 文件清单（树形）
## 4. AC 验收矩阵（AC-XXX → 测试文件 → 结果）
## 5. 已知限制与 ISSUE 列表（v1.1+ 合并入此）
   - 限制 | 影响 | 推迟版本
   - ISSUE-NNN | 严重度 | 标题 | 状态 | 修复版本
## 6. 前端（若实施）
## 7. 运行方法（venv / pip install / make / npm）
## 8. 变更记录
```

---

## 产物 4：test-results.md（04-implementation）

```markdown
---
document_type: test-results
version: 1.0.0
status: draft
owner: QA / Tech Lead
last_updated: YYYY-MM-DD
---

# <产品> v{major}.{minor} 测试结果

## 1. 验证层级（命令 + 触发时机 + 通过状态）
## 2. AC 验收测试（AC | 测试文件 | 期望 | 实际）
## 3. Unit Tests（测试名 + 期望 + 实际）
## 4. 覆盖率
## 5. 已知问题（指针到 source-code.md §5）
## 6. 变更记录
```

---

## 产物 5：issue-fixes.md（v1.0 专用，v1.1+ 取消）

```markdown
---
document_type: issue-fixes
version: 0.4.0
status: Approved
owner: Tech Lead
last_updated: YYYY-MM-DD
---

# <产品> v1.0 问题修复记录

> v1.1+ 起，本文档合并入 v1.1-source-code.md §5 已知限制。

## 1. Issue 列表
## 2. Issue 详情模板
## 3. 修复汇总
## 4. 已知遗留（不修）
## 5. 变更记录
```

## 模板修改流程

详见 `templates/README.md` §模板修改流程。