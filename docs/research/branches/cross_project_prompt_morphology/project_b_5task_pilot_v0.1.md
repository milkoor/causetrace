# Project B 5-task Pilot v0.1

Status: planning.

This pilot is the second concrete application of the cross-project prompt morphology study. It uses real `Project B` work items to compare prompt structure against runtime morphology and project-level execution quality.

The pilot is intentionally small:

- 5 real tasks
- 2 to 3 prompt variants per task where feasible
- 1 fixed runtime where possible
- clean repo reset between variants
- prompt order recorded for every run

The pilot is a workflow validation and measurement pass, not a strong-conclusion study.

## Pilot Purpose

The goal is to determine whether prompt structure changes:

- invalid retry behavior
- branchy or long-session behavior
- business-rule clarification behavior
- human intervention frequency
- task completion quality
- refactor safety

This repo is a good second pilot because it contains business workflow, data extraction, API work, SMS-related operational tasks, and reporting surfaces that can respond differently to prompt form.

## Fixed Controls

- Same task across prompt variants.
- Same repository baseline where possible.
- Same runtime where possible.
- Clean workspace reset between variants.
- No patch reuse from a prior variant.
- Prompt order must be recorded.
- Randomized A/B/C order is preferred when possible.

## Prompt Variants

### A. `minimal_prompt`

Use a short prompt that resembles a real minimal task handoff:

```text
请处理 Project B 当前的业务功能问题，尽量保证相关流程和测试通过。
```

### B. `expanded_constrained_prompt`

Use a stronger, AI-expanded prompt that adds operational constraints without assuming it is better:

```text
请在 Project B 项目中处理当前业务功能问题。

约束：
1. 不要改动无关业务流程。
2. 不要重构与本任务无关的核心模块。
3. 优先定位导致数据流、接口返回、权限判断或报表结果异常的最小原因。
4. 涉及 API、记录列表、订单列表、短信签名、报表或权限时，优先保证字段一致性和现有流程兼容。
5. 如果任务边界不清晰，应先澄清再动手，不要一次改太大范围。
6. 修改后必须运行相关测试或最小验证脚本。
7. 如果现有测试不足，可以补一个最小回归测试。
8. 输出时说明：
   - 修改了哪些文件；
   - 修复了什么问题；
   - 跑了哪些测试或验证；
   - 是否仍有业务流程、数据口径或权限风险。

目标：
- 保持现有业务兼容；
- 提高交付稳定性；
- 避免把局部修复扩成全局重构；
- 确保相关验证通过。
```

### C. `human_structured_prompt`

Use a human-written middle-detail prompt:

```text
帮我看一下 Project B 里这个业务功能问题，重点关注数据流、接口返回、权限判断、报表口径和短信/通知相关流程。

如果边界不清楚，先梳理现有链路和风险点，再做最小修改。不要大改架构，也不要把局部问题扩成全局重构。修完后跑相关测试或验证脚本，如果有必要可以补一个最小回归测试。最后告诉我改了什么、验证结果是什么、还有没有业务风险。
```

## Task Slots

### LS-PM-001: record extraction / list consistency

Purpose:

- Verify that record list extraction / display / pagination-related behavior stays consistent under prompt variants.

Candidate real task:

- record list extraction or display consistency issue

Project state:

- `project-specific extraction script B`
- `project guide` record API sections
- record list / complex API behavior already documented

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- cleaner record data handling
- fewer retries around list / pagination
- better API and field consistency

Morphology signals to watch:

- `retry_density`
- `branch_density`
- clarification / question loops
- field mapping corrections

### LS-PM-002: order / payment reporting

Purpose:

- Verify how prompt structure affects order detail, payment breakdown, or daily reporting work.

Candidate real task:

- order list, order detail, payment summary, or report generation issue

Project state:

- `project-specific extraction script C`
- reporting and dashboard docs
- order / payment API references in `project guide`

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- more stable reporting logic
- fewer misread fields or mismatched totals
- lower risk of over-broad edits

Morphology signals to watch:

- long-session behavior
- repeated data verification
- correction triggers from mismatched totals
- manual intervention around report correctness

### LS-PM-003: SMS signature / template workflow

Purpose:

- Verify whether prompt structure changes risk-taking when touching SMS signature/template or message-flow work.

Candidate real task:

- SMS signature, template, or send-flow behavior

Project state:

- SMS endpoints documented in `project API reference`
- `project guide` has explicit endpoint inventory and gaps

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- safer API work
- clearer handling of 404 / unavailable endpoints
- less overreach into unsupported flows

Morphology signals to watch:

- ambiguity resolution
- fallback exploration
- human intervention
- whether strong constraints reduce unnecessary endpoint chasing

### LS-PM-004: permissions / role-gated business logic

Purpose:

- Verify whether prompt structure affects tasks that depend on role, tenant, or permission gating.

Candidate real task:

- role / permission / tenant-related behavior

Project state:

- role and permission API references are already mapped
- multi-tenant data model exists in project documentation

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- fewer permission-related regressions
- better boundary awareness
- clearer handling of role-specific behavior

Morphology signals to watch:

- repeated verification loops
- correction after wrong assumptions
- cross-module branch exploration

### LS-PM-005: workflow / refactor / cleanup

Purpose:

- Verify whether prompt structure influences refactor safety and business-flow preservation.

Candidate real task:

- workflow adjustment
- refactor
- cleanup
- cross-file business logic repair

Project state:

- docs and scripts expose multiple real workflow surfaces

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- less accidental over-editing
- better task boundary control
- fewer regressions across adjacent modules

Morphology signals to watch:

- fan-out into unrelated files
- branch-collapse after verification
- long-session refactor behavior
- whether strong constraints keep changes local

## Execution Log

| task_id | prompt_variant | runtime | repository_commit | session_ref | outcome | topology_label | event_count | tool_call_count | retry_density | branch_density | AskUserQuestion_count | human_intervention | correction_trigger | final_patch_quality | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LS-PM-001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| LS-PM-002 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| LS-PM-003 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| LS-PM-004 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| LS-PM-005 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Review Checklist

- Did `expanded_constrained_prompt` reduce invalid retry?
- Did it reduce `AskUserQuestion` or `human_intervention`?
- Did it improve task completion quality?
- Did it over-constrain business logic exploration?
- Did it keep refactors local and safe?
- Did `human_structured_prompt` outperform both extremes on this task?
- Should automatic prompt expansion be recommended by default for this task type?

## Reporting Rule

This pilot produces a project-level decision page for `Project B` and a morphology comparison page for `causetrace`.

Do not merge its results into native lane conclusions without explicit review.
