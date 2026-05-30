# Project A 5-task Pilot v0.1

Status: planning.

This pilot is the first concrete application of the cross-project prompt morphology study. It uses real `Project A` work items to compare prompt structure against runtime morphology and project-level execution quality.

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
- `need_review` gating behavior
- false-positive control
- calibration and template-matching safety
- overall task completion quality
- human intervention frequency

This repo is a good first pilot because it already contains explicit safety-sensitive regression areas such as:

- `false_positive_tables`
- `need_review` safety gates
- OCR fallback behavior
- `grid_template` security audit paths
- calibrator auto-match safety

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
请检查并修复 Project A 当前的签名识别/模板匹配问题，确保相关测试通过。
```

### B. `expanded_constrained_prompt`

Use a stronger, AI-expanded prompt that adds operational constraints without assuming it is better:

```text
请在 Project A 项目中修复当前签名识别/模板匹配相关问题。

约束：
1. 不要改变项目主体流程和既有输入输出格式。
2. 不要引入新的大依赖。
3. 优先定位导致误签、误匹配或 need_review 判断异常的最小原因。
4. 如果 OCR 信息不足、结构置信度不够，或页面内容更像正文表格，应优先走 need_review，而不是强行自动签名。
5. 对于正文材料表、设备表、目录表、底边长表等 false-positive 场景，要优先保证不误判为 title block。
6. 如果 OCR unavailable，图像型图签必须保守退化，不要 silently degrade 成自动签名成功。
7. 修改范围尽量小，避免重写检测管线。
8. 修改后必须运行相关单元测试或集成测试；如现有测试不足，可补一个最小回归测试。
9. 输出时说明：
   - 修改了哪些文件；
   - 修复了什么问题；
   - 跑了哪些测试；
   - 是否仍有 need_review、OCR fallback 或 template-matching 风险。

目标：
- 保持现有功能兼容；
- 降低误签和 false-positive 风险；
- 确保相关测试通过；
- 避免把不确定样本误判为可自动签名。
```

### C. `human_structured_prompt`

Use a human-written middle-detail prompt:

```text
帮我看一下 Project A 里签名识别、模板匹配和 need_review 安全门这块的问题。

重点关注 false_positive_tables、OCR unavailable、grid_template 审计和 calibrator 自动匹配。
如果页面看起来更像正文材料表、设备表、目录表或底边大表格，应该优先进入 need_review，而不是继续自动签名。

请先梳理当前判断链路，再做最小修改。不要大改架构，也不要改输入输出格式。修完后跑相关测试，如果需要可以补一个小测试。最后告诉我改了什么、测试结果是什么、还有没有风险。
```

## Task Slots

### AS-PM-001: `false_positive_tables`

Purpose:

- Verify that body-only material/equipment tables do not become title blocks or automatic signatures.

Candidate real task:

- false-positive control for body tables and bottom-edge equipment tables

Project state:

- baseline repo state with `test_false_positive_tables` and `test_real_body_tables_false_positive`

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- stronger false-positive protection
- safer `need_review` behavior
- more robust table-vs-title-block boundary

Morphology signals to watch:

- `retry_density`
- `branch_density`
- `need_review` vs success
- correction triggers from detector output

### AS-PM-002: `need_review` safety gate

Purpose:

- Verify that image-based drawings with insufficient OCR keywords go to `need_review`, and the pipeline / calibrator do not auto-sign.

Candidate real task:

- `need_review` safety gate for detector, pipeline, and calibrator

Project state:

- image-based title-block regression surfaces
- `review_bbox` path available
- pipeline must short-circuit on `need_review`

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- fewer unsafe auto-matches
- clearer manual-review behavior
- better calibration safety

Morphology signals to watch:

- `AskUserQuestion`
- `human_intervention`
- `need_review` persistence
- template auto-load avoidance

### AS-PM-003: OCR unavailable / fallback behavior

Purpose:

- Verify that OCR unavailable does not silently degrade into unsafe automatic signing.

Candidate real task:

- OCR-unavailable safety gate for image-based drawings

Project state:

- OCR-dependent detection path available
- text-based drawings must still work without OCR

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- safer fallback behavior
- clearer error handling
- lower risk of false success when OCR is missing

Morphology signals to watch:

- fallback retries
- error handling loops
- explicit clarification / intervention
- whether the agent over-fixes unrelated OCR plumbing

### AS-PM-004: `grid_template` security audit

Purpose:

- Verify the gate logic around OCR keyword counts and structural confidence so `grid_template` does not become an unsafe auto-sign path.

Candidate real task:

- `grid_template` audit and gate behavior

Project state:

- `grid_template` is intentionally conservative / closed
- detector safety audit already exists in tests

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- tighter template-matching safety
- clearer reasoning about threshold boundaries
- less risk of over-eager auto-signing

Morphology signals to watch:

- branch switching between layout and OCR reasoning
- retry loops around threshold tuning
- human intervention when thresholds are ambiguous

### AS-PM-005: calibrator auto-match safety

Purpose:

- Verify that the GUI calibrator does not auto-load a template when the detection mode is `need_review`.

Candidate real task:

- calibrator matching behavior under ambiguous detections

Project state:

- `_loaded_template_id` behavior is testable
- `review_bbox` and paper-size hints exist
- template persistence is already covered by integration tests

Eligible prompt variants:

- `minimal_prompt`
- `expanded_constrained_prompt`
- `human_structured_prompt`

Expected project benefit:

- safer calibration workflow
- fewer accidental template auto-matches
- clearer manual review flow

Morphology signals to watch:

- template lookup retries
- clarification loops
- manual review preservation
- over-eager refactoring of the GUI flow

## Execution Log

| task_id | prompt_variant | runtime | repository_commit | session_ref | outcome | topology_label | event_count | tool_call_count | retry_density | branch_density | AskUserQuestion_count | human_intervention | correction_trigger | final_patch_quality | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AS-PM-001 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AS-PM-002 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AS-PM-003 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AS-PM-004 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| AS-PM-005 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Review Checklist

- Did `expanded_constrained_prompt` reduce invalid retry?
- Did it reduce `AskUserQuestion` or `human_intervention`?
- Did it reduce `need_review` handling errors?
- Did it over-constrain exploration or hide uncertainty?
- Did it improve final patch quality?
- Did `human_structured_prompt` outperform both extremes on this task?
- Should `Project A` use automatic prompt expansion by default for this task type?

## Reporting Rule

This pilot produces a project-level decision page for `Project A` and a morphology comparison page for `causetrace`.

Do not merge its results into native lane conclusions without explicit review.
