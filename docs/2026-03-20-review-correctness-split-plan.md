# Split `review-correctness` Into Two Faster Skills

## Summary
- Replace the monolithic correctness reviewer with two standalone correctness skills, each with a smaller checklist and tighter scope.
- Keep the overall PR review pipeline behavior the same, but update orchestration from 5 to 6 parallel reviewers.
- Use a dedup-first method: first remove overlap with existing runtime/compatibility reviewers, then split remaining correctness checks evenly.

## Public Interface Changes
- Remove legacy skill entrypoint at [skills/review-correctness/SKILL.md](/Users/jujiajia/playground/ai-engineer/skills/review-correctness/SKILL.md) (full replace, no compatibility shim).
- Add two new skill entrypoints (same 3-parameter interface as existing reviewers):
1. `review-correctness-query-planner-execution`
2. `review-correctness-state-schema-transaction`
- Keep input/output contract unchanged for both new skills:
1. Inputs: `code_path`, `diff_filename`, `output_filename`
2. Output: JSON formatted by `review-output-format`
- Update orchestrator at [skills/orchestrate-github-pr-review/SKILL.md](/Users/jujiajia/playground/ai-engineer/skills/orchestrate-github-pr-review/SKILL.md) to dispatch 6 reviewers and include 2 correctness output files.
- `review_outputs` remains a list in orchestration summary JSON, now with 6 entries (accepted change).

## Implementation Changes
1. Build an explicit section mapping from [correctness-checklist.md](/Users/jujiajia/playground/ai-engineer/skills/review-correctness/references/correctness-checklist.md) before editing:
   - `Query/Planner/Execution` skill owns: Business logic, control-flow correctness, input/output semantics, positional shape correctness, SQL semantics, parser/binder, optimizer/planning, execution-engine correctness, behavior-preservation regression traps.
   - `State/Schema/Transaction` skill owns: State/data integrity, DDL/schema correctness (non-upgrade-operational parts), index correctness (semantic/data-integrity parts), transaction correctness (semantic/integrity parts), numerical/time/locale correctness, state-oriented regression traps.
   - Move out of correctness entirely (do not duplicate): Locking/MVCC/concurrency lifecycle checks to `review-runtime-reliability-performance`; external interaction compatibility/fallback checks to runtime/compatibility skills.
2. Create two new checklist reference files with dedup-first scope:
   - Each checklist should be concise and high-signal.
   - Each checklist must require full-pass or explicit `N/A` with diff-tied reason.
   - Each checklist must include concrete evidence gate + severity mapping + output handoff rules.
3. Create two new `SKILL.md` files mirroring existing review skill conventions:
   - Keep static-analysis-only policy.
   - Keep identical finding fields and severity taxonomy.
   - Keep mandatory handoff to `review-output-format`.
4. Update orchestration skill details:
   - Replace single `review-correctness` in “Direct Skill Invocation Rule” with the two new correctness skills.
   - Update parallel dispatch contract to 6 subagents.
   - Update fixed output filenames and invocation examples.
   - Update merge step input file list to include both correctness JSON files.
   - Update determinism/failure-handling wording from “5 review skills” to “6 review skills” consistently.
5. Remove stale references to removed `review-correctness` skill across repository docs/skill links.
6. Keep merge skill unchanged unless a hardcoded assumption of 5 inputs is discovered (expected none, since `input_files` is already variable-length).

## Test Plan
1. Static consistency checks:
   - Verify no stale references to `review-correctness` remain.
   - Verify all intra-skill links resolve to existing files.
   - Verify both new skills declare identical input/output contracts to other category reviewers.
2. Checklist balance/coverage checks:
   - Produce a mapping artifact during implementation: each old checklist section marked as `moved to new skill A`, `moved to new skill B`, `owned by runtime/compat`, or `dropped as low-yield overlap`.
   - Ensure the two new checklists are approximately balanced by item count after dedup-first split (target difference <= 15%).
3. Output contract checks:
   - Run both new reviewers on the same sample diff and confirm each writes valid review-output-format JSON.
   - Confirm merge step succeeds with 6 input files and keeps severity ordering and one-finding-per-issue behavior.
4. Pipeline behavior checks:
   - Run orchestration on representative PRs and confirm end-to-end still prepares, reviews, merges, and cleans up with unchanged flow semantics.
5. Performance validation (relative metric):
   - Compare old vs new on identical PR diffs.
   - Success criteria: reduced correctness-review wall-clock time and fewer/zero hang incidents in correctness category reviewers.

## Assumptions and Defaults
- “Split” means full replacement of old correctness skill, not wrapper/sub-skill nesting.
- Orchestrator can emit 6 review outputs with no downstream contract break beyond list length.
- Dedup-first sizing is the governing rule; no fixed arbitrary item count is set before overlap mapping.
- Overlap ownership is intentional: concurrency/failure-lifecycle belongs to runtime reviewer; upgrade/mixed-version compatibility belongs to compatibility reviewer.
