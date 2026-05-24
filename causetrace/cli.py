"""CLI entry point: timeline, tree, sessions, export, replay."""

import argparse
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

from .core import JSONStore, ReplayEngine, TimelineRenderer, ToolEvent, trace_causal_chain, validate_session, _fmt_input
from .analysis import (
    compute_stats, find_roots, longest_path, fan_out_distribution,
    connected_components, detect_repeated_paths, detect_common_transitions,
    detect_fan_in_patterns, detect_branch_collapse,
)
from .annotation import load_annotation, save_annotation, list_annotated, list_unannotated, TASK_TYPES, SOURCES
from .causality import causal_quality_report
from .hooks.claude_project_parser import parse_session as enrich_session, list_sessions as list_claude_sessions
from .hooks.opencode_parser import parse_session as enrich_opencode_session, list_sessions as list_opencode_sessions
from .hooks.codex_parser import parse_session as enrich_codex_session, list_sessions as list_codex_sessions
from .hooks.opencode_tailer import scan_logs as scan_opencode
from .hooks.continue_tailer import scan_logs as scan_continue
from .hooks.codex_tailer import scan_logs as scan_codex
from .hooks.copilot_tailer import scan_logs as scan_copilot
from .onboarding import create_demo_session, install_claude_hook, uninstall_claude_hook

try:
    from importlib.metadata import version as _import_version
    _CAUSETRACE_VERSION = _import_version("causetrace")
except Exception:
    try:
        from importlib.metadata import version as _import_version
        _CAUSETRACE_VERSION = _import_version("causetrace")
    except Exception:
        _CAUSETRACE_VERSION = "0.1.3"


def _check_result(label: str, ok: bool, detail: str = "") -> tuple[bool, str, str]:
    return (ok, label, detail)


