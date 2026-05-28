from __future__ import annotations

import json
from pathlib import Path

import causetrace.hooks.codex_tailer as codex_tailer


def test_codex_tailer_preserves_distinct_call_ids(tmp_path: Path) -> None:
    session_dir = tmp_path / "sessions" / "2026" / "05" / "28"
    session_dir.mkdir(parents=True)
    (session_dir / "rollout-1.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-05-28T10:00:01",
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "name": "exec_command",
                            "arguments": '{"cmd":"echo hello"}',
                            "call_id": "call_a",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-05-28T10:00:02",
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "name": "exec_command",
                            "arguments": '{"cmd":"echo hello"}',
                            "call_id": "call_b",
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    old_home = codex_tailer.CODEX_HOME
    old_session_dir = codex_tailer._SESSION_DIR
    codex_tailer.CODEX_HOME = tmp_path
    codex_tailer._SESSION_DIR = tmp_path / "sessions"
    try:
        events = codex_tailer.scan_logs(max_sessions=1)
    finally:
        codex_tailer.CODEX_HOME = old_home
        codex_tailer._SESSION_DIR = old_session_dir

    assert len(events) == 2
    assert [ev.timestamp for ev in events] == [
        "2026-05-28T10:00:01",
        "2026-05-28T10:00:02",
    ]


def test_codex_tailer_dedups_exact_duplicate_rows(tmp_path: Path) -> None:
    session_dir = tmp_path / "sessions" / "2026" / "05" / "28"
    session_dir.mkdir(parents=True)
    line = json.dumps(
        {
            "timestamp": "2026-05-28T10:00:01",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": '{"cmd":"echo hello"}',
                "call_id": "call_a",
            },
        }
    )
    (session_dir / "rollout-1.jsonl").write_text(f"{line}\n{line}\n")

    old_home = codex_tailer.CODEX_HOME
    old_session_dir = codex_tailer._SESSION_DIR
    codex_tailer.CODEX_HOME = tmp_path
    codex_tailer._SESSION_DIR = tmp_path / "sessions"
    try:
        events = codex_tailer.scan_logs(max_sessions=1)
    finally:
        codex_tailer.CODEX_HOME = old_home
        codex_tailer._SESSION_DIR = old_session_dir

    assert len(events) == 1


def test_codex_tailer_preserves_distinct_old_format_actions(tmp_path: Path) -> None:
    session_dir = tmp_path / "sessions" / "2026" / "05" / "28"
    session_dir.mkdir(parents=True)
    (session_dir / "rollout-1.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-05-28T10:00:01",
                        "type": "action",
                        "action": {
                            "name": "read_file",
                            "input": {"file_path": "a.py"},
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-05-28T10:00:02",
                        "type": "action",
                        "action": {
                            "name": "read_file",
                            "input": {"file_path": "a.py"},
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    old_home = codex_tailer.CODEX_HOME
    old_session_dir = codex_tailer._SESSION_DIR
    codex_tailer.CODEX_HOME = tmp_path
    codex_tailer._SESSION_DIR = tmp_path / "sessions"
    try:
        events = codex_tailer.scan_logs(max_sessions=1)
    finally:
        codex_tailer.CODEX_HOME = old_home
        codex_tailer._SESSION_DIR = old_session_dir

    assert len(events) == 2
    assert [ev.timestamp for ev in events] == [
        "2026-05-28T10:00:01",
        "2026-05-28T10:00:02",
    ]
