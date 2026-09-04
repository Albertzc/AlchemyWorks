---
name: manage-iteration
description: Use when creating a new iteration directory (iteration/v{N}/), archiving a previous iteration to iteration/archive/, or resolving the current active iteration reference. Centralizes all iteration-number operations.
---

# Manage Iteration

## Purpose

集中处理所有版本号相关操作。版本号格式：`v{major}.{minor}`，详见 AGENTS.md §17。

1. **检测下一个迭代号**：扫描 `iteration/` 下现有 `v{N}(.{M})?/` 目录，返回 `v{N+1}.0`（major升级）或 `v{N}.{M+1}`（minor升级）。
2. **创建新迭代骨架**：在 `iteration/v{N}/` 下创建 6 个阶段的空子目录。
3. **归档旧迭代**：把已 RC 完成的 `iteration/v{N}/` 整体迁移到 `iteration/archive/v{N}/`，记录归档时间。
4. **解析当前活动迭代**：返回最新已 Approved 的迭代号，供其他 skill 引用。

## Path Conventions

```text
Project Root
├── iteration/
│   ├── v1/                                  ← 当前活动
│   ├── v2/                                  ← 当前活动
│   └── archive/
│       └── v1/                              ← 已 RC 完成的快照
```

## Operations

### 1. Detect Next Version

扫描 `iteration/` 下的 `v{N}(.{M})?/` 目录名，返回下一个迭代号。

```python
import re
from pathlib import Path

def next_version(iteration_dir: Path) -> str:
    """Return the next iteration id given existing v{major}.{minor} directories.

    Bumps the minor when current major matches the highest seen; otherwise
    starts a new major at `.0`.
    """
    pattern = re.compile(r"v(\d+)(?:\.(\d+))?$")
    pairs: list[tuple[int, int]] = []
    for p in iteration_dir.iterdir():
        if not p.is_dir():
            continue
        m = pattern.match(p.name)
        if m:
            pairs.append((int(m.group(1)), int(m.group(2) or 0)))
    if not pairs:
        return "v1.0"
    pairs.sort()
    major, minor = pairs[-1]
    # Decision rule: bump minor by 1. Promote to (major+1, 0) only when the
    # caller explicitly signals a baseline shift; default behavior stays in-major.
    return f"v{major}.{minor + 1}"
```

未通过 `baseline-gate` 时不得调用 `next_version` 返回 `v1.0` 的情况（必须先 baseline）。

### 2. Create New Version Skeleton

```text
iteration/v{N}/
├── 01-product/
├── 02-design/
├── 03-planning/
├── 04-implementation/
├── 05-pull-request/
└── 06-rc-review-release/
```

仅创建空目录；不放任何文件。后续各阶段 skill 自行写入产物。

### 3. Archive Previous Version

触发条件：`iteration/v{major}.{minor}/06-rc-review-release/v{major}.{minor}-release-notes.md` 标记为 `status: Approved` 时（**注意**：文件名以 README §3 流程图与 `.workflow/workflow.py` 为准；旧文档曾用 `-README.md`，已统一为 `-release-notes.md`）。

执行步骤：

1. 创建 `iteration/archive/v{N}/` 目录（其中 `{N}` 是被归档的迭代号，如 `v1.0` 或 `v1.1`）。
2. 把 `iteration/v{N}/` 下**所有内容**移动到 `iteration/archive/v{N}/`。
3. 在 `iteration/archive/v{N}/ARCHIVED.md` 写入归档元数据：

```text
# Archive: v{N}

- archived_at: YYYY-MM-DD
- superseded_by: v{major}.{minor+1}  (in-major bump)  OR  v{major+1}.0  (major promotion)
- rc_artifact: iteration/v{N}/06-rc-review-release/v{N}-release-notes.md
- changelog:    iteration/v{major}.{minor}/01-product/v{major}.{minor}-iteration-changelog.md  (引用)
- note: 此目录只读，不得修改。
```

4. 不删除 `iteration/v{major}.{minor}/01-product/v{major}.{minor}-iteration-changelog.md` 中对 v{N} 的引用。

### 4. Resolve Current Active Version

返回最新**已 Approved** 的版本号：

1. 读取 `iteration/` 下所有 `v{major}.{minor}/06-rc-review-release/v{major}.{minor}-release-notes.md` 的 frontmatter `status`。
2. 按 `(major, minor)` 降序，找到首个 `status: Approved` 的迭代。
3. 若全部未 Approved，返回 `(major, minor)` 最大的迭代（即使是 draft）。

## Failure Handling

- **不允许跳过迭代号**（如禁止从 v1.0 直接到 v1.2；major 之间禁止跳号 v1 → v3）。
- **不允许覆盖** `iteration/archive/` 下的已归档迭代。
- **不允许创建** `iteration/v1.0/` 而未通过 `baseline-gate`（参见 `baseline-gate` skill）。后续 minor 升级不走 baseline-gate。
- 检测到冲突（如手动创建了 `v{major}.{minor}/` 但未走 skill）时，报告并请求用户决策。

## Common Mistakes

| 错误 | 修正 |
|---|---|
| 直接 `mkdir iteration/v1.1/` 而不调本 skill | 走 manage-iteration，确保引用、归档链完整 |
| 把上一迭代 archive 后忘记写 changelog | 提示用户：`v{major}.{minor}-iteration-changelog.md` 必须存在 |
| 手动修改 `iteration/archive/v{N}/` 下的文件 | 阻止；如需更正，开新迭代 |
