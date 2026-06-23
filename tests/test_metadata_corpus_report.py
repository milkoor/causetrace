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
from causetrace.metadata import load_metadata, load_metadata_provenance, merge_metadata, merge_metadata_provenance
from causetrace.report import generate_corpus_health_report, generate_corpus_origin_report, generate_phase3_readiness_report
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

    save_annotation("s1", {"task_type": "bug_fix", "source": "real_work", "success": True, "data_origin": "native"})
    merged = load_metadata("s1")
    assert merged.task_type == "bug_fix"
    assert merged.task_source == "real_work"
    assert merged.success is True
    assert merged.data_origin == "native"

    provenance = load_metadata_provenance("s1")
    assert provenance["task_type"] == "annotation"
    assert provenance["task_source"] == "annotation"
    assert provenance["success"] == "annotation"
    assert provenance["data_origin"] == "annotation"

    updated = merge_metadata("s1", {"runtime": "codex", "model": "gpt-5", "data_origin": "native"})
    assert updated.runtime == "codex"
    assert updated.data_origin == "native"
    assert load_metadata("s1").model == "gpt-5"


def test_metadata_accepts_behavior_distribution_fields(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    empty = load_metadata("empty").to_dict()
    assert empty == {}

    updated = merge_metadata("s1", {
        "behavior_distribution_tag": "prompt_ablation_v1",
        "bde_generated": "true",
        "experiment_id": "exp_001",
        "control_group_id": "ctrl_a",
    })

    assert updated.behavior_distribution_tag == "prompt_ablation_v1"
    assert updated.bde_generated is True
    assert updated.experiment_id == "exp_001"
    assert updated.control_group_id == "ctrl_a"

    saved = load_metadata("s1")
    assert saved.bde_generated is True


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


def test_corpus_origin_report_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "native")
    _write_session(store, "benchmark")
    merge_metadata("native", {
        "data_origin": "native",
        "runtime": "claude",
        "task_type": "review",
        "task_source": "real_work",
        "success": True,
    })
    merge_metadata("benchmark", {
        "data_origin": "controlled_benchmark",
        "runtime": "codex",
        "task_type": "bug_fix",
        "task_source": "demo",
        "success": False,
    })

    report = generate_corpus_origin_report(store)
    assert "# Corpus origin report" in report
    assert "## Data Origin Counts" in report
    assert "native: 1" in report
    assert "controlled_benchmark: 1" in report
    assert "## Task Source Lane Hints" in report
    assert "demo-lane candidate" in report
    assert "## Missing Data Origin Candidates" in report
    assert "## Phase 3C Guidance" in report

    output = tmp_path / "origins.md"
    result = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "origins", "--output", str(output)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert result.returncode == 0
    assert output.exists()
    assert "Corpus origin report written" in result.stdout


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


def test_crdd_compile_subsets_read_only_and_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import compile_subsets

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "native-success")
    _write_session(store, "native-failure")
    _write_session(store, "intervention")
    _write_session(store, "codex-success")

    merge_metadata("native-success", {
        "data_origin": "native",
        "runtime": "claude",
        "task_type": "feature_add",
        "task_source": "real_work",
        "success": True,
    })
    merge_metadata("native-failure", {
        "data_origin": "native",
        "runtime": "claude",
        "task_type": "bug_fix",
        "task_source": "real_work",
        "success": False,
    })
    merge_metadata("intervention", {
        "data_origin": "native",
        "runtime": "claude",
        "task_type": "exploration",
        "task_source": "superpowers_workflow_intervention",
        "intervention_lane": "superpowers_workflow_intervention",
        "success": True,
        "human_intervention": True,
    })
    merge_metadata("codex-success", {
        "data_origin": "native",
        "runtime": "codex",
        "task_type": "feature_add",
        "task_source": "real_work",
        "success": True,
    })

    before = sorted((tmp_path / "data").glob("*.jsonl"))
    result = compile_subsets(
        store,
        subset_ids=["strict_research_grade", "failure_enriched", "intervention_lane", "balanced_cross_runtime"],
        output_dir=tmp_path / "subsets",
        name="daily",
    )
    after = sorted((tmp_path / "data").glob("*.jsonl"))

    assert before == after
    assert result["source_session_count"] == 4
    assert (tmp_path / "subsets" / "daily" / "index.json").exists()

    manifests = {manifest["subset_id"]: manifest for manifest in result["manifests"]}
    assert manifests["strict_research_grade"]["selected_count"] == 4
    assert manifests["failure_enriched"]["session_ids"] == ["intervention", "native-failure"]
    assert manifests["intervention_lane"]["session_ids"] == ["intervention"]
    assert manifests["balanced_cross_runtime"]["selected_count"] == 2
    assert 0 <= manifests["strict_research_grade"]["comparability"]["score"] <= 1
    assert manifests["failure_enriched"]["bias_register"]["failure_scarcity"]["present"] is True

    cli_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causetrace",
            "corpus",
            "compile-subsets",
            "--subset",
            "strict_research_grade",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )

    assert cli_result.returncode == 0
    assert "Dry-run compiled CRDD subsets" in cli_result.stdout
    assert "strict_research_grade" in cli_result.stdout


