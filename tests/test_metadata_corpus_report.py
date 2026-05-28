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
from causetrace.corpus import export_dataset, snapshot_corpus
from causetrace.metadata import load_metadata, merge_metadata


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
    assert (snapshot_dir / "sessions" / "s1.jsonl").exists()
    assert (snapshot_dir / "metadata" / "s1.json").exists()
    assert (snapshot_dir / "labels").is_dir()
    assert (snapshot_dir / "benchmarks").is_dir()

    dataset = export_dataset(store)
    assert dataset["session_count"] == 1
    assert dataset["sessions"][0]["metadata"]["runtime"] == "claude"


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