def _run_doctor() -> list[tuple[bool, str, str]]:
    """Run all diagnostic checks and return list of (ok, label, detail)."""
    results: list[tuple[bool, str, str]] = []

    # ── Self check ──
    try:
        import causetrace
        version = getattr(causetrace, "__version__", _CAUSETRACE_VERSION)
        results.append(_check_result("causetrace", True, f"v{version} — {sys.executable}"))
    except Exception as e:
        results.append(_check_result("causetrace", False, str(e)))

    # ── Claude Code hooks ──
    claude_settings = Path.home() / ".claude" / "settings.json"
    if claude_settings.exists():
        try:
            data = json.loads(claude_settings.read_text())
            hooks = data.get("hooks", {})
            pre = hooks.get("PreToolUse", [])
            post = hooks.get("PostToolUse", [])
            if pre and post:
                results.append(_check_result("Claude Code hooks", True,
                    f"{len(pre)} PreToolUse, {len(post)} PostToolUse hooks"))
            else:
                results.append(_check_result("Claude Code hooks", False,
                    "settings.json exists but no PreToolUse/PostToolUse hooks"))
        except Exception as e:
            results.append(_check_result("Claude Code hooks", False, f"parse error: {e}"))
    else:
        results.append(_check_result("Claude Code hooks", False, "settings.json not found"))

    # Claude Code project sessions
    claude_projects = Path.home() / ".claude" / "projects"
    if claude_projects.exists():
        sessions = list(claude_projects.rglob("*.jsonl"))
        results.append(_check_result("Claude Code sessions", True,
            f"{len(sessions)} session files in {claude_projects}"))
    else:
        results.append(_check_result("Claude Code sessions", False,
            f"{claude_projects} not found"))

    # ── Codex CLI ──
    codex_sessions = Path.home() / ".codex" / "sessions"
    if codex_sessions.exists():
        rollouts = list(codex_sessions.rglob("rollout*.jsonl"))
        results.append(_check_result("Codex CLI", True,
            f"{len(rollouts)} rollout files in {codex_sessions}"))
    else:
        results.append(_check_result("Codex CLI", False,
            f"{codex_sessions} not found"))

    # ── OpenCode ──
    opencode_db = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
    if opencode_db.exists():
        size = opencode_db.stat().st_size
        results.append(_check_result("OpenCode DB", True,
            f"{opencode_db} ({size // 1024} KB)"))
    else:
        opencode_logs = Path.home() / ".local" / "share" / "opencode" / "logs"
        if opencode_logs.exists():
            results.append(_check_result("OpenCode DB", False,
                f"DB not found at {opencode_db}, but logs dir exists"))
        else:
            results.append(_check_result("OpenCode", False, "not found"))

    # ── Continue.dev ──
    continue_log = Path.home() / ".continue" / "logs" / "core.log"
    if continue_log.exists():
        size = continue_log.stat().st_size
        results.append(_check_result("Continue.dev", True,
            f"{continue_log} ({size // 1024} KB)"))
    else:
        real_continue_log = Path.home() / ".continue" / "core.log"
        if real_continue_log.exists():
            size = real_continue_log.stat().st_size
            results.append(_check_result("Continue.dev", True,
                f"{real_continue_log} ({size // 1024} KB)"))
        else:
            results.append(_check_result("Continue.dev", False, "no log file found"))

    # ── GitHub Copilot ──
    code_logs = Path.home() / ".config" / "Code" / "logs"
    if code_logs.exists():
        copilot_logs = list(code_logs.rglob("*.log"))
        results.append(_check_result("GitHub Copilot", True,
            f"{len(copilot_logs)} log files in {code_logs}"))
    else:
        results.append(_check_result("GitHub Copilot", False,
            f"{code_logs} not found"))

    return results


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="causetrace", description="Agent Runtime Trace CLI")
    sub = parser.add_subparsers(dest="command")

    p_tl = sub.add_parser("timeline", help="Show flat chronological timeline")
    p_tl.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_tl.add_argument("--output", "-o", action="store_true", help="Show tool output")

    p_tr = sub.add_parser("tree", help="Show causal tree (parent→child)")
    p_tr.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_tr.add_argument("--quality", "-q", action="store_true", help="Show causal quality report")

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

    sub.add_parser("enrich-sessions", help="List available Claude Code project sessions")

    p_enrich = sub.add_parser("enrich", help="Enrich trace from Claude Code project session (extracts reasoning)")
    p_enrich.add_argument("session_id", help="Claude Code project session ID")
    p_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_enrich.add_argument("--output", "-o", action="store_true", help="Show full timeline")

    sub.add_parser("enrich-opencode-sessions", help="List available OpenCode DB sessions")

    p_oc_enrich = sub.add_parser("enrich-opencode", help="Enrich trace from OpenCode DB session (extracts reasoning)")
    p_oc_enrich.add_argument("session_id", help="OpenCode session ID")
    p_oc_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_oc_enrich.add_argument("--output", "-o", action="store_true", help="Show full timeline")

    sub.add_parser("enrich-codex-sessions", help="List available Codex CLI rollout sessions")

    p_cx_enrich = sub.add_parser("enrich-codex", help="Enrich trace from Codex CLI rollout session (extracts reasoning)")
    p_cx_enrich.add_argument("session_id", help="Codex session ID")
    p_cx_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_cx_enrich.add_argument("--output", "-o", action="store_true", help="Show full timeline")

    p_val = sub.add_parser("validate", help="Validate session integrity")
    p_val.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_val.add_argument("--all", action="store_true", help="Validate all stored sessions")
    p_val.add_argument("--fix", action="store_true", help="Fix orphan parent refs (experimental)")

    p_st = sub.add_parser("stats", help="Show structural session statistics")
    p_st.add_argument("session_id", nargs="?", help="Session ID (default: latest)")

    p_rt = sub.add_parser("roots", help="Show root events with downstream metrics")
    p_rt.add_argument("session_id", nargs="?", help="Session ID (default: latest)")

    p_cp = sub.add_parser("critical-path", help="Show longest root-to-leaf causal chain")
    p_cp.add_argument("session_id", nargs="?", help="Session ID (default: latest)")

    p_pt = sub.add_parser("patterns", help="Show repeated tool patterns and transitions")
    p_pt.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_pt.add_argument("--top", type=int, default=15, help="Top N transitions (default: 15)")
    p_pt.add_argument("--transitions-only", action="store_true", help="Show only the transition matrix")
    p_pt.add_argument("--json", action="store_true", help="Output as JSON")
    p_pt.add_argument("--csv", action="store_true", help="Output transitions as CSV")

    p_an = sub.add_parser("annotate", help="View or set session metadata annotations")
    p_an.add_argument("session_id", nargs="?", help="Session ID")
    p_an.add_argument("--task-type", choices=list(TASK_TYPES), help="Task category")
    p_an.add_argument("--source", choices=list(SOURCES), help="Session source")
    p_an.add_argument("--success", type=lambda s: s.lower() in ("true", "1", "yes"), nargs="?", const=True, help="Task completed successfully")
    p_an.add_argument("--notes", help="Free-text observation notes")
    p_an.add_argument("--list", action="store_true", dest="_list", help="List all annotated sessions")
    p_an.add_argument("--unannotated", action="store_true", help="List sessions without annotations")

    p_cmp = sub.add_parser("compare", help="Compare two sessions side by side")
    p_cmp.add_argument("session_a", help="First session ID")
    p_cmp.add_argument("session_b", help="Second session ID")
    p_cmp.add_argument("--top", type=int, default=8, help="Top N transitions per session (default: 8)")

    sub.add_parser("doctor", help="Diagnose agent configuration and data sources")

    sub.add_parser("demo", help="Create and display a saved demo causal trace")

    p_hook_install = sub.add_parser("install-claude-hook", help="Install Claude Code recording hooks")
    p_hook_install.add_argument("--settings", type=Path, help="Claude settings path override")

    p_hook_remove = sub.add_parser("uninstall-claude-hook", help="Remove causetrace Claude Code hooks")
    p_hook_remove.add_argument("--settings", type=Path, help="Claude settings path override")

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
            agent = _detect_agent(evs)
            linked = sum(1 for e in evs if e.parent_event_id)
            link_pct = int(linked / len(evs) * 100) if evs else 0
            agent_tag = f"[{agent}]" if agent else ""
            print(f"  {sid}  ({len(evs)} events, {dur}) {agent_tag} linked:{link_pct}%")

    elif args.command == "timeline":
        sid, events = _load(args.session_id)
        print(f"Session: {sid}  ({len(events)} events)\n")
        TimelineRenderer.print_timeline(events, show_output=args.output)

    elif args.command == "tree":
        sid, events = _load(args.session_id)
        print(f"Session: {sid}  ({len(events)} events, causal tree)\n")
        TimelineRenderer.print_tree(events)
        if args.quality:
            report = causal_quality_report(events)
            print()
            print(f"  Causal quality report:")
            print(f"    Linked events: {report['linked_events']}/{report['total_events']}")
            print(f"    Multi-parent:  {report['multi_parent_events']}")
            print(f"    Max depth:     {report['max_depth']}")
            print(f"    Avg chain:     {report['avg_chain_length']}")
            print(f"    Cycles:        {report['cycles_remaining']}")
            print(f"    Score:         {_quality_bar(report['score'])}")
            if report['score'] < 0.5:
                print(f"    ⚠ Session has weak causal links (likely inferred/heuristic)")
            elif report['cycles_remaining'] > 0:
                print(f"    ⚠ Remaining cycles detected in causal graph")

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

    elif args.command == "enrich-sessions":
        sessions = list_claude_sessions()
        if not sessions:
            print("No Claude Code project sessions found.")
            return
        print(f"Claude Code project sessions ({len(sessions)}):")
        for s in sessions:
            print(f"  {s['session_id']}  ({s['project']}, {s['lines']} lines)")

    elif args.command == "enrich":
        events = enrich_session(args.session_id)
        if not events:
            print(f"No events extracted from session: {args.session_id}")
            sys.exit(1)

        reasoning = sum(1 for e in events if e.event_type == "reasoning")
        tool_calls = sum(1 for e in events if e.event_type == "tool_call")
        rooted = sum(1 for e in events if e.parent_event_id)
        print(f"Session: {args.session_id}")
        print(f"  Events:   {len(events)}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Tool calls: {tool_calls}")
        print(f"  Rooted:   {rooted}")

        if args.output:
            print()
            TimelineRenderer.print_timeline(events)

        if args.save:
            for ev in events:
                store.append(args.session_id, ev)
            print(f"\nSaved as session: {args.session_id} ({len(events)} events)")

    elif args.command == "enrich-opencode-sessions":
        sessions = list_opencode_sessions()
        if not sessions:
            print("No OpenCode sessions found in DB.")
            return
        print(f"OpenCode sessions ({len(sessions)}):")
        for s in sessions[:30]:
            print(f"  {s['session_id']}  ({s['slug']}, {s['title'][:60]})")
        if len(sessions) > 30:
            print(f"  ... and {len(sessions) - 30} more")

    elif args.command == "enrich-opencode":
        events = enrich_opencode_session(args.session_id)
        if not events:
            print(f"No events extracted from session: {args.session_id}")
            sys.exit(1)

        reasoning = sum(1 for e in events if e.event_type == "reasoning")
        tool_calls = sum(1 for e in events if e.event_type == "tool_call")
        rooted = sum(1 for e in events if e.parent_event_id)
        print(f"Session: {args.session_id}")
        print(f"  Events:    {len(events)}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Tool calls: {tool_calls}")
        print(f"  Rooted:    {rooted}")

        if args.output:
            print()
            TimelineRenderer.print_timeline(events)

        if args.save:
            for ev in events:
                store.append(args.session_id, ev)
            print(f"\nSaved as session: {args.session_id} ({len(events)} events)")

    elif args.command == "enrich-codex-sessions":
        sessions = list_codex_sessions()
        if not sessions:
            print("No Codex CLI rollout sessions found.")
            return
        print(f"Codex sessions ({len(sessions)}):")
        for s in sessions[:20]:
            print(f"  {s['session_id']}  ({s['lines']} lines)")
        if len(sessions) > 20:
            print(f"  ... and {len(sessions) - 20} more")

    elif args.command == "enrich-codex":
        events = enrich_codex_session(args.session_id)
        if not events:
            print(f"No events extracted from session: {args.session_id}")
            sys.exit(1)

        reasoning = sum(1 for e in events if e.event_type == "reasoning")
        tool_calls = sum(1 for e in events if e.event_type == "tool_call")
        rooted = sum(1 for e in events if e.parent_event_id)
        print(f"Session: {args.session_id}")
        print(f"  Events:    {len(events)}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Tool calls: {tool_calls}")
        print(f"  Rooted:    {rooted}")
        print(f"  ⚠ Proxy-based sessions may loop tool calls (DeepSeek quirk).")

        if args.output:
            print()
            TimelineRenderer.print_timeline(events)

        if args.save:
            for ev in events:
                store.append(args.session_id, ev)
            print(f"\nSaved as session: {args.session_id} ({len(events)} events)")

    elif args.command == "stats":
        sid, events = _load(args.session_id)
        stats = compute_stats(events)
        print(f"Session: {sid}  ({stats['event_count']} events)\n")
        _print_stats(stats)

    elif args.command == "roots":
        sid, events = _load(args.session_id)
        roots = find_roots(events)
        by_id = {e.event_id: e for e in events}
        print(f"Session: {sid}  ({len(events)} events, {len(roots)} roots)\n")
        _print_roots(roots)

    elif args.command == "critical-path":
        sid, events = _load(args.session_id)
        path_ids = longest_path(events)
        by_id = {e.event_id: e for e in events}
        print(f"Session: {sid}  (critical path: {len(path_ids)} events)\n")
        _print_critical_path(path_ids, by_id)

    elif args.command == "patterns":
        sid, events = _load(args.session_id)

        transitions = detect_common_transitions(events, top_n=args.top)

        # CSV represents the transition table regardless of other view flags.
        if args.csv:
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["from", "to", "count"])
            for t in transitions:
                w.writerow([t["from_tool"], t["to_tool"], t["count"]])
            print(buf.getvalue(), end="")
            return

        # --transitions-only: skip repeated paths and fan-in
        if args.transitions_only:
            if args.json:
                json.dump(transitions, sys.stdout)
                print()
            else:
                print(f"Session: {sid}  ({len(events)} events)\n")
                print(f"  Top {args.top} tool transitions:")
                for t in transitions:
                    bar = "█" * min(t["count"], 40)
                    print(f"    {t['from_tool']:>15s} → {t['to_tool']:<15s}  {bar} {t['count']}")
            return

        # --json: full structured output
        if args.json:
            result = {
                "session_id": sid,
                "event_count": len(events),
                "repeated_patterns": detect_repeated_paths(events, min_length=2, min_occurrences=2)[:10],
                "transitions": transitions,
                "fan_in_patterns": detect_fan_in_patterns(events)[:5],
            }
            json.dump(result, sys.stdout)
            print()
            return

        # Default: human-readable full output
        print(f"Session: {sid}  ({len(events)} events)\n")

        repeated = detect_repeated_paths(events, min_length=2, min_occurrences=2)
        if repeated:
            print("  Repeated tool patterns (>=2 occurrences):")
            for r in repeated[:10]:
                pat_str = " → ".join(r["pattern"])
                print(f"    ×{r['occurrences']}  {pat_str}")
        else:
            print("  No repeated patterns found.")

        print(f"\n  Top {args.top} tool transitions:")
        for t in transitions:
            bar = "█" * min(t["count"], 40)
            print(f"    {t['from_tool']:>15s} → {t['to_tool']:<15s}  {bar} {t['count']}")

        fan_ins = detect_fan_in_patterns(events)
        if fan_ins:
            print(f"\n  Multi-parent convergence ({len(fan_ins)} nodes):")
            for fi in fan_ins[:5]:
                print(f"    {fi['tool_name']}({fi['event_id'][:8]})  parents={fi['parent_count']}")

    elif args.command == "annotate":
        _handle_annotate(store, args)

    elif args.command == "compare":
        _handle_compare(store, args)

    elif args.command == "doctor":
        results = _run_doctor()
        print("causetrace doctor — agent configuration & data source check\n")
        for ok, label, detail in results:
            icon = "✓" if ok else "✗"
            print(f"  {icon} {label}")
            if detail:
                print(f"     {detail}")
        print()

    elif args.command == "demo":
        sid, events, target_id = create_demo_session(store)
        print(f"Demo session saved: {sid}  ({len(events)} events, causal tree)\n")
        TimelineRenderer.print_tree(events)
        print("\nInspect the same trace:")
        print(f"  causetrace graph {sid}")
        print(f"  causetrace why {sid} {target_id}")
        print(f"  causetrace stats {sid}")

    elif args.command == "install-claude-hook":
        try:
            path, changed = install_claude_hook(args.settings)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        verb = "Installed" if changed else "Already installed"
        print(f"{verb}: causetrace Claude Code hooks in {path}")
        print("Run `causetrace doctor` after your next Claude Code session.")

    elif args.command == "uninstall-claude-hook":
        try:
            path, changed = uninstall_claude_hook(args.settings)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        verb = "Removed" if changed else "No causetrace hooks found"
        print(f"{verb}: {path}")

    elif args.command == "validate":
        if args.all:
            sids = store.list_sessions()
            if not sids:
                print("No sessions found.")
                sys.exit(1)
            failed = 0
            for sid in sids:
                path = store._path(sid)
                if not path.exists():
                    print(f"  ✗ {sid}: file not found")
                    failed += 1
                    continue
                raw = path.read_text().splitlines()
                result = _validate_raw(sid, raw)
                status = "✓" if result["valid"] else "✗"
                print(f"  {status} {sid}  ({result['event_count']} events, {len(result['cycles'])} cycles, {len(result['broken_refs'])} broken refs)")
                if not result["valid"]:
                    failed += 1
            print(f"\n{failed}/{len(sids)} sessions failed validation.")
            if failed:
                sys.exit(1)
        else:
            sid = _resolve_sid(args.session_id)
            if not sid:
                print("No sessions found.")
                sys.exit(1)
            path = store._path(sid)
            if not path.exists():
                print(f"Session file not found: {path}")
                sys.exit(1)
            raw = path.read_text().splitlines()
            result = _validate_raw(sid, raw)

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
            else:
                sys.exit(1)


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


