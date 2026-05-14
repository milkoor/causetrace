# Trace Corpus

This directory stores real-world agent trace data for Runtime Reality Validation.

## Structure

```
traces/
  successful/     — clean sessions (normal task completion)
  failures/       — sessions where the agent failed (most valuable)
  loops/          — retry loops, oscillation, repeated failing edits
  retries/        — explicit retry patterns
  refactors/      — refactoring sessions
  debugging/      — bug-fix sessions
```

## File format

Each trace is a directory containing:

- `session.jsonl`       — raw append-only trace data
- `tree.txt`            — `causetrace tree` output
- `why-examples.txt`    — `causetrace why` for interesting events
- `observations.md`     — what was learned from this trace

## Naming convention

```
<agent>-<date>-<description>
```

Example: `claude-code-20260514-bugfix-session`

## How to submit

1. Run `causetrace export <session_id> > session.jsonl`
2. Run `causetrace tree <session_id> > tree.txt`
3. Add observations
4. Open a PR
