---
name: d3hunter-pr-reviewing
description: Use when reviewing behavior-changing pull requests where correctness, compatibility, failure semantics, concurrency safety, and test adequacy need a structured second-opinion check.
---

# PR Reviewing (D3Hunter Style)

## Overview

Review for correctness and operational safety first, then maintainability.

The comment style is concise and action-oriented:
- ask direct questions when intent is unclear
- propose a concrete alternative when possible
- request tests for risk-bearing behavior
- use small inline suggestion blocks for local rewrites

Use [references/phrase-bank.md](references/phrase-bank.md) as a required tone source before drafting final comments.

## When To Use

Use this skill when a PR likely changes behavior and needs a structured
second-opinion pass.

Typical triggers:
- touches versioned metadata, bootstrap, or migration paths
- changes retry/cancel/context/lifecycle behavior
- changes concurrency, locking, or task scheduling flow
- changes compatibility behavior across upgrade/downgrade or mixed-version nodes
- modifies failure classification, logging/observability, or fallback paths
- changes tests for critical behavior, negative paths, or determinism guarantees

## When Not To Use

Do not use this skill as the primary workflow when:
- the request is purely mechanical formatting/lint cleanup with no behavior impact
- the diff is fully generated code where manual style feedback adds little value
- changes are typo-only or wording-only and do not affect business semantics

In those cases, keep feedback minimal and mechanical.

## Review Order (Default Sequence)

1. Correctness and invariants
2. Compatibility and upgrade safety
3. Code structure, package boundaries, and duplication
4. Failure semantics and observability
5. Concurrency, context, and lifecycle
6. Scope and complexity
7. Performance and scaling
8. API clarity and naming
9. Comments and intent documentation
10. Test quality and coverage

## Risk-Adaptive Entry (Hotspot First)

Use this fast-path before the full checklist when the PR is large or high risk.

Hotspot activation signals:
- touches `pkg/ddl`, `pkg/meta`, `pkg/session/bootstrap`, `pkg/disttask`, `pkg/lightning`
- touches transaction/lock/retry/cancel behavior
- spans many files/packages and needs quick risk triage

Hotspot pass:
1. Identify hotspot files/modules first.
2. Prioritize checks `1, 2, 3, 4, 5, 7, 10` in those hotspots.
3. If Blocker/Major evidence appears, report early with concrete scope and evidence.
4. Then complete the full `1 -> 10` default sequence for the entire diff (including hotspot files).
5. Before posting final output, verify each hotspot file/module has at least one pass over all `1 -> 10` categories (or mark explicit `N/A` for category/file pairs that truly do not apply).

## Review Workflow (Execution Checklist)

Copy this checklist and track progress:

```text
Review Progress:
- [ ] Step 1: Triage diff scope (behavioral vs mechanical-only changes) and identify hotspots
- [ ] Step 2: If hotspot-eligible, run Hotspot First pass; then run full Review Order (1 -> 10) across the entire diff (hotspots + non-hotspots) using `references/checklist-by-category.md`
- [ ] Step 3: Apply Evidence Gate and Confidence-to-Action Matrix for each non-trivial finding
- [ ] Step 4: Run D3Hunter wording pass using [references/phrase-bank.md](references/phrase-bank.md) for each drafted finding
- [ ] Step 5: Select output mode (Threaded Review Mode vs Inline Comment Mode vs Standalone Summary Mode)
- [ ] Step 6: Assign severity and include required rubric fields in posted output
- [ ] Step 7: Produce output using Review Output Contract
```

Stop conditions (do not proceed to prescriptive feedback until resolved):
- no objective signal for a non-trivial issue -> ask a clarifying question instead of prescribing a fix
- cannot name concrete scope (`file/line/module`) -> gather more evidence first
- cannot state concrete risk if unchanged -> downgrade to suggestion/question
- behavior changes are not test-backed and cannot be reasoned from diff -> require targeted validation before merge
- any required category checks in the Review Order pass are incomplete -> do not post final output

## Review Output Contract

Use this contract for all final review output.

### Global Rules (all output modes)

- **Add this exact bold attribution line once in summary sections only:** `**AI-generated review based on @D3Hunter’s standards; manual follow-up after comments are addressed.**`
- **Do not repeat the attribution line inside per-finding items/comments** (for example, `comments[]` entries in a single GitHub review object).
- **One finding = one actionable issue.**
- **Sort by risk:** present highest-risk findings first.
- **Tone guardrail:** each finding must use at least one adapted stem from [references/phrase-bank.md](references/phrase-bank.md) (opener or change-request line).
- **No-findings gate:** do not output `No findings.` unless the full Review Order pass (`1 -> 10`) is completed.
- **Non-trivial findings must include severity plus all 5 rubric fields:** `Why`, `Scope`, `Risk if unchanged`, `Evidence`, `Change request`.
- **Markdown structure is required:** use section titles (`###`/`####`) and bold field labels (`**Why**`, `**Scope**`, etc.) exactly as shown in templates.
- **Severity line format is required:** use emoji + bold severity tag (`🚨 **[Blocker]**`, `⚠️ **[Major]**`, `🟡 **[Minor]**`, `ℹ️ **[Info]**`, `🧹 **[Nit]**`).
- **Nit/Info findings can be shorter,** but must still be explicit about scope and requested change.

