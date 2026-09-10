---
name: normalize-requirement
description: Use whenever a user provides an unstructured requirement. Routes it to baseline intake or the manifest-selected iteration, then normalizes it into the appropriate draft artifacts.
---

# Normalize Requirement

## Purpose

将用户提供、格式可能不统一的原始需求，先路由并归档，再归一化为 baseline 草稿或 `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md` 草稿。

## Route First

开始归一化前，运行：

```powershell
python .workflow/workflow.py route-requirement
```

该命令按以下规则输出原始需求的归档位置：

1. `baseline/` 除 `README.md` 外为空：返回 `mode: baseline` 与 `baseline/raw-requirement/`。这是首次项目的 baseline 需求处理；保留用户原文，并根据其明确事实起草 4 份 baseline 文档和 1 份核心流程原型，全部保持 `status: draft`。
2. baseline 已初始化：返回 `mode: iteration`。优先使用 `.workflow/manifest.yaml` 的 `iteration` 字段；若 manifest 不存在或没有有效版本号，再使用目录发现结果。将用户原始材料原样保存到输出的 `iteration/raw-requirement/`；命令返回的 `iteration` 是该输入对应的目标版本。

原始材料不是门禁产物，不要求 frontmatter 或 `status: Approved`。`iteration/raw-requirement/` 中的材料归用户所有且只读：Agent 不得修改、重命名或删除原始文件。归一化产物必须在 frontmatter 或“来源追溯”章节记录原始文件路径与 `route-requirement` 返回的目标版本；归一化产物才进入人工审核。

## Pre-flight

| 版本 | 必须先调用 |
|---|---|
| baseline 路由 | 归档原始需求，起草 `baseline/` 的 4 个文档和核心流程原型；人工审核后运行 `validate --stage 00-baseline`。 |
| `v1.0`（首次项目） | `00-baseline` 通过后调用 manage-iteration 创建骨架，归档同一原始需求的迭代快照，再归一化为产品需求。 |
| `v{major}.{minor}`（已初始化项目） | 使用 `route-requirement` 解析的版本；如目录不存在，先调用 manage-iteration 创建骨架。 |

## Required References

在 iteration 路由下，开始转换前，**必须**读取：

- `baseline/01-product-vision.md`
- `baseline/02-product-charter.md`
- `baseline/04-glossary.md`
- `iteration/raw-requirement/` 中与 `route-requirement` 返回目标版本关联的全部原始需求材料
- `iteration/{上一已批准版本}/01-product/{上一版本}-requirement.md`（用于 diff 与继承）
- `iteration/{上一已批准版本}/01-product/{上一版本}-iteration-changelog.md`（如存在）
- `templates/product.md`（合并后的统一模板）

模板是输出结构的唯一权威来源。不得自行发明另一套 Product Requirement 结构。

## Input

原始材料来自用户，可为直接描述、Markdown、纯文本、邮件、会议纪要或其他可读取文件。先完整阅读全部材料，再开始归一化；不得仅依据文件名、摘要或聊天记忆推断需求。

baseline 路由只从原始材料提取明确事实来起草 baseline 文档；技术选型或其他缺失信息必须保留为 `draft` 中的待确认项，不能擅自补全。iteration 路由使用已批准 baseline 与该迭代原始材料生成产品需求草稿。

## Conversion Rules

### 1. 先提取事实，再组织结构

把输入中的内容区分为：

- **明确事实**：原文直接表达的目标、用户、功能或约束。
- **合理推断**：根据上下文推导出的内容。
- **缺失信息**：无法从输入确定的内容。
- **冲突信息**：输入中互相矛盾的内容。

只允许把明确事实直接写入需求正文。推断、缺失和冲突必须在正文中标记，并汇总到"假设与待确认问题"。

推荐标记：

- `[待确认]`：需要产品负责人确认。
- `[推断]`：由上下文推断，尚未被用户明确确认。
- `[未提供]`：输入中没有相关信息。
- `[冲突]`：存在互相矛盾的描述。

不得为了让文档看起来完整而虚构用户、指标、权限、技术方案、数据模型或业务规则。

### 2. 以产品语言表达

将口语、抱怨和零散想法转换为产品需求语言。**复用 baseline/glossary 的术语**。

不要把技术实现写成产品需求。例如：

- 不将"需要一个 REST API"写成 FR，除非用户明确提出 API 作为产品能力。
- 不擅自生成数据库表、字段、缓存、消息队列或框架选型。

### 3. 需求编号

为可独立验证的内容生成稳定编号：

- 功能需求：`FR-001`、`FR-002`……
- 业务规则：`BR-001`、`BR-002`……
- 非功能需求：`NFR-001`、`NFR-002`……
- 验收标准：`AC-001`、`AC-002`……

一条编号只描述一个可判断的要求。如果已有文档中存在编号，优先保留原编号。**迭代场景下编号从上一版本最大编号继续递增，禁止重用已废弃编号。**

### 4. 保留产品边界

必须区分：

- MVP 必须包含。
- MVP 暂不包含。
- 后续版本候选。
- 非目标。

### 5. 迭代场景的额外要求（v{major}.{minor} minor ≥ 1）

在 §1-§4 之上**额外**要求：

#### 5.1 增量识别

明确区分：