def _detect_agent(events) -> str:
    """Detect agent type from events (stops at first direct match)."""
    for ev in events:
        if ev.agent:
            return ev.agent
        if ev.provider:
            return ev.provider
    tool_names = {ev.tool_name.lower() for ev in events}
    if "thinking" in tool_names:
        return "claude-code"
    return "unknown"


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
    if len(events) > 2:
        report = causal_quality_report(events)
        if report["score"] < 0.7:
            print(f"\n  ⚠ Causal quality: {_quality_bar(report['score'])}")
            print(f"     (Codex logs lack native causality — links are heuristic)")
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


def _print_stats(stats: dict) -> None:
    """Render compute_stats output."""
    DIM = TimelineRenderer.DIM
    RST = TimelineRenderer.RESET

    # Basic counts
    print(f"  {DIM}Events{RST}       {stats['event_count']}")
    print(f"  {DIM}Tools{RST}        {stats['tool_count']} ({_freq_bar(stats['tool_freq'], 5)})")
    print(f"  {DIM}Roots{RST}        {stats['root_count']}")
    print(f"  {DIM}Leaves{RST}       {stats['leaf_count']}")
    print(f"  {DIM}Time span{RST}    {_fmt_duration(stats['time_span_s'])}")

    # Graph topology
    print(f"\n  {DIM}Causal topology:{RST}")
    print(f"  {DIM}Max depth{RST}         {stats['max_depth']}")
    print(f"  {DIM}Avg depth{RST}         {stats['avg_depth']}")
    print(f"  {DIM}Avg chain length{RST}  {stats['chain_length_avg']}")
    print(f"  {DIM}Fan-out avg{RST}       {stats['fan_out_avg']}")
    print(f"  {DIM}Fan-out max{RST}       {stats['fan_out_max']}")
    print(f"  {DIM}Link ratio{RST}        {stats['link_ratio']}")
    print(f"  {DIM}Multi-parent{RST}      {stats['multi_parent_count']}")