def test_cerc_gap_analysis_and_experiment_plan_are_external_only(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import analyze_gaps, plan_experiments

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))

    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "failure")
    _write_session(store, "success")
    merge_metadata("failure", {
        "runtime": "codex",
        "task_type": "bug_fix",
        "task_source": "real_work",
        "success": False,
    })
    merge_metadata("success", {
        "runtime": "claude",
        "task_type": "feature_add",
        "task_source": "real_work",
        "success": True,
    })

    gap_report = analyze_gaps(store, subset_ids=["failure_enriched"])
    assert gap_report["subset_gaps"][0]["subset_id"] == "failure_enriched"
    assert gap_report["subset_gaps"][0]["current_sessions"] == 1
    assert gap_report["subset_gaps"][0]["missing_sessions"] == 49

    before = sorted((tmp_path / "data").glob("*.jsonl"))
    result = plan_experiments(
        store,
        target_subset="failure_enriched",
        output_dir=tmp_path / "plans",
        name="exp_failure_test",
    )
    after = sorted((tmp_path / "data").glob("*.jsonl"))
    queue = result["plan"]["experiment_queue"]

    assert before == after
    assert result["written"] is True
    assert (tmp_path / "plans" / "exp_failure_test" / "gap_report.json").exists()
    assert (tmp_path / "plans" / "exp_failure_test" / "experiment_queue.json").exists()
    assert (tmp_path / "plans" / "exp_failure_test" / "experiment_plan.md").exists()
    assert queue["execution_mode"] == "external_only"
    assert queue["must_not_execute"] is True
    assert queue["evidence_status"] == "planned_not_observed"
    assert queue["observed_session_count"] == 0
    assert queue["phase4_grade_effect"] == "none"
    assert queue["validation"]["ok"] is True
    assert all(scenario["descriptor_only"] is True for scenario in queue["bde_scenarios"])
    assert "command" not in json.dumps(queue)


