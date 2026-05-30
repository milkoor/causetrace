# Phase 3D Tier 2 Triage v0.2.5

This note splits the current Tier 2 seed pool into practical acquisition buckets.

It is not a failure taxonomy and it is not a validation result. It is a triage aid for the next acquisition pass.

## Bucket 1: Failure Anchor

- `aider_902f54e8`
  - runtime: `aider`
  - task_type: `review`
  - task_source: `real_work`
  - success: `false`
  - human_intervention: `false`
  - topology: `mixed`
  - events: `1350`
  - retry_density: `0.9997`

This is the only native failure anchor currently available.

## Bucket 1b: Proxy Failure Candidate

- `7de9a576-5306-4f0b-8950-53938c6b8dd9`
  - runtime: `anthropic`
  - task_type: `debug_test`
  - task_source: `proxy`
  - data_origin: `unknown`
  - success: `false`
  - human_intervention: `false`
  - topology: `dominant_chain`
  - events: `12`
  - retry_density: `0.8462`

This is the only additional failure example currently available outside the native lane. It should be treated as a proxy-mediated failure candidate, not as a native strict failure.

## Bucket 2: Near-Failure-Like Candidate

- `1a00157a-1359-4981-a11d-21f8164b2130`
  - runtime: `anthropic`
  - task_type: `migration`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `unknown`
  - topology: `dominant_chain`
  - events: `1499`
  - retry_density: `0.8183`

This is the strongest current near-failure-like candidate because it combines very high retry density with a long session length.

Additional near-failure-style candidates worth keeping in the same review bucket:

- `f4b12241-c80c-4fa3-9201-2d218db6030c`
- `0e4c8b35-f7d1-491d-b654-a2904677451c`

## Bucket 3: High-Retry Short Sessions

These sessions are useful for correction-trigger inspection, but they are weaker near-failure candidates than the long-session case above.

- `1645d1ea-b14d-4a49-bcb9-60c29ed4226c`
- `ses_192be68d4ffenQmPDOZBl4PLxS`
- `a6cdfbdf-45a6-4b5d-9998-ad2d16ac288b`
- `51f5dd18-1feb-4224-b6d7-5445bbdda5e2`

Observed traits:

- high retry density
- dominant_chain topology
- real_work source
- no confirmed human-intervention positive example

## Bucket 4: Longer High-Retry Non-Failure Candidates

These are useful leads, but they are still not failure examples.

- `f4b12241-c80c-4fa3-9201-2d218db6030c`
- `0e4c8b35-f7d1-491d-b654-a2904677451c`
- `8d79b673-13f5-4985-904f-98e7219de91a`
- `0ad05f47-9856-454f-94af-51224ebb8497`
- `019e6d76-ffe2-7b82-ad40-8a351378ab5b`
- `019e6c41-e043-7190-872f-60dae5e13eeb`
- `c9e68c5f-88ff-4e67-88d9-f16a4bdffe34`

## Triage Guidance

Prioritize review in this order:

1. failure anchor
2. near-failure-like long session
3. high-retry short sessions
4. longer high-retry non-failure candidates

## Next Action

Use this triage to decide which sessions deserve manual trace review before the next acquisition round.
