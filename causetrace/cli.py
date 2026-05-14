"""CLI entry point: timeline, tree, sessions, export, replay."""

import argparse
import json
import sys
from datetime import datetime

from .core import JSONStore, ReplayEngine, TimelineRenderer, trace_causal_chain, validate_session
from .hooks.opencode_tailer import scan_logs as scan_opencode
from .hooks.continue_tailer import scan_logs as scan_continue
from .hooks.codex_tailer import scan_logs as scan_codex
from .hooks.copilot_tailer import scan_logs as scan_copilot


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="causetrace", description="Agent Runtime Trace CLI")
    sub = parser.add_subparsers(dest="command")

    p_tl = sub.add_parser("timeline", help="Show flat chronological timeline")
    p_tl.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_tl.add_argument("--output", "-o", action="store_true", help="Show tool output")

    p_tr = sub.add_parser("tree", help="Show causal tree (parent→child)")
    p_tr.add_argument("session_id", nargs="?", help="Session ID (default: latest)")

    p_gr = sub.add_parser("graph", help="Show multi-parent DAG (fan-in)")
    p_gr.add_argument("session_id", nargs="?", help="Session ID (default: latest)")

    sub.add_parser("sessions", help="List all recorded sessions")

    p_exp = sub.add_parser("export", help="Export session as JSON")
    p_exp.add_argument("session_id", help="Session ID to export")
    p_exp.add_argument("--pretty", "-p", action="store_true", help="Pretty-print JSON")

    p_rep = sub.add_parser("replay", help="Show replay trace for a session")
    p_rep.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_rep.add_argument("--summary", "-s", action="store_true", help="Show compact summary only")

    p_oc = sub.add_parser("opencode", help="Scan OpenCode logs and show tool calls")
    p_oc.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_oc.add_argument("--files", type=int, default=3, help="Number of log files to scan (default: 3)")

    p_ai = sub.add_parser("aider", help="Run aider with causetrace tracing")
    p_ai.add_argument("aider_args", nargs="*", help="Arguments passed to aider")
    p_ai.add_argument("--save", action="store_true", help="Save session after completion")

    p_co = sub.add_parser("continue", help="Scan Continue.dev logs")
    p_co.add_argument("--save", action="store_true", help="Save as a new causetrace session")

    p_cx = sub.add_parser("codex", help="Scan OpenAI Codex CLI logs")
    p_cx.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_cx.add_argument("--sessions", type=int, default=3, help="Number of session dirs to scan (default: 3)")

    p_cp = sub.add_parser("copilot", help="Scan GitHub Copilot agent logs")
    p_cp.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_cp.add_argument("--max-dirs", type=int, default=3, help="Number of log dirs to scan (default: 3)")


    p_why = sub.add_parser("why", help="Trace causal chain backward from an event")
    p_why.add_argument("session_id", help="Session ID")
    p_why.add_argument("event_id", help="Event ID to trace from")
    p_why.add_argument("--depth", type=int, default=20, help="Max chain depth (default: 20)")

    p_val = sub.add_parser("validate", help="Validate session integrity")
    p_val.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_val.add_argument("--fix", action="store_true", help="Fix orphan parent refs (experimental)")

    args = parser.parse_args(argv)
    store = JSONStore()

    def _resolve_sid(sid: str | None) -> str | None:
        if sid:
            return sid
        sessions = store.list_sessions()
        return sessions[-1] if sessions else None

    def _load(sid: str | None):
        sid = _resolve_sid(sid)
        if not sid:
            print("No sessions found.")
            sys.exit(1)
        events = store.load(sid)
        if not events:
            print(f"No events for session: {sid}")
            sys.exit(1)
        return sid, events

    if args.command is None:
        args.command = "timeline"
        args.session_id = None
        args.output = False

    if args.command == "sessions":
        sessions = store.list_sessions()
        if not sessions:
            print("No sessions found.")
            return
        print(f"Sessions ({len(sessions)}):")
        for sid in sessions:
            evs = store.load(sid)
            dur = _session_duration(evs)
            print(f"  {sid}  ({len(evs)} events, {dur})")

    elif args.command == "timeline":
        sid, events = _load(args.session_id)
        print(f"Session: {sid}  ({len(events)} events)\n")
        TimelineRenderer.print_timeline(events, show_output=args.output)

    elif args.command == "tree":
        sid, events = _load(args.session_id)
        print(f"Session: {sid}  ({len(events)} events, causal tree)\n")
        TimelineRenderer.print_tree(events)

    elif args.command == "graph":
        sid, events = _load(args.session_id)
        print(f"Session: {sid}  ({len(events)} events, multi-parent DAG)\n")
        TimelineRenderer.print_graph(events)

    elif args.command == "opencode":
        events = scan_opencode(max_files=args.files)
        if not events:
            print("No tool calls found in OpenCode logs.")
            return
        hdr = TimelineRenderer.session_header(events)
        print(f"OpenCode tool calls ({len(events)} events, {args.files} log files){hdr}\n")
        TimelineRenderer.print_timeline(events)
        if args.save:
            for ev in events:
                store.append("opencode_latest", ev)
            print(f"\nSaved as session: opencode_latest ({len(events)} events)")

    elif args.command == "aider":
        _handle_aider(store, args)

    elif args.command == "continue":
        _handle_continue(store, args)

    elif args.command == "codex":
        _handle_codex(store, args)

    elif args.command == "copilot":
        _handle_copilot(store, args)

    elif args.command == "export":
        _, events = _load(args.session_id)
        data = [e.to_dict() for e in events]
        kwargs = {"indent": 2} if args.pretty else {}
        json.dump(data, sys.stdout, **kwargs)
        print()

    elif args.command == "replay":
        sid, events = _load(args.session_id)
        engine = ReplayEngine(events)
        if args.summary:
            print(f"Session {sid}")
            print(f"  All:  {engine.summary()}")
            print(f"  Detail: {engine.detailed_summary()}")
        else:
            print(f"Replay trace for {sid}\n")
            engine.print_trace()

    elif args.command == "why":
        sid, events = _load(args.session_id)
        chain = trace_causal_chain(events, args.event_id)
        if not chain:
            print(f"Event not found: {args.event_id}")
            sys.exit(1)
        by_id = {e.event_id: e for e in events}
        target = by_id.get(args.event_id)
        print(f"Causal chain for {target.tool_name}({args.event_id[:8]}) in {sid}\n")
        print(TimelineRenderer.render_chain(chain))

    elif args.command == "validate":
        sid = _resolve_sid(args.session_id)
        if not sid:
            print("No sessions found.")
            sys.exit(1)
        path = store._path(sid)
        if not path.exists():
            print(f"Session file not found: {path}")
            sys.exit(1)
        raw = path.read_text().splitlines()
        events = store.load(sid)
        result = validate_session(events, raw_lines=raw)

        status = "✓" if result["valid"] else "✗"
        print(f"Session: {sid}  ({result['event_count']} events, {len(raw)} raw lines)\n")

        print(f"  {status} Valid: {result['valid']}")
        print(f"  Events:     {result['event_count']}")
        print(f"  Malformed:  {result['malformed_lines']}")
        print(f"  Orphans:    {result['orphan_count']}")
        print(f"  Broken refs: {len(result['broken_refs'])}")
        print(f"  Cycles:     {len(result['cycles'])}")

        if result["warnings"]:
            print(f"\n  Warnings ({len(result['warnings'])}):")
            for w in result["warnings"][:10]:
                print(f"    ⚠ {w}")
        if result["errors"]:
            print(f"\n  Errors ({len(result['errors'])}):")
            for e in result["errors"][:10]:
                print(f"    ✗ {e}")
        if result["valid"]:
            print("\n  ✓ All checks passed.")


