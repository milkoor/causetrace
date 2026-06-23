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
    detect_fan_in_patterns, detect_branch_collapse, classify_topology,
    detect_topology_shift, TOPOLOGY_PHENOTYPES, detect_branch_persistence,
    compute_frontier_width, detect_retry_density, root_spawning_rate,
)
from .annotation import load_annotation, save_annotation, list_annotated, list_unannotated, TASK_TYPES, SOURCES
from .causality import causal_quality_report
from .corpus import benchmark_corpus, compare_benchmark_manifests, export_dataset, group_labeled_sessions, list_corpus_records, materialize_corpus_metadata, snapshot_corpus, taxonomy_corpus, verify_benchmark_manifest, verify_snapshot
from .crdd import (
    SUBSET_DEFINITIONS,
    analyze_gaps,
    compile_subsets,
    ingest_feedback,
    plan_experiments,
    reprioritize_experiments,
    update_gaps,
)
from .hooks.claude_project_parser import parse_session as enrich_session, list_sessions as list_claude_sessions
from .hooks.opencode_parser import parse_session as enrich_opencode_session, list_sessions as list_opencode_sessions
from .hooks.codex_parser import parse_session as enrich_codex_session, list_sessions as list_codex_sessions
from .hooks.opencode_tailer import scan_logs as scan_opencode
from .hooks.continue_tailer import scan_logs as scan_continue
from .hooks.codex_tailer import scan_logs as scan_codex
from .hooks.copilot_tailer import scan_logs as scan_copilot
from .metadata import INTERVENTION_LANES, detect_causetrace_tags, load_metadata, merge_metadata
from .onboarding import create_demo_session, install_claude_hook, uninstall_claude_hook
from .report import generate_report, generate_corpus_health_report, generate_corpus_origin_report, generate_phase3_readiness_report

try:
    from importlib.metadata import version as _import_version
    _CAUSETRACE_VERSION = _import_version("causetrace")
