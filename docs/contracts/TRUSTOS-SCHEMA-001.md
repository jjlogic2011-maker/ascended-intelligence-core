# TRUSTOS-SCHEMA-001 — Four-Record Contract Conformance

**Status:** SPECIFICATION + LOCAL STAGED TESTS ONLY; no GitHub commit, CI, or deployment evidence for this candidate.

**Parent baseline:** `e4e28bcfaf7220b712e9fa9b9ab5fd4fc8a91fb6` (October 28, 2026).

## Contract mapping

| Source of truth | Metadata-only parser |
|---|---|
| `schemas/authority_request.schema.json` | `security.precept_authority_request.parse_precept_authority_request` |
| `schemas/claim_record.schema.json` | `security.claim_record.parse_claim_record` |
| `schemas/event.schema.json` | `security.precept_witness_event.parse_precept_witness_event` |
| `schemas/memory_beacon.schema.json` | `security.memory_beacon.parse_memory_beacon` |

## Explicit compatibility policy and breaking changes

1. Unknown properties must be **rejected** at the JSON Schema and Python ingestion boundaries. This adds `additionalProperties: false` to ClaimRecord and MemoryBeacon. The two upstream schemas **previously allowed unknown fields**, so this is a breaking validation policy decision, not a neutral refactor. Review existing stored records before promotion.
2. MemoryBeacon `date` requires RFC3339 full-date format via JSON Schema `format: date` and an enabled format checker. **Before this change the schema required only a string.** This intentionally tightens the contract to match the existing parser.
3. All six optional MemoryBeacon properties are accepted and typed: `participants`, `emotional_tone`, `difficulty_burden`, `lesson_learned`, `future_recall_cues`, `cross_ledger_link`.
4. Date-time format checking is enabled for AuthorityRequest and WitnessEvent, including real calendar validity. Schema files are loaded from the repository's `schemas/` directory. Deployments packaging Python modules must include these schema assets.
5. Runtime validation uses `jsonschema[format]` / Draft 2020-12. On Android Termux, preflight the runtime dependency installation before adopting this implementation; native dependency build availability has **not been verified on the target device**.
6. Parsers accept only finite JSON-compatible data and return isolated copies. No claim is automatically promoted to verified; no AuthorityRequest `ALLOW` value is treated as a SHAPE grant; no WitnessEvent hash is authenticated by parsing.
7. Existing HTTP endpoints, the SHAPE state machine, Living Ledger, and ExecutionDispatcher are not modified by this work package.

## Acceptance requirements

- Exact-base SHA check before staging changes; no direct push to main.
- Run four-contract parity suite using Draft 2020-12 and `FormatChecker`.
- Run existing targeted parser tests, full pytest, TABS, and import/startup CI checks on a single commit.
- Record results and versions of Python, jsonschema, and other dependencies.
- Independently review the two explicit schema-breaking changes and existing stored-data migration behavior.
- PR + human review before merge; do not claim production conformance until independently reproduced.

## Evidence tiers

- **VERIFIED:** source schema properties and original file SHA values checked against the specified GitHub commit.
- **SPECIFICATION:** explicit unknown-key policy and date format decision.
- **LOCAL TEST:** parity suite executed on staged files under the model's isolated Python container.
- **ROADMAP:** same-commit GitHub CI, Termux validation, data migration assurance, independent reproduction.
