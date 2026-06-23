# AI Behavior Science OS v1.0

`causetrace` is evolving from a runtime tracing tool into a full-stack AI
behavior science operating system with explicit separation of generation,
execution, observation, dataset design, and research validation.

## System Definition

AI Behavior Science OS is a system that:

1. generates controlled agent behavior scenarios through BDE,
2. executes them across agent runtimes,
3. captures runtime traces through `causetrace`,
4. structures traces into comparable datasets through CRDD,
5. derives and tests runtime morphology hypotheses.

## Architecture

```text
                +------------------------------------+
                |        Behavior Generation         |
                |              (BDE)                 |
                |  - prompt shaping                  |
                |  - failure injection               |
                |  - multi-agent simulation          |
                |  - task distribution design        |
                +----------------+-------------------+
                                 |
                                 v
                +------------------------------------+
                |          Execution Layer           |
                |       Agent Runtime Pool           |
                |  - Claude Code                     |
                |  - Codex CLI                       |
                |  - OpenCode                        |
                |  - Aider                           |
                |  - Continue.dev                    |
                +----------------+-------------------+
                                 |
                                 v
                +------------------------------------+
                |        Observability Layer         |
                |         causetrace core            |
                |  - event logging                   |
                |  - DAG / topology                  |
                |  - tool calls                      |
                |  - intervention tracking           |
                +----------------+-------------------+
                                 |
                                 v
                +------------------------------------+
                |      Dataset Design Layer          |
                |              CRDD                  |
                |  - comparable corpus               |
                |  - subset definitions              |
                |  - comparability scoring           |
                |  - experimental units              |
                +----------------+-------------------+
                                 |
                                 v
                +------------------------------------+
                |        Research Layer              |
                |   Phase 4 / Hypothesis System      |
                |  - runtime morphology theory       |
                |  - evidence grading                |
                |  - validation triggers             |
                +------------------------------------+
```

## Control Loop

```text
BDE -> Agent Runtime -> causetrace -> CRDD -> Hypothesis -> BDE
```

The loop is a research design loop, not an autonomous optimization loop.
No layer may silently change another layer's authority.

## Layer Authority

| Layer | Authority | Prohibition |
| --- | --- | --- |
| BDE | generate scenario descriptors | must not modify actual agent execution |
| Runtime pool | execute selected scenarios | must not define research claims |
| causetrace core | observe and persist traces | must not shape behavior |
| CRDD | structure comparable datasets | must not mutate corpus data |
| Research layer | grade evidence and hypotheses | must not hide denominators or lane scope |

## Current Implementation Boundary

The v1.0 implementation starts with passive interfaces:

- `causetrace.bde`: metadata-only scenario descriptors.
- `causetrace.crdd`: read-only subset compilation and comparability scoring.
- `causetrace corpus compile-subsets`: generates subset manifests from existing
  corpus records.
- `causetrace corpus analyze-gaps`: reports CERC subset coverage gaps.
- `causetrace corpus plan-experiments`: emits external-only experiment
  requirement queues with `must_not_execute=true`.
- `causetrace corpus ingest-feedback`, `update-gaps`, and
  `reprioritize-experiments`: normalize external feedback and reprioritize
  future sampling without execution authority.

The minimal experiment runner is not part of this boundary yet. It requires a
separate design review because it touches the execution layer.

## Safety Constraint

BDE must remain generate-only. `causetrace` remains a passive observer. CRDD
remains read-only over stored trace data and metadata. Any future experiment
runner must preserve these authority boundaries.
