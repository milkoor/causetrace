"""First-run demo data and Claude Code hook configuration helpers."""
from __future__ import annotations

import json
import shlex
import shutil
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .core import JSONStore, ToolEvent


def create_demo_session(store: JSONStore) -> tuple[str, list[ToolEvent], str]:
    """Create a saved causal DAG that can be inspected immediately."""
    suffix = uuid.uuid4().hex[:6]
    session_id = datetime.now(timezone.utc).strftime("demo_%Y%m%d_%H%M%S_") + suffix
    started = datetime.now(timezone.utc).replace(microsecond=0)
    specs = [
        ("demo-read-main", "Read", {"file_path": "src/main.py"}, None, "user_request"),
        ("demo-grep-fixme", "Grep", {"pattern": "FIXME"}, "demo-read-main", "investigation"),
        ("demo-read-utils", "Read", {"file_path": "src/utils.py"}, "demo-grep-fixme", "investigation"),
        ("demo-read-test", "Read", {"file_path": "tests/test_utils.py"}, None, "user_request"),
        (
            "demo-edit-fix",
            "Edit",
            {"file_path": "src/utils.py", "change": "range(n+1) -> range(n)"},
            "demo-read-utils,demo-read-test",
            "task_execution",
        ),
        (
            "demo-verify-fix",
            "Bash",
            {"command": "python -m pytest tests/ -x"},
            "demo-edit-fix",
            "verification",
        ),
    ]
    events: list[ToolEvent] = []
    for i, (event_id, name, tool_input, parent, reason) in enumerate(specs):
        event = ToolEvent(
            event_id=event_id,
            session_id=session_id,
            agent="demo",
            tool_name=name,
            tool_input=tool_input,
            tool_output="ok",
            parent_event_id=parent,
            caused_by=reason,
            timestamp=(started + timedelta(seconds=i)).isoformat(),
        )
        store.append(session_id, event)
        events.append(event)
    return session_id, events, "demo-verify-fix"


def claude_hook_command() -> str:
    """Return the installed interpreter command used in Claude settings."""
    return f"{shlex.quote(sys.executable)} -m causetrace.hooks.claude_code"


def install_claude_hook(settings_path: Path | None = None) -> tuple[Path, bool]:
    """Install causetrace PreToolUse/PostToolUse hooks without replacing others."""
    path = settings_path or Path.home() / ".claude" / "settings.json"
    settings = _load_settings(path)
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"Expected an object at hooks in {path}")

    changed = False
    for event_name in ("PreToolUse", "PostToolUse"):
        entries = hooks.setdefault(event_name, [])
        if not isinstance(entries, list):
            raise ValueError(f"Expected a list at hooks.{event_name} in {path}")
        if not any(_contains_managed_hook(entry) for entry in entries):
            entries.append(_hook_entry())
            changed = True

    if changed:
        _write_settings(path, settings)
    return path, changed


def uninstall_claude_hook(settings_path: Path | None = None) -> tuple[Path, bool]:
    """Remove only causetrace-managed Claude Code hooks."""
    path = settings_path or Path.home() / ".claude" / "settings.json"
    settings = _load_settings(path)
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"Expected an object at hooks in {path}")

    changed = False
    for event_name in ("PreToolUse", "PostToolUse"):
        entries = hooks.get(event_name)
        if not isinstance(entries, list):
            continue
        retained: list[Any] = []
        event_changed = False
        for entry in entries:
            updated, removed = _remove_managed_hooks(entry)
            changed = changed or removed
            event_changed = event_changed or removed
            if updated is not None:
                retained.append(updated)
        if not event_changed:
            continue
        if retained:
            hooks[event_name] = retained
        else:
            hooks.pop(event_name, None)

    if changed:
        _write_settings(path, settings)
    return path, changed


def _hook_entry() -> dict[str, Any]:
    return {
        "matcher": "*",
        "hooks": [{
            "type": "command",
            "command": claude_hook_command(),
            "timeout": 5,
        }],
    }


def _is_managed_command(command: Any) -> bool:
    if not isinstance(command, str):
        return False
    return (
        "causetrace.hooks.claude_code" in command
        or "causetrace/hooks/claude_code.py" in command
    )


def _contains_managed_hook(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    nested = entry.get("hooks", [])
    return isinstance(nested, list) and any(
        isinstance(item, dict) and _is_managed_command(item.get("command"))
        for item in nested
    )


def _remove_managed_hooks(entry: Any) -> tuple[Any | None, bool]:
    if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
        return entry, False
    nested = entry["hooks"]
    retained = [
        item for item in nested
        if not (isinstance(item, dict) and _is_managed_command(item.get("command")))
    ]
    if len(retained) == len(nested):
        return entry, False
    if not retained:
        return None, True
    updated = dict(entry)
    updated["hooks"] = retained
    return updated, True


def _load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Cannot parse Claude settings file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _write_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + ".causetrace.bak")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    temporary = path.with_name(path.name + ".causetrace.tmp")
    temporary.write_text(json.dumps(settings, indent=2) + "\n")
    temporary.replace(path)
