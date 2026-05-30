# Phase 3D Hypothesis Registry v0.2.5

This registry stores falsifiable hypotheses about runtime morphology. These are not conclusions and they do not change core schema, topology taxonomy, or readiness gates.

## Registry Rules

- Each hypothesis must be testable against a corpus snapshot.
- Every claim must name its corpus scope.
- Every validation must disclose denominator and lane.
- Negative results are first-class entries.
- Literature-derived ideas stay hypotheses until causetrace corpus evidence supports them.

## Hypothesis Categories

- runtime morphology hypotheses
- topology-task morphology hypotheses
- failure / near-failure morphology hypotheses
- human intervention morphology hypotheses
- observation-triggered transition hypotheses
- long-horizon software evolution hypotheses
- external generalization hypotheses
- epistemic runtime morphology hypotheses

## A. Runtime morphology hypotheses

### H-RM-001

- **Category:** runtime morphology
- **Claim:** dominant_chain is the default morphology in native coding-agent sessions.
- **Corpus scope:** native lane, strict research-grade, v0.2.5+
- **Required evidence:** native strict n >= 100; runtime distribution reported; task_type distribution reported; demo/non-demo disclosed
- **Metrics:** dominant_chain ratio; branch_density; transition_entropy; path_reuse_ratio
- **Falsification condition:** dominant_chain is not the plurality topology in native strict sessions after stratifying by runtime and task_type
- **Status:** open
- **Notes:** Baseline claim for native lane morphology, not a universal law

### H-RM-002

- **Category:** runtime morphology
- **Claim:** runtime-level topology differences shrink after controlling for `data_origin` and `task_type`.
- **Corpus scope:** native + controlled benchmark lanes, strict research-grade, v0.2.5+
- **Required evidence:** stratified runtime comparison; lane-separated distributions; sufficient per-runtime sample counts
- **Metrics:** topology distribution distance; branch_density; transition_entropy; path_reuse_ratio; long-session ratio
- **Falsification condition:** runtime separation remains large and stable after controlling for `data_origin` and `task_type`
- **Status:** open
- **Notes:** This is a confounder-control hypothesis, not a fingerprint claim

### H-RM-003

- **Category:** runtime morphology
- **Claim:** multi_root_exploration remains a minority morphology in native real_work sessions.
- **Corpus scope:** native lane, real_work subset, strict research-grade, v0.2.5+
- **Required evidence:** native real_work count; multi_root_exploration count; runtime distribution
- **Metrics:** multi_root_exploration ratio; root count distribution; branch_density
- **Falsification condition:** multi_root_exploration becomes a plurality or near-plurality morphology in native real_work sessions
- **Status:** open
- **Notes:** Useful as a baseline check on native lane diversity

## B. Topology-task morphology hypotheses

### H-TT-001

- **Category:** topology-task morphology
- **Claim:** review and exploration tasks are more likely to show multi_root_exploration than feature_add tasks.
- **Corpus scope:** native lane, strict research-grade, v0.2.5+
- **Required evidence:** task_type distribution; per-task topology distribution; sufficient review/exploration/feature_add counts
- **Metrics:** multi_root_exploration ratio by task_type; root spawning rate; transition entropy
- **Falsification condition:** feature_add matches or exceeds review/exploration in multi_root_exploration frequency after stratification
- **Status:** open
- **Notes:** Task-level association hypothesis

### H-TT-002

- **Category:** topology-task morphology
- **Claim:** feature_add tasks are more likely to show dominant_chain or branch_collapse than exploration tasks.
- **Corpus scope:** native lane, strict research-grade, v0.2.5+
- **Required evidence:** feature_add and exploration subsets; topology distributions; stratified runtime view
- **Metrics:** dominant_chain ratio; branch_collapse ratio; path_reuse_ratio
- **Falsification condition:** exploration matches or exceeds feature_add in dominant_chain or branch_collapse frequency after stratification
- **Status:** open
- **Notes:** Candidate comparison between goal-oriented and exploratory work

## C. Failure / near-failure morphology hypotheses

### H-FM-001

