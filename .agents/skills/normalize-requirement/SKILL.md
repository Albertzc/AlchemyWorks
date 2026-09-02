---
name: normalize-requirement
description: Use whenever a new requirement document must be produced. Converts raw requirements into the project's standard Product Requirement under iteration/v{major}.{minor}/01-product/. For first project (v1.0) this triggers baseline-gate first; for iterations (v2.0+, v1.1, ...) it triggers manage-iteration.
---

# Normalize Requirement

## Purpose

将非结构化或格式不统一的用户需求，归一化为 `iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md`。

适用所有版本：
- **首次版本（v1.0）**：先 `baseline-gate`，再 manage-iteration。
- **迭代（v1.1+）**：先 manage-iteration（创建骨架 + 检测 `base_version`），再 normalize。

## Pre-flight

| 版本 | 必须先调用 |
|---|---|
| `v1.0`（首次项目） | `baseline-gate` 校验 `baseline/` 完整性。未通过 → 报错并停止。 |
| `v{major}.{minor}`（minor ≥ 1） | `manage-iteration` 创建骨架并校验 `base_version` 指向已存在的上一迭代。 |
| `v{major}.0` 且 major > 1 | `baseline-gate`（重大变更需重新校验 baseline）；然后 manage-iteration。 |

## Required References

开始转换前，**必须**读取：

- `baseline/01-product-vision.md`
- `baseline/02-product-charter.md`
- `baseline/04-glossary.md`
- `iteration/{上一已批准版本}/01-product/{上一版本}-requirement.md`（用于 diff 与继承）
- `iteration/{上一已批准版本}/01-product/{上一版本}-iteration-changelog.md`（如存在）
- `templates/product.md`（合并后的统一模板）

模板是输出结构的唯一权威来源。不得自行发明另一套 Product Requirement 结构。

## Input

支持以下输入形式：

- 用户直接描述的产品想法或功能需求。
- Markdown、纯文本、邮件或会议纪要。
- 多轮对话中分散出现的需求。
- 已有但章节不完整的需求文档。
- **迭代增量**：在上一版本基础上的新增 / 修改 / 废弃条目。

如果输入来自文件，先完整阅读文件，再开始归一化；不要只依据文件名或摘要推断需求。

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

### 6. 生成原型所需信息

从需求中提取页面和交互线索，写入"原型生成要求"。

### 7. 验收标准

优先把明确的业务结果转换为 `Given / When / Then`。

## Output Contract

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
change_set:                  # 仅迭代场景
  added: [FR-XXX, ...]
  modified: [FR-XXX, ...]
  deprecated: [FR-XXX, ...]
baseline_ref:
  - baseline/01-product-vision.md
  - baseline/02-product-charter.md
owner: Product Owner
last_updated: YYYY-MM-DD
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

转换完成后，先进行人工确认，不要直接将结果作为下一阶段正式输入。确认重点：

- 产品目标和用户角色是否准确（与 baseline 一致）。
- MVP 范围是否过大或过小。
- 功能需求是否完整且没有擅自扩展。
- 关键流程和验收标准是否符合预期。
- 标记项是否已处理。
- （迭代）change_set 是否准确（added/modified/deprecated）。

## Validation Checklist

- [ ] 已通过对应版本的 pre-flight（baseline-gate / manage-iteration）。
- [ ] 已读取 standard template 和 baseline。
- [ ] 原始输入中的明确事实都能在输出中找到。
- [ ] 没有把推断写成已确认事实。
- [ ] 没有引入未经请求的技术设计。
- [ ] 每条功能需求只表达一个可验证目标。
- [ ] MVP 范围、非目标和待确认问题已明确。
- [ ] 页面、关键交互和模拟数据要求足以支持原型生成。
- [ ] 输出文件名 = `v{major}.{minor}-requirement.md`。
- [ ] （迭代）`change_set` 完整列出本轮所有变更。
- [ ] （迭代）未修改 `iteration/v{major}.{minor-1}/` 任何文件。