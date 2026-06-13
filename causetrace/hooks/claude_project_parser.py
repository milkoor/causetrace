"""Claude Code project session parser: extracts thinking + tool_use from JSONL.

Claude Code stores full session history at:
  ~/.claude/projects/<project_path>/<sessionId>.jsonl

Each line contains a message in Anthropic Messages API format with
content blocks that include thinking (model reasoning), tool_use,
tool_result, and text. This parser extracts those blocks and creates
causally-linked ToolEvents.

Usage:
    from causetrace.hooks.claude_project_parser import parse_session
    events = parse_session("session_id")
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from causetrace.core import ToolEvent

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def _find_session_file(session_id: str) -> Optional[Path]:
    """Find the project JSONL file for a given session ID.

    Searches all project directories under ~/.claude/projects/.
    Returns the first match or None.
    """
    if not PROJECTS_DIR.exists():
        return None

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        target = project_dir / f"{session_id}.jsonl"
        if target.exists():
            return target

    return None


def _parse_block(block: dict, idx: int) -> dict:
    """Normalize a content block into a standard dict."""
    btype = block.get("type", "unknown")
    result: dict = {"type": btype, "index": idx}

    if btype == "thinking":
        result["content"] = block.get("thinking", "")
        result["signature"] = block.get("signature")
    elif btype == "tool_use":
        result["tool_name"] = block.get("name", "")
        result["tool_input"] = block.get("input", {})
        result["tool_use_id"] = block.get("id", "")
    elif btype == "tool_result":
        result["tool_use_id"] = block.get("tool_use_id", "")
        result["content"] = _serialize_tool_result(block.get("content", ""))
    elif btype == "text":
        result["content"] = block.get("text", "")
    else:
        result["content"] = str(block)

    return result


def _serialize_tool_result(content: Any) -> str:
    """Serialize tool result to string."""
    if isinstance(content, str):
        return content[:2000]
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", json.dumps(item)))
            else:
                parts.append(str(item))
        return "\n".join(parts)[:2000]
    return str(content)[:2000]


def list_sessions() -> List[Dict[str, Any]]:
    """List all sessions found in project JSONL files with metadata."""
    sessions: List[Dict[str, Any]] = []
    if not PROJECTS_DIR.exists():
        return sessions

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        for f in sorted(project_dir.glob("*.jsonl")):
            if f.stem == "memory":
                continue
            # Count lines for a quick size estimate
            try:
                line_count = sum(1 for _ in f.open())
            except OSError:
                line_count = 0
            sessions.append({
                "session_id": f.stem,
                "project": project_dir.name,
                "path": str(f),
                "lines": line_count,
            })

    return sessions


def _detect_provider(model: Optional[str]) -> str:
    """Infer LLM provider from model name."""
    if not model:
        return "anthropic"
    m = model.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("deepseek"):
        return "deepseek"
    if m.startswith("ark-") or m.startswith("doubao"):
        return "bytedance"
    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        return "openai"
    if m.startswith("minimax"):
        return "minimax"
    return "anthropic"


def parse_session(session_id: str) -> List[ToolEvent]:
    """Parse a Claude Code project session JSONL into causally-linked events.

    Extracts thinking, tool_use, and tool_result blocks from the session
    file and creates ToolEvents with parent_event_id chains.

    Returns:
        List of ToolEvents in chronological order, with causal links.
    """
    path = _find_session_file(session_id)
    if not path:
        return []

    with open(path) as f:
        raw_lines = [line for line in f if line.strip()]

    events: List[ToolEvent] = []
    last_event_id: Optional[str] = None

    for line in raw_lines:
        obj = json.loads(line)
        msg = obj.get("message", {})
        content = msg.get("content", [])

        for block in content:
            if not isinstance(block, dict):
                continue

            parsed = _parse_block(block, 0)
            btype = parsed["type"]

            if btype == "thinking":
                event = ToolEvent(
                    tool_name="Thinking",
                    tool_input={"content": parsed["content"]},
                    event_type="reasoning",
                    parent_event_id=last_event_id,
                    timestamp=obj.get("timestamp"),
                    model=msg.get("model"),
                    provider=_detect_provider(msg.get("model")),
                    agent="claude-code",
                )
                events.append(event)
                last_event_id = event.event_id

            elif btype == "tool_use":
                tool_input = parsed.get("tool_input", {})
                # Map the description or key params as display-friendly input
                display_input = _shorten_tool_input(tool_input)
                event = ToolEvent(
                    tool_name=parsed["tool_name"],
                    tool_input=display_input,
                    event_type="tool_call",
                    parent_event_id=last_event_id,
                    timestamp=obj.get("timestamp"),
                    model=msg.get("model"),
                    provider=_detect_provider(msg.get("model")),
                    agent="claude-code",
                )
                events.append(event)
                last_event_id = event.event_id

            elif btype == "text":
                text = parsed.get("content", "")
                if text.strip():
                    event = ToolEvent(
                        tool_name="Response",
                        tool_input={"text": text[:500]},
                        event_type="reasoning",
                        parent_event_id=last_event_id,
                        timestamp=obj.get("timestamp"),
                        model=msg.get("model"),
                        provider=_detect_provider(msg.get("model")),
                        agent="claude-code",
                    )
                    events.append(event)
                    last_event_id = event.event_id

    return events


def _shorten_tool_input(inp: dict) -> dict:
    """Keep only the most informative fields from tool input."""
    keep = {"command", "file_path", "pattern", "url", "query",
            "old_string", "new_string", "content", "description",
            "name", "arguments"}
    return {k: v for k, v in inp.items() if k in keep}


def scan_session(session_id: str) -> Tuple[str, List[ToolEvent]]:
    """Parse a Claude Code project session and return (session_id, events)."""
    events = parse_session(session_id)
    return session_id, events