def test_cerc_cli_analyze_and_plan_dry_run(tmp_path):
    home = tmp_path / "home"
    store = JSONStore(store_dir=str(home / ".causetrace" / "data"))
    _write_session(store, "failure")

    env = {**os.environ, "HOME": str(home)}
    metadata_dir = home / ".causetrace" / "metadata"
    metadata_dir.mkdir(parents=True)
    (metadata_dir / "failure.json").write_text(json.dumps({
        "session_id": "failure",
        "runtime": "codex",
        "task_type": "bug_fix",
        "task_source": "real_work",
        "success": False,
    }))

    gaps = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "analyze-gaps", "--subset", "failure_enriched"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert gaps.returncode == 0
    assert "CERC gap report" in gaps.stdout
    assert "failure_enriched" in gaps.stdout

    plan = subprocess.run(
        [
            sys.executable,
            "-m",
            "causetrace",
            "corpus",
            "plan-experiments",
            "--target",
            "failure_enriched",
            "--dry-run",
            "--name",
            "exp_cli_dry",
            "--output-dir",
            str(tmp_path / "cli-plans"),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert plan.returncode == 0
    assert "Dry-run planned CERC experiment" in plan.stdout
    assert "Execution mode: external_only" in plan.stdout
    assert "Must not execute: True" in plan.stdout
    assert not (tmp_path / "cli-plans" / "exp_cli_dry").exists()


def test_bde_interfaces_are_metadata_only():
    from causetrace.bde import BehaviorScenario, FailureInjection, MultiAgentSimulation, PromptVariant, TaskDistribution

    scenario = BehaviorScenario(
        scenario_id="scn_1",
        task="fix failing test",
        behavior_distribution_tag="ablation",
        prompt_variants=(PromptVariant("A", "minimal"), PromptVariant("B", "structured")),
        experiment_id="exp_1",
        control_group_id="control",
    )
    distribution = TaskDistribution("dist_1", ("bug_fix", "feature_add"), {"bug_fix": 0.5})
    failure = FailureInjection("fail_1", "ambiguous_requirements", target_task_type="bug_fix")
    simulation = MultiAgentSimulation("sim_1", ("planner", "executor"))

    assert scenario.prompt_variants[0].variant_id == "A"
    assert distribution.task_types == ("bug_fix", "feature_add")
    assert failure.failure_mode == "ambiguous_requirements"
    assert simulation.agent_roles == ("planner", "executor")


# ── classify-unlabeled tests ──────────────────────────────────────────


def test_classify_unlabeled_dry_run_no_write(monkeypatch, tmp_path):
    """classify-unlabeled --dry-run must not write to metadata sidecars."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    # Write a session that qualifies for high-confidence classification
    sid = "test-native-001"
    (mdir / f"{sid}.json").write_text(json.dumps({
        "session_id": sid,
        "data_origin": "native",
        "task_source": "real_work",
        "runtime": "anthropic",
    }))

    _print_classify_unlabeled(min_confidence="high", apply_confirmed=False)

    # Metadata must NOT be modified
    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert "intervention_lane" not in meta


def test_classify_unlabeled_apply_confirmed_writes_high_confidence(monkeypatch, tmp_path):
    """--apply-confirmed writes intervention_lane for high-confidence proposals."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    sid = "test-native-002"
    (mdir / f"{sid}.json").write_text(json.dumps({
        "session_id": sid,
        "data_origin": "native",
        "task_source": "real_work",
        "runtime": "anthropic",
    }))

    _print_classify_unlabeled(min_confidence="high", apply_confirmed=True)

    # Metadata must now have intervention_lane
    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert meta.get("intervention_lane") == "direct_prompt_native"

    # Provenance must be written
    prov = json.loads((mdir / f"{sid}.provenance.json").read_text())
    assert prov.get("intervention_lane") == "classified_from_explicit_metadata"


def test_classify_unlabeled_unknown_unchanged(monkeypatch, tmp_path):
    """data_origin=unknown sessions must remain unmodified."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    sid = "test-unknown-001"
    original = {"session_id": sid, "data_origin": "unknown", "runtime": "codex"}
    (mdir / f"{sid}.json").write_text(json.dumps(original))

    _print_classify_unlabeled(min_confidence="high", apply_confirmed=True)

    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert "intervention_lane" not in meta
    assert meta.get("data_origin") == "unknown"


def test_classify_unlabeled_preserves_existing_lane(monkeypatch, tmp_path):
    """Existing intervention_lane must not be overwritten."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    sid = "test-sp-001"
    (mdir / f"{sid}.json").write_text(json.dumps({
        "session_id": sid,
        "data_origin": "native",
        "task_source": "superpowers_workflow_intervention",
        "intervention_lane": "superpowers_workflow_intervention",
        "runtime": "claude-code",
    }))

    _print_classify_unlabeled(min_confidence="high", apply_confirmed=True)

    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert meta.get("intervention_lane") == "superpowers_workflow_intervention"


def test_classify_unlabeled_medium_not_applied(monkeypatch, tmp_path):
    """Medium-confidence proposals are never applied even with --apply-confirmed."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    sid = "test-medium-001"
    (mdir / f"{sid}.json").write_text(json.dumps({
        "session_id": sid,
        "data_origin": "native",
        "runtime": "anthropic",
    }))

    _print_classify_unlabeled(min_confidence="medium", apply_confirmed=True)

    # Medium confidence => not applied
    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert "intervention_lane" not in meta


def test_classify_unlabeled_high_confidence_not_applied_if_tags(monkeypatch, tmp_path):
    """Sessions with causetrace_tags are skipped even if native+real_work."""
    import causetrace.metadata as metadata
    from causetrace.cli import _print_classify_unlabeled

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    mdir = Path(metadata.METADATA_DIR)
    mdir.mkdir(parents=True)

    sid = "test-tagged-001"
    (mdir / f"{sid}.json").write_text(json.dumps({
        "session_id": sid,
        "data_origin": "native",
        "task_source": "real_work",
        "causetrace_tags": ["superpowers-workflow"],
        "runtime": "claude-code",
    }))

    _print_classify_unlabeled(min_confidence="high", apply_confirmed=True)

    meta = json.loads((mdir / f"{sid}.json").read_text())
    assert "intervention_lane" not in meta


def test_cerc_feedback_ingest_update_and_reprioritize(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import ingest_feedback, plan_experiments, reprioritize_experiments, update_gaps

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    _write_session(store, "s2")
    merge_metadata("s1", {"runtime": "codex", "task_type": "bug_fix", "task_source": "real_work", "success": False})
    merge_metadata("s2", {"runtime": "claude", "task_type": "review", "task_source": "real_work", "success": True})

    plan_result = plan_experiments(
        store,
        target_subset="failure_enriched",
        required_sessions=7,
        name="exp_feedback",
        output_dir=tmp_path / "plans",
    )
    plan_dir = Path(plan_result["output_dir"])
    payload_path = tmp_path / "feedback.json"
    payload_path.write_text(json.dumps({
        "experiment_id": "exp_feedback",
        "target_subset": "failure_enriched",
        "observed_sessions": [
            "s1",
            "s2",
            {"label": "missing-session", "runtime": "opencode"},
        ],
    }))

    report = ingest_feedback(store, input_path=payload_path, plan_dir=plan_dir, output_dir=tmp_path / "feedback")
    assert report["constraints"]["external_only"] is True
    assert report["observed_count"] == 3
    assert report["resolved_count"] == 2
    assert report["unresolved_session_ids"] == ["missing-session"]
    assert report["plan_queue"]["experiment_id"] == "exp_feedback"
    assert report["gap_projection"]["target_sessions"] == 7
    assert report["gap_projection"]["remaining_sessions"] == 4
    assert (Path(report["output_dir"]) / "feedback_report.json").exists()

    gap_update = update_gaps(store, feedback_report=report, output_dir=tmp_path / "feedback")
    assert gap_update["status"] in {"met", "under_target"}
    assert gap_update["priority_hint"] in {"reprioritize", "hold"}
    assert (Path(gap_update["output_dir"]) / "gap_update.json").exists()

    prioritized = reprioritize_experiments(store, feedback_report=report, output_dir=tmp_path / "feedback")
    assert prioritized["constraints"]["no_execution"] is True
    assert prioritized["constraints"]["no_evidence_inflation"] is True
    assert prioritized["priorities"]
    assert (Path(prioritized["output_dir"]) / "reprioritized_plan.json").exists()


def test_cerc_feedback_cli_commands(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import plan_experiments

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    merge_metadata("s1", {"runtime": "codex", "task_type": "bug_fix", "task_source": "real_work", "success": False})

    plan_result = plan_experiments(store, target_subset="failure_enriched", name="exp_cli", output_dir=tmp_path / "plans")
    plan_dir = Path(plan_result["output_dir"])
    payload_path = tmp_path / "feedback.json"
    payload_path.write_text(json.dumps({
        "experiment_id": "exp_cli",
        "target_subset": "failure_enriched",
        "observed_sessions": ["s1"],
    }))

    ingest_cmd = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "ingest-feedback", str(payload_path), "--plan-dir", str(plan_dir), "--output-dir", str(tmp_path / "feedback")],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert ingest_cmd.returncode == 0
    assert "External only: True" in ingest_cmd.stdout

    report_path = Path(tmp_path / "feedback" / "exp_cli" / "feedback_report.json")
    update_cmd = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "update-gaps", str(report_path), "--output-dir", str(tmp_path / "feedback")],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert update_cmd.returncode == 0
    assert "Priority hint:" in update_cmd.stdout

    reprioritize_cmd = subprocess.run(
        [sys.executable, "-m", "causetrace", "corpus", "reprioritize-experiments", str(report_path), "--output-dir", str(tmp_path / "feedback")],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert reprioritize_cmd.returncode == 0
    assert "Top priority:" in reprioritize_cmd.stdout


def test_cerc_plan_validation_detects_duplicates(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import plan_experiments, validate_experiment_plan

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    merge_metadata("s1", {"runtime": "codex", "task_type": "bug_fix", "task_source": "real_work", "success": False})

    plan_a = plan_experiments(
        store,
        target_subset="failure_enriched",
        required_sessions=5,
        name="exp_plan_a",
        output_dir=tmp_path / "plans",
    )
    plan_b = plan_experiments(
        store,
        target_subset="failure_enriched",
        required_sessions=5,
        name="exp_plan_b",
        output_dir=tmp_path / "plans",
    )

    report = validate_experiment_plan(store, plan_dir=Path(plan_b["output_dir"]), output_dir=tmp_path / "plan-validation")
    assert report["constraints"]["external_only"] is True
    assert report["validation"]["status"] == "duplicate"
    assert report["duplicate_plans"]
    assert Path(report["output_dir"]).joinpath("plan_validation.json").exists()
    assert Path(report["output_dir"]).joinpath("plan_validation.md").exists()


def test_cerc_plan_validation_cli(monkeypatch, tmp_path):
    import causetrace.metadata as metadata
    from causetrace.crdd import plan_experiments

    monkeypatch.setattr(metadata, "METADATA_DIR", str(tmp_path / "metadata"))
    store = JSONStore(store_dir=str(tmp_path / "data"))
    _write_session(store, "s1")
    merge_metadata("s1", {"runtime": "codex", "task_type": "bug_fix", "task_source": "real_work", "success": False})

    plan_result = plan_experiments(
        store,
        target_subset="failure_enriched",
        required_sessions=5,
        name="exp_plan_cli",
        output_dir=tmp_path / "plans",
    )

    cmd = subprocess.run(
        [
            sys.executable,
            "-m",
            "causetrace",
            "corpus",
            "validate-plan",
            str(Path(plan_result["output_dir"])),
            "--output-dir",
            str(tmp_path / "plan-validation"),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert cmd.returncode == 0
    assert "Validation ok:" in cmd.stdout
    assert "Status:" in cmd.stdout
