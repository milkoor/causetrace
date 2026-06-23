# Agentic Auditability Roadmap v0.2.5

**Status**: Long-term roadmap correction. Not an active implementation plan.

`causetrace` currently studies observable runtime morphology: the external structure of agent execution as represented by events, tool calls, messages, file changes, interventions, and topology transitions. The long-term research direction should now be framed as:

```text
Runtime Morphology
-> Auditability-aware Runtime Morphology
-> Data-grounded Method Discovery
-> Agentic Audit Infrastructure
```

This means future work may need to study not only what runtime structures are visible, but also whether those structures are human-auditable, machine-audited, partially observable, or opaque. This roadmap clarifies a future boundary only. It does not unfreeze Phase 4, open Phase 4-3, open Phase 5, change schema, or add audit automation.

## Strategic Position

`causetrace` should not position itself as a system for making agents more capable, faster, or more autonomous. Its long-term position is runtime auditability research infrastructure for high-performance AI agents.

Working positioning statement:

```text
causetrace studies the observable runtime and auditability morphology of high-performance AI agents.
```

The strategic premise is that mainstream agent development will often optimize first for capability, cost, latency, success rate, longer task chains, tool autonomy, and reduced human intervention. Auditability, explainability, and responsibility-chain reconstruction are likely to appear as downstream constraints rather than the primary optimization target.

For `causetrace`, the core question is therefore not whether an agent is faster or stronger. The core question is whether stronger, faster, more autonomous agents still leave enough observable evidence for humans and audit systems to reconstruct what happened, why it happened, what channels were covered, and where responsibility or uncertainty remains.

## Methodology

The future auditability branch should use data-grounded runtime method discovery:

```text
Capture -> Curate -> Compare -> Hypothesize -> Validate -> Revise
```

The rule is:

```text
Do not assume a method improves performance, safety, or auditability.
Record it.
Compare it.
Then decide.
```

Each method claim should separately report performance, morphology, and auditability effects. The `machine_state + human_audit_summary` pilot illustrates why this matters: it improved audit structure on a small read-only task but increased runtime overhead. That result is useful precisely because it corrects the method boundary rather than confirming the original efficiency expectation.

See [Data-Grounded Runtime Method Discovery](data_grounded_method_discovery_v0.2.5.md).

## Conceptual Layers

Auditability work should distinguish three different concepts that are easy to collapse.

Layer A: Prompt-level compressed text

Prompting an agent to "think in machine language," use symbols, or emit compact codes still operates at the visible text-token layer. It may reduce verbosity, but it does not give the model a true hidden-state, embedding, or KV-cache communication channel. For `causetrace`, this remains observable text morphology.

Layer B: Structured machine-state reasoning

Agents can maintain compact, structured state objects for task tracking, then expand only the audit-relevant parts into natural language. This is not latent reasoning, but it is immediately testable, auditable, and compatible with existing agent interfaces.

Example:

```yaml
msr_v1:
  goal: improve_metadata_capture
  scope: docs_only
  constraints:
    - no_schema_change
    - phase4_frozen
    - no_unknown_inference
  evidence:
    - 879_unknown_data_origin
    - trigger8_10_9_percent
  decision: future_capture_quality_only
  risk:
    - heuristic_pollution
  next_action: update_runbook
  stop_condition: git_diff_check_pass
```

Layer C: True latent or vector communication

True machine-language or latent communication requires model or system support, such as direct hidden-state transfer, embedding exchange, shared KV-cache, a latent reasoning head, or multi-agent collaboration in latent space. This is not available through ordinary prompting alone and is outside the current `causetrace` mainline.

## Why This Matters

Future agent systems may use compressed, latent, high-density, non-human-readable, or agent-to-agent communication channels. These channels may improve performance, latency, coordination, and token efficiency.

The trade-off is auditability. Natural-language traces may become incomplete external projections of the task process, while important coordination or reasoning moves occur in compact machine-readable channels. Human reviewers cannot manually inspect massive runtime traces at scale, so future AI audit will likely become highly automated.

That creates a second-order audit problem: if audit agents review other agents, the audit agents themselves must be traceable. Their reasoning, evidence selection, coverage limits, and report generation need audit trails rather than becoming a new opaque authority layer.

## Performance-Auditability Trade-Off

The long-term research axis is:

```text
Performance up vs. Auditability down
```

This is a hypothesis and research frame, not a validated law. It should guide future branch studies without changing current evidence grades.

Possible performance optimizations and auditability costs:

| Performance direction | Possible auditability cost |
| --- | --- |
| less visible reasoning | fewer decision justifications |
| shorter visible traces | missing intermediate states |
| latent or machine-readable communication | human-unreadable collaboration |
| automatic tool calls | larger external action surface |
| multi-agent collaboration | longer and less local responsibility chains |
| automatic repair or rollback | masked failure and recovery process |
| audit-agent summarization | second-order opacity |

The resulting research question is:

```text
When agent systems optimize for speed, cost, autonomy, or success rate, what evidence is lost, compressed, hidden, or shifted into channels that current trace capture does not cover?
```

The machine-state pilot reinforces this boundary in the opposite direction: auditability instrumentation is not free. It may improve reviewability while increasing runtime overhead.

## What Causetrace Should Study In The Future

Q1. Observable runtime projection:
Does the visible trace explain the task outcome, or are there unexplained topology transitions?

Q2. Performance-auditability trade-off:
Do higher performance, lower event counts, or shorter visible traces correlate with reduced human-auditable evidence?

Q3. Communication channel visibility:
Which communication channels are human-readable, machine-readable, partially observable, or opaque?

Q4. Safety-control coverage:
Do safety gates, `need_review`, hard-stop, fallback, and `human_intervention` signals cover the actual communication and execution channels?

Q5. Agentic audit traceability:
If an audit agent reviews another agent, is the audit agent's own reasoning, evidence selection, and report generation traceable?

Q6. Audit evidence sufficiency:
Does the audit report include evidence references, coverage limits, uncertainty, and human-review entry points?

## Structured Machine-State Reasoning

A practical near-term experiment is structured machine-state reasoning: agents exchange a compact `machine_state` object while also emitting a concise `human_audit_summary`.

The intended dual-channel shape is:

```text
machine_state channel: compact state for agent continuity
audit_summary channel: natural-language summary for human review
```

The `machine_state` channel should track fields such as:

- `goal`
- `scope`
- `constraints`
- `evidence`
- `decision`
- `risks`
- `next_action`
- `stop_condition`

Every material `machine_state` update should be paired with a human-auditable summary explaining:

- what decision was made
- what evidence supports it
- what remains uncertain
- what requires human review

This preserves a useful compromise: higher-density agent state without turning the workflow into unreadable or unaudited communication.

This roadmap explicitly rejects unreadable pseudo-machine language, random encodings, Base64-style obfuscation, private agent shorthand that bypasses review, or hidden reasoning used to avoid human oversight.

## Future Concepts, Not Current Schema

The following are future concepts only:

- `auditability_morphology`
- `performance_auditability_tradeoff`
- `visible_runtime_projection`
- `opaque_communication_boundary`
- `audit_agent_trace`
- `audit_evidence_graph`
- `channel_visibility`
- `auditability_score`
- `decision_trace_coverage`
- `safety_gate_coverage`
- `human_review_queue`
- `audit_report_provenance`
- `structured_machine_state_reasoning`
- `human_audit_summary`

These are not current schema fields and must not be added until supported by corpus evidence and a separate design review.

## Audit Automation Hierarchy

The expected future structure has four layers.

Layer 1: Runtime capture

- events
- tool calls
- messages
- file changes
- memory access
- permission use
- A2A communication where available

Layer 2: Machine audit

- automated screening
- policy checks
- causal graph analysis
- anomaly candidates
- safety-control coverage analysis
- audit agent summaries

Layer 3: Evidence package

- evidence references
- coverage report
- uncertainty report
- risk triage
- unresolved gaps
- human review queue

Layer 4: Human oversight

- high-risk sample review
- policy judgment
- exception approval
- liability and governance decisions

The human role shifts from reading every trace to auditing the audit system, reviewing high-risk cases, and approving risk boundaries.

## Non-Goals

`causetrace` must not become:

- a hidden-language decoder
- a latent-state interpreter
- a jailbreak or covert-channel research tool
- a universal safety classifier
- an automatic diagnosis engine
- a prediction system
- a generic observability SaaS
- an unverified audit-agent platform

## Mainline Impact

- Phase 4 remains frozen.
- Phase 4-3 remains trigger-gated.
- Phase 4-3 remains at 0/8 triggers met.
- New literature alone does not trigger Phase 4-3.
- Phase 5 remains closed.
- This roadmap only clarifies future direction.
- Any future move toward auditability morphology requires explicit corpus triggers or a separate branch.

## Branch Proposal

Branch name:

```text
agentic_auditability_branch
```

Purpose:

Study auditability morphology and agentic audit traceability without changing the `causetrace` mainline.

Allowed scope:

- literature notes
- external examples
- small controlled pilots
- auditability metrics prototypes
- audit report provenance experiments
- structured machine-state reasoning pilots with human audit summaries

Disallowed scope:

- mainline schema changes
- Phase 5 opening
- automatic safety judgment
- automatic unknown-session classification
- hidden language decoding
- latent hidden-state or KV-cache integration in the mainline
- unreadable pseudo-machine-language protocols

### Possible Sub-Branch: machine_state_reasoning_branch

Purpose:

Study whether structured `machine_state` reduces token use, event count, retry density, or handoff cost while preserving or improving auditability through paired `human_audit_summary` records.

Comparison groups:

| Group | Description |
| --- | --- |
| A | ordinary natural-language prompt |
| B | structured `machine_state` |
| C | structured `machine_state` plus `human_audit_summary` |
| D | minimal prompt |

Candidate metrics:

- `event_count`
- `tool_call_count`
- `retry_density`
- `branch_collapse`
- `success`
- `human_review_time`
- `audit_summary_quality`
- `decision_trace_coverage`

This sub-branch must remain experimental. It must not add schema fields, classify unknown sessions, open Phase 5, or infer that compact traces are deeper, safer, or more capable without corpus evidence.

## Current Boundary

This document is a roadmap correction from runtime-only morphology toward auditability-aware runtime research. It does not classify unknown sessions, promote any theory candidate, add topology classes, add schema fields, or implement audit agents.
