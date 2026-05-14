"""GitHub Copilot log tailer: extracts tool calls from VS Code logs.

GitHub Copilot's agent mode logs tool calls in VS Code extension host logs:
    ~/.config/Code/logs/<session>/exthost/window<X>/github.copilot-chat/

On macOS:  ~/Library/Application Support/Code/logs/...
On Windows: %APPDATA%/Code/logs/...

Usage:
    from causetrace.hooks.copilot_tailer import scan_logs
    events = scan_logs()
"""
from __future__ import annotations

import json
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from causetrace.core import ToolEvent, TraceRecorder
from causetrace.causality import infer_relations

# Detect OS-specific VS Code log path
_system = platform.system().lower()
if _system == "darwin":
    _CODE_LOG_BASE = Path.home() / "Library" / "Application Support" / "Code" / "logs"
elif _system == "windows":
    _CODE_LOG_BASE = Path.home() / "AppData" / "Roaming" / "Code" / "logs"
else:
    _CODE_LOG_BASE = Path.home() / ".config" / "Code" / "logs"

# Copilot extension identifiers in VS Code
_COPILOT_EXT_DIRS = [
    "github.copilot-chat",
    "GitHub.copilot-chat",
    "github.copilot",
    "GitHub.copilot",
]

# Patterns to identify tool calls in Copilot log lines
_TOOL_CALL_PATTERNS = [
    re.compile(
        r'\[tool_call\]\s*(?:\{.*?"name"\s*:\s*"(\w+)".*?"input".*?)?', re.DOTALL
    ),
    re.compile(
        r"(?:tool_call|tool_use|function_call)\s*[:=]\s*(\w+)", re.IGNORECASE
    ),
    re.compile(
        r'"tool"\s*:\s*"(\w+)"', re.IGNORECASE
    ),
    re.compile(
        r"running\s+(?:tool|command|step)\s*[:\s]+(\w+)", re.IGNORECASE
    ),
]

# Map Copilot tool names to causetrace names
_TOOL_MAP: Dict[str, str] = {
    "read_file": "Read",
    "read": "Read",
    "view": "Read",
    "write_file": "Write",
    "write": "Write",
    "create_file": "Write",
    "edit_file": "Edit",
    "edit": "Edit",
    "run_in_terminal": "Bash",
    "run_terminal": "Bash",
    "bash": "Bash",
    "command": "Bash",
    "terminal": "Bash",
    "search": "Grep",
    "grep": "Grep",
    "glob": "Glob",
    "file_search": "Grep",
    "web_fetch": "WebFetch",
    "fetch_webpage": "WebFetch",
    "fetch": "WebFetch",
    "web_search": "WebSearch",
    "simple_browser": "WebFetch",
    "install_extension": "Extension",
    "open": "Read",
    "list": "Glob",
    "list_dir": "Glob",
    "status": "Bash",
    "diff": "Read",
    "apply_diff": "Edit",
}


def _normalize_tool(name: str) -> str:
    """Map Copilot tool names to causetrace tool names."""
    key = name.lower().strip()
    return _TOOL_MAP.get(key, name)


def _find_log_dirs() -> List[Path]:
    """Find VS Code log directories, newest first."""
    if not _CODE_LOG_BASE.exists():
        return []
    dirs = sorted(
        (d for d in _CODE_LOG_BASE.iterdir() if d.is_dir()),
        reverse=True,
    )
    return dirs


def _find_copilot_logs(max_log_dirs: int = 3) -> List[Path]:
    """Find Copilot extension log files from recent VS Code sessions."""
    log_files: List[Path] = []

    for log_dir in _find_log_dirs()[:max_log_dirs]:
        ext_host_dir = log_dir / "exthost"
        if not ext_host_dir.exists():
            continue

        for window_dir in sorted(ext_host_dir.iterdir()):
            if not window_dir.is_dir():
                continue
            for ext_name in _COPILOT_EXT_DIRS:
                ext_dir = window_dir / ext_name
                if ext_dir.exists():
                    for f in ext_dir.iterdir():
                        if f.is_file() and f.suffix in (".log", ""):
                            log_files.append(f)

    return log_files


def _parse_log_line(line: str) -> Optional[Tuple[str, dict, str]]:
    """Extract (tool_name, tool_input, tool_output) from a single log line.

    Returns None if the line doesn't contain a tool call.
    """
    line_stripped = line.strip()

    # Try to find embedded JSON
    json_match = re.search(r"\{.*\}", line_stripped)
    data = {}
    if json_match:
        try:
            data = json.loads(json_match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    if data:
        tool_name = data.get("name") or data.get("tool") or data.get("function") or ""
        if tool_name:
            inp = data.get("input") or data.get("arguments") or data.get("args") or {}
            out = data.get("output") or data.get("result") or ""
            return _normalize_tool(str(tool_name)), inp if isinstance(inp, dict) else {"text": str(inp)[:2000]}, str(out)[:2000]

    # Try pattern matching on the line
    for pattern in _TOOL_CALL_PATTERNS:
        m = pattern.search(line_stripped)
        if m:
            tool_name = m.group(1)
            return _normalize_tool(tool_name), {"raw": line_stripped[:300]}, ""

    return None


def _parse_timestamp_from_line(line: str) -> Optional[str]:
    """Extract timestamp from a VS Code log line."""
    # VS Code log format: [YYYY-MM-DD HH:MM:SS.mmm] [...]
    ts_match = re.match(r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line)
    if ts_match:
        try:
            dt = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except ValueError:
            return ts_match.group(1)
    return None


def scan_logs(max_log_dirs: int = 3) -> List[ToolEvent]:
    """Scan GitHub Copilot logs and extract all tool calls as ToolEvents.

    Args:
        max_log_dirs: Number of most recent VS Code log directories to scan.

    Returns:
        List of ToolEvents with inferred causal relations.
    """
    log_files = _find_copilot_logs(max_log_dirs=max_log_dirs)
    events: List[ToolEvent] = []
    seen: set = set()

    for f in log_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in content.splitlines():
            result = _parse_log_line(line)
            if result is None:
                continue

            tool_name, tool_input, tool_output = result
            if not tool_name:
                continue

            # Deduplicate
            dedup_key = f"{tool_name}:{str(tool_input.get('raw', str(tool_input)))[:80]}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            timestamp = _parse_timestamp_from_line(line)

            event = ToolEvent(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output or None,
                timestamp=timestamp,
                agent="copilot",
            )
            events.append(event)

    infer_relations(events)
    return events


def scan_session(
    session_label: str = "copilot_latest",
) -> Tuple[str, List[ToolEvent]]:
    """Convenience: scan Copilot logs and save as a causetrace session.

    Returns (session_id, events) with inferred causality.
    """
    events = scan_logs()
    if not events:
        return ("", [])

    recorder = TraceRecorder()
    for ev in events:
        recorder.record(ev)
    return recorder.session_id, events
