# Controlled Benchmark Candidates (v0.2.5)

This is a candidate list only. It does not ingest data into any corpus lane by itself.

## Candidate Sources

- SWE-Gym
- SWE-EVO

These are controlled benchmark candidates, not native evidence.

## Recommended Benchmark Set

The first controlled benchmark set should be small and repeatable.

### Task Shapes

- narrow bug fix with a known failing test
- small feature change with a clear acceptance check
- repo review task with a fixed rubric
- short migration or config update

### Runtime Coverage

At minimum, compare each task across:

- Claude Code
- Codex CLI
- Aider
- OpenCode

If a runtime is unavailable for a task, record the gap rather than filling it with a different task.

## Candidate Matrix

| Candidate | Why it matters | Primary question | Lane |
| --- | --- | --- | --- |
| SWE-Gym | Controlled same-task comparison | Do runtime-level topology differences persist after task control? | controlled_benchmark |
| SWE-EVO | Longer-horizon task morphology | Does long-horizon work change fan-in, branch-collapse, or root spawning? | controlled_benchmark |
| Narrow bug fix | Stable failure shape | Does retry-heavy topology differ by runtime on the same failing test? | controlled_benchmark |
| Small feature task | Bounded acceptance | Does branching / convergence differ when the task is well-scoped? | controlled_benchmark |
| Repo review task | Read-heavy comparison | Does review shape differ from implementation tasks? | controlled_benchmark |
| Short migration task | Configuration and compatibility behavior | Does topology remain dominant_chain or branch toward mixed forms? | controlled_benchmark |

## Ingestion Rule

Do not ingest any item in this list until:

- manual origin annotation is complete
- the controlled benchmark protocol is accepted
- the lane baseline is recomputed after the first controlled batch

## What Not to Do

- Do not label these as native.
- Do not use them to patch native gaps.
- Do not blend them into strict native claims.
- Do not treat them as proof of runtime laws before comparison runs exist.

## Next Use

Once a benchmark batch exists, recompute:

- runtime distribution by task
- topology distribution by task
- retry density by runtime
- branch collapse by task
- human intervention by runtime
