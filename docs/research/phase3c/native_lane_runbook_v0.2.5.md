# Native Lane Runbook (v0.2.5)

This runbook turns the current native-lane expansion targets into an execution plan. It is descriptive, not prescriptive, and it does not modify corpus metadata by itself.

## Objective

Grow the strict native lane beyond its current `54` sessions without degrading provenance discipline or reintroducing demo bias.

## Collection Principles

- Prefer real_work sessions only.
- Keep `data_origin = native` only when the session is clearly a direct native agent run.
- Keep demo, proxy-mediated, controlled benchmark, and external trajectories out of the native lane unless explicitly reviewed.
- Do not force every new session to be strict native; some sessions are useful precisely because they stay outside strict coverage and document the boundary.

## Suggested Batch Size

Collect the next `20` native candidates in one pass:

- `8` non-Anthropic runtime comparison sessions
- `6` underrepresented task-type sessions
- `4` branchy or multi-root candidates
- `2` failure or near-failure real_work sessions

## Runtime Comparison Batch

Goal: diversify native runtime signal beyond anthropic dominance.

Suggested runtimes:

- `Codex CLI`
- `Claude Code`
- `Aider`
- `OpenCode`

Suggested tasks:

- `review` on the same repository
- `feature_add` on a small CLI or reporting change
- `bug_fix` on a narrow failing test
- `project_init` or `migration` only if the session is real_work and reviewable

Prompt template:

```text
这是一次真实的 runtime 研究采集，不是修复任务。

目标：
- 在 causetrace 仓库中完成一个小而明确的真实工作任务

约束：
- 只做必要修改
- 先读代码和测试
- 必须运行相关测试
- 保持任务边界清晰
- 不要中途换题

输出要求：
- 最后说明你做了什么，跑了什么测试，是否完成
```

## Underrepresented Task-Type Batch

Goal: fill task-type gaps inside the native lane.

Prioritize:

- `debug_test`
- `migration`
- `doc_gen`
- `project_init`
- `bug_fix`
- `review`

Recommended tasks:

- fix a deliberately narrow test failure
- migrate a small config or file-format detail
- generate a short internal doc that summarizes one runtime flow
- initialize a small local research artifact or utility

## Branchy / Multi-Root Batch

Goal: collect sessions that are more likely to show mixed or multi-root structure.

Candidate task shapes:

- repo-wide review of a subsystem
- cross-file analysis with multiple entry points
- a task that requires checking CLI, hooks, and report layers together
- a task that begins in one module and is validated in another

Prompt template:

```text
请分析这个 causetrace 子系统如何工作，并完成一个小的真实任务。

约束：
- 先找入口，再追调用链
- 如果需要改动，只做最小改动
- 必须验证行为
- 不要把问题扩大成重构

目标：
- 保持任务真实
- 尽量形成多入口、多步骤、多验证的运行轨迹
```

## Failure / Near-Failure Batch

Goal: increase the failure corpus without fabricating failure.

Acceptable sources:

- a task that fails a test and is not fully repaired in the same session
- a task that needs human intervention
- a task that is abandoned after a reproducible blocker
- a task where the agent must explicitly report unresolved failure

Do not:

- invent failure
- label partial work as success
- reclassify demo artifacts as failure

## Annotation Rules After Each Session

Write or verify these fields:

- `data_origin = native`
- `task_source = real_work`
- `runtime`
- `task_type`
- `success`
- `human_intervention`
- `repo_language`
- `repo_size`
- provenance for each field as `annotation` or `explicit_sidecar`

## Review Checklist

For every new native candidate, verify:

- direct native capture path
- no proxy mediation
- no demo lane contamination
- no benchmark replay confusion
- task is still representable as real_work

## Recompute After the Batch

After the next 20 sessions, recompute:

- strict native count
- runtime distribution
- task-type distribution
- topology distribution
- mixed / multi-root count
- failure count
- human-intervention count

## Success Criteria

The batch is useful if it increases at least one of:

- non-Anthropic native sessions
- underrepresented task types
- non-dominant topology counts
- failure or near-failure sessions

It is also useful if it confirms that dominant_chain remains dominant after more native collection.
