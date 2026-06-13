"""Backfill agent and provider fields on existing JSONL sessions.

One-shot script — run once to fix historical data, not a permanent tool.
"""

import json
import os
import sys
from pathlib import Path

DATA_DIR = Path.home() / ".causetrace" / "data"


def _detect_provider(model: str | None) -> str:
    if not model:
        return ""
    m = model.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("deepseek"):
        return "deepseek"
    if m.startswith("ark-") or m.startswith("doubao"):
        return "bytedance"
    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        return "openai"
    if m.startswith("minimax"):
        return "minimax"
    return ""


def infer_fields(first_event: dict, session_id: str) -> tuple[str, str]:
    """Infer (agent, provider) from session metadata."""
    agent = first_event.get("agent") or ""
    provider = first_event.get("provider") or ""
    model = first_event.get("model") or ""

    if not agent:
        # Identify agent from session ID prefix or provider/model
        if session_id.startswith("ses_"):
            agent = "opencode"
        elif session_id.startswith("aider_"):
            agent = "aider"
        elif session_id.startswith("019"):
            agent = "codex"
        elif provider == "openai":
            agent = "codex"
        elif provider == "opencode":
            agent = "opencode"
        elif provider == "anthropic":
            agent = "claude-code"
        elif "doubao" in model and not provider:
            agent = "opencode"
        elif model in ("deepseek-v4-pro", "deepseek-chat", "deepseek-v4-flash",
                       "ark-code-latest", "doubao-seed-2.0-pro"):
            agent = "claude-code"
        elif "minimax" in model:
            agent = "opencode"
        else:
            # Default for UUID-format: Claude Code
            agent = "claude-code"

    if not provider:
        provider = _detect_provider(model)

    # Fallback: infer provider from agent when model is unavailable
    if not provider and agent:
        if agent == "opencode":
            provider = "bytedance"
        elif agent == "claude-code":
            provider = "deepseek"
        elif agent == "codex":
            provider = "openai"

    return agent, provider


def backfill_file(filepath: Path) -> tuple[int, int]:
    """Backfill agent/provider on all events in a JSONL file.

    Returns (total_events, fixed_events).
    """
    session_id = filepath.stem

    # Read all events
    events = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        return 0, 0

    # Infer from first event
    agent, provider = infer_fields(events[0], session_id)

    # Also look at the full session for better inference
    if not agent or agent == "claude-code":
        # Check if any event has agent set
        for evt in events:
            if evt.get("agent"):
                agent = evt["agent"]
                break

    fixed = 0
    for evt in events:
        changed = False
        if not evt.get("agent") and agent:
            evt["agent"] = agent
            changed = True
        if not evt.get("provider") and provider:
            evt["provider"] = provider
            changed = True
        if changed:
            fixed += 1

    # Write back
    with open(filepath, "w") as f:
        for evt in events:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    return len(events), fixed


def main():
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)

    files = sorted(DATA_DIR.glob("*.jsonl"))
    total_sessions = len(files)
    total_events = 0
    total_fixed = 0

    for fp in files:
        nevents, nfixed = backfill_file(fp)
        total_events += nevents
        total_fixed += nfixed
        if nfixed > 0:
            pct = nfixed * 100 // nevents if nevents else 0
            print(f"  {fp.stem}: {nfixed}/{nevents} events fixed ({pct}%)")

    print(f"\nBackfill complete: {total_sessions} sessions, "
          f"{total_events} events, {total_fixed} fixed")


if __name__ == "__main__":
    main()
