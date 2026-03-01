# Compatibility and Test Determinism Checklist

## Core Checks

Check:
- compatibility promises are preserved or explicitly versioned
- upgrade, mixed-version, and rollback paths are concretely safe
- migrations are resumable, validated, and operationally controlled
- tests cover changed behavior and are deterministic under parallel/constrained execution
- release notes and operator runbooks describe required actions and validation
- backward compatibility across mixed-version clusters is preserved (or explicitly guarded)
- bootstrap/versioned metadata changes are append-only unless migration safety is proven
- changed behavior during rolling upgrade/downgrade has explicit fallback or version gating
- migration paths are idempotent and retry-safe under partial failure
- incompatibility paths return actionable errors instead of silent fallback

## Compatibility and Upgrade Safety

### Public API backward compatibility

- Existing request/response fields, error codes, status codes, and semantics are unchanged unless explicitly versioned.
- Removed/renamed fields are avoided or guarded by API version negotiation.

### Forward compatibility

- Older components safely ignore unknown fields/options from newer components.
- New data fields have safe defaults when read by older code.

### Wire/protocol compatibility

- Protocol versioning strategy is explicit (capability negotiation, min/max supported versions).
- No unversioned breaking change in RPC/message formats.

### Serialization compatibility

- Persisted serialized objects (JSON/protobuf/avro/etc.) remain readable across versions.
- Field number/tag reuse is avoided (for protobuf-like formats).

### Storage/on-disk format compatibility

- New binary/on-disk formats are versioned.
- Readers can handle old formats; migration path is explicit and tested.

### Schema migration safety

- DB migrations are reversible or explicitly marked irreversible with rollback plan.
- Expand-contract pattern is used for zero-downtime changes.
- Long-running migrations are resumable/idempotent.

### Data migration correctness

- Backfill/migration jobs include validation (checksums/count parity/invariants).
- Partial migration failure handling and restart behavior are defined.
- Migration paths are idempotent and retry-safe under partial failure.

### Mixed-version compatibility (rolling upgrade)

- N/N-1 (and N/N-2 if required) mixed cluster behavior is supported.
- Leadership transfer/rebalance/failover works with mixed binaries.
- Backward compatibility across mixed-version clusters is preserved or explicitly guarded.

### Bootstrap and versioned metadata safety

- Bootstrap/versioned metadata changes are append-only unless migration safety is proven.
- Compatibility-sensitive metadata transitions are version-gated during rollout where needed.

### Upgrade sequencing rules

- Order constraints are documented (control plane before data plane, etc.).
- Unsupported upgrade paths fail fast with actionable errors.

### Downgrade/rollback safety

- Downgrade policy is clear (supported window and prerequisites).
- New writes in upgraded version do not irreversibly break old readers unless explicitly blocked.
- Changed behavior during rolling downgrade has explicit fallback or version gating.

### Feature-flag gating

- New behavior is behind flags when needed for safe rollout.
- Flags have stable defaults and clear removal plan.

### Config compatibility

- Renamed/removed config keys have aliases or migration warnings.
- Config parsing is tolerant where possible; strict failures are actionable.

### Dependency/runtime compatibility

- Runtime/library upgrades do not break supported OS/kernel/JDK/Go/Python versions.
- External service version constraints are validated.

### State machine/invariant compatibility

- Persisted state transitions remain valid across version boundaries.
- No "new state old code cannot interpret" without guardrails.

### Security/permissions compatibility

- AuthN/AuthZ behavior changes are backward compatible or migration-safe.
- Certificate/credential format changes include transition period.

### Operational compatibility

- Metrics/log fields change safely (no silent dashboard/alert breakage).
- Health checks/readiness semantics remain stable.

### Performance/SLO safety during upgrade

- Expected temporary impact is measured and documented.
- Rate-limits/throttling for migrations prevent production overload.

### Release notes and operator runbook

- Breaking changes, required actions, and rollback steps are explicit.
- Preconditions and post-upgrade verification steps are documented.

### Incompatibility-path error handling

- Incompatibility paths return actionable errors instead of silent fallback behavior.
- Errors include enough context to guide operators toward supported upgrade/downgrade actions.

## Tests and Determinism