- **新增需求**：本轮新增的 FR / BR / NFR / AC。
- **修改需求**：本轮修改的现有编号（保留编号，更新内容）。
- **废弃需求**：本轮明确废弃的编号（在前言中标注 deprecated，不删除）。
- **未变更需求**：不重复列写。

#### 5.2 跨版本追溯

每条新增 / 修改 / 废弃的需求必须在前言中标注：

```yaml
change_set:
  added: [FR-100, FR-101]
  modified: [FR-010, FR-022]
  deprecated: [FR-005]
```

并在文档正文中体现。

#### 5.3 不破坏上一版本

不得改动 `iteration/v{major}.{minor-1}/` 下的任何文件。如发现上一版本有错误，开新迭代以"修改"条目覆盖。

### 6. 原型决策与所需信息

从需求中提取页面和交互线索，完成原型触发评估，并写入"原型决策与生成要求"。每个 iteration 输出的 frontmatter 必须写入 `prototype_required: true` 或 `prototype_required: false`：新页面、复杂/跨页面流程、影响业务结果的交互、体验重点、多端适配或体验分歧时为 `true`；纯技术改动、沿用既有交互模式的轻量改动，或规格与验收标准可无歧义表达时可为 `false`。`false` 时还必须在 frontmatter 写入非空的 `prototype_baseline` 与 `prototype_rationale`。

### 7. 验收标准

优先把明确的业务结果转换为 `Given / When / Then`。

## Output Contract

### Baseline route

当 `route-requirement` 返回 `mode: baseline` 时，输出为以下 5 份 `status: draft` 产物：

```text
baseline/01-product-vision.md
baseline/02-product-charter.md
baseline/03-tech-stack-decision.md
baseline/04-glossary.md
baseline/05-core-user-flow-prototype.html
```

必须在每份文档中标识原始需求来源。未提供的技术、指标或术语不得虚构；保留为待确认项并等待人工审核。通过 `validate --stage 00-baseline` 后，才可创建 `iteration/v1.0/`。

核心流程原型可为低保真线框、可点击流程或结构化 HTML，必须覆盖核心角色、关键任务闭环、关键状态和权限差异；不要求高保真视觉稿。生成 HTML 原型时仍须遵循 `prototype-design-system` 的工具路由。

### Iteration route

输出文件路径：

```text
iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md
```

frontmatter 必须包含：

```yaml
---
document_type: product-requirement
version: 1.0.0
status: draft
product_name: <产品名称>
base_version: <上一已批准迭代，如 v1.0>
prototype_required: <true|false>
prototype_baseline: <prototype_required 为 false 时必填>
prototype_rationale: <prototype_required 为 false 时必填>
change_set:                  # 仅迭代场景
  added: [FR-XXX, ...]
  modified: [FR-XXX, ...]
  deprecated: [FR-XXX, ...]
baseline_ref:
  - baseline/01-product-vision.md
  - baseline/02-product-charter.md
owner: Product Owner
last_updated: YYYY-MM-DDTHH:MM:SS±HH:MM # Codex client local time
---
```

输出要求：

1. 使用模板中的 YAML frontmatter 和章节顺序。
2. 文档标题、产品名称和版本与输入保持一致；未提供时使用 `[未提供]`。
3. 功能、业务规则、非功能需求和验收标准使用稳定编号。
4. 所有不确定信息都显式标记。
5. 在文档末尾保留"假设与待确认问题"。
6. 不输出 API、数据库字典、系统架构或实现任务。

## Human Review Gate

转换完成后，Agent 必须保持 `status: draft` 或 `status: In Review`，列出该阶段全部待审产物及验证证据，并进行人工确认；不得将状态改为 `Approved`，也不得直接将结果作为下一阶段正式输入。人工审核通过后由人类手动将每份必需产物改为 `Approved`，再运行 `validate --stage 01-product`。确认重点：

- 产品目标和用户角色是否准确（与 baseline 一致）。
- MVP 范围是否过大或过小。
- 功能需求是否完整且没有擅自扩展。
- 关键流程和验收标准是否符合预期。
- 标记项是否已处理。
- （迭代）change_set 是否准确（added/modified/deprecated）。

## Validation Checklist

- [ ] 已运行 `route-requirement`，并按其返回的 mode 与目录归档原始材料。
- [ ] baseline 路由下已起草完整 baseline，或 iteration 路由下已读取已批准 baseline。
- [ ] 已读取 standard template 和 baseline。
- [ ] 原始输入中的明确事实都能在输出中找到。
- [ ] 没有把推断写成已确认事实。
- [ ] 没有引入未经请求的技术设计。
- [ ] 每条功能需求只表达一个可验证目标。
- [ ] MVP 范围、非目标和待确认问题已明确。
- [ ] 已在 frontmatter 声明 `prototype_required: true|false`；`false` 时另有非空 `prototype_baseline` 和 `prototype_rationale`。
- [ ] `true` 时页面、关键交互和模拟数据要求足以支持原型生成。
- [ ] 生成 HTML 原型时已从 `templates/Prototype.html` 保留审核 frontmatter：`status`、`review_decision`、`reviewer`、`reviewed_at`、`review_notes`。
- [ ] 输出文件名 = `v{major}.{minor}-requirement.md`。
- [ ] （迭代）`change_set` 完整列出本轮所有变更。
- [ ] （迭代）未修改 `iteration/v{major}.{minor-1}/` 任何文件。