Canonical templates and payload examples are in:
- [references/output-examples.md](references/output-examples.md)

Shared finding structure for non-trivial findings:
- `Severity` line (`<emoji> **[Severity]** <short title>`)
- `Why`
- `Scope`
- `Risk if unchanged`
- `Evidence`
- `Change request`

### Inline Comment Mode

Use when posting direct line-level comments without a summary thread.

Requirements:
- one finding = one actionable issue
- each non-trivial finding uses severity + the full 5-field rubric above
- Nit/Info findings stay short but explicit about scope and ask
- do not prepend the attribution line in individual inline comment bodies
- template: [references/output-examples.md](references/output-examples.md)

### Threaded Review Mode (default when platform supports replies)

#### Top-level summary comment (exactly one)

- start with `Findings (highest risk first)`
- include a concise index only (`severity`, `title`, `scope`, `risk if unchanged` in one line per finding)
- do not expand the full severity + 5-field rubric in the top-level summary
- end with `Required validation before merge`
- template: [references/output-examples.md](references/output-examples.md)

#### Sub-comments under the summary thread

- post one sub-comment per finding
- one finding = one actionable issue
- non-trivial findings must include severity + full 5-field rubric (`Why`, `Scope`, `Risk if unchanged`, `Evidence`, `Change request`)
- Nit/Info findings may be shorter but must keep clear scope and ask
- template: [references/output-examples.md](references/output-examples.md)

#### GitHub PR submission contract (required when posting via `gh api`)

- create exactly one review object via `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`
- set summary content in review `body` (use the top-level summary template, including the attribution line once)
- put each finding in a separate item in `comments[]` (one finding = one inline comment object)
- do not include the attribution line inside `comments[]` item bodies
- submit once with `event=COMMENT`; do not post one review per finding
- if any finding has no valid inline anchor, keep it in summary body and still submit one review object
- payload shape example: [references/output-examples.md](references/output-examples.md)

### Standalone Summary Mode (single comment fallback)

Use when reply threads/sub-comments are unavailable, or when a single-summary output is explicitly requested.

Requirements:
- start with `Findings (highest risk first)`
- list findings in risk order
- every non-trivial finding includes severity + the same 5 rubric fields used in Inline Comment Mode
- end with `Required validation before merge` and concrete test/verification items
- template: [references/output-examples.md](references/output-examples.md)

### No-findings Mode

Required output:
- write `No findings.`
- include `Residual risks / verification gaps`
- include `Suggested validation`
- only use this mode after the full Review Order pass (`1 -> 10`) is completed
- template: [references/output-examples.md](references/output-examples.md)

## Core Checklist

Use `1 -> 10` as the default pass order for every behavior-changing review.

Detailed checks, heuristics, and phrase stems live in:
- [references/checklist-by-category.md](references/checklist-by-category.md)
- [references/phrase-bank.md](references/phrase-bank.md)

Quick category index:
1. Correctness and invariants
2. Compatibility and upgrade safety
3. Code structure, encapsulation, and duplication
4. Failure semantics and observability
5. Concurrency, context, and lifecycle
6. Scope and complexity
7. Performance and scaling
8. API clarity and naming
9. Comments and intent documentation
10. Tests and determinism

## D3Hunter Wording Pass (Required)

Run this pass before posting any comment:

1. Select one stem family in [references/phrase-bank.md](references/phrase-bank.md): `clarify intent`, `request change`, `tests and validation`, `comments and rationale`, or `compatibility and scale`.
2. Adapt one stem to the exact code scope and evidence from the current diff. Do not leave generic wording.
3. Keep the opening short and direct (for example: `why`, `can we`, `please add`, `seems no need`), then provide full rubric fields for non-trivial findings.
4. Keep one comment to one actionable issue. Split comments if there are multiple asks.
5. Avoid robotic repetition: if the same stem appears in nearby comments, switch to another stem from the same family.

## Finding Decision Pipeline (Single Flow)

Use this pipeline for every non-trivial finding. Do not skip steps.

### Confidence-to-Action Matrix

| Confidence | Minimum evidence bar | Allowed action | Default severity band | Merge stance |
| --- | --- | --- | --- | --- |
| High | clear objective evidence + concrete risk if unchanged | prescriptive change request | Blocker or Major based on risk class | blocking when risk is correctness/safety/compatibility/lifecycle/performance critical |
| Medium | partial evidence + plausible risk | request targeted validation; avoid hard prescription unless validated | Major or Minor | non-blocking until validation confirms risk |
| Low | weak/unclear evidence or risk statement | ask clarifying questions only; no prescriptive fix | Info or Nit | non-blocking |

