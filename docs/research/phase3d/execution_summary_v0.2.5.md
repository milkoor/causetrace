# Phase 3D Execution Summary v0.2.5

This page is a short operational summary for the current Phase 3D state.

It does not replace the registry, the validation protocol, or the acquisition plan. It exists so the next execution step can start from a compact view.

## Current State

- Phase 3D: active
- Phase 2.5: complete
- Phase 3A: complete
- Phase 3B: complete
- Phase 3C: complete
- Phase 3E: reserved

## Corpus Baseline

- sessions: `980`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- data_origin labeled sessions: `980`
- missing data_origin: `0`
- data_origin coverage: `100%`
- native failure sessions: `1/100`
- native human_intervention=true sessions: `5/100`

## Tier 1 Status

- H-RM-001: supported
- H-RM-002: inconclusive
- H-RM-003: supported
- H-TT-001: not supported
- H-TT-002: supported with caveat

## Tier 2 Status

- Tier 2 is not validation-ready.
- Tier 2 remains acquisition-only.
- Current native failure anchor: `aider_902f54e8`
- Current native human-intervention exemplars: 5 sessions with explicit `AskUserQuestion` events

## Tier 2 Acquisition Targets

- native failure sessions: `10`
- native near-failure sessions: `10`
- native human_intervention=true sessions: `5` (target met)
- explicit correction-trigger sessions: `20`
- failure / near-failure coverage across at least `3` runtimes

## Native Candidate Seed Pointers

- `aider_902f54e8`
- `1645d1ea-b14d-4a49-bcb9-60c29ed4226c`
- `ses_192be68d4ffenQmPDOZBl4PLxS`
- `a6cdfbdf-45a6-4b5d-9998-ad2d16ac288b`
- `51f5dd18-1feb-4224-b6d7-5445bbdda5e2`
- `1a00157a-1359-4981-a11d-21f8164b2130`
- `1aa8aadf-59c1-4998-a2d8-79a838b3600f`
- `8d686330-8939-4ef7-a15f-deed94f8a076`
- `f4b12241-c80c-4fa3-9201-2d218db6030c`
- `0e4c8b35-f7d1-491d-b654-a2904677451c`
- `8d79b673-13f5-4985-904f-98e7219de91a`
- `0ad05f47-9856-454f-94af-51224ebb8497`
- `019e6d76-ffe2-7b82-ad40-8a351378ab5b`
- `1ad59fe8-a890-468c-a148-4b7a30d45936`
- `019e6c41-e043-7190-872f-60dae5e13eeb`

## Operating Rule

- Do not treat high retry density as failure by itself.
- Do not fabricate intervention or correction triggers.
- Keep the acquisition focused on real task failures, near-failures, and explicit intervention contexts.

## Next Action

Continue Tier 2 acquisition and then re-run the Tier 2 readiness check.
