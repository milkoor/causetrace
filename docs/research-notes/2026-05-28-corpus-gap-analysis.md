# Corpus gap analysis for 2026-05-28

This note captures the current state of the local corpus and the remaining conditions needed for the next topology milestone.

## Snapshot

- sessions: 509
- events: 10,145
- metadata sessions: 0
- annotated sessions: 27
- explicit runtime sessions: 0
- heuristic runtime sessions: 50
- task-type sessions: 27
- source sessions: 27

## Milestones

- Corpus scale: 509/1000 (remaining 491)
- Research-ready labeled corpus: 0/100 (remaining 100)
- Explicit runtime fingerprint set: 0/4 (remaining 4)
- Task taxonomy breadth: 7/4 (remaining 0)
- Fan-in exemplars: 1/10 (remaining 9)
- Branch-collapse exemplars: 1/10 (remaining 9)
- Multi-root exemplars: 2/10 (remaining 8)

## Coverage

- explicit runtime counts:
  - none
- task type counts:
  - exploration: 14
  - bug_fix: 5
  - unknown: 3
  - review: 2
  - debug_test: 1
  - feature_add: 1
  - migration: 1
- topology counts:
  - dominant_chain: 436
  - mixed: 72
  - multi_root_exploration: 1

## Structural Signals

- long sessions (>=100 events): 14
- branchy sessions: 95
- frontier-wide sessions (max width >= 4): 14
- retry-heavy sessions (retry density >= 0.2): 155
- fan-in sessions: 1
- branch-collapse sessions: 1
- multi-root sessions (roots >= 5): 2

## What this means

The corpus is no longer too small to study, but it is still too sparse in the dimensions that matter for topology research.

- Explicit metadata coverage is effectively absent.
- Labeled task coverage is still narrow.
- The corpus is dominated by linear or near-linear behavior.
- High-signal structural exemplars are rare enough that taxonomy work would still overfit if treated as complete.

## Next collection target

Before treating milestone taxonomy or runtime fingerprinting as stable, the corpus needs:

1. More explicit metadata sidecars.
2. More balanced task labels.
3. More fan-in, branch-collapse, and multi-root sessions.
4. Multiple runs from each runtime family under comparable task types.