except Exception:
    try:
        from importlib.metadata import version as _import_version
        _CAUSETRACE_VERSION = _import_version("causetrace")
    except Exception:
        _CAUSETRACE_VERSION = "0.3.0"


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
    p_tr.add_argument("--compress", "-c", type=int, nargs="?", const=3, default=0,
                      help="Compress consecutive same-tool runs (default: 3, use -c to set threshold)")

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
    p_oc.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_oc.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
    p_oc.add_argument("--files", type=int, default=3, help="Number of log files to scan (default: 3)")

    p_ai = sub.add_parser("aider", help="Run aider with causetrace tracing")
    p_ai.add_argument("aider_args", nargs="*", help="Arguments passed to aider")
    p_ai.add_argument("--save", action="store_true", help="Save session after completion")
    p_ai.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_ai.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")

    p_co = sub.add_parser("continue", help="Scan Continue.dev logs")
    p_co.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_co.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_co.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")

    p_cx = sub.add_parser("codex", help="Scan OpenAI Codex CLI logs")
    p_cx.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_cx.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_cx.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
    p_cx.add_argument("--sessions", type=int, default=3, help="Number of session dirs to scan (default: 3)")

    p_cp = sub.add_parser("copilot", help="Scan GitHub Copilot agent logs")
    p_cp.add_argument("--save", action="store_true", help="Save as a new causetrace session")
    p_cp.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_cp.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
    p_cp.add_argument("--max-dirs", type=int, default=3, help="Number of log dirs to scan (default: 3)")


    p_why = sub.add_parser("why", help="Trace causal chain backward from an event")
    p_why.add_argument("session_id", help="Session ID")
    p_why.add_argument("event_id", help="Event ID to trace from")
    p_why.add_argument("--depth", type=int, default=20, help="Max chain depth (default: 20)")

    sub.add_parser("enrich-sessions", help="List available Claude Code project sessions")

    p_enrich = sub.add_parser("enrich", help="Enrich trace from Claude Code project session (extracts reasoning)")
    p_enrich.add_argument("session_id", help="Claude Code project session ID")
    p_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_enrich.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_enrich.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
    p_enrich.add_argument("--output", "-o", action="store_true", help="Show full timeline")

    sub.add_parser("enrich-opencode-sessions", help="List available OpenCode DB sessions")

    p_oc_enrich = sub.add_parser("enrich-opencode", help="Enrich trace from OpenCode DB session (extracts reasoning)")
    p_oc_enrich.add_argument("session_id", help="OpenCode session ID")
    p_oc_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_oc_enrich.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_oc_enrich.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
    p_oc_enrich.add_argument("--output", "-o", action="store_true", help="Show full timeline")

    sub.add_parser("enrich-codex-sessions", help="List available Codex CLI rollout sessions")

    p_cx_enrich = sub.add_parser("enrich-codex", help="Enrich trace from Codex CLI rollout session (extracts reasoning)")
    p_cx_enrich.add_argument("session_id", help="Codex session ID")
    p_cx_enrich.add_argument("--save", action="store_true", help="Save enriched events as a causetrace session")
    p_cx_enrich.add_argument("--upsert", action="store_true", help="Save only events not already present")
    p_cx_enrich.add_argument("--dry-run", action="store_true", help="Show upsert counts without writing")
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
    p_an.add_argument("--tag", help="Filter sessions by causetrace_tags value")

    p_md = sub.add_parser("metadata", help="Show standardized session metadata")
    p_md.add_argument("session_id", help="Session ID")
    p_md.add_argument("--json", action="store_true", help="Output as JSON")

    p_ms = sub.add_parser("metadata-set", help="Set standardized session metadata")
    p_ms.add_argument("session_id", help="Session ID")
    p_ms.add_argument("--runtime", help="Runtime name (e.g. claude, codex, aider)")
    p_ms.add_argument("--model", help="Model name")
    p_ms.add_argument("--task-type", choices=list(TASK_TYPES), help="Task category")
    p_ms.add_argument("--task-source", choices=list(SOURCES), help="Task/data source")
    p_ms.add_argument("--repo-language", help="Repository primary language")
    p_ms.add_argument("--repo-size", help="Repository size bucket or count")
    p_ms.add_argument("--success", type=_parse_cli_bool, help="true/false")
    p_ms.add_argument("--duration", type=float, help="Session duration in seconds")
    p_ms.add_argument("--human-intervention", type=_parse_cli_bool, help="true/false")
    p_ms.add_argument("--intervention-lane", choices=list(INTERVENTION_LANES), help="Intervention lane")

    p_cr = sub.add_parser("corpus", help="Query, snapshot, and export session corpus")
    p_cr.add_argument("--runtime", help="Filter by runtime (e.g. claude, codex, opencode)")
    p_cr.add_argument("--task", choices=list(TASK_TYPES), help="Filter by task type")
    p_cr.add_argument("--topology", choices=list(TOPOLOGY_PHENOTYPES), help="Filter by topology phenotype")
    p_cr.add_argument("--source", choices=list(SOURCES), help="Filter by session source")
    p_cr.add_argument(
        "--lane",
        choices=list(SOURCES) + ["direct_prompt_native"],
        help="Filter by intervention lane (direct_prompt_native maps to task_source=real_work)",
    )
    p_cr_sub = p_cr.add_subparsers(dest="corpus_command")
    p_cr_snapshot = p_cr_sub.add_parser("snapshot", help="Create a reproducible corpus snapshot")
    p_cr_snapshot.add_argument("--name", help="Snapshot name (default: timestamp)")
    p_cr_snapshot.add_argument("--output-dir", help="Corpus root directory (default: ~/.causetrace/corpus)")
    p_cr_export = p_cr_sub.add_parser("export", help="Export corpus dataset manifest as JSON")
    p_cr_export.add_argument("--output", "-o", help="Output file (default: stdout)")
    p_cr_verify = p_cr_sub.add_parser("verify", help="Verify a corpus snapshot manifest and files")
    p_cr_verify.add_argument("snapshot_dir", help="Snapshot directory to verify")
    p_cr_benchmark = p_cr_sub.add_parser("benchmark", help="Build a benchmark manifest from the corpus")
    p_cr_benchmark.add_argument("--name", help="Benchmark name (default: timestamp)")
    p_cr_benchmark.add_argument("--output-dir", help="Corpus root directory (default: ~/.causetrace/corpus)")
    p_cr_benchmark.add_argument("--label", default="task_type", help="Metadata label to group by")
    p_cr_benchmark_sub = p_cr_benchmark.add_subparsers(dest="benchmark_command")
    p_cr_benchmark_verify = p_cr_benchmark_sub.add_parser("verify", help="Verify a benchmark manifest")
    p_cr_benchmark_verify.add_argument("benchmark_dir", help="Benchmark directory to verify")
    p_cr_lane_count = p_cr_sub.add_parser("lane-count", help="Print per-lane session and event counts")
    p_cr_gate = p_cr_sub.add_parser("gate-status", help="Show Phase 3E parser detection gate readiness")
    p_cr_benchmark_compare = p_cr_benchmark_sub.add_parser("compare", help="Compare two benchmark manifests")
    p_cr_benchmark_compare.add_argument("benchmark_a", help="First benchmark directory")
    p_cr_benchmark_compare.add_argument("benchmark_b", help="Second benchmark directory")
    p_cr_taxonomy = p_cr_sub.add_parser("taxonomy", help="Build a structural topology taxonomy from the corpus")
    p_cr_taxonomy.add_argument("--name", help="Taxonomy name (default: timestamp)")
    p_cr_taxonomy.add_argument("--output-dir", help="Corpus root directory (default: ~/.causetrace/corpus)")
    p_cr_groups = p_cr_sub.add_parser("groups", help="Show labeled session groups")
    p_cr_groups.add_argument("--label", default="task_type", help="Metadata label to group by")
    p_cr_health = p_cr_sub.add_parser("health", help="Show corpus milestone gaps and coverage")
    p_cr_health.add_argument("--output", "-o", help="Write report to file")
    p_cr_phase4 = p_cr_sub.add_parser("phase4-status", help="Show Phase 4-3 trigger status for evidence refresh gating")
    p_cr_classify = p_cr_sub.add_parser("classify-unlabeled", help="Propose lane classification for unlabeled sessions")
    p_cr_classify.add_argument("--dry-run", action="store_true", default=True, help="Proposal only, no metadata writes (default)")
    p_cr_classify.add_argument("--apply-confirmed", action="store_true", default=False,
                               help="Apply high-confidence proposals to metadata sidecars")
    p_cr_classify.add_argument("--limit", type=int, default=0, help="Limit to N sessions (0 = all)")
    p_cr_classify.add_argument("--min-confidence", choices=["high", "medium"], default="high",
                               help="Minimum confidence threshold for proposals (default: high)")
    p_cr_origins = p_cr_sub.add_parser("origins", help="Show corpus source-origin coverage for Phase 3C planning")
    p_cr_origins.add_argument("--output", "-o", help="Write report to file")
    p_cr_readiness = p_cr_sub.add_parser("readiness", help="Show phase-3 research readiness and blockers")
    p_cr_readiness.add_argument("--output", "-o", help="Write report to file")
    p_cr_materialize = p_cr_sub.add_parser("materialize", help="Materialize canonical metadata sidecars from annotations and runtime hints")
    p_cr_materialize.add_argument("--output", "-o", help="Write a summary report to file")
    p_cr_compile = p_cr_sub.add_parser("compile-subsets", help="Compile CRDD comparable subset manifests")
    p_cr_compile.add_argument("--subset", action="append", choices=sorted(SUBSET_DEFINITIONS), help="Subset to compile (repeatable; default: all)")
    p_cr_compile.add_argument("--name", help="Manifest run name (default: timestamp)")
    p_cr_compile.add_argument("--output-dir", help="Output directory (default: docs/research/dataset_design/manifests)")
    p_cr_compile.add_argument("--dry-run", action="store_true", help="Build manifests without writing files")
    p_cr_compile.add_argument("--json", action="store_true", help="Print full compile result as JSON")
    p_cr_gaps = p_cr_sub.add_parser("analyze-gaps", help="Analyze CRDD subset coverage gaps")
    p_cr_gaps.add_argument("--subset", action="append", choices=sorted(SUBSET_DEFINITIONS), help="Subset to analyze (repeatable; default: all)")
    p_cr_gaps.add_argument("--output", "-o", help="Write gap report JSON to file")
    p_cr_gaps.add_argument("--json", action="store_true", help="Print full gap report as JSON")
    p_cr_plan = p_cr_sub.add_parser("plan-experiments", help="Plan external-only CERC experiment requirements")
    p_cr_plan.add_argument("--target", choices=sorted(SUBSET_DEFINITIONS), default="failure_enriched", help="Target subset to plan for")
    p_cr_plan.add_argument("--required-sessions", type=int, help="Override required missing session count")
    p_cr_plan.add_argument("--name", help="Experiment plan run name / experiment_id")
    p_cr_plan.add_argument("--output-dir", help="Output directory (default: docs/research/dataset_design/plans)")
    p_cr_plan.add_argument("--dry-run", action="store_true", help="Build plan without writing files")
    p_cr_plan.add_argument("--json", action="store_true", help="Print full plan result as JSON")
    p_cr_feedback = p_cr_sub.add_parser("ingest-feedback", help="Ingest external execution feedback and normalize it")
    p_cr_feedback.add_argument("input", help="Feedback payload JSON path")
    p_cr_feedback.add_argument("--plan-dir", help="Experiment plan directory to link against")
    p_cr_feedback.add_argument("--output-dir", help="Output directory (default: docs/research/dataset_design/feedback)")
    p_cr_feedback.add_argument("--json", action="store_true", help="Print full feedback report as JSON")
    p_cr_gaps_update = p_cr_sub.add_parser("update-gaps", help="Update gap projections from feedback")
    p_cr_gaps_update.add_argument("input", help="Feedback report JSON path")
    p_cr_gaps_update.add_argument("--output-dir", help="Output directory (default: docs/research/dataset_design/feedback)")
    p_cr_gaps_update.add_argument("--json", action="store_true", help="Print gap update report as JSON")
    p_cr_reprioritize = p_cr_sub.add_parser("reprioritize-experiments", help="Reprioritize future experiments from feedback")
    p_cr_reprioritize.add_argument("input", help="Feedback report JSON path")
    p_cr_reprioritize.add_argument("--output-dir", help="Output directory (default: docs/research/dataset_design/feedback)")
    p_cr_reprioritize.add_argument("--json", action="store_true", help="Print reprioritized plan as JSON")

    p_cmp = sub.add_parser("compare", help="Compare two sessions side by side")
    p_cmp.add_argument("session_a", help="First session ID")
    p_cmp.add_argument("session_b", help="Second session ID")
    p_cmp.add_argument("--top", type=int, default=8, help="Top N transitions per session (default: 8)")
    p_cmp.add_argument("--window", type=int, default=50, help="Window size for root spawning comparison")

    p_rp = sub.add_parser("report", help="Generate a markdown research report template")
    p_rp.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_rp.add_argument("--window", type=int, default=50, help="Window size for drift analysis")
    p_rp.add_argument("--top", type=int, default=10, help="Top N roots/transitions")
    p_rp.add_argument("--output", "-o", help="Write report to file")

    sub.add_parser("doctor", help="Diagnose agent configuration and data sources")

    p_sh = sub.add_parser("shifts", help="Detect topology shifts across time windows")
    p_sh.add_argument("session_id", nargs="?", help="Session ID (default: latest)")
    p_sh.add_argument("--window", type=int, default=50, help="Window size in events (default: 50)")
    p_sh.add_argument("--z", type=float, default=2.0, help="Z-score threshold (default: 2.0)")

    p_dt = sub.add_parser("detect-tags", help="Detect causetrace_tags patterns in session events")
    p_dt.add_argument("session_id", help="Session ID to scan")

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
        TimelineRenderer.print_tree(events, compress=args.compress)
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
        if args.save or args.upsert or args.dry_run:
            _persist_imported_events(store, "opencode_latest", events, args)

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

        summary = _persist_imported_events(store, args.session_id, events, args)
        if summary and summary["written"]:
            _auto_detect_intervention_tags(args.session_id)

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

        summary = _persist_imported_events(store, args.session_id, events, args)
        if summary and summary["written"]:
            _auto_detect_intervention_tags(args.session_id)

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

        summary = _persist_imported_events(store, args.session_id, events, args)
        if summary and summary["written"]:
            _auto_detect_intervention_tags(args.session_id)

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

    elif args.command == "metadata":
        _handle_metadata(args)

    elif args.command == "metadata-set":
        _handle_metadata_set(args)

    elif args.command == "corpus":
        _handle_corpus(store, args)

    elif args.command == "compare":
        _handle_compare(store, args)

    elif args.command == "report":
        _handle_report(store, args, _resolve_sid)

    elif args.command == "shifts":
        sid = _resolve_sid(args.session_id)
        if not sid:
            print("No sessions found.")
            sys.exit(1)
        events = store.load(sid)
        if not events:
            print(f"No events for session: {sid}")
            sys.exit(1)
        shifts = detect_topology_shift(events, window_size=args.window, z_threshold=args.z)
        if not shifts:
            print(f"Session: {sid}  ({len(events)} events, window={args.window})\n")
            print("  No significant topology shifts detected.")
            sys.exit(0)
        print(f"Session: {sid}  ({len(events)} events, window={args.window}, z≥{args.z})\n")
        print(f"  {len(shifts)} topology shift(s) detected:\n")
        for s in shifts:
            metrics = ", ".join(f"{k} (z={v})" for k, v in s["shifts"].items())
            print(f"  Window {s['window']:3d}  events [{s['event_index_start']}-{s['event_index_end']})")
            print(f"         {metrics}")
            print()

    elif args.command == "detect-tags":
        result = detect_causetrace_tags(args.session_id)
        print(f"Session: {args.session_id}")
        print(f"  Found: {result['found']}")
        print(f"  Tags: {result['tags']}")
        print(f"  Intervention lane: {result['intervention_lane']}")
        print(f"  Evidence level: {result['evidence_level']}")

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


