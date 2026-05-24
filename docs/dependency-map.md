# Dependency Map

> Internal dependency graph for causetrace. Use this to assess change impact
> before modifying any module.

## Layer 1: Core (`causetrace/core.py`)

Zero intra-project dependencies. Foundation layer.

**Exports:** `ToolEvent`, `TraceRecorder`, `JSONStore`, `TimelineRenderer`,
`ReplayEngine`, `build_tree`, `trace_causal_chain`, `validate_session`,
`SCHEMA_VERSION`

**Consumed by:** every other module

| Consumer | What it uses |
|----------|-------------|
| `cli.py` | `JSONStore`, `ReplayEngine`, `TimelineRenderer`, `trace_causal_chain`, `validate_session` |
| `analysis.py` | (duck-typing only — no import of core, consumes ToolEvent interfaces) |
| `hooks/aider_bridge.py` | `TraceRecorder` |
| `hooks/claude_code.py` | `TraceRecorder` |
| `hooks/claude_project_parser.py` | `ToolEvent` |
| `hooks/codex_parser.py` | `ToolEvent` |
| `hooks/codex_tailer.py` | `ToolEvent`, `TraceRecorder` |
| `hooks/continue_tailer.py` | `ToolEvent`, `TraceRecorder` |
| `hooks/copilot_tailer.py` | `ToolEvent`, `TraceRecorder` |
| `hooks/opencode_parser.py` | `ToolEvent` |
| `hooks/opencode_tailer.py` | `ToolEvent`, `TraceRecorder` |
| `demo/run_demo.py` | `TraceRecorder` |
| `tests/test_invariants.py` | All core exports |
| `tests/test_hooks_integration.py` | `JSONStore`, `ToolEvent`, `build_tree` |

## Layer 1.5: Analysis (`causetrace/analysis.py`)

Zero intra-project dependencies. Operates on ToolEvent interfaces via duck-typing.

**Exports:** `compute_stats`, `find_roots`, `longest_path`, `fan_out_distribution`,
`connected_components`, `detect_repeated_paths`, `detect_common_transitions`,
`detect_fan_in_patterns`, `detect_branch_collapse`, `windowed`,
`transition_entropy`, `branch_density`, `root_spawning_rate`,
`path_reuse_ratio`

**Consumed by:**

| Consumer | What it uses |
|----------|-------------|
| `cli.py` | `compute_stats`, `find_roots`, `longest_path`, `detect_repeated_paths`, `detect_common_transitions`, `detect_fan_in_patterns` |
| `tests/test_dag_fixtures.py` | Public primitives and DAG boundary behavior |

**Boundary rule:** topology functions build edges only between events present in
the loaded session. A parent reference outside the loaded session is retained
in raw data but its child is a local analysis root.

## Layer 1.55: Invariants (`causetrace/invariants.py`)

Composable DAG correctness checkers. Zero intra-project dependencies.

**Exports:** `check_unique_ids`, `check_acyclicity`, `check_local_references`,
`check_root_definition`, `check_invariants`

**Consumed by:**

| Consumer | What it uses |
|----------|-------------|
| `tests/test_dag_fixtures.py` | `check_invariants` (parametrized invariant battery) |

## Layer 1.6: Annotation (`causetrace/annotation.py`)

Zero intra-project dependencies. Sidecar JSON metadata store for session task labels.

**Exports:** `load_annotation`, `save_annotation`, `list_annotated`, `list_unannotated`

**Consumed by:**

| Consumer | What it uses |
|----------|-------------|
| `cli.py` | All 4 exports |

## Layer 2: Causality (`causetrace/causality.py`)

**Exports:** `infer_relations`, `build_causal_graph`

**Consumed by:** legacy tailers only

| Consumer | What it uses |
|----------|-------------|
| `hooks/codex_tailer.py` | `infer_relations` |
| `hooks/continue_tailer.py` | `infer_relations` |
| `hooks/copilot_tailer.py` | `infer_relations` |
| `hooks/opencode_tailer.py` | `infer_relations` |

## Layer 3: Hooks & Parsers

### `hooks/claude_code.py`
- **Depends on:** `core.TraceRecorder`
- **Used by:** Claude Code hook bridge (external, via settings.json)
- **Tested by:** `tests/test_hooks_integration.py`

### `hooks/claude_project_parser.py`
- **Depends on:** `core.ToolEvent`
- **Used by:** `cli.py` → `enrich`, `enrich-sessions`
- **Tested by:** `tests/test_enrich.py`

### `hooks/opencode_parser.py`
- **Depends on:** `core.ToolEvent`
- **Used by:** `cli.py` → `enrich-opencode`, `enrich-opencode-sessions`
- **Tested by:** `tests/test_opencode_enrich.py`

### `hooks/codex_parser.py`
- **Depends on:** `core.ToolEvent`
- **Used by:** `cli.py` → `enrich-codex`, `enrich-codex-sessions`

### `hooks/opencode_tailer.py` (legacy)
- **Depends on:** `core.ToolEvent`, `core.TraceRecorder`, `causality.infer_relations`
- **Used by:** `cli.py` → `opencode`

