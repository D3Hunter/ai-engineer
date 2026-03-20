---
name: review-correctness-state-schema-transaction
description: Use when reviewing pull requests for state integrity, schema/DDL/index correctness, transaction semantics, and state-preservation regression risks before merge.
---

# Review Correctness: State, Schema, and Transactions

## Overview

Use this skill to identify state-oriented correctness issues in behavior-changing pull requests.
Focus on state/data integrity, schema and index semantics, transaction correctness, numerical/time/locale correctness, and state-preservation regressions.

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

1. Scope state/schema/transaction correctness surface
   - Use `code_path` as the working directory.
   - Load and review changes from `diff_filename` as the primary review scope.
   - Identify changed state boundaries: mutations, transactional write sets, schema/DDL/index behavior, and numeric/time/locale data semantics.

2. Run full checklist pass
   - Use every section in [references/state-schema-transaction-checklist.md](references/state-schema-transaction-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Evaluate each potential issue with evidence
   - Confirm at least one objective signal:
     - illegal state transition or partial-update inconsistency
     - atomicity/isolation/transaction semantic mismatch
     - schema/index semantic mismatch causing incorrect persisted/observed outcomes
     - concrete state-oriented regression scenario
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Assign severity for handoff
   - `Blocker`: likely integrity break, incorrect persisted state, or major transactional correctness break.
   - `Major`: high-confidence correctness risk with meaningful user or operational impact.
   - `Minor`: localized correctness gap with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

5. Prepare findings payload
   - One issue per finding.
   - Capture: `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
   - Keep scope concrete (`path:line`, module, branch, or scenario boundary).

6. Required output handoff
   - After the correctness pass is complete, invoke [review-output-format](../review-output-format/SKILL.md).
   - Render final findings strictly with that skill's output contract.
   - Write that JSON to `output_filename`.

## Runtime Validation Policy

- Never execute project build commands during this review flow.
- Never execute project test commands during this review flow.
- Never run broad verification tasks (full suite, integration matrix, benchmarks) directly in this skill.
- If runtime confirmation is needed, request targeted validation with the minimal scenario and exact command, but do not run it yourself.
- Keep review latency low by relying on diff evidence, invariants, and local code-path reasoning.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Prioritize integrity and transactional risk over style/structure feedback.
- For non-trivial findings, include at least one concrete scenario (`state/input -> incorrect outcome`).
- If uncertain, ask for focused tests/validation rather than making a hard claim.

## References

- State/schema/transaction checklist:
  - [references/state-schema-transaction-checklist.md](references/state-schema-transaction-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
