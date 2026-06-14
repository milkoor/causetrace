# Future Run Metadata Checklist v0.2.5

Before or immediately after each causetrace session capture, declare the session's metadata. Do not leave sessions to be classified later — retroactive surface is exhausted.

## Rule

Every session entering the corpus MUST carry:

- `data_origin`
- `task_source`
- `intervention_lane` (when known)
- `causetrace_tags` (when applicable)

Unknown historical sessions remain unknown. No inference.

## Checklists by Capture Type

### Direct Native Real Work

Use when running a real task directly — no routing, no workflow plugin, no experiment.

```bash
# Before or after the session, run:
causetrace metadata-set <session_id> \
  --data-origin native \
  --task-source real_work \
  --intervention-lane direct_prompt_native
```

Check:
- [ ] Not a demo or test run
- [ ] No prompt-routing-skill involved
- [ ] No superpowers workflow structure applied
- [ ] No controlled experiment variables

### Routed Prompt Task

Use when `prompt-routing-skill` selected the prompt posture.

```bash
causetrace metadata-set <session_id> \
  --data-origin native \
  --task-source real_work \
  --intervention-lane routed_prompt_intervention
```

Check:
- [ ] `prompt-routing-skill` was explicitly invoked before the task
- [ ] `causetrace_tags` were emitted by the routing skill (verify in session content)
- [ ] Session is tagged `prompt-routing`, `routed-prompt`, `causetrace-prompt-posture`

### Superpowers Workflow

Use when superpowers workflow structure (Skill → Plan → Execute → Verify) was applied.

```bash
causetrace metadata-set <session_id> \
  --data-origin native \
  --task-source real_work \
  --intervention-lane superpowers_workflow_intervention
```

Check:
- [ ] `causetrace_tags` block was emitted in first response or plan output
- [ ] Tags include `superpowers-workflow`, `workflow-intervention`
- [ ] `intervention_evidence_level: strong` (from the emitted block)
- [ ] `workflow_label` is set in the emitted block

### Controlled Prompt Morphology Pilot

Use when running a controlled prompt comparison (A/B/C variants).

```bash
causetrace metadata-set <session_id> \
  --data-origin controlled_benchmark \
  --task-source prompt_morphology_pilot \
  --intervention-lane controlled_prompt_morphology
```

Check:
- [ ] Prompt variant tag is recorded (A, B, or C)
- [ ] Benchmark protocol is followed (same task, different prompt posture)
- [ ] Session is explicitly tagged as pilot/controlled

### External Trajectory

Use when importing external data (third-party logs, external traces).

```bash
causetrace metadata-set <session_id> \
  --data-origin external_trajectory \
  --task-source <external_source_name>
```

Check:
- [ ] Source is documented in `task_source`
- [ ] External origin is explicit (not inferred from content)

### Demo or Test Run

Use when the session is a causetrace demo or a test.

```bash
causetrace metadata-set <session_id> \
  --data-origin native \
  --task-source demo
```

Check:
- [ ] Session is explicitly a demo, not real work
- [ ] Will NOT be counted in native strict lane (no real_work task_source)

## Post-Capture Verification

After declaring metadata, verify:

```bash
# Confirm the session appears in the correct lane
causetrace corpus lane-count

# Confirm intervention_lane is set
causetrace metadata-show <session_id> | grep intervention_lane

# Confirm provenance is recorded
causetrace metadata-show <session_id> --provenance
```

## Non-Rules (Do Not Use)

These are NOT valid classification signals:

- `runtime=claude-code` → native (wrong: runtime does not determine lane)
- `used Skill tool` → superpowers (wrong: Skill alone is not evidence)
- `session ended with exit code 0` → success=true (wrong: clean exit ≠ success)
- `prompt looks structured` → routed (wrong: prompt style is not a marker)
- `data_origin=unknown + runtime known` → direct_prompt_native (wrong: origin is still unknown)

## Historical Sessions

Sessions captured before this checklist was in place (data_origin=unknown) remain unlabeled unless:

- Explicit source evidence is found (e.g., the original task description, project context, or tool logs confirm the capture type)
- A human annotates the session with high confidence

Do not bulk-classify old sessions. The 879 unlabeled sessions are evidence gaps, not technical debt.
