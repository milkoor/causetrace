"""DeepSeek Harness (DSH) session parser: extracts native causal structure.

DSH stores each agent session as an append-only JSONL log (zstd-compressed
stream frames) at:

    ~/.dsh/sessions/<workspace-slug>/<session-id>/session.jsonl.zstd

Unlike file-tailing runtimes, DSH persists *first-class causal metadata*, so
this parser does not need heuristic chaining:

    turn/start ──┐
    user/message ├─ turn 1 ──► step (turn,1) ──► step (turn,2) ──► turn/end
    step/start   │                │                 │
    assistant/   │                │ reasoning/text  │
    message      │                │                 │
    tool/call    │                │ N parallel calls│
    tool/result  │                │ paired callId   │

Record vocabulary (observed in real sessions, DSH >= current npx build):

    {"type":"session","id":"session-…","createdAt":<ms>,"cwd":…,"agentPreset":…}
    {"type":"user/message","data":{"content":[…],"source":{"kind":"user"}}}
    {"type":"assistant/message","data":{"turn":T,"step":S,"message":{"content":[
        {"type":"reasoning"|"text"|"tool-call", …}]}}}
    {"type":"tool/call","data":{"turn":T,"step":S,"callId":…,"name":…,"arguments":"<json str>"}}
    {"type":"tool/result","data":{"message":{"source":{"callId":…},"content":[
        {"type":"tool-result","content":[{"type":"text","text":…}],"isError":b}]}}}
    {"type":"command/run","data":{"commandId":…,"name":…,"args":…}}
    {"type":"command/done","data":{"commandId":…,"kind":…,"text":…}}
    {"type":"request/header","data":{"header":{"config":{"provider":…,"model":…}}}}
    {"type":"model/selection","data":{"provider":…,"model":…}}

Streaming fragments (``assistant/chunk``, ``reasoning-chunks``, ``text-chunks``,
``tool-call-chunks``) are redundant with the settled ``*/message``/``*/call``
records and are skipped.

Causal fidelity:
    - a user message is the root of its turn (``user_input``)
    - all tool calls issued in one step share the step's reasoning event as
      parent (fan-out), or the step's causal parent when the model emitted
      calls without visible reasoning
    - the first event of the next step is parented by *every* tool call of the
      previous step via comma-separated ``parent_event_id`` (fan-in), because
      their joint results are what the next model request consumes
    - tool results are merged back into their call event (output + measured
      duration), never as separate events — same convention as codex_parser
    - slash commands become ``context_update`` events (schema-approved type)

Sub-agents run as separate DSH session directories (``delegationDepth`` in the
header) and are parsed independently; cross-session delegation links are not
invented, per the fidelity-over-coverage principle.

Usage:
    from causetrace.hooks.dsh_parser import parse_session
    events = parse_session("session-c3613e12-…")
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from causetrace.core import ToolEvent

DSH_HOME = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh"))
SESSIONS_DIR = DSH_HOME / "sessions"

AGENT_NAME = "dsh"

# Settled record types we consume; streaming chunk records are ignored.
_SESSION = "session"
_USER_MESSAGE = "user/message"
_ASSISTANT_MESSAGE = "assistant/message"
_TOOL_CALL = "tool/call"
_TOOL_RESULT = "tool/result"
_COMMAND_RUN = "command/run"
_COMMAND_DONE = "command/done"
_REQUEST_HEADER = "request/header"
_MODEL_SELECTION = "model/selection"
_SESSION_TITLE = "session/title"


# ---------------------------------------------------------------------------
# session file discovery


def set_sessions_dir(path: Path) -> None:
    """Override the sessions root (e.g. a backup home like ~/.dsh-backup).

    Accepts either a DSH home directory (containing ``sessions/``) or the
    sessions directory itself.
    """
    global SESSIONS_DIR
    p = Path(path).expanduser()
    if (p / "sessions").is_dir():
        p = p / "sessions"
    SESSIONS_DIR = p


def _session_files() -> List[Path]:
    """All DSH session log files, newest first (plain JSONL or zstd)."""
    if not SESSIONS_DIR.exists():
        return []
    files: List[Path] = []
    for workspace in sorted(SESSIONS_DIR.iterdir()):
        if not workspace.is_dir():
            continue
        for sess in sorted(workspace.iterdir()):
            if not sess.is_dir():
                continue
            for name in ("session.jsonl.zstd", "session.jsonl"):
                f = sess / name
                if f.exists():
                    files.append(f)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def find_session_file(session_id: str) -> Optional[Path]:
    """Locate the session log for a DSH session ID (exact, prefix, or contains)."""
    candidates = _session_files()
    for f in candidates:
        dir_name = f.parent.name
        if dir_name == session_id or f.stem == session_id:
            return f
    for f in candidates:
        dir_name = f.parent.name
        if dir_name.startswith(session_id) or session_id in dir_name:
            return f
    return None


# ---------------------------------------------------------------------------
# decompression helpers


def _read_text(path: Path, max_bytes: int = 0) -> str:
    """Read a session log, transparently decompressing .zstd files.

    Live sessions may end in an incomplete zstd frame; whatever decoded
    successfully is returned. ``max_bytes`` (when > 0) bounds the *decompressed*
    size for cheap peeking.
    """
    if path.suffix != ".zstd":
        with open(path, "rb") as f:
            data = f.read(max_bytes) if max_bytes else f.read()
        return data.decode("utf-8", "replace")

    chunks: List[bytes] = []
    total = 0
    try:
        import zstandard  # optional dependency, lazy

        with open(path, "rb") as f:
            reader = zstandard.ZstdDecompressor().stream_reader(f)
            try:
                while True:
                    block = reader.read(1 << 20)
                    if not block:
                        break
                    chunks.append(block)
                    total += len(block)
                    if max_bytes and total >= max_bytes:
                        break
            except Exception:
                # Truncated / in-flight frame: keep what we have.
                pass
    except ImportError:
        try:
            proc = subprocess.run(
                ["zstd", "-dc", str(path)],
                capture_output=True,
                timeout=30,
            )
            chunks.append(proc.stdout[:max_bytes] if max_bytes else proc.stdout)
        except (OSError, subprocess.SubprocessError):
            return ""
    return b"".join(chunks).decode("utf-8", "replace")


def load_records(path: Path) -> List[Dict[str, Any]]:
    """Parse all JSONL records from a session log (skipping malformed lines)."""
    records: List[Dict[str, Any]] = []
    for line in _read_text(path).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("type"):
            records.append(obj)
    return records


def _record_data(obj: Dict[str, Any]) -> Dict[str, Any]:
    data = obj.get("data")
    return data if isinstance(data, dict) else {}


def _ms_to_iso(ms: Any) -> Optional[str]:
    """DSH record timestamps are epoch milliseconds."""
    if not isinstance(ms, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def _detect_provider(model: Optional[str], route: Optional[str]) -> str:
    """Prefer a recognizable provider from the model name; fall back to the DSH route id."""
    m = (model or "").lower()
    if "claude" in m:
        return "anthropic"
    if "deepseek" in m:
        return "deepseek"
    if "gpt" in m or m.startswith("o1") or m.startswith("o3") or m.startswith("o4"):
        return "openai"
    if "gemini" in m:
        return "google"
    if "qwen" in m:
        return "alibaba"
    if "glm" in m:
        return "zhipu"
    if "kimi" in m or "moonshot" in m:
        return "moonshot"
    if "doubao" in m or "seed" in m:
        return "bytedance"
    if "minimax" in m:
        return "minimax"
    if "mistral" in m:
        return "mistral"
    if "llama" in m:
        return "meta"
    return route or ""


def _blocks_text(content: Any, limit: int = 2000) -> str:
    """Join the text parts of a DSH content-block list."""
    if isinstance(content, str):
        return content[:limit]
    parts: List[str] = []
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
    return "\n".join(parts)[:limit]


# ---------------------------------------------------------------------------
# listing


def list_sessions(max_peek_bytes: int = 2_000_000) -> List[Dict[str, Any]]:
    """List DSH sessions with cheap header/title peeking (newest first)."""
    sessions: List[Dict[str, Any]] = []
    for f in _session_files():
        meta: Dict[str, Any] = {
            "session_id": f.parent.name,
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "title": None,
            "model": None,
            "cwd": None,
            "created": None,
        }
        try:
            text = _read_text(f, max_bytes=max_peek_bytes)
        except OSError:
            text = ""
        for line in text.splitlines():
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = obj.get("type")
            if t == _SESSION:
                meta["session_id"] = obj.get("id") or meta["session_id"]
                meta["cwd"] = obj.get("cwd")
                meta["created"] = _ms_to_iso(obj.get("createdAt"))
            elif t == _SESSION_TITLE:
                meta["title"] = _record_data(obj).get("title")
            elif t == _REQUEST_HEADER and not meta["model"]:
                cfg = (_record_data(obj).get("header") or {}).get("config") or {}
                meta["model"] = cfg.get("model")
            elif t == _MODEL_SELECTION and not meta["model"]:
                meta["model"] = _record_data(obj).get("model")
            if meta["title"] and meta["model"]:
                break
        sessions.append(meta)
    return sessions


# ---------------------------------------------------------------------------
# parsing


def parse_session(session_id: str) -> List[ToolEvent]:
    """Parse a DSH session into causally-linked ToolEvents.

    Returns events in chronological order. Parallel tool calls in one step
    fan-out from the step's reasoning event; the next step fans-in on all of
    those calls via comma-separated parent_event_id.
    """
    path = find_session_file(session_id)
    if not path:
        return []
    records = load_records(path)
    if not records:
        return []

    events: List[ToolEvent] = []
    calls_by_id: Dict[str, ToolEvent] = {}   # DSH callId -> event
    cmds_by_id: Dict[str, ToolEvent] = {}    # DSH commandId -> event
    call_times: Dict[str, int] = {}          # DSH callId -> call record ms

    model: Optional[str] = None
    route: Optional[str] = None

    user_root_id: Optional[str] = None       # latest user_input event
    prev_refs: List[str] = []                # events causing the next step head
    current_key: Optional[Tuple[int, int]] = None
    step_head: Dict[Tuple[int, int], str] = {}     # step -> first event
    step_calls: Dict[Tuple[int, int], List[str]] = {}  # step -> call events

    def add(event: ToolEvent) -> ToolEvent:
        events.append(event)
        return event

    def step_key(data: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        turn = data.get("turn")
        step = data.get("step")
        if not isinstance(turn, int) or not isinstance(step, int):
            return None
        return (turn, step)

    def finalize_step(key: Optional[Tuple[int, int]]) -> None:
        """When leaving a step, its calls (or its head) cause the next step."""
        nonlocal prev_refs
        if key is None:
            return
        refs = step_calls.get(key)
        if refs:
            prev_refs = list(refs)
        elif key in step_head:
            prev_refs = [step_head[key]]

    def begin_step(key: Optional[Tuple[int, int]]) -> Optional[str]:
        """Parent for the first event of this step; also handles switching."""
        nonlocal current_key
        if key is None:
            return ",".join(prev_refs) if prev_refs else user_root_id
        if key != current_key:
            finalize_step(current_key)
            current_key = key
        if key in step_head:
            return step_head[key]  # already inside the step: chain from head
        if prev_refs:
            return ",".join(prev_refs)
        return user_root_id

    for obj in records:
        t = obj.get("type")
        data = _record_data(obj)
        stamp = _ms_to_iso(obj.get("time") or obj.get("time0"))

        if t == _SESSION:
            continue

        if t in (_REQUEST_HEADER, _MODEL_SELECTION):
            if t == _REQUEST_HEADER:
                cfg = (data.get("header") or {}).get("config") or {}
            else:
                cfg = data
            if cfg.get("model"):
                model = cfg.get("model")
                route = cfg.get("provider") or route
            continue

        if t == _USER_MESSAGE:
            source = data.get("source") or {}
            # Only genuine user turns root the causal tree; plugin/skill
            # injections are context, not causes (semantic restraint).
            if source.get("kind") != "user":
                continue
            text = _blocks_text(data.get("content"))
            if not text.strip():
                continue
            finalize_step(current_key)
            current_key = None
            prev_refs = []
            event = add(ToolEvent(
                tool_name="Prompt",
                tool_input={"text": text[:2000]},
                event_type="user_input",
                caused_by="user",
                parent_event_id=None,
                timestamp=stamp,
                model=model,
                provider=_detect_provider(model, route),
                agent=AGENT_NAME,
            ))
            user_root_id = event.event_id
            continue

        if t == _ASSISTANT_MESSAGE:
            key = step_key(data)
            msg = data.get("message") or {}
            parent = begin_step(key)
            chain = parent
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "reasoning":
                    text = block.get("text", "") or block.get("reasoning", "")
                    if not text.strip():
                        continue
                    event = add(ToolEvent(
                        tool_name="Thinking",
                        tool_input={"content": text[:2000]},
                        event_type="reasoning",
                        parent_event_id=chain,
                        timestamp=stamp,
                        model=model,
                        provider=_detect_provider(model, route),
                        agent=AGENT_NAME,
                    ))
                elif btype == "text":
                    text = block.get("text", "")
                    if not text.strip():
                        continue
                    event = add(ToolEvent(
                        tool_name="Response",
                        tool_input={"text": text[:500]},
                        event_type="reasoning",
                        parent_event_id=chain,
                        timestamp=stamp,
                        model=model,
                        provider=_detect_provider(model, route),
                        agent=AGENT_NAME,
                    ))
                else:
                    continue  # tool-call blocks are settled tool/call records
                if key is not None and key not in step_head:
                    step_head[key] = event.event_id
                chain = event.event_id
            continue

        if t == _TOOL_CALL:
            key = step_key(data)
            parent = begin_step(key)
            call_id = data.get("callId", "") or ""
            name = data.get("name", "unknown") or "unknown"
            try:
                arguments = json.loads(data.get("arguments", "{}") or "{}")
                if not isinstance(arguments, dict):
                    arguments = {"value": arguments}
            except (json.JSONDecodeError, TypeError):
                arguments = {"raw": data.get("arguments", "")}
            caused_by = None
            if parent and key is not None and step_head.get(key) == parent:
                caused_by = "reasoning"
            elif parent and parent == user_root_id:
                caused_by = "user"
            event = add(ToolEvent(
                tool_name=name,
                tool_input=arguments,
                event_type="tool_call",
                parent_event_id=parent,
                caused_by=caused_by,
                timestamp=stamp,
                model=model,
                provider=_detect_provider(model, route),
                agent=AGENT_NAME,
            ))
            if call_id:
                calls_by_id[call_id] = event
                if isinstance(obj.get("time"), (int, float)):
                    call_times[call_id] = obj["time"]
            if key is not None:
                step_calls.setdefault(key, []).append(event.event_id)
            continue

        if t == _TOOL_RESULT:
            msg = data.get("message") or {}
            source = msg.get("source") or {}
            call_id = source.get("callId", "") or ""
            out_parts: List[str] = []
            for block in msg.get("content") or []:
                if not isinstance(block, dict) or block.get("type") != "tool-result":
                    continue
                content = block.get("content")
                if isinstance(content, list):
                    out_parts.append(_blocks_text(content))
                else:
                    out_parts.append(str(content or ""))
                if block.get("isError"):
                    out_parts.append("[isError=true]")
            call_event = calls_by_id.get(call_id)
            if call_event is not None:
                output = "\n".join(p for p in out_parts if p).strip()
                call_event.tool_output = (output or "")[:2000]
                call_ms = call_times.get(call_id)
                result_ms = obj.get("time")
                if isinstance(call_ms, (int, float)) and isinstance(result_ms, (int, float)):
                    delta = float(result_ms - call_ms)
                    if delta >= 0:  # tolerate clock-ordered logs; never emit negative
                        call_event.duration_ms = delta
            continue

        if t == _COMMAND_RUN:
            event = add(ToolEvent(
                tool_name=f"/{data.get('name', 'command')}",
                tool_input={"args": (data.get("args") or "")[:500]},
                event_type="context_update",
                caused_by="user",
                parent_event_id=",".join(prev_refs) if prev_refs else user_root_id,
                timestamp=stamp,
                model=model,
                provider=_detect_provider(model, route),
                agent=AGENT_NAME,
            ))
            cmd_id = data.get("commandId", "") or ""
            if cmd_id:
                cmds_by_id[cmd_id] = event
            continue

        if t == _COMMAND_DONE:
            cmd_id = data.get("commandId", "") or ""
            event = cmds_by_id.get(cmd_id)
            if event is not None:
                event.tool_output = (data.get("text") or data.get("kind") or "")[:2000]
            continue

        # everything else (chunk records, turn/*, step/*, compaction/*,
        # todo/write, agent/inbox/spliced, llm/retry, metadata) carries no
        # causetrace-level action; skipped deliberately.

    finalize_step(current_key)
    return events


def scan_session(session_id: str) -> Tuple[str, List[ToolEvent]]:
    """Parse a DSH session and return (session_id, events)."""
    return session_id, parse_session(session_id)
