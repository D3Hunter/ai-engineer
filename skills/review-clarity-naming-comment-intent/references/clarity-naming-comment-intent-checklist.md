# Clarity, Naming, and Comment Intent Checklist

## Core Checks

Check:
- names reflect side effects, not only checks
- terminology is domain-specific and unambiguous
- exported surface area stays minimal
- comments explain intent where code is non-obvious
- public contract docs stay synchronized with behavior

## 1) Domain Vocabulary

- Names use domain terms users already know (for example `invoice`, `shipment`, `policy`) instead of internal terms (`row`, `handler`, `dto`).
- One concept has one canonical name across code and interface surfaces (avoid `customerId` in one place and `clientId` in another for the same meaning).
- Distinct concepts are not given near-identical names (`status` vs `state` must be clearly differentiated or unified).
- Entity names are stable nouns; actions are verbs.
- No leaked storage/implementation details in public names (`mongoId`, `cacheKey`, `v2Record` in interface fields).
- Business terms are consistent with product/UI/legal language when applicable.
- Synonyms are avoided unless aliasing is intentional and documented.

## 2) Method / Endpoint / Function Naming

- Method names start with clear verbs reflecting behavior (`create`, `update`, `delete`, `list`, `get`, `search`).
- Method names reflect side effects correctly (`get*` must be read-only; mutating reads are not named `get`).
- Endpoint paths use nouns for resources and consistent hierarchy (`/users/{id}/sessions`).
- Collection vs single-resource naming is consistent (`/users` vs `/user` pattern is chosen and followed).
- Action endpoints are used only when resource semantics do not fit CRUD, and are explicitly verb-named.
- Boolean intent is explicit in verbs (`enable`, `disable`, `archive`, `restore`) instead of vague `setStatus`.
- Async operations are clearly named (`startExport`, `cancelJob`, `getJobStatus`).

## 3) Parameter Naming

- Parameter names express meaning, not just type (`timeoutSeconds` is clearer than unit-ambiguous `timeout`).
- Time-related fields include timezone/unit clarity (`createdAt` in UTC ISO8601, `ttlSeconds`).
- IDs are scoped in names where needed (`userId`, `orderId`) to avoid ambiguous `id`.
- Booleans read as predicates (`isActive`, `includeArchived`, `shouldRetry`).
- Filters are named by field meaning (`createdBefore`, `minAmount`) rather than generic placeholders.
- Pagination params are clear and consistent (`page`/`pageSize` or `cursor`/`limit`, but not mixed arbitrarily).
- Sorting params are explicit (`sortBy`, `sortOrder`) and constrained to known values.
- Optionality is obvious (required vs optional parameters are not inferred from vague names).
- Abbreviations are limited and unambiguous (`url`, `id` acceptable; `cfg`, `opt`, `val` usually poor).
- Parameter names avoid negation traps (`disableCache=false` is harder than `useCache=true`).

## 4) Request/Response Field Naming

- Response field names mirror request naming when semantics are the same.
- Field names indicate cardinality (`item` vs `items`, `count` vs `totalCount`).
- Derived/computed fields are clearly distinguished from source fields.
- Enum field names and enum values are human-meaningful and consistent (`PENDING`, `RUNNING`, `FAILED`).
- Error-related fields are standardized (`code`, `message`, `details`, `requestId`).
- Timestamps follow one naming convention (`createdAt`, `updatedAt`, `deletedAt`).
- Fields are not overloaded with context-dependent meaning.
- Backward-compatible renames keep old fields deprecated with clear transition docs.

## 5) Consistency and Symmetry

- Opposite operations are symmetrically named (`add`/`remove`, `grant`/`revoke`, `lock`/`unlock`).
- Batch operations are clearly prefixed/suffixed (`batchCreateUsers`, `/users:batchCreate`).
- Sync and async variants are distinguishable by naming.
- Internal and external surfaces use the same conceptual naming map where possible.
- Similar resources follow the same conventions (`projectId` and `teamId` style consistency).
- HTTP status, method semantics, and naming agree (for example `delete` maps to DELETE behavior).

## 6) Clarity of Behavior (via Naming)

- Names communicate side effects (whether operation mutates data, triggers notifications, or starts jobs).
- Idempotency is explicit where important (`upsert`, `put`, idempotency key naming).
- `preview`, `dryRun`, or `validate` operations are named to indicate non-mutating behavior.
- `force` or override behavior is explicit in parameter naming (`forceDelete`, `ignoreConflicts`).
- Security/privacy-sensitive operations are explicit (`redact`, `mask`, `tokenize`, `revokeToken`).

## 7) Interface and Callsite Readability

- Call sites read like intent-revealing sentences.
- Method names are short but specific; avoid cryptic short forms.
- Deeply nested namespace/class naming is avoided unless it adds real disambiguation.
- Generic names (`process`, `handle`, `execute`, `data`) are avoided when specific alternatives exist.
- Names remain clear without reading implementation code.
- Public API naming differs from internal helper naming only when justified.

## 8) Error and Exception Naming

- Error types/codes are specific (`InvalidEmailFormat`, `QuotaExceeded`) rather than generic `BadRequestError`.
- Retryable vs non-retryable failures are distinguishable by code/name.
- Authn vs authz failures are clearly separated (`Unauthenticated` vs `PermissionDenied`).
- Conflict/state errors are named by condition (`VersionConflict`, `AlreadyArchived`).
- Validation errors identify field-level context with clear keys.
- Transport errors and domain errors are not conflated in naming.

## 9) Versioning and Deprecation Naming

- Version markers are not embedded in resource names unless policy requires it.
- Deprecated fields/methods include clear markers and replacement names.
- Replacement names improve clarity, not just cosmetic renaming.
- Aliases are temporary and tracked with removal timelines.
- Breaking renames are documented with exact `old -> new` mapping.

## 10) Cross-Language / Cross-Platform Consistency

- Naming style is idiomatic per language but semantically aligned (`camelCase` vs `snake_case` differences only where conventional).
- Reserved keywords are handled predictably (`type`, `class`) with clean alternatives.
- Generated SDK names remain readable and not artifact-heavy.
- Pluralization rules are consistent across languages/SDKs.
- Case conventions are consistent per surface (JSON fields, query params, SDK methods).

## 11) Documentation Alignment

- Docs use exactly the same names as code and contract/schema definitions.
- Examples demonstrate real naming usage for common flows.
- Any intentionally unusual name has rationale documented.
- Glossary exists for overloaded business terms.
- Changelog calls out renamed fields/endpoints explicitly.
- Migration guides include before/after snippets with exact identifiers.

## 12) Naming Smell Checks (Fast Rejection Signals)

- Same meaning appears under multiple names across the codebase or public interfaces.
- Same name means different things depending on endpoint or context.
- Names require tribal knowledge to understand.
- Overuse of vague prefixes/suffixes (`data`, `info`, `mgr`, `util`, `tmp`).
- Boolean flags invert each other (`includeX`, `excludeX`) in the same API.
- Version/tech details leak into public contracts.
- New names are introduced without old-term mapping.

## Comment and Documentation Intent Checklist

### 1) Comment Necessity and Signal Quality

- Keep comments only where intent is not obvious from names/structure.
- Remove narration comments that only restate code mechanics.
- Document high-value areas: complex logic, invariants, edge cases, non-obvious tradeoffs.
- Remove stale/redundant comments instead of keeping them "just in case."
- Keep density proportional to complexity (dense in complex modules, light in simple code).

### 2) Intent Over Mechanics

- Explain why an approach exists, not only what each line does.
- Capture business rules and domain constraints explicitly.
- For non-obvious algorithms, record rationale and expected complexity impact.
- For workarounds, document root cause/limitation, not only "temporary hack."
- When important, note considered-and-rejected alternatives briefly.

### 3) Correctness and Synchronization with Code

- Keep comments synchronized after refactors and behavior changes.
- Update or remove comments when logic is removed/rewritten.
- Ensure parameter/return/side-effect docs match actual behavior.
- Revalidate "temporary" comments and track when they stop being valid.
- Avoid contradictory comments across files for the same behavior.

### 4) Interface and Contract Documentation

- Public interfaces document inputs, outputs, side effects, and error behavior.
- State preconditions and postconditions clearly.
- Clarify mutability expectations (does this mutate argument/state).
- Document nullability/optionality explicitly.
- Keep versioning/deprecation notes explicit for public contracts.
- State thread-safety/reentrancy contracts where relevant.

