# Promotion Index

Track promotion activities. Add entries when new content is published.

## Published

| Date | Type | Title/Description | URL | Status |
|------|------|-------------------|-----|--------|
| 2026-05-14 | HN | Coding agents produce causal DAGs, not timelines | https://news.ycombinator.com/item?id=48132377 | Dead/flagged; do not link |
| 2026-05-14 | Blog | Coding agents produce causal DAGs, not logs | https://dev.to/milkoor/coding-agents-produce-causal-dags-not-logs-ne6 | Live |
| 2026-05-14 | Blog | Reverse engineering Codex CLI rollout traces | https://dev.to/milkoor/reverse-engineering-codex-cli-rollout-traces-3b9b | Live |
| 2026-05-14 | X/Twitter | Tweet 1: Causal tree vs flat log | URL not recorded | Publication unverified |
| 2026-05-24 | Release | v0.1.3 - Runnable onboarding for agent causal tracing | https://github.com/milkoor/causetrace/releases/tag/v0.1.3 | GitHub live; PyPI pending publisher registration |

## Pending

| Item | Status | Ready when |
|------|--------|------------|
| v0.1.3 release announcement | Content ready in `docs/promotion/release_v0.1.3.md` | After PyPI package is live |
| New Show HN post (demo-focused) | Content ready in `docs/promotion/show_hn_v0.1.3.md` | After v0.1.3 demo is live |
| X/Twitter Tweet 2 | Content ready in `docs/promotion/twitter.md` | 24h after Tweet 1 |
| X/Twitter Tweet 3 | Content ready in `docs/promotion/twitter.md` | 24h after Tweet 2 |
| Blog 3: Claude Code hooks parent_event_id bug | Outline in `docs/promotion/blog_posts.md` | Next major cycle |
| Existing dev.to updates | Source corrected; live update requires `DEVTO_API_KEY` | After v0.1.3 release |
| Reddit post | Drafts ready | After v0.1.3 release and demo image |
| PyPI `0.1.3` upload | Workflow built artifacts; OIDC returned `invalid-publisher` | Register Trusted Publisher, then rerun workflow |

## Templates

- `docs/promotion/hn_final.txt` — Clean HN post (no project name, no GitHub link)
- `docs/promotion/show_hn_v0.1.3.md` — New runnable Show HN draft
- `docs/promotion/twitter.md` — Tweet drafts with screenshot suggestions
- `docs/promotion/blog_causal_dags.md` — Blog post 1
- `docs/promotion/blog_codex_reverse_engineering.md` — Blog post 2
- `docs/promotion/blog_posts.md` — Blog outlines for future posts
- `docs/promotion/release_v0.1.3.md` — Release announcement copy and distribution checklist
- `tools/promote.py` — CLI tools for dev.to posting, tweet formatting, HN stripping
