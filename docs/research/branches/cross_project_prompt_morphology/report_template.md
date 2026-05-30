# Report Template

Use this template for a single study run or pilot batch.

## Metadata

- project
- task id / task label
- runtime
- prompt variant
- repo commit or reset point
- run order

## Outcome Summary

- success
- partial_success
- failure
- abandoned
- human_rescued
- final patch quality
- test pass status

## Morphology Summary

- topology label
- `retry_density`
- `branch_density`
- `path_reuse_ratio`
- `transition_entropy`
- `fan-in`
- `branch-collapse`
- `multi_root_exploration`
- `long_session`

## Intervention Summary

- `AskUserQuestion` count
- `human_intervention`
- `correction_trigger`
- `clarification_needed`
- `manual_takeover`

## Interpretation

- what changed under the prompt variant
- what did not change
- what remains uncertain
- whether the prompt variant is worth adopting for this project
