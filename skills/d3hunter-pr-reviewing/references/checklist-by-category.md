# Checklist by Category

Use this file as the detailed companion for `1 -> 10` review order.

## 1) Correctness and Invariants

Check:
- versioned metadata and bootstrap rules are not mutated in-place
- state-machine transitions are still valid under retry/failover
- changed conditions do not hide bugs with silent skips

Comment templates:
- `why change this invariant?`
- `must not change this one, add a new version entry instead`
- `when will this happen? seems a bug`

## 2) Compatibility and Upgrade Safety

Check:
- backward compatibility across mixed-version clusters is preserved (or explicitly guarded)
- bootstrap/versioned metadata changes are append-only unless migration safety is proven
- changed behavior during rolling upgrade/downgrade has explicit fallback or version gating
- migration paths are idempotent and retry-safe under partial failure
- incompatibility paths return actionable errors instead of silent fallback

Comment templates:
- `is this backward compatible with N-1 nodes?`
- `should this be guarded by version gate/feature flag?`
- `upgrade path from <old-version> may hit this branch; can we keep fallback behavior?`
- `can we add an upgrade/compat test for this path?`

## 3) Code Structure, Encapsulation, and Duplication

Check:
- package cohesion: avoid mixing unrelated concerns in one package
- code placement: keep logic at the right layer (planner/executor/scheduler/storage)
- encapsulation: extract methods when one block mixes responsibilities
- readability: name extracted methods by behavior, not by mechanism
- testability: create seams that reduce setup and isolate side effects
- deduplication: if similar logic appears in 2+ places, prefer one focused helper
- duplicate-definition safety: detect same-scope collisions in map keys, switch labels, registry entries, and table-driven test definitions
- SQL fixture duplication: normalize and compare raw SQL strings (case/whitespace/quoting), including repeated placeholder-style literals such as `select $$`
- duplicate-definition sweep: when duplication-prone structures are touched, run a sweep for collisions, shadowing, and unreachable duplicate cases

Comment templates:
- `this pkg mixes too many concerns, can we move this to <pkg>?`
- `this logic is better colocated with <component>, current location increases coupling`
- `can we extract this into a separate method for readability and easier testing?`
- `duplicated logic with <path>, can we abstract one helper?`
- `this helper is too generic, prefer a domain-specific method name`
- `this definition looks duplicated with <path:line>; can we keep one source of truth?`
- `same SQL case appears multiple times (for example, select $$); can we dedupe to avoid shadowing/coverage blind spots?`

Extraction thresholds:
- extract when one block has 2+ responsibilities (for example: validation + mutation + logging)
- extract when similar logic exists in 2+ call sites
- extract when a branch carries business invariants that need a meaningful method name
- extract when tests need large setup to reach a sub-branch and a method seam can isolate it

Duplication policy:
- prefer abstraction for repeated business logic, validation flow, or state transitions
- acceptable temporary duplication: migration phases, deliberate hot-path specialization, or intentionally different business semantics
- if duplication is intentional, require a short comment explaining why and when to converge
- avoid generic utility dumping; keep shared helper close to dominant caller unless cross-package reuse is real

Duplicate-definition sweep:
When duplication-prone structures are touched, run this sweep during the category-3 pass.

1. Enumerate changed definition sites:
   - map literals and map assignments
   - switch/case labels and parser token branches
   - registry/table-driven test entries
   - raw SQL fixture literals in tests and parser-related code
2. Compare same-scope entries for collisions:
   - identical keys/labels/IDs in one scope
   - semantically duplicated SQL fixtures that differ only by case/whitespace/quoting
3. Normalize SQL fixture text before comparing duplicates:
   - trim spaces and collapse repeated internal whitespace
   - compare case-insensitively for SQL keywords
   - treat placeholder-heavy patterns (for example, repeated `select $$`) as high-risk duplicates
4. If duplicate definitions exist, raise a finding with concrete scope and risk:
   - scope must list both definitions (`path:line` for each)
   - risk must explain shadowing/override/coverage-blindspot impact
5. If no duplicates are found, keep an explicit internal review note that the sweep was completed.

## 4) Failure Semantics and Observability

Check:
- retriable vs non-retriable errors are explicit and aligned with scheduler behavior
- duplicate logging is avoided across framework and caller layers
- cancellation path returns meaningful cause (`ctx.Err()` or `context.Cause`)

Comment templates:
- `framework already prints this error, no need to print again`
- `can be retried automatically?`
- `return ctx.Err()?`
- `should we record this error? since it is recoverable`

## 5) Concurrency, Context, and Lifecycle

Check:
- cancellation order is safe (stop producer loops, wait for exit, then cleanup)
- shared mutable state is scoped locally when possible
- map/slice mutation has no data-race window

Comment templates:
- `can we make sure the submit loop exits before cancel?`
- `init this map before create task, else there might be data race`
- `create it on demand, no need to use global var`
- `why not use context.Cause`

## 6) Scope and Complexity

Check:
- avoid generic wrappers when direct APIs are clearer
- avoid exported or global utilities for one-time local logic
- avoid mixing unrelated behavior changes in a bugfix PR

Comment templates:
- `it is too complex for this; can we use context.WithTimeout directly?`
- `only used here, move it closer or inline`
- `this is not part of the fix`
- `seems no need`

## 7) Performance and Scaling

Check:
- new loops/scans/validation are justified with expected overhead
- concurrency formulas remain safe at large node/store counts
- unnecessary storage/network calls are removed

Comment templates:
- `what is the performance penalty introduced by this?`
- `will this concurrency be too large when store count is large?`
- `can we avoid this extra get/head call?`

## 8) API Clarity and Naming

Check:
- names reflect side effects, not just checks
- terminology is domain-specific and unambiguous
- exported surface area stays minimal

Comment templates:
- `this is not only a check, it also mutates state; rename to reflect that`
- `prefer a more specific name`
- `can be un-exported`

## 9) Comments and Intent Documentation

Check:
- core logic that is hard to understand at first glance has a short explanatory comment
- branch behavior driven by business decisions or compatibility constraints has a `why` comment
- comments explain intent, invariant, or trade-off, not line-by-line workflow
- obvious workflow code is not over-commented
- comments that can become stale are anchored to stable rationale (decision, invariant, contract)

Comment templates:
- `can we add a short comment on why this branch exists?`
- `this depends on business decision/compat behavior, please add a why-comment`
- `the workflow is already clear, this comment may be distracting and can be removed`
- `please explain the invariant/trade-off here, current intent is hard to infer`

## 10) Tests and Determinism

Check:
- behavior changes include UT and/or integration tests
- edge/negative cases are covered
- tests are deterministic (avoid sleep/random where possible)
- mixed scenarios are split into focused cases

Comment templates:
- `add UT for it`
- `add some negative cases`
- `maybe split the test into 2, one for each kernel type`
- `use require.Eventually`

Determinism patterns:
- anti-pattern: `time.Sleep`-based waiting in assertions -> preferred: `require.Eventually`, channel/sync-based signaling, or explicit hooks
- anti-pattern: timing races to hit hard-to-reach branches -> preferred: targeted failpoint/hook to make branch execution deterministic
- anti-pattern: one large test mixing happy/negative/retry paths -> preferred: split into focused test cases with one behavior target each
- anti-pattern: random/non-fixed timing inputs -> preferred: deterministic inputs and stable assertions
