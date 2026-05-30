# Phase 3C Review Batches (v0.2.5)

This is a human review aid. It does not backfill metadata and it does not assert final labels.

## Batch 1: Native Candidates

Review order: strict research-grade sessions with `task_source=real_work`.

| rank | session_id | runtime | task_type | task_source | success | topology | events | lane_hint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `1a00157a-1359-4981-a11d-21f8164b2130` | anthropic | migration | real_work | true | dominant_chain | 1499 | native candidate |
| 2 | `019e6c41-e043-7190-872f-60dae5e13eeb` | codex | review | real_work | true | dominant_chain | 1473 | native candidate |
| 3 | `270e9651-6b70-499e-84c8-9beb36d6fa75` | anthropic | debug_test | real_work | true | mixed | 1420 | native candidate |
| 4 | `aider_902f54e8` | aider | review | real_work | false | mixed | 1350 | native candidate |
| 5 | `0ad05f47-9856-454f-94af-51224ebb8497` | anthropic | feature_add | real_work | true | dominant_chain | 794 | native candidate |
| 6 | `4ca90ca7-8270-4a85-9334-61613eee8457` | claude | review | real_work | true | dominant_chain | 533 | native candidate |
| 7 | `c9e68c5f-88ff-4e67-88d9-f16a4bdffe34` | anthropic | exploration | real_work | true | dominant_chain | 532 | native candidate |
| 8 | `f4b12241-c80c-4fa3-9201-2d218db6030c` | anthropic | feature_add | real_work | true | dominant_chain | 400 | native candidate |
| 9 | `0e4c8b35-f7d1-491d-b654-a2904677451c` | anthropic | bug_fix | real_work | true | dominant_chain | 389 | native candidate |
| 10 | `8d79b673-13f5-4985-904f-98e7219de91a` | anthropic | review | real_work | true | dominant_chain | 310 | native candidate |
| 11 | `793bf8bf-f829-4b7e-b4b8-17f3b46db2c2` | anthropic | review | real_work | true | dominant_chain | 263 | native candidate |
| 12 | `644ba24e-d487-43da-9cbd-d282bf4e9733` | anthropic | exploration | real_work | true | dominant_chain | 219 | native candidate |
| 13 | `47ba453a-d03c-48bf-807f-5bc5b3891eec` | anthropic | exploration | real_work | true | dominant_chain | 188 | native candidate |
| 14 | `fdb0c54b-ee2f-472f-9044-c8b36e2d5880` | anthropic | exploration | real_work | true | dominant_chain | 114 | native candidate |
| 15 | `3e18b52d-d148-4f48-b5ef-b05b7db46fec` | anthropic | bug_fix | real_work | true | dominant_chain | 104 | native candidate |
| 16 | `e7fc44f1-0bfa-45d5-96b5-2f71dd015cd7` | anthropic | exploration | real_work | true | dominant_chain | 90 | native candidate |
| 17 | `d1261375-349e-44a6-9a12-42a1622d112d` | anthropic | bug_fix | real_work | true | dominant_chain | 85 | native candidate |
| 18 | `1a9a5969-0209-457b-bc6a-a7ee78a92659` | anthropic | feature_add | real_work | true | dominant_chain | 69 | native candidate |
| 19 | `a6cdfbdf-45a6-4b5d-9998-ad2d16ac288b` | anthropic | exploration | real_work | true | dominant_chain | 60 | native candidate |
| 20 | `0a2ab964-b056-425b-b7d3-4a04b6e5a4af` | anthropic | feature_add | real_work | true | dominant_chain | 56 | native candidate |

## Batch 2: Demo / Proxy Candidates

Review order: strict research-grade sessions with `task_source=demo` or `task_source=proxy`.

| rank | session_id | runtime | task_type | task_source | success | topology | events | lane_hint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `7de9a576-5306-4f0b-8950-53938c6b8dd9` | anthropic | debug_test | proxy | false | dominant_chain | 12 | proxy-mediated candidate |
| 2 | `ses_01548638` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 3 | `ses_01685153` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 4 | `ses_05278e67` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 5 | `ses_05f6e48b` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 6 | `ses_080489dc` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 7 | `ses_097e57fd` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 8 | `ses_0cd215a4` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 9 | `ses_10d49a6d` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 10 | `ses_1240cca3` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 11 | `ses_15c89a17` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 12 | `ses_18356061` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 13 | `ses_18e1bb25` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 14 | `ses_18eab36d` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |
| 15 | `ses_1f0b4f3b` | demo | debug_test | demo | true | dominant_chain | 6 | demo-lane candidate (keep separate from controlled_benchmark) |

## Batch 3: Manual Classification Needed

Review order: strict-lane rows that do not fit the first two batches.

| rank | session_id | runtime | task_type | task_source | success | topology | events | lane_hint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `ses_1dbbca86cffepmHBhw7I0hA7VI` | ​sisyphus - ultraworker | unknown | real_work | unknown | dominant_chain | 91 | native candidate |
| 2 | `codex_latest` | codex | unknown | proxy | unknown | dominant_chain | 672 | proxy-mediated candidate |
| 3 | `ses_ff36867c` | unknown | exploration | demo | unknown | dominant_chain | 4 | demo-lane candidate (keep separate from controlled_benchmark) |
| 4 | `aider_2161035b` | aider | unknown | unknown | unknown | mixed | 1350 | manual classification needed |
| 5 | `ed735994-b052-475e-8d28-d8f54c1257d1` | anthropic | unknown | unknown | unknown | dominant_chain | 1278 | manual classification needed |
