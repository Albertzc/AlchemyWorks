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

1. `iteration/v{N}/03-planning/v{N}-task-plan-dag.md` `status: Approved`
2. `iteration/v{N}/03-planning/v{N}-validation-plan.md` 已确定验证命令
3. `iteration/v{N}/02-design/` 三件套（architecture / api-spec / database-dictionary）齐全
4. `iteration/v{N}/01-product/v{N}-requirement.md`、适用的 `baseline/decisions/` 与 `baseline/03-tech-stack-decision.md` 存在
5. 用户已确认实现范围、数据环境、优先级和验证命令，或这些决策已在已批准的上游产物中明确。

## Output Artifacts

| 文件 | 路径 | 必填 |
|---|---|---|
| 实际代码 | `workspace/{backend,frontend,...}/` | ✅ |
| 实施主记录 | `iteration/v{N}/04-implementation/v{N}-source-code.md` | ✅ |
| 测试结果 | `iteration/v{N}/04-implementation/v{N}-test-results.md` | ✅ |
| 问题修复（仅 v1.0） | `iteration/v1.0/04-implementation/v1.0-issue-fixes.md` | 兼容旧产物 |
| 阶段导航 | `iteration/v{N}/04-implementation/README.md` | 推荐 |

## Scope and Environment Resolution

实现范围、依赖服务、数据环境、执行顺序和验证命令必须来自已批准的产品需求、技术选型、TASK DAG 与验证计划。若这些输入缺失或相互矛盾，停止并请求人类决定；不得以某个项目的框架、数据库或命令作为默认值。

| 决策点 | 依据 |
|---|---|
| 实现范围 | 已批准 TASK 与关联 AC |
| 数据/外部服务 | `baseline/03-tech-stack-decision.md` 与设计产物 |
| 优先级 | TASK DAG 的依赖关系 |
| 验证命令 | 已批准 validation plan 与项目实际脚本 |

## Workflow

```text
0. 用户确认四元组（实现范围 / DB / 优先级 / 验证）
1. 创建 iteration/v{N}/04-implementation/ 目录骨架
2. 实际写代码到 workspace/{子项目}/
3. 编写 v{N}-source-code.md 主记录（结构见 `templates/implementation.md` 的“产物 3”）
4. 占位 v{N}-test-results.md（首次实际跑测试后填数据）
5. 在 `v{N}-source-code.md` §5 记录已知问题；仅 v1.0 额外维护 `v1.0-issue-fixes.md` 以兼容旧产物。
6. 编写 README.md（如何跑测试 / 启动 dev server）
7. 使用项目语言和工具链对应的静态检查或构建命令验证改动。
8. 在 README 和交付消息中记录实际可执行的安装、启动和测试命令。
9. 保持 04 阶段产物为 `draft` 或 `In Review`，列出全部必需产物和测试/验证证据，交由人类审核。Agent 不得将任何产物的 `status` 写入或修改为 `Approved`；人类批准后运行 `validate --stage 04-implementation`，才可进入 05 阶段。
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

Default behaviour (matches the unit test `test_task_finished_records_result_and_refreshes_dashboard`): the call appends one JSON record to `.workflow/task-runs/` and prints the conclusion. It does **not** re-render the dashboard — that was made explicit default-off to keep repeated `task-finished` calls O(1) instead of O(N_artifacts).

To see the new task on the dashboard afterwards, run **one** of:

```powershell
python .workflow/workflow.py task-finished ... --refresh-dashboard
# or separately:
python .workflow/workflow.py dashboard --iteration vN
```

Use `failed` when verification fails and `blocked` when a required decision or dependency prevents completion. Do not report the TASK as complete until the task-run JSON has been written and the printed conclusion has been confirmed.

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

这条规则优先于任何范围偏好：如果当前 TASK 会触发超预算，先缩小或拆分范围。

### Frontend Vue 3 multi-batch delivery (only when baseline matches)

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

收尾前根据已批准的 validation plan 和项目实际脚本，运行 type-check、lint、unit test 与开发启动验证；具体命令以项目自身工具链为准。

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

上述约束适用于所有大规模实现任务；应优先使用项目提供的精确检索、局部读取和小范围编辑能力。

## Companion Documents Structure

`v{N}-source-code.md` 8 节结构（参考 `templates/implementation.md` 的“产物 3”）：

1. 交付范围（按 task-plan-dag 列表，每条标 ✅/⚠️/❌）
2. 关键设计决策（实施层，含 ADR 引用）
3. 文件清单（树形）
4. AC 验收矩阵（测试 ↔ AC）
5. 已知限制与后续工作（明确推迟项 + 原因）
6. 前端/其他子项目（若未实施，注明目标版本或待确认原因）
7. 运行方法（项目实际安装、启动和测试命令）
8. 变更记录

## Validation Checklist (before reporting done)

- [ ] 已运行适用于当前语言和项目工具链的静态检查、构建或类型检查
- [ ] `v{N}-source-code.md` 8 节齐全
- [ ] `v{N}-test-results.md` 至少含 AC 矩阵（即使实际数据待填）
- [ ] v1.0 的 `v1.0-issue-fixes.md` 含当前已知遗留；v1.1+ 已知问题已写入 `v{N}-source-code.md` §5
- [ ] README.md 含项目实际的安装、启动和测试步骤
- [ ] 在 `v{N}-source-code.md` §5 明确列出"已知限制"
- [ ] 在交付消息里给出清晰的后续执行命令或说明无后续命令