### 5) Invariants, Assumptions, and Safety-Critical Notes

- Place invariant comments near enforcement points.
- Make ordering/uniqueness/identity/monotonicity assumptions explicit.
- Document failure-mode expectations (retryable vs fatal, rollback behavior).
- Call out security-sensitive assumptions (trust boundaries, sanitization expectations).
- Document data consistency guarantees (eventual/strong/transactional) where needed.

### 6) Edge Cases and Boundary Behavior

- Clarify boundary behavior (empty input, zero, max size, overflow).
- Document time assumptions (timezone, skew, monotonic clock usage).
- Document locale/encoding/case-sensitivity semantics when surprising.
- Explain partial-failure and timeout semantics in IO/distributed paths.
- Distinguish "best effort" behavior from strict guarantees.

### 7) TODO/FIXME/HACK Hygiene

- Every TODO/FIXME/HACK states actionable intent (what and why).
- Temporary notes include owner, ticket/reference, and removal condition.
- Avoid vague placeholders without acceptance criteria.
- Periodically triage legacy TODOs; remove dead TODOs.
- State limitation severity (cosmetic/correctness/security/perf).

### 8) Placement and Scope

- Place comments at the narrowest scope that matches intent.
- Use function/module headers for behavior summaries, not duplicated inline narration.
- Put inline comments directly above the logic they explain.
- Avoid large prose blocks in hot paths; link design docs when needed.
- For cross-file behavior, include pointers to related implementation locations.

### 9) Readability and Style

- Keep comments concise, specific, and grammatically clear.
- Keep terminology consistent with domain vocabulary used by the codebase and product.
- Avoid ambiguous pronouns when referents are unclear.
- Use formatting that is easy to scan (short paragraphs, bullets when needed).
- Keep language professional and objective.

### 10) Examples and Usage Guidance

- Public-facing docs include realistic examples and common pitfalls.
- Mark pseudo-code clearly; otherwise examples should be runnable.
- Cover happy path and at least one failure/edge scenario.
- Document defaults and override behavior for configuration.
- For behavior changes, include migration before/after examples.

### 11) Tests as Intent Documentation

- Test names describe expected behavior, not only function names.
- Non-obvious test setup includes brief rationale comments.
- Regression tests reference bug IDs/issues and failure conditions.
- Assertions encode specific intent instead of broad/non-specific checks.
- Explain subtle business-rule cases in tests when needed.

### 12) Architecture and Decision Context

- Link non-trivial design choices to ADR/spec/discussion.
- Module docs explain responsibilities and boundaries.
- Integration points describe external protocol/contract assumptions.
- Concurrency model notes document ownership/locking/message-passing decisions.
- Performance-sensitive paths document constraints and measurement assumptions.

### 13) Documentation Drift and Governance

- Review flow explicitly checks comment/doc accuracy.
- Use doc/comment quality linters or checkers when practical.
- Behavior-changing PRs include corresponding doc/comment updates.
- Remove deprecated docs or mark replacements clearly.
- Maintain a periodic cleanup process for stale comments/TODOs.

### 14) Fast Smell Checks (Immediate Flags)

- Comment says one thing, code does another.
- Comment only repeats code text and adds no intent.
- Critical behavior has no rationale documentation.
- TODO/FIXME lacks owner/reference and lingers indefinitely.
- Public contract surface has no docs for side effects/errors.
- Security/concurrency-sensitive logic has no explanatory comments.

## Export and Surface-Minimization Sweep

1. Enumerate newly added or changed externally visible names:
   - exported methods/functions/types/fields/constants
   - endpoint names, externally consumed schema keys, and stable module entry points
2. Validate necessity:
   - required by external callers or cross-package contracts
   - not a local helper that can stay private
3. Flag candidates for scope reduction:
   - public helper used in one file/callsite only
   - exported name leaks implementation details
   - new public symbol duplicates an existing concept under a different term
4. If surface bloat exists, raise a finding with concrete scope:
   - include exact exported identifiers and `path:line`
   - explain compatibility and maintenance risk
5. If no surface issues are found, keep an internal note that the sweep completed.

## Comment Templates

- `this is not only a check, it also mutates state; rename to reflect that`
- `prefer a more specific name`
- `can be un-exported`
