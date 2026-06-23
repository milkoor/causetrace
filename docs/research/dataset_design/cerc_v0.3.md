# Causal Experiment Requirement Compiler v0.3

CERC is the experiment planning layer above CRDD. It turns observed corpus gaps
into external-only experiment requirements. It does not execute agents, simulate
execution, or upgrade evidence grades.

## Definition

```text
Input:
  observed runtime corpus

Process:
  gap analysis
  subset imbalance detection
  experimental requirement derivation

Output:
  structured experiment plans and execution queues
  with execution_mode=external_only
```

## Commands

```bash
causetrace corpus analyze-gaps
causetrace corpus plan-experiments --target failure_enriched
causetrace corpus ingest-feedback <feedback.json>
causetrace corpus update-gaps <feedback_report.json>
causetrace corpus reprioritize-experiments <feedback_report.json>
```

`analyze-gaps` reports subset coverage against CRDD targets. `plan-experiments`
builds a plan directory with:

```text
gap_report.json
experiment_queue.json
experiment_plan.md
```

## Safety Boundary

Every CERC queue must preserve these fields:

```json
{
  "execution_mode": "external_only",
  "must_not_execute": true,
  "evidence_status": "planned_not_observed",
  "observed_session_count": 0,
  "phase4_grade_effect": "none"
}
```

The queue must not contain shell commands, agent commands, API calls, or runtime
execution payloads.

## Principles

### No Execution Authority

CERC never runs, launches, controls, or simulates agent runtimes. It only emits
requirements for external execution.

### No Evidence Inflation

Planned sessions are not observed sessions. A plan can identify a sampling gap,
but it cannot increase denominators or support claims until traces are actually
captured by `causetrace`.

### No Theory Promotion

CERC plans do not change Phase 4 evidence grades. They may prepare future
sampling work that could later satisfy Phase 4-3 trigger conditions.

## Current Targets

Default v0.3 targets:

| Subset | Target sessions | Purpose |
| --- | ---: | --- |
| `strict_research_grade` | 150 | Baseline comparable corpus |
| `balanced_cross_runtime` | 20 | Runtime-balanced comparison input |
| `failure_enriched` | 50 | Failure and near-failure boundary study |
| `intervention_lane` | 15 | Control-vs-intervention study input |

These are planning targets, not evidence thresholds.

## Relationship To CRDD

CRDD compiles existing comparable subsets. CERC compiles missing experimental
work. CRDD says what can be compared now; CERC says what must be collected next.

## Feedback Integration

Feedback integration consumes external execution results after collection. It
does not execute runtimes, synthesize commands, or change Phase 4 evidence
grading. It only updates gap projections and future priorities.
