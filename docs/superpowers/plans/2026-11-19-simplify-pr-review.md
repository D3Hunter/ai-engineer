# Simplify PR Review Implementation Plan

**Goal:** Apply the approved adaptive review design to the consolidated skill and its references.

**Architecture:** The lead owns preparation, risk selection, consolidation, delivery, and cleanup. Fresh reviewers provide independent coverage for substantial changes; focused references retain domain hazards without duplicating the common review contract.

**Scope:** Edit `skills/review-github-pr/` and align `review-skill-create-template.md`. Preserve pre-existing changes elsewhere. Keep static-only review and existing severity labels.

## Tasks

- [x] Capture the existing protocol's behavior on small, state-only, and incomplete/stale-head review scenarios.
- [x] Rewrite `SKILL.md` with adaptive delegation, a common evidence/reporting contract, and existing revision/submission/cleanup safeguards.
- [x] Shorten the four correctness/runtime/compatibility references; combine clarity and structure into `maintainability.md`; consolidate framing checks into `streaming-framing.md`.
- [x] Update the scope-extension template to use the common contract and conditional references.
- [x] Validate frontmatter and local links, inspect changes against the frozen starting snapshot, and verify unrelated files remain unchanged.
- [x] Run fresh behavioral checks and independent spec/quality review; address concrete failures before completion.

## Behavioral acceptance

- Small changes can be reviewed directly without fixed six-agent fan-out or exhaustive N/A reports.
- Substantial changes receive independent review when available, with specialists selected by risk and limitations disclosed.
- Transaction-only changes do not require delimiter traces; scanner changes retain pending/token/boundary/path checks and planner changes retain operator-preservation checks.
- Findings need concrete evidence and impact; naming preferences and intentional SQL fixture differences are not automatic defects.
- Missing assigned coverage or a changed PR head cannot silently produce a complete or stale posted review.
- Posting remains explicitly authorized, tied to the reviewed commit, and protected against duplicate retries. Cleanup removes only owned, unchanged temporary resources after reviewers finish.

## Validation limits

Synthetic workflow checks and document review verify the revised protocol. Equivalent defect recall, false-positive rates, and performance on real historical PRs require a separate comparative evaluation; do not claim them from this refactor.

## Observations

- Frozen-protocol baseline: both a docstring typo and a transaction-only change required six scope reviewers plus a merger. State review contained conflicting unconditional scanner trace requirements. Failed coverage and changed heads correctly prevented posting.
- Unassisted-agent baseline: a static review of a temporary query-adapter fixture found all three seeded regressions (dropped remote-scan limit, cleared pending record bytes, and an incompatible catalog status) without flagging intentional SQL fixture variations. The refactor should preserve that result; this small example does not demonstrate recall on real PRs.
- Forward fixture check: a fresh reviewer using the rewritten skill found the same three seeded defects and accepted the intentional SQL fixture variations. No fixture code or tests were executed.
- Forward workflow check: direct review for the typo, relevant state guidance without framing obligations for the transaction fix, recovery of missing coverage and current-head revalidation before posting, disclosed reduced independence when agents are unavailable, and no automatic extraction/SQL-deduplication finding.
- Spec review found a missing common-contract handoff to fresh reviewers. Added the skill path and explicit static-review/evidence/reporting instructions; the reviewer confirmed the gap resolved.
- Frontmatter validator, eight local Markdown links, whitespace checks, and the six-reference inventory passed. Hashes of 23 unrelated pre-existing files matched the starting snapshot.
- Final independent quality review found no actionable inconsistencies or lost critical domain safeguards.

## Approved reference regrouping

- [x] Rename query/planner/execution to `sql-semantics.md`, state/schema/transaction to `data-integrity.md`, and failure/concurrency/performance to `runtime-reliability.md`; align titles while retaining their guidance.
- [x] Split compatibility and test determinism into `compatibility.md` and `test-quality.md`, with independent selection triggers. Retain `maintainability.md` and `streaming-framing.md`.
- [x] Update the entrypoint routing and clarify that reviewer assignments can span references.
- [x] Verify all seven references are reachable, no active links use retired filenames, and all existing review bullets are preserved.

Regrouping validation: skill validator and whitespace checks passed; all nine local links resolve. Renamed reference bodies and all bullets from the split file are unchanged, as are the two retained references. Hashes of 24 unrelated files match the starting snapshot. Independent review found no material gaps and confirmed separate test-only routing plus combined references for rolling-upgrade state changes and planner/framing changes.
