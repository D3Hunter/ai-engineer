---
name: tidb-coding-reference
description: Primary reference skill for coding in pingcap/tidb, including storage SQL, service/handler logic, runtime visibility guards, and test design.
---

# TiDB Coding Reference

## Purpose

This skill is a reusable coding playbook based on implementation experience in `pingcap/tidb`.

Use it when a change affects behavior across layers, such as:

- SQL/data access in framework or storage packages
- server/service/handler behavior
- route/feature visibility by runtime predicates
- compatibility constraints (nextgen/classic, keyspace, feature mode)
- tests across storage and HTTP/integration surfaces

## What To Extract From Prompt First

Before coding, normalize the request into these six constraints:

1. **Behavior contract**
   - exact input/output shape
   - required error messages and status behavior

2. **Data contract**
   - source-of-truth tables and boundaries (for example: active-only, history-only, or union)
   - missing-data semantics

3. **Runtime visibility policy**
   - predicates that enable/disable functionality
   - where endpoint or feature must not be exposed

4. **Privilege and execution model**
   - user privilege expectations
   - whether internal execution context is required

5. **Layer ownership**
   - which package owns SQL execution
   - which package owns transport/request parsing

6. **Verification policy**
   - whether to run tests or provide reasoning-only validation

Do not implement until these are explicit.

## TiDB Implementation Heuristics

1. **Follow existing package boundaries**
   - Keep SQL in storage/repository-style code.
   - Keep handlers focused on validation, context, and serialization.

2. **Use runtime predicates at registration point**
   - Apply visibility guards where features/routes are wired.
   - Do not rely on deep handler checks alone.

3. **Preserve data semantics literally**
   - If requirement says history-only, enforce history-only in SQL.
   - Do not silently broaden scope in the first implementation.

4. **Prefer typed structs over map-based payloads**
   - Domain structs in storage layer.
   - JSON structs in API response path.

5. **Return meaningful lower-layer errors**
   - Use typed/known errors in storage layer.
   - Annotate with operational context (`id`, constrained source).
   - Map to transport response in handler layer.

6. **Use internal execution context when required**
   - Internal SQL/data calls should carry internal source context where expected by TiDB patterns.

7. **Keep SQL retrieval-oriented; move presentation math to Go**
   - SQL should prefer returning raw values (`bytes`, `seconds`, counts), not formatted strings.
   - Avoid SQL-side display transforms such as `SEC_TO_TIME` and chained unit divisions for API presentation.
   - Compute display fields in Go so formatting can evolve without rewriting SQL.

8. **Format runtime-facing values in Go with standard helpers**
   - For durations, convert raw seconds to `time.Duration` and use Go string formatting.
   - For byte size display, use `github.com/docker/go-units` (for example `units.BytesSize`) instead of ad-hoc `GiB` string logic.
   - This keeps behavior readable for small values too (for example values below `1GiB` can render as `MiB`).

9. **Separate feature-specific methods into focused files**
   - If a method is strongly tied to one feature (for example DXF import-into history), move it out of generic task-table files.
   - Keep shared storage files centered on common manager primitives.
   - This improves maintainability and reduces cognitive load during future reviews.

10. **Avoid abbreviation-heavy names in SQL mapping and helpers**
   - Prefer explicit aliases and local names (`column_count`, `distsql_scan_concurrency`, `durationSeconds`) over shortened forms (`col_cnt`, `distsql_con`, `dur`).
   - Even when mapping by index, SQL aliases should remain readable for future maintenance and review.
   - Helper parameter names should encode domain intent (`totalBytes`, `taskConcurrency`) rather than generic placeholders.

11. **Document non-obvious contract and schema semantics close to code**
   - For API-facing display fields, document output format expectations (for example Go `time.Duration` strings and binary size units).
   - When storage schema names are unintuitive (for example a `task_key` column storing numeric task ID), leave a concise note near the query.
   - Keep comments intent-focused and close to enforcement/use sites to reduce misreads.

12. **Filter unset timestamp rows when computing duration-based metrics**
   - In DXF history tables, `start_time`/`state_update_time` can be unset (`0` or `NULL`) for placeholders or incomplete subtasks.
   - Duration aggregation SQL must filter to valid timestamps (for example `start_time > 0 and state_update_time > 0`) before `min/max` or `TIMESTAMPDIFF`.
   - Otherwise totals and per-step durations can be inflated and derived speed fields become misleading.

## Recommended Workflow

1. **Locate ownership quickly**
   - Find analogous feature path first (storage -> handler -> router -> tests).

2. **Implement storage change first**
   - Add/extend method.
   - Keep SQL and row mapping there.
   - Return typed result + explicit not-found behavior.

3. **Implement service/handler**
   - Parse and validate params.
   - Build context/timeout/internal source.
   - Call storage method.
   - Return JSON and mapped errors.

4. **Wire visibility in router/server**
   - Register route/feature under explicit runtime predicates.

5. **Add tests in two layers**
   - Storage test: SQL semantics, mapping, edge behavior.
   - HTTP/integration test: route wiring, validation, status, response shape.

6. **Quality pass**
   - `gofmt` touched files.
   - lint/diagnostics on changed files.
   - run tests if requested; otherwise provide correctness reasoning.
   - if tests are intentionally skipped by instruction, include explicit reasoning for SQL semantics, null/zero guards, and output compatibility.

## Test Design Pattern (Reusable)

Always cover:

1. invalid method and invalid parameter paths
2. constrained-source not-found behavior
3. happy path with deterministic seeded fixtures
4. critical field mapping assertions
5. storage semantics independently from HTTP behavior

When tests are not run, report:

- which tests were added
- why those tests prove requirements
- residual risk (if any)

## Common TiDB Pitfalls

- Mixing transport logic and SQL in the same layer.
- Registering endpoint without runtime visibility guard.
- Replacing precise not-found semantics with generic errors.
- Accidentally changing data scope (history-only -> broader query).
- Adding tests only at one layer (missing storage or integration coverage).
- Ignoring existing feature patterns and introducing one-off conventions.
- Aggregating duration across history subtasks without filtering unset timestamp rows (`0`/`NULL`), which can silently skew API metrics.

## Completion Checklist

- [ ] Prompt constraints extracted (behavior/data/scope/privilege/layer/verification)
- [ ] Storage implementation complete with typed return
- [ ] Handler implementation complete with validation and error mapping
- [ ] Router visibility guard applied via runtime predicates
- [ ] Storage tests added
- [ ] HTTP/integration tests added
- [ ] Formatting and lint checks completed
- [ ] Final summary includes correctness reasoning (if tests were not executed)
- [ ] SQL is retrieval-oriented and formatting is handled in Go
- [ ] Feature-specific methods are placed in focused files instead of generic aggregating files
- [ ] SQL aliases and helper names avoid unclear abbreviations
- [ ] Non-obvious schema semantics and API output formats are documented near implementation
- [ ] Duration aggregation SQL excludes unset timestamp rows before `TIMESTAMPDIFF`/`min`/`max`