- **Category:** failure / near-failure morphology
- **Claim:** failure or near-failure sessions are enriched for retry_heavy or branchy topology.
- **Corpus scope:** native lane, failure and near-failure subsets, strict research-grade, v0.2.5+
- **Required evidence:** failure/near-failure sample count; success baseline; topology distribution by outcome
- **Metrics:** retry_heavy ratio; branchy ratio; transition entropy; repeated path count
- **Falsification condition:** failure/near-failure sessions do not exceed successful sessions in retry_heavy or branchy morphology after stratification
- **Status:** open
- **Notes:** Requires more failure data before strong claims

### H-FM-002

- **Category:** failure / near-failure morphology
- **Claim:** failed sessions are less likely to show branch_collapse than successful sessions.
- **Corpus scope:** native lane, failed vs successful subsets, strict research-grade, v0.2.5+
- **Required evidence:** failed sample count; successful baseline; branch_collapse distribution
- **Metrics:** branch_collapse ratio; path_reuse_ratio; branch density
- **Falsification condition:** failed sessions show equal or higher branch_collapse frequency than successful sessions
- **Status:** open
- **Notes:** May indicate unresolved work instead of convergence

## D. Human intervention morphology hypotheses

### H-IM-001

- **Category:** human intervention morphology
- **Claim:** human intervention acts as an external correction trigger.
- **Corpus scope:** native lane, human_intervention subset, strict research-grade, v0.2.5+
- **Required evidence:** intervention sample count; pre/post comparison; explicit intervention markers
- **Metrics:** branch collapse rate after intervention; topology transition distance; retry density
- **Falsification condition:** intervention does not coincide with measurable correction-like topology changes
- **Status:** open
- **Notes:** Requires intervention-rich corpus before validation

### H-IM-002

- **Category:** human intervention morphology
- **Claim:** post-intervention traces show topology regime shifts.
- **Corpus scope:** native lane, human_intervention subset, strict research-grade, v0.2.5+
- **Required evidence:** trace segments before and after intervention; comparable task slices
- **Metrics:** topology distance; branch density; transition entropy; root spawning rate
- **Falsification condition:** post-intervention topology remains statistically indistinguishable from pre-intervention topology
- **Status:** open
- **Notes:** Useful for later controlled transition studies

## E. Observation-triggered transition hypotheses

### H-OT-001

- **Category:** observation-triggered transition
- **Claim:** test failures trigger corrective branch exploration.
- **Corpus scope:** native lane and controlled benchmark lane, strict research-grade, v0.2.5+
- **Required evidence:** test-failure-linked traces; before/after observation windows; outcome labels
- **Metrics:** branch exploration rate after failure; retry density; path reuse ratio
- **Falsification condition:** test failures do not precede an increase in corrective exploration
- **Status:** open
- **Notes:** Suitable for Phase 3E controlled transition studies

### H-OT-002

- **Category:** observation-triggered transition
- **Claim:** contradictory tool observations precede branch_collapse.
- **Corpus scope:** native lane and controlled benchmark lane, strict research-grade, v0.2.5+
- **Required evidence:** explicit contradictory observation markers; transition windows; lane-separated examples
- **Metrics:** branch_collapse ratio after contradiction; transition entropy; branch density
- **Falsification condition:** contradictory observations do not precede collapse-like transitions
- **Status:** open
- **Notes:** Requires event-level observation annotations

## F. Long-horizon software evolution hypotheses

### H-LH-001

- **Category:** long-horizon software evolution
- **Claim:** long-horizon software evolution tasks produce more fan-in and branch-collapse than single-issue tasks.
- **Corpus scope:** native lane, long-session subset, strict research-grade, v0.2.5+
- **Required evidence:** task duration/length labels; long-horizon designation; fan-in and collapse counts
- **Metrics:** fan-in ratio; branch_collapse ratio; path reuse ratio; root spawning rate
- **Falsification condition:** long-horizon tasks do not exceed single-issue tasks in fan-in or branch_collapse
- **Status:** open
- **Notes:** Bridges morphology with task longevity

### H-LH-002

- **Category:** long-horizon software evolution
- **Claim:** multi-file tasks increase root spawning and transition entropy.
- **Corpus scope:** native lane, multi-file task subset, strict research-grade, v0.2.5+
- **Required evidence:** multi-file task labels; comparison baseline; sufficient sample size
- **Metrics:** root spawning rate; transition entropy; frontier width
- **Falsification condition:** multi-file tasks do not show higher root spawning or entropy than single-file tasks
- **Status:** open
- **Notes:** Useful for refactor, feature_add, and repo-analysis comparisons

