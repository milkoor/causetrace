#!/usr/bin/env python3
"""Validate that the public cross-project prompt morphology docs stay redacted.

The validator exports the current public tree into a temporary location and
compares it against the tracked public tree. If the tracked tree contains
unredacted content, the exported copy will diverge and the check fails.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SENSITIVE_TERMS = [
    "automatic-signature",
    "lingjian-saas",
    "lingjian",
    "customer",
    "客户",
    "5736",
    "extract_all",
    "extract_customers",
    "scripts/",
    "session_id",
]


def export_public_tree(source: Path, dest: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "export_public_cross_project_prompt_morphology.py"),
        str(source),
        str(dest),
    ]
    subprocess.run(cmd, check=True)


def diff_trees(left: Path, right: Path) -> list[str]:
    mismatches: list[str] = []
    cmp = filecmp.dircmp(left, right)
    if cmp.left_only:
        mismatches.extend(f"only in public tree: {name}" for name in cmp.left_only)
    if cmp.right_only:
        mismatches.extend(f"only in exported tree: {name}" for name in cmp.right_only)
    if cmp.diff_files:
        mismatches.extend(f"content differs: {name}" for name in cmp.diff_files)
    for sub in sorted(cmp.common_dirs):
        mismatches.extend(
            f"{sub}: {item}" for item in diff_trees(left / sub, right / sub)
        )
    return mismatches


def grep_sensitive_terms(root: Path) -> list[str]:
    results: list[str] = []
    for term in SENSITIVE_TERMS:
        proc = subprocess.run(
            ["rg", "-n", "--hidden", "-S", term, str(root)],
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            results.append(f"term {term!r} matched:\n{proc.stdout.strip()}")
        elif proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr.strip() or f"rg failed for term {term!r}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the public cross-project prompt morphology docs."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("docs/research/branches/cross_project_prompt_morphology"),
        help="Public branch directory to validate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    if not source.exists():
        print(f"source directory not found: {source}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="cross-project-public-") as tmp:
        exported = Path(tmp) / "exported"
        export_public_tree(source, exported)

        sensitive_hits = grep_sensitive_terms(source)
        diffs = diff_trees(source, exported)

        if sensitive_hits:
            print("sensitive terms found in public tree:", file=sys.stderr)
            for hit in sensitive_hits:
                print(hit, file=sys.stderr)
            return 1

        if diffs:
            print("public tree diverges from redacted export:", file=sys.stderr)
            for item in diffs:
                print(item, file=sys.stderr)
            return 1

    print("public cross-project prompt morphology docs validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
