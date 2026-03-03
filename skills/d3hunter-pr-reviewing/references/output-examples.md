# Output Examples

Use these examples with the `Review Output Contract`.
These examples are contract-compliant and should be treated as canonical templates.

## Inline Comment Mode

Attribution is summary-only; inline finding bodies do not repeat it.

```markdown
#### ⚠️ **[Major]** Invariant mutation without versioned migration path

**Why**
- mutating versioned metadata in-place can break downgrade and mixed-version safety.

**Scope**
- pkg/session/bootstrap/bootstrap.go (version metadata update block)

**Risk if unchanged**
- clusters rolling back to N-1 may read incompatible state and fail bootstrap.

**Evidence**
- diff replaces existing version entry instead of appending a new gated version branch.

**Change request**
- keep old entry immutable, append a new versioned path, and add upgrade/downgrade coverage.
```

## Threaded Review Mode (Top-Level Summary)

```markdown
**AI-generated review based on @D3Hunter’s standards; manual follow-up after comments are addressed.**

### Findings (highest risk first)

1. 🚨 **[Blocker]** Cancellation lifecycle race in submit loop
   - **Scope:** pkg/disttask/scheduler/scheduler.go submit loop + cancel path
   - **Risk if unchanged:** intermittent task leak and non-deterministic failures under cancellation.

2. ⚠️ **[Major]** Missing compat guard for mixed-version path
   - **Scope:** pkg/meta/model/job.go compatibility branch
   - **Risk if unchanged:** rolling upgrade can enter unsupported branch silently.

### Required validation before merge

1. Add mixed-version compatibility test for N/N-1 branch behavior.
2. Add deterministic cancellation lifecycle test that covers producer exit ordering.
```

## Threaded Review Mode (Sub-Comment Per Finding)

```markdown
#### ⚠️ **[Major]** Missing compat guard for mixed-version path

**Why**
- mixed-version behavior must remain explicit during rolling upgrades.

**Scope**
- pkg/meta/model/job.go compatibility branch

**Risk if unchanged**
- upgrade can silently enter an unsupported path and produce hard-to-debug failures.

**Evidence**
- new branch lacks version gate/fallback while old path is still reachable in N/N-1 topology.

**Change request**
- add explicit version guard (or fallback path) and include an N/N-1 compatibility test.
```

## Standalone Summary Mode

```markdown
**AI-generated review based on @D3Hunter’s standards; manual follow-up after comments are addressed.**

### Findings (highest risk first)

#### ⚠️ **[Major]** Missing compat guard for mixed-version path

**Why**
- mixed-version safety relies on explicit branch gating.

**Scope**
- pkg/meta/model/job.go compatibility branch

**Risk if unchanged**
- rolling upgrade can take unsupported behavior and fail unpredictably.

**Evidence**
- compatibility branch was added without version gate or fallback handling.

**Change request**
- gate this branch by version and add upgrade/downgrade coverage for N/N-1 combinations.

### Required validation before merge

1. Add mixed-version compatibility test for N/N-1 branch behavior.
2. Add deterministic cancellation lifecycle test that covers producer exit ordering.
```

## No-Findings Mode

```markdown
**AI-generated review based on @D3Hunter’s standards; manual follow-up after comments are addressed.**

### Findings

No findings.

### Residual risks / verification gaps

1. No large-scale performance run in this review context.
2. Mixed-version upgrade path validated by reasoning but not by dedicated integration case.

### Suggested validation

1. Run targeted upgrade/downgrade integration test for touched compatibility paths.
2. Run cancellation/retry stress test with deterministic hooks or failpoints.
```

## GitHub PR Single-Review Payload (`gh api`)

```json
{
  "event": "COMMENT",
  "body": "**AI-generated review based on @D3Hunter’s standards; manual follow-up after comments are addressed.**\n\n### Findings (highest risk first)\n\n1. ⚠️ **[Major]** Missing compat guard for mixed-version path\n   - **Scope:** pkg/meta/model/job.go compatibility branch\n   - **Risk if unchanged:** rolling upgrade can enter unsupported branch silently.\n\n### Required validation before merge\n\n1. Add mixed-version compatibility test for N/N-1 branch behavior.",
  "comments": [
    {
      "path": "pkg/meta/model/job.go",
      "line": 120,
      "side": "RIGHT",
      "body": "#### ⚠️ **[Major]** Missing compat guard for mixed-version path\n\n**Why**\n- mixed-version behavior must remain explicit during rolling upgrades.\n\n**Scope**\n- pkg/meta/model/job.go compatibility branch\n\n**Risk if unchanged**\n- upgrade can silently enter an unsupported path and produce hard-to-debug failures.\n\n**Evidence**\n- new branch lacks version gate/fallback while old path is still reachable in N/N-1 topology.\n\n**Change request**\n- add explicit version guard (or fallback path) and include an N/N-1 compatibility test."
    }
  ]
}
```
