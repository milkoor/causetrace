# Cross-project Prompt Morphology Study

Status: v0.1 and v0.2 complete.

This is a controlled cross-project experimental layer that studies whether prompt structure changes coding-agent runtime morphology, task outcome, and project-level execution quality across multiple active repositories.

It is not `causetrace` core, not a prompt tool, and not a standalone execution platform. `causetrace` provides observation, attribution, and morphology analysis. Active repositories provide real tasks, real constraints, and project-specific benefits.

## Project Roles

Public-facing labels:

- `Project A` = document automation workflow
- `Project B` = business SaaS workflow

### `causetrace`

- experiment protocol
- trace capture
- topology / morphology analysis
- cross-project trend synthesis
- hypothesis feedback

### `Project A`

- first pilot application repo
- suitable for long-chain calibration, rule conflict, fallback, signature safety, review, and correction tasks
- receives project-specific prompt templates and execution strategy

### `Project B`

- second pilot application repo
- suitable for business logic, product workflow, refactor, feature, and constraint-heavy SaaS tasks
- receives project-specific prompt templates and execution strategy

## Prompt Groups

| Group | Name | Description |
| --- | --- | --- |
| A | `minimal_prompt` | Original short prompt, usually a brief problem description. |
| B | `expanded_constrained_prompt` | AI-expanded strong-constraint prompt. This is a treatment group, not assumed to be better. |
| C | `human_structured_prompt` | Medium-detail human-written prompt used as a control. |

## Core Question

Does prompt structure change:

- runtime topology
- retry density
- branching and collapse behavior
- human intervention frequency
- success / near-failure / failure balance
- project-level delivery quality

## Execution Stages

1. `Project A` pilot.
2. `Project B` pilot.
3. Project-level decision pages.
4. Cross-project synthesis report.

## Output Layers

### Causetrace Output

`causetrace` receives morphology evidence such as:

- prompt variant vs `event_count`
- prompt variant vs `retry_density`
- prompt variant vs `branch_density`
- prompt variant vs `AskUserQuestion` count
- prompt variant vs `human_intervention`
- prompt variant vs `failure` / `near-failure`
- prompt variant vs topology label
- prompt variant vs convergence quality

### Project Output

Each application repo receives its own decision page with:

- whether automatic prompt expansion is recommended
- task types where expansion helps
- task types where expansion hurts or over-constrains
- reusable prompt templates
- task description guidelines
- pre-execution checklist
- observed morphology impact
- observed outcome impact

## Lane Rule

By default, sessions created for this study are treated as `controlled_benchmark` or `controlled_study` evidence, not native project truth, unless explicitly reviewed as naturally occurring native work.

Do not mix prompt morphology results into native lane conclusions without explicit review.

## Boundary

This study may inform `causetrace` hypotheses and project-level development workflows, but it must not change `causetrace` core schema, topology taxonomy, readiness gates, or native corpus conclusions without evidence.

## Working Documents

- [Apply-first phase](apply_first_phase.md)
- [Protocol](protocol_v0.1.md)
- [Project lanes](project_lanes.md)
- [Metrics](metrics.md)
- [Aggregation rules](aggregation_rules.md)
- [Execution queue](execution_queue_v0.1.md)
- [Project A 5-task pilot](project_a_5task_pilot_v0.1.md)
- [Project B 5-task pilot](project_b_5task_pilot_v0.1.md)
- [Project A decision page](project_a_decision_v0.1.md)
- [Project B decision page](project_b_decision_v0.1.md)
- [cross-project synthesis](cross_project_synthesis_v0.1.md)
- [pilot completion note](pilot_v0.1_completion_note.md)
- [pilot v0.2 runtime expansion note](pilot_v0.2_runtime_expansion_note.md)
- [pilot v0.2 completion note](pilot_v0.2_completion_note.md)
- [pilot v0.3 options](pilot_v0.3_options.md)
- [Project A pilot plan](project_a_pilot_plan.md)
- [Project B pilot plan](project_b_pilot_plan.md)
- [Report template](report_template.md)
- [Cross-project summary template](cross_project_summary_template.md)

## Boundary Note

v0.2 provides runtime expansion evidence, not a universal prompt morphology conclusion.
Project-level conclusions remain separate.
Cross-project synthesis may compare trends only.

## Public / Private Boundary

This public research branch intentionally redacts external project names, raw task details, exact business data, script paths, and raw session identifiers.
Detailed project-level execution records are kept outside the public `causetrace` repository.

## Related Skill Repo

- [prompt-routing](https://github.com/milkoor/prompt-routing-skill) provides the prompt-posture routing skill used to apply these findings in real agent workflows.
- It pairs with `causetrace` by selecting the prompt posture first and measuring the resulting morphology here.

## Prompt-Routing Intervention Lane

When this branch's findings are applied through `prompt-routing-skill`, treat the resulting sessions as a routed intervention lane:

- record that prompt posture selection was applied
- keep the routed lane separate from native direct-prompt traces
- compare morphology before generalizing the effect to any project workflow
- routed traces are workflow interventions, not natural baseline prompts
- direct-prompt native traces remain the only native direct baseline
- expanded prompt study traces stay in the controlled / intervention lane

## Public Export Workflow

Generate the public tree from a private source tree with:

```bash
python3 tools/export_public_cross_project_prompt_morphology.py <private-source-dir> <public-output-dir>
```

Only the redacted public output should be pushed to the public repository.

## Push-time Automation

Install the repository hooks once:

```bash
bash tools/install_public_export_hooks.sh
```

After that, `git push` will automatically validate that the public branch still
matches the redacted export and contains no sensitive terms from the private
source tree.
