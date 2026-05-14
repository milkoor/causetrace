# causetrace

**causetrace** captures tool calls from AI agents (Claude Code, OpenCode) and links them into causal trees and DAGs — not flat timelines. Each event records *why* it happened via `parent_event_id` chains, enabling replay, root-cause analysis, and anomaly detection.

**causetrace** 捕获 AI 智能体（Claude Code、OpenCode）的工具调用，并将它们链接成因树与 DAG，而非扁平的时序线。每个事件通过 `parent_event_id` 链记录"为什么会发生"，支持回放、根因分析与异常检测。

---

## Features

- **Causal traceability** — events linked via parent→child chains, forming trees and DAGs
- **Multi-source** — Claude Code hooks, OpenCode log tailing
- **No database** — append-only JSONL files, zero dependencies
- **CLI** — timeline, tree, graph, replay, and `why` (causal chain tracing)
- **Replay engine** — step through a trace with provenance

## 特性

- **因果可追溯** — 事件通过父子链连接，形成树与 DAG
- **多数据源** — Claude Code hook、OpenCode 日志监听
- **无需数据库** — 追加写入 JSONL，零依赖
- **命令行** — 时间线、因果树、DAG、回放、因果链追踪
- **回放引擎** — 带溯源关系的逐步回放

---

## Quick Start

```bash
pip install causetrace

# Record a session from Claude Code
causetrace timeline <session_id>   # flat view
causetrace tree <session_id>       # causal tree
causetrace graph <session_id>      # DAG (fan-in)
causetrace replay <session_id>     # replay with provenance
causetrace why <session_id> <eid>  # trace causal chain
```

### Hook up Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "python3 /path/to/causetrace/hooks/claude_code.py",
          "timeout": 5
        }],
        "description": "causetrace - record tool call start"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "python3 /path/to/causetrace/hooks/claude_code.py",
          "timeout": 5
        }],
        "description": "causetrace - record tool call completion"
      }
    ]
  }
}
```

### Scan OpenCode logs

```bash
causetrace opencode --save
```

---

## Data Model

Every event is a `ToolEvent` with causal fields:

| Field | Description |
|-------|-------------|
| `event_id` | UUID |
| `tool_name` | e.g. `Bash`, `Read`, `Write` |
| `tool_input` | serialized input arguments |
| `tool_output` | serialized output |
| `timestamp` | ISO 8601 |
| `duration_ms` | execution time |
| `parent_event_id` | causal parent (comma-separated for fan-in) |
| `session_id` | owning session |
| `event_type` | `tool_call` / `reasoning` / `context_update` / `user_input` |
| `caused_by` | `user` / `reasoning` / event_id / semantic tag |

Storage: `~/.causetrace/data/<session_id>.jsonl` (append-only JSONL).

---

## CLI Reference

```
causetrace timeline [session_id]     Flat chronological view
causetrace tree [session_id]         Causal parent→child tree
causetrace graph [session_id]        Multi-parent DAG (fan-in)
causetrace sessions                  List recorded sessions
causetrace export <session_id>        Export as JSON
causetrace replay [session_id]        Replay trace with provenance
causetrace why <session_id> <eid>    Trace causal chain from event
causetrace opencode [--save]         Scan OpenCode logs
```

---

## Architecture

```
┌──────────────┐    ┌──────────────┐
│ Claude Code  │    │   OpenCode   │
│  (hooks)     │    │  (log tail)  │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────┐
│         TraceRecorder            │
│  (causal linking, storage)       │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│         JSONStore                │
│  (append-only JSONL, no DB)      │
└──────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│   Tree / DAG Builders           │
│   Renderers / ReplayEngine      │
└──────────────────────────────────┘
```

- **`causetrace/core.py`** — Data model, `TraceRecorder`, `JSONStore`, tree/DAG builders, renderers, `ReplayEngine`
- **`causetrace/causality.py`** — Temporal causality inference for unstructured OpenCode logs
- **`causetrace/cli.py`** — argparse-based CLI (8 subcommands)
- **`causetrace/hooks/`** — Claude Code hook bridge + OpenCode log tailer

---

## Development

```bash
git clone https://github.com/milkoor/causetrace.git
cd causetrace
pip install -e .

python -m pytest tests/ -v
```

---

## License

MIT
