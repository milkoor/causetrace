#!/usr/bin/env python3
"""Promotion toolkit for causetrace.

Usage:
    # Publish a blog post to dev.to
    python3 tools/promote.py devto-post docs/promotion/blog.md --api-key "$DEVTO_KEY"

    # Update an existing dev.to article after reviewing the source draft
    python3 tools/promote.py devto-update <article_id> docs/promotion/blog.md --api-key "$DEVTO_KEY"

    # Format tweet text (check length, strip ANSI)
    python3 tools/promote.py tweet "Your tweet text here"

    # Format HN post (strip project name / GitHub links from text)
    python3 tools/promote.py hn-strip < input.txt > output.txt

    # Generate promotion checklist for a new version
    python3 tools/promote.py checklist v0.2.0 "brief description of what's new"

Environment:
    DEVTO_API_KEY — dev.to API key for blogging
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _devto_article(md_path: Path) -> dict:
    """Build a dev.to article payload from a Markdown source file."""
    content = md_path.read_text()
    title = ""
    tags = ["opensource", "ai"]
    description = ""

    for line in content.splitlines():
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            title = m.group(1).strip()
            break

    if not title:
        title = md_path.stem.replace("_", " ").replace("-", " ").title()

    for line in content.splitlines():
        if line.strip() and not line.startswith("#") and not line.startswith("---"):
            description = line.strip()[:150]
            break

    return {
        "title": title,
        "body_markdown": content,
        "tags": tags[:4],
        "description": description or title,
        "published": True,
    }


def _api_key(args: list[str]) -> str:
    api_key = os.environ.get("DEVTO_API_KEY", "")
    for i, value in enumerate(args):
        if value == "--api-key" and i + 1 < len(args):
            api_key = args[i + 1]
    if not api_key:
        print("Error: DEVTO_API_KEY not set. Provide via --api-key or DEVTO_API_KEY env var.",
              file=sys.stderr)
        sys.exit(1)
    return api_key


def cmd_devto_post(args: list[str]) -> None:
    """Publish a Markdown file as a new dev.to article."""
    import httpx  # only needed for devto-post
    if not args:
        print("Usage: promote.py devto-post <markdown_file> [--api-key KEY]", file=sys.stderr)
        sys.exit(1)

    md_path = Path(args[0])
    if not md_path.exists():
        print(f"File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    api_key = _api_key(args[1:])
    article = _devto_article(md_path)

    resp = httpx.post(
        "https://dev.to/api/articles",
        headers={"api-key": api_key, "content-type": "application/json"},
        json={"article": article},
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        print(f"Error: dev.to API returned {resp.status_code}", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    url = result.get("url", "")
    print(f"Published: {url}")


def cmd_devto_update(args: list[str]) -> None:
    """Update an existing dev.to article from a Markdown source file."""
    import httpx
    if len(args) < 2:
        print("Usage: promote.py devto-update <article_id> <markdown_file> [--api-key KEY]",
              file=sys.stderr)
        sys.exit(1)

    article_id, path_value = args[0], args[1]
    md_path = Path(path_value)
    if not article_id.isdigit() or not md_path.exists():
        print("Article ID must be numeric and the Markdown file must exist.", file=sys.stderr)
        sys.exit(1)

    resp = httpx.put(
        f"https://dev.to/api/articles/{article_id}",
        headers={"api-key": _api_key(args[2:]), "content-type": "application/json"},
        json={"article": _devto_article(md_path)},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"Error: dev.to API returned {resp.status_code}", file=sys.stderr)
        print(resp.text[:500], file=sys.stderr)
        sys.exit(1)
    print(f"Updated: {resp.json().get('url', '')}")


def cmd_tweet(args: list[str]) -> None:
    """Check tweet length and format."""
    text = " ".join(args) if args else sys.stdin.read().strip()

    # Replace Unicode box-drawing chars with ASCII equivalents
    text = text.replace("└─", "+--").replace("──", "--")

    # Count chars (X uses variable-length for CJK/emoji, but for ASCII it's simple)
    # HN: simple length check
    if len(text) > 280:
        print(f"WARNING: {len(text)} chars (over 280 limit)", file=sys.stderr)
        print(text[:280])
        print("^^^ TRUNCATED to 280 chars ^^^", file=sys.stderr)
    else:
        print(text)
        print(f"[{len(text)} chars / 280]", file=sys.stderr)


def cmd_hn_strip(args: list[str]) -> None:
    """Strip project names and marketing language for HN repost."""
    text = sys.stdin.read()

    # Common patterns to strip
    patterns = [
        r"causetrace",  # project name
        r"github\.com/milkoor/causetrace",  # repo URL
        r"pip install causetrace",  # install command
        r"causetrace\s+(tree|graph|why|replay|doctor)",  # CLI commands
    ]

    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    # Clean up double blanks left by removal
    text = re.sub(r"\n{3,}", "\n\n", text)

    print(text.strip())


def cmd_checklist(args: list[str]) -> None:
    """Generate a promotion checklist for a new version/discovery."""
    version = args[0] if args else "<version>"
    desc = args[1] if len(args) > 1 else ""

    print(f"# Promotion Checklist: {version}")
    if desc:
        print(f"> {desc}")
    print()
    print("## Pre-flight")
    print("- [ ] Update version in `causetrace/__init__.py`")
    print("- [ ] Update `pyproject.toml`")
    print("- [ ] Run all tests: `python -m pytest tests/ -v`")
    print("- [ ] Run demo: `causetrace demo`")
    print("- [ ] Check CI status")
    print()
    print("## Content")
    print("- [ ] Write blog post: `docs/promotion/blog_<topic>.md`")
    print("      Publish: `python3 tools/promote.py devto-post docs/promotion/blog_<topic>.md`")
    print("- [ ] Draft HN post (technical discovery framing, no project name)")
    print("- [ ] Prepare tweet(s) with terminal screenshots")
    print()
    print("## Distribution")
    print("- [ ] Publish blog post to dev.to")
    print("- [ ] Post to Hacker News (wait 24h+ after previous HN post)")
    print("      Title: <technical discovery, no product name>")
    print("      Text: pure insight, link in comments if asked")
    print("- [ ] Tweet 1 (24h after HN)")
    print("- [ ] Tweet 2 (24h after Tweet 1)")
    print("- [ ] Tweet 3 (24h after Tweet 2)")
    print("- [ ] Reddit (r/ClaudeAI, r/programming) — optional, only if high-signal")
    print()
    print("## Follow-up")
    print("- [ ] Monitor HN comments (reply within 24h)")
    print("- [ ] Monitor dev.to comments")
    print("- [ ] Collect trace feedback → schema pressure log")
    print("- [ ] Add blog link to `docs/promotion/` index")

    print()
    print("## Real KPI")
    print("- Complex real traces collected? (500+ event sessions)")
    print("- Schema pressure identified?")
    print("- High-quality developer feedback received?")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "devto-post": cmd_devto_post,
        "devto-update": cmd_devto_update,
        "tweet": cmd_tweet,
        "hn-strip": cmd_hn_strip,
        "checklist": cmd_checklist,
    }

    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(f"Available: {', '.join(commands)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
