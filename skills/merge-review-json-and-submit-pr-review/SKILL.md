---
name: merge-review-json-and-submit-pr-review
description: Use when multiple `review-output-format` JSON files must be merged into one result and submitted as a single GitHub PR review where each finding becomes one inline `comments[]` item.
---

# Merge Review JSON And Submit PR Review

## Overview

Merge multiple JSON files produced by `review-output-format`, create one GitHub PR review payload, and submit it in one API call.

This skill guarantees:
- merged findings are sorted by severity (`Blocker`, `Major`, `Minor`, `Info`, `Nit`)
- each severity level is rendered with a dedicated emoji for fast scanning
- summary starts with an explicit AI-generated attribution and manual follow-up note
- findings summary is grouped by severity to avoid repeated risk labels on every line
- one finding maps to one `comments[]` object when an inline anchor is available
- summary body stays short and includes rollup counts
- any unanchored findings stay in summary body instead of being dropped

## Inputs

- `pr_link` (required)
  - full GitHub PR URL: `https://github.com/<owner>/<repo>/pull/<number>`
- `input_files` (required)
  - each file must follow `review-output-format`: top-level `{ "findings": [] }`
  - pass with repeated `--input` flags or `--input-glob`
- `merged_output` (optional)
  - default: `merged-review-output.json`
- `payload_output` (optional)
  - default: `github-review-payload.json`

Inline anchor resolution for each finding:
1. use `path` + `line` directly if present
2. otherwise parse from `scope` with `<path>:<line>`
3. if anchor cannot be resolved, keep finding in summary body

## Command

```bash
python3 ./merge-review-json-and-submit-pr-review/scripts/merge_and_submit_review.py \
  --pr-link "https://github.com/pingcap/tidb/pull/12345" \
  --input review-a.json \
  --input review-b.json \
  --merged-output merged-review-output.json \
  --payload-output github-review-payload.json
```

Use globs when needed:

```bash
python3 ./merge-review-json-and-submit-pr-review/scripts/merge_and_submit_review.py \
  --pr-link "https://github.com/pingcap/tidb/pull/12345" \
  --input-glob "outputs/reviews/*.json"
```

## Dry Run

Generate merged JSON and payload without posting:

```bash
python3 ./merge-review-json-and-submit-pr-review/scripts/merge_and_submit_review.py \
  --pr-link "https://github.com/pingcap/tidb/pull/12345" \
  --input-glob "outputs/reviews/*.json" \
  --dry-run
```

## Authentication

Submission requires GitHub CLI authentication:

```bash
gh auth status
```

If unauthenticated, run:

```bash
gh auth login
```

## Output

The script writes:
- merged findings JSON (`merged_output`)
- final GitHub payload (`payload_output`)

Then it prints one JSON result object with counts and submission status.
