# Code Structure, Encapsulation, and Duplication Checklist

## Core Checks

Check:
- package cohesion: avoid mixing unrelated concerns in one package
- code placement: keep logic at the right layer (planner/executor/scheduler/storage)
- encapsulation: extract methods when one block mixes responsibilities
- readability: name extracted methods by behavior, not by mechanism
- testability: create seams that reduce setup and isolate side effects
- deduplication: if similar logic appears in 2+ places, prefer one focused helper
- domain modeling: business/domain records avoid opaque positional containers unless true matrix semantics apply
- avoid generic wrappers when direct APIs are clearer
- avoid exported or global utilities for one-time local logic
- avoid mixing unrelated behavior changes in a bugfix PR
- duplicate-definition safety: detect same-scope collisions in map keys, switch labels, registry entries, and table-driven test definitions
- SQL fixture duplication: normalize and compare raw SQL strings (case/whitespace/quoting), including repeated placeholder-style literals such as `select $$`
- duplicate-definition sweep: when duplication-prone structures are touched, run a sweep for collisions, shadowing, and unreachable duplicate cases

## Scope Definition

- the change has a one-sentence objective
- the PR description states what is explicitly out of scope
- every touched file can be justified by the objective
- no drive-by cleanup is mixed into a bugfix unless isolated in a separate commit
- refactor and behavior change are separated (or clearly justified if combined)
- any dependency/version bump is directly required by the fix
- any config/schema/protocol impact is called out explicitly

## Scope Containment

- the fix is the smallest viable change (minimum blast radius)
- no unnecessary public API expansion for one local use
- no new global/shared utility for one-time logic
- no cross-package refactor unless required for correctness
- no broad signature changes when a local adapter would work
- no unrelated naming/moving/reformatting mixed with logic changes

## Abstraction Discipline

- new abstractions solve a real repeated need, not speculative reuse
- check whether a new abstraction adds real reuse/clarity or just indirection
- prefer direct calls (for example `context.WithTimeout`) when wrapper is single-use or hides important behavior
- wrapper layers do not hide critical semantics (timeouts, retries, cancellation, transactions)
- a helper with one callsite stays local/private unless there is a strong reason
- duplication removal does not over-generalize the domain model
- interface extraction is driven by testability or multiple implementations, not style

## Domain Data Modeling (Positional vs Named)

- prefer structs/value objects with named fields for business/domain records
- use multidimensional arrays/slices only when data is inherently matrix/grid/algorithmic
- if positional storage remains, document dimension order once and expose named accessors/helpers
- avoid raw magic index access across broad call paths; confine index arithmetic to boundary adapters
- validate positional shape invariants at construction/decoding boundaries (rank, lengths, non-empty constraints)
- if adding one domain attribute forces broad positional rewrites, refactor to a named type
- recurring primitive tuples across 2+ callsites should be promoted to a named struct/value object
- replace reorder-prone primitive/boolean argument packs with named parameter or options structs

## Control-Flow Complexity

- function/method branching is manageable (no branch explosion)
- nesting depth is reasonable; early returns/guard clauses are used
- boolean flags are not combinatorial (flag soup)
- state transitions are explicit and understandable
- order-dependent calls (temporal coupling) are minimized and documented

## State and Side-Effect Complexity

- ownership/lifecycle of mutable state is clear
- no hidden side effects across layers
- retry/idempotency behavior is explicit where relevant
- partial-failure and rollback behavior is defined
- concurrency interactions do not introduce implicit shared-state complexity

## Interface and Contract Complexity

- external behavior changes are minimal and intentional
- backward compatibility is assessed when contracts change
- defaults remain unsurprising and safe
- added options/flags do not create hard-to-test interaction matrices
- error contracts remain consistent and actionable

## Reviewability Complexity

- diff size remains reviewable; large mechanical changes are isolated
- commit structure tells a clear story (prep/refactor/fix/tests)
- reviewers can map each major hunk to a requirement or defect
- risky hotspots are called out directly in the PR text
- non-obvious trade-offs/invariants are documented briefly

## Test Complexity Alignment

- tests cover each newly introduced branch/failure path
- edge cases introduced by new complexity are explicitly tested
- tests are deterministic (no flaky timing/random dependence)
- integration tests are added only where contract boundaries changed
- test setup remains readable and not over-coupled to internals

## Complexity Acceptance Gates

- reject if one PR mixes multiple unrelated concerns
- reject if abstraction count increases without measurable clarity/reuse gain
- reject if reviewers cannot explain the main execution path quickly
- reject if behavior change lacks corresponding test or rationale
- prefer splitting into staged PRs when complexity is needed (prep PR, then behavior PR)

## Comment Templates

- `this pkg mixes too many concerns, can we move this to <pkg>?`
- `this logic is better colocated with <component>, current location increases coupling`
- `can we extract this into a separate method for readability and easier testing?`
- `duplicated logic with <path>, can we abstract one helper?`
- `this helper is too generic, prefer a domain-specific method name`
- `this definition looks duplicated with <path:line>; can we keep one source of truth?`
- `same SQL case appears multiple times (for example, select $$); can we dedupe to avoid shadowing/coverage blind spots?`
- `it is too complex for this; can we use context.WithTimeout directly?`
- `only used here, move it closer or inline`
- `this is not part of the fix`
- `seems no need`

## Extraction Thresholds

- extract when one block has 2+ responsibilities (for example: validation + mutation + logging)
- extract when similar logic exists in 2+ call sites
- extract when a branch carries business invariants that need a meaningful method name
- extract when tests need large setup to reach a sub-branch and a method seam can isolate it

## Duplication Policy

- prefer abstraction for repeated business logic, validation flow, or state transitions
- acceptable temporary duplication: migration phases, deliberate hot-path specialization, or intentionally different business semantics
- if duplication is intentional, require a short comment explaining why and when to converge
- avoid generic utility dumping; keep shared helper close to dominant caller unless cross-package reuse is real

## Duplicate-Definition Sweep

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
