# Product Template (merged: requirement + feature-specification)

> 跨版本复用的产品阶段文档模板。**模板本身不带版本号**，被 `iteration/v{major}.{minor}/01-product/` 产物引用。
> 本文件合并了旧 `product-requirement.md` 与 `feature-specification.md`，按 8 节结构组织。
> 修改本模板前请评估对未归档迭代的影响（详见 README §模板修改流程）。

## 用法

| 产物 | 路径 | 用途 |
|---|---|---|
| `v{major}.{minor}-requirement.md` | `iteration/v{major}.{minor}/01-product/` | 产品需求规格书 |
| `v{major}.{minor}-feature-specification.md` | 同上（可选/合并到 requirement） | 功能规格 — 见 §6"FS 段落是否单独成文" |

> **v1.1+ 优化**：FS 段落并入 requirement 的对应 FR 章节（见 §6），不再生成独立 feature-specification。

---

## 文档骨架

```markdown
---
document_type: product-requirement
product_name: <产品名>
document_version: 0.1.0
product_version: MVP
status: draft
owner: Product Owner
last_updated: YYYY-MM-DD
base_version: <上一已批准迭代，如 v1.0>      # 迭代场景必填
change_set:                                  # 迭代场景必填
  added: [FR-XXX, ...]
  modified: [FR-XXX, ...]
  deprecated: [FR-XXX, ...]
baseline_ref:
  - baseline/01-product-vision.md
  - baseline/02-product-charter.md
  - baseline/04-glossary.md
---

# <产品名> 产品需求规格书

> 本文档回答：为什么做、为谁做、做什么。不在此处提前确定 API、数据库表结构或具体技术实现。

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 产品名称 | |
| 产品版本 | MVP / v1.0 / v1.1 / ... |
| 文档状态 | Draft / In Review / Approved |
| 产品负责人 | |
| 技术负责人 | |
| 关联 baseline | baseline/01-product-vision.md, 02-product-charter.md, 04-glossary.md |
| 关联章程 | baseline/02-product-charter.md |

## 2. 产品概述

### 2.1 产品背景
### 2.2 产品定位
### 2.3 产品目标
### 2.4 成功指标

## 3. 用户角色

### 3.1 <角色名>
### 3.2 <角色名>
<!-- ... -->

## 4. 核心概念

| 概念 | 定义 |
|---|---|
| | |

## 5. 核心用户场景

### 5.1 <场景名>
### 5.2 <场景名>
<!-- ... -->

## 6. 功能需求

### 6.1 <功能模块>

- **FR-001**：<需求描述>
  - **FS-001**（v1.0+ 推荐合并到此处）：
    - 关联需求：FR-001
    - 所属页面：
    - 用户角色：
    - 前置条件：
    - 主要流程：
    - 异常路径：
    - 验收要点：
- **FR-002**：<需求描述>
  - **FS-002**：...

### 6.2 <功能模块>

<!-- ... -->

> **FS 段落是否单独成文**：v1.0 阶段建议功能数量多时单独写 feature-specification.md；v1.1+ 增量建议把 FS-XXX 段落并入 requirement.md 对应 FR 下方（节省 token、减少产物）。

## 7. 业务规则

- **BR-001**：<规则描述>
- **BR-002**：<规则描述>

## 9. 非功能需求

- **NFR-001 <类别>**：<描述>
- **NFR-002 <类别>**：<描述>

## 10. 原型生成要求

### 10.1 页面清单

| 页面 ID | 页面名称 | URL/路由 | 主要功能 | 关联 FS |
|---|---|---|---|---|
| | | | | |

### 10.2 必须演示的交互
### 10.3 模拟数据要求

## 11. 验收标准（Given / When / Then）

### AC-001 <场景>

**Given** ...  
**When** ...  
**Then** ...

### AC-002 <场景>
<!-- ... -->

## 12. 需求追踪约定

| 本文档对象 | 下游对象示例 |
|---|---|
| FR-001 | FS-001、Prototype 页面：项目列表 |
| BR-005 | FS-025、Prototype 状态：逾期标识 |
| AC-003 | Validate Case：任务状态更新 |

## 13. 假设与待确认问题

- [待确认] ...
- [推断] ...
- [未提供] ...
- [冲突] ...

## 14. 变更记录

| 版本 | 日期 | 修改人 | 变更说明 |
|---|---|---|---|
| 0.1.0 | YYYY-MM-DD | Product Owner | 初始版本 |
```

---

## 状态机 / 权限矩阵（仅当存在时加入 §6 末尾）

```markdown
### 6.X 状态机

<!-- 关键对象的状态枚举与转换规则，与 baseline/04-glossary.md 保持一致 -->

### 6.X 权限矩阵

| 操作 \ 角色 | 角色 A | 角色 B | 角色 C |
|---|---|---|---|
| | | | |
```

## 模板修改流程

详见 `templates/README.md` §模板修改流程。