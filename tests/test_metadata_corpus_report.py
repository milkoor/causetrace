import json
import os
import subprocess
import sys
from pathlib import Path

from causetrace.analysis import (
    compute_frontier_width,
    detect_branch_persistence,
    detect_retry_density,
)
from causetrace.annotation import save_annotation
from causetrace.core import JSONStore, ToolEvent
from causetrace.corpus import Phase3ReadinessRequirements, assess_phase3_readiness, benchmark_corpus, build_corpus_facts, compare_benchmark_manifests, export_dataset, list_corpus_records, materialize_corpus_metadata, snapshot_corpus, taxonomy_corpus, verify_benchmark_manifest, verify_snapshot
from causetrace.metadata import load_metadata, load_metadata_provenance, merge_metadata
from causetrace.report import generate_corpus_health_report, generate_phase3_readiness_report
from causetrace.corpus import summarize_corpus_health


def _write_session(store: JSONStore, session_id: str) -> None:
    events = [
        ToolEvent("Read", {"file": "a.py"}, event_id="r", timestamp="2026-01-01T00:00:00"),
        ToolEvent("Edit", {"file": "a.py"}, event_id="e", parent_event_id="r", timestamp="2026-01-01T00:00:01"),
    ]
    for event in events:
        store.append(session_id, event)


def test_metadata_merges_legacy_annotation(monkeypatch, tmp_path):
    import causetrace.annotation as annotation
    import causetrace.metadata as metadata

    monkeypatch.setattr(annotation, "ANNOTATION_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    save_annotation("s1", {"task_type": "bug_fix", "source": "real_work", "success": True})
    merged = load_metadata("s1")
    assert merged.task_type == "bug_fix"
    assert merged.task_source == "real_work"
    assert merged.success is True

    provenance = load_metadata_provenance("s1")
    assert provenance["task_type"] == "annotation"
    assert provenance["task_source"] == "annotation"
    assert provenance["success"] == "annotation"

    updated = merge_metadata("s1", {"runtime": "codex", "model": "gpt-5"})
    assert updated.runtime == "codex"
    assert load_metadata("s1").model == "gpt-5"


def test_corpus_snapshot_and_export(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    merge_metadata("s1", {"runtime": "claude", "task_type": "feature_add"})

    snapshot = snapshot_corpus(store, output_dir=tmp_path / "corpus", name="daily")
    snapshot_dir = Path(snapshot["snapshot_dir"])
    assert snapshot["session_count"] == 1
    assert snapshot["manifest"]["snapshot_hash"]
    assert snapshot["manifest"]["sessions"][0]["session_hash"]
    assert snapshot["manifest"]["sessions"][0]["session_bytes"] > 0
    assert (snapshot_dir / "sessions" / "s1.jsonl").exists()
    assert (snapshot_dir / "metadata" / "s1.json").exists()
    assert (snapshot_dir / "labels").is_dir()
    assert (snapshot_dir / "benchmarks").is_dir()

    dataset = export_dataset(store)
    assert dataset["session_count"] == 1
    assert dataset["dataset_hash"]
    assert dataset["sessions"][0]["metadata"]["runtime"] == "claude"


def test_corpus_snapshot_verify(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    merge_metadata("s1", {"runtime": "claude", "task_type": "feature_add"})

    snapshot = snapshot_corpus(store, output_dir=tmp_path / "corpus", name="daily")
    snapshot_dir = Path(snapshot["snapshot_dir"])

    result = verify_snapshot(snapshot_dir)
    assert result["ok"] is True
    assert result["manifest_hash_match"] is True
    assert result["verified_count"] == 1
    assert result["issues"] == []

    (snapshot_dir / "metadata" / "s1.json").write_text("{}")
    broken = verify_snapshot(snapshot_dir)
    assert broken["ok"] is False
    assert broken["issues"]


def test_corpus_benchmark_manifest_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    merge_metadata("a", {"runtime": "claude", "task_type": "bug_fix"})
    merge_metadata("b", {"runtime": "codex", "task_type": "exploration"})

    result = benchmark_corpus(store, output_dir=tmp_path / "corpus", name="daily", label="task_type")
    benchmark_dir = Path(result["benchmark_dir"])
    assert result["session_count"] == 2
    assert result["manifest"]["benchmark_hash"]
    assert result["manifest"]["group_count"] == 2
    assert result["manifest"]["session_ids"] == ["a", "b"]
    assert (benchmark_dir / "benchmark.json").exists()
    assert result["manifest"]["runtime_counts"]["claude"] == 1
    assert result["manifest"]["topology_counts"]

    verify = verify_benchmark_manifest(benchmark_dir)
    assert verify["ok"] is True
    assert verify["manifest_hash_match"] is True
    assert verify["verified_session_count"] == 2

    cli_result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "benchmark", "--name", "daily", "--output-dir", str(tmp_path / "corpus")],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert cli_result.returncode == 0
    assert "Benchmark:" in cli_result.stdout
    assert "Hash:" in cli_result.stdout

    verify_result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "benchmark", "verify", str(benchmark_dir)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert verify_result.returncode == 0
    assert "OK: True" in verify_result.stdout
    assert "Hash match: True" in verify_result.stdout


def test_corpus_benchmark_verify_ignores_top_level_order(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    merge_metadata("a", {"runtime": "claude", "task_type": "bug_fix"})
    merge_metadata("b", {"runtime": "codex", "task_type": "exploration"})

    result = benchmark_corpus(store, output_dir=tmp_path / "corpus", name="daily", label="task_type")
    benchmark_dir = Path(result["benchmark_dir"])
    manifest_path = benchmark_dir / "benchmark.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["session_ids"] = list(reversed(manifest["session_ids"]))
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    verify = verify_benchmark_manifest(benchmark_dir)
    assert verify["ok"] is True
    assert verify["manifest_hash_match"] is True
    assert verify["verified_session_count"] == 2


def test_corpus_benchmark_hash_is_order_stable(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    merge_metadata("a", {"runtime": "claude", "task_type": "bug_fix"})
    merge_metadata("b", {"runtime": "codex", "task_type": "bug_fix"})

    manifest_a = benchmark_corpus(
        store,
        output_dir=tmp_path / "corpus-a",
        name="daily-a",
        label="task_type",
        session_ids=["a", "b"],
    )["manifest"]
    manifest_b = benchmark_corpus(
        store,
        output_dir=tmp_path / "corpus-b",
        name="daily-b",
        label="task_type",
        session_ids=["b", "a"],
    )["manifest"]

    assert manifest_a["groups"][0]["session_ids"] == ["a", "b"]
    assert manifest_b["groups"][0]["session_ids"] == ["a", "b"]
    assert manifest_a["benchmark_hash"] == manifest_b["benchmark_hash"]


def test_corpus_benchmark_compare_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    _write_session(store, "c")
    merge_metadata("a", {"runtime": "claude", "task_type": "bug_fix"})
    merge_metadata("b", {"runtime": "codex", "task_type": "exploration"})
    merge_metadata("c", {"runtime": "aider", "task_type": "feature_add"})

    bench_a = benchmark_corpus(
        store,
        output_dir=tmp_path / "corpus",
        name="alpha",
        label="task_type",
        session_ids=["a", "b"],
    )
    bench_b = benchmark_corpus(
        store,
        output_dir=tmp_path / "corpus",
        name="beta",
        label="task_type",
        session_ids=["b", "c"],
    )

    comparison = compare_benchmark_manifests(bench_a["benchmark_dir"], bench_b["benchmark_dir"])
    assert comparison["hash_match"] is False
    assert comparison["session_count_a"] == 2
    assert comparison["session_count_b"] == 2
    assert comparison["shared_session_ids"] == ["b"]
    assert comparison["only_in_a"] == ["a"]
    assert comparison["only_in_b"] == ["c"]
    assert comparison["runtime_distance"] > 0
    assert comparison["topology_distance"] >= 0

    cli_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causetrace",
            "corpus",
            "benchmark",
            "compare",
            bench_a["benchmark_dir"],
            bench_b["benchmark_dir"],
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert cli_result.returncode == 0
    assert "Benchmark A:" in cli_result.stdout
    assert "Runtime distance:" in cli_result.stdout
    assert "Only in A:" in cli_result.stdout


def test_corpus_taxonomy_manifest_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))

    deep_chain = [
        ToolEvent("Read", {}, event_id="d1", timestamp="2026-01-01T00:00:00"),
        ToolEvent("Edit", {}, event_id="d2", parent_event_id="d1", timestamp="2026-01-01T00:00:01"),
        ToolEvent("Bash", {}, event_id="d3", parent_event_id="d2", timestamp="2026-01-01T00:00:02"),
        ToolEvent("Grep", {}, event_id="d4", parent_event_id="d3", timestamp="2026-01-01T00:00:03"),
        ToolEvent("Read", {}, event_id="d5", parent_event_id="d4", timestamp="2026-01-01T00:00:04"),
        ToolEvent("Write", {}, event_id="d6", parent_event_id="d5", timestamp="2026-01-01T00:00:05"),
    ]
    for event in deep_chain:
        store.append("deep", event)

    fan_in_events = [
        ToolEvent("Read", {}, event_id="f1", timestamp="2026-01-01T01:00:00"),
        ToolEvent("Read", {}, event_id="f2", timestamp="2026-01-01T01:00:01"),
        ToolEvent("Edit", {}, event_id="f3", parent_event_id="f1,f2", timestamp="2026-01-01T01:00:02"),
    ]
    for event in fan_in_events:
        store.append("fanin", event)

    multi_root_events = [
        ToolEvent("Read", {}, event_id="m1", timestamp="2026-01-01T02:00:00"),
        ToolEvent("Read", {}, event_id="m2", timestamp="2026-01-01T02:00:01"),
        ToolEvent("Read", {}, event_id="m3", timestamp="2026-01-01T02:00:02"),
        ToolEvent("Read", {}, event_id="m4", timestamp="2026-01-01T02:00:03"),
        ToolEvent("Read", {}, event_id="m5", timestamp="2026-01-01T02:00:04"),
    ]
    for event in multi_root_events:
        store.append("multiroot", event)

    merge_metadata("deep", {"runtime": "claude", "task_type": "feature_add"})
    merge_metadata("fanin", {"runtime": "codex", "task_type": "bug_fix"})
    merge_metadata("multiroot", {"runtime": "aider", "task_type": "exploration"})

    result = taxonomy_corpus(store, output_dir=tmp_path / "corpus", name="daily")
    taxonomy_dir = Path(result["taxonomy_dir"])
    assert result["session_count"] == 3
    assert result["manifest"]["taxonomy_hash"]
    assert result["manifest"]["session_ids"] == ["deep", "fanin", "multiroot"]
    assert (taxonomy_dir / "taxonomy.json").exists()
    assert result["manifest"]["tag_counts"]["deep_linear"] == 1
    assert result["manifest"]["tag_counts"]["fan_in"] == 1
    assert result["manifest"]["tag_counts"]["branch_collapse"] == 1
    assert result["manifest"]["tag_counts"]["multi_root_exploration"] == 1

    cli_result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "taxonomy", "--name", "daily", "--output-dir", str(tmp_path / "corpus")],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert cli_result.returncode == 0
    assert "Taxonomy:" in cli_result.stdout
    assert "Hash:" in cli_result.stdout


def test_corpus_taxonomy_hash_is_order_stable(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))

    deep_chain = [
        ToolEvent("Read", {}, event_id="d1", timestamp="2026-01-01T00:00:00"),
        ToolEvent("Edit", {}, event_id="d2", parent_event_id="d1", timestamp="2026-01-01T00:00:01"),
        ToolEvent("Bash", {}, event_id="d3", parent_event_id="d2", timestamp="2026-01-01T00:00:02"),
        ToolEvent("Grep", {}, event_id="d4", parent_event_id="d3", timestamp="2026-01-01T00:00:03"),
    ]
    for event in deep_chain:
        store.append("deep", event)

    fan_in_events = [
        ToolEvent("Read", {}, event_id="f1", timestamp="2026-01-01T01:00:00"),
        ToolEvent("Read", {}, event_id="f2", timestamp="2026-01-01T01:00:01"),
        ToolEvent("Edit", {}, event_id="f3", parent_event_id="f1,f2", timestamp="2026-01-01T01:00:02"),
    ]
    for event in fan_in_events:
        store.append("fanin", event)

    multi_root_events = [
        ToolEvent("Read", {}, event_id="m1", timestamp="2026-01-01T02:00:00"),
        ToolEvent("Read", {}, event_id="m2", timestamp="2026-01-01T02:00:01"),
        ToolEvent("Read", {}, event_id="m3", timestamp="2026-01-01T02:00:02"),
        ToolEvent("Read", {}, event_id="m4", timestamp="2026-01-01T02:00:03"),
        ToolEvent("Read", {}, event_id="m5", timestamp="2026-01-01T02:00:04"),
    ]
    for event in multi_root_events:
        store.append("multiroot", event)

    merge_metadata("deep", {"runtime": "claude", "task_type": "feature_add"})
    merge_metadata("fanin", {"runtime": "codex", "task_type": "bug_fix"})
    merge_metadata("multiroot", {"runtime": "aider", "task_type": "exploration"})

    taxonomy_a = taxonomy_corpus(
        store,
        output_dir=tmp_path / "corpus-a",
        name="daily-a",
        session_ids=["deep", "fanin", "multiroot"],
    )["manifest"]
    taxonomy_b = taxonomy_corpus(
        store,
        output_dir=tmp_path / "corpus-b",
        name="daily-b",
        session_ids=["multiroot", "fanin", "deep"],
    )["manifest"]

    assert taxonomy_a["session_ids"] == ["deep", "fanin", "multiroot"]
    assert taxonomy_b["session_ids"] == ["deep", "fanin", "multiroot"]
    assert taxonomy_a["groups"][0]["session_ids"] == taxonomy_b["groups"][0]["session_ids"]
    assert taxonomy_a["taxonomy_hash"] == taxonomy_b["taxonomy_hash"]


def test_phase3_readiness_report_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    merge_metadata("a", {
        "runtime": "claude",
        "model": "sonnet",
        "task_type": "bug_fix",
        "task_source": "real_work",
        "repo_language": "python",
        "repo_size": "small",
        "success": True,
        "duration": 12.5,
        "human_intervention": False,
    })
    merge_metadata("b", {
        "runtime": "codex",
        "model": "gpt-5",
        "task_type": "exploration",
        "task_source": "demo",
        "repo_language": "python",
        "repo_size": "small",
        "success": False,
        "duration": 15.0,
        "human_intervention": False,
    })

    requirements = Phase3ReadinessRequirements(
        min_sessions=2,
        min_metadata_sessions=2,
        min_explicit_runtime_sessions=2,
        min_task_type_sessions=2,
        min_runtime_breadth=2,
        min_task_breadth=2,
        min_fan_in_sessions=0,
        min_branch_collapse_sessions=0,
        min_multi_root_sessions=0,
        min_long_sessions=0,
        min_retry_heavy_sessions=0,
    )
    readiness = assess_phase3_readiness(store, requirements=requirements)
    assert readiness["ready"] is True
    assert all(item["passed"] for item in readiness["criteria"])
    assert readiness["explicit_metadata_field_counts"]["runtime"] == 2

    report = generate_phase3_readiness_report(store)
    assert "# Phase 3 readiness report" in report
    assert "## Research Protocol" in report
    assert "## Blockers" in report
    assert "strict research-grade sessions" in report
    assert "## Missing Metadata Coverage" in report
    assert "## Near Research-Grade Sessions" in report

    cli_result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "readiness"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert cli_result.returncode == 0
    assert "Phase 3 readiness report" in cli_result.stdout
    assert "research-grade sessions" in cli_result.stdout


def test_corpus_facts_and_record_provenance(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    _write_session(store, "s2")
    merge_metadata("s1", {
        "runtime": "claude",
        "task_type": "review",
        "task_source": "real_work",
        "success": True,
    })
    merge_metadata("s2", {"runtime": "codex"})

    facts = build_corpus_facts(store)
    assert facts["session_count"] == 2
    assert facts["research_grade_sessions"] == 1
    assert facts["metadata_sessions"] == 2
    assert facts["task_type_sessions"] == 1
    assert facts["metadata_missing_counts"]["task_type"] == 1
    assert facts["metadata_missing_counts"]["task_source"] == 1
    assert facts["metadata_provenance_counts"].get("unknown", 0) == 0

    facts_again = build_corpus_facts(store)
    assert facts_again["explicit_runtime_sessions"] == 2

    corpus_records = list_corpus_records(store)
    corpus_record = next(record for record in corpus_records if record["session_id"] == "s1")
    provenance = corpus_record["metadata_provenance"]
    assert provenance["runtime"] == "explicit_sidecar"
    assert provenance["task_type"] == "explicit_sidecar"


def test_corpus_materialize_metadata(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    store.append("a", ToolEvent("Read", {}, event_id="a1", timestamp="2026-01-01T00:00:00", agent="claude"))
    store.append("b", ToolEvent("Read", {}, event_id="b1", timestamp="2026-01-01T00:00:00", provider="codex"))
    save_annotation("a", {"task_type": "bug_fix", "source": "real_work", "success": True})

    before_a = load_metadata("a", include_annotation=False).to_dict()
    before_b = load_metadata("b", include_annotation=False).to_dict()
    assert before_a == {}
    assert before_b == {}

    result = materialize_corpus_metadata(store)
    assert result["updated_count"] == 2
    assert result["runtime_inferred_count"] == 2
    assert result["annotation_materialized_count"] == 1
    assert result["provenance_written_count"] == 2

    after_a = load_metadata("a", include_annotation=False).to_dict()
    after_b = load_metadata("b", include_annotation=False).to_dict()
    assert after_a["runtime"] == "claude"
    assert after_a["task_type"] == "bug_fix"
    assert after_b["runtime"] == "codex"

    provenance_a = load_metadata_provenance("a")
    provenance_b = load_metadata_provenance("b")
    assert provenance_a["runtime"] == "inferred_from_runtime_adapter"
    assert provenance_a["task_type"] == "materialized"
    assert provenance_a["task_source"] == "materialized"
    assert provenance_a["success"] == "materialized"
    assert provenance_b["runtime"] == "inferred_from_runtime_adapter"


def test_report_cli_outputs_template(tmp_path):
    store_dir = tmp_path / ".causetrace" / "data"
    store_dir.mkdir(parents=True)
    store = JSONStore(store_dir=str(store_dir))
    _write_session(store, "s1")

    result = subprocess.run(
        [sys.executable, "-m", "causetrace", "report", "s1"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert result.returncode == 0
    assert "# causetrace report: s1" in result.stdout
    assert "## Stats" in result.stdout
    assert "## Window Drift" in result.stdout
    assert "## Observations" in result.stdout


def test_topology_primitives_are_structural():
    events = [
        ToolEvent("Read", {}, event_id="r", timestamp="2026-01-01T00:00:00"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="r", timestamp="2026-01-01T00:00:01"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1", timestamp="2026-01-01T00:00:02"),
        ToolEvent("Edit", {}, event_id="e1", parent_event_id="r", timestamp="2026-01-01T00:00:03"),
    ]

    persistence = detect_branch_persistence(events)
    by_id = {row["branch_id"]: row for row in persistence}
    assert by_id["r"]["descendants"] == 3
    assert by_id["b1"]["descendants"] == 1
    assert by_id["e1"]["descendants"] == 0

    frontier = compute_frontier_width(events)
    assert frontier["max_width"] >= 2
    assert len(frontier["width_by_event"]) == len(events)

    retry = detect_retry_density(events)
    assert retry["local_loop_density"] > 0
    assert retry["retry_density"] > 0


def test_compare_cli_includes_enhanced_sections(tmp_path):
    store_dir = tmp_path / ".causetrace" / "data"
    store_dir.mkdir(parents=True)
    store = JSONStore(store_dir=str(store_dir))
    _write_session(store, "a")
    events = [
        ToolEvent("Read", {}, event_id="r", timestamp="2026-01-01T00:00:00"),
        ToolEvent("Bash", {}, event_id="b", parent_event_id="r", timestamp="2026-01-01T00:00:01"),
        ToolEvent("Edit", {}, event_id="e", parent_event_id="b", timestamp="2026-01-01T00:00:02"),
    ]
    for event in events:
        store.append("b", event)

    result = subprocess.run(
        [sys.executable, "-m", "causetrace", "compare", "a", "b", "--window", "2"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert result.returncode == 0
    assert "Topology distance" in result.stdout
    assert "Branch distribution" in result.stdout
    assert "Root spawning" in result.stdout


def test_corpus_health_report_reports_milestones(monkeypatch, tmp_path):
    import causetrace.annotation as annotation
    import causetrace.metadata as metadata

    monkeypatch.setattr(annotation, "ANNOTATION_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    _write_session(store, "b")
    merge_metadata("a", {"runtime": "codex", "task_type": "bug_fix"})
    save_annotation("b", {"task_type": "exploration", "source": "real_work"})

    summary = summarize_corpus_health(store)
    assert summary["session_count"] == 2
    assert summary["metadata_sessions"] == 1
    assert summary["annotated_sessions"] == 1
    assert summary["milestones"]["scale_1000"]["remaining"] == 998
    assert summary["milestones"]["research_100"]["current"] == 1
    assert summary["task_type_counts"]["bug_fix"] == 1
    assert summary["task_type_counts"]["exploration"] == 1

    report = generate_corpus_health_report(store)
    assert "# Corpus health report" in report
    assert "## Milestones" in report
    assert "Corpus scale" in report
    assert "Need explicit runtime labels" in report
    assert "## Metadata Provenance Audit" in report
    assert "## Missing Metadata Coverage" in report
    assert "## Near Research-Grade Sessions" in report
    assert "strict research-grade sessions" in report


def test_corpus_health_cli_writes_report(monkeypatch, tmp_path):
    import causetrace.annotation as annotation
    import causetrace.metadata as metadata

    monkeypatch.setattr(annotation, "ANNOTATION_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    merge_metadata("a", {"runtime": "codex", "task_type": "bug_fix"})

    output = tmp_path / "health.md"
    result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "health", "--output", str(output)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert result.returncode == 0
    assert output.exists()
    assert "Corpus health report written" in result.stdout


def test_corpus_verify_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "a")
    merge_metadata("a", {"runtime": "codex", "task_type": "bug_fix"})

    snapshot = snapshot_corpus(store, output_dir=tmp_path / "corpus", name="verify-me")

    result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "verify", snapshot["snapshot_dir"]],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert result.returncode == 0
    assert "Snapshot:" in result.stdout
    assert "OK: True" in result.stdout