def _print_roots(roots: list) -> None:
    """Render find_roots output."""
    DIM = TimelineRenderer.DIM
    RST = TimelineRenderer.RESET
    for i, r in enumerate(roots[:20]):
        ts = r["timestamp"][11:19] if len(r["timestamp"]) >= 19 else r["timestamp"]
        print(f"  {i+1:>2d}. {r['tool_name']:<14s}  {DIM}[{ts}]{RST}  "
              f"downstream={r['downstream_count']}  depth={r['max_subtree_depth']}  "
              f"({r['tool_input_preview'][:50]})")
    if len(roots) > 20:
        print(f"  ... and {len(roots) - 20} more roots")


def _print_critical_path(path_ids: list, by_id: dict) -> None:
    """Render longest_path output."""
    DIM = TimelineRenderer.DIM
    RST = TimelineRenderer.RESET
    for i, eid in enumerate(path_ids):
        ev = by_id.get(eid)
        if not ev:
            continue
        ts = ev.timestamp[11:19] if len(ev.timestamp) >= 19 else ev.timestamp
        inp = _fmt_input(ev.tool_input)
        prefix = "  └─ " if i == len(path_ids) - 1 else "  ├─ "
        depth_label = f"  {DIM}(depth {i}){RST}" if i > 0 else f"  {DIM}(root){RST}"
        print(f"{prefix}{ev.tool_name}({inp})  {DIM}[{ts}]{RST}{depth_label}")
    print(f"\n  {DIM}Chain length: {len(path_ids)} events{RST}")


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s}s"


