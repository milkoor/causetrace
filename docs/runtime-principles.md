# Runtime Principles

> Design principles for causetrace. These exist to protect runtime semantics —
> the project's core asset — against feature pressure, integration sprawl, and
> premature ontology.

---

### 1. Observe-first

causetrace records runtime behavior before attempting interpretation or enforcement.
Observation is the primitive; analysis is derived.

### 2. Causality over chronology

Temporal ordering is insufficient to explain agent behavior.
The causal graph is the primary runtime abstraction — not the timeline.

### 3. Runtime-native semantics

Schema evolves from real execution traces, not speculative ontology design.
Field additions must be reactive, not preemptive.

### 4. Fidelity over coverage

Higher-fidelity causality for one runtime is preferred over shallow support for
many. A wrong trace is worse than no trace.

### 5. Append-only runtime history

Execution traces are immutable. Events are never mutated after storage.
Any derived representation (summaries, aggregations) lives separately.

### 6. Runtime neutrality

causetrace observes runtimes rather than coupling to agent frameworks.
Hooks and tailers are boundary adapters, not core abstractions.

### 7. Semantic restraint

New event types and ontology categories require recurring evidence across
multiple independent runtimes before promotion to first-class fields.

### 8. Separate core from intelligence

Runtime IR (causal graph, schema, storage, query) is physically separate from
derived intelligence (analysis, prediction, summarization). The core has zero
dependency on AI inference.

### 9. Explicit analysis boundaries

Derived topology is scoped to the loaded session or window. Parent references
outside that scope remain source evidence, but they are not synthesized into
local nodes; their children are local roots. This keeps metrics consumable for
partial traces without rewriting stored history.

---

## Application

These principles override convenience. When a decision conflicts:

1. Prefer the option that preserves causal fidelity
2. Prefer the option that keeps the schema minimal
3. Prefer the option that maintains runtime neutrality
4. Only then consider developer convenience or feature velocity
