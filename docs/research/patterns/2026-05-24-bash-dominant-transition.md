# Pattern: bash-dominant-transition

## Sessions

| Session | Agent | Events | Bash→Bash | Bash % |
|---------|-------|--------|-----------|--------|
| 1a00157a | claude-code | 1499 | 648 | 57% (856/1499) |
| 270e9651 | claude-code | 1420 | 339 | 37% (528/1420) |
| codex_latest | codex-cli | 672 | 291 | 63% (420/672) |

## Raw Metrics (Claude A)

tool_freq: Bash×856, Read×408, Edit×178, Agent×22, TaskUpdate×7
repeated_paths (>=2 occurrences):
- Bash → Bash: ×648
- Bash → Bash → Bash: ×525
- Bash → Bash → Bash → Bash: ×444
- Bash → Bash → Bash → Bash → Bash: ×383

The n-gram frequency decays slowly: 648 → 525 → 444 → 383. This means Bash→Bash is not a 2-event flicker — it's sustained Bash chains of 5+ events.

## Raw Metrics (Claude B)

tool_freq: Bash×528, Thinking×303, Edit×203, Read×151, Response×114
repeated_paths:
- Bash → Bash: ×339
- Bash → Bash → Bash: ×185
- Bash → Bash → Bash → Bash: ×129
- Bash → Bash → Bash → Bash → Bash: ×88

Same pattern, but weaker decay (339 → 185 → 129 → 88). Bash chains are shorter here. This session also has Thinking→Response (×110) and Thinking→Bash (×88), suggesting reasoning steps interleaved with Bash that may break the chaining.

## Raw Metrics (Codex CLI)

tool_freq: Bash×420, write_stdin×151, Edit×70
repeated_paths:
- Bash → Bash: ×291
- Bash → Bash → Bash: ×217
- Bash → Bash → Bash → Bash: ×171
- Bash → Bash → Bash → Bash → Bash: ×136

Even stronger decay (291 → 217 → 171 → 136): Codex CLI has the longest sustained Bash chains.

## Observation

Bash→Bash is the single most common transition across all three sessions. It is not a short artifact — long chains of 5+ consecutive Bash events exist in every session.

Possible explanations for what drives Bash→Bash:
1. **Shell batching**: a single logical "run tests" step produces multiple Bash events (install, compile, run, parse output)
2. **Iterative repair**: run → fail → run different command → fail → run again
3. **Verification chaining**: run test → run coverage → run lint → run format check
4. **Tool routing**: the agent uses Bash as a meta-tool for everything not covered by native tools

## Open Questions

- Does Bash→Bash correlate with failure states (retry loops)?
- Can we distinguish "productive Bash chain" from "oscillating Bash chain" without examining tool_output?
- Is Bash→Bash a Codex/DeepSeek-specific artifact (proxy loops)?
- Would first-class test/compile/lint semantics reduce Bash chaining?
- Is sustained Bash chaining a signature of "agent doesn't know when to stop trying"?
- Does the presence of Thinking events BETWEEN Bash events (Claude B: 129 Bash→Thinking) indicate different agent behavior than contiguous Bash→Bash (Claude A)?

## Window Drift (Claude B: 270e9651)

Count-based windows (size=300, overlap=100) over 1420 events:

| Window | Events | Roots | Depth | Top Transition |
|--------|--------|-------|-------|----------------|
| W0     | 300    | 89    | 211   | Bash→Bash: 64  |
| W1     | 300    | 87    | 0     | Bash→Bash: 37  |
| W2     | 300    | 76    | 7     | Bash→Bash: 48  |
| W3     | 300    | 22    | 57    | Bash→Bash: 43  |
| W4     | 300    | 0     | 0     | Bash→Bash: 80  |
| W5     | 300    | 0     | 0     | Bash→Bash: 123 |
| W6     | 220    | 0     | 0     | Bash→Bash: 71  |

Observation recorded from the original analysis run: roots decrease (89→0)
across the session as Bash→Bash concentration increases (64→123). Depth
regeneration in W3 (57) after zero-depth W1-W2 suggested a window-boundary
effect.

Correction (2026-05-24): `analysis.py` now treats parent references outside a
loaded window as local-root boundaries. The zero-root/zero-depth values above
reflect the pre-fix implementation and should be recomputed before drawing
topology conclusions; the transition counts remain historical observations.
