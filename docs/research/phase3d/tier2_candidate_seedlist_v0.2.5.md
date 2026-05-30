# Phase 3D Tier 2 Candidate Seed List v0.2.5

This document lists current corpus sessions that are useful as acquisition leads for Tier 2, especially near-failure and correction-trigger investigation.

These are not automatically classified as failures. They are candidate seeds for follow-up review and future acquisition planning.

## Native Failure Anchor

- `aider_902f54e8`
  - runtime: `aider`
  - task_type: `review`
  - task_source: `real_work`
  - success: `false`
  - human_intervention: `false`
  - topology: `mixed`
  - events: `1350`
  - retry_density: `0.9997`

## High-Retry Native Candidate Seeds

These are the strongest current native leads for near-failure / correction-trigger study.

| session_id | runtime | task_type | success | human_intervention | topology | events | retry_density |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1645d1ea-b14d-4a49-bcb9-60c29ed4226c` | anthropic | exploration | true | unknown | dominant_chain | 31 | 0.8918 |
| `ses_192be68d4ffenQmPDOZBl4PLxS` | anthropic | exploration | true | false | dominant_chain | 29 | 0.8625 |
| `a6cdfbdf-45a6-4b5d-9998-ad2d16ac288b` | anthropic | exploration | true | unknown | dominant_chain | 60 | 0.8520 |
| `51f5dd18-1feb-4224-b6d7-5445bbdda5e2` | anthropic | feature_add | true | unknown | dominant_chain | 17 | 0.8269 |
| `1a00157a-1359-4981-a11d-21f8164b2130` | anthropic | migration | true | unknown | dominant_chain | 1499 | 0.8183 |
| `1aa8aadf-59c1-4998-a2d8-79a838b3600f` | anthropic | bug_fix | true | false | dominant_chain | 35 | 0.7922 |
| `8d686330-8939-4ef7-a15f-deed94f8a076` | anthropic | project_init | true | false | dominant_chain | 18 | 0.7633 |
| `f4b12241-c80c-4fa3-9201-2d218db6030c` | anthropic | feature_add | true | unknown | dominant_chain | 400 | 0.7623 |
| `0e4c8b35-f7d1-491d-b654-a2904677451c` | anthropic | bug_fix | true | false | dominant_chain | 389 | 0.7581 |
| `8d79b673-13f5-4985-904f-98e7219de91a` | anthropic | review | true | unknown | dominant_chain | 310 | 0.7497 |
| `0ad05f47-9856-454f-94af-51224ebb8497` | anthropic | feature_add | true | false | dominant_chain | 794 | 0.7470 |
| `019e6d76-ffe2-7b82-ad40-8a351378ab5b` | codex | review | true | false | dominant_chain | 36 | 0.7311 |
| `1ad59fe8-a890-468c-a148-4b7a30d45936` | anthropic | doc_gen | true | false | dominant_chain | 18 | 0.7249 |
| `019e6c41-e043-7190-872f-60dae5e13eeb` | codex | review | true | false | dominant_chain | 1473 | 0.7228 |
| `c9e68c5f-88ff-4e67-88d9-f16a4bdffe34` | anthropic | exploration | true | unknown | dominant_chain | 532 | 0.7086 |
| `0a2ab964-b056-425b-b7d3-4a04b6e5a4af` | anthropic | feature_add | true | unknown | dominant_chain | 56 | 0.7042 |
| `fdb0c54b-ee2f-472f-9044-c8b36e2d5880` | anthropic | exploration | true | unknown | dominant_chain | 114 | 0.7008 |
| `3e18b52d-d148-4f48-b5ef-b05b7db46fec` | anthropic | bug_fix | true | unknown | dominant_chain | 104 | 0.6942 |
| `2bdc7399-6334-44ed-a247-186f02483f90` | anthropic | project_init | true | false | dominant_chain | 10 | 0.6795 |
| `47ba453a-d03c-48bf-807f-5bc5b3891eec` | anthropic | exploration | true | unknown | dominant_chain | 188 | 0.6772 |

## Strong Near-Failure Native Candidates

These sessions are still success cases, but they are the strongest native leads for near-failure and correction-trigger review.

| session_id | runtime | task_type | success | human_intervention | topology | events | retry_density | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1a00157a-1359-4981-a11d-21f8164b2130` | anthropic | migration | true | true | dominant_chain | 1499 | 0.8183 | long session, explicit intervention |
| `f4b12241-c80c-4fa3-9201-2d218db6030c` | anthropic | feature_add | true | true | dominant_chain | 400 | 0.7623 | explicit intervention, sustained retry |
| `0e4c8b35-f7d1-491d-b654-a2904677451c` | anthropic | bug_fix | true | false | dominant_chain | 389 | 0.7581 | sustained retry without intervention |

## Notes

- These sessions are not failures by metadata label.
- They are the best current native candidates for near-failure review because they exhibit high retry density and/or sustained repetition.
- The single native failure anchor is already known; the acquisition task is to find additional failure and intervention examples that are structurally comparable.
- Mixed or non-dominant topology is not required for Tier 2 acquisition, but it is useful when it appears.

## Recommended Follow-Up

- Inspect whether any of these candidate seeds contain explicit correction triggers in the raw trace.
- Prioritize follow-up capture of similar task types in runtimes that are currently underrepresented in the native lane.
- Re-run Tier 2 readiness after acquisition.
