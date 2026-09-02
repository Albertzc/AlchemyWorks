---
name: iterate-implementation
description: "04 stage write code source-code.md tests."
---

# Iterate Implementation

## Purpose

把 03-planning 的任务 DAG 真正落地为代码：源码、配置、测试，并把实施过程结构化记录到 `iteration/v{N}/04-implementation/` 三个核心文档。

本 skill 只覆盖**一个完整版本的 04 阶段**（如 v1 或 v2+）。前端 / 后端分立项目时按 workspace 目录拆分。

## Inputs (preconditions)

进入 04 前必须确认：

1. `iteration/v{N}/03-planning/v1-task-plan-dag.md` `status: Approved`
2. `iteration/v{N}/03-planning/v1-validation-plan.md` 已确定验证命令
3. `iteration/v{N}/02-design/` 三件套（architecture / api-spec / database-dictionary）齐全
4. `iteration/v{N}/01-product/v1-requirement.md` 与 `baseline/decisions/` 存在
5. 用户已回答"实现范围 + DB 实例 + 优先级 + 验证命令"四元组（默认推荐组合见 `references/scope-recommendation.md`）

## Output Artifacts

| 文件 | 路径 | 必填 |
|---|---|---|
| 实际代码 | `workspace/{backend,frontend,...}/` | ✅ |
| 实施主记录 | `iteration/v{N}/04-implementation/v{N}-source-code.md` | ✅ |
| 测试结果 | `iteration/v{N}/04-implementation/v{N}-test-results.md` | ✅ |
| 问题修复 | `iteration/v{N}/04-implementation/v{N}-issue-fixes.md` | ✅ |
| 阶段导航 | `iteration/v{N}/04-implementation/README.md` | 推荐 |

## Default Scope Recommendations (when user says "G")

如果用户回复"G"（默认），按下列推荐组合：

| 决策点 | 默认 | 适用场景 |
|---|---|---|
| 实现范围 | **B 最小可运行版本** | 覆盖 AC-001..007 端到端可演示；非全量 TASK |
| DB 实例 | **P3 Testcontainers + dev SQLite** | dev SQLite 启动快，集成测试用真实 PG 行为 |
| 优先级 | 按 task-plan-dag 默认 1→7 | SETUP → DATA → CONN → STEP → RUN → INT → TEST |
| 验证命令 | Format + Lint + Type + Unit | 前 4 项；E2E / Build / Security 推迟 RC |

## Workflow

```text
0. 用户确认四元组（实现范围 / DB / 优先级 / 验证）
1. 创建 iteration/v{N}/04-implementation/ 目录骨架
2. 实际写代码到 workspace/{子项目}/
3. 编写 v{N}-source-code.md 主记录（结构见 references/source-code-template.md）
4. 占位 v{N}-test-results.md（首次实际跑测试后填数据）
5. 占位 v{N}-issue-fixes.md（实际发现 issue 后追加）
6. 编写 README.md（如何跑测试 / 启动 dev server）
7. 全部代码文件经 compileall 静态校验（即使未安装依赖）
8. 列出"待你执行"清单（venv 创建 / pip install / make test）
```

## Context Budget Rules (HARD)

> **核心原则**：**按 TASK-XXX 切片**装载上下文，**禁止**整篇前置文档作为单次 prompt 输入。

### Project Context Pack integration

Before starting a task, run from the project root:

```powershell
python .workflow/workflow.py index --iteration vN
python .workflow/workflow.py context --iteration vN --task TASK-XXX-NNN
```

Use the generated `.workflow/context-packs/vN-TASK-XXX-NNN.md` as the task context. The Context Pack is authoritative for the selected excerpts; load a full source artifact only when a required detail is absent and record that exception in the implementation log.

### Task completion report

After each TASK's code and verification work, run:

```powershell
python .workflow/workflow.py task-finished --iteration vN --task TASK-XXX-NNN --result succeeded
```

Use `failed` when verification fails and `blocked` when a required decision or dependency prevents completion. Do not report the TASK as complete until the command has refreshed `.workflow/dashboard/index.html` and printed the task conclusion for human confirmation.

