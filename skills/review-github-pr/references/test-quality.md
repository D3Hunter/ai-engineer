# Test Quality

Use when tests change or when evaluating whether existing tests meaningfully cover the changed behavior, across any review area.

## Evidence and determinism

- Look for assertions that distinguish the changed behavior from the old behavior, including the relevant boundary, error, alternate-path, or interrupted-migration case. Mocks that bypass the changed contract can give false confidence.
- Sleeps and scheduling races do not establish ordering. Prefer explicit synchronization, hooks/failpoints, fake clocks, or bounded condition waiting with useful diagnostics.
- Check wall-clock, timezone/locale, random seed, map iteration, unordered SQL results, and host/network dependencies. Normalize ordering only when the contract permits it; otherwise normalization can hide a defect.
- Parallel tests need isolated ports, temporary paths, globals, environment variables, and fixtures. Cleanup must run on failure and release workers/resources before the next case.
- Golden/fixture updates must preserve meaningful assertions. Fixed seeds, version-pinned fixtures, and failure context should make cases reproducible under constrained CPU/memory as well as normal execution.
