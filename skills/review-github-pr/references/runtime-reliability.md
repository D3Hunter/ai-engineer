# Runtime Reliability

Use when changed code affects failures, retries, asynchronous work, shared resources, or scaling. Concentrate on the lifecycle and workload that can reach the changed path.

## Failure and replay

- Distinguish success, retryable failure, terminal failure, timeout, and cancellation. Preserve error causes and scheduler-facing classifications; background work must not silently lose failures.
- Check partial-success windows: a timeout can occur after a remote write succeeds. Retries and duplicate delivery need idempotent effects, deduplication, or an explicit compensation strategy.
- Keep retry attempts, elapsed time, and backoff bounded by the operation budget. Do not retry unsafe or permanent failures merely because a transport error occurred.
- Match acknowledgments to persistence guarantees. Fail-open/fail-closed and fallback behavior must preserve the affected contract under dependency degradation.

## Ownership and cancellation

- Follow ownership of goroutines/tasks, channels, locks, timers, subscriptions, and connections through startup, completion, and shutdown.
- Cancellation order matters: stop submission/producer loops, signal cancellation as required to unblock them, wait for workers to exit, then release resources they may still use. Check the actual dependency order for deadlocks and use-after-close races.
- Propagate request context/deadlines and useful cancellation causes. Long loops and blocking calls need a path to observe cancellation.
- Shared map/slice initialization and mutation must be synchronized before workers access them. Check lock ordering, blocking I/O under locks, reentrancy, and atomic updates of multi-field invariants.
- Distributed leases or locks need safe expiry/renewal and fencing where stale owners can still act.

## Bounded work and scaling

- Bound parallelism, queues, retries, memory, and open resources. Check concurrency formulas at realistic large node/store counts and define queue-full behavior.
- Inspect newly repeated scans, copies, allocations, network/storage calls, and N+1 access patterns on growth paths. Tie performance concerns to reachable input sizes and expected workloads.
- Consider backpressure, contention, cache invalidation/stampedes, and tail latency during overload. Existing metrics/logging should still expose actionable failures without unbounded label cardinality.
