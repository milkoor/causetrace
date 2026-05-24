#!/usr/bin/env python3
"""Generate DAG fixture JSONL files for topology invariant testing.

Each fixture is a valid `causetrace/core.py` ToolEvent JSONL file with known
topological properties, used to verify analysis.py primitives against regression.

Run:  python3 tests/fixtures/dags/generate_fixtures.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

FIXTURE_DIR = Path(__file__).resolve().parent


def _ev(event_id: str, tool_name: str = "Read", parent_event_id: str | None = None,
        timestamp: str | None = None, **kw) -> str:
    d = {
        "schema_version": "0.1",
        "event_id": event_id,
        "tool_name": tool_name,
        "tool_input": kw.get("tool_input", {}),
        "tool_output": kw.get("tool_output"),
        "timestamp": timestamp or "2026-01-01T00:00:00",
        "duration_ms": kw.get("duration_ms"),
    }
    if parent_event_id:
        d["parent_event_id"] = parent_event_id
    return json.dumps(d, sort_keys=True) + "\n"


FIXTURES = {}

# 1. Simple chain: root → a → b → c
FIXTURES["chain"] = "".join([
    _ev("root", "Read"),
    _ev("a", "Bash", "root"),
    _ev("b", "Edit", "a"),
    _ev("c", "Read", "b"),
])

# 2. Fan-in: two separate roots converge on one child
# root_a → target
# root_b → target
FIXTURES["fan-in"] = "".join([
    _ev("root_a", "Read"),
    _ev("root_b", "Grep"),
    _ev("target", "Edit", "root_a,root_b"),
])

# 3. Deep merge: same root, two branches merge
# root → a → c
# root → b → c
FIXTURES["deep-merge"] = "".join([
    _ev("root", "Read"),
    _ev("a", "Bash", "root"),
    _ev("b", "Grep", "root"),
    _ev("c", "Edit", "a,b"),
])

# 4. Diamond: two-layer merge
# root → a → c
# root → b → d
#         c → target
#         d → target
FIXTURES["diamond"] = "".join([
    _ev("root", "Read"),
    _ev("a", "Bash", "root"),
    _ev("b", "Grep", "root"),
    _ev("c", "Edit", "a"),
    _ev("d", "Write", "b"),
    _ev("target", "Bash", "c,d"),
])

# 5. Cycle corruption: a → b → c → a
FIXTURES["cycle"] = "".join([
    _ev("a", "Bash", "c"),
    _ev("b", "Read", "a"),
    _ev("c", "Edit", "b"),
])

# 6. Disconnected forest: two independent trees
#  a → b
#  c → d → e
FIXTURES["forest"] = "".join([
    _ev("a", "Read"),
    _ev("b", "Bash", "a"),
    _ev("c", "Grep"),
    _ev("d", "Edit", "c"),
    _ev("e", "Write", "d"),
])

# 7. Deep linear chain: 10 nodes
FIXTURES["deep-chain"] = "".join([
    _ev(f"n{i:03d}", "Bash" if i % 2 else "Read", f"n{i-1:03d}" if i > 0 else None)
    for i in range(10)
])

# 8. Multi-level fan-in with timestamp ordering
# (ordered to verify causal chain order is preserved)
FIXTURES["timed-fan-in"] = "".join([
    _ev("r1", "Read", timestamp="2026-01-01T00:00:01"),
    _ev("r2", "Grep", timestamp="2026-01-01T00:00:02"),
    _ev("w1", "Write", "r1,r2", timestamp="2026-01-01T00:00:03"),
    _ev("e1", "Edit", "w1", timestamp="2026-01-01T00:00:04"),
])

# 9. Fork: one root, two children (no merge)
FIXTURES["fork"] = "".join([
    _ev("root", "Read"),
    _ev("a", "Bash", "root"),
    _ev("b", "Grep", "root"),
])

# 10. Multi-parent cycle (from the audit scenario)
# a.parent_event_id="root,b", b.parent_event_id="a"
FIXTURES["multi-parent-cycle"] = "".join([
    _ev("root", "Read"),
    _ev("a", "Bash", "root,b"),
    _ev("b", "Edit", "a"),
])


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in sorted(FIXTURES.items()):
        path = FIXTURE_DIR / f"{name}.jsonl"
        path.write_text(content)
        line_count = len([l for l in content.splitlines() if l.strip()])
        print(f"  {name:20s}  {line_count} events → {path.name}")


if __name__ == "__main__":
    main()