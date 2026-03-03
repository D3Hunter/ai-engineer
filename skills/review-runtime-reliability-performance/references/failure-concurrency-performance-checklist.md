# Failure Semantics, Concurrency Lifecycle, and Performance Checklist

## 1) Failure Semantics and Resilience

### Failure Contracts and Error Taxonomy

- Failure contract is explicit: every API/job/worker defines success, retryable failure, non-retryable failure, timeout, and cancellation outcomes.
- Typed error taxonomy exists: errors map to stable codes/classes (not free-form strings) and preserve cause chains.
- No silent failure paths: background tasks, callbacks, and async branches propagate or record errors; no dropped futures/promises.
- Partial-failure behavior is defined: multi-step flows specify what happens when step N fails after step N-1 succeeded.

### Retry, Timeout, and Degradation Policy

- Idempotency is guaranteed where retries occur: duplicate delivery/request replay cannot create duplicate side effects.
- Retry policy is bounded and correct: exponential backoff + jitter, max attempts, and retry only for safe/transient classes.
- Timeout semantics are deliberate: timeouts are set per dependency and aligned with end-to-end request budget.
- Fail-open vs fail-closed is intentional: security-critical paths fail closed; availability-favoring paths fail open with guardrails.
- Circuit breaking/load shedding exists: under dependency degradation, system degrades predictably instead of cascading failures.
- Compensation/rollback semantics are defined: for non-atomic distributed operations, compensating actions are explicit and tested.
- Durability/ack semantics are explicit: at-most-once / at-least-once / effectively-once behavior is documented and verified.

### Observability and Operations

- Structured logging quality is high: logs include operation, resource identifiers, request/trace IDs, error class/code, and outcome.
- Metrics cover failures and saturation: error rate, timeout rate, retries, queue depth, rejection/drop counts, and dependency health.
- Tracing is end-to-end: trace context propagates across service/message boundaries with spans around external calls.
- Alerts are actionable: alerts tie to SLO symptoms, include thresholds, and avoid noise from transient/expected blips.
- Observability avoids cardinality explosions: labels are bounded; high-cardinality fields stay in logs/traces, not metrics tags.
- Runbooks exist for top failure modes: on-call can diagnose and mitigate from dashboards/logs/traces without code spelunking.

### Focused Review Prompts (Failure Semantics)

Check:
- retriable vs non-retriable errors are explicit and aligned with scheduler behavior
- duplicate logging is avoided across framework and caller layers
- cancellation path returns meaningful cause (`ctx.Err()` or `context.Cause`)

Comment templates:
- `framework already prints this error, no need to print again`
- `can be retried automatically?`
- `return ctx.Err()?`
- `should we record this error? since it is recoverable`

## 2) Concurrency, Context, and Lifecycle

### Ownership, Synchronization, and Atomicity

- Concurrency ownership model is clear: shared state uses immutable snapshots, actor/single-owner, or explicit synchronization.
- Data-race safety is enforceable: all mutable shared data is guarded (locks/atomics/channels); race tooling is used in CI where possible.
- Lock discipline prevents deadlocks: global lock ordering, minimal critical sections, and no blocking I/O while holding hot locks.
- Atomicity preserves invariants: multi-variable updates that represent one invariant are atomic/transactional.

### Context, Cancellation, and Timeout Hierarchy

- Context/request scope propagates correctly: request context, cancellation, deadlines, and correlation IDs flow through all downstream calls.
- Cancellation is cooperative and fast: long loops/streams/checkpoints observe cancellation and stop work quickly.
- Timeout hierarchy is sane: child operations have stricter deadlines than parent; no infinite waits on blocking operations.

### Backpressure, Bounded Parallelism, and Lifecycle Hygiene

- Parallelism is bounded: worker pools/semaphores/queue bounds prevent unbounded goroutine/thread/task creation.
- Backpressure is explicit: queue full behavior is deterministic (block, drop oldest/newest, fail fast), never accidental.
- No lifecycle leaks: threads/goroutines/timers/subscriptions/connections are always stopped/closed on completion or cancellation.
- Startup ordering is correct: dependencies initialize before serving traffic; readiness reflects actual ability to serve.
- Shutdown is graceful: new work is rejected, in-flight work drains within budget, cleanup hooks run deterministically.
- Reentrancy/thread-affinity assumptions are safe: callbacks do not accidentally reenter unsafe code paths; thread-bound resources are respected.
- Cross-process concurrency is safe: distributed locks/leases include TTL renewal, fencing tokens, and split-brain considerations.
- Concurrency tests are deterministic enough: stress/fuzz/race tests exist for critical synchronization and cancellation paths.

### Focused Review Prompts (Concurrency and Lifecycle)

Check:
- cancellation order is safe (stop producer loops, wait for exit, then cleanup)
- shared mutable state is scoped locally when possible
- map/slice mutation has no data-race window

Comment templates:
- `can we make sure the submit loop exits before cancel?`
- `init this map before create task, else there might be data race`
- `create it on demand, no need to use global var`
- `why not use context.Cause`

## 3) Performance and Scaling

### Targets, Measurement, and Complexity

- Performance targets are defined: p50/p95/p99 latency, throughput, and resource budgets are explicit per critical path.
- Hot paths are measured, not guessed: profiling/tracing identifies CPU, memory, lock, and I/O hotspots before optimization.
- Algorithmic complexity is appropriate: no accidental O(n^2)/O(n^3) operations on growth paths; scaling assumptions are documented.
- Allocation pressure is controlled: hot paths avoid excessive allocations/copies; object reuse or pooling where justified.

### Data Access and Dependency Efficiency

- I/O is efficient: batching, streaming, pagination, and compression are used appropriately to reduce round-trips and payload size.
- No N+1 access patterns: DB/service calls are batched or prefetched; repeated lookups are eliminated in loops.
- Query/index design is validated: query plans are inspected; indexes match predicates/sorts; full scans on hot paths are avoided.
- Cache strategy is coherent: key design, TTL/invalidation, warmup behavior, and stampede protection are defined.

### Contention, Tail Latency, and Overload Behavior

- Contention bottlenecks are addressed: lock contention, queue contention, and single-threaded chokepoints are measured and reduced.
- Tail latency is treated as first-class: slow dependency paths, retries, and queueing effects on p99 are explicitly mitigated.
- Load shedding and overload behavior are tested: system maintains core function under load instead of collapsing.
- Horizontal scaling model is viable: statelessness, partitioning/sharding strategy, and rebalancing behavior are clear.
- Resource limits are explicit: CPU/memory/file descriptors/connections have sane limits and protection against exhaustion.
- Cold start and autoscaling effects are understood: startup time, cache warmup, and burst handling are measured.
- Performance regressions are gated: benchmarks/load tests run in CI or pre-release; regressions fail gates.
- Cost-performance tradeoffs are visible: improvements are evaluated against infra cost, not latency only.

### Focused Review Prompts (Performance and Scaling)

Check:
- new loops/scans/validation are justified with expected overhead
- concurrency formulas remain safe at large node/store counts
- unnecessary storage/network calls are removed

Comment templates:
- `what is the performance penalty introduced by this?`
- `will this concurrency be too large when store count is large?`
- `can we avoid this extra get/head call?`
