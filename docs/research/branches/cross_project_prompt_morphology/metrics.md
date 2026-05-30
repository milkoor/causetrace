# Metrics

This study uses four metric groups so that outcome, cost, morphology, and intervention are separated.

## Outcome Metrics

- `success`
- `partial_success`
- `failure`
- `abandoned`
- `human_rescued`
- final patch quality
- test pass status

## Cost Metrics

- `event_count`
- `tool_call_count`
- duration
- `time_to_convergence`
- token cost when available

## Morphology Metrics

- topology label
- `retry_density`
- `branch_density`
- `path_reuse_ratio`
- `transition_entropy`
- `fan-in`
- `branch-collapse`
- `multi_root_exploration`
- `long_session`

## Intervention Metrics

- `AskUserQuestion` count
- `human_intervention`
- `correction_trigger`
- `clarification_needed`
- `manual_takeover`

## Interpretation Rule

Do not use a single metric as proof of improvement.

For example:

- fewer events without better outcomes is not automatically better
- fewer questions without better quality is not automatically better
- shorter traces without lower failure risk are not automatically better
