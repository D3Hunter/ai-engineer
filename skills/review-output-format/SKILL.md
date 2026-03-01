---
name: review-output-format
description: Use when rendering review output, including severity ordering, required rubric fields, and mode-specific comment structure.
---

# Review Output Format

## Overview

Use this skill to format final review output after findings are already identified.
It defines required structure for review findings.

## Global Contract

- Output must be exactly one valid JSON object (no Markdown headings, lists, or code fences).
- The top-level object must include a `findings` array.
- Every review finding must appear exactly once inside `findings`.
- Do not repeat the attribution line inside individual finding objects.
- One finding = one actionable issue.
- Sort `findings` by risk (highest risk first).
- `severity` must be one of:
  - `Blocker`
  - `Major`
  - `Minor`
  - `Info`
  - `Nit`
- Non-trivial findings must include `severity` plus all 5 rubric fields:
  - `why`
  - `scope`
  - `risk_if_unchanged`
  - `evidence`
  - `change_request`
- `Info`/`Nit` findings can be shorter, but `scope` and `change_request` are still required.
- Tone guardrail: each finding should use at least one adapted stem from [phrase-bank](references/phrase-bank.md).
- Do not output a no-findings result unless the full review-category pass is complete.

Shared non-trivial finding object:
- `severity`
- `title`
- `why`
- `scope`
- `risk_if_unchanged`
- `evidence`
- `change_request`

Required top-level shape:

```json
{
  "findings": []
}
```

Example final output:

```json
{
  "findings": [
    {
      "severity": "Blocker",
      "title": "Transaction rollback can be skipped on context cancellation",
      "why": "An early return on canceled context occurs before rollback is guaranteed for the opened transaction.",
      "scope": "pkg/txn/retry.go:112",
      "risk_if_unchanged": "Open transactions may leak locks and trigger broad write failures under load.",
      "evidence": "In `runWithRetry`, the `ctx.Err()` return path runs before rollback is ensured in that retry branch.",
      "change_request": "Guarantee rollback for every opened transaction, including all early-return paths."
    },
    {
      "severity": "Major",
      "title": "Safety flag check is inverted for delete protection",
      "why": "The current condition permits deletes when safety mode is disabled, opposite to the expected guard behavior.",
      "scope": "service/delete_guard.go:47",
      "risk_if_unchanged": "Protected data can be deleted in environments that should block destructive operations.",
      "evidence": "Code path allows delete when `SafeDeleteEnabled` is false; product behavior requires deny-by-default in that state.",
      "change_request": "Invert the condition and add tests for both enabled and disabled flag modes."
    },
    {
      "severity": "Nit",
      "title": "Warning log omits request identifier",
      "scope": "api/handler/update_user.go:89",
      "change_request": "Add `request_id` to warning log fields to improve traceability."
    }
  ]
}
```
