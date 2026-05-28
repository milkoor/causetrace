"""Regression tests for tailer line-level deduplication."""

from __future__ import annotations

import json
from pathlib import Path

import causetrace.hooks.continue_tailer as continue_tailer
import causetrace.hooks.copilot_tailer as copilot_tailer


def test_continue_tailer_preserves_repeated_tool_calls(tmp_path: Path) -> None:
    logs_dir = tmp_path / ".continue" / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "core.log").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "message": "Running tool: read",
                        "tool": {"name": "read", "input": {"file_path": "a.py"}},
                        "timestamp": "2026-05-28T10:00:01",
                    }
                ),
                json.dumps(
                    {
                        "message": "Running tool: read",
                        "tool": {"name": "read", "input": {"file_path": "a.py"}},
                        "timestamp": "2026-05-28T10:00:02",
                    }
                ),
            ]
        )
        + "\n"
    )

    old_log_dir = continue_tailer.LOG_DIR
    continue_tailer.LOG_DIR = logs_dir
    try:
        events = continue_tailer.scan_logs(max_files=1)
    finally:
        continue_tailer.LOG_DIR = old_log_dir

    assert len(events) == 2
    assert [ev.tool_name for ev in events] == ["Read", "Read"]
    assert [ev.timestamp for ev in events] == [
        "2026-05-28T10:00:01",
        "2026-05-28T10:00:02",
    ]


def test_continue_tailer_dedups_identical_log_lines(tmp_path: Path) -> None:
    logs_dir = tmp_path / ".continue" / "logs"
    logs_dir.mkdir(parents=True)
    line = json.dumps(
        {
            "message": "Running tool: read",
            "tool": {"name": "read", "input": {"file_path": "a.py"}},
            "timestamp": "2026-05-28T10:00:01",
        }
    )
    (logs_dir / "core.log").write_text(f"{line}\n{line}\n")

    old_log_dir = continue_tailer.LOG_DIR
    continue_tailer.LOG_DIR = logs_dir
    try:
        events = continue_tailer.scan_logs(max_files=1)
    finally:
        continue_tailer.LOG_DIR = old_log_dir

    assert len(events) == 1


def test_copilot_tailer_preserves_repeated_tool_calls(tmp_path: Path) -> None:
    base = tmp_path / "Code" / "logs"
    log_dir = base / "2026-05-28" / "exthost" / "window1" / "github.copilot-chat"
    log_dir.mkdir(parents=True)
    (log_dir / "copilot.log").write_text(
        "\n".join(
            [
                '[2026-05-28 10:00:01] {"name":"read_file","input":{"file_path":"a.py"}}',
                '[2026-05-28 10:00:02] {"name":"read_file","input":{"file_path":"a.py"}}',
            ]
        )
        + "\n"
    )

    old_base = copilot_tailer._CODE_LOG_BASE
    copilot_tailer._CODE_LOG_BASE = base
    try:
        events = copilot_tailer.scan_logs(max_log_dirs=1)
    finally:
        copilot_tailer._CODE_LOG_BASE = old_base

    assert len(events) == 2
    assert [ev.tool_name for ev in events] == ["Read", "Read"]
    assert [ev.timestamp for ev in events] == [
        "2026-05-28T10:00:01",
        "2026-05-28T10:00:02",
    ]


def test_copilot_tailer_dedups_identical_log_lines(tmp_path: Path) -> None:
    base = tmp_path / "Code" / "logs"
    log_dir = base / "2026-05-28" / "exthost" / "window1" / "github.copilot-chat"
    log_dir.mkdir(parents=True)
    line = '[2026-05-28 10:00:01] {"name":"read_file","input":{"file_path":"a.py"}}'
    (log_dir / "copilot.log").write_text(f"{line}\n{line}\n")

    old_base = copilot_tailer._CODE_LOG_BASE
    copilot_tailer._CODE_LOG_BASE = base
    try:
        events = copilot_tailer.scan_logs(max_log_dirs=1)
    finally:
        copilot_tailer._CODE_LOG_BASE = old_base

    assert len(events) == 1