### Unit test coverage for changed logic

- Each new branch, boundary, and error path has unit test coverage.
- Bug fixes include regression tests that fail before fix.
- Behavior changes include unit and/or integration tests.
- Edge and negative cases are covered.
- Mixed scenarios are split into focused cases.

### Contract tests

- API/serialization contracts are tested across versions where applicable.
- Golden compatibility fixtures are version-pinned.

### Integration tests

- Cross-component behavior is tested (not just isolated mocks).
- Realistic dependency interactions are validated.

### End-to-end tests

- Critical user flows work from entry to persistence/output.
- Upgrade-related customer journeys are covered.

### Upgrade tests

- Start old version, upgrade to new, verify invariants.
- Mixed-version operation is tested before full convergence.

### Downgrade/rollback tests

- Rollback path is exercised, not just documented.
- Data created post-upgrade is validated against downgrade policy.

### Migration tests

- Schema/data migrations are tested on representative volume and edge data.
- Interrupted migration and resume behavior are tested.

### Failure-path tests

- Network partitions/timeouts/retries/partial failures are tested.
- Crash/restart in critical windows is covered.

### Concurrency tests

- Race-prone sections are tested under parallel stress.
- Deadlock/livelock/starvation scenarios are considered.

### Deterministic time handling

- Tests do not rely on wall clock; use fake clocks/time injection.
- Timezone/locale effects are explicit and pinned.

### Deterministic randomness

- Random seeds are fixed and logged.
- Property/fuzz tests persist failing seeds/cases.

### Deterministic ordering

- Assertions do not depend on map/hash iteration order or scheduling luck.
- Outputs are sorted/normalized before comparison when order is irrelevant.

### No sleep-based synchronization

- Avoid arbitrary sleep; use explicit synchronization/conditions.
- Polling loops have deterministic bounds and diagnostics.
- Prefer `require.Eventually`, channel/sync-based signaling, or explicit hooks over `time.Sleep`.

### Isolation from environment

- Tests do not depend on host state, network, or shared mutable resources unless explicitly integration/e2e.
- Temp dirs/ports are unique and cleaned up.

### Stable fixtures and snapshots

- Fixture generation is deterministic and version-controlled.
- Snapshot/golden update process is intentional, reviewed, and not auto-masked.

### Flake resistance checks

- Key suites are rerun multiple times to detect nondeterminism.
- Flaky tests are tracked with owner and fix plan, not silently ignored.

### Matrix coverage in CI

- Required OS/runtime/db/version matrices are covered.
- Important feature-flag combinations are tested.

### Resource-bound determinism

- Tests pass under constrained CPU/memory (avoid timing-only pass conditions).
- Parallel test execution does not create hidden coupling.

### Observability in tests

- Failures emit enough context (seed, version, config, logs) for reproduction.
- Repro command for CI failures is documented.

### Test quality gates

- New code does not reduce meaningful coverage in critical modules.
- Static checks/race detector/sanitizers (where applicable) are included.

### Performance/regression tests (where relevant)

- Baseline and threshold are defined for hot paths.
- Results are noise-aware and reproducible.

### Deterministic cleanup

- Teardown always runs and is idempotent.
- No leaked goroutines/threads/file handles/processes between tests.

## Determinism Patterns

- anti-pattern: `time.Sleep`-based waiting in assertions -> preferred: `require.Eventually`, channel/sync-based signaling, or explicit hooks
- anti-pattern: timing races to hit hard-to-reach branches -> preferred: targeted failpoint/hook to make branch execution deterministic
- anti-pattern: one large test mixing happy/negative/retry paths -> preferred: split into focused test cases with one behavior target each
- anti-pattern: random/non-fixed timing inputs -> preferred: deterministic inputs and stable assertions

## Comment Templates

### Compatibility and upgrade safety

- `is this backward compatible with N-1 nodes?`
- `should this be guarded by version gate/feature flag?`
- `upgrade path from <old-version> may hit this branch; can we keep fallback behavior?`
- `can we add an upgrade/compat test for this path?`

### Tests and determinism

- `add UT for it`
- `add some negative cases`
- `maybe split the test into 2, one for each kernel type`
- `use require.Eventually`
