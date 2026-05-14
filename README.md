# causetrace

**causetrace** captures tool calls from AI agents and links them into causal trees and DAGs — **not flat timelines**. Every event records *why* it happened, enabling replay, root-cause analysis, and anomaly detection.

**causetrace** 捕获 AI 智能体的工具调用，并将其链接成因树与 DAG —— **而非扁平的时序线**。每个事件都记录了"为什么会发生"，支持回放、根因分析和异常检测。

> **Data sources**: Claude Code (hooks), OpenCode (log tailing)  
> **数据源**: Claude Code（hooks）、OpenCode（日志监听）
>
> **Storage**: `~/.causetrace/data/<session_id>.jsonl` — append-only JSONL, zero external dependencies  
> **存储**: `~/.causetrace/data/<session_id>.jsonl` — 追加写入 JSONL，零外部依赖

---

## Showcase · 功能展示

The same session viewed four ways — flat vs. causal.  
同一会话的四种视图 —— 扁平 vs. 因果。

### Timeline (flat) · 时间线（扁平）

```
$ causetrace timeline ses_10d2f16e
[03:13:37] Read(file_path=src/main.py)
[03:13:37] Grep(pattern=FIXME)
[03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)
[03:13:38] Edit(file_path=src/utils.py)
[03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
[03:13:38] Edit(file_path=docs/api.md)
[03:13:38] Bash(command=python -m pytest tests/)
```

Chronological order, but no insight into *why* each event happened.  
按时间排序，但看不出"为什么"发生。

### Causal Tree · 因果树

```
$ causetrace tree ses_10d2f16e
[03:13:37] Read(file_path=src/main.py)
    └─ [03:13:37] Grep(pattern=FIXME)
      └─ [03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)  [caused by: need_context]
    └─ [03:13:38] Edit(file_path=src/utils.py)
      └─ [03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
    └─ [03:13:38] Edit(file_path=docs/api.md)
      └─ [03:13:38] Bash(command=python -m pytest tests/)
```

Parent→child chains reveal the causal structure: each tool call is a direct response to its parent.  
父子链揭示了因果结构：每个工具调用都是对其父节点的直接响应。

### Why (causal chain trace) · 因果链追踪

```
$ causetrace why ses_10d2f16e <event_id>
[03:13:38] Grep(pattern=counter) ──→
[03:13:38] Edit(file_path=docs/api.md) ──→
[03:13:38] Bash(command=python -m pytest tests/) ◀── TARGET
```

Trace *why a specific event happened* — follow the causal chain backward from any event to its root.  
追溯**某个事件为何发生** —— 从任意事件回溯因果链直至根因。

### Multi-parent DAG · 多父节点 DAG

```
$ causetrace graph ses_3e23bcc8
[02:42:40] Bash(command=python -m pytest tests/)  ← Edit(file_path=docs/api.md)
[02:42:41] Read(file_path=src/main.py)
[02:42:41] Grep(pattern=FIXME)  ← Read(file_path=src/main.py)
[02:42:41] Read(file_path=src/utils.py)  ← Grep(pattern=FIXME)
[02:42:41] Read(file_path=src/utils.py)
[02:42:41] Edit(file_path=src/utils.py)  ← Read(file_path=src/utils.py)
[02:42:41] Bash(command=python -m pytest tests/ -x)  ← Edit(file_path=src/utils.py)
[02:42:42] Grep(pattern=counter)
[02:42:42] Edit(file_path=docs/api.md)  ← Grep(pattern=counter)
```

Fan-in DAGs visualize convergent causation — one tool consuming multiple prior results. Support for multi-parent causal links via comma-separated `parent_event_id`.  
扇入 DAG 展示汇聚因果关系 —— 一个工具消费了多个前置结果。通过逗号分隔的 `parent_event_id` 支持多父节点因果链接。

---

## Quick Start · 快速开始

```bash
pip install causetrace

# Run a demo with sample data
causetrace timeline ses_10d2f16e
causetrace tree    ses_10d2f16e
causetrace replay  ses_10d2f16e --summary
causetrace why     ses_10d2f16e <event_id>
```

### Hook up Claude Code · 接入 Claude Code

Add to `~/.claude/settings.json` to start recording every Claude Code session automatically.  
添加到 `~/.claude/settings.json` 即可自动记录每个 Claude Code 会话。

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "*", "hooks": [{
      "type": "command",
      "command": "python3 /path/to/causetrace/hooks/claude_code.py",
      "timeout": 5
    }]}],
    "PostToolUse": [{ "matcher": "*", "hooks": [{
      "type": "command",
      "command": "python3 /path/to/causetrace/hooks/claude_code.py",
      "timeout": 5
    }]}]
  }
}
```

### Scan OpenCode logs · 扫描 OpenCode 日志

```bash
causetrace opencode --save
```

Parses OpenCode log files, infers causal relations from temporal proximity, and saves as a causetrace session.  
解析 OpenCode 日志文件，从时间邻近性推断因果关系，并保存为 causetrace 会话。

---

## Data Model · 数据模型

Every event is a `ToolEvent`. The four causal fields (`parent_event_id`, `session_id`, `event_type`, `caused_by`) distinguish causetrace from flat logging systems.  
每个事件是一个 `ToolEvent`。四个因果字段（`parent_event_id`, `session_id`, `event_type`, `caused_by`）使 causetrace 区别于扁平日志系统。

| Field | Description |
|-------|-------------|
| `event_id` | UUID |
| `parent_event_id` | Causal parent (comma-separated for fan-in) |
| `session_id` | Owning session |
| `tool_name` | e.g. `Bash`, `Read`, `Write` |
| `tool_input` | Serialized input arguments |
| `tool_output` | Serialized output |
| `timestamp` | ISO 8601 |
| `duration_ms` | Execution time |
| `event_type` | `tool_call` / `reasoning` / `context_update` / `user_input` |
| `caused_by` | `user` / `reasoning` / event_id / semantic tag |

---

## CLI Reference · 命令参考

| Command | Description | 说明 |
|---------|-------------|------|
| `causetrace timeline <id>` | Flat chronological view | 扁平时间线 |
| `causetrace tree <id>` | Causal parent→child tree | 因果树 |
| `causetrace graph <id>` | Multi-parent DAG (fan-in) | 多父节点 DAG |
| `causetrace sessions` | List recorded sessions | 列出所有会话 |
| `causetrace export <id>` | Export as JSON | 导出 JSON |
| `causetrace replay <id>` | Replay with provenance | 回放溯源 |
| `causetrace why <id> <eid>` | Trace causal chain from event | 回溯因果链 |
| `causetrace opencode [--save]` | Scan OpenCode logs | 扫描 OpenCode 日志 |

---

## Architecture · 架构

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
│   Tree / DAG Builders            │
│   Renderers / ReplayEngine       │
└──────────────────────────────────┘
```

| Module | Responsibility |
|--------|---------------|
| `causetrace/core.py` | Data model, `TraceRecorder`, `JSONStore`, tree/DAG builders, renderers, `ReplayEngine` |
| `causetrace/causality.py` | Temporal causal inference for unstructured logs |
| `causetrace/cli.py` | argparse CLI dispatching to 8 subcommands |
| `causetrace/hooks/` | Claude Code hook bridge + OpenCode log tailer |

---

## Development · 开发

```bash
git clone https://github.com/milkoor/causetrace.git
cd causetrace
pip install -e .
python -m pytest tests/ -v
```

---

## License · 许可

MIT
