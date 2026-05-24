"""First-run CLI and Claude Code setup tests."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from causetrace.core import JSONStore, validate_session


def _run_cli(home: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "causetrace", *args],
        env={**os.environ, "HOME": home},
        capture_output=True,
        text=True,
    )


def test_demo_creates_immediately_inspectable_session():
    with tempfile.TemporaryDirectory() as tmp:
        result = _run_cli(tmp, "demo")
        assert result.returncode == 0, result.stderr
        assert "Demo session saved:" in result.stdout
        assert "causetrace why" in result.stdout
        session_id = result.stdout.split("Demo session saved: ", 1)[1].split()[0]

        store = JSONStore(store_dir=str(Path(tmp) / ".causetrace" / "data"))
        events = store.load(session_id)
        assert len(events) == 6
        assert validate_session(events)["valid"] is True
        assert any("," in (event.parent_event_id or "") for event in events)

        why = _run_cli(tmp, "why", session_id, "demo-verify-fix")
        assert why.returncode == 0, why.stderr
        assert "demo-ver" in why.stdout
        assert "Bash" in why.stdout


def test_install_and_uninstall_claude_hook_preserve_existing_hooks():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / ".claude" / "settings.json"
        settings.parent.mkdir()
        original = {
            "hooks": {
                "PreToolUse": [{
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "existing-tool"}],
                }]
            },
            "permissions": {"allow": ["Read"]},
        }
        settings.write_text(json.dumps(original))

        installed = _run_cli(tmp, "install-claude-hook")
        assert installed.returncode == 0, installed.stderr
        assert "Installed:" in installed.stdout
        data = json.loads(settings.read_text())
        assert data["permissions"] == original["permissions"]
        assert len(data["hooks"]["PreToolUse"]) == 2
        assert "causetrace.hooks.claude_code" in json.dumps(data["hooks"])
        assert settings.with_name("settings.json.causetrace.bak").exists()

        repeated = _run_cli(tmp, "install-claude-hook")
        assert repeated.returncode == 0
        assert "Already installed:" in repeated.stdout
        assert len(json.loads(settings.read_text())["hooks"]["PreToolUse"]) == 2

        removed = _run_cli(tmp, "uninstall-claude-hook")
        assert removed.returncode == 0, removed.stderr
        data = json.loads(settings.read_text())
        assert data["hooks"]["PreToolUse"] == original["hooks"]["PreToolUse"]
        assert "PostToolUse" not in data["hooks"]
        assert data["permissions"] == original["permissions"]


def test_install_claude_hook_rejects_malformed_settings():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text("{bad")

        result = _run_cli(tmp, "install-claude-hook")
        assert result.returncode != 0
        assert "Cannot parse Claude settings file" in result.stderr
        assert settings.read_text() == "{bad"
