# Design Template (merged: architecture + api-spec + database-dictionary)

> 跨版本复用的设计阶段文档模板。**模板本身不带版本号**，被 `iteration/v{major}.{minor}/02-design/` 产物引用。
> 本文件合并了旧 `architecture-design.md` + `api-spec.md` + `database-dictionary.md`，按 6 节结构组织。

## 用法

| 产物 | 路径 | 用途 |
|---|---|---|
| `v{major}.{minor}-architecture-design.md` | `iteration/v{major}.{minor}/02-design/` | 模块边界、数据流、关键决策 |
| `v{major}.{minor}-api-spec.md` | 同上 | 接口契约（REST/RPC/事件/Webhook） |
| `v{major}.{minor}-database-dictionary.md` | 同上 | 数据表 / 字段 / 索引 / 迁移策略 |

3 个产物章节结构一致，仅 frontmatter `document_type` 不同。便于同模板派生。

---

## 文档骨架

```markdown
---
document_type: <architecture-design | api-spec | database-dictionary>
version: 1.0.0
status: draft
owner: Tech Lead
last_updated: YYYY-MM-DD
base_version: <上一已批准迭代，如 v1.0>
baseline_ref:
  - baseline/03-tech-stack-decision.md
---

# <产物名>

> <一段引言说明本文档的边界与不写什么>

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 关联产品需求 | iteration/v{major}.{minor}/01-product/v{major}.{minor}-requirement.md |
| 关联功能规格 | iteration/v{major}.{minor}/01-product/v{major}.{minor}-feature-specification.md（或内嵌） |
| 关联技术选型 | baseline/03-tech-stack-decision.md |
| 关联 ADR | baseline/decisions/ADR-*.md |

## 2. 通用约定

<!-- 协议、域名、端口、认证、字符编码、时区、时间格式 -->
<!-- 主键策略、时间戳、软删除、多租户、审计字段 -->
<!-- 模块划分概览 -->

## 3. <模块名>

| ID | 名称 | 层级 | 职责 | 主要依赖 |
|---|---|---|---|---|
| | | | | |

<!-- 或 -->
<!-- 接口 ID | 名称 | 调用方 | 提供方 | 协议 -->
<!-- 或 -->
<!-- 表 ID | 表名 | 模块 | 用途 | 关联接口 -->

## 4. <细颗粒度内容>

### 4.1 <条目>

#### <稳定 ID> <条目名>

<!-- architecture: 模块说明、接口契约（指针到 api-spec）、数据流 -->
<!-- api-spec: 路径、方法、鉴权、参数、响应、错误码、幂等性、限流、示例 -->
<!-- database-dictionary: 表名、模块、主键、字符集、字段、索引、外键、关联接口 -->

**索引**：

| 索引名 | 字段 | 类型 | 唯一 | 说明 |
|---|---|---|---|---|

**外键**：

| 外键名 | 字段 | 引用表 | 引用字段 | 删除策略 |
|---|---|---|---|---|

### 4.2 <条目>

<!-- ... -->

## 5. 兼容性 / 迁移 / 跨切面

<!-- api-spec: 兼容窗口、弃用流程、版本号机制 -->
<!-- database-dictionary: 迁移工具、回滚、灰度策略 -->
<!-- architecture: 认证/授权、日志/监控、异常处理、缓存、限流、i18n -->

## 6. 变更记录

| 版本 | 日期 | 修改人 | 变更说明 |
|---|---|---|---|
| 1.0.0 | YYYY-MM-DD | Tech Lead | 初始版本 |
```

---

## 三种产物的差异点

| 产物 | §1 关键引用 | §2 通用约定 | §3-4 主体内容 | §5 关键内容 |
|---|---|---|---|---|
| architecture-design | feature-spec | ADR 列表 | 模块划分 + 接口契约（指针）+ 数据模型概述 | 跨切面（auth/log/cache/rate-limit/i18n）|
| api-spec | db-dict | 协议 / 错误码 | 接口清单 + 事件回调 | 兼容性策略 |
| database-dictionary | api-spec | 主键 / 软删除 / 多租户 | 表结构（字段+索引+外键+关联接口）+ 视图 | 迁移策略 |

## 模板修改流程

详见 `templates/README.md` §模板修改流程。