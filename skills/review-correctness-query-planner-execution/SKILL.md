---
name: review-correctness-query-planner-execution
description: Use when reviewing pull requests for query semantics, planner/optimizer correctness, execution-engine behavior, and behavior-preservation regression risks before merge.
---

# Review Correctness: Query, Planner, and Execution

## Overview

Use this skill to identify behavioral correctness issues in query/planner/execution changes.
Focus on domain behavior, control-flow semantics, SQL/parser/binder/planner/executor correctness, and behavior-preservation regressions.

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

1. Scope behavioral correctness surface
   - Use `code_path` as the working directory.
   - Load and review changes from `diff_filename` as the primary review scope.
   - Identify changed behavioral boundaries: domain logic, control flow, input/output contracts, parser/binder/planner logic, and execution operators.
   - Expand each touched behavior block beyond the hunk before concluding:
     - open the full changed function body
     - open all callers and all callees when they participate in state/token/operator handoff
     - include unchanged branches that share state flags, offsets, or fallback paths

2. Run full checklist pass
   - Use every section in [references/query-planner-execution-checklist.md](references/query-planner-execution-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Run high-risk trigger gate for parser/scanner and reverse/forward scan paths
   - Activate this gate when any changed path touches tokenization/framing/splitting/chunked reads/reverse scans/fallback parsing/state flags.
   - Mandatory boundary matrix in this gate:
     - framing token: delimiter-only (`""`) vs non-empty content
     - carry state: pending/partial block empty vs non-empty
     - scan direction/path: reverse vs forward (or equivalent alternate reader paths)
   - Include at least one adversarial scenario where a chunk ends exactly at the delimiter and the next chunk continues the same logical record.
   - Verify framing artifacts cannot be promoted into record content while a partial block is in progress.
   - Verify fallback/error branches do not reset state flags on framing-only artifacts.

4. Build cross-function traces for changed behavioral boundaries
   - For parser/scanner/token-stream changes: trace at least one end-to-end record path from producer to consumer, including boundary tokens (`""`, delimiter-only, partial records across chunks/files).
   - For planner/rewrite/pushdown changes: trace at least one end-to-end operator path and verify early-return branches preserve required operators instead of silently dropping them.
   - Capture concrete handoff assumptions between functions (for example: token shape, ordering, offset semantics, state-flag transitions).
   - Keep an internal trace table with at least:
     - one normal-path row
     - one boundary-path row
     - state snapshots before/after each handoff (`pending`, flags, offsets, output emission decision)

5. Evaluate each potential issue with evidence
   - Confirm at least one objective signal:
     - code-path contradiction with requirements/invariants
     - semantic mismatch between query stages or execution paths
     - boundary/edge-case handling gap
     - concrete behavior regression scenario
     - trace-table state contradiction (for example: framing artifact changes semantic state)
   - If evidence is weak, request targeted validation instead of asserting a defect.

6. Assign severity for handoff
   - `Blocker`: likely incorrect results, semantic corruption, or major contract break.
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
- Prioritize behavioral correctness risk over style/structure feedback.
- For non-trivial findings, include at least one concrete scenario (`input/condition -> incorrect outcome`).
- For token/streaming/reverse-scan diffs, do not conclude until chunk/file boundary matrix checks are explicitly completed.
- For pushdown/rewrite diffs, do not conclude until operator-preservation checks (including early-return branches) are explicitly completed.
- For parser/scanner tokenization changes, do not conclude until unchanged neighboring fallback/state-transition branches are inspected.
- No-findings output is forbidden when the internal boundary trace table is missing or incomplete.
- If uncertain, ask for focused tests/validation rather than making a hard claim.

## References

- Query/planner/execution checklist:
  - [references/query-planner-execution-checklist.md](references/query-planner-execution-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
