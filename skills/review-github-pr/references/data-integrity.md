# Data Integrity

Use when changed code affects mutations, persisted state, DDL, indexes, or transaction semantics. Follow the affected operation from its preconditions through commit, error, rollback, and any restart/resume path.

## Legal transitions and atomicity

- Identify the invariant joining related fields, records, or metadata. Required multi-entity writes must remain atomic; partial success cannot leave an internally inconsistent state visible to readers.
- Check legal state-machine transitions, defaults, and terminal states. Early returns must preserve required handoffs, cleanup, and rollback rather than bypassing them.
- Verify read-after-write, snapshot, isolation, and durability assumptions against the storage model. Shared mutable objects or cached metadata must not expose an uncommitted update through another caller.
- Preserve `BEGIN`/`COMMIT`/`ROLLBACK`, savepoint, and autocommit behavior where touched. Retryable error classification must agree with whether replay is safe after the observed write outcome.

## Schema and index integrity

- Keep DDL metadata updates atomic where required, schema-version progression legal, and partially applied DDL recoverable. Failed or rolled-back operations must not leave orphan metadata or unusable objects.
- Inspect constraint validation phases and concurrent read/write behavior at intermediate schema states. Rename/drop/recreate must preserve intended object identity rather than accidentally targeting a replacement object.
- Preserve index key encoding/decoding and unique, prefix, partial, and functional index semantics. Index insert/update/delete maintenance must stay atomic with row mutations; covering reads must not return stale or missing values.
- Default and generated column evaluation must remain consistent after reload or restart.

## Value preservation

For changed persisted values, check integer bounds, decimal precision, timezones/DST/calendar boundaries, Unicode normalization, and case semantics as relevant. Renamed fields, configuration defaults, and serialization changes can silently alter stored meaning even when the state transition itself is legal.

Use [Streaming and Framing](streaming-framing.md) only when the affected serialization or ingestion path changes actual record framing, chunk/file reconstruction, or framing-related state flags. Transaction state alone does not activate its boundary matrix.
