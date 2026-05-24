# Pattern: deep-linear-chain

## Session

session_id: 1a00157a-1359-4981-a11d-21f8164b2130
agent: claude-code
event_count: 1499
enriched: true (Claude Code project parser)
task: football system migration

## Raw Metrics

max_depth: 1273
roots: 1
leaf_nodes: 31
avg_chain_length: 1274
fan_out_max: 3
fan_out_avg: 1.0
link_ratio: 0.999
time_span: 2883m (~48h)

top_transitions:
- Bash -> Bash: 648
- Bash -> Read: 169
- Read -> Read: 167
- Read -> Bash: 144
- Read -> Edit: 81
- Edit -> Edit: 77
- Edit -> Read: 54
- Edit -> Bash: 46

## Observation

The session behaves like a single iterative repair chain rather than a branching planner graph. With 1 root and 1499 events, almost the entire session is one deep causal chain. The 31 leaf nodes indicate short side branches that terminate quickly while one dominant chain (depth=1273) absorbs the majority of execution.

Bash→Bash (648) dominates all transitions — 43% of all events are Bash. This suggests the agent operates primarily through shell commands, with occasional reads and edits interspersed.

Read→Edit (81) vs Edit→Read (54) ratio: slightly more read-before-edit than edit-then-re-read, but both are present and close.

## Cross-session Comparison

| Metric | Claude A (1499) | Claude B (1420) | Codex (672) |
|--------|----------------|----------------|-------------|
| roots | 1 | 193 | 2 |
| max_depth | 1273 | 749 | 641 |
| avg_chain | 1274 | 7.2 | 336 |
| fan-out max | 3 | 3 | 1 |
| Bash→Bash | 648 | 339 | 291 |

Session B (270e9651) has 193 roots with avg_chain_length=7.2 — a fundamentally different topology. Unlike Session A's single deep chain, Session B is made of many short independent chains. This may reflect a different task type (multi-step exploration vs focused repair).

## Open Questions

- Is single-root deep-linear topology specific to continuous repair tasks (migration, debugging)?
- Does multi-root topology correspond to exploration/learning phases?
- Do all coding agents converge toward deep linear chains given enough time?
- Is the Bash→Bash dominance a function of the agent's tool-use policy or the task's actual needs?
- Does long-depth correlate with successful task completion, or with oscillation/stuck states?