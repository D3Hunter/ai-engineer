---
name: review-runtime-reliability-performance
description: Use when reviewing pull requests for failure semantics, concurrency lifecycle safety, and performance scalability risks before merge.
---

# Review Failure Semantics, Concurrency Lifecycle, and Performance

## Overview

Use this skill to identify reliability and scalability issues in behavior-changing pull requests.
Focus on failure contracts, retry/timeout/cancellation behavior, concurrency ownership and lifecycle discipline, and performance risks under realistic load.

This skill covers discovery only.
After findings are identified, hand off output rendering to [review-output-format](../review-output-format/SKILL.md).

This is a static-analysis-first review flow.
Do not run build/test commands directly as part of this skill.

## Input

This skill accepts exactly three input parameters:

- `code_path` (required): absolute path to the cloned codebase; this is the working directory for review.
- `diff_filename` (required): filename of the diff to review.
- `output_filename` (required): final output JSON filename for the rendered findings payload.

## Output

- Final output must be a file named exactly as `output_filename`.
- File content format is already defined by [review-output-format](../review-output-format/SKILL.md).
- Do not invent or emit an alternate output schema.

## Review Flow

1. Scope the review surface
   - Use `code_path` as the working directory.
   - Load and review changes from `diff_filename` as the primary review scope.
   - Identify changed boundaries that can fail or saturate: API handlers, async workers/jobs, scheduler loops, retry loops, queueing paths, lock/transaction paths, and external dependency calls.

2. Run full checklist pass
   - Use every section in [references/failure-concurrency-performance-checklist.md](references/failure-concurrency-performance-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.
   - Apply the focused prompt blocks in each category and reuse their comment templates when phrasing `change_request`.

3. Evaluate potential issues with objective evidence
   - Confirm at least one objective signal:
     - failure contract ambiguity or silent failure path
     - retry/idempotency/timeout mismatch with dependency behavior
     - cancellation, lifecycle, or synchronization race/leak risk
     - unbounded parallelism, queue growth, or overload collapse risk
     - measurable performance/scaling anti-pattern in hot paths
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Assign severity for handoff
   - `Blocker`: high-confidence data integrity/safety break, deadlock risk, destructive failure-mode bug, or collapse risk under expected load.
   - `Major`: high-confidence reliability/concurrency/performance risk with meaningful user or operational impact.
   - `Minor`: localized risk with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

5. Prepare findings payload
   - One issue per finding.
   - For each finding include:
     - `severity`
     - `title`
     - `why`
     - `scope`
     - `risk_if_unchanged`
     - `evidence`
     - `change_request`
   - Keep scope concrete (`path:line`, module, branch, or scenario boundary).

6. Required output handoff
   - After the checklist pass is complete, invoke [review-output-format](../review-output-format/SKILL.md).
   - Render final findings strictly with that skill's output contract.
   - Write that JSON to `output_filename`.

## Runtime Validation Policy

- Never execute project build commands during this review flow.
- Never execute project test commands during this review flow.
- Never run broad verification tasks directly in this skill.
- If runtime confirmation is needed, request targeted validation with a minimal scenario and exact command, but do not run it yourself.
- Keep review latency low by relying on diff evidence, failure-model reasoning, and local code-path context.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Prioritize failure-mode and lifecycle correctness over style feedback.
- For non-trivial findings, include at least one concrete scenario (`trigger/condition -> incorrect outcome`).
- Treat retry/idempotency mismatches and cancellation leaks as high-risk by default.
- Treat p99/tail-latency regressions and overload-path weaknesses as first-class risks.
- If uncertain, ask for focused validation rather than making a hard claim.

## References

- Failure/concurrency/performance checklist:
  - [references/failure-concurrency-performance-checklist.md](references/failure-concurrency-performance-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
