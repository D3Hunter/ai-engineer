---
name: orchestrate-github-pr-review
description: Use when given a GitHub pull request link and needing an end-to-end multi-skill review pipeline that prepares a PR worktree, runs category reviews in parallel, submits one merged PR review, and then cleans up.
---

# Orchestrate PR Review Pipeline

## Overview

Run a full PR review pipeline by orchestrating existing skills directly.

This skill must:
- prepare PR diff worktree metadata
- run 5 review skills in parallel subagents
- merge and submit one PR review
- clean up the temporary worktree

Do not call scripts from this skill. Invoke the skills themselves.

## Inputs

- `pr_link` (required)
  - GitHub PR URL, for example `https://github.com/pingcap/tidb/pull/12345`
- `project_path` (optional)
  - absolute path to target repo, used when current directory is outside the project

## Output

Emit one JSON object summarizing orchestration status:

```json
{
  "pr_link": "https://github.com/pingcap/tidb/pull/12345",
  "prepare": {},
  "review_outputs": [],
  "merge_submit": {},
  "cleanup": {},
  "status": "success",
  "reason": ""
}
```

`status` values:
- `success`
- `partial-failure` (review/merge failed but cleanup attempted)
- `failed` (prepare failed, or critical orchestration failure)

`reason` values:
- empty string on success
- machine-readable failure reason on non-success (for example `subagent-dispatch-unavailable`)

## Direct Skill Invocation Rule

Required: invoke these skills directly by name:
- [prepare-pr-diff-worktree](../prepare-pr-diff-worktree/SKILL.md)
- [review-clarity-naming-comment-intent](../review-clarity-naming-comment-intent/SKILL.md)
- [review-correctness](../review-correctness/SKILL.md)
- [review-runtime-reliability-performance](../review-runtime-reliability-performance/SKILL.md)
- [review-scope-structure-abstraction](../review-scope-structure-abstraction/SKILL.md)
- [review-upgrade-compatibility-and-test-determinism](../review-upgrade-compatibility-and-test-determinism/SKILL.md)
- [merge-review-json-and-submit-pr-review](../merge-review-json-and-submit-pr-review/SKILL.md)
- [cleanup-pr-diff-worktree](../cleanup-pr-diff-worktree/SKILL.md)

Forbidden in this skill:
- direct execution of `prepare-pr-diff-worktree/scripts/*`
- direct execution of `merge-review-json-and-submit-pr-review/scripts/*`
- direct execution of `cleanup-pr-diff-worktree/scripts/*`

## Subagent Execution Hard Gate

- For step 2, invoke `dispatching-parallel-agents` by workflow intent (parallel, independent tasks).
- Before launching reviewer tasks, validate that Task/subagent dispatch is available in the current runtime.
- Step 2 MUST use the Task/subagent mechanism.
- The parent agent MUST NOT run any of the 5 review skills inline.
- Dispatch all 5 review subagents in one batch so they run concurrently.
- If Task/subagent dispatch is unavailable (or returns "unsupported"/"unavailable"), stop and return `failed` with reason `subagent-dispatch-unavailable`.
- Do not silently fall back to sequential, in-parent execution.
- Do not continue with any review skill execution after a subagent-dispatch failure.

## Workflow

1. Prepare worktree metadata
   - Invoke [prepare-pr-diff-worktree](../prepare-pr-diff-worktree/SKILL.md) with:
     - `pr_link`
     - `project_path` (when provided)
   - Capture output JSON fields:
     - `code_path`
     - `diff_filename`
     - `work_tree`

