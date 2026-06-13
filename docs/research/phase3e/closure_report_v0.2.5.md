# Phase 3E Closure Report v0.2.5

Phase 3E is the controlled transition and intervention-aware validation layer. This report assesses whether its deliverables are complete and whether the phase can graduate.

## Phase Mission (from charter)

Validate the relationship between events, observations, interventions, workflow conditions and topology transitions under controlled or intervention-aware conditions, without entering Phase 4 theory finalization.

## Corpus Snapshot at Closure

| Metric | Value |
|--------|-------|
| Data sessions | 1,517 |
| Metadata sessions | 992 |
| Events | 131,952 |
| Runtime breadth | 7 |
| Task breadth | 9 |

**Lane distribution**:

| Lane | Sessions | Events |
|------|----------|--------|
| `direct_prompt_native` | 101 | 32,141 |
| `superpowers_workflow_intervention` | 8 | 42,465 |
| `controlled_prompt_morphology` | 3 | 135 |
| `routed_prompt_intervention` | 0 | 0 |
| unlabeled | 880 | 16,160 |

## Deliverable 1: Lane Baseline (3E-1) — COMPLETE

Four lanes characterized with per-lane session counts, event counts, runtime distributions, and task type distributions. Baseline frozen at `lane_baseline_v0.2.5.md`.

Key finding: native lane (101 sessions) is the only lane with statistical mass. Intervention lanes are infrastructure-ready but corpus-sparse.

## Deliverable 2: Intervention Lane Annotation (3E-2) — COMPLETE

Annotation pass reviewed 18 Skill-tool candidate sessions. Results:

| Evidence Level | Count | Action |
|----------------|-------|--------|
| Strong (Skill+PlanMode+Workflow) | 1 | Annotated as superpowers |
| Moderate (Skill+PlanMode) | 2 | Annotated as superpowers |
| Weak (Skill only) | 15 | Deferred (insufficient evidence) |
| Routed | 0 | Honestly reported |

Annotation criteria, evidence levels, and non-inference rule documented in `intervention_lane_annotation_plan_v0.2.5.md` and `intervention_lane_candidates_v0.2.5.md`.

## Deliverable 3: Capture Instrumentation (3E-3) — COMPLETE

- `SOURCES` expanded to accept `routed_prompt_intervention`, `superpowers_workflow_intervention`, `controlled_prompt_morphology`
- `INTERVENTION_LANES` constant defined
- `SessionMetadata` expanded with `intervention_lane`, `causetrace_tags`, `intervention_evidence_source`, `intervention_evidence_level`
- Capture tag format specs defined for prompt-routing-skill, superpowers, and controlled prompt morphology
- Upstream tools updated (prompt-routing-skill SKILL.md, superpowers using-superpowers SKILL.md)
- `causetrace metadata-set --intervention-lane`, `annotate --tag`, `corpus --lane` CLI tooling built
- `corpus lane-count` and `corpus gate-status` subcommands operational
- `detect-tags` command for scanning session JSONL for causetrace_tags YAML blocks

## Deliverable 4: Parser Detection Gate — COMPLETE

Activation gate system implemented: parser detection for an intervention lane requires >=5 explicitly tagged sessions before activation. Rationale: premature detection on 1-2 samples risks encoding heuristic patterns that mislabel future sessions.

| Lane | Tagged | Required | Gate |
|------|--------|----------|------|
| `superpowers_workflow_intervention` | 5 | 5 | **OPEN** |
| `routed_prompt_intervention` | 0 | 5 | BLOCKED |
| `controlled_prompt_morphology` | 0 | 5 | BLOCKED |

Gate opened for superpowers_workflow_intervention on 2026-06-13 after 5 headless Claude Code sessions accumulated workflow intervention tags.

## Deliverable 5: Phase 2 Auto-Detection — COMPLETE

With superpowers gate OPEN, Phase 2 enrichment recognition implemented:

- `_auto_detect_intervention_tags()` scans newly enriched session JSONL for causetrace_tags YAML blocks
- Auto-sets `task_source`, `intervention_lane`, `causetrace_tags`, `intervention_evidence_level`, `intervention_evidence_source` in metadata sidecar
- Wired into all three enrichment handlers (`enrich`, `enrich-opencode`, `enrich-codex`)
- JSON-escaped newline handling fixed in `detect_causetrace_tags`

Tag format detection verified against session 7e8574ec (actual YAML blocks in tool_input). Other 4 tagged sessions carry tags in metadata sidecars only (manually annotated during Phase 3E-3 headless runs).

## Deliverable 6: Tier 2 Readiness — DEFERRED (honest)

Tier 2 requires failure/near-failure density that the current corpus does not provide:

| Criterion | Current | Required | Status |
|-----------|---------|----------|--------|
| Native failure sessions (success=False) | 1 | 10 | NOT MET |
| Native near-failure (human_intervention=True) | 5 | 10 | NOT MET |
| Multi-runtime failure coverage | 6 | 3 | MET |

Failure and near-failure samples remain genuinely rare in real agent behavior. This mirrors the Phase 3D Tier 2 deferral finding. Background acquisition continues.

## Deferred Hypotheses — Carried Forward

### Tier 2 (failure / intervention morphology)

- H-FM-001, H-FM-002, H-IM-001, H-IM-002, H-EV-004, H-EV-005

Target: opportunistic validation when native failure >= 10, near-failure >= 10.

### Tier 3 (controlled benchmark / external lane)

- H-OT-001, H-OT-002, H-EG-001, H-EG-002, H-EV-002, H-EV-003

Activate when controlled benchmark protocol is operational.

### Tier 4 (literature-inspired, registry-only)

- H-EV-001, H-LH-001, H-LH-002

Maintain in registry for future corpus expansion.

## What Phase 3E Did NOT Do (per charter)

- Did not enter Phase 4 theory finalization
- Did not merge intervention lanes into native baseline
- Did not implement heuristic parser detection for blocked lanes
- Did not implement prediction, anomaly detection, or auto-diagnosis
- Did not promote hypotheses to conclusions without corpus-backed validation
- Did not change topology taxonomy or readiness gates without justification
- Did not make cross-lane comparisons beyond trend reporting
- Did not make universal prompt policy recommendations

## Phase 3E Graduation Assessment

Phase 3E infrastructure work is complete. All designed sub-phases (3E-1 through 3E-3) delivered. Phase 2 auto-detection is operational for the one lane that met the gate threshold.

Tier 2 validation is honestly deferred — the bottleneck is corpus failure density, not methodology or infrastructure. This is a data problem, not a design problem.

**Recommendation: Graduate Phase 3E. Mark complete. Carry deferred hypotheses and background acquisition forward.**

## Next Phase

Phase 4 is open for **evidence-graded theory drafting and consolidation only**. It is explicitly NOT open for:

- Prediction, anomaly detection, or automatic diagnosis
- Universal prompt policy defaulting
- Promotion of exploratory findings to stable theory without additional evidence
- Cross-lane aggregation without lane disclosure
- Phase 5 (evaluation / diagnostics)

Phase 4-1 deliverable: theory candidate inventory with evidence grading (`supported`, `supported_with_caveat`, `exploratory`, `inconclusive`, `deferred`). Each candidate must carry corpus snapshot, lane scope, denominator, runtime/task caveats, and falsification condition.

Phase 3E operating rules carry forward into Phase 4 unchanged.