def _freq_bar(tool_freq: dict, top_n: int) -> str:
    """Compact tool frequency bar, e.g. Bash×14, Edit×8, ..."""
    items = list(tool_freq.items())[:top_n]
    return ", ".join(f"{t}×{c}" for t, c in items)


def _handle_annotate(store, args) -> None:
    """Handle `causetrace annotate`."""
    if args._list:
        annotated = list_annotated()
        if not annotated:
            print("No annotated sessions.")
            return
        print(f"Annotated sessions ({len(annotated)}):")
        for a in annotated:
            tt = a.get("task_type", "?")
            src = a.get("source", "?")
            ok = "✓" if a.get("success") else ("✗" if a.get("success") is False else "?")
            print(f"  {a['session_id'][:20]:20s}  task={tt:14s}  source={src:14s}  {ok}")
        return

    if args.unannotated:
        all_sids = store.list_sessions()
        unann = list_unannotated(all_sids)
        if not unann:
            print("All sessions are annotated.")
            return
        print(f"Sessions without annotations ({len(unann)}):")
        for sid in unann:
            evs = store.load(sid)
            print(f"  {sid}  ({len(evs)} events)")
        return

    if not args.session_id:
        print("Usage: causetrace annotate <session_id> [--task-type ...] [--list]")
        sys.exit(1)

    # Show current annotation if no flags set
    if not any([args.task_type, args.source, args.success is not None, args.notes]):
        meta = load_annotation(args.session_id)
        if meta:
            print(f"Annotation for {args.session_id}:")
            for k, v in meta.items():
                print(f"  {k}: {v}")
        else:
            print(f"No annotation for {args.session_id}.")
        return

    # Set annotation fields
    updates = {}
    if args.task_type:
        updates["task_type"] = args.task_type
    if args.source:
        updates["source"] = args.source
    if args.success is not None:
        updates["success"] = args.success
    if args.notes:
        updates["notes"] = args.notes

    meta = save_annotation(args.session_id, updates)
    print(f"Annotated {args.session_id}:")
    for k, v in meta.items():
        if k in ("session_id", "annotated_at"):
            continue
        print(f"  {k}: {v}")


