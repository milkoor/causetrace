# Pattern: edit-read-locality

## Session

session_id: 1a00157a-1359-4981-a11d-21f8164b2130
agent: claude-code
event_count: 1499

## Raw Metrics

Read frequency: 408 (27%)
Edit frequency: 178 (12%)

Transitions involving Edit/Read:
- Read -> Edit: 81
- Edit -> Read: 54
- Edit -> Bash: 46
- Edit -> Edit: 77
- Read -> Read: 167
- Read -> Bash: 144
- Bash -> Edit: 17

Edit→Read ratio: 54 out of 178 Edits (30%) are followed by a Read.

Read→Edit ratio: 81 out of 408 Reads (20%) are followed by an Edit.

Edit→Edit: 77 out of 178 Edits (43%) are followed by another Edit.

## Cross-session Comparison (Claude B: 270e9651)

Read frequency: 151 (11%)
Edit frequency: 203 (14%)

Transitions:
- Read -> Read: 66
- Read -> Thinking: 41
- Edit -> Edit: 103
- Edit -> Thinking: 60
- Edit -> Bash: 30
- Thinking -> Edit: 44

Distinctly different: Claude B interposes Thinking between Edit and Read. Edit→Thinking (60) is more common than Edit→Read (not in top 15). This suggests this agent reasons between mutations.

## Observation

The Read→Edit→Read cycle appears to be a fundamental agent operation: read context → make change → verify by re-reading. But Edit→Edit (77) is more common than Edit→Read (54), suggesting the agent often makes multiple edits before re-reading.

Claude B's Edit→Edit (103) is even more dominant relative to its event count. 51% of edits are followed by another edit, compared to 43% in Claude A.

The presence of Thinking between Edit and Read in Claude B (but not Claude A) raises a question: is Claude B's enriched trace capturing a different reasoning layer, or is the agent actually behaving differently?

Codex CLI shows Edit→Bash (34) instead of Edit→Read — the Codex agent tests after editing rather than re-reading.

## Open Questions

- Is the Read→Edit→Read pattern the core "cognition locality" primitive for coding agents?
- Does Edit→Edit indicate productive multi-step editing or oscillation (reverting changes)?
- Is Edit followed by Thinking qualitatively different from Edit followed by Read?
- Do different runtimes have characteristic Edit transitions (Claude: Edit→Read, Codex: Edit→Bash)?
- Could Edit→Edit ratio serve as a proxy for "agent certainty" (low = confident single edit, high = uncertain trial/error)?