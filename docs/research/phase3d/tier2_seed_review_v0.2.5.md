# Phase 3D Tier 2 Seed Review v0.2.5

This note records the first review pass over the current Tier 2 candidate seeds.

It is not a failure taxonomy. It is a practical review of which sessions are worth the next acquisition pass.

## Reviewed Seed Set

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

## Main Observations

### 1. The only native failure anchor is structurally extreme

- `aider_902f54e8` is the only native failure anchor.
- It is a `mixed` topology session with `1350` events.
- It has `retry_density = 0.9997`.
- Its repeated transitions are dominated by `Bash -> Bash`.

This makes it a strong failure anchor, but also a special-case session that should not be treated as a generic failure prototype.

### 2. The strongest native candidate seeds are near-failure leads, not failures

Most high-retry native seeds are still marked `success = true`.

Common traits:

- `dominant_chain` topology
- high retry density
- repeated Bash, Read, or Edit loops
- real_work task source
- no explicit human-intervention positive examples

### 3. Runtime and task variety exist, but they are not yet enough for Tier 2 validation

The reviewed seed set includes:

- `anthropic`
- `claude-code`
- `codex`
- `claude`
- `aider`

and tasks such as:

- `exploration`
- `feature_add`
- `bug_fix`
- `review`
- `migration`
- `doc_gen`
- `project_init`

This is useful for acquisition, but not enough to validate failure morphology or human-intervention morphology.

### 4. Human-intervention coverage is still absent from the reviewed seeds

None of the reviewed native seeds provide a clear `human_intervention=true` example.

That means the current next step is acquisition, not validation.

## Acquisition Interpretation

The reviewed seed set suggests that Tier 2 should continue to focus on:

- real failure examples
- near-failure recovery traces
- explicit correction-trigger traces
- native human-intervention traces

## Next Action

- keep the native failure anchor
- use the high-retry seeds as acquisition leads
- continue collecting failure / near-failure / intervention examples
- do not validate Tier 2 hypotheses until the acquisition targets are materially met