### `hooks/codex_tailer.py` (legacy)
- **Depends on:** `core.ToolEvent`, `core.TraceRecorder`, `causality.infer_relations`
- **Used by:** `cli.py` → `codex`
- **Note:** validated rollout ingestion uses `codex_parser.py` via `enrich-codex`

### `hooks/continue_tailer.py`
- **Depends on:** `core.ToolEvent`, `core.TraceRecorder`, `causality.infer_relations`
- **Used by:** `cli.py` → `continue`

### `hooks/copilot_tailer.py`
- **Depends on:** `core.ToolEvent`, `core.TraceRecorder`, `causality.infer_relations`
- **Used by:** `cli.py` → `copilot`

### `hooks/aider_bridge.py`
- **Depends on:** `core.TraceRecorder`
- **Used by:** `cli.py` → `aider` (via `_handle_aider`)

## Layer 4: CLI (`causetrace/cli.py`)

The CLI is the **single integration point** — it wires all hooks/parsers to user-facing commands.

**Depends on:** `core`, `analysis`, `annotation`, `causality`, all hook/parser modules, `pathlib.Path`

**Subcommands and their dispatch:**

| Command | Handler | Module |
|---------|---------|--------|
| `timeline` | inline (uses `JSONStore.load`) | core |
| `tree` | inline (uses `JSONStore.load`) | core |
| `graph` | inline (uses `JSONStore.load`) | core |
| `sessions` | inline (uses `JSONStore.list_sessions`) | core |
| `export` | inline (uses `JSONStore.load`) | core |
| `replay` | inline (uses `ReplayEngine`) | core |
| `why` | inline (uses `trace_causal_chain`) | core |
| `opencode` | `scan_opencode()` | hooks/opencode_tailer |
| `aider` | `_handle_aider()` | hooks/aider_bridge |
| `continue` | `_handle_continue()` | hooks/continue_tailer |
| `codex` | `_handle_codex()` | hooks/codex_tailer |
| `copilot` | `_handle_copilot()` | hooks/copilot_tailer |
| `enrich` | `enrich_session()` | hooks/claude_project_parser |
| `enrich-sessions` | `list_claude_sessions()` | hooks/claude_project_parser |
| `enrich-opencode` | `enrich_opencode_session()` | hooks/opencode_parser |
| `enrich-opencode-sessions` | `list_opencode_sessions()` | hooks/opencode_parser |
| `enrich-codex` | `enrich_codex_session()` | hooks/codex_parser |
| `enrich-codex-sessions` | `list_codex_sessions()` | hooks/codex_parser |
| `validate` | inline (uses `validate_session`) | core |
| `stats` | inline (uses `compute_stats`) | analysis |
| `roots` | inline (uses `find_roots`) | analysis |
| `critical-path` | inline (uses `longest_path`) | analysis |
| `patterns` | inline (uses pattern detectors; JSON/CSV output) | analysis |
| `annotate` | `_handle_annotate()` | annotation |
| `compare` | `_handle_compare()` | analysis, annotation |
| `doctor` | `_run_doctor()` | cli (inline) |

## Layer 5: Tests

| Test file | Depends on |
|-----------|-----------|
| `tests/test_invariants.py` | All of `core` |
| `tests/test_hooks_integration.py` | `core.ToolEvent`, `core.JSONStore`, `core.build_tree` |
| `tests/test_enrich.py` | `hooks/claude_project_parser` (4 internals + list_sessions, parse_session) |
| `tests/test_opencode_enrich.py` | `hooks/opencode_parser` (4 internals + list_sessions, parse_session) |
| `tests/test_dag_fixtures.py` | `analysis` primitives, `core.validate_session`, fixture DAGs |

## Layer 6: Tools

| Tool | Depends on |
|------|-----------|
| `tools/codex_deepseek_proxy.py` | `httpx` (external), no causetrace deps |
| `tools/promote.py` | `httpx` only for the `devto-post` command |
| `demo/run_demo.py` | `core.TraceRecorder` |

---

## Change Impact Rules

```
core.py change          → EVERYTHING (all hooks, CLI, tests)
causality.py change     → all 4 legacy tailers
analysis.py change      → stats/roots/critical-path/patterns/compare + DAG tests
annotation.py change    → annotate/compare commands
parser change           → cli.py + its specific command + its specific test file
tailer change           → cli.py + its specific command + its tests
cli.py change           → no modules depend on it (it's the sink)
__init__.py change      → external consumers (pip installers)
```

### When modifying a parser (`*_parser.py`):

1. Check `cli.py` for the command handler
2. Run the corresponding enrich command manually
3. Run the corresponding test file

### When modifying `core.py`:

1. Run ALL tests (`tests/test_invariants.py` covers all core exports)
2. Check each hook/tailer for the specific core API it uses
3. Run `demo/run_demo.py` to verify integration

### When modifying `causality.py`:

1. Run all 4 tailers that use `infer_relations`
2. Verify `test_invariants.py` still passes

### When modifying `analysis.py`:

1. Run `python -m pytest tests/test_dag_fixtures.py -v`
2. Check session-local external-parent behavior and cycle boundedness
3. Exercise output contracts for `patterns --json` and `patterns --csv`
