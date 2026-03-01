---
name: review-upgrade-compatibility-and-test-determinism
description: Use when reviewing pull requests for API, schema, protocol, upgrade/downgrade compatibility, migration safety, and test determinism risks before merge.
---

# Review Compatibility, Upgrade Safety, and Test Determinism

## Overview

Use this skill to identify compatibility and test-determinism risks in behavior-changing pull requests.
Focus on backward/forward compatibility, rolling upgrade and rollback safety, migration correctness, and whether tests provide deterministic evidence for changed behavior.

This skill covers compatibility and test-determinism discovery only.
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

1. Scope the compatibility surface
   - Use `code_path` as the working directory.
   - Load and review changes from `diff_filename` as the primary review scope.
   - Identify changed compatibility surfaces: API contracts, protocol payloads, serialization formats, storage/on-disk formats, config keys, migration scripts, and release/runbook docs.
   - Identify changed validation surfaces: unit, integration, e2e, upgrade/downgrade, migration, failure-path, and determinism tests.

2. Run full checklist pass
   - Use every section in [references/compatibility-and-test-determinism-checklist.md](references/compatibility-and-test-determinism-checklist.md).
   - Do not skip sections; mark `N/A` only with a concrete, diff-tied reason.

3. Evaluate potential issues with objective evidence
   - Confirm at least one objective signal:
     - unversioned contract or protocol break
     - backward compatibility gap for mixed-version clusters without explicit guard
     - bootstrap or versioned metadata mutation that is not append-only and lacks proven migration safety
     - rolling upgrade/downgrade behavior change without explicit fallback or version gating
     - migration/rollback path missing safeguards
     - migration path is not idempotent/retry-safe under partial failure
     - incompatibility path silently falls back instead of returning an actionable error
     - mixed-version behavior not covered by tests or explicit guarantees
     - defaults/unknown-field handling that breaks forward/backward compatibility
     - deterministic-test anti-patterns (sleep-based sync, wall-clock dependence, unstable ordering)
     - test changes mix multiple scenarios into one case, reducing failure isolation
     - missing failure-path/concurrency coverage for changed logic
   - If evidence is weak, request targeted validation instead of asserting a defect.

4. Assign severity for handoff
   - `Blocker`: high-confidence incompatibility or determinism failure likely to break upgrade/rollback safety, data integrity, or production correctness.
   - `Major`: high-confidence compatibility or test-quality risk with meaningful user or operational impact.
   - `Minor`: localized compatibility or determinism gap with limited blast radius.
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
- Keep review latency low by relying on diff evidence, compatibility reasoning, and deterministic-test design checks.

## Review Depth Rules

- Do not emit a no-findings conclusion until every checklist section is passed or explicitly `N/A`.
- Treat unversioned breaking changes across API/protocol/storage formats as high risk by default.
- Treat migration/rollback assumptions as insufficient unless downgrade behavior and restart safety are explicit.
- Treat mixed-version and upgrade sequencing gaps as high-risk operational defects for distributed systems.
- Treat flaky-test patterns in changed critical paths as reliability risks, not style-only issues.
- Prefer concrete validation requests when confidence is medium or low.

## References

- Compatibility and determinism checklist:
  - [references/compatibility-and-test-determinism-checklist.md](references/compatibility-and-test-determinism-checklist.md)
- Output rendering contract:
  - [review-output-format/SKILL.md](../review-output-format/SKILL.md)
