# Phase 3D Validation Protocol

Phase 3D validation is descriptive and falsifiable. It does not produce prediction models, anomaly scores, or automated diagnosis.

## Core Rules

1. Every validation must bind to a specific corpus snapshot and version.
2. Every percentage must include its denominator.
3. Every runtime conclusion must disclose runtime distribution.
4. Every task conclusion must disclose task_type distribution.
5. Strong claims require stratified checks, not only aggregate counts.
6. Literature-derived hypotheses remain hypotheses until supported by causetrace corpus evidence.
7. Negative results must be recorded and kept alongside positive ones.
8. Cross-lane aggregation must state the lane composition explicitly.
9. Controlled benchmark lanes may be compared with native lanes only under the controlled benchmark protocol.
10. External trajectory lanes must remain isolated from native conclusions unless explicitly labeled as external generalization.

## Required Validation Context

Each validation note should record:

- corpus snapshot ID or hash
- corpus version
- lane scope
- inclusion criteria
- exclusion criteria
- runtime distribution
- task_type distribution
- outcome distribution
- intervention distribution, when relevant

## Allowed Validation Types

- baseline distribution checks
- lane-separated descriptive comparisons
- stratified association checks
- pre/post intervention comparisons
- controlled benchmark contrasts
- negative result logging

## Disallowed Validation Types

- prediction
- anomaly scoring
- automatic diagnosis
- unstratified universal claims
- unlabelled cross-lane aggregation
- promotion of literature ideas into conclusions without corpus evidence

## Falsification Workflow

For each hypothesis:

1. State the hypothesis explicitly.
2. Define the corpus scope.
3. Define the required evidence.
4. Choose metrics.
5. Check the falsification condition.
6. Record whether the result is:
   - supported
   - weakened
   - not supported
   - inconclusive

## Negative Result Logging

If a hypothesis is not supported, record:

- the corpus snapshot used
- the lane scope
- the metrics computed
- the observed result
- the reason it failed
- the next action

Negative results are part of the research record and must not be deleted or hidden.
