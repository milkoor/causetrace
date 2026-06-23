# CERC Feedback Integration v0.4

CERC feedback integration turns external execution results into updated gap
projections and experiment priorities. It is a read-only planning layer above
CRDD and below any future execution system.

## Definition

```text
Input:
  external execution feedback
  plus optional experiment plan references

Process:
  normalize observations
  compare observed outcomes with current gap projections
  reprioritize future experimental sampling

Output:
  feedback reports, gap updates, and reprioritized plans
```

## Commands

```bash
causetrace corpus ingest-feedback <feedback.json>
causetrace corpus update-gaps <feedback_report.json>
causetrace corpus reprioritize-experiments <feedback_report.json>
```

## Safety Boundary

Feedback integration does not execute runtimes, synthesize commands, or
upgrade Phase 4 evidence. It only normalizes observed results and updates the
next sampling plan.

## Constraints

- external execution only
- no evidence inflation
- no Phase 4 grade promotion
- no runtime control authority

## Relationship To CERC

CERC plans missing work. Feedback integration updates those plans after external
execution has already happened.
