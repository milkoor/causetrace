"""Aider bridge: runs aider as a subprocess and captures tool calls.

Works by running `aider` as a subprocess and watching its output for
tool call patterns (file edits, bash commands, file reads).

Usage:
    python -m causetrace.hooks.aider_bridge [aider args...]

    # or via CLI:
    causetrace aider -- --model gpt-4 --yes "fix the bug"
"""
from __future__ import annotations

import re
import sys
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from causetrace.core import TraceRecorder


# Patterns to identify tool calls in aider's standard output
_TOOL_PATTERNS = {
    "Bash": re.compile(
        r"^\$\s+(.+)$", re.MULTILINE
    ),
    "Edit": re.compile(
        r"^Applied\s+edit\s+to\s+(.+)$", re.MULTILINE | re.IGNORECASE
    ),
    "Create": re.compile(
        r"^Created\s+(.+)$", re.MULTILINE | re.IGNORECASE
    ),
    "Read": re.compile(
        r"^Reading\s+(.+)$", re.MULTILINE | re.IGNORECASE
    ),
}

# History file path (relative to repo or cwd)
_HISTORY_FILE = ".aider.chat.history.md"


def _parse_line(recorder: TraceRecorder, line: str) -> None:
    """Try to extract a tool call from a single line of aider output."""
    for tool_name, pattern in _TOOL_PATTERNS.items():
        m = pattern.match(line.strip())
        if m:
            recorder.record_call(
                tool_name=tool_name,
                tool_input=m.group(1).strip()[:500],
                agent="aider",
            )
            return


def _parse_history(recorder: TraceRecorder, history_path: Path) -> None:
    """Parse aider chat history for tool call patterns.

    The history file contains Markdown with code blocks and tool outputs.
    We look for known indicators like shell commands, file diffs, etc.
    """
    if not history_path.exists():
        return

    content = history_path.read_text(encoding="utf-8", errors="replace")

    # Bash commands: lines starting with ```bash ... ```
    bash_pattern = re.compile(r"```bash\n(.+?)\n```", re.DOTALL)
    for m in bash_pattern.finditer(content):
        cmd = m.group(1).strip()
        if cmd:
            recorder.record_call(
                tool_name="Bash",
                tool_input=cmd[:500],
                agent="aider",
            )

    # File edits: diff-style sections
    edit_pattern = re.compile(r"```diff.*?\n(.+?)\n```", re.DOTALL)
    edits = edit_pattern.findall(content)
    for edit in edits[:10]:  # limit to avoid noise
        recorder.record_call(
            tool_name="Edit",
            tool_input=edit[:500],
            agent="aider",
        )


def run_with_tracing(
    aider_args: list[str],
    session_id: Optional[str] = None,
) -> TraceRecorder:
    """Run aider as a subprocess and capture tool calls from output.

    Args:
        aider_args: Arguments to pass to the aider CLI (e.g. ["--model", "gpt-4", "--yes"]).
        session_id: Optional session ID. Auto-generated if not provided.

    Returns:
        TraceRecorder with captured events.

    Raises:
        SystemExit: If aider is not installed.
    """
    recorder = TraceRecorder(
        session_id=session_id or f"aider_{uuid.uuid4().hex[:8]}",
    )
    cmd = ["aider"] + aider_args

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print(
            "Error: aider is not installed. Run: pip install aider-chat",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[causetrace] Running: {' '.join(cmd)}", file=sys.stderr)
    print(f"[causetrace] Session: {recorder.session_id}", file=sys.stderr)

    for line in proc.stdout:
        print(line, end="", flush=True)
        _parse_line(recorder, line)

    proc.wait()

    # Also parse the history file for any missed tool calls
    _parse_history(recorder, Path.cwd() / _HISTORY_FILE)

    events = recorder.events
    print(
        f"\n[causetrace] Captured {len(events)} tool calls "
        f"(session: {recorder.session_id})",
        file=sys.stderr,
    )
    return recorder


def patch_coder(
    recorder: Optional[TraceRecorder] = None,
) -> TraceRecorder:
    """Patch aider's Coder class to capture tool calls.

    This wraps `Coder.send()` to intercept LLM interactions and extract
    tool calls. Works with aider v0.40+.

    Args:
        recorder: Optional existing recorder. A new one is created if omitted.

    Returns:
        The TraceRecorder instance.

    Raises:
        ImportError: If aider is not installed.
    """
    try:
        from aider.coders import Coder
    except ImportError:
        raise ImportError("aider is not installed. Run: pip install aider-chat")

    recorder = recorder or TraceRecorder(
        session_id=f"aider_{uuid.uuid4().hex[:8]}",
    )

    import functools

    original_send = Coder.send

    @functools.wraps(original_send)
    def patched_send(self, *args, **kwargs):
        result = original_send(self, *args, **kwargs)

        # Try to capture tool calls from chat_history
        try:
            for msg in getattr(self, "chat_history", [])[-5:]:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "")
                if role == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        fn = getattr(tc, "function", None) or {}
                        recorder.record_call(
                            tool_name=getattr(fn, "name", str(fn)),
                            tool_input=getattr(fn, "arguments", str(tc)),
                            agent="aider",
                        )
        except Exception:
            pass

        return result

    Coder.send = patched_send
    return recorder


if __name__ == "__main__":
    run_with_tracing(sys.argv[1:])
