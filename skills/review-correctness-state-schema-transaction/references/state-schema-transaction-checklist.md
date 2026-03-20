# Correctness Checklist (State/Schema/Transaction)

## Execution Protocol (Mandatory)

- Complete every section in this checklist.
- If a section is not relevant, mark it `N/A` with a concrete reason tied to the diff.
- Do not conclude "no findings" until each section is passed or explicitly `N/A` with rationale.

## Out Of Scope (Route Elsewhere)

- Locking/MVCC/concurrency lifecycle ownership, deadlock timeout mechanics, and retry-loop lifecycle -> `review-runtime-reliability-performance`.
- Upgrade/downgrade protocol compatibility, mixed-version contract policy, and fallback compatibility behavior -> `review-upgrade-compatibility-and-test-determinism`.

## Evidence Gate (Required For Each Finding)

Before filing a finding, capture at least one objective signal:
- Illegal state transition or partial-update inconsistency risk.
- Atomicity/isolation guarantee mismatch in changed transaction or mutation paths.
- Schema/index semantic mismatch causing incorrect read/write outcomes.
- Concrete state-oriented regression scenario (`state/input -> incorrect persisted/observed outcome`).

## Severity Mapping

- `Blocker`: high-confidence data-integrity break, non-recoverable incorrect persisted state, or major transactional correctness break.
- `Major`: high-confidence state/schema/transaction correctness risk with meaningful impact.
- `Minor`: localized integrity/correctness gap with limited blast radius.
- `Info` / `Nit`: low-risk clarification or polish.

## Checklist

### 1) State and Data Integrity

- Changed state transitions remain legal and enforce invariants.
- Partial updates cannot leave persisted state internally inconsistent.
- Required multi-entity writes remain atomic as designed.
- Read-after-write assumptions still match the storage consistency model.
- Defaults are explicit and do not silently alter persisted behavior.
- Shared mutable structures are not changed in hidden ways that violate caller assumptions.

### 2) DDL and Schema Correctness (Semantic/Integrity)

- DDL metadata changes remain atomic/transactional where required.
- Constraint lifecycle semantics (`NOT VALID`, deferred validation, phased validate) remain correct.
- Failed DDL paths do not leave orphan metadata or residual partial state.
- Rename/drop/recreate edge cases preserve intended object identity semantics.
- Rollback semantics for partially applied DDL remain safe.
- Schema-version progression logic remains monotonic where required by local invariants.
- Default/generated column semantic evaluation remains stable across restart/reload boundaries.

### 3) Index Correctness (Semantic/Integrity)

- Key encoding/decoding remains canonical and version-safe in touched paths.
- Unique index semantics remain transactionally correct.
- Prefix/partial/functional index semantics remain logically correct.
- Index maintenance on insert/update/delete remains atomic with row mutations.
- Covering-index behavior does not produce stale/missing semantic values.

### 4) Transaction Correctness (Semantic/Integrity)

- Transaction state-machine transitions (`BEGIN`/`COMMIT`/`ROLLBACK`) remain valid.
- Atomicity guarantees hold across all changed write paths.
- Isolation-level guarantees remain preserved for changed operations.
- Savepoint and autocommit semantics remain consistent with contract.
- Retryable vs non-retryable error classification remains semantically correct.
- Durability assumptions expressed by changed logic remain consistent with persistence model.

### 5) Numerical, Time, and Locale Correctness

- Integer range/overflow/underflow handling remains correct.
- Floating-point comparison tolerance is intentional where required.
- Decimal/currency calculations avoid unintended binary-float errors.
- Timezone/DST/leap-day/end-of-month behavior remains explicit and correct.
- String/case/Unicode normalization behavior remains intentional and stable.

### 6) Regression Traps (State-Preservation)

- State-oriented side effects relied on by callers are preserved.
- Default/config changes do not silently alter persisted behavior unexpectedly.
- Legacy/new state paths remain equivalent where equivalence is required.
- Prior state-integrity bugfix scenarios touched by this diff remain preserved.

## Output Handoff Rules

- Emit one finding per issue.
- Include these fields: `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
- Keep scope concrete (`path:line`, module/state boundary, transaction phase, or scenario).
- After checklist completion, hand findings to `review-output-format` and write the final JSON payload.
