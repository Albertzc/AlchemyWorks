#!/usr/bin/env python3
"""
sync-framework.py
=================

双向同步 Nyxigen 稳定版的「工作流框架层」与一个或多个应用项目仓库。

设计目标
--------
- Nyxigen 是工作流框架（.workflow/、.agents/、AGENTS.md、README.md）的稳定版。
- 多个应用项目（Project1、Project2、…）复用同一框架。
- 应用过程中可能对框架层做优化，需要把这些改动回灌到 Nyxigen。
- 此脚本提供 diff / forward / backport / status 四类操作。

当前版本（v1）
---------------
- 实现：枚举框架层 + diff 子命令
- forward / backport 子命令在后续步骤实现。

用法
----
    python scripts/sync-framework.py diff --target <path>
    python scripts/sync-framework.py forward --target <path> [--dry-run] [--backup]
    python scripts/sync-framework.py backport --target <path> [--mode commit|patch]
    python scripts/sync-framework.py status --target <path>

参数
----
    --target <path>    应用项目仓库的本地路径（绝对或相对）。
    --framework-root <path>   框架层根目录（默认 = 脚本所在仓库的根）。

框架层边界（白名单）
-------------------
仅以下路径视为「框架层」，其余目录（workspace/、iteration/、baseline/、templates/）
属于应用项目自身，不在同步范围内：

    .workflow/
    .agents/
    AGENTS.md
    README.md
"""
from __future__ import annotations

import argparse
import filecmp
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# 框架层白名单
# ---------------------------------------------------------------------------

FRAMEWORK_PATHS: tuple[str, ...] = (
    # 工作流 CLI 与编排
    ".workflow/workflow.py",
    ".workflow/README.md",
    # 工作流自动化脚本（不包含运行时缓存/产物）
    ".workflow/scripts/",
    # 单元测试（与工作流逻辑一起演进）
    ".workflow/tests/",
    # 项目级 AI Agent Skill（仓库根的 .agents/）
    ".agents/",
    # 项目协作规则与对外说明
    "AGENTS.md",
    "README.md",
)


@dataclass(frozen=True)
class SyncPaths:
    """一次同步操作涉及的所有路径。"""

    source_root: Path  # 框架源（Nyxigen）仓库根
    target_root: Path  # 应用项目仓库根

    def framework_files(self) -> list[Path]:
        """枚举 source_root 下属于框架层的所有文件（相对 source_root）。

        排除规则：
          - __pycache__/（Python 编译产物，运行时自动生成）
          - *.pyc（同上）
        """
        result: list[Path] = []
        for rel in FRAMEWORK_PATHS:
            abs_path = self.source_root / rel
            if abs_path.is_file():
                if self._is_framework_file(Path(rel)):
                    result.append(Path(rel))
            elif abs_path.is_dir():
                for child in abs_path.rglob("*"):
                    if child.is_file() and self._is_framework_file(
                        child.relative_to(self.source_root)
                    ):
                        result.append(child.relative_to(self.source_root))
        result.sort()
        return result

    @staticmethod
    def _is_framework_file(rel: Path) -> bool:
        parts = rel.parts
        if "__pycache__" in parts:
            return False
        if rel.suffix == ".pyc":
            return False
        return True


@dataclass
class DiffReport:
    """diff 子命令的输出。"""

    only_in_source: list[Path] = field(default_factory=list)
    only_in_target: list[Path] = field(default_factory=list)
    changed: list[tuple[Path, str, str]] = field(default_factory=list)  # (rel, src_hash, tgt_hash)
    identical: list[Path] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.only_in_source or self.only_in_target or self.changed)


def _quick_hash(path: Path) -> str:
    """快速文件指纹（大小 + sha1）。相同 ⇒ 内容相同。"""
    import hashlib

    h = hashlib.sha1()
    h.update(str(path.stat().st_size).encode())
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_paths(paths: SyncPaths) -> DiffReport:
    """对比 source_root 与 target_root 中所有框架层文件。"""
    report = DiffReport()
    source_files = paths.framework_files()

    for rel in source_files:
        src = paths.source_root / rel
        tgt = paths.target_root / rel

        if not tgt.exists():
            report.only_in_source.append(rel)
            continue

        # 快速 hash 比对；不同再用 filecmp 二进制比对确认
        src_hash = _quick_hash(src)
        if tgt.is_file() and _quick_hash(tgt) == src_hash:
            report.identical.append(rel)
            continue

        # 内容确实不同
        if tgt.is_file():
            report.changed.append((rel, src_hash, _quick_hash(tgt)))
        else:
            # target 是目录，source 是文件（罕见但需处理）
            report.changed.append((rel, src_hash, "<dir>"))

    # 反向：target 中存在但 source 中不存在的框架层文件
    target_existing: set[Path] = set()
    for rel in FRAMEWORK_PATHS:
        abs_path = paths.target_root / rel
        if abs_path.is_file():
            target_existing.add(Path(rel))
        elif abs_path.is_dir():
            for child in abs_path.rglob("*"):
                if child.is_file() and SyncPaths._is_framework_file(
                    child.relative_to(paths.target_root)
                ):
                    target_existing.add(child.relative_to(paths.target_root))

    for rel in sorted(target_existing - set(source_files)):
        report.only_in_target.append(rel)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_paths(args: argparse.Namespace) -> SyncPaths:
    source_root = Path(args.framework_root).resolve() if args.framework_root \
        else Path(__file__).resolve().parent.parent
    target_root = Path(args.target).resolve()
    if not source_root.is_dir():
        sys.exit(f"[error] framework root not found: {source_root}")
    if not target_root.is_dir():
        sys.exit(f"[error] target not found: {target_root}")
    return SyncPaths(source_root=source_root, target_root=target_root)


def cmd_diff(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args)
    report = diff_paths(paths)

    print(f"Framework source : {paths.source_root}")
    print(f"Target project   : {paths.target_root}")
    print(f"Framework files  : {len(paths.framework_files())}")
    print()

    if not report.has_changes:
        print("[OK] framework layer is in sync — no differences.")
        return 0

    if report.only_in_source:
        print(f"[only in source] ({len(report.only_in_source)})")
        for rel in report.only_in_source:
            print(f"  + {rel}")

    if report.only_in_target:
        print(f"[only in target] ({len(report.only_in_target)})  ← target has framework files NOT in source")
        for rel in report.only_in_target:
            print(f"  - {rel}")

    if report.changed:
        print(f"[changed] ({len(report.changed)})")
        for rel, _, _ in report.changed:
            print(f"  ~ {rel}")

    if report.identical:
        print(f"[identical] {len(report.identical)} files")

    return 1 if report.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync-framework",
        description="双向同步 Nyxigen 工作流框架层与应用项目。",
    )
    parser.add_argument(
        "--framework-root",
        help="框架源仓库根（默认 = 脚本所在仓库的根）。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_diff = sub.add_parser("diff", help="对比框架层与目标项目的差异（不修改任何文件）。")
    p_diff.add_argument("--target", required=True, help="应用项目仓库路径。")
    p_diff.set_defaults(func=cmd_diff)

    # forward / backport 在后续步骤实现
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
