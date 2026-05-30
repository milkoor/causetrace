# Native Lane Research Candidates (v0.2.5)

This is a descriptive report for the current native lane. It does not alter metadata.

- native sessions: 54
- native strict sessions: 54

## Native Topology
- dominant_chain: 48
- mixed: 5
- multi_root_exploration: 1

## Native Strict Gap Matrix

### Strict native subset

- strict sessions: `54`
- runtime:
  - `anthropic`: `50`
  - `codex`: `2`
  - `claude`: `1`
  - `aider`: `1`
  - `sisyphus - ultraworker`: `1`
- task type:
  - `exploration`: `19`
  - `feature_add`: `10`
  - `review`: `9`
  - `bug_fix`: `6`
  - `project_init`: `5`
  - `debug_test`: `2`
  - `migration`: `1`
  - `doc_gen`: `1`
  - `unknown`: `1`
- topology:
  - `dominant_chain`: `48`
  - `mixed`: `5`
  - `multi_root_exploration`: `1`

### Strict native near-misses

None. The native lane now has complete strict coverage.

### Interpretation

- The native lane is still the cleanest research lane.
- The strict native subset is now `54` sessions.
- The next useful action is not more schema work; it is native-lane expansion with new real_work sessions, especially if they diversify runtime and topology beyond dominant_chain.
