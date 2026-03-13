# Correctness (Extended) Checklist

## Core Invariants and Contracts

- Core invariants are explicitly documented near the code and tests that enforce them.
- Preconditions are validated before executing core logic at key boundaries.
- Postconditions are checked after mutation points at key boundaries.
- Cross-component invariants are validated (for example SQL layer vs storage layer).
- Assertions guard impossible or forbidden states.
- Determinism is preserved (`same input + same snapshot -> same output`).
- Idempotency is preserved for retries and duplicate requests.
- Crash-consistency invariants are preserved.
- No invariant relies on timing assumptions alone.
- Invariant checks exist in tests, not only comments.
- Regression tests cover previously violated invariants.

## Business Logic

- Behavior matches stated requirements and acceptance criteria.
- Domain rules are enforced in the right layer (not bypassable by alternate paths).
- Feature-flag ON/OFF behavior is both correct.
- Compatibility breaks are explicitly gated, versioned, or intentionally documented.

## Control Flow and Branches

- Every `if`/`else` branch has valid behavior (including "impossible" branches).
- Early returns do not skip required cleanup or state updates.
- Loop termination conditions are correct (no off-by-one or infinite loops).
- `switch`/`case` has no missing case and safe default handling.
- Error, timeout, and cancellation branches are functionally correct, not just logged.

## Input and Output Semantics

- `null`/empty/zero/`false` inputs are intentionally handled.
- Boundary values are explicitly handled (min/max length, min/max numeric range).
- Invalid inputs fail safely with correct and stable error types/messages.
- Output schema and field meanings remain consistent with the contract.
- Output ordering is deterministic where callers depend on it.

## Positional Data and Shape Correctness

- Dimension/index order is treated as an invariant and covered by tests.
- Dynamic index access is bounds-safe across success, error, and retry paths.
- Shape assumptions (rank, rectangular vs ragged, non-empty constraints) are validated before traversal.
- Conversions between positional arrays and named structs preserve ordering and units explicitly.
- Malformed positional payloads fail fast with stable, actionable errors.
- Refactors that add/remove fields cannot silently shift positional meaning; migration is explicit and tested.
- Repeated same-typed primitive arguments use typed wrappers or structs to prevent parameter-order bugs.
- Edge-case tests cover first/last index, empty container, singleton container, and max-size boundaries.

## SQL Language and Type Semantics

- SQL dialect behavior matches the documented contract.
- `NULL` semantics are correct for predicates and aggregates.
- Type coercion and implicit casts are deterministic.
- Decimal/float overflow and rounding rules are consistent.
- Collation and case-sensitivity behavior is correct.
- Timezone and timestamp precision semantics are unambiguous.
- `ORDER BY` stability/tie behavior is intentional.
- `GROUP BY`, `HAVING`, and window semantics match engine rules.
- Semantic SQL error codes/messages are stable for equivalent cases.

## Parser and Binder Correctness

- Grammar changes avoid shift/reduce ambiguity.
- New keywords/reserved words do not unexpectedly break existing SQL.
- Parser rejects malformed input early and safely.
- AST normalization preserves intent and source positions where needed.
- Name resolution handles aliases, CTEs, and shadowing correctly.
- Column/table ambiguity is detected with actionable errors.
- Parameter marker binding is type-safe and deterministic.
- Privilege-sensitive objects resolve in the correct namespace.
- Parser/binder fuzz tests cover malformed and adversarial input.
- Syntax errors remain clear, consistent, and non-leaky.

## Optimizer and Planning Correctness

- Logical rewrites are semantics-preserving.
- Predicate pushdown remains correct with `NULL` and outer-join semantics.
- Join reordering respects non-associative edge cases.
- Cost-model inputs are bounded and validated.
- Cardinality estimation handles skew and stale stats safely.
- Plan-cache keys include all semantic discriminators.
- Hint precedence and fallback behavior are deterministic.
- Partition-pruning rules are correct for boundary values.
- Worst-case plan regressions are benchmarked.
- Plan-stability policy (if any) is upheld.

## Execution Engine Correctness