### 单次 prompt 预算红线

| 项目 | 红线 |
|---|---|
| 输入侧 tokens | **≤ 16k**（主流 8B 模型窗口下留 50% 给输出 + 工具响应） |
| 单次 TASK 数量 | **= 1**（严禁"TASK-001..005 一起做"） |
| 前置文档装载 | 禁止整篇；只摘录该 TASK 涉及的 ID 对应小节 |

### ❌ 禁止的反模式

1. 把 `v{N}-requirement.md` / `architecture-design.md` / `api-spec.md` / `database-dictionary.md` / `task-plan-dag.md` / `validation-plan.md` **任一份整篇**塞入单次 prompt
2. 把 `v{N}-source-code.md` **已写的全部历史章节**复读到当前 prompt（哪怕"以防万一"）
3. 把完整 git diff（**>2k 行变更**）一次性喂给 reviewer 子代理
4. 同时打开多个非必要的 `read_file`/`search_files`（独立读取合并到一次 batch）

### ✅ 正确的上下文装载流程（每个 TASK 开工前 30 秒）

```text
1. 锁定唯一 TASK-XXX ID（来自 v{N}-task-plan-dag.md）
2. 从 task-plan-dag.md 中摘录该 TASK 一行 + 它的 "depends_on" / "AC refs"
3. 列出它涉及的所有稳定 ID（FS-XXX / API-XXX / TBL-XXX / AC-XXX），逐个去对应文档
   用 search_files + offset/limit 精准拉取该 ID 所在段落（不是全文）
4. 把当前要修改的源码文件路径列出来，按需 read_file（不要把所有相关文件预先全读）
5. 已有测试文件路径，按需 grep 关键符号
6. 历史上下文：先 session_search 最近一次相关实施记录，再决定要不要 load
```

### 触线处理（决策表）

| 信号 | 动作 |
|---|---|
| 想装载整篇 source-code.md | **改为** grep 该 TASK 的章节（head + tail 各 100 行够用） |
| 想装载整篇 api-spec.md | **改为** grep 该 TASK 涉及的 1-3 个 endpoint 行 |
| 涉及 3+ 张表的多模块改动 | **拆 TASK**（回到 task-plan-dag.md 重新拆粒度） |
| 单 TASK 真实需要 >16k tokens（如大模块重构） | **用 `delegate_task` 起独立子会话**，主会话只持有摘要 |
| prompt 输入侧接近 16k | **立即停止**，拆分 prompt 或拆 TASK，不要硬塞 |

### Plan-and-Execute 替代模式

当一个 TASK 本质就要 30k+ tokens（复杂模块重构、跨 3+ 文件的大改动）：

1. 在主会话里**只持有 plan**（5-10 行：目标 / 输入切片 / 验收）
2. 用 `delegate_task(goal=..., context=<最小上下文>)` 起**独立子会话**
3. 子会话返回 **patch 后的代码 + source-code.md 该 TASK 章节的追加条目**（不是整篇）
4. 主会话**接收摘要**（≤2k tokens），负责把摘要追加回 source-code.md

这条规则**优先于** "Default Scope Recommendations"——如果默认组合会触发超预算，先缩范围，再谈默认值。

## Critical Pitfalls

完整 pitfall 列表见 `references/pitfalls.md`。最常见的 3 个：

1. **`patch` 工具缩进陷阱**：大块替换时 `new_string` 整体缩进错误把代码推出函数 → 每次大块 patch 后立即 `python3 -m compileall -q <dir>` 验证。
2. **async generator 不能 return value**：用 `return`（裸）而非 `return iter([])`。
3. **顶层 `type X = ...` 陷阱**：统一用工厂函数 `def foo_column(): return mapped_column(...)`。

### Frontend multi-batch delivery (large UI surface)

> 经验：用户填 10+ 个视图页面时，一次性写完会让 prompt 上下文爆炸、vue-tsc 报错成百上千无法定位、出错重写代价高。**强制分批 + 每批 type-check 验证**。

**强制规则**：

