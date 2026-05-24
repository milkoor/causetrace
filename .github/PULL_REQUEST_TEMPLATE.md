## Summary

Describe the behavior being changed and the runtime or command it affects.

## Causal / Schema Impact

- Does this change event linkage, topology analysis, schema fields, or ingestion fidelity?
- For a new or changed bridge/parser, include a sanitized real-trace example.

## Validation

- [ ] `python -m pytest tests/ -v`
- [ ] `python demo/run_demo.py` where integration behavior changes
- [ ] No prompts, credentials, private paths, or sensitive tool output are included

## Related Issues

Link issues or schema pressure notes where applicable.
