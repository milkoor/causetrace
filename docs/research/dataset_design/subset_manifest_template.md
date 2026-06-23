# Subset Manifest Template

Use this template for any comparable or experimental subset used in morphology
analysis. A subset manifest is required before a subset can support Phase 4
candidate revalidation.

## Identity

- **subset_id**:
- **subset_type**:
- **created_at**:
- **corpus_snapshot_date**:
- **owner/reviewer**:
- **status**: draft | active | superseded | retired

## Purpose

- **research purpose**:
- **intended claims**:
- **prohibited claims**:
- **related theory candidates**:

## Source Corpus

- **data sessions before filtering**:
- **metadata sessions before filtering**:
- **source command/query**:
- **source files or manifests**:

## Inclusion Criteria

| Criterion | Required value | Metadata tier |
| --- | --- | --- |
| runtime |  | observed / derived / experimental |
| task_type |  | observed / derived / experimental |
| success |  | observed / derived / experimental |
| task_source |  | observed / derived / experimental |
| intervention_lane |  | observed / derived / experimental |
| data_origin |  | observed / derived / experimental |
| human_intervention |  | observed / derived / experimental |

Additional structural criteria:

- 

## Exclusion Criteria

- 

## Resulting Denominators

| Count | Value |
| --- | --- |
| sessions included |  |
| events included |  |
| sessions excluded |  |
| missing required metadata |  |
| rejected for lane ambiguity |  |
| rejected for parse/validation issues |  |

## Distribution

Runtime distribution:

| Runtime | Sessions | Events |
| --- | ---: | ---: |
|  |  |  |

Task distribution:

| Task type | Sessions | Events |
| --- | ---: | ---: |
|  |  |  |

Lane distribution:

| Lane | Sessions | Events |
| --- | ---: | ---: |
|  |  |  |

Outcome distribution:

| Outcome | Sessions |
| --- | ---: |
| success |  |
| failure |  |
| near_failure |  |
| unknown |  |

## Bias Register

| Bias risk | Present? | Mitigation |
| --- | --- | --- |
| unlabeled majority |  |  |
| failure scarcity |  |  |
| intervention scarcity |  |  |
| runtime imbalance |  |  |
| task imbalance |  |  |
| success-label scarcity |  |  |
| duration absence |  |  |
| post-hoc parsing |  |  |

## Validation Checks

- [ ] duplicate event scan completed
- [ ] broken parent references reviewed
- [ ] runtime/task/lane denominators disclosed
- [ ] metadata tiers disclosed
- [ ] excluded sessions counted
- [ ] bias register completed
- [ ] claims scoped to this subset only

## Notes

- 