def _handle_compare(store, args) -> None:
    """Handle `causetrace compare`."""
    sid_a = args.session_a
    sid_b = args.session_b

    events_a = store.load(sid_a)
    events_b = store.load(sid_b)

    if not events_a:
        print(f"No events for session: {sid_a}")
        return
    if not events_b:
        print(f"No events for session: {sid_b}")
        return

    stats_a = compute_stats(events_a)
    stats_b = compute_stats(events_b)
    trans_a = detect_common_transitions(events_a, top_n=args.top)
    trans_b = detect_common_transitions(events_b, top_n=args.top)
    meta_a = load_annotation(sid_a)
    meta_b = load_annotation(sid_b)

    # Header with metadata
    def _meta_str(m):
        parts = []
        if m.get("task_type"):
            parts.append(f"task={m['task_type']}")
        if m.get("source"):
            parts.append(f"source={m['source']}")
        if m.get("success") is not None:
            parts.append("success" if m["success"] else "fail")
        return ", ".join(parts) if parts else ""

    DIM = TimelineRenderer.DIM
    RST = TimelineRenderer.RESET
    BOLD = TimelineRenderer.BOLD

    ma = _meta_str(meta_a)
    mb = _meta_str(meta_b)
    print(f"{BOLD}Compare{RST}: {DIM}{sid_a}{RST} vs {DIM}{sid_b}{RST}")
    if ma or mb:
        print(f"  {DIM}A:{RST} {ma}")
        print(f"  {DIM}B:{RST} {mb}")
    print()

    # Structural comparison table
    rows = [
        ("Events",        str(stats_a["event_count"]),     str(stats_b["event_count"])),
        ("Roots",         str(stats_a["root_count"]),      str(stats_b["root_count"])),
        ("Leaves",        str(stats_a["leaf_count"]),      str(stats_b["leaf_count"])),
        ("Max depth",     str(stats_a["max_depth"]),       str(stats_b["max_depth"])),
        ("Avg chain len", str(stats_a["chain_length_avg"]),str(stats_b["chain_length_avg"])),
        ("Fan-out max",   str(stats_a["fan_out_max"]),     str(stats_b["fan_out_max"])),
        ("Link ratio",    str(stats_a["link_ratio"]),      str(stats_b["link_ratio"])),
        ("Time span",     _fmt_duration(stats_a["time_span_s"]), _fmt_duration(stats_b["time_span_s"])),
    ]

    # Topology shape heuristic
    shape_a = _topology_shape(stats_a, stats_a["root_count"])
    shape_b = _topology_shape(stats_b, stats_b["root_count"])
    rows.append(("Topology", shape_a, shape_b))

    print(f"  {DIM}Structural:{RST}")
    for label, va, vb in rows:
        marker = ""
        if va != vb:
            marker = f" {DIM}← diff{RST}"
        print(f"    {label:15s}  {va:>12s}  {vb:>12s}{marker}")
    print()

    # Transition comparison
    print(f"  {DIM}Top transitions:{RST}")
    t_by_a = {t["from_tool"] + "→" + t["to_tool"]: t["count"] for t in trans_a}
    t_by_b = {t["from_tool"] + "→" + t["to_tool"]: t["count"] for t in trans_b}
    all_keys = list(dict.fromkeys(list(t_by_a.keys()) + list(t_by_b.keys())))

    for key in all_keys[:args.top]:
        ca = t_by_a.get(key, 0)
        cb = t_by_b.get(key, 0)
        marker = ""
        if ca != cb:
            marker = f" {DIM}← diff{RST}"
        bar_a = "█" * min(ca, 30)
        bar_b = "█" * min(cb, 30)
        print(f"    {key:25s}  {bar_a:30s} {ca:>4d}  {bar_b:30s} {cb:>4d}{marker}")


