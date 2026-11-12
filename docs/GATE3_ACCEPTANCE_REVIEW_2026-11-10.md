# Gate 3 Acceptance Criteria Review
# 2026-11-10

## Commits under review

82c98dd - Correction propagation v0.1 (15 tests)
b9e6b1f - Correction-ledger binding v0.1 (7 tests)
11cd457 - Correction-ledger persistence v0.1 (4 tests)

Aggregate: 26 passed.

## Acceptance criteria

1. Submitted with source evidence - NOT MET
2. Origin and affected components identifiable - PARTIAL
3. Agent cannot approve own authority expansion - NOT MET
4. Corrections can be reviewed independently - NOT MET
5. Approved corrections propagate to designated agents - NOT MET
6. Regression tests establish behavioral improvement - NOT MET
7. Rejected corrections remain in evidence history - NOT MET
8. Human authorization enforceable at boundaries - NOT MET

Score: 0 fully met, 1 partial, 7 not addressed.

## What the 26 tests prove

The correction mechanism works on a synthetic graph: register a
correction, compute material descendants, require terminal disposition,
verify closure, record in a hash-chained ledger, detect six classes of
tampering including post-reload tampering.

Maturity of mechanism: M3 VERIFIED (internal tests).

## What the 26 tests do not prove

- Any correction refers to a real artifact
- Any node name corresponds to a registered entity
- Any reviewer saw the correction, or was independent of the submitter
- Any agent received or acted on it
- Any human authorized it
- Any behavior changed
- Rejected corrections are durable or immutable

## Field presence is not property satisfaction

1. reviewed_by does not prove independent review unless a
   separation-of-duty check exists.
2. propagation_targets does not prove delivery; a receipt does.
3. REJECTED does not prove immutable history unless the ledger
   chain covers the rejection event.

## Split recommendation

Gate 3b - structural integration. No external systems required:
evidence reference resolution, artifact identity resolution, reviewer
identity plus separation-of-duty check, disposition states written to
the ledger event, propagation targets resolved against a registry.

Gate 3c - behavioral integration. Requires systems that do not yet
exist in executable form: authorization enforcement at the dispatcher
boundary, delivery acknowledgment, regression baseline measurement,
human authorization in the correction flow.

## Status

- Gate 3 mechanism: CLOSED (26/26)
- Gate 3 acceptance criteria: OPEN (0/8 met, 1/8 partial)
- Gate 3b: SPECIFICATION
- Gate 3c: SPECIFICATION
- Gate 4: BLOCKED pending 3b decision

## Principle

A mechanism can be verified without its institutional integration being
verified. The 26 tests establish the former. The eight criteria ask for
the latter.
