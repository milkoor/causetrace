# Causal Runtime Dataset Design v0.1

CRDD defines how `causetrace` turns raw runtime traces into comparable research
datasets. It treats `causetrace` as a runtime causality dataset, governance
system, and research harness, not only as an ingestion tool.

## Position

The project has moved from instrumentation-dominant work to data-dominant
research work.

```text
Layer 1: ingestion system       hooks, parsers, CLI import paths
Layer 2: causal graph system    DAGs, topology metrics, corpus tools
Layer 3: research system        phases, governance, hypotheses, evidence grades
```

The next research bottleneck is not trace volume. It is comparability:
most raw sessions cannot yet support cross-session conclusions because their
runtime, task, outcome, lane, and provenance are incomplete or mixed.

## Core Rule

Do not treat the raw corpus as the research sample.

Every claim must name the dataset layer it uses:

| Layer | Meaning | Valid use |
| --- | --- | --- |
| `raw_corpus` | All locally stored sessions that parse as traces | Ingestion health, coverage, source inventory |
| `observational_corpus` | Sessions with enough structure for descriptive analysis | Morphology exploration, candidate discovery |
| `comparable_corpus` | Sessions with sufficient metadata and lane separation | Cross-session comparison |
| `experimental_subset` | Balanced, enriched, or controlled subset with explicit inclusion rules | Candidate validation and revalidation |

Counts from lower layers must not be reused as denominators for higher-layer
claims.

## Comparability Dimensions

A session becomes comparable only when the relevant comparison dimensions are
declared or explicitly marked unknown.

| Dimension | Why it matters |
| --- | --- |
| `runtime` | Allows runtime-family comparison and balance checks |
| `task_type` | Prevents task mix from masquerading as topology effects |
| `success` | Enables outcome correlation and failure contrast |
| `duration` | Supports cost and density interpretation |
| `task_source` | Separates real work, demo, proxy, and controlled sources |
| `intervention_lane` | Separates native control behavior from workflow interventions |
| `data_origin` | Separates native, controlled benchmark, and external trajectories |
| `human_intervention` | Makes control and recovery dynamics observable |

Missing metadata is not automatically disqualifying for descriptive work, but it
does disqualify a session from comparisons that depend on that dimension.

## Metadata Tiers

Metadata must keep provenance. Do not collapse inferred or manually completed
fields into factual capture fields.

| Tier | Meaning | Examples | Use in claims |
| --- | --- | --- | --- |
| `observed` | Captured directly from runtime, hook, parser, or sidecar at collection time | runtime, model, provider, timestamps | Strongest evidence |
| `derived` | Computed from trace structure or deterministic parser rules | topology class, event density, inferred duration | Usable with method disclosure |
| `experimental` | Added by reviewer or controlled protocol after the run | task_type label, success label, intervention tag | Usable only with provenance and reviewer/protocol disclosure |

Research reports must disclose the tier for fields that determine inclusion,
matching, or outcome classification.

## Required Subsets

CRDD requires named manifests for any theory refresh or cross-lane comparison.

| Subset | Purpose | Minimum inclusion rule |
| --- | --- | --- |
| `strict_research_grade` | Baseline runtime morphology | Runtime, task source, task type, success, and provenance are explicit or trusted |
| `balanced_cross_runtime` | Runtime comparison | Matched or capped per-runtime sample counts with task mix disclosed |
| `failure_enriched` | Boundary and recovery analysis | Failure and near-failure sessions intentionally oversampled and labeled |
| `intervention_lane` | Control vs intervention study | Native and intervention lanes separated before comparison |
| `controlled_prompt_morphology` | Prompt posture effect study | Variant tags and protocol provenance present |
| `safety_control` | Safety-boundary morphology | Safety-control signal definitions and annotation provenance present |

Subset manifests should include:

- corpus snapshot date
- source query or selection rule
- inclusion and exclusion criteria
- denominator before and after filtering
- runtime and task distribution
- metadata tier requirements
- known sampling bias
- intended claims and prohibited claims

## Sampling Bias Register

Every analysis that leaves descriptive counting must include a bias register.

Current known risks:

| Risk | Effect |
| --- | --- |
| Unlabeled majority | Raw session counts overstate research sample size |
| Failure scarcity | Failure morphology and recovery dynamics are underpowered |
| Intervention scarcity | Control-vs-intervention effects may be invisible or unstable |
| Runtime imbalance | Apparent morphology defaults may be runtime-specific |
| Success-label scarcity | Outcome correlation can be dominated by labeled subset bias |
| Duration absence | Event density and cost interpretations are incomplete |
| Post-hoc parsing | Causality may be parser-dependent for some runtimes |

Bias registers do not block analysis. They prevent overclaiming.

## Continuous Sampling Loop

Phase 4-3 remains a formal evidence refresh gate, but CRDD adds a continuous
sampling loop upstream of it.

```text
raw corpus
  -> classify candidate comparable sessions
  -> build subset manifests
  -> inspect balance and bias
  -> enrich failure/intervention/control samples
  -> re-run candidate checks in sandbox reports
  -> open formal Phase 4-3 only when evidence thresholds are satisfied
```

This loop does not upgrade evidence grades by itself. It prepares the comparable
subsets needed for a defensible grade change.

## Claim Discipline

Use these claim scopes:

| Scope | Allowed wording |
| --- | --- |
| Raw corpus | "The stored trace corpus contains..." |
| Observational corpus | "Among sessions with observable structure..." |
| Comparable corpus | "Among comparable sessions with declared metadata..." |
| Experimental subset | "Within the named subset and protocol..." |

Avoid statements that imply all stored sessions are equivalent research samples.

## Immediate Work Program

1. Create subset manifests for `strict_research_grade`, `balanced_cross_runtime`,
   `failure_enriched`, and `intervention_lane`.
2. Reclassify "metadata gap" work as "comparability gap" work.
3. Prioritize failure and near-failure acquisition over broad raw ingestion.
4. Preserve metadata tier provenance when filling labels.
5. Use Phase 4-3 triggers as formal promotion gates, not as the only sampling
   activity.

## Boundary

CRDD does not open Phase 5. It does not introduce prediction, anomaly detection,
leaderboards, or automated diagnosis. It only defines how runtime traces become
valid research datasets for morphology analysis.
