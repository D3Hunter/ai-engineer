# Correctness Split Mapping (Dedup-First)

Source checklist: legacy monolithic correctness checklist (captured before split)

Legend:
- `QPE`: `review-correctness-query-planner-execution`
- `SST`: `review-correctness-state-schema-transaction`
- `Runtime`: `review-runtime-reliability-performance`
- `Compat`: `review-upgrade-compatibility-and-test-determinism`
- `Dropped`: removed as low-yield overlap after dedup

## Section Mapping

| Legacy section | Ownership | Notes |
| --- | --- | --- |
| Core Invariants and Contracts | Split (`QPE` + `SST`), with runtime overlap removed | Query/result invariants and I/O contract invariants go to `QPE`; state-transition and atomicity invariants go to `SST`; timing-only assumptions and crash-lifecycle mechanics move to `Runtime`. |
| Business Logic | `QPE` | Domain rules and requirement alignment stay in behavioral correctness. |
| Control Flow and Branches | `QPE` | Branch/early-return/loop/switch correctness is execution-path semantics. |
| Input and Output Semantics | `QPE` | Boundary/null/error/output-contract checks stay with behavioral query-path correctness. |
| Positional Data and Shape Correctness | `QPE` | Positional/shape/index semantics remain in planner/execution correctness. |
| SQL Language and Type Semantics | `QPE` | SQL semantic behavior remains in planner/execution track. |
| Parser and Binder Correctness | `QPE` | Grammar, name resolution, binding determinism remain in planner/execution track. |
| Optimizer and Planning Correctness | `QPE` (semantic only) | Semantics-preserving rewrites and plan-key correctness stay; benchmark-only items move to `Runtime`. |
| Execution Engine Correctness | `QPE` | Operator schema/nullability/order/semantic parity stay in planner/execution track. |
| State and Data Integrity | `SST` | State transitions, atomic writes, consistency-model assumptions stay in state/schema/transaction track. |
| DDL and Schema Evolution | `SST` (semantic/integrity), `Compat` (mixed-version policy), `Runtime` (online operational lifecycle) | Semantic correctness and integrity remain in `SST`; mixed-version compatibility checks move to `Compat`; online backfill operational resilience checks move to `Runtime`. |
| Index Correctness | `SST` (semantic/integrity), `Runtime` (performance/operational) | Key encoding, uniqueness semantics, and atomic maintenance stay in `SST`; rebuild availability/perf evidence moves to `Runtime`. |
| Transaction Correctness | `SST` (semantic/integrity), `Runtime` (lock-timeout lifecycle) | State-machine/isolation/atomicity semantics stay in `SST`; lock-timeout lifecycle and long-running operational pressure checks move to `Runtime`. |
| Locking, MVCC, and Concurrency | `Runtime` | Entire section moved out of correctness split per ownership decision. |
| Numerical, Time, and Locale | `SST` | Numeric/time/locale data correctness stays with state/integrity track. |
| External Interaction Correctness | `Runtime` + `Compat` | Failure fallback semantics move to `Runtime`; backward/forward contract compatibility moves to `Compat`. |
| Common Regression Traps | Split (`QPE` + `SST`), with overlap removed | Behavior-preservation traps map to `QPE`; state/default/legacy-equivalence traps map to `SST`; purely test-structure overlap dropped. |

## Explicit Dropped Low-Yield Overlap

- "Invariant checks exist in tests, not only comments."  
  Dropped from correctness split; test-design quality is already covered in compatibility/determinism review.
- "Regression tests cover previously violated invariants."  
  Dropped from correctness split; deterministic validation quality is handled by compatibility/determinism review.
- "Optimizer index-selection changes include performance evidence."  
  Moved to runtime performance review, not retained in correctness checklists.

## Checklist Balance Snapshot

- `QPE` checklist actionable items: `38`
- `SST` checklist actionable items: `33`
- Relative difference: `5 / 35.5 = 14.1%` (within `<= 15%` target)
