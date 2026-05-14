"""Demo: simulate an agent session with causal trace data.

Run:  python3 demo/run_demo.py
Then: causetrace timeline <id>
      causetrace tree <id>
      causetrace replay <id>
"""
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.core import TraceRecorder


def simulate_agent_session():
    recorder = TraceRecorder()

    print(f"Starting demo session: {recorder.session_id}")
    print("Generating causal trace...\n")

    # ── Turn 1: user asks to find a bug ──
    recorder.new_group()

    recorder.record_call("Read", {"file_path": "src/main.py"}, "def main():\n    print('hello')\n")
    time.sleep(0.15)

    recorder.record_call("Grep", {"pattern": "FIXME", "path": "src/"},
                         "src/utils.py:12: # FIXME: off-by-one error")
    time.sleep(0.2)

    # Grep result → Read the suspect file (causal chain)
    recorder.record_call("Read", {"file_path": "src/utils.py"},
                         "def counter(n):\n    for i in range(n+1): ...\n")
    time.sleep(0.15)

    # ── Turn 2: user asks to fix ──
    recorder.new_group()

    recorder.record_call("Read", {"file_path": "src/utils.py"},
                         "def counter(n):\n    for i in range(n+1): ...\n",
                         caused_by="need_context")
    time.sleep(0.1)

    recorder.record_call("Edit", {"file_path": "src/utils.py",
                                   "old_string": "range(n+1)",
                                   "new_string": "range(n)"},
                         "Edit applied successfully.",
                         caused_by="task_execution")
    time.sleep(0.2)

    # ── Verify the fix ──
    recorder.record_call("Bash", {"command": "python -m pytest tests/ -x"},
                         "==== 5 passed, 1 skipped ====",
                         caused_by="verification")
    time.sleep(0.15)

    # ── Turn 3: user asks to document ──
    recorder.new_group()

    recorder.record_call("Grep", {"pattern": "counter", "path": "docs/"},
                         "docs/api.md:36: counter function docs")
    time.sleep(0.1)

    recorder.record_call("Edit", {"file_path": "docs/api.md",
                                   "old_string": "range(n+1)",
                                   "new_string": "range(n)"},
                         "Edit applied successfully.",
                         caused_by="task_execution")
    time.sleep(0.15)

    recorder.record_call("Bash", {"command": "python -m pytest tests/"},
                         "==== 5 passed ====",
                         caused_by="verification")
    time.sleep(0.1)

    print(f"Recorded {len(recorder.events)} events to ~/.causetrace/data/{recorder.session_id}.jsonl\n")
    print("Commands:")
    print(f"  causetrace timeline {recorder.session_id}")
    print(f"  causetrace tree    {recorder.session_id}")
    print(f"  causetrace replay  {recorder.session_id}")
    print(f"  causetrace replay  {recorder.session_id} --summary")


if __name__ == "__main__":
    simulate_agent_session()
