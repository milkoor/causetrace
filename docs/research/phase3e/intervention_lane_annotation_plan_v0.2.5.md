# Phase 3E-2 Intervention Lane Annotation Plan v0.2.5

This document defines the annotation pass for Phase 3E-2. The goal is to identify and label existing sessions that have explicit evidence of intervention lanes, not to validate hypotheses.

## Position

- Phase 3D: complete
- Phase 3E: active
- Phase 3E-1: complete (lane baseline)
- Phase 3E-2: **active** (annotation pass)
- Phase 4: not open

## Motivation

Phase 3E-1 found:

| Lane | Sessions | Status |
|------|----------|--------|
| `direct_prompt_native` | 101 | baseline-ready |
| `controlled_prompt_morphology` | 3 | pilot only |
| `routed_prompt_intervention` | 0 | no labeled data |
| `superpowers_workflow_intervention` | 0 | no labeled data |

The bottleneck is not validation methodology — it is annotation coverage. Phase 3E-2 addresses this by identifying sessions with explicit intervention evidence and assigning lane labels.

## Annotation Targets (First Stage)

| Lane | Current | Target | Note |
|------|---------|--------|------|
| `routed_prompt_intervention` | 0 | 5–10 | if evidence exists |
| `superpowers_workflow_intervention` | 0 | 5–10 | if evidence exists |
| `controlled_prompt_morphology` | 3 | preserve + identify | do not inflate |

Targets are aspirational. If evidence does not exist, the lane stays at 0 honestly — do not fabricate labels.

## Annotation Criteria

### `routed_prompt_intervention`

**Required evidence** (at least one):

- `prompt-routing-skill` invoked via `Skill` tool
- `routed-prompt` label in metadata or event content
- `causetrace-prompt-posture` label present
- Routing decision record (skill output selecting `minimal_prompt`, `human_structured_prompt`, or `expanded_constrained_prompt`)
- Task framed by routing template with explicit posture selection

**Excluded** (not sufficient):

- Prompt looks structured or template-like
- File path containing `prompt-routing-skill` (e.g., directory listing)
- Discussion of routing concepts without actual routing

### `superpowers_workflow_intervention`

**Required evidence** (at least one):

- `Skill` tool used to invoke a superpowers skill (e.g., `superpowers:brainstorming`, `superpowers:using-superpowers`)
- `EnterPlanMode` / `ExitPlanMode` tools used (structured plan-act workflow)
- `Workflow` tool used
- Superpowers plugin installation or configuration present in session
- `TaskCreate`/`TaskUpdate`/`TaskStop` tools used as part of structured task management (superpowers workflow pattern)

**Evidence strength levels**:

| Level | Criteria | Examples |
|-------|----------|----------|
| Strong | Skill + PlanMode + Workflow tools all present | `f4e2f505`, `1ecb1c32` |
| Moderate | Skill + PlanMode present | `6e86a3e4`, `1a00157a` |
| Weak | Skill tool present in isolation | single Skill invocation, no PlanMode |

Only Strong and Moderate evidence qualifies for annotation. Weak evidence should be noted but not labeled.

**Excluded** (not sufficient):

- Prompt is detailed or structured
- Agent self-describes as thorough
- Multi-step execution without explicit workflow tooling

### `controlled_prompt_morphology`

**Required evidence** (at least one):

- `data_origin=controlled_benchmark` in metadata
- A/B/C prompt variant records in event content
- Cross-project prompt morphology pilot records
- Repeated same-task with different prompt variants
- Explicit experimental prompt variant documentation

**Excluded** (not sufficient):

- Prompt was expanded or rewritten (normal workflow, not controlled experiment)
- General "a/b" mentions in code or documentation
- Single-use prompt template

## Non-Inference Rule

> Do not infer intervention lane solely from prompt length, prompt quality, structured wording, or execution complexity. Intervention labels require explicit evidence traceable to tool usage, metadata fields, or documented workflow markers.

If evidence is ambiguous, record the session as a candidate with `annotation_decision=deferred` and state what additional evidence would resolve it.

## Annotation Process

1. **Identify candidates** — scan corpus for tool-usage signals and metadata patterns
2. **Review evidence** — inspect event content for explicit intervention markers
3. **Assign lane** — label with `task_source` or `data_origin` in metadata sidecar
4. **Record decision** — log in `intervention_lane_candidates_v0.2.5.md` with evidence and rationale
5. **Do not remove from native** — sessions reclassified from native must be documented, not silently moved

## Lane Reclassification Rule

Sessions currently labeled `data_origin=native` / `task_source=real_work` that show explicit superpowers workflow evidence may be reclassified to `superpowers_workflow_intervention`. When this happens:

- Record the original label
- Document the reclassification evidence
- Update both lane counts
- Do not delete the session from native analysis history — note the reclassification date

This is the only valid reclassification path at this stage. Do not reclassify to `routed_prompt_intervention` or `controlled_prompt_morphology` without explicit evidence specific to those lanes.

## Non-Goals

- Do not annotate all unlabeled sessions — only those with intervention evidence
- Do not change topology taxonomy
- Do not enter Phase 4
- Do not make cross-lane validation claims
- Do not fabricate labels to hit targets

## Current State

Annotation pass begins. Candidate review table at `intervention_lane_candidates_v0.2.5.md`.

Corpus scan found:
- 18 sessions with `Skill` tool usage (superpowers indicator)
- 0 sessions with genuine `prompt-routing-skill` usage
- 3 sessions with `controlled_benchmark` data_origin
- 2 sessions with `proxy` task_source (potential external trajectory)

## Next Action

Review each candidate, assign labels where evidence supports, record decisions in the candidate table.
