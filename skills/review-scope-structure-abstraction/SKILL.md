---
name: review-scope-structure-abstraction
description: Use when reviewing pull requests for package cohesion, layer placement, method extraction, and duplication risks before merge.
---

# Review Code Structure, Encapsulation, and Duplication

## Overview

Use this skill to identify structure and maintainability issues in behavior-changing pull requests.
Focus on package boundaries, layer placement, extraction seams, abstraction discipline, scope containment, and duplicate definitions that can cause drift or shadowing.

This skill covers category-3 discovery only.
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
   - Derive or confirm a one-sentence PR objective and explicit out-of-scope boundary.
   - Map each touched file to that objective; flag any out-of-scope edits.
   - Identify touched packages/modules and classify each changed block by concern (planner, executor, scheduler, storage, test scaffolding, registry/definition table).

2. Run full category-3 checklist pass
   - Use every section in [references/structure-encapsulation-duplication-checklist.md](references/structure-encapsulation-duplication-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Evaluate potential issues with objective evidence
   - Confirm at least one objective signal:
     - package mixes unrelated concerns
     - logic is placed in the wrong layer
     - one block has 2+ responsibilities and should be extracted
     - repeated logic appears in 2+ call sites without a focused helper
     - single-use wrapper or abstraction adds indirection without clear reuse/clarity gain
     - exported/global utility is introduced for one-time local logic
     - PR mixes unrelated behavior changes, refactors, or drive-by cleanup
     - control-flow or state complexity increases (branch explosion, flag soup, hidden side effects)
     - same-scope definition collision or duplicated SQL fixture pattern
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Run scope and complexity acceptance gates
   - Use scope checks from the checklist to confirm:
     - each major hunk maps to the stated objective
     - blast radius is minimal for the defect being fixed
     - abstraction/API surface growth is justified by concrete reuse or testability needs
   - If acceptance gates fail, raise a finding and prefer splitting into staged PRs when appropriate.

5. Run duplicate-definition sweep when applicable
   - Trigger this sweep whenever duplication-prone structures are touched.
   - Enumerate changed definition sites:
     - map literals and map assignments
     - switch/case labels and parser token branches
     - registry/table-driven test entries
     - raw SQL fixture literals in tests and parser-related code
   - Compare same-scope entries for collisions:
     - identical keys/labels/IDs in one scope
     - semantically duplicated SQL fixtures that differ only by case/whitespace/quoting
   - Normalize SQL fixture text before duplicate comparison:
     - trim spaces and collapse repeated internal whitespace
     - compare case-insensitively for SQL keywords
     - treat placeholder-heavy patterns (for example, repeated `select $$`) as high-risk duplicates
   - If duplicates exist, raise a finding with concrete scope:
     - include both definition sites (`path:line` for each)
     - explain shadowing/override/coverage-blindspot risk
   - If no duplicates exist, keep an explicit internal review note that the sweep was completed.

6. Assign severity for handoff
   - `Blocker`: definition collision/shadowing or severe structure regression with high confidence and immediate merge risk.
   - `Major`: high-confidence layering/encapsulation/duplication/scope risk with meaningful maintenance or regression impact.
   - `Minor`: localized structure issue with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

7. Prepare findings payload
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

8. Required output handoff
   - After the category-3 pass is complete, invoke [review-output-format](../review-output-format/SKILL.md).
   - Render final findings strictly with that skill's output contract.
   - Write that JSON to `output_filename`.

## Runtime Validation Policy

- Never execute project build commands during this review flow.
- Never execute project test commands during this review flow.
- Never run broad verification tasks directly in this skill.
- If runtime confirmation is needed, request targeted validation with a minimal scenario and exact command, but do not run it yourself.
- Keep review latency low by relying on diff evidence and static code-path reasoning.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Prioritize structure risks that affect correctness, coupling, testability, or long-term drift.
- Treat intentional duplication as acceptable only when rationale is explicit (why now, and when to converge).
- Flag wrappers that obscure timeout/retry/cancellation/transaction semantics.
- Prefer local/private helpers for one-callsite logic unless a multi-caller contract is clear.
- Flag out-of-scope changes in bugfix PRs when they increase review risk or blur regression attribution.
- For duplicate-definition findings, always provide both scopes and concrete impact.

## References

- Category-3 checklist and sweep procedure:
  - [references/structure-encapsulation-duplication-checklist.md](references/structure-encapsulation-duplication-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