def _validate_raw(sid: str, raw: list[str]) -> dict:
    """Parse and validate raw JSONL lines for a session. Returns validate_session result dict."""
    events = []
    schema_errors = []
    for line_number, line in enumerate(raw, start=1):
        if line.strip():
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise TypeError("expected a JSON object")
                events.append(ToolEvent.from_dict(value))
            except json.JSONDecodeError:
                pass
            except (AttributeError, KeyError, TypeError) as exc:
                schema_errors.append(f"Line {line_number}: invalid event data ({exc})")
    result = validate_session(events, raw_lines=raw)
    if schema_errors:
        result["errors"].extend(schema_errors)
        result["valid"] = False
    return result


def _topology_shape(stats: dict, roots_count: int) -> str:
    if roots_count <= 2 and stats["max_depth"] > stats["event_count"] * 0.3:
        return "dominant chain"
    if roots_count > 10 and stats["chain_length_avg"] < 20:
        return "exploratory forest"
    return "mixed"


def _quality_bar(score: float) -> str:
    """Render quality score as a colored bar."""
    bar_len = 20
    filled = int(score * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = int(score * 100)
    if score >= 0.7:
        color = "\033[32m"
    elif score >= 0.4:
        color = "\033[33m"
    else:
        color = "\033[31m"
    return f"{color}{bar} {pct}%\033[0m"
