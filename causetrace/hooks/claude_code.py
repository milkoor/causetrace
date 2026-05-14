"""Claude Code Hook bridge: captures tool calls with causal tracking.

PreToolUse → save start time + parent_event_id
PostToolUse → calculate duration, record event with causal link
"""
import json
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from causetrace.core import TraceRecorder

_ACTIVE_DIR = Path.home() / ".causetrace" / "active"
_CC_MODEL = os.environ.get("ANTHROPIC_MODEL", "") or "unknown"
_CC_PROVIDER = "anthropic"


def main() -> None:
    raw = sys.stdin.read()
    if not raw:
        sys.exit(0)
    try:
        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event_name = hook_input.get("hook_event_name", "")
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "unknown")

    if event_name == "PreToolUse":
        _save_pre(session_id, tool_name)
        result = {
            "hookSpecificOutput": {"permissionDecision": "allow", "hookEventName": "PreToolUse"},
            "systemMessage": "[causetrace] Recording tool call",
        }
        json.dump(result, sys.stdout)
        return

    if event_name == "PostToolUse":
        pre_data = _load_pre(session_id, tool_name)
        if pre_data is None:
            json.dump({"continue": True}, sys.stdout)
            return

        duration = (time.time() - pre_data["start_time"]) * 1000
        parent_id = pre_data.get("parent_event_id")
        tool_result = hook_input.get("tool_result", {})

        recorder = TraceRecorder(session_id=session_id)
        event = recorder.record_call(
            tool_name=tool_name,
            tool_input=_shorten_input(tool_input),
            tool_output=_shorten_output(tool_result),
            parent_event_id=parent_id,
            model=_CC_MODEL,
            provider=_CC_PROVIDER,
            duration_ms=duration,
        )
        _save_last_event_id(session_id, event.event_id)

    json.dump({"continue": True}, sys.stdout)


def _save_pre(session_id: str, tool_name: str) -> None:
    _ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "start_time": time.time(),
        "parent_event_id": _load_last_event_id(session_id),
    }
    (_ACTIVE_DIR / f"{session_id}_{tool_name}.pre").write_text(json.dumps(data))


def _load_pre(session_id: str, tool_name: str) -> dict | None:
    path = _ACTIVE_DIR / f"{session_id}_{tool_name}.pre"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        path.unlink()
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _last_event_id_path(session_id: str) -> Path:
    return _ACTIVE_DIR / f"{session_id}_last_event_id"


def _load_last_event_id(session_id: str) -> str | None:
    path = _last_event_id_path(session_id)
    try:
        return path.read_text().strip()
    except (FileNotFoundError, OSError):
        return None


def _save_last_event_id(session_id: str, event_id: str) -> None:
    if event_id:
        _ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
        _last_event_id_path(session_id).write_text(event_id)


def _shorten_input(inp: dict) -> dict:
    keep_keys = {"command", "file_path", "pattern", "url", "query",
                 "old_string", "new_string", "tool_slug", "arguments", "prompt"}
    return {k: v for k, v in inp.items() if k in keep_keys}


def _shorten_output(out: dict) -> dict | str:
    if isinstance(out, dict) and "output" in out:
        return str(out["output"])[:500]
    return str(out)[:500]


if __name__ == "__main__":
    main()
