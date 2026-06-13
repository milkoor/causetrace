# Phase 3E-3 Intervention Capture Instrumentation Plan v0.2.5

This document defines the instrumentation plan for making intervention lane metadata capturable at acquisition time, rather than requiring post-hoc manual annotation.

## Position

- Phase 3D: complete
- Phase 3E: active
- Phase 3E-1: complete (lane baseline)
- Phase 3E-2: complete (annotation pass)
- Phase 3E-3: **active** (capture instrumentation)
- Phase 4: not open

## Motivation

Phase 3E-2 found:

| Lane | Sessions | Acquisition Gap |
|------|----------|-----------------|
| `superpowers_workflow_intervention` | 3 | Requires manual evidence review |
| `routed_prompt_intervention` | 0 | No capture path exists |
| `controlled_prompt_morphology` | 3 | Labeled via data_origin only |

The bottleneck is no longer annotation methodology — it is capture infrastructure. Intervention lane evidence must be capturable at acquisition time through explicit, auditable metadata or tags, not retroactively inferred from event content.

## Mission

Make workflow intervention lanes capturable at acquisition time. The goal is that a session created under `prompt-routing-skill` or `superpowers` workflow should carry its intervention provenance automatically into the causetrace metadata system.

## Design Principle

Intervention metadata lives in the existing sidecar annotation system (`~/.causetrace/metadata/`). No core schema (ToolEvent fields) changes. No new database. No new file format.

The only code change is expanding the `SOURCES` enum to accept intervention lane values, enabling `causetrace metadata-set --task-source superpowers_workflow_intervention` to work.

## Minimal Intervention Metadata

### Field: `task_source` (expand existing)

Add three values to `SOURCES` in `causetrace/annotation.py`:

| Value | Definition |
|-------|-----------|
| `routed_prompt_intervention` | Task framed by `prompt-routing-skill`; posture selected before execution |
| `superpowers_workflow_intervention` | Structured workflow plugin (superpowers) changed execution shape |
| `controlled_prompt_morphology` | Controlled prompt comparison, A/B/C variant, or pilot run |

These join existing `real_work`, `demo`, `proxy`, `unknown`.

Existing lane assignment logic (Phase 3E-1 baseline) uses `task_source` as the primary lane discriminator. Expanding `SOURCES` completes the loop: acquisition → metadata → lane assignment.

### Field: `intervention_evidence_level` (new, optional sidecar)

| Value | Meaning |
|-------|---------|
| `none` | No intervention evidence found |
| `weak` | Skill tool present, no PlanMode/Workflow |
| `moderate` | Skill + PlanMode present |
| `strong` | Skill + PlanMode + Workflow present |

Populated by parser/enrichment or manual annotation. Stored in metadata sidecar only. Not a core schema field.

### Field: `intervention_evidence_source` (new, optional sidecar)

| Value | Meaning |
|-------|---------|
| `prompt-routing-skill` | Evidence from prompt-routing-skill tags |
| `superpowers-workflow` | Evidence from superpowers workflow markers |
| `prompt-morphology-pilot` | Evidence from controlled prompt experiment |
| `manual_annotation` | Evidence from human review (Phase 3E-2 pattern) |

### Field: `prompt_posture` (new, optional sidecar)

| Value | Meaning |
|-------|---------|
| `minimal_prompt` | Minimal direct prompt (no framing) |
| `expanded_constrained_prompt` | Expanded prompt with constraints |
| `human_structured_prompt` | Human-structured detailed prompt |
| `routed_prompt` | Posture selected by routing skill |
| `unknown` | Posture not recorded |

Populated by prompt-routing-skill or manual annotation.

### Field: `routing_decision_id` (new, optional sidecar)

Identifier for the routing decision that selected the prompt posture. Allows tracing a session back to the routing event.

### Field: `workflow_label` (new, optional sidecar)

Free-text or structured label describing the workflow intervention (e.g., `audit_plan_execute_verify`, `brainstorm_plan_act_review`).

### Field: `notes` (existing, already in annotate CLI)

Use existing `--notes` flag on `causetrace annotate` for free-text intervention documentation.

## Capture Requirements

