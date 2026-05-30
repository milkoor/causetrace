# Phase 3C Origin Labeling Queue (v0.2.5)

This document is a human review queue. It does not write back to metadata and it does not backfill data_origin automatically.

## Queue Summary

- unlabeled sessions: 930
- strict-lane candidates: 115
- task_source=real_work: 54
- task_source=demo: 62
- task_source=proxy: 2
- task_source=unknown: 812

## Review Rules

- Treat `lane_hint` as advisory only.
- Do not copy this queue into `data_origin` without human review.
- Prefer labeling strict research-grade sessions first.
- Keep native, controlled benchmark, and external trajectory lanes separate.

## Priority Ordering

1. strict research-grade + real_work
2. strict research-grade + demo/proxy
3. failure or intervention candidates
4. long / multi-root / branchy candidates
5. remaining unlabeled sessions

## Candidate Sessions

| rank | session_id | runtime | task_type | task_source | success | topology | events | strict | lane_hint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `1a00157a-1359-4981-a11d-21f8164b2130` | anthropic | migration | real_work | true | dominant_chain | 1499 | true | native candidate |
| 2 | `019e6c41-e043-7190-872f-60dae5e13eeb` | codex | review | real_work | true | dominant_chain | 1473 | true | native candidate |
| 3 | `270e9651-6b70-499e-84c8-9beb36d6fa75` | anthropic | debug_test | real_work | true | mixed | 1420 | true | native candidate |
| 4 | `aider_902f54e8` | aider | review | real_work | false | mixed | 1350 | true | native candidate |
| 5 | `0ad05f47-9856-454f-94af-51224ebb8497` | anthropic | feature_add | real_work | true | dominant_chain | 794 | true | native candidate |
| 6 | `4ca90ca7-8270-4a85-9334-61613eee8457` | claude | review | real_work | true | dominant_chain | 533 | true | native candidate |
| 7 | `c9e68c5f-88ff-4e67-88d9-f16a4bdffe34` | anthropic | exploration | real_work | true | dominant_chain | 532 | true | native candidate |
| 8 | `f4b12241-c80c-4fa3-9201-2d218db6030c` | anthropic | feature_add | real_work | true | dominant_chain | 400 | true | native candidate |
| 9 | `0e4c8b35-f7d1-491d-b654-a2904677451c` | anthropic | bug_fix | real_work | true | dominant_chain | 389 | true | native candidate |
| 10 | `8d79b673-13f5-4985-904f-98e7219de91a` | anthropic | review | real_work | true | dominant_chain | 310 | true | native candidate |
| 11 | `793bf8bf-f829-4b7e-b4b8-17f3b46db2c2` | anthropic | review | real_work | true | dominant_chain | 263 | true | native candidate |
| 12 | `644ba24e-d487-43da-9cbd-d282bf4e9733` | anthropic | exploration | real_work | true | dominant_chain | 219 | true | native candidate |
| 13 | `47ba453a-d03c-48bf-807f-5bc5b3891eec` | anthropic | exploration | real_work | true | dominant_chain | 188 | true | native candidate |
| 14 | `fdb0c54b-ee2f-472f-9044-c8b36e2d5880` | anthropic | exploration | real_work | true | dominant_chain | 114 | true | native candidate |
| 15 | `3e18b52d-d148-4f48-b5ef-b05b7db46fec` | anthropic | bug_fix | real_work | true | dominant_chain | 104 | true | native candidate |
| 16 | `e7fc44f1-0bfa-45d5-96b5-2f71dd015cd7` | anthropic | exploration | real_work | true | dominant_chain | 90 | true | native candidate |
| 17 | `d1261375-349e-44a6-9a12-42a1622d112d` | anthropic | bug_fix | real_work | true | dominant_chain | 85 | true | native candidate |
| 18 | `1a9a5969-0209-457b-bc6a-a7ee78a92659` | anthropic | feature_add | real_work | true | dominant_chain | 69 | true | native candidate |
| 19 | `a6cdfbdf-45a6-4b5d-9998-ad2d16ac288b` | anthropic | exploration | real_work | true | dominant_chain | 60 | true | native candidate |
| 20 | `0a2ab964-b056-425b-b7d3-4a04b6e5a4af` | anthropic | feature_add | real_work | true | dominant_chain | 56 | true | native candidate |
| 21 | `08ed9b81-1947-46ab-93d6-5d9eb265205c` | anthropic | feature_add | real_work | true | dominant_chain | 51 | true | native candidate |
| 22 | `66808ae5-0da5-4790-b6ac-0158b9f26fae` | anthropic | exploration | real_work | true | dominant_chain | 43 | true | native candidate |
| 23 | `3de5c24c-10da-44cf-b9c0-ed9bd41aee58` | anthropic | review | real_work | true | dominant_chain | 42 | true | native candidate |
| 24 | `0edbbdf0-5114-4144-98b0-ec865c415019` | anthropic | project_init | real_work | true | dominant_chain | 39 | true | native candidate |
| 25 | `ses_193525266ffeT9lwg7MQYe5TIm` | anthropic | review | real_work | true | dominant_chain | 38 | true | native candidate |
| 26 | `019e6d76-ffe2-7b82-ad40-8a351378ab5b` | codex | review | real_work | true | dominant_chain | 36 | true | native candidate |
| 27 | `1aa8aadf-59c1-4998-a2d8-79a838b3600f` | anthropic | bug_fix | real_work | true | dominant_chain | 35 | true | native candidate |
| 28 | `a71d550c-7891-478e-8502-2f8f63a6cea7` | anthropic | bug_fix | real_work | true | dominant_chain | 34 | true | native candidate |
| 29 | `076ac32b-a5a7-4452-9dfd-32c6afc1b07b` | anthropic | project_init | real_work | true | multi_root_exploration | 32 | true | native candidate |
| 30 | `774af7b9-79d4-45e1-8ca0-79febee625a0` | anthropic | exploration | real_work | true | dominant_chain | 32 | true | native candidate |
| 31 | `1645d1ea-b14d-4a49-bcb9-60c29ed4226c` | anthropic | exploration | real_work | true | dominant_chain | 31 | true | native candidate |
| 32 | `ses_192be68d4ffenQmPDOZBl4PLxS` | anthropic | exploration | real_work | true | dominant_chain | 29 | true | native candidate |
| 33 | `1ad59fe8-a890-468c-a148-4b7a30d45936` | anthropic | doc_gen | real_work | true | dominant_chain | 18 | true | native candidate |
| 34 | `8d686330-8939-4ef7-a15f-deed94f8a076` | anthropic | project_init | real_work | true | dominant_chain | 18 | true | native candidate |
| 35 | `51f5dd18-1feb-4224-b6d7-5445bbdda5e2` | anthropic | feature_add | real_work | true | dominant_chain | 17 | true | native candidate |
| 36 | `446f8a08-56e1-4f29-982d-bfee7f581a2b` | anthropic | feature_add | real_work | true | dominant_chain | 16 | true | native candidate |
| 37 | `8ae5f32d-02b9-423d-94c5-257a98616580` | anthropic | feature_add | real_work | true | dominant_chain | 16 | true | native candidate |
| 38 | `3c1045b2-c8f0-44a1-8b11-f83ccb84d896` | anthropic | bug_fix | real_work | true | dominant_chain | 15 | true | native candidate |
| 39 | `afaa0b3e-058f-49e8-bf2c-2ced9ce5f023` | anthropic | review | real_work | true | mixed | 14 | true | native candidate |
| 40 | `ses_193518f0effeWsGotv4AUaSIVr` | anthropic | exploration | real_work | true | dominant_chain | 12 | true | native candidate |
| 41 | `016cc5d2-a64d-4273-ac2f-97fe56b27585` | anthropic | feature_add | real_work | true | dominant_chain | 11 | true | native candidate |
| 42 | `1d4849eb-d9fe-472c-8803-8a87b133f210` | anthropic | exploration | real_work | true | dominant_chain | 11 | true | native candidate |
| 43 | `2bdc7399-6334-44ed-a247-186f02483f90` | anthropic | project_init | real_work | true | dominant_chain | 10 | true | native candidate |
| 44 | `17156e75-6f1d-4c97-b048-ec730a67309c` | anthropic | exploration | real_work | true | dominant_chain | 7 | true | native candidate |
| 45 | `3bb2c4e9-c230-4e52-9246-f8951bd0a719` | anthropic | feature_add | real_work | true | dominant_chain | 7 | true | native candidate |
| 46 | `712ced62-f25f-42ff-880d-61641688ecf8` | anthropic | project_init | real_work | true | dominant_chain | 7 | true | native candidate |
| 47 | `a72e0d82-f68c-4ab6-b83e-7e98b3a5603b` | anthropic | exploration | real_work | true | dominant_chain | 7 | true | native candidate |
| 48 | `ba7614de-bd11-42d6-91bf-b858871566cf` | anthropic | exploration | real_work | true | dominant_chain | 7 | true | native candidate |
| 49 | `42976d25-7ab0-4852-ba64-4db405d4a04e` | anthropic | exploration | real_work | true | dominant_chain | 6 | true | native candidate |
| 50 | `0a33cd09-73f2-472c-8c3d-b76fcee6c01f` | anthropic | exploration | real_work | true | dominant_chain | 4 | true | native candidate |
| 51 | `afc0f5f0-50f7-461a-bf4c-bb646f3e00b9` | anthropic | debug_test | real_work | true | dominant_chain | 4 | true | native candidate |
| 52 | `c96660e5-5c4b-4050-afc8-e26aa8ef3c57` | anthropic | exploration | real_work | true | mixed | 2 | true | native candidate |
| 53 | `4d201fc7-4911-41d9-a3cf-53198be99ff7` | anthropic | exploration | real_work | true | mixed | 1 | true | native candidate |
| 54 | `7de9a576-5306-4f0b-8950-53938c6b8dd9` | anthropic | debug_test | proxy | false | dominant_chain | 12 | true | proxy-mediated candidate |
| 55 | `ses_01548638` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 56 | `ses_01685153` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 57 | `ses_05278e67` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 58 | `ses_05f6e48b` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 59 | `ses_080489dc` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 60 | `ses_097e57fd` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 61 | `ses_0cd215a4` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 62 | `ses_10d49a6d` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 63 | `ses_1240cca3` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 64 | `ses_15c89a17` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 65 | `ses_18356061` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 66 | `ses_18e1bb25` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 67 | `ses_18eab36d` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 68 | `ses_1f0b4f3b` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 69 | `ses_203fb93d` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 70 | `ses_233cec08` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 71 | `ses_25789494` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 72 | `ses_2ab6bcc8` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 73 | `ses_2e16f9c3` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 74 | `ses_30704d21` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 75 | `ses_3cf43c11` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 76 | `ses_3d3d2321` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 77 | `ses_3ea1243d` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 78 | `ses_3f8d6699` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 79 | `ses_40f7f98e` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 80 | `ses_424e064b` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 81 | `ses_42677436` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 82 | `ses_43c13dae` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 83 | `ses_4534e4c3` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 84 | `ses_4a47fb4f` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 85 | `ses_51b27427` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 86 | `ses_52b4fe4c` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 87 | `ses_53ab410f` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 88 | `ses_5a1dc72d` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 89 | `ses_62b43261` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 90 | `ses_66673e7a` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 91 | `ses_67280fe0` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 92 | `ses_677bf6e8` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 93 | `ses_68374cb6` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 94 | `ses_69a7ce0c` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 95 | `ses_6bffb414` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 96 | `ses_6dec7029` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 97 | `ses_6e04a58c` | demo | debug_test | demo | true | dominant_chain | 6 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 98 | `demo_faninbc_01` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 99 | `demo_faninbc_02` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 100 | `demo_faninbc_03` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 101 | `demo_faninbc_04` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 102 | `demo_faninbc_05` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 103 | `demo_faninbc_06` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 104 | `demo_faninbc_07` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 105 | `demo_faninbc_08` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 106 | `demo_faninbc_09` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 107 | `demo_faninbc_10` | demo | debug_test | demo | true | dominant_chain | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 108 | `demo_multiroot_01` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 109 | `demo_multiroot_02` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 110 | `demo_multiroot_03` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 111 | `demo_multiroot_04` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 112 | `demo_multiroot_05` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 113 | `demo_multiroot_06` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 114 | `demo_multiroot_07` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 115 | `demo_multiroot_08` | demo | debug_test | demo | true | multi_root_exploration | 5 | true | demo-lane candidate (keep separate from controlled_benchmark) |
| 116 | `ses_1dbbca86cffepmHBhw7I0hA7VI` | ​sisyphus - ultraworker | unknown | real_work | unknown | dominant_chain | 91 | false | native candidate |
| 117 | `codex_latest` | codex | unknown | proxy | unknown | dominant_chain | 672 | false | proxy-mediated candidate |
| 118 | `ses_ff36867c` | unknown | exploration | demo | unknown | dominant_chain | 4 | false | demo-lane candidate (keep separate from controlled_benchmark) |
| 119 | `aider_2161035b` | aider | unknown | unknown | unknown | mixed | 1350 | false | manual classification needed |
| 120 | `ed735994-b052-475e-8d28-d8f54c1257d1` | anthropic | unknown | unknown | unknown | dominant_chain | 1278 | false | manual classification needed |

## Suggested Manual Labels for the Top Tier


## Manual Annotation Notes

- The queue is advisory only.
- Treat the top 20 rows as the first manual review batch.
- Start with strict research-grade sessions that have `task_source=real_work`.
- Treat demo and proxy rows as separate review batches.
- Do not assume `lane_hint` is a final label.

- `task_source=real_work` sessions should be reviewed first for `data_origin=native`.
- `task_source=demo` sessions should remain separate from controlled benchmark unless explicitly reclassified.
- `task_source=proxy` sessions need manual review before any strict conclusion.
- Sessions with unknown task source should stay `unknown` until a human confirms provenance.