1. Scope one issue:
   - one finding = one actionable issue
   - if the issue is comment-related, decide first:
     - non-obvious/business-decision logic -> ask for a short `why` comment
     - comment only restates obvious workflow -> suggest removing it
     - changed branch condition/invariant with stale rationale -> request comment update
2. Apply Evidence Gate (false-positive guard):
   - before prescribing a fix, confirm at least one objective signal:
     - invariant mismatch
     - reproducible failing scenario (test/case/path)
     - contradiction between code path and expected behavior
     - measurable performance or scale risk
     - concrete structure/duplication smell visible in the diff
     - duplicate definition in one scope (for example duplicated `select $$` fixture entry) with overwrite/shadowing risk
   - if no objective signal is available, ask a clarifying question first and stop escalation
3. Assign confidence and action using the `Confidence-to-Action Matrix`:
   - if confidence changes after new evidence, update severity and requested action
4. Assign severity and merge policy:
   - Blocker: invariant break, correctness regression risk, data race risk, wrong failure model
     - action: must fix before merge
   - Major: strong package-boundary coupling, high-scale performance risk, cancellation/lifecycle bug, critical missing test
     - action: fix before merge, or document explicit justification with follow-up tracking
   - Minor: naming/placement/readability or low-risk cleanup
     - action: optional in current PR; may defer if acknowledged
   - Info: observation or low-risk concern worth validation
     - action: non-blocking; acknowledge and optionally track
   - Nit: tiny style/wording preference with negligible risk
     - action: fully optional; do not block merge
5. Format output with severity + the 5-field rubric (inline or summary):
   - `why`: why this matters (correctness, readability, testability, performance, maintainability)
   - `scope`: exact change boundary (line/block/file/module)
   - `risk if unchanged`: concrete consequence
   - `evidence`: observed behavior, contradiction, failing path, or measurable signal
   - `change request`: specific and actionable fix direction
6. Choose output mode and render using `Review Output Contract`:
   - Threaded Review Mode (default when reply threads exist): one top-level summary + per-finding sub-comments
   - Inline Comment Mode: direct line-level finding comments without a summary thread
   - Standalone Summary Mode: single-comment fallback when sub-comments/reply threads are unavailable or explicitly requested
7. Final summary contract:
   - list findings first, highest risk first
   - every non-trivial finding must include all required fields
   - end with required validation/tests before merge

## Comment Decision Flow

Comment-related decisions are handled in Step 1 of `Finding Decision Pipeline (Single Flow)`.
Do not run a separate decision path; keep one issue per finding.

## Comment Writing Rules

- Keep one comment to one actionable point.
- Phrase bank is mandatory input for wording: draft each comment with one adapted stem from [references/phrase-bank.md](references/phrase-bank.md).
- Prefer frequent D3Hunter starters when they match evidence: `why`, `can we`, `please`, `seems`, `maybe`.
- Use stems as scaffolding, not copy-paste text; always bind wording to concrete scope/risk/evidence.
- Prefer question + direction instead of vague criticism.
- Use imperative short form for clear requests.
- For repeated issues in nearby code, comment once and include explicit repeat scope (`path:line` list or block range).
- Use `suggestion` blocks only for small local changes.
- Extract by responsibility boundary, not line count alone.
- Avoid utility dumping; keep helpers near the dominant caller unless multi-package reuse is real.
- Prefer unexported helper methods first; export only when cross-package reuse is required.
- Add comments for non-obvious logic and business-driven branches, focusing on `why`.
- Avoid comments for plain workflow code that is already readable.
- Keep comments concise and durable; prefer intent/invariant over restating code.
- For Blocker/Major findings or summary output, expand shorthand into full rubric fields (`why/scope/risk/evidence/change request`).

## Compact Drafting Helper

Use this while drafting, then expand to full severity + 5-field rubric before posting:
- `Issue`: one sentence
- `Why`: one sentence
- `Scope`: one sentence
- `Evidence`: one sentence
- `Ask`: one sentence (`Ask` maps to `change request`)

Examples:
- `Issue: this branch is business-rule driven but has no rationale comment. Why: future changes may break compatibility silently. Change request: add a short why-comment with the decision/invariant.`
- `Issue: same validation logic appears in 3 places. Why: behavior drift and test duplication risk. Change request: extract one helper near the dominant caller and reuse it.`

## References

- category-level checklist and templates:
  - [references/checklist-by-category.md](references/checklist-by-category.md)
- phrase stems:
  - [references/phrase-bank.md](references/phrase-bank.md)
- output templates and examples:
  - [references/output-examples.md](references/output-examples.md)
