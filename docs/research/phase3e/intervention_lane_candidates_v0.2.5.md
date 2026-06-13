# Phase 3E-2 Intervention Lane Candidates v0.2.5

This document records candidate review decisions for Phase 3E-2 intervention lane annotation. It is a living log, not a validation result.

## Candidate Summary

| Lane | Strong | Moderate | Weak | Total Candidates |
|------|--------|----------|------|-----------------|
| `superpowers_workflow_intervention` | 1 | 2 | 15 | 18 |
| `routed_prompt_intervention` | 0 | 0 | 0 | 0 |
| `controlled_prompt_morphology` | 0 | 0 | 3 (existing pilot) | 3 |

## Corpus Scan Results

### routed_prompt_intervention — 0 genuine candidates

Full corpus scan (1,351 sessions, 128,552 events) found:

- 1 mention of `prompt-routing-skill` in a file path listing (`find /mnt/d/project -name .git` output in Codex CLI session `019e8afe`) — false positive
- 1 session (`7e8574ec`) containing `routed_prompt_intervention` text — this is the causetrace research documentation session itself, not an intervention session
- 0 sessions with `Skill` tool invoking `prompt-routing`
- 0 sessions with explicit prompt posture selection records

**Decision**: `routed_prompt_intervention` lane remains at 0. No sessions meet annotation criteria. The `prompt-routing-skill` is deployed but its usage has not yet been captured in the causetrace corpus.

### superpowers_workflow_intervention — 18 candidates with Skill tool

#### Strong Evidence (Skill + PlanMode + Workflow)

| # | Session ID | Events | Skill | PlanMode | Workflow | Current Label | Annotation Decision |
|---|-----------|--------|-------|----------|----------|---------------|-------------------|
| 1 | `f4e2f505-4e9c-4695-a313-b0535d5a6852` | 19,297 | ×14 | yes | yes | unlabeled | **Annotate** `superpowers_workflow_intervention` |

**Evidence for #1**: Uses `Skill`×14, `EnterPlanMode`/`ExitPlanMode`, `Workflow` tool, `TaskCreate`/`TaskUpdate`/`TaskStop`, `mcp__gitnexus__impact`, `mcp__gitnexus__detect_changes`. Complete superpowers workflow pattern. Runtime: claude-code.

#### Moderate Evidence (Skill + PlanMode)

| # | Session ID | Events | Skill | PlanMode | Workflow | Current Label | Annotation Decision |
|---|-----------|--------|-------|----------|----------|---------------|-------------------|
| 2 | `6e86a3e4-2599-4758-9edb-bfa6d687064d` | 11,383 | ×3 | yes | no | unlabeled | **Annotate** `superpowers_workflow_intervention` |
| 3 | `1ecb1c32-6545-4a18-850e-3e0ef172383b` | 10,353 | ×10 | yes | no | unlabeled | **Annotate** `superpowers_workflow_intervention` |

**Evidence for #2**: Uses `Skill`×3, `EnterPlanMode`/`ExitPlanMode`, `TaskCreate`/`TaskUpdate`/`TaskStop`, `AskUserQuestion`, mcp tools. Agent: claude-code + opencode (mixed). "superpowers" mention in context of installing superpowers.

**Evidence for #3**: Uses `Skill`×10, `EnterPlanMode`/`ExitPlanMode`, `TaskCreate`/`TaskUpdate`, `mcp__gitnexus__impact`, `mcp__gitnexus__detect_changes`. Agent: claude-code. "superpowers" mention in CLAUDE.md skill instruction context.

#### Weak Evidence (Skill only — not annotated)

These sessions use the `Skill` tool but lack PlanMode/Workflow confirmation. Recorded for future reference, not annotated:

