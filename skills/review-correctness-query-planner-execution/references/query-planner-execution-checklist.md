# Correctness Checklist (Query/Planner/Execution)

## Execution Protocol (Mandatory)

- Complete every section in this checklist.
- If a section does not apply, mark it `N/A` with a concrete reason tied to the actual diff.
- Do not conclude "no findings" until every section is either passed or `N/A` with evidence.

## Out Of Scope (Route Elsewhere)

- Locking, MVCC, thread/concurrency lifecycle, retry-loop lifecycle ownership -> `review-runtime-reliability-performance`.
- External API compatibility, fallback contract compatibility, mixed-version/upgrade compatibility -> `review-upgrade-compatibility-and-test-determinism` or runtime reviewer.

## Evidence Gate (Required For Each Finding)

Before filing a finding, capture at least one objective signal:
- Requirement/invariant contradiction in changed code paths.
- Edge-case branch that produces incorrect behavior or contract output.
- Semantic mismatch between parser/binder/planner/executor stages.
- Concrete regression scenario (`input/condition -> incorrect outcome`).

## Severity Mapping

- `Blocker`: high-confidence incorrect results, semantic corruption, or major contract break.
- `Major`: high-confidence correctness risk with meaningful user or operational impact.
- `Minor`: localized correctness gap with limited blast radius.
- `Info` / `Nit`: low-risk clarification or polish.

## Checklist

### 1) Behavioral Contracts and Domain Logic

- Changed behavior still matches stated requirements and acceptance criteria.
- Domain rules are enforced in the authoritative layer and cannot be bypassed by alternate paths.
- Feature-flag ON/OFF behavior remains logically consistent.
- Determinism expectation is preserved (`same logical input + same snapshot -> same logical output`).

### 2) Control Flow, Input Validation, and Output Semantics

- Every changed branch (`if/else/switch`) has valid behavior, including defaults and error branches.
- Early returns do not skip required semantic checks or required state handoff steps.
- Loop boundaries and termination conditions are correct (no off-by-one/infinite path).
- Boundary inputs (`null`, empty, zero, false, min/max) are intentionally handled.
- Output schema, field meaning, and ordering semantics remain contract-consistent.

### 3) Positional Data and Shape Semantics

- Index and dimension ordering are explicit and preserved through all changed paths.
- Dynamic index access is bounds-safe in success, error, and retry paths.
- Shape assumptions (rank, non-empty, rectangular/ragged expectations) are validated before traversal.
- Conversion between positional arrays and named structures preserves ordering and units.
- Malformed positional payloads fail fast with actionable, stable errors.

### 4) SQL Language and Type Semantics

- `NULL` predicate/aggregate behavior remains semantically correct.
- Type coercion and implicit cast behavior are deterministic and intentional.
- Decimal/float precision, overflow, and rounding behavior remain stable.
- Collation/case-sensitivity/timezone/timestamp-precision semantics remain unambiguous.
- `ORDER BY`, `GROUP BY`, `HAVING`, and window semantics remain rule-correct.

### 5) Parser and Binder Correctness

- Grammar changes do not introduce ambiguity or unintended parse acceptance.
- New keywords/reserved tokens do not silently break valid existing input.
- Parser rejects malformed input early with stable, non-leaky errors.
- Name resolution handles alias/CTE/shadowing rules correctly.
- Parameter binding and resolved object namespace behavior remain deterministic and type-safe.

### 6) Optimizer and Planning Correctness (Semantic)

- Logical rewrites are semantics-preserving.
- Predicate pushdown remains correct under `NULL` and outer-join semantics.
- Join reordering still respects non-associative edge cases.
- Plan-cache key includes all changed semantic discriminators.
- Hint precedence and fallback semantics remain deterministic.

### 7) Execution Engine Correctness

- Operator input/output schema contracts remain explicit and correct.
- Row-count/nullability propagation remains correct after changed logic.
- Ordering guarantees are either preserved or intentionally and explicitly dropped.
- Row-mode and vectorized-mode behavior remains semantically equivalent where both apply.
- Error mapping still yields stable, contract-consistent SQL/user-facing errors.

### 8) Regression Traps (Behavior-Preservation)

- Refactors preserve side effects that callers depend on.
- Renamed fields/parameters remain correctly mapped at all touched call sites.
- Legacy and new code paths remain behaviorally equivalent where equivalence is required.
- Existing bugfix edge cases touched by this diff are still covered by logic and tests.

## Output Handoff Rules

- Emit one finding per issue.
- Include these fields: `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
- Keep scope concrete (`path:line`, branch, module, or scenario).
- After checklist completion, hand findings to `review-output-format` and write the final JSON payload.
