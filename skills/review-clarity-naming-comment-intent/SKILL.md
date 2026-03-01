---
name: review-clarity-naming-comment-intent
description: Use when reviewing pull requests for naming clarity, domain vocabulary consistency, behavior-signaling names, comment intent quality, and public-surface minimization across code and interfaces before merge.
---

# Review Clarity, Naming, and Comment Intent

## Overview

Use this skill to identify clarity, naming, and documentation-intent issues in behavior-changing pull requests.
Focus on whether names and nearby docs/comments communicate domain intent, side effects, and contract semantics clearly to code consumers.

This skill covers clarity, naming, and comment/documentation discovery only.
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
   - Identify changed interface/contract surfaces (HTTP endpoints, RPC methods, exported SDK/service methods, request/response schema fields, error codes/types, config flags, and public module contracts).
   - Identify changed comment/doc surfaces (public docs, docstrings, TODO/FIXME/HACK notes, module headers, and test intent comments).
   - Map each changed identifier to its domain concept and behavior.

2. Run full checklist pass
   - Use every section in [references/clarity-naming-comment-intent-checklist.md](references/clarity-naming-comment-intent-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Evaluate potential issues with objective evidence
   - Confirm at least one objective signal:
     - same concept has multiple names across code or interface surfaces
     - same name has multiple meanings depending on context
     - naming hides or contradicts side effects
     - endpoint/method names conflict with HTTP or lifecycle semantics
     - parameter/field names are ambiguous about unit, scope, polarity, or optionality
     - error naming conflates categories (for example authn vs authz, transport vs domain)
     - public/exported naming surface grows without clear consumer need
     - docs/examples/schema naming diverges from implementation
     - comments restate mechanics but omit intent/invariants
     - comment text contradicts current code behavior
     - public behavior changes lack side-effect/error contract docs
     - TODO/FIXME/HACK notes lack owner/ticket/removal condition
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Run naming and surface acceptance gates
   - Ensure names are domain-specific and unambiguous.
   - Ensure names truthfully communicate side effects, idempotency, and mutability.
   - Ensure exported/public symbols are minimal for the use case; flag symbols that can be un-exported/internalized.
   - Ensure comments explain intent (`why`) for non-obvious behavior and avoid narration-only noise.

5. Assign severity for handoff
   - `Blocker`: high-confidence naming ambiguity or semantic mismatch that can cause destructive misuse, security/privacy mistakes, or breaking contract behavior.
   - `Major`: high-confidence naming/clarity/comment-intent issue with meaningful integration, maintenance, or operability impact.
   - `Minor`: localized naming ambiguity with limited blast radius.
   - `Info` / `Nit`: low-risk observation, clarification, or polish.

6. Prepare findings payload
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

7. Required output handoff
   - After the checklist pass is complete, invoke [review-output-format](../review-output-format/SKILL.md).
   - Render final findings strictly with that skill's output contract.
   - Write that JSON to `output_filename`.

## Runtime Validation Policy

- Never execute project build commands during this review flow.
- Never execute project test commands during this review flow.
- Never run broad verification tasks directly in this skill.
- If runtime confirmation is needed, request targeted validation with a minimal scenario and exact command, but do not run it yourself.
- Keep review latency low by relying on diff evidence, naming-contract reasoning, and local code-path context.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Prioritize externally consumed naming and heavily reused internal contracts over purely local helper naming.
- Treat side-effect-masking names as high-risk even when implementation is functionally correct.
- Treat domain-term drift (`customerId` vs `clientId`) as a correctness-of-contract issue for consumers.
- Prefer explicit rename requests with old-to-new mapping when ambiguity is systemic.
- Flag newly exported symbols unless cross-package or external consumer need is concrete.
- Treat stale or contradictory contract comments as correctness-of-intent risk, not stylistic nit only.
- Flag security/concurrency-sensitive logic that lacks rationale comments near enforcement points.

## References

- Clarity, naming, and comment-intent checklist:
  - [references/clarity-naming-comment-intent-checklist.md](references/clarity-naming-comment-intent-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
