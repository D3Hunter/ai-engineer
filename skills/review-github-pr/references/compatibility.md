# Compatibility

Use when contracts, formats, configuration, bootstrap metadata, or migrations change.

## Version boundaries

- Preserve supported API fields, error codes, defaults, wire formats, serialized tags, and on-disk readers, or follow the repository's explicit versioning policy. Unknown fields and missing new fields need safe handling in the supported old/new combinations.
- For rolling upgrades, consider old and new binaries acting as readers, writers, leaders, and followers before convergence. Newly persisted states that old code cannot interpret need capability/version gating before any node writes them.
- Bootstrap and versioned metadata should remain append-only unless migration safety is established. Inspect old bootstrap paths and version progression; editing an existing definition can behave differently on fresh installation and upgrade.
- Migrations/backfills need idempotent restart/resume after partial failure and validation of the resulting data. Check checkpoint atomicity and throttling where long work affects availability.
- Follow downgrade/rollback policy through data written after upgrade. A fallback or gate must remain usable while versions coexist; unsupported paths should fail with actionable errors. Check ordering prerequisites and necessary operator-facing instructions.
