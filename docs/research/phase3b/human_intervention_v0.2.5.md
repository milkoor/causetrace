# Phase 3B Human Intervention: v0.2.5

Date: 2026-05-29

This report checks whether human intervention is represented strongly enough in
the strict subset to support stratified comparison.

## Corpus Snapshot

- strict research-grade sessions: `107`
- explicit `human_intervention=true` in strict subset: `0`
- explicit `human_intervention=false` in strict subset: `81`
- missing `human_intervention`: `26`

## Topology Distribution

| label | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: |
| human_intervention=false | 70 | 9 | 2 |
| missing | 25 | 0 | 1 |

## Descriptive Metric Means

| label | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| human_intervention=false | 81 | 0.3307 | 1.1225 | 0.3714 | 18.1975 |
| missing | 26 | 0.1009 | 2.5432 | 0.3634 | 4.4231 |

## Observations

- There are no positive strict cases with `human_intervention=true` in this snapshot.
- The split is therefore not balanced enough to support a meaningful comparison.
- The missing group is not an intervention group; it is a metadata gap.

## Negative Results

- No human-intervention effect can be inferred from the strict subset.
- The corpus needs explicit positive `human_intervention=true` examples before this split becomes useful.
