# Data-Grounded Runtime Method Discovery v0.2.5

**Status**: Long-term research method. Not a new phase and not an implementation plan.

`causetrace` should discover methods from recorded runtime behavior rather than starting with a fixed theory and forcing traces to confirm it.

Core loop:

```text
Capture -> Curate -> Compare -> Hypothesize -> Validate -> Revise
```

Expanded path:

```text
real process records
-> structured corpus
-> reproducible analysis
-> observed patterns
-> falsifiable hypotheses
-> additional trace validation
-> revised method
```

This is the working rule:

```text
Do not assume a method improves performance, safety, or auditability.
Record it.
Compare it.
Then decide.
```

## Principle

All future method claims must be grounded in recorded runtime traces. A method is not considered effective unless its impact on performance, morphology, and auditability is separately recorded.

Final task success is not enough. A method may improve auditability while increasing overhead, reduce tool calls while weakening evidence, or improve performance while reducing human reviewability.

## Why This Matters

Agent systems change quickly. Preset theories about prompting, workflow structure, machine-state reasoning, audit summaries, or agent handoff can become stale or misleading.

The `machine_state + human_audit_summary` pilot is the current example. The initial expectation that structured state might improve efficiency was not supported on a small read-only task. The recorded runtime instead showed higher event count, more tool calls, longer elapsed span, and more output/reasoning tokens, while the visible benefit was clearer audit structure.

That negative performance result improved the method:

```text
machine_state is not a general performance optimization by default.
It is better treated as auditability instrumentation until larger traces show otherwise.
```

## Minimum Experiment Record

Future prompt, workflow, machine-state, handoff, or auditability experiments should record at least:

```yaml
experiment:
  id:
  date:
  task:
  project:
  runtime:
  model:
  agent:
  branch_or_lane:

groups:
  A:
    prompt_type:
    session_id:
  B:
    prompt_type:
    session_id:

metrics:
  performance:
    elapsed_time:
    output_tokens:
    reasoning_tokens:
    tool_calls:
    success:
  morphology:
    event_count:
    topology:
    max_depth:
    retry_density:
    branch_collapse:
  auditability:
    audit_summary_present:
    evidence_references:
    decision_trace_coverage:
    human_review_needed:
    unexplained_transitions:

conclusion:
  supported:
  not_supported:
  limitation:
  next_test:
```

## Separate Result Axes

Every method comparison should separate three result axes.

Performance:

- elapsed time
- output tokens
- reasoning tokens
- tool calls
- retry count or retry density
- success or failure

Morphology:

- event count
- topology label
- max depth
- branch or collapse behavior
- fan-in or multi-root behavior
- critical path length

Auditability:

- audit summary presence
- evidence references
- decision trace coverage
- human review entry points
- unresolved uncertainty
- unexplained topology transitions

These axes must not be collapsed into a single good or bad outcome.

## Method Claim Rules

- Do not infer method effectiveness from final success alone.
- Do not promote a method because it is fashionable, simpler to explain, or supported by external literature only.
- Do not treat a negative result as failure if it clarifies method boundaries.
- Do not merge intervention-lane evidence into native baseline conclusions without lane disclosure.
- Do not classify unknown sessions to improve apparent coverage.
- Do not change schema or topology taxonomy based on a pilot.
- Do not open Phase 4-3 or Phase 5 based on method pilots alone.

## Relationship To Roadmap

The long-term route becomes:

```text
Runtime Morphology
-> Auditability-aware Runtime Morphology
-> Data-grounded Method Discovery
-> Agentic Audit Infrastructure
```

`causetrace` should not directly prescribe which agent method to use. It should record real processes, compare methods across performance, morphology, and auditability, and let repeated runtime evidence shape later hypotheses and theory.
