#!/usr/bin/env python3
"""Export a redacted public version of the cross-project prompt morphology docs.

This script is intended for a private-source-to-public-export workflow:

- read a private research branch tree
- redact project names, script paths, business counts, and raw session ids
- write the sanitized public tree to a separate output directory

The repository copy of the branch should contain only the public export.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


FILE_RENAMES = {
    "automatic_signature_5task_pilot_v0.1.md": "project_a_5task_pilot_v0.1.md",
    "automatic_signature_decision_v0.1.md": "project_a_decision_v0.1.md",
    "automatic_signature_pilot_plan.md": "project_a_pilot_plan.md",
    "lingjian_saas_5task_pilot_v0.1.md": "project_b_5task_pilot_v0.1.md",
    "lingjian_saas_decision_v0.1.md": "project_b_decision_v0.1.md",
    "lingjian_saas_pilot_plan.md": "project_b_pilot_plan.md",
}


TEXT_REPLACEMENTS = [
    ("automatic-signature", "Project A"),
    ("lingjian-saas", "Project B"),
    ("automatic_signature", "project_a"),
    ("lingjian_saas", "project_b"),
    ("scripts/extract_all.py", "project-specific extraction script A"),
    ("scripts/extract_customers.py", "project-specific extraction script B"),
    ("scripts/extract_orders.py", "project-specific extraction script C"),
    ("tests/test_extract_all.py", "project-specific validation tests"),
    ("tests/test_extract_customers.py", "project-specific validation tests"),
    ("tests/test_extract_orders.py", "project-specific validation tests"),
    ("docs/PROJECT_GUIDE.md", "project guide"),
    ("docs/sms_api_reference.md", "project API reference"),
    ("customer", "record"),
    ("Customers", "Records"),
    ("CUSTOMER", "RECORD"),
    ("客户", "记录"),
    ("5736", "dataset-size redacted; extraction completed successfully"),
    ("session_id", "session_ref"),
]


SESSION_ID_PATTERNS = [
    re.compile(r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b", re.IGNORECASE),
    re.compile(r"\bPM-[AB]-\d{3}\b"),
]


def redact_text(text: str) -> str:
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)

    # Stable anonymous ids for any raw session identifiers we encounter.
    anon_ids = ["PM-A-001", "PM-A-002", "PM-B-001", "PM-B-002"]
    used = 0

    def replace_session_id(match: re.Match[str]) -> str:
        nonlocal used
        if used < len(anon_ids):
            replacement = anon_ids[used]
            used += 1
            return replacement
        return "PM-ANON"

    for pattern in SESSION_ID_PATTERNS:
        text = pattern.sub(replace_session_id, text)

    return text


def export_tree(source: Path, dest: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target_name = FILE_RENAMES.get(path.name, path.name)
        target = dest / relative.parent / target_name

        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in {".md", ".txt"}:
            target.write_text(redact_text(path.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(path, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a redacted public version of the cross-project prompt morphology docs."
    )
    parser.add_argument("source", type=Path, help="Private source directory to redact")
    parser.add_argument("destination", type=Path, help="Public export directory to write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    export_tree(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
