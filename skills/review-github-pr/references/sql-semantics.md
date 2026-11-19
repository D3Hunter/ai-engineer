# SQL Semantics

Use when changed code affects SQL interpretation, binding, optimization, or execution results. Select the contracts affected by the diff and follow them across the relevant stages.

## SQL and binding semantics

- Preserve SQL `NULL` and three-valued logic, including predicates, aggregates, outer joins, and empty inputs.
- Check implicit casts, signedness, decimal/float precision, overflow, rounding, collation, case sensitivity, timezone, and timestamp precision where affected.
- Grammar or keyword changes can reject previously valid SQL or accept ambiguous input. Inspect name resolution for aliases, CTEs, shadowing, namespaces, and bound parameters.
- Preserve `ORDER BY`, grouping, `HAVING`, window, and limit/offset semantics, including output names, types, nullability, and ordering guarantees.

## Planner handoffs

- Follow rewritten predicates and operators through their consumers. Predicate pushdown and join reordering must preserve semantics under `NULL`, outer joins, and other non-associative cases.
- A function receiving an upstream operator and returning `self` can silently drop that operator. Inspect early returns, unsupported pushdown, hint-controlled branches, and fallback paths; required semantics must remain attached or be represented by an equivalent operator.
- Hints select optimizations without changing results. Check hint precedence and unsupported-hint behavior, plus offset/count overflow handling.
- Plan-cache keys and reuse checks must include changed semantic discriminators, such as session settings, parameter types, schema versions, or collation, when they affect the plan.

## Execution parity

- Compare row and vectorized execution where both implement the affected expression/operator. Preserve error behavior as well as values.
- Check producer/consumer schema order, positional dimensions, bounds, row counts, and mutation of reused buffers. A locally valid change can violate its caller's shape or ownership assumptions.
- Preserve side effects and prior bugfix behavior on early exits and alternate execution paths.

When actual tokenization, chunking, or logical-record framing contracts change, also use [Streaming and Framing](streaming-framing.md). An ordinary SQL or planner change does not activate that reference.