1. **每批 2-4 个 view，最多 5 个**。超出就拆。
2. **每批结束必跑 `vue-tsc --noEmit`**，只看本批写的 + 已被前批修过的错；用 `grep -v "Cannot find module '@/views/"` 过滤掉"待续 view"的预期缺失。
3. **batch 划分原则**：
   - 列表/CRUD 页面（轻量、可独立验证）放同一批
   - 含业务组件 + 时间轴 + 错误诊断的详情页单独一批
   - 边缘页（404 / 空状态）放最后一批
4. **副产修跨批累积**：A 批修的 type re-export / schema 类型补全，B 批才能用；不要把"待修"推到收尾。
5. **写新组件前先 `read_file` 看现有组件的 prop 定义**。盲猜组件签名（特别是 `PipelineStageTimeline` 给 Run 用还是 Pipeline 用）会撞类型墙。

详见 `references/frontend-vue3-stack.md` §13（含收尾前必跑的 type-check / lint / unit / dev 四件套 + ESLint v9 flat config + side-effects-in-computed 修复 + `vue/require-default-prop` 套路）。

### Context-bloat discipline (applies to any large task)

用户原话：「上下文太大的这个情况，有什么办法解决？」→ 这是 **类级别** 工作流问题，不是单次抱怨。

**5 个工具级手段**（按优先级用）：

| 优先级 | 工具 | 用法 |
|---|---|---|
| 1 | `search_files` / `search_content` | 找关键行而非全文读，省 80%+ token |
| 2 | `read_file offset=N limit=M` | 大文件分页（默认 200 行/页），按需读 |
| 3 | `patch` 改 5-30 行 | 不用 `write_file` 整页覆盖，避免上下文重复装载 |
| 4 | `delegate_task` | 探索性/汇总性子任务扔给隔离 context 子 agent，只回摘要 |
| 5 | `open_preview` + `read_preview` + vision | 浏览器看渲染态，代替读静态 HTML（原型/UI 阶段） |

**绝对不做**：

- 一次 `read_file` 拉 100KB+ 全文
- 把长文档复制到我的回复里（用 grep 摘要行）
- 把"待修"列表塞进 prompt，让 prompt 越来越长

完整论述见 `references/frontend-vue3-stack.md` §14。

## Companion Documents Structure

`v{N}-source-code.md` 8 节结构（参考 `references/source-code-template.md`）：

1. 交付范围（按 task-plan-dag 列表，每条标 ✅/⚠️/❌）
2. 关键设计决策（实施层，含 ADR 引用）
3. 文件清单（树形）
4. AC 验收矩阵（测试 ↔ AC）
5. 已知限制与后续工作（明确推迟项 + 原因）
6. 前端/其他子项目（若未实施，注明推迟到 v1.1）
7. 运行方法（venv / pip install / make 目标）
8. 变更记录

## Validation Checklist (before reporting done)

- [ ] 所有 .py 文件通过 `python3 -m compileall -q` （无需装依赖即可静态校验）
- [ ] `v{N}-source-code.md` 8 节齐全
- [ ] `v{N}-test-results.md` 至少含 AC 矩阵（即使实际数据待填）
- [ ] `v{N}-issue-fixes.md` 至少含模板 + 当前已知遗留
- [ ] README.md 含 3 步可执行：venv / install / test
- [ ] 在 v1-source-code.md §5 明确列出"已知限制"
- [ ] 在交付消息里给出清晰的"待你执行"清单（venv、pip install、make test）

## References

- `references/source-code-template.md` — `v{N}-source-code.md` 完整模板（基于 v1 实证）
- `references/pitfalls.md` — 详尽 pitfall 清单 + 修复方案
- `references/dual-db-compat.md` — SQLite / PostgreSQL 双数据库兼容模式
- `references/p3-test-strategy.md` — Testcontainers 之外的低成本 E2E 验证策略
- `references/frontend-stack-comparison.md` — Vue3 vs React 对 FastAPI 后端决策模板
- `references/scope-recommendation.md` — 用户回复"G"时的默认四元组
- `references/frontend-vue3-stack.md` — Vue 3 + Element Plus + openapi-typescript 实战配方（类型链路、按需导入、14 路由模板、type-check 验证脚本）