2. Dispatch 5 review skills in parallel subagents
   - Fail fast if Task/subagent dispatch capability is not present.
   - Use one subagent per review skill.
   - Dispatch these 5 subagents at the same time (single parallel batch).
   - Every subagent must inherit the same permissions as the parent agent:
     - same sandbox level
     - same network restrictions
     - same escalation/approval behavior
   - Required per-subagent prompt contract:
     - "Invoke skill `<review-skill-name>` directly."
     - "Inputs: `code_path=<...>`, `diff_filename=<...>`, `output_filename=<...>`."
     - "Write output JSON to exactly `output_filename`."
     - "Do not run in parent; execute in this subagent only."
   - Example dispatch shape (conceptual; use your runtime's Task/subagent API):
     ```text
     Task("Invoke skill review-clarity-naming-comment-intent with code_path=<...> diff_filename=<...> output_filename=review-clarity-naming-comment-intent.json. Execute in this subagent only.")
     Task("Invoke skill review-correctness with code_path=<...> diff_filename=<...> output_filename=review-correctness.json. Execute in this subagent only.")
     Task("Invoke skill review-runtime-reliability-performance with code_path=<...> diff_filename=<...> output_filename=review-runtime-reliability-performance.json. Execute in this subagent only.")
     Task("Invoke skill review-scope-structure-abstraction with code_path=<...> diff_filename=<...> output_filename=review-scope-structure-abstraction.json. Execute in this subagent only.")
     Task("Invoke skill review-upgrade-compatibility-and-test-determinism with code_path=<...> diff_filename=<...> output_filename=review-upgrade-compatibility-and-test-determinism.json. Execute in this subagent only.")
     ```
   - Start all five tasks before awaiting any single one.
   - Use fixed output filenames:
     - `review-clarity-naming-comment-intent.json`
     - `review-correctness.json`
     - `review-runtime-reliability-performance.json`
     - `review-scope-structure-abstraction.json`
     - `review-upgrade-compatibility-and-test-determinism.json`
   - Reviewer invocation map:
     - [review-clarity-naming-comment-intent](../review-clarity-naming-comment-intent/SKILL.md) -> `review-clarity-naming-comment-intent.json`
     - [review-correctness](../review-correctness/SKILL.md) -> `review-correctness.json`
     - [review-runtime-reliability-performance](../review-runtime-reliability-performance/SKILL.md) -> `review-runtime-reliability-performance.json`
     - [review-scope-structure-abstraction](../review-scope-structure-abstraction/SKILL.md) -> `review-scope-structure-abstraction.json`
     - [review-upgrade-compatibility-and-test-determinism](../review-upgrade-compatibility-and-test-determinism/SKILL.md) -> `review-upgrade-compatibility-and-test-determinism.json`

3. Merge and submit review
   - After all subagents finish, invoke [merge-review-json-and-submit-pr-review](../merge-review-json-and-submit-pr-review/SKILL.md).
   - Pass:
     - `pr_link`
     - `input_files` = all 5 review JSON files from step 2
   - Optional outputs:
     - `merged_output` = `merged-review-output.json`
     - `payload_output` = `github-review-payload.json`

4. Cleanup (always attempt)
   - Invoke [cleanup-pr-diff-worktree](../cleanup-pr-diff-worktree/SKILL.md) in a finally-style step.
   - Pass:
     - `work_tree` from prepare output
     - `project_path` when needed by current directory context
   - Cleanup must run even if any reviewer or merge step fails.

5. Return orchestration summary JSON
   - Include:
     - prepare result JSON
     - per-review output file list
     - merge/submit result JSON
     - cleanup result JSON
     - final `status`

## Failure Handling

- If prepare fails: stop pipeline and return `failed`.
- If subagent dispatch is unavailable in step 2: stop pipeline and return `failed` with reason `subagent-dispatch-unavailable`.
- If subagent dispatch is unavailable, do not run any reviewer inline as fallback.
- If one or more review subagents fail:
  - skip merge step
  - run cleanup
  - return `partial-failure` with failure details
- If merge fails:
  - run cleanup
  - return `partial-failure` with merge error and file outputs kept for retry
- If cleanup fails:
  - return `partial-failure` and include cleanup error details

## Determinism Requirements

- Do not rename review output filenames.
- Do not drop any of the 5 category review skills.
- Do not reorder severity handling logic inside downstream skills.
