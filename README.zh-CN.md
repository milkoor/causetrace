# causetrace

> [English](README.md)

**causetrace** 捕获 AI 智能体（Claude Code、OpenCode）的工具调用，并将其链接成因树与 DAG —— **而非扁平的时序线**。每个事件都记录了"为什么会发生"，支持回放、根因分析和异常检测。

> **数据源**: Claude Code（hooks）、OpenCode（日志监听）  
> **存储**: `~/.causetrace/data/<session_id>.jsonl` — 追加写入 JSONL，零外部依赖

---

## 功能展示

同一会话的四种视图 —— 扁平 vs. 因果。

### 时间线（扁平）

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

按时间排序，但看不出"为什么"发生。

### 因果树

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

父子链揭示了因果结构：每个工具调用都是对其父节点的直接响应。

### 因果链追踪

```
$ causetrace why ses_10d2f16e <event_id>
[03:13:38] Grep(pattern=counter) ──→
[03:13:38] Edit(file_path=docs/api.md) ──→
[03:13:38] Bash(command=python -m pytest tests/) ◀── TARGET
```

追溯**某个事件为何发生** —— 从任意事件回溯因果链直至根因。

### 多父节点 DAG

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

扇入 DAG 展示汇聚因果关系 —— 一个工具消费了多个前置结果。通过逗号分隔的 `parent_event_id` 支持多父节点因果链接。

---

## 快速开始

```bash
pip install causetrace

# 运行示例数据演示
causetrace timeline ses_10d2f16e
causetrace tree    ses_10d2f16e
causetrace replay  ses_10d2f16e --summary
causetrace why     ses_10d2f16e <event_id>
```

### 接入 Claude Code

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

### 扫描 OpenCode 日志

```bash
causetrace opencode --save
```

解析 OpenCode 日志文件，从时间邻近性推断因果关系，并保存为 causetrace 会话。

---

## 数据模型

每个事件是一个 `ToolEvent`。四个因果字段（`parent_event_id`, `session_id`, `event_type`, `caused_by`）使 causetrace 区别于扁平日志系统。

| 字段 | 说明 |
|------|------|
| `event_id` | UUID |
| `parent_event_id` | 因果父节点（逗号分隔支持扇入） |
| `session_id` | 所属会话 |
| `tool_name` | 例如 `Bash`、`Read`、`Write` |
| `tool_input` | 序列化的输入参数 |
| `tool_output` | 序列化的输出结果 |
| `timestamp` | ISO 8601 时间戳 |
| `duration_ms` | 执行耗时（毫秒） |
| `event_type` | `tool_call` / `reasoning` / `context_update` / `user_input` |
| `caused_by` | `user` / `reasoning` / event_id / 语义标签 |

---

## 命令参考

| 命令 | 说明 |
|------|------|
| `causetrace timeline <id>` | 扁平时间线 |
| `causetrace tree <id>` | 因果树 |
| `causetrace graph <id>` | 多父节点 DAG（扇入） |
| `causetrace sessions` | 列出所有会话 |
| `causetrace export <id>` | 导出 JSON |
| `causetrace replay <id>` | 回放溯源 |
| `causetrace why <id> <eid>` | 回溯因果链 |
| `causetrace opencode [--save]` | 扫描 OpenCode 日志 |

---

## 架构

```
┌──────────────┐    ┌──────────────┐
│ Claude Code  │    │   OpenCode   │
│  (hooks)     │    │  (log tail)  │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────┐
│         TraceRecorder            │
│  (因果链接、存储)                │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│         JSONStore                │
│  (追加写入 JSONL, 无数据库)      │
└──────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│   Tree / DAG Builders            │
│   Renderers / ReplayEngine       │
└──────────────────────────────────┘
```

| 模块 | 职责 |
|------|------|
| `causetrace/core.py` | 数据模型、`TraceRecorder`、`JSONStore`、树/DAG 构建、渲染器、`ReplayEngine` |
| `causetrace/causality.py` | 非结构化日志的时间因果推断 |
| `causetrace/cli.py` | argparse CLI，8 个子命令 |
| `causetrace/hooks/` | Claude Code hook 桥接 + OpenCode 日志监听 |

---

## 开发

```bash
git clone https://github.com/milkoor/causetrace.git
cd causetrace
pip install -e .
python -m pytest tests/ -v
```

---

## 许可

MIT