- Operator input/output schema contracts are explicit.
- Row-count and nullability propagation are correct.
- Ordering guarantees are preserved or intentionally dropped.
- Vectorized and row-mode execution return equivalent results.
- Spill-to-disk path matches in-memory semantics.
- Short-circuit paths do not skip required side effects.
- Cancellation/timeouts abort safely and release resources.
- Runtime filters and late materialization preserve correctness.
- Resource cleanup occurs on both success and failure paths.
- Operator-level errors map to stable SQL errors.

## State and Data Integrity

- State transitions are legal (no invalid transition path).
- Partial updates cannot leave data in inconsistent state.
- Transactions include all related writes that must be atomic.
- Read-after-write assumptions match the storage consistency model.
- Defaults are explicit and do not silently change existing behavior.
- Shared objects/collections are not mutated in hidden ways that break callers.

## DDL and Schema Evolution

- DDL metadata updates are atomic and transactional where required.
- Online-DDL and blocking-DDL paths are both validated.
- Backfill strategy remains safe under concurrent writes.
- Defaults/generated columns evaluate consistently across versions.
- Constraint validation phase behavior is correct (`NOT VALID`, deferred validate, etc.).
- Schema-version transitions are monotonic.
- Mixed-version cluster behavior is tested.
- Failed DDL leaves no orphan metadata or residual state.
- Rename/drop/recreate edge cases are covered.
- Rollback of partially applied DDL is safe.

## Index Correctness

- Key encoding/decoding is canonical and version-safe.
- Unique-index enforcement is transactionally correct.
- Prefix/partial/functional index semantics are correct.
- Index maintenance on insert/update/delete is atomic with row changes.
- Covering-index logic avoids stale or missing columns.
- Invisible/disabled index behavior is explicit and tested.
- Rebuild/reorg paths preserve availability and correctness.
- Index-corruption detection and reporting are present.
- Index-scan MVCC visibility checks are correct.
- Optimizer index-selection changes include performance evidence.

## Transaction Correctness

- Transaction state machine (`BEGIN`/`COMMIT`/`ROLLBACK`) is valid.
- Atomicity is preserved across all write paths.
- Isolation-level guarantees are preserved and tested.
- Durability is upheld under crash/power-loss scenarios.
- Savepoint semantics are correct.
- Autocommit and implicit-transaction behavior are consistent.
- Write-write/read-write conflict behavior matches the isolation contract.
- Retryable vs non-retryable error classes are correct.
- Long-running transactions do not break GC/vacuum assumptions.
- Transaction-timeout and lock-timeout interactions are sane.

## Locking, MVCC, and Concurrency

- Shared mutable state is synchronized correctly.
- Race-prone shared structures are protected correctly.
- Check-then-act races are eliminated.
- Lock acquisition order avoids unintended deadlocks.
- Deadlock detection or timeout path is reliable.
- Lock/latch leaks are impossible on error paths.
- Lock granularity is justified for contention profile.
- Starvation/fairness behavior is acceptable.
- MVCC snapshot visibility rules are correct.
- Phantom protection matches the configured isolation level.
- Metadata locks and data locks interact safely.
- Retry loops are bounded and instrumented.

## Numerical, Time, and Locale

- Integer overflow/underflow and precision loss are considered.
- Floating-point comparisons use safe tolerance where needed.
- Currency/decimal math avoids binary-float errors where inappropriate.
- Timezone handling is explicit (store/compare/render consistently).
- DST/leap-day/end-of-month edge cases are correct.
- String/case/Unicode normalization behavior is intentional.

## External Interaction Correctness

- Assumptions about external API responses are validated.
- Backward compatibility with older clients/servers is preserved (or intentionally broken with contract updates).
- Pagination/token handling returns complete and non-duplicated results.
- Cache key/value semantics are correct (no stale/wrong-key reads).
- Failure of downstream dependencies produces correct fallback behavior.

## Common Regression Traps

- Refactors preserve side effects relied on by callers.
- Renamed fields/params map correctly everywhere.
- Default-config changes do not alter behavior unexpectedly.
- Legacy and new paths produce equivalent results where required.
- Edge-case behavior from previous bugfixes remains intact.