## G. External generalization hypotheses

### H-EG-001

- **Category:** external generalization
- **Claim:** controlled benchmark lanes will show lower branch entropy than native lanes after task normalization.
- **Corpus scope:** controlled benchmark lane vs native lane, strict research-grade, v0.2.5+
- **Required evidence:** controlled benchmark protocol; same-task multi-runtime runs; lane-separated comparison
- **Metrics:** branch entropy; branch density; dominant_chain ratio
- **Falsification condition:** controlled benchmark lanes do not differ from native lanes after task normalization
- **Status:** open
- **Notes:** Candidate for controlled benchmark validation only

### H-EG-002

- **Category:** external generalization
- **Claim:** external trajectories over-represent retry-heavy and branchy morphologies relative to native real_work sessions.
- **Corpus scope:** external trajectory lane vs native lane, strict research-grade, v0.2.5+
- **Required evidence:** explicit external provenance; reconstructed causality marker; lane isolation
- **Metrics:** retry_heavy ratio; branchy ratio; repeated path count
- **Falsification condition:** external trajectories do not differ materially from native real_work sessions in retry/branchy morphology
- **Status:** open
- **Notes:** Do not mix external evidence into native conclusions

## H. Epistemic runtime morphology hypotheses

### H-EV-001

- **Category:** epistemic runtime morphology
- **Claim:** sessions containing explicit uncertainty verbalization may show higher branch exploration or retry-heavy topology.
- **Corpus scope:** native lane, strict research-grade, v0.2.5+
- **Required evidence:** uncertainty markers; event windows; topology labels before/after markers
- **Metrics:** branch exploration rate; retry_heavy ratio; transition entropy
- **Falsification condition:** uncertainty markers do not precede more exploratory or retry-heavy topology
- **Status:** open
- **Notes:** Literature-informed, but requires corpus-backed validation

### H-EV-002

- **Category:** epistemic runtime morphology
- **Claim:** external tool observations, such as test failures or contradictory shell outputs, may substitute for epistemic verbalization as correction triggers.
- **Corpus scope:** native lane and controlled benchmark lane, strict research-grade, v0.2.5+
- **Required evidence:** observation markers; correction windows; event-level ordering
- **Metrics:** correction-trigger rate; branch exploration; branch collapse
- **Falsification condition:** tool observations do not act like correction triggers
- **Status:** open
- **Notes:** Strong candidate for transition studies

### H-EV-003

- **Category:** epistemic runtime morphology
- **Claim:** branch collapse may occur after either explicit uncertainty markers or external observations resolve uncertainty.
- **Corpus scope:** native lane and controlled benchmark lane, strict research-grade, v0.2.5+
- **Required evidence:** uncertainty markers, observation markers, collapse windows
- **Metrics:** collapse rate after marker windows; transition distance
- **Falsification condition:** collapse does not cluster after uncertainty resolution signals
- **Status:** open
- **Notes:** Requires dense event segmentation

### H-EV-004

- **Category:** epistemic runtime morphology
- **Claim:** failure sessions may contain silent divergence-like patterns where neither epistemic verbalization nor external observation triggers a corrective topology transition.
- **Corpus scope:** native lane, failure subset, strict research-grade, v0.2.5+
- **Required evidence:** failure sessions; absence of correction markers; topology persistence across windows
- **Metrics:** silent divergence candidate count; retry density; path reuse ratio
- **Falsification condition:** failure sessions consistently show corrective transitions after uncertainty markers or tool observations
- **Status:** open
- **Notes:** This is the most speculative hypothesis in the registry

### H-EV-005

- **Category:** epistemic runtime morphology
- **Claim:** human intervention may act as an external correction trigger and produce topology regime shifts.
- **Corpus scope:** native lane, human_intervention subset, strict research-grade, v0.2.5+
- **Required evidence:** intervention markers; pre/post comparison; topology shift windows
- **Metrics:** topology distance; branch collapse rate; retry density
- **Falsification condition:** human intervention does not produce measurable topology regime shifts
- **Status:** open
- **Notes:** Connects human-in-the-loop events to topology transitions
