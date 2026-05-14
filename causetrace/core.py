"""causetrace core: ToolEvent with causality, TraceRecorder, ReplayEngine, Timeline."""
from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


__all__ = [
    "ToolEvent", "TraceRecorder", "JSONStore",
    "TimelineRenderer", "ReplayEngine", "build_tree",
]


class ToolEvent:
    """A tool invocation event with causal context and model attribution."""

    def __init__(
        self,
        tool_name: str,
        tool_input: Any,
        tool_output: Any = None,
        *,
        event_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: str = "tool_call",
        caused_by: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        agent: Optional[str] = None,
        timestamp: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        self.event_id = event_id or uuid.uuid4().hex[:12]
        self.parent_event_id = parent_event_id
        self.session_id = session_id
        self.event_type = event_type
        self.caused_by = caused_by
        self.model = model
        self.provider = provider
        self.agent = agent
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.tool_output = tool_output
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.duration_ms = duration_ms

    def to_dict(self) -> dict:
        d: dict = {
            "event_id": self.event_id,
            "tool_name": self.tool_name,
            "tool_input": _safe_serialize(self.tool_input),
            "tool_output": _safe_serialize(self.tool_output),
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }
        if self.parent_event_id:
            d["parent_event_id"] = self.parent_event_id
        if self.session_id:
            d["session_id"] = self.session_id
        if self.event_type != "tool_call":
            d["event_type"] = self.event_type
        if self.caused_by:
            d["caused_by"] = self.caused_by
        if self.model:
            d["model"] = self.model
        if self.provider:
            d["provider"] = self.provider
        if self.agent:
            d["agent"] = self.agent
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ToolEvent":
        return cls(
            event_id=d["event_id"],
            parent_event_id=d.get("parent_event_id"),
            session_id=d.get("session_id"),
            event_type=d.get("event_type", "tool_call"),
            caused_by=d.get("caused_by"),
            model=d.get("model"),
            provider=d.get("provider"),
            agent=d.get("agent"),
            tool_name=d["tool_name"],
            tool_input=d.get("tool_input"),
            tool_output=d.get("tool_output"),
            timestamp=d.get("timestamp"),
            duration_ms=d.get("duration_ms"),
        )

    def __repr__(self) -> str:
        return f"<ToolEvent {self.tool_name} @ {self.timestamp[11:19]} id={self.event_id}>"


def _safe_serialize(obj: Any) -> Any:
    if isinstance(obj, str):
        return obj[:2000] + "..." if len(obj) > 2000 else obj
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)[:2000]


def _parse_parents(ev: ToolEvent) -> List[str]:
    """Parse parent IDs from parent_event_id (may be comma-separated for multi-parent)."""
    if not ev.parent_event_id:
        return []
    return [p.strip() for p in ev.parent_event_id.split(",") if p.strip()]


def build_tree(events: List[ToolEvent]) -> List[dict]:
    """Build a nested tree from flat event list using parent_event_id.

    Returns list of dicts: {event: ToolEvent, children: [{event, children}]}
    Root nodes are events with no parent_event_id.
    Supports multi-parent (comma-separated parent_event_id).
    A child appears under the FIRST valid parent found.
    """
    by_id: Dict[str, dict] = {}

    for ev in events:
        node = {"event": ev, "children": []}
        by_id[ev.event_id] = node

    roots: List[dict] = []

    for ev in events:
        parents = _parse_parents(ev)
        if not parents:
            roots.append(by_id[ev.event_id])
            continue

        placed_in_parent = False
        for pid in parents:
            if pid in by_id:
                parent = by_id[pid]
                child = by_id[ev.event_id]
                if child not in parent["children"]:
                    parent["children"].append(child)
                placed_in_parent = True
                break

        if not placed_in_parent:
            roots.append(by_id[ev.event_id])

    return roots


def trace_causal_chain(events: List[ToolEvent], event_id: str) -> List[ToolEvent]:
    """Walk backward through parent_event_id chain from an event to its root.

    Supports multi-parent (comma-separated). Follows the first parent.
    Returns ordered list from root → target event.
    """
    by_id = {e.event_id: e for e in events}
    chain: List[ToolEvent] = []
    current = by_id.get(event_id)
    seen: set = set()

    while current and current.event_id not in seen:
        chain.append(current)
        seen.add(current.event_id)
        parents = _parse_parents(current)
        if not parents:
            break
        current = by_id.get(parents[0])

    chain.reverse()
    return chain


DEFAULT_STORE_DIR = os.path.expanduser("~/.causetrace/data")


