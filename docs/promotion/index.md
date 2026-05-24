# Promotion Index

Track promotion activities. Add entries when new content is published.

## Published

| Date | Type | Title/Description | URL | Status |
|------|------|-------------------|-----|--------|
| 2026-05-14 | HN | Coding agents produce causal DAGs, not timelines | https://news.ycombinator.com/item?id=48132377 | Flagged, repost pending |
| 2026-05-14 | Blog | Coding agents produce causal DAGs, not logs | https://dev.to/milkoor/coding-agents-produce-causal-dags-not-logs-ne6 | Live |
| 2026-05-14 | Blog | Reverse engineering Codex CLI rollout traces | https://dev.to/milkoor/reverse-engineering-codex-cli-rollout-traces-3b9b | Live |
| 2026-05-14 | X/Twitter | Tweet 1: Causal tree vs flat log | — | Live |

## Pending

| Item | Status | Ready when |
|------|--------|------------|
| HN repost (cleaned) | Content ready in `docs/promotion/hn_final.txt` | Wait 24h+ since original post |
| X/Twitter Tweet 2 | Content ready in `docs/promotion/twitter.md` | 24h after Tweet 1 |
| X/Twitter Tweet 3 | Content ready in `docs/promotion/twitter.md` | 24h after Tweet 2 |
| Blog 3: Claude Code hooks parent_event_id bug | Outline in `docs/promotion/blog_posts.md` | Next major cycle |
| Reddit post | Not started | Optional, only if high-signal |

## Templates

- `docs/promotion/hn_final.txt` — Clean HN post (no project name, no GitHub link)
- `docs/promotion/twitter.md` — Tweet drafts with screenshot suggestions
- `docs/promotion/blog_causal_dags.md` — Blog post 1
- `docs/promotion/blog_codex_reverse_engineering.md` — Blog post 2
- `docs/promotion/blog_posts.md` — Blog outlines for future posts
- `tools/promote.py` — CLI tools for dev.to posting, tweet formatting, HN stripping
