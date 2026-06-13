# Causetrace CLI Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Five small independent CLI/docs enhancements to causetrace

**Architecture:** Each task touches 1-2 files. No shared state. No new dependencies. All changes in cli.py, annotation.py, or docs.

**Tech Stack:** Python 3, argparse, existing causetrace metadata system

---

### Task A: annotate --tag filter

**Files:**
- Modify: `causetrace/cli.py` (add --tag argument + handler logic)

- [ ] **Step 1: Add --tag argument to annotate subparser**

In `causetrace/cli.py`, find the `p_an` annotate subparser definition (~line 235) and add:

```python
p_an.add_argument("--tag", help="Filter sessions by causetrace_tags value")
```

- [ ] **Step 2: Add tag filtering in _handle_annotate**

In the `_handle_annotate` function, after computing the session list but before printing, filter by tag if `--tag` is set:

```python
if args.tag:
    filtered = []
    for sid in sessions:
        meta = load_annotation(sid)
        tags = meta.get("causetrace_tags", [])
        if args.tag in tags:
            filtered.append(sid)
    sessions = filtered
```

- [ ] **Step 3: Test**

```bash
causetrace annotate --list --tag superpowers-workflow
```

Expected: lists sessions with matching causetrace_tags (currently 0)

- [ ] **Step 4: Commit**

### Task B: ea49a219 investigation

**Files:**
- Read only: `~/.causetrace/data/ea49a219-*.jsonl`

- [ ] **Step 1: Check source project**

```bash
causetrace enrich-sessions 2>&1 | grep ea49a219
```

- [ ] **Step 2: Read the JSONL file**

```bash
wc -l ~/.causetrace/data/ea49a219-*.jsonl
head -3 ~/.causetrace/data/ea49a219-*.jsonl
```

- [ ] **Step 3: Report root cause**

Compare source line count (15 from enrich output) vs event count. If 1:1, source is a tiny session. If events < lines, parsing is dropping events.

- [ ] **Step 4: Document finding in notes** (no commit needed if no code change)

### Task C: corpus lane-count

**Files:**
- Modify: `causetrace/cli.py` (~25 lines)

- [ ] **Step 1: Add lane-count subcommand to corpus subparser**

In `causetrace/cli.py`, find the corpus subparser area and add:

```python
p_cr_lane = p_cr_sub.add_parser("lane-count", help="Print per-lane session and event counts")
```

- [ ] **Step 2: Add handler logic in _handle_corpus**

```python
if args.corpus_command == "lane-count":
    from collections import Counter
    import os, json
    meta_dir = os.path.expanduser("~/.causetrace/metadata")
    data_dir = os.path.expanduser("~/.causetrace/data")
    lanes = Counter()
    lane_events = Counter()
    for f in os.listdir(meta_dir):
        if f.endswith(".json") and not f.endswith(".provenance.json"):
            sid = f.replace(".json", "")
            with open(os.path.join(meta_dir, f)) as mf:
                meta = json.load(mf)
            ts = meta.get("task_source", "")
            do = meta.get("data_origin", "")
            lane = "unlabeled"
            if ts in ("routed_prompt_intervention", "superpowers_workflow_intervention", "controlled_prompt_morphology"):
                lane = ts
            elif do in ("native", "real_work", "direct_prompt_native") and ts == "real_work":
                lane = "direct_prompt_native"
            jf = os.path.join(data_dir, f"{sid}.jsonl")
            ev = 0
            if os.path.exists(jf):
                with open(jf) as ef:
                    for _ in ef:
                        ev += 1
            lanes[lane] += 1
            lane_events[lane] += ev
    print(f"{'Lane':45s} {'Sessions':>8s} {'Events':>10s}")
    print("-" * 65)
    for lane in ["direct_prompt_native", "superpowers_workflow_intervention", "controlled_prompt_morphology", "routed_prompt_intervention", "unlabeled"]:
        if lanes[lane] or lane != "unlabeled":
            print(f"{lane:45s} {lanes[lane]:8d} {lane_events[lane]:10d}")
    return
```

- [ ] **Step 3: Test**

```bash
causetrace corpus lane-count
```

Expected: formatted table with 5 rows

- [ ] **Step 4: Run existing tests**

```bash
python3 -m pytest tests/ -v --tb=short
```

Expected: all 195 pass

- [ ] **Step 5: Commit**

### Task D: SOURCES review

**Files:**
- Read: `causetrace/annotation.py`

- [ ] **Step 1: Read SOURCES dict**

Verify it contains: real_work, demo, proxy, routed_prompt_intervention, superpowers_workflow_intervention, controlled_prompt_morphology, unknown

- [ ] **Step 2: Cross-reference Phase 3E README**

All 4 lanes have corresponding SOURCES values. No gaps.

- [ ] **Step 3: Report finding** (no commit needed)

### Task E: README lane table update

**Files:**
- Modify: `docs/research/phase3e/README.md`

- [ ] **Step 1: Update lane counts in Current State section**

Change the lane table to reflect latest counts (101/3/3/0 if unchanged from current).

- [ ] **Step 2: Run git diff --check**

- [ ] **Step 3: Commit**
