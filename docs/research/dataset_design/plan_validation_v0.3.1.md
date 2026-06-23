# CERC Plan Validation v0.3.1

Plan validation checks whether a CERC experiment plan is still necessary and
whether it remains safe under the external-only boundary. It is read-only and
does not change corpus data or evidence grades.

## Definition

```text
Input:
  plan directory with experiment_queue.json
  optional gap_report.json

Process:
  validate queue constraints
  compute canonical queue signature
  detect duplicate plans
  compare requested sampling against current gaps

Output:
  validation report and markdown summary
```

## Commands

```bash
causetrace corpus validate-plan docs/research/dataset_design/plans/<experiment_id>
```

## Safety Boundary

Plan validation never executes runtimes, never emits commands, and never
upgrades Phase 4 evidence. It only decides whether a proposed plan is ready,
duplicated, or no longer needed.

## Relationship To CERC

CERC plans missing work. Validation decides whether that work is still needed
and whether the plan already exists elsewhere in the corpus.