def _session_duration(events) -> str:
    if len(events) < 2:
        return ""
    t0 = events[0].timestamp
    t1 = events[-1].timestamp
    try:
        d = datetime.fromisoformat(t1) - datetime.fromisoformat(t0)
        s = int(d.total_seconds())
        if s < 60:
            return f"{s}s"
        return f"{s // 60}m{s % 60}s"
    except Exception:
        return ""


def _handle_aider(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace aider`."""
    from .hooks.aider_bridge import run_with_tracing

    recorder = run_with_tracing(args.aider_args)
    events = recorder.events
    if not events:
        print("[causetrace] No tool calls captured.")
        return
    print(f"\n[causetrace] Session: {recorder.session_id} ({len(events)} events)")
    TimelineRenderer.print_timeline(events)
    if args.save:
        for ev in events:
            store.append(recorder.session_id, ev)
        print(f"\nSaved as session: {recorder.session_id} ({len(events)} events)")


def _handle_continue(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace continue`."""
    events = scan_continue()
    if not events:
        print("No tool calls found in Continue.dev logs.")
        return
    print(f"Continue.dev tool calls ({len(events)} events)\n")
    TimelineRenderer.print_timeline(events)
    if args.save:
        for ev in events:
            store.append("continue_latest", ev)
        print(f"\nSaved as session: continue_latest ({len(events)} events)")


def _handle_codex(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace codex`."""
    events = scan_codex(max_sessions=args.sessions)
    if not events:
        print("No tool calls found in Codex CLI logs.")
        return
    print(f"Codex CLI tool calls ({len(events)} events, {args.sessions} sessions)\n")
    TimelineRenderer.print_timeline(events)
    if args.save:
        for ev in events:
            store.append("codex_latest", ev)
        print(f"\nSaved as session: codex_latest ({len(events)} events)")


def _handle_copilot(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace copilot`."""
    events = scan_copilot(max_log_dirs=args.max_dirs)
    if not events:
        print("No tool calls found in Copilot logs.")
        return
    print(f"Copilot tool calls ({len(events)} events, {args.max_dirs} log dirs)\n")
    TimelineRenderer.print_timeline(events)
    if args.save:
        for ev in events:
            store.append("copilot_latest", ev)
        print(f"\nSaved as session: copilot_latest ({len(events)} events)")


if __name__ == "__main__":
    cli()
