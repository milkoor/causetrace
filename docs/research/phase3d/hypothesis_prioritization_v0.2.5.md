# Phase 3D Hypothesis Prioritization v0.2.5

This prioritization groups hypotheses by what can be checked with the current corpus and what requires more data or controlled benchmarking.

## Tier 1: Checkable with current native lane

These can be checked first against the current native strict corpus, with stratification and lane disclosure.

- H-RM-001
- H-RM-002
- H-RM-003
- H-TT-001
- H-TT-002

## Tier 2: Requires more failure / intervention samples

These need a denser failure or human-intervention subset before validation is meaningful.

- H-FM-001
- H-FM-002
- H-IM-001
- H-IM-002
- H-EV-004
- H-EV-005

## Tier 3: Requires controlled benchmark or external lane

These should wait until the controlled benchmark protocol is actively used.

- H-OT-001
- H-OT-002
- H-EG-001
- H-EG-002
- H-EV-002
- H-EV-003

## Tier 4: Literature-inspired, registry-only until further evidence

These remain useful as hypothesis records, but should not be treated as near-term validation targets.

- H-EV-001
- H-LH-001
- H-LH-002

## Prioritization Notes

- Tier 1 is for immediate descriptive checks only.
- Tier 2 becomes actionable after native failure and intervention coverage increases.
- Tier 3 depends on controlled benchmark lane execution or external trajectory support.
- Tier 4 is reserved for future corpus expansion and transition studies.
