---
name: gitnexus-refactoring
description: "Use when the user wants to rename, extract, split, move, or restructure code safely. Examples: \"Rename this function\", \"Extract this into a module\", \"Refactor this class\", \"Move this to a separate file\""
---

# Refactoring with GitNexus

## When to Use

- "Rename this function safely"
- "Extract this into a module"
- "Split this service"
- "Move this to a new file"
- Any task involving renaming, extracting, splitting, or restructuring code

## Workflow

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → Map all dependents
2. gitnexus_query({query: "X"})                            → Find execution flows involving X
3. gitnexus_context({name: "X"})                           → See all incoming/outgoing refs
4. Plan update order: interfaces → implementations → callers → tests
```

> If "Index is stale" → run `npx gitnexus analyze` in terminal.

## Checklists

### Rename Symbol

```
- [ ] gitnexus_context({name: "oldName"}) — identify references and call sites
- [ ] gitnexus_impact({target: "oldName", direction: "upstream"}) — assess callers
- [ ] Edit definitions and verified references in scope
- [ ] Inspect `git diff --stat` and search for remaining old-name references
- [ ] Run tests for affected processes
```

### Extract Module

```
- [ ] gitnexus_context({name: target}) — see all incoming/outgoing refs
- [ ] gitnexus_impact({target, direction: "upstream"}) — find all external callers
- [ ] Define new module interface
- [ ] Extract code, update imports
- [ ] Inspect `git diff --stat` and run relevant tests
- [ ] Run tests for affected processes
```

### Split Function/Service

```
- [ ] gitnexus_context({name: target}) — understand all callees
- [ ] Group callees by responsibility
- [ ] gitnexus_impact({target, direction: "upstream"}) — map callers to update
- [ ] Create new functions/services
- [ ] Update callers
- [ ] Inspect `git diff --stat` and run relevant tests
- [ ] Run tests for affected processes
```

## Tools

**gitnexus_context** — enumerate references before a rename:

```
gitnexus_context({name: "validateUser"})
→ Incoming callers and outgoing dependencies to update deliberately
```

**gitnexus_impact** — map all dependents first:

```
gitnexus_impact({target: "validateUser", direction: "upstream"})
→ d=1: loginHandler, apiMiddleware, testUtils
→ Affected Processes: LoginFlow, TokenRefresh
```

**Diff and tests** — verify your changes after refactoring:

```
git diff --stat
pytest tests/ -v
```

**gitnexus_cypher** — custom reference queries:

```cypher
MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "validateUser"})
RETURN caller.name, caller.filePath ORDER BY caller.filePath
```

## Risk Rules

| Risk Factor         | Mitigation                                |
| ------------------- | ----------------------------------------- |
| Many callers (>5)   | Use `context` and `impact` before editing |
| Cross-area refs     | Inspect diff and test all affected paths  |
| String/dynamic refs | gitnexus_query to find them               |
| External/public API | Version and deprecate properly            |

## Example: Rename `validateUser` to `authenticateUser`

```
1. gitnexus_context({name: "validateUser"})
   → Identify definition, callers, tests, and dynamic-reference risk

2. gitnexus_impact({target: "validateUser", direction: "upstream"})
   → Affected: LoginFlow, TokenRefresh

3. Rename the definition and verified callers; search for remaining references.

4. Inspect `git diff --stat` and run tests for affected flows.
```