def _persist_imported_events(
    store: JSONStore,
    session_id: str,
    events: list[ToolEvent],
    args: argparse.Namespace,
) -> dict | None:
    """Persist imported events through one CLI data path."""
    use_upsert = bool(getattr(args, "upsert", False) or getattr(args, "dry_run", False))
    dry_run = bool(getattr(args, "dry_run", False))
    should_save = bool(getattr(args, "save", False) or use_upsert)
    if not should_save:
        return None

    if use_upsert:
        summary = store.append_missing(session_id, events, dry_run=dry_run)
        verb = "Would upsert" if dry_run else "Upserted"
        print(
            f"\n{verb} session: {session_id} "
            f"({summary['added']} added, {summary['skipped']} skipped, "
            f"{summary['existing']} existing)"
        )
        summary["written"] = not dry_run and summary["added"] > 0
        summary["mode"] = "upsert"
        return summary

    for event in events:
        store.append(session_id, event)
    print(f"\nSaved as session: {session_id} ({len(events)} events)")
    return {
        "session_id": session_id,
        "incoming": len(events),
        "existing": None,
        "added": len(events),
        "skipped": 0,
        "dry_run": False,
        "written": bool(events),
        "mode": "append",
    }


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
    _persist_imported_events(store, recorder.session_id, events, args)


