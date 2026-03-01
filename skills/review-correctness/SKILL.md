---
name: review-correctness
description: Use when reviewing pull requests for functional correctness, invariant preservation, state integrity, concurrency safety, and regression risk before merge.
---

# Review Correctness

## Overview

Use this skill to identify correctness issues in behavior-changing pull requests.
Focus on whether the code does the right thing under normal, edge, and failure conditions.

This skill covers correctness discovery only.
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

1. Build expected behavior model
   - Use `code_path` as the working directory.
   - Load and review changes from `diff_filename` as the primary review scope.
   - Extract requirements, preconditions, and invariants before judging implementation.
   - Capture feature-flag ON/OFF expectations and contract assumptions.

2. Run full checklist pass
   - Use every section in [references/correctness-checklist.md](references/correctness-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Evaluate each potential issue with evidence
   - Confirm at least one objective signal:
     - code-path contradiction with requirements/invariants
     - unsafe state transition or partial update risk
     - boundary/edge-case handling gap
     - concurrency/retry/replay correctness risk
     - external interaction contract violation
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Assign severity for handoff
   - `Blocker`: likely incorrect results, corruption, or integrity/safety break.
   - `Major`: high-confidence correctness risk with meaningful user or operational impact.
   - `Minor`: localized correctness gap with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

5. Prepare findings payload
   - One issue per finding.
   - Capture: `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
   - Keep scope concrete (`path:line`, module, branch, or scenario boundary).

6. Required output handoff
   - After the correctness pass is complete, invoke [review-output-format](../review-output-format/SKILL.md).
   - Pass `final_output_json_filename` to that handoff.
   - Render final findings strictly with that skill's output contract, then write that JSON to `final_output_json_filename`.

## Runtime Validation Policy

- Never execute project build commands during this review flow.
- Never execute project test commands during this review flow.
- Never run broad verification tasks (full suite, integration matrix, benchmarks) directly in this skill.
- If runtime confirmation is needed, request targeted validation with the minimal scenario and exact command, but do not run it yourself.
- Keep review latency low by relying on diff evidence, invariants, and local code-path reasoning.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Prioritize behavioral risk over style/structure feedback.
- For non-trivial findings, include at least one concrete scenario (`input/condition -> incorrect outcome`).
- If uncertain, ask for focused tests/validation rather than making a hard claim.

## References

- Extended correctness checklist:
  - [references/correctness-checklist.md](references/correctness-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
