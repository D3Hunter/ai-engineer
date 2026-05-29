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
   - Expand each touched state boundary beyond the hunk before concluding:
     - open the full changed function body
     - open all callers and all callees when they exchange markers, sentinels, offsets, or partial-state buffers
     - include unchanged fallback branches that can mutate or reset state flags

2. Run full checklist pass
   - Use every section in [references/state-schema-transaction-checklist.md](references/state-schema-transaction-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Run high-risk framing/state gate for chunked parsing or stateful ingestion
   - Activate this gate when touched code includes framing/tokenization/splitting/chunked reads/reverse scans/state flags/fallback parsing.
   - Mandatory boundary matrix in this gate:
     - framing token: delimiter-only (`""`) vs non-empty content
     - carry state: partial/pending block empty vs non-empty
     - path parity: reverse vs forward (or equivalent alternate ingestion paths)
   - Include at least one adversarial case where chunk N ends at delimiter and chunk N+1 continues the same logical record.
   - Verify delimiter-only artifacts cannot trigger semantic state transitions or state resets while a logical record is in progress.
   - Verify fallback/error branches cannot silently drop valid records or mutations after framing artifacts.

4. Build cross-function traces for changed state boundaries
   - Trace at least one full mutation/read path across function boundaries, including handoff assumptions (ordering, sentinel values, partial state markers).
   - When parsing or chunked ingestion touches persisted/stateful behavior, include one boundary trace (delimiter-only token, split record, or cross-file boundary) and verify it cannot produce illegal intermediate state.
   - For transaction/state-machine changes, verify early returns preserve atomicity/isolation invariants and do not bypass required cleanup or state transitions.
   - Keep an internal trace table with at least:
     - one normal-path row
     - one boundary-path row
     - state snapshots before/after each handoff (`pending`, flags, offsets, emission/drop decision)

5. Evaluate each potential issue with evidence
   - Confirm at least one objective signal:
     - illegal state transition or partial-update inconsistency
     - atomicity/isolation/transaction semantic mismatch
     - schema/index semantic mismatch causing incorrect persisted/observed outcomes
     - concrete state-oriented regression scenario
     - trace-table state contradiction caused by framing artifact handling
   - If evidence is weak, request targeted validation instead of asserting a defect.

6. Assign severity for handoff
   - `Blocker`: likely integrity break, incorrect persisted state, or major transactional correctness break.
   - `Major`: high-confidence correctness risk with meaningful user or operational impact.
   - `Minor`: localized correctness gap with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

7. Prepare findings payload
   - One issue per finding.
   - Capture: `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
   - Keep scope concrete (`path:line`, module, branch, or scenario boundary).

8. Required output handoff
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
- For stateful parser/scanner/serialization changes, do not conclude until boundary-handoff checks are explicitly completed.
- For transaction/state-machine changes, do not conclude until early-return and rollback/cleanup preservation checks are explicitly completed.
- For stateful framing/parser changes, do not conclude until unchanged neighboring fallback/state-transition branches are inspected.
- No-findings output is forbidden when the internal boundary trace table is missing or incomplete.
- If uncertain, ask for focused tests/validation rather than making a hard claim.

## References

- State/schema/transaction checklist:
  - [references/state-schema-transaction-checklist.md](references/state-schema-transaction-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