class JSONStore:
    """Append-only JSON-per-session storage."""

    def __init__(self, store_dir: str = DEFAULT_STORE_DIR):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.store_dir / f"{session_id}.jsonl"

    def append(self, session_id: str, event: ToolEvent) -> None:
        with open(self._path(session_id), "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def load(self, session_id: str) -> List[ToolEvent]:
        path = self._path(session_id)
        if not path.exists():
            return []
        with open(path) as f:
            events = [ToolEvent.from_dict(json.loads(line)) for line in f if line.strip()]
        events.sort(key=lambda e: e.timestamp)
        return events

    def list_sessions(self) -> List[str]:
        return sorted(set(p.stem for p in self.store_dir.glob("*.jsonl")))


class TraceRecorder:
    """Captures tool events with automatic causal linking."""

    def __init__(self, session_id: Optional[str] = None, store: Optional[JSONStore] = None):
        self.session_id = session_id or f"ses_{uuid.uuid4().hex[:8]}"
        self.store = store or JSONStore()
        self._events: List[ToolEvent] = []
        self._last_event_id: Optional[str] = None

    def record(self, event: ToolEvent) -> None:
        event.session_id = self.session_id
        self._events.append(event)
        self.store.append(self.session_id, event)
        self._last_event_id = event.event_id

    def record_call(
        self,
        tool_name: str,
        tool_input: Any,
        tool_output: Any = None,
        *,
        parent_event_id: Optional[str] = None,
        event_type: str = "tool_call",
        caused_by: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        agent: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> ToolEvent:
        event = ToolEvent(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            parent_event_id=parent_event_id or self._last_event_id,
            session_id=self.session_id,
            event_type=event_type,
            caused_by=caused_by,
            model=model,
            provider=provider,
            agent=agent,
            duration_ms=duration_ms,
        )
        self.record(event)
        return event

    def new_group(self) -> None:
        """Reset causal chain. Next event starts a new root."""
        self._last_event_id = None

    def load_into(self, session_id: str) -> None:
        """Load existing events from a session into this recorder's in-memory list."""
        events = self.store.load(session_id)
        self._events.extend(events)
        if events:
            self._last_event_id = events[-1].event_id

    @property
    def events(self) -> List[ToolEvent]:
        return list(self._events)

    def tree(self) -> List[dict]:
        return build_tree(self._events)


class ReplayEngine:
    """Replay a recorded session. Trace-only: shows what would execute."""

    def __init__(self, events: List[ToolEvent]):
        self.events = events

    def trace(self) -> str:
        """Show the planned replay sequence with causal context."""
        lines: list[str] = []
        by_id = {e.event_id: e for e in self.events}

        for ev in self.events:
            arrow = "  "
            ctx = ""
            if ev.parent_event_id and ev.parent_event_id in by_id:
                parent = by_id[ev.parent_event_id]
                arrow = f"  ← {parent.tool_name}({_fmt_input(parent.tool_input)})"
            if ev.caused_by:
                ctx = f"  [{ev.caused_by}]"
            inp = _fmt_input(ev.tool_input)
            dur = f" ({ev.duration_ms:.0f}ms)" if ev.duration_ms is not None else ""
            lines.append(f"  {ev.tool_name}({inp}){dur}{arrow}{ctx}")

        return "\n".join(lines)

    def summary(self) -> str:
        """Return a compact summary of the session for replay."""
        tool_counts: Dict[str, int] = defaultdict(int)
        total_dur = 0.0
        for ev in self.events:
            tool_counts[ev.tool_name] += 1
            if ev.duration_ms:
                total_dur += ev.duration_ms
        tools = ", ".join(f"{name}×{count}" for name, count in sorted(tool_counts.items()))
        return f"{len(self.events)} events ({tools}) · {total_dur / 1000:.1f}s total"

    def detailed_summary(self) -> str:
        """Return a detailed summary with frequency, timing, and anomalies."""
        if not self.events:
            return "No events."

        tool_counts: Dict[str, int] = defaultdict(int)
        total_dur = 0.0
        durations: list[float] = []
        by_tool_dur: Dict[str, list[float]] = defaultdict(list)

        for ev in self.events:
            tool_counts[ev.tool_name] += 1
            if ev.duration_ms is not None:
                total_dur += ev.duration_ms
                durations.append(ev.duration_ms)
                by_tool_dur[ev.tool_name].append(ev.duration_ms)

        tools_sorted = sorted(tool_counts.items(), key=lambda x: -x[1])
        freq = ", ".join(f"{name}×{count}" for name, count in tools_sorted[:10])

        # Duration stats
        dur_str = f"{total_dur/1000:.1f}s total"
        if durations:
            avg = sum(durations) / len(durations)
            dur_str += f" · avg {avg:.0f}ms · max {max(durations):.0f}ms"
            # Detect slowest tools
            slowest = sorted(by_tool_dur.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:3]
            slow_str = " · slowest: " + ", ".join(
                f"{t}({sum(d)/len(d):.0f}ms)" for t, d in slowest
            )
            dur_str += slow_str

        anomalies: list[str] = []
        tool_avgs = {t: sum(d)/len(d) for t, d in by_tool_dur.items() if d}
        for ev in self.events:
            if ev.duration_ms and ev.tool_name in tool_avgs:
                avg = tool_avgs[ev.tool_name]
                if ev.duration_ms > avg * 3 and avg > 50:
                    anomalies.append(f"{ev.tool_name}({ev.duration_ms:.0f}ms)")

        anomaly_str = ""
        if anomalies:
            anomaly_str = f" ⚠ anomalies: {', '.join(anomalies[:5])}"

        return f"{len(self.events)} events ({freq}) · {dur_str}{anomaly_str}"

    def print_trace(self) -> None:
        print(self.trace())


class TimelineRenderer:
    """Renders tool events as flat timeline or causal tree."""

    @classmethod
    def _color(cls, tool_name: str) -> str:
        return cls.COLOR_MAP.get(tool_name, cls.COLOR_MAP["default"])

    @staticmethod
    def _ts(ev: ToolEvent) -> str:
        return ev.timestamp[11:19] if len(ev.timestamp) >= 19 else ev.timestamp

    @staticmethod
    def _dur(ev: ToolEvent) -> str:
        return f" ({ev.duration_ms:.0f}ms)" if ev.duration_ms is not None else ""

    COLOR_MAP = {
        "Bash": "\033[36m",
        "Read": "\033[32m",
        "Write": "\033[33m",
        "Edit": "\033[35m",
        "Grep": "\033[34m",
        "Glob": "\033[34m",
        "default": "\033[37m",
    }
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"

    @classmethod
    def session_header(cls, events: List[ToolEvent]) -> str:
        """Render a header line showing model/provider info if consistent across events."""
        models = set()
        providers = set()
        agents = set()
        for ev in events:
            if ev.model: models.add(ev.model)
            if ev.provider: providers.add(ev.provider)
            if ev.agent: agents.add(ev.agent)
        parts = []
        if len(models) == 1:
            parts.append(f"model={next(iter(models))}")
        elif len(models) > 1:
            parts.append(f"models={','.join(sorted(models))}")
        if len(providers) == 1:
            parts.append(f"provider={next(iter(providers))}")
        if len(agents) == 1:
            parts.append(f"agent={next(iter(agents))}")
        return "  [" + ", ".join(parts) + "]" if parts else ""

    @classmethod
    def render_chain(cls, chain: List[ToolEvent]) -> str:
        """Render a causal chain (root → target) as a compact backward trace."""
        lines: list[str] = []
        for i, ev in enumerate(chain):
            color = cls._color(ev.tool_name)
            ts = cls._ts(ev)
            inp = _fmt_input(ev.tool_input)
            dur = cls._dur(ev)
            arrow = " ──→" if i < len(chain) - 1 else " ◀── TARGET"
            line = (f"  {cls.DIM}[{ts}]{cls.RESET} {color}{ev.tool_name}{cls.RESET}"
                    f"({inp}){cls.DIM}{dur}{cls.RESET}{arrow}")
            lines.append(line)
        return "\n".join(lines)

    @classmethod
    def render(cls, events: List[ToolEvent], show_output: bool = False) -> str:
        """Render as flat chronological timeline (original format)."""
        # Calculate anomaly threshold: mean + 2σ of durations
        durations = [e.duration_ms for e in events if e.duration_ms is not None]
        threshold = None
        if len(durations) >= 3:
            mean = sum(durations) / len(durations)
            variance = sum((d - mean) ** 2 for d in durations) / len(durations)
            threshold = mean + 2 * (variance ** 0.5)

        lines: list[str] = []
        for ev in events:
            ts = ev.timestamp[11:19] if len(ev.timestamp) >= 19 else ev.timestamp
            color = cls.COLOR_MAP.get(ev.tool_name, cls.COLOR_MAP["default"])
            inp = _fmt_input(ev.tool_input)
            dur = f" ({ev.duration_ms:.0f}ms)" if ev.duration_ms is not None else ""
            anomaly_flag = ""
            if threshold is not None and ev.duration_ms and ev.duration_ms > threshold:
                anomaly_flag = f" {cls.BOLD}⚠{cls.RESET}"
            line = f"  {cls.DIM}[{ts}]{cls.RESET} {color}{ev.tool_name}{cls.RESET}({inp}){cls.DIM}{dur}{cls.RESET}{anomaly_flag}"
            lines.append(line)
            if show_output and ev.tool_output:
                out_str = str(ev.tool_output)[:120]
                lines.append(f"    {cls.DIM}→ {out_str}{cls.RESET}")
        return "\n".join(lines)

    @classmethod
    def render_tree(cls, events: List[ToolEvent]) -> str:
        """Render as causal tree showing parent→child relationships."""
        roots = build_tree(events)
        lines: list[str] = []

        def _walk(nodes: List[dict], depth: int = 0) -> None:
            prefix = "  " * depth
            for i, node in enumerate(nodes):
                ev = node["event"]
                is_last = i == len(nodes) - 1
                color = cls._color(ev.tool_name)
                ts = cls._ts(ev)
                inp = _fmt_input(ev.tool_input)
                dur = cls._dur(ev)

                if depth == 0:
                    branch = ""
                elif is_last:
                    branch = "  └─ "
                else:
                    branch = "  ├─ "

                causal = ""
                if ev.caused_by and depth == 0:
                    causal = f"  {cls.DIM}[caused by: {ev.caused_by}]{cls.RESET}"

                lines.append(
                    f"{prefix}{branch}{cls.DIM}[{ts}]{cls.RESET} "
                    f"{color}{ev.tool_name}{cls.RESET}({inp}){cls.DIM}{dur}{cls.RESET}{causal}"
                )
                if node["children"]:
                    _walk(node["children"], depth + 1)

        _walk(roots)
        return "\n".join(lines)

    @classmethod
    def render_graph(cls, events: List[ToolEvent], show_output: bool = False) -> str:
        """Render as a DAG showing multi-parent relationships (fan-in).

        Multi-parent events show all incoming parents:
          Read(a) ──────┐
                        ├──→ Edit(c)
          Grep(b) ──────┘
        """
        by_id = {e.event_id: e for e in events}
        lines: list[str] = []

        for ev in events:
            parents = _parse_parents(ev)
            color = cls._color(ev.tool_name)
            ts = cls._ts(ev)
            inp = _fmt_input(ev.tool_input)
            dur = cls._dur(ev)

            if len(parents) >= 2:
                # Multi-parent: draw fan-in
                label = f"{color}{ev.tool_name}{cls.RESET}({inp}){cls.DIM}{dur}{cls.RESET}"
                lines.append(f"  {cls.DIM}──┐{cls.RESET}")
                for i, pid in enumerate(parents):
                    p_ev = by_id.get(pid)
                    p_name = f"{p_ev.tool_name}({_fmt_input(p_ev.tool_input)})" if p_ev else "?"
                    is_last = (i == len(parents) - 1)
                    branch = "  ├──→ " if not is_last else f"  └──→ {label}"
                    lines.append(f"  {p_name} {cls.DIM}{branch}{cls.RESET}")
            elif len(parents) == 1:
                pid = parents[0]
                p_ev = by_id.get(pid)
                p_name = f"{p_ev.tool_name}({_fmt_input(p_ev.tool_input)})" if p_ev else "?"
                line = (f"  {cls.DIM}[{ts}]{cls.RESET} {color}{ev.tool_name}{cls.RESET}"
                        f"({inp}){cls.DIM}{dur}{cls.RESET}"
                        f"  {cls.DIM}← {p_name}{cls.RESET}")
                lines.append(line)
            else:
                line = (f"  {cls.DIM}[{ts}]{cls.RESET} {color}{ev.tool_name}{cls.RESET}"
                        f"({inp}){cls.DIM}{dur}{cls.RESET}")
                lines.append(line)

            if show_output and ev.tool_output:
                out_str = str(ev.tool_output)[:120]
                lines.append(f"    {cls.DIM}→ {out_str}{cls.RESET}")

        return "\n".join(lines)

    @classmethod
    def print_timeline(cls, events: List[ToolEvent], show_output: bool = False) -> None:
        print(cls.render(events, show_output=show_output))

    @classmethod
    def print_tree(cls, events: List[ToolEvent]) -> None:
        print(cls.render_tree(events))

    @classmethod
    def print_graph(cls, events: List[ToolEvent], show_output: bool = False) -> None:
        print(cls.render_graph(events, show_output=show_output))


def _fmt_input(inp: Any) -> str:
    """Short, readable representation of tool input."""
    if isinstance(inp, dict):
        for key in ("command", "file_path", "url", "pattern", "query"):
            if key in inp:
                val = str(inp[key])[:80]
                return f"{key}={val}"
        return str(list(inp.keys())[:3]) if inp else "{}"
    s = str(inp)[:80]
    return s