| # | Session ID | Events | Skill | Current Label | Task Type | Notes |
|---|-----------|--------|-------|---------------|-----------|-------|
| 4 | `52dbf652-7721-493b-9c48-411aa169247d` | 10,627 | ×2 | unlabeled | — | Large session, no PlanMode |
| 5 | `360e1036-7589-4c0b-87c2-111aa2314102` | 5,128 | ×9 | unlabeled | — | High Skill count, no PlanMode |
| 6 | `1a00157a-1359-4981-a11d-21f8164b2130` | 4,726 | ×5 | native | migration | human_intervention=true, large |
| 7 | `9fe3f018-cda9-41ad-8203-4ae1d61b6d17` | 2,065 | ×6 | unlabeled | — | Installs superpowers plugin |
| 8 | `e9680e4d-e56b-44f0-82c0-2fbe6c46b0b7` | 1,368 | ×2 | unlabeled | — | — |
| 9 | `ce71e410-b2d2-48e8-bd72-30f0a76f4221` | 737 | ×2 | unlabeled | — | — |
| 10 | `4ca90ca7-8270-4a85-9334-61613eee8457` | 533 | ×2 | native | review | — |
| 11 | `076ac32b-a5a7-4452-9dfd-32c6afc1b07b` | 356 | ×1 | native | project_init | Single Skill invocation |
| 12 | `e1e676f9-602c-44ac-9f4d-00cdbe0a973f` | 279 | ×1 | native | project_init | Single Skill invocation |
| 13 | `d1261375-349e-44a6-9a12-42a1622d112d` | 262 | ×3 | native | bug_fix | — |
| 14 | `3de5c24c-10da-44cf-b9c0-ed9bd41aee58` | 163 | ×2 | native | review | — |
| 15 | `8ff5d09a-8638-49be-bb43-334162048731` | 122 | ×2 | unlabeled | — | — |
| 16 | `ses_1dbbca86cffepmHBhw7I0hA7VI` | 91 | ×1 | native | unknown | Sisyphus agent |
| 17 | `1d4849eb-d9fe-472c-8803-8a87b133f210` | 41 | ×2 | native | exploration | Small session |
| 18 | `a72e0d82-f68c-4ab6-b83e-7e98b3a5603b` | 7 | ×1 | native | exploration | Trivial session |

### controlled_prompt_morphology — 3 existing pilot sessions

| # | Session ID | Events | Agent | Runtime | Task Type | Annotation Decision |
|---|-----------|--------|-------|---------|-----------|-------------------|
| C1 | `c25d26b1-0ad9-4688-875e-b9b1d36fd5e8` | 3 | claude-code | — | — | Preserve `controlled_prompt_morphology` |
| C2 | `f5681f25-b5f0-4c5d-9d6f-34ba79884628` | 61 | claude-code | — | — | Preserve `controlled_prompt_morphology` |
| C3 | `fb0ec92b-a473-4248-8f29-26e8c0377be2` | 71 | claude-code | — | — | Preserve `controlled_prompt_morphology` |

These 3 sessions are already labeled with `data_origin=controlled_benchmark`. No additional controlled_prompt_morphology candidates found in corpus scan.

No additional `controlled_prompt_morphology` candidates identified. The `a/b prompt` string matches in 17 other sessions were all code-level A/B testing references, not controlled prompt experiment records.

## External Trajectory Candidates (for future reference)

| Session ID | Events | Agent | Notes |
|-----------|--------|-------|-------|
| `7de9a576-5306-4f0b-8950-53938c6b8dd9` | 38 | claude-code | `task_source=proxy`, failure, debug_test |
| `codex_latest` | 672 | codex | `task_source=proxy`, codex runtime |

These sessions have `task_source=proxy` and may qualify as `external_trajectory` lane in the future. Not annotated as intervention lanes at this stage.

## Annotation Execution Plan

### Batch 1: Annotate Strong + Moderate superpowers candidates

Annotate sessions #1, #2, #3 as `superpowers_workflow_intervention`:

- Set `task_source=superpowers_workflow_intervention` in metadata sidecar
- Record provenance: `{"annotated_by": "Phase 3E-2", "date": "2026-06-13", "evidence": "Skill+PlanMode[+Workflow] tool usage"}`
- Session IDs: `f4e2f505`, `6e86a3e4`, `1ecb1c32`

### Batch 2: Preserve controlled_prompt_morphology

- Verify C1, C2, C3 retain `data_origin=controlled_benchmark`
- No additional controlled sessions to add

### Batch 3: routed_prompt_intervention — no action

- 0 candidates. Lane remains at 0.
- This is an honest result, not a failure.

## Post-Annotation Lane Counts (Projected)

| Lane | Before | After | Delta |
|------|--------|-------|-------|
| `direct_prompt_native` | 101 | 101 | 0 (no reclassification from native) |
| `superpowers_workflow_intervention` | 0 | 3 | +3 |
| `routed_prompt_intervention` | 0 | 0 | 0 |
| `controlled_prompt_morphology` | 3 | 3 | 0 |

Note: No sessions are reclassified from `direct_prompt_native` in this pass. The 9 native-labeled sessions with Skill tool usage (#6, #10–#14, #16–#18) remain in native because their Skill usage lacks PlanMode confirmation (weak evidence). Reclassification of these sessions requires additional evidence review.

## Operating Rules

- Annotation decisions are reversible with additional evidence.
- Do not annotate without explicit evidence.
- Document every annotation decision.
- Do not merge annotated intervention sessions into native baseline.
- Weak-evidence sessions remain in their current lane.