def _handle_continue(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace continue`."""
    events = scan_continue()
    if not events:
        print("No tool calls found in Continue.dev logs.")
        return
    print(f"Continue.dev tool calls ({len(events)} events)\n")
    TimelineRenderer.print_timeline(events)
    _persist_imported_events(store, "continue_latest", events, args)


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
    _persist_imported_events(store, "codex_latest", events, args)


def _handle_copilot(store: JSONStore, args: argparse.Namespace) -> None:
    """Handle `causetrace copilot`."""
    events = scan_copilot(max_log_dirs=args.max_dirs)
    if not events:
        print("No tool calls found in Copilot logs.")
        return
    print(f"Copilot tool calls ({len(events)} events, {args.max_dirs} log dirs)\n")
    TimelineRenderer.print_timeline(events)
    _persist_imported_events(store, "copilot_latest", events, args)


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


def _parse_cli_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in ("true", "1", "yes", "y"):
        return True
    if lowered in ("false", "0", "no", "n"):
        return False
    raise argparse.ArgumentTypeError("expected true or false")


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

    if args.tag:
        annotated = list_annotated()
        matches = []
        for a in annotated:
            tags = a.get("causetrace_tags", [])
            if isinstance(tags, str):
                tags = [tags]
            if args.tag in tags:
                matches.append(a)
        if not matches:
            print(f"No sessions with causetrace_tags containing '{args.tag}'.")
            return
        print(f"Sessions with tag '{args.tag}' ({len(matches)}):")
        for m in matches:
            sid = m.get("session_id", "?")[:40]
            src = m.get("source", "?")
            il = m.get("intervention_lane", "")
            print(f"  {sid:40s}  source={src:35s}  lane={il}")
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


def _handle_metadata(args) -> None:
    """Handle ``causetrace metadata``."""
    meta = load_metadata(args.session_id)
    data = meta.to_dict()
    if args.json:
        json.dump({"session_id": args.session_id, "metadata": data}, sys.stdout, indent=2)
        print()
        return
    if not data:
        print(f"No metadata for {args.session_id}.")
        return
    print(f"Metadata for {args.session_id}:")
    for key, value in data.items():
        print(f"  {key}: {value}")


def _handle_metadata_set(args) -> None:
    """Handle ``causetrace metadata-set``."""
    updates = {
        "runtime": args.runtime,
        "model": args.model,
        "task_type": args.task_type,
        "task_source": args.task_source,
        "repo_language": args.repo_language,
        "repo_size": args.repo_size,
        "success": args.success,
        "duration": args.duration,
        "human_intervention": args.human_intervention,
        "intervention_lane": args.intervention_lane if hasattr(args, "intervention_lane") else None,
    }
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        print("No metadata fields provided.")
        sys.exit(1)
    try:
        meta = merge_metadata(args.session_id, updates)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"Metadata saved for {args.session_id}:")
    for key, value in meta.to_dict().items():
        print(f"  {key}: {value}")


def _auto_detect_intervention_tags(session_id: str) -> bool:
    """Scan newly enriched session JSONL for causetrace_tags and auto-set metadata.

    Called after enrichment --save. If causetrace_tags are found in event
    content, sets task_source and intervention_lane in the metadata sidecar
    without overwriting existing manual annotations.

    Returns True if tags were found and metadata was updated.
    """
    result = detect_causetrace_tags(session_id)
    if not result.get("found"):
        return False

    tags = result.get("tags") or []
    lane = result.get("intervention_lane")
    level = result.get("evidence_level")

    updates: dict[str, Any] = {}
    if "superpowers-workflow" in tags or "workflow-intervention" in tags:
        updates["task_source"] = "superpowers_workflow_intervention"
        updates["intervention_lane"] = "superpowers_workflow_intervention"
    elif "prompt-routing" in tags or "routed-prompt" in tags:
        updates["task_source"] = "routed_prompt_intervention"
        updates["intervention_lane"] = "routed_prompt_intervention"
    elif "controlled-prompt-morphology" in tags or "prompt-pilot" in tags:
        updates["task_source"] = "controlled_prompt_morphology"
        updates["intervention_lane"] = "controlled_prompt_morphology"

    if updates:
        updates["causetrace_tags"] = tags
        if level:
            updates["intervention_evidence_level"] = level
        updates["intervention_evidence_source"] = "auto-detected"
        merge_metadata(session_id, updates)
        print(f"  ✓ Auto-detected {updates['intervention_lane']} lane (tags: {', '.join(tags)})")
        return True

    return False


def _print_lane_counts() -> None:
    """Print per-lane session and event counts for Phase 3E."""
    import json
    from collections import Counter

    meta_dir = Path.home() / ".causetrace" / "metadata"
    data_dir = Path.home() / ".causetrace" / "data"
    lanes = Counter()
    lane_events = Counter()

    for f in meta_dir.iterdir():
        if not f.name.endswith(".json") or f.name.endswith(".provenance.json"):
            continue
        sid = f.stem
        with open(f) as mf:
            meta = json.load(mf)
        ts = meta.get("task_source", "")
        do = meta.get("data_origin", "")

        lane = "unlabeled"
        if ts in ("routed_prompt_intervention", "superpowers_workflow_intervention",
                   "controlled_prompt_morphology"):
            lane = ts
        elif do in ("native", "real_work", "direct_prompt_native") and ts == "real_work":
            lane = "direct_prompt_native"

        jf = data_dir / f"{sid}.jsonl"
        ev = 0
        if jf.exists():
            with open(jf) as ef:
                for _ in ef:
                    ev += 1
        lanes[lane] += 1
        lane_events[lane] += ev

    print(f"{'Lane':45s} {'Sessions':>8s} {'Events':>10s}")
    print("-" * 65)
    for lane in ["direct_prompt_native", "superpowers_workflow_intervention",
                  "controlled_prompt_morphology", "routed_prompt_intervention", "unlabeled"]:
        if lanes[lane] or lane != "unlabeled":
            print(f"{lane:45s} {lanes[lane]:8d} {lane_events[lane]:10d}")


def _print_phase4_trigger_status() -> None:
    """Print Phase 4-3 trigger status for evidence refresh gating.

    Read-only. Reports all 8 triggers with current values, thresholds,
    met/not-met status, affected candidates, and next actions.
    """
    import json
    from collections import Counter

    meta_dir = Path.home() / ".causetrace" / "metadata"
    data_dir = Path.home() / ".causetrace" / "data"

    # Gather corpus metrics
    total_meta = 0
    native_sessions = 0
    native_strict = 0
    sp_sessions = 0
    sp_runtimes: set[str] = set()
    routed_sessions = 0
    controlled_sessions = 0
    failure_count = 0
    near_failure_count = 0
    safety_annotated = 0
    runtime_counts: Counter = Counter()       # native strict only (Trigger 7)
    native_strict_runtimes_with_5 = 0
    unlabeled = 0

    for f in meta_dir.iterdir():
        if not f.name.endswith(".json") or f.name.endswith(".provenance.json"):
            continue
        total_meta += 1
        with open(f) as fh:
            meta = json.load(fh)
        ts = meta.get("task_source", "")
        do = meta.get("data_origin", "")
        rt = meta.get("runtime", "")

        # Lane classification
        if ts in ("superpowers_workflow_intervention",):
            sp_sessions += 1
            if rt:
                sp_runtimes.add(rt)
        elif ts == "routed_prompt_intervention":
            routed_sessions += 1
        elif ts == "controlled_prompt_morphology":
            controlled_sessions += 1
        elif ts == "real_work" or do in ("native", "real_work", "direct_prompt_native"):
            native_sessions += 1
            # Check for strict native (direct_prompt_native is the native baseline lane)
            tags = meta.get("causetrace_tags", [])
            il = meta.get("intervention_lane", "")
            is_intervention_lane = il in ("routed_prompt_intervention",
                                          "superpowers_workflow_intervention",
                                          "controlled_prompt_morphology")
            is_strict = bool(not tags and not is_intervention_lane)
            if is_strict:
                native_strict += 1
                if rt:
                    runtime_counts[rt] += 1
            if meta.get("success") is False:
                failure_count += 1
            if meta.get("human_intervention") is True:
                near_failure_count += 1
            if meta.get("causetrace_tags") or meta.get("intervention_evidence_source"):
                safety_annotated += 1
        else:
            unlabeled += 1

    # Count runtimes with >=5 native strict sessions
    for c in runtime_counts.values():
        if c >= 5:
            native_strict_runtimes_with_5 += 1

    # Count data sessions
    data_sessions = sum(1 for f in data_dir.iterdir() if f.name.endswith(".jsonl"))

    trigger_results: list[dict] = []

    # Trigger 1: Native strict growth
    t1_current = native_strict
    t1_threshold = 150
    t1_met = t1_current >= t1_threshold
    trigger_results.append({
        "id": "1", "name": "Native strict growth",
        "current": str(t1_current), "threshold": str(t1_threshold),
        "met": t1_met,
        "affected": "T-RM-001, T-RM-002, T-RM-003",
        "action": "Re-run topology distribution against expanded native strict set."
    })

    # Trigger 2: Failure/near-failure threshold
    t2_current = f"failure={failure_count}, near-failure={near_failure_count}"
    t2_met = failure_count >= 10 and near_failure_count >= 10
    trigger_results.append({
        "id": "2", "name": "Failure/near-failure threshold",
        "current": t2_current, "threshold": "failure>=10, near>=10",
        "met": t2_met,
        "affected": "T-FM-001, T-SC-004, T-SC-005",
        "action": "Reopen Tier 2 failure/intervention validation."
    })

    # Trigger 3: Routed gate
    t3_met = routed_sessions >= 5
    trigger_results.append({
        "id": "3", "name": "Routed-prompt gate",
        "current": str(routed_sessions), "threshold": ">=5 tagged",
        "met": t3_met,
        "affected": "T-RP-001",
        "action": "Open routed lane for basic characterization."
    })

    # Trigger 4: Controlled prompt expansion
    t4_met = controlled_sessions >= 10
    trigger_results.append({
        "id": "4", "name": "Controlled prompt expansion",
        "current": str(controlled_sessions), "threshold": ">=10 with variant tags",
        "met": t4_met,
        "affected": "T-PM-001",
        "action": "Characterize per-variant topology."
    })

    # Trigger 5: SP lane growth
    t5_current = f"{sp_sessions} sessions, {len(sp_runtimes)} runtimes"
    t5_met = sp_sessions >= 15 and len(sp_runtimes) >= 2
    trigger_results.append({
        "id": "5", "name": "Superpowers lane growth",
        "current": t5_current, "threshold": ">=15 sessions, >=2 runtimes",
        "met": t5_met,
        "affected": "T-WI-001, T-SC-003",
        "action": "Re-run SP lane event density distribution."
    })

    # Trigger 6: Safety-control annotation
    t6_met = safety_annotated >= 10
    trigger_results.append({
        "id": "6", "name": "Safety-control annotation",
        "current": str(safety_annotated), "threshold": ">=10 annotated sessions",
        "met": t6_met,
        "affected": "T-SC-001 through T-SC-005",
        "action": "First safety-control morphology baseline."
    })

    # Trigger 7: Runtime balance (native strict lane only)
    dominant_pct = max(runtime_counts.values()) / max(sum(runtime_counts.values()), 1) * 100 if runtime_counts else 100
    t7_current = f"top runtime={dominant_pct:.0f}%, runtimes with >=5: {native_strict_runtimes_with_5}"
    t7_met = dominant_pct < 60 and native_strict_runtimes_with_5 >= 4
    trigger_results.append({
        "id": "7", "name": "Runtime balance",
        "current": t7_current, "threshold": "<60% single runtime, >=4 runtimes with >=5 sessions",
        "met": t7_met,
        "affected": "T-RM-001, T-RM-002, T-RM-003",
        "action": "Test per-runtime topology distribution."
    })

    # Trigger 8: Metadata density
    labeled = total_meta - unlabeled
    pct_labeled = labeled / max(total_meta, 1) * 100
    t8_current = f"{pct_labeled:.1f}% labeled ({labeled}/{total_meta})"
    t8_met = pct_labeled >= 40
    trigger_results.append({
        "id": "8", "name": "Metadata density",
        "current": t8_current, "threshold": ">=40% labeled, >=80% lane coverage",
        "met": t8_met,
        "affected": "All (indirect)",
        "action": "Re-run lane-count with reduced unlabeled population."
    })

    met_count = sum(1 for t in trigger_results if t["met"])

    # Print report
    print("Phase 4-3 Trigger Status")
    print(f"Corpus: {total_meta} metadata sessions, {data_sessions} data sessions")
    print(f"Phase 4: frozen (4-1/4-2 complete, 4-3 trigger-gated)")
    print(f"Phase 5: not open")
    print()
    print(f"{'#':>3s}  {'Trigger':40s} {'Current':>22s}  {'Threshold':30s}  {'Met':5s}")
    print("-" * 107)
    for t in trigger_results:
        flag = "  YES" if t["met"] else "  no"
        print(f"{t['id']:>3s}  {t['name']:40s} {t['current']:>22s}  {t['threshold']:30s}  {flag:5s}")
    print("-" * 107)
    print(f"\nTriggers met: {met_count}/8")
    if met_count == 0:
        print("Phase 4-3 remains closed. No evidence refresh trigger has fired.")
    else:
        print("Phase 4-3 should reopen for affected candidates only.")
    print()
    print("Affected candidates per trigger:")
    for t in trigger_results:
        if t["met"]:
            print(f"  Trigger {t['id']}: {t['affected']}")
            print(f"    → {t['action']}")
    print()
    print("Next check: opportunistic — run after significant corpus growth.")


def _print_classify_unlabeled(limit: int = 0, min_confidence: str = "high",
                              apply_confirmed: bool = False) -> None:
    """Propose lane classification for unlabeled metadata sessions.

    Dry-run by default. --apply-confirmed writes high-confidence proposals
    to metadata sidecars. Does not infer intervention lanes. Does not use
    prompt length, style, tool patterns, or runtime-only rules.
    """
    import json

    from causetrace.metadata import METADATA_DIR, merge_metadata, merge_metadata_provenance

    meta_dir = Path(METADATA_DIR)

    proposals: list[dict] = []
    skipped_reasons: dict[str, int] = {}
    total_unlabeled = 0
    total_existing_lane = 0
    total_scanned = 0

    for f in sorted(meta_dir.iterdir()):
        if not f.name.endswith(".json") or f.name.endswith(".provenance.json"):
            continue
        total_scanned += 1
        with open(f) as fh:
            meta = json.load(fh)
        sid = f.stem
        ts = meta.get("task_source", "")
        do = meta.get("data_origin", "")
        il = meta.get("intervention_lane", "")
        tags = meta.get("causetrace_tags", [])
        rt = meta.get("runtime", "")

        # Already classified via explicit lane assignment
        if ts in ("routed_prompt_intervention", "superpowers_workflow_intervention",
                   "controlled_prompt_morphology"):
            total_existing_lane += 1
            continue
        if il:
            total_existing_lane += 1
            continue

        total_unlabeled += 1

        if limit and len(proposals) >= limit:
            continue

        # Rule: external trajectory
        if do == "external_trajectory":
            proposals.append({
                "session_id": sid, "proposed_lane": "external_trajectory",
                "evidence": f"data_origin={do}", "confidence": "high",
            })
            continue

        # Rule: controlled benchmark
        if do == "controlled_benchmark":
            proposals.append({
                "session_id": sid, "proposed_lane": "controlled_prompt_morphology",
                "evidence": f"data_origin={do}", "confidence": "high",
            })
            continue

        # Rule: native direct prompt (high confidence)
        # Requires: data_origin=native + task_source=real_work + no intervention markers
        if do == "native" and ts == "real_work":
            if tags or il:
                skipped_reasons["has intervention markers despite native+real_work"] = \
                    skipped_reasons.get("has intervention markers despite native+real_work", 0) + 1
                continue
            proposals.append({
                "session_id": sid, "proposed_lane": "direct_prompt_native",
                "evidence": f"data_origin={do}, task_source={ts}, no intervention markers",
                "confidence": "high",
            })
            continue

        # Medium confidence: data_origin=native with no task_source
        if min_confidence == "medium" and do == "native" and not ts:
            if tags or il:
                skipped_reasons["native data_origin but has intervention markers"] = \
                    skipped_reasons.get("native data_origin but has intervention markers", 0) + 1
                continue
            proposals.append({
                "session_id": sid, "proposed_lane": "direct_prompt_native",
                "evidence": f"data_origin={do}, no task_source, no intervention markers",
                "confidence": "medium",
            })
            continue

        # Count skip reasons
        reason = f"no matching rule (do={do}, ts={ts or 'unset'}, rt={rt or 'unset'})"
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    # Apply confirmed writes (high-confidence only)
    applied_count = 0
    if apply_confirmed:
        for p in proposals:
            if p["confidence"] != "high":
                continue
            sid = p["session_id"]
            merge_metadata(sid, {"intervention_lane": p["proposed_lane"]})
            merge_metadata_provenance(sid, {
                "intervention_lane": "classified_from_explicit_metadata"
            })
            applied_count += 1

    # Print report
    mode = "--apply-confirmed" if apply_confirmed else "--dry-run"
    print(f"classify-unlabeled {mode}  (confidence >= {min_confidence})")
    print(f"  Total scanned: {total_scanned}")
    print(f"  Total unlabeled (no intervention_lane): {total_unlabeled}")
    print(f"  Existing lane (already classified): {total_existing_lane}")
    if apply_confirmed:
        print(f"  Applied (written to metadata): {applied_count}")
    print(f"  Proposed (not applied): {len(proposals) - applied_count if apply_confirmed else len(proposals)}")
    print(f"  Skipped (unknown/no rule): {total_unlabeled - len(proposals)}")
    print()
    print(f"{'Confidence':12s} {'Proposed Lane':40s} {'Count':>6s}")
    print("-" * 62)
    from collections import Counter
    lane_counter: Counter = Counter()
    for p in proposals:
        lane_counter[p["proposed_lane"]] += 1
    for conf in ["high", "medium"]:
        for lane in sorted(lane_counter):
            count = sum(1 for p in proposals if p["confidence"] == conf and p["proposed_lane"] == lane)
            if count:
                applied_mark = " (applied)" if apply_confirmed and conf == "high" else ""
                print(f"{conf:12s} {lane:40s} {count:>6d}{applied_mark}")
    print()

    if not apply_confirmed and proposals:
        print("Sample proposals:")
        for p in proposals[:10]:
            sid_short = p["session_id"][:40]
            print(f"  {sid_short:40s} → {p['proposed_lane']:35s} [{p['confidence']}]")
        if len(proposals) > 10:
            print(f"  ... and {len(proposals) - 10} more")
        print()

    if skipped_reasons:
        print("Top skip reasons:")
        for reason, count in sorted(skipped_reasons.items(), key=lambda x: -x[1])[:5]:
            print(f"  [{count:>4d}] {reason[:80]}")
        print()

    if not apply_confirmed:
        print("No metadata written. Use --apply-confirmed to apply high-confidence proposals.")
        return

    # After-apply summary
    unlabeled_after = total_unlabeled - applied_count
    classified_after = total_existing_lane + applied_count
    coverage_before = (total_existing_lane / total_scanned * 100) if total_scanned else 0
    coverage_after = (classified_after / total_scanned * 100) if total_scanned else 0
    print(f"Before: {total_existing_lane}/{total_scanned} classified ({coverage_before:.1f}%)")
    print(f"After:  {classified_after}/{total_scanned} classified ({coverage_after:.1f}%)")
    print(f"Unlabeled remaining: {unlabeled_after}")
    print()
    print("Applied entries have provenance: intervention_lane=classified_from_explicit_metadata")


def _print_gate_status() -> None:
    """Print Phase 3E parser detection gate readiness table."""
    import json
    from collections import Counter
    from pathlib import Path

    GATE_REQUIRED = 5
    LANES = [
        "routed_prompt_intervention",
        "superpowers_workflow_intervention",
        "controlled_prompt_morphology",
    ]

    meta_dir = Path.home() / ".causetrace" / "metadata"
    data_dir = Path.home() / ".causetrace" / "data"

    # Primary signal: causetrace_tags field in annotation metadata
    tagged_sessions = Counter()
    event_tag_hits = Counter()

    for f in meta_dir.iterdir():
        if not f.name.endswith(".json"):
            continue
        try:
            with open(f) as mf:
                meta = json.load(mf)
        except (json.JSONDecodeError, OSError):
            continue

        source = meta.get("source") or meta.get("task_source", "")
        if source not in LANES:
            continue

        tags = meta.get("causetrace_tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if tags:
            tagged_sessions[source] += 1

        # Secondary signal: scan event content for 'causetrace_tags' string
        sid = meta.get("session_id") or f.stem
        jf = data_dir / f"{sid}.jsonl"
        if jf.exists():
            try:
                content = jf.read_text()
                if "causetrace_tags" in content:
                    event_tag_hits[source] += 1
            except OSError:
                pass

    print(f"Phase 3E Parser Detection Gate (requires >= {GATE_REQUIRED} tagged sessions per lane)\n")
    print(f"{'Lane':45s} {'Tagged':>8s} {'Required':>8s} {'Gate':>8s}  {'Event Hits':>10s}")
    print("-" * 85)
    for lane in LANES:
        count = tagged_sessions[lane]
        met = "OPEN" if count >= GATE_REQUIRED else "BLOCKED"
        print(f"{lane:45s} {count:8d} {GATE_REQUIRED:8d} {met:>8s}  {event_tag_hits[lane]:10d}")


def _handle_corpus(store, args) -> None:
    """Handle ``causetrace corpus``."""
    if args.corpus_command == "snapshot":
        result = snapshot_corpus(store, output_dir=args.output_dir, name=args.name)
        print(f"Snapshot: {result['snapshot_dir']}")
        print(f"  Sessions: {result['session_count']}")
        return

    if args.corpus_command == "export":
        dataset = export_dataset(store, output=args.output)
        if args.output:
            print(f"Exported {dataset['session_count']} session(s) to {args.output}")
        else:
            json.dump(dataset, sys.stdout, indent=2)
            print()
        return

    if args.corpus_command == "health":
        report = generate_corpus_health_report(store)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Corpus health report written: {args.output}")
        else:
            print(report)
        return

    if args.corpus_command == "phase4-status":
        _print_phase4_trigger_status()
        return

    if args.corpus_command == "classify-unlabeled":
        _print_classify_unlabeled(args.limit, args.min_confidence, args.apply_confirmed)
        return

    if args.corpus_command == "origins":
        report = generate_corpus_origin_report(store)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Corpus origin report written: {args.output}")
        else:
            print(report)
        return

    if args.corpus_command == "readiness":
        report = generate_phase3_readiness_report(store)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Phase 3 readiness report written: {args.output}")
        else:
            print(report)
        return

    if args.corpus_command == "materialize":
        result = materialize_corpus_metadata(store)
        report_lines = [
            "# Metadata materialization",
            "",
            f"- sessions selected: {result['selected_count']}",
            f"- sessions updated: {result['updated_count']}",
            f"- runtime labels inferred: {result['runtime_inferred_count']}",
            f"- annotation-only sessions materialized: {result['annotation_materialized_count']}",
            f"- provenance sidecars written: {result['provenance_written_count']}",
        ]
        report = "\n".join(report_lines)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(f"Metadata materialization report written: {args.output}")
        else:
            print(report)
        return

    if args.corpus_command == "compile-subsets":
        result = compile_subsets(
            store,
            subset_ids=args.subset,
            output_dir=args.output_dir,
            name=args.name,
            write=not args.dry_run,
        )
        if args.json:
            json.dump(result, sys.stdout, indent=2)
            print()
            return
        action = "Compiled" if result["written"] else "Dry-run compiled"
        print(f"{action} CRDD subsets from {result['source_session_count']} session(s)")
        print(f"Output: {result['output_dir']}")
        for manifest in result["manifests"]:
            score = manifest["comparability"]["score"]
            print(
                f"  {manifest['subset_id']}: "
                f"{manifest['selected_count']} selected, "
                f"{manifest['excluded_count']} excluded, "
                f"score={score}"
            )
        return

    if args.corpus_command == "analyze-gaps":
        report = analyze_gaps(store, subset_ids=args.subset, output=args.output)
        if args.json:
            json.dump(report, sys.stdout, indent=2)
            print()
            return
        if args.output:
            print(f"Gap report written: {args.output}")
        print(f"CERC gap report from {report['source_session_count']} session(s)")
        for gap in report["subset_gaps"]:
            print(
                f"  {gap['subset_id']}: "
                f"{gap['current_sessions']}/{gap['target_sessions']} "
                f"(missing {gap['missing_sessions']}, "
                f"severity={gap['severity']}, "
                f"score={gap['comparability_score']})"
            )
        return

    if args.corpus_command == "plan-experiments":
        result = plan_experiments(
            store,
            target_subset=args.target,
            required_sessions=args.required_sessions,
            output_dir=args.output_dir,
            name=args.name,
            write=not args.dry_run,
        )
        if args.json:
            json.dump(result, sys.stdout, indent=2)
            print()
            return
        plan = result["plan"]
        queue = plan["experiment_queue"]
        gap = plan["gap"]
        action = "Planned" if result["written"] else "Dry-run planned"
        print(f"{action} CERC experiment: {queue['experiment_id']}")
        print(f"Output: {result['output_dir']}")
        print(f"Target subset: {queue['target_subset']}")
        print(f"Current/target: {gap['current_sessions']}/{gap['target_sessions']}")
        print(f"Required sessions: {queue['required_sessions']}")
        print(f"Execution mode: {queue['execution_mode']}")
        print(f"Must not execute: {queue['must_not_execute']}")
        print(f"Evidence status: {queue['evidence_status']}")
        print(f"Queue validation: {queue['validation']['ok']}")
        return

    if args.corpus_command == "ingest-feedback":
        report = ingest_feedback(
            store,
            input_path=args.input,
            plan_dir=args.plan_dir,
            output_dir=args.output_dir,
            write=True,
        )
        if args.json:
            json.dump(report, sys.stdout, indent=2)
            print()
            return
        print(f"Feedback report: {report['output_dir']}")
        print(f"  Experiment: {report['experiment_id']}")
        print(f"  Target subset: {report['target_subset']}")
        print(f"  Observed/resolved: {report['observed_count']}/{report['resolved_count']}")
        print(f"  Resolved ratio: {report['quality']['resolved_ratio']}")
        print(f"  External only: {report['constraints']['external_only']}")
        return

    if args.corpus_command == "update-gaps":
        feedback_report = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = update_gaps(
            store,
            feedback_report=feedback_report,
            output_dir=args.output_dir,
            write=True,
        )
        if args.json:
            json.dump(report, sys.stdout, indent=2)
            print()
            return
        print(f"Gap update: {report['output_dir']}")
        print(f"  Experiment: {report['experiment_id']}")
        print(f"  Target subset: {report['target_subset']}")
        print(f"  Remaining sessions: {report['remaining_sessions']}")
        print(f"  Status: {report['status']}")
        print(f"  Priority hint: {report['priority_hint']}")
        return

    if args.corpus_command == "reprioritize-experiments":
        feedback_report = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = reprioritize_experiments(
            store,
            feedback_report=feedback_report,
            output_dir=args.output_dir,
            write=True,
        )
        if args.json:
            json.dump(report, sys.stdout, indent=2)
            print()
            return
        print(f"Reprioritized plan: {report['output_dir']}")
        print(f"  Experiment: {report['experiment_id']}")
        print(f"  Target subset: {report['target_subset']}")
        print(f"  Remaining sessions: {report['feedback_summary']['remaining_sessions']}")
        print(f"  Top priority: {report['priorities'][0]['subset_id'] if report['priorities'] else 'none'}")
        return

    if args.corpus_command == "verify":
        result = verify_snapshot(args.snapshot_dir)
        print(f"Snapshot: {result['snapshot_dir']}")
        print(f"  OK: {result['ok']}")
        print(f"  Manifest hash match: {result['manifest_hash_match']}")
        print(f"  Sessions verified: {result['verified_count']}/{result['session_count']}")
        if result["issues"]:
            print("  Issues:")
            for issue in result["issues"]:
                print(f"    - {issue}")
        return

    if args.corpus_command == "benchmark":
        if getattr(args, "benchmark_command", None) == "verify":
            result = verify_benchmark_manifest(args.benchmark_dir)
            print(f"Benchmark: {result['benchmark_dir']}")
            print(f"  OK: {result['ok']}")
            print(f"  Hash match: {result['manifest_hash_match']}")
            print(f"  Sessions verified: {result['verified_session_count']}/{result['session_count']}")
            if result["issues"]:
                print("  Issues:")
                for issue in result["issues"]:
                    print(f"    - {issue}")
            return
        if getattr(args, "benchmark_command", None) == "compare":
            result = compare_benchmark_manifests(args.benchmark_a, args.benchmark_b)
            print(f"Benchmark A: {result['benchmark_a']}")
            print(f"Benchmark B: {result['benchmark_b']}")
            print(f"  Hash match: {result['hash_match']}")
            print(f"  Sessions: {result['session_count_a']} vs {result['session_count_b']}")
            print(f"  Groups: {result['group_count_a']} vs {result['group_count_b']}")
            print(f"  Runtime distance: {result['runtime_distance']}")
            print(f"  Topology distance: {result['topology_distance']}")
            print(f"  Shared session IDs: {len(result['shared_session_ids'])}")
            print(f"  Only in A: {len(result['only_in_a'])}")
            print(f"  Only in B: {len(result['only_in_b'])}")
            if result["verify_a"]["issues"]:
                print("  Benchmark A issues:")
                for issue in result["verify_a"]["issues"]:
                    print(f"    - {issue}")
            if result["verify_b"]["issues"]:
                print("  Benchmark B issues:")
                for issue in result["verify_b"]["issues"]:
                    print(f"    - {issue}")
            return
        result = benchmark_corpus(store, output_dir=args.output_dir, name=args.name, label=args.label)
        print(f"Benchmark: {result['benchmark_dir']}")
        print(f"  Sessions: {result['session_count']}")
        print(f"  Groups: {result['manifest']['group_count']}")
        print(f"  Hash: {result['manifest']['benchmark_hash']}")
        return

    if args.corpus_command == "taxonomy":
        result = taxonomy_corpus(store, output_dir=args.output_dir, name=args.name)
        print(f"Taxonomy: {result['taxonomy_dir']}")
        print(f"  Sessions: {result['session_count']}")
        print(f"  Groups: {result['manifest']['group_count']}")
        print(f"  Tags: {len(result['manifest']['tag_counts'])}")
        print(f"  Hash: {result['manifest']['taxonomy_hash']}")
        return

    if args.corpus_command == "lane-count":
        _print_lane_counts()
        return

    if args.corpus_command == "gate-status":
        _print_gate_status()
        return

    records = list_corpus_records(store)
    if not records:
        print("No sessions found.")
        return

    if args.corpus_command == "groups":
        groups = group_labeled_sessions(records, label=args.label)
        print(f"Corpus groups by {args.label}:")
        for label, session_ids in sorted(groups.items()):
            print(f"  {label}: {len(session_ids)}")
            for sid in session_ids[:10]:
                print(f"    {sid}")
            if len(session_ids) > 10:
                print(f"    ... and {len(session_ids) - 10} more")
        return

    rows = []
    for record in records:
        metadata = record["metadata"]
        stats = record["stats"]
        rows.append({
            "session_id": record["session_id"],
            "runtime": metadata.get("runtime", "") or "",
            "task": metadata.get("task_type", "") or "",
            "topology": record.get("topology", "") or "",
            "events": stats.get("event_count", 0),
            "depth": stats.get("max_depth", 0),
            "roots": stats.get("root_count", 0),
            "source": metadata.get("task_source", "") or "",
        })

    # Filter
    if args.runtime:
        rows = [r for r in rows if args.runtime.lower() in r["runtime"].lower()]
    if args.task:
        rows = [r for r in rows if r["task"] == args.task]
    if args.topology:
        rows = [r for r in rows if r["topology"] == args.topology]
    if args.source:
        rows = [r for r in rows if r["source"] == args.source]
    if args.lane:
        lane_source = "real_work" if args.lane == "direct_prompt_native" else args.lane
        rows = [r for r in rows if r["source"] == lane_source]

    if not rows:
        print("No matching sessions.")
        return

    # Print table
    header = f"{'Session ID':24s}  {'Runtime':12s}  {'Task':14s}  {'Topology':22s}  {'Events':>6s}  {'Depth':>5s}  {'Roots':>5s}"
    print(f"Corpus: {len(rows)} session(s)\n")
    print(header)
    print("-" * len(header))
    for r in rows:
        sid = r["session_id"][:22]
        print(f"{sid:24s}  {r['runtime']:12s}  {r['task']:14s}  {r['topology']:22s}  {r['events']:6d}  {r['depth']:5d}  {r['roots']:5d}")


def _handle_report(store, args, resolve_sid) -> None:
    """Handle ``causetrace report``."""
    sid = resolve_sid(args.session_id)
    if not sid:
        print("No sessions found.")
        sys.exit(1)
    events = store.load(sid)
    if not events:
        print(f"No events for session: {sid}")
        sys.exit(1)
    report = generate_report(sid, events, window_size=args.window, top=args.top)
    if args.output:
        Path(args.output).write_text(report)
        print(f"Report written: {args.output}")
        return
    print(report)


def _topology_distance(stats_a: dict, stats_b: dict) -> float:
    keys = (
        "root_count",
        "leaf_count",
        "max_depth",
        "fan_out_avg",
        "fan_out_max",
        "link_ratio",
        "multi_parent_count",
    )
    distances = []
    for key in keys:
        a = float(stats_a.get(key, 0) or 0)
        b = float(stats_b.get(key, 0) or 0)
        denom = max(abs(a), abs(b), 1.0)
        distances.append(abs(a - b) / denom)
    return round(sum(distances) / len(distances), 4)


def _transition_divergence(trans_a: list[dict], trans_b: list[dict]) -> float:
    counts_a = {f"{t['from_tool']}->{t['to_tool']}": t["count"] for t in trans_a}
    counts_b = {f"{t['from_tool']}->{t['to_tool']}": t["count"] for t in trans_b}
    keys = set(counts_a) | set(counts_b)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    if not keys or total_a == 0 or total_b == 0:
        return 0.0 if total_a == total_b else 1.0
    delta = 0.0
    for key in keys:
        pa = counts_a.get(key, 0) / total_a
        pb = counts_b.get(key, 0) / total_b
        delta += abs(pa - pb)
    return round(delta / 2, 4)


def _branch_summary(events) -> dict:
    branches = detect_branch_persistence(events)
    descendants = [b["descendants"] for b in branches]
    lifespans = [b["lifespan"] for b in branches]
    frontier = compute_frontier_width(events)
    retry = detect_retry_density(events)
    return {
        "branch_count": len(branches),
        "avg_descendants": round(sum(descendants) / len(descendants), 2) if descendants else 0.0,
        "max_lifespan": max(lifespans) if lifespans else 0.0,
        "frontier_max": frontier["max_width"],
        "frontier_avg": frontier["avg_width"],
        "retry_density": retry["retry_density"],
    }


def _root_spawning_summary(events, window_size: int) -> dict:
    windows = root_spawning_rate(events, window_size=window_size)
    roots = [w["root_count"] for w in windows]
    return {
        "windows": len(windows),
        "avg_roots": round(sum(roots) / len(roots), 2) if roots else 0.0,
        "max_roots": max(roots) if roots else 0,
    }


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
    trans_all_a = detect_common_transitions(events_a, top_n=None)
    trans_all_b = detect_common_transitions(events_b, top_n=None)
    branch_a = _branch_summary(events_a)
    branch_b = _branch_summary(events_b)
    root_spawn_a = _root_spawning_summary(events_a, args.window)
    root_spawn_b = _root_spawning_summary(events_b, args.window)
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

    print(f"  {DIM}Topology distance:{RST}")
    print(f"    distance            {_topology_distance(stats_a, stats_b):>12.4f}")
    print(f"    transition divergence {_transition_divergence(trans_all_a, trans_all_b):>9.4f}")
    print()

    branch_rows = [
        ("Branches", str(branch_a["branch_count"]), str(branch_b["branch_count"])),
        ("Avg descendants", str(branch_a["avg_descendants"]), str(branch_b["avg_descendants"])),
        ("Max lifespan", _fmt_duration(branch_a["max_lifespan"]), _fmt_duration(branch_b["max_lifespan"])),
        ("Frontier max", str(branch_a["frontier_max"]), str(branch_b["frontier_max"])),
        ("Frontier avg", str(branch_a["frontier_avg"]), str(branch_b["frontier_avg"])),
        ("Retry density", str(branch_a["retry_density"]), str(branch_b["retry_density"])),
    ]
    print(f"  {DIM}Branch distribution:{RST}")
    for label, va, vb in branch_rows:
        marker = f" {DIM}← diff{RST}" if va != vb else ""
        print(f"    {label:15s}  {va:>12s}  {vb:>12s}{marker}")
    print()

    root_rows = [
        ("Windows", str(root_spawn_a["windows"]), str(root_spawn_b["windows"])),
        ("Avg roots", str(root_spawn_a["avg_roots"]), str(root_spawn_b["avg_roots"])),
        ("Max roots", str(root_spawn_a["max_roots"]), str(root_spawn_b["max_roots"])),
    ]
    print(f"  {DIM}Root spawning (window={args.window}):{RST}")
    for label, va, vb in root_rows:
        marker = f" {DIM}← diff{RST}" if va != vb else ""
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


def _is_malformed_json(line: str) -> bool:
    """Check if a non-empty line is valid JSON."""
    try:
        json.loads(line)
        return False
    except json.JSONDecodeError:
        return True


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
    malformed = sum(1 for line in raw if line.strip() and _is_malformed_json(line))
    result = validate_session(events)
    result["malformed_lines"] = malformed
    if schema_errors:
        result["errors"].extend(schema_errors)
        result["valid"] = False
    if malformed:
        result["warnings"].append(f"{malformed} malformed JSON line(s) skipped")
        if not result["errors"]:
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