### For `prompt-routing-skill`

The `prompt-routing-skill` must emit explicit, machine-readable tags in its output that causetrace can capture. Minimum:

```yaml
causetrace_tags:
  - prompt-routing
  - routed-prompt
  - causetrace-prompt-posture
prompt_posture: expanded_constrained_prompt
routing_decision_id: <uuid>
selected_prompt_style: expanded_constrained_prompt
routing_reason: task_complexity_high
```

When causetrace enrichment encounters these tags in tool output or event content, it should set:

```
task_source = routed_prompt_intervention
prompt_posture = <value from routing output>
intervention_evidence_source = prompt-routing-skill
intervention_evidence_level = strong
```

### For superpowers workflows

Superpowers workflow executions must emit explicit markers. Minimum:

```yaml
causetrace_tags:
  - superpowers-workflow
workflow_intervention: superpowers
workflow_mode: audit_plan_execute_verify
evidence_level: strong
```

When causetrace enrichment encounters these markers:

```
task_source = superpowers_workflow_intervention
workflow_label = <value from workflow output>
intervention_evidence_source = superpowers-workflow
intervention_evidence_level = strong
```

### For controlled prompt morphology

Controlled prompt experiments must carry explicit pilot labels:

```yaml
causetrace_tags:
  - controlled-prompt-morphology
  - prompt-pilot
prompt_variant: A | B | C
experiment_id: <uuid>
```

When causetrace enrichment encounters these:

```
data_origin = controlled_benchmark
task_source = controlled_prompt_morphology
intervention_evidence_source = prompt-morphology-pilot
```

### Fallback: tool-usage detection (moderate only)

When explicit tags are absent but tool-usage patterns match, enrichment may set moderate evidence:

| Tool Pattern | Lane | Evidence Level |
|-------------|------|---------------|
| `Skill` + `EnterPlanMode` + `Workflow` | `superpowers_workflow_intervention` | strong |
| `Skill` + `EnterPlanMode` | `superpowers_workflow_intervention` | moderate |
| `Skill` only | none | weak (not annotated) |

This fallback is secondary to explicit tags. Explicit tags always take precedence.

## Parser / Enrichment Recognition Plan

### Phase 1: Expand SOURCES (now)

Expand `SOURCES` in `causetrace/annotation.py` to include the three intervention lane values. This enables `causetrace metadata-set --task-source superpowers_workflow_intervention` and `causetrace annotate --source superpowers_workflow_intervention`.

No other code changes in this phase. This is a one-line-per-value expansion.

### Phase 2: Tag detection in enrichment (future)

When prompt-routing-skill and superpowers begin emitting structured tags, add detection logic to the enrichment pipeline that:

1. Scans tool output for `causetrace_tags` patterns
2. Extracts `prompt_posture`, `routing_decision_id`, `workflow_label`
3. Sets `task_source`, `intervention_evidence_level`, `intervention_evidence_source` in metadata sidecar

This is deferred until the tag format is stabilized and at least 5 sessions carry the tags.

### Phase 3: Tool-usage heuristic (future, optional)

Add a lightweight post-enrichment pass that detects `Skill` + `PlanMode` + `Workflow` tool patterns and suggests intervention lane labeling. This is a suggestion, not automatic labeling — human review gates moderate/strong assignments.

## Non-Goals

- No core schema (ToolEvent) changes
- No new database or file format
- No automatic intervention lane labeling without explicit evidence
- No promotion of weak (Skill-only) evidence to intervention lane
- No intervention effectiveness conclusions
- No universal prompt policy defaults
- No Phase 4 entry
- No prediction, anomaly detection, or auto-diagnosis

## Current State

Phase 3E-3 begins with the minimal code change: expanding `SOURCES` to accept intervention lane values. The tag format specifications above are requirements documents for `prompt-routing-skill` and `superpowers` — they describe what causetrace needs to capture, not what causetrace implements today.

## Next Action After Instrumentation

Once capture tags are emitted by intervention tools and recognized by causetrace enrichment, Phase 3E-4 can begin opportunistic Tier 2 validation when the intervention lanes naturally accumulate sessions.
