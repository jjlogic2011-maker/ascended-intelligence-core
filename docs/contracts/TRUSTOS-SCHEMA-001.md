# TRUSTOS-SCHEMA-001 — Record contract policy

**Policy: strict closed world**

For typed governance records (AuthorityRequest, ClaimRecord, WitnessEvent, MemoryBeacon):

1. **Required** fields must be present and type-valid.
2. **Optional** fields may be omitted; if present they must match the schema types.
3. **Unknown** fields are **rejected** (fail closed).
4. JSON Schema and Python `parse_*` must accept and reject the **same** records.

### What “strict closed world” means

Imagine a form with labeled boxes only. You may leave optional boxes empty. You may not write in the margins or invent new boxes. Both the paper form (JSON Schema) and the clerk (Python parser) enforce the same rule.

Opposite (not used here): an **open world** that silently ignores extra fields — weaker for governance evidence.

### Implementation notes

- Schemas SHOULD set `"additionalProperties": false`.
- Parsers use an explicit `_ALLOWED` key set equal to `required ∪ optional` properties.
- Prefer Draft 2020-12 validators in CI when `jsonschema` is available; unit tests enforce parser behavior always.

### Status

| Record | Schema closed | Parser closed | Optionals aligned |
|--------|---------------|---------------|-------------------|
| MemoryBeacon | yes (this change) | yes | yes |
| ClaimRecord | yes (this change) | yes | yes |
| AuthorityRequest | already `additionalProperties: false` | verify separately | — |
| WitnessEvent | verify separately | verify separately | — |
