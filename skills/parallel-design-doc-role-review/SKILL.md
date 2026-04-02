---
name: parallel-design-doc-role-review
description: Use when reviewing a database design doc with cross-functional role perspectives that must run in isolated subagents, then be semantically deduplicated into one versioned unified report under docs/design/reviews.
---

# Parallel Design Doc Role Review

## Overview

Run one fresh review subagent per role with strict context isolation, dispatched in bounded parallel batches.

Hard requirements for this skill:
- dispatch all role reviews using parallel batches (size bounded by `max_parallel_subagents`)
- each review runs in a subagent with `fork_context=false`
- each review uses a fresh subagent (no subagent reuse across batches)
- each subagent writes exactly one intermediate review file under `docs/design/reviews/`
- parent agent semantically deduplicates and unifies successful role reviews into one final file
- unified output filename uses a zero-padded numeric suffix (`0000`, `0001`, ...) and must never overwrite an existing unified file
- after successfully writing the unified file, remove the intermediate role files produced by this run

## Inputs

- `design_doc_path` (required): path to the design doc to review
  - absolute path preferred
  - relative path allowed and resolved from current working directory
- `output_dir` (optional): defaults to `docs/design/reviews`
- `max_parallel_subagents` (optional): defaults to `12`
  - must be an integer >= 1
  - use environment-specific limit when known

## Fixed Reviewer Roles

Use exactly this role set and slug mapping:

| Role | role_slug |
| --- | --- |
| Database Architect | `database-architect` |
| Tech Lead (DB Team) | `tech-lead-db-team` |
| Query/Optimizer Engineer | `query-optimizer-engineer` |
| Storage Engine Engineer | `storage-engine-engineer` |
| Transaction/Consistency Engineer | `transaction-consistency-engineer` |
| DBA (Production Operations) | `dba-production-operations` |
| SRE (Reliability/Capacity) | `sre-reliability-capacity` |
| Security Engineer | `security-engineer` |
| Performance Engineer | `performance-engineer` |
| QA/Test Engineer | `qa-test-engineer` |
| Product Manager | `product-manager` |
| Service Owner (upstream/downstream dependent team) | `service-owner-dependent-team` |

## Output Filename Contracts

1. Compute `doc_slug` from `design_doc_path`:
   - take basename without extension
   - lowercase
   - replace every non `[a-z0-9]` run with `-`
   - trim leading and trailing `-`
   - if empty, use `design-doc`
2. For each role, write intermediate output to:
   - `<output_dir>/<doc_slug>--<role_slug>.md`
3. Compute unified report sequence number:
   - list existing files matching `<output_dir>/<doc_slug>--unified-*.md`
   - parse suffix numbers from `<doc_slug>--unified-<seq>.md` where `<seq>` is digits
   - `next_seq = max(existing_seq) + 1`, default `0` when no matches exist
   - format `next_seq` as at least 4 digits with zero-padding (`0000`, `0001`, ...)
4. Write unified output to:
   - `<output_dir>/<doc_slug>--unified-<seq>.md`
5. Ensure `output_dir` exists (`mkdir -p`).

Example:
- input: `docs/design/txn-pipeline-v2.md`
- intermediate output for Security Engineer:
  - `docs/design/reviews/txn-pipeline-v2--security-engineer.md`
- first unified output:
  - `docs/design/reviews/txn-pipeline-v2--unified-0000.md`
- second unified output:
  - `docs/design/reviews/txn-pipeline-v2--unified-0001.md`

## Subagent Isolation Contract

Every reviewer must run in a fresh isolated subagent:
- set `fork_context=false`
- do not reuse previous subagents
- do not inherit parent conversation context
- pass only explicit inputs in the prompt (`design_doc_path`, `role`, `role_slug`, `output_file`)

If context isolation cannot be guaranteed, fail fast and report `context-isolation-unavailable`.

## Tooling Contract (Codex)

- Create one subagent per role with `spawn_agent`.
- Required spawn settings:
  - `fork_context=false`
  - `message` contains only the role-specific review task
- Do not dispatch reviewer tasks in parent agent.
- Do not queue reviewer tasks onto previously used agents with `send_input`.
- Dispatch reviewers in batches up to `max_parallel_subagents`.
- Wait for each batch with `wait_agent` and collect per-role status before launching the next batch.
- Semantic deduplication and unified report generation must run in the parent agent only (not in reviewer subagents).

## Execution Workflow

1. Validate inputs.
   - fail if `design_doc_path` is missing or file does not exist
2. Resolve `output_dir` (default `docs/design/reviews`) and create it.
3. Resolve `max_parallel_subagents` (default `12`) and validate it is an integer >= 1.
4. Build 12 review tasks from the role mapping table.
5. Dispatch review tasks in parallel batches.
   - each batch size is `min(remaining_roles, max_parallel_subagents)`
   - each role is dispatched to a fresh subagent
   - do not reuse subagents across batches
6. Wait for the active batch to finish before launching the next batch.
7. Collect successful intermediate review files produced by this run.
8. Semantically deduplicate and unify successful role reviews into one versioned file:
   - identify semantically equivalent findings even when wording differs
   - merge duplicates into one canonical item
   - preserve role attributions for each merged item
   - preserve strictest verdict signal when conflicts exist (`Block` > `Needs Changes` > `Approve`)
9. Write unified output atomically to `<output_dir>/<doc_slug>--unified-<seq>.md` using the next available sequence suffix.
10. After unified output is written successfully, delete only the intermediate role files produced by this run.
11. Return a summary:
   - `design_doc_path`
   - reviewer count
   - succeeded roles
   - failed roles
   - unified output file path
   - deleted intermediate file paths
   - undeleted intermediate file paths (if any)

## Required Subagent Prompt

Use this prompt shape per role:

```text
You are the <Role> reviewer for a database design doc.

Inputs:
- design_doc_path: <design_doc_path>
- role: <Role>
- role_slug: <role_slug>
- output_file: <output_dir>/<doc_slug>--<role_slug>.md (intermediate role file)

Requirements:
1. Read the design doc from design_doc_path.
2. Review from this role perspective only.
3. Write the review to output_file.
4. Overwrite output_file atomically.
5. Do not write any other files.

Review file format:
- Title: Review - <Role> - <doc_slug>
- Design Doc: <design_doc_path>
- Role: <Role>
- Verdict: Approve | Needs Changes | Block
- Top Risks (max 5)
- Required Changes
- Open Questions
- Suggested Tests / Validation
- Non-blocking Suggestions
```

## Unified Report Format

The parent agent writes exactly one unified file for this run:

- Title: Unified Review - <doc_slug> - <seq>
- Design Doc: <design_doc_path>
- Source Role Reviews: `<succeeded_count>/12`
- Overall Verdict: Approve | Needs Changes | Block
- Consolidated Top Risks
- Consolidated Required Changes
- Consolidated Open Questions
- Consolidated Suggested Tests / Validation
- Consolidated Non-blocking Suggestions
- Role Attribution Matrix (for each consolidated item, list contributing roles)

## Failure Handling

- If one reviewer fails, continue waiting for the rest in the current batch.
- Continue dispatching later batches even if earlier batches had failures.
- Do not cancel healthy running reviewers because another reviewer failed.
- Final status:
  - `success` if all 12 reviewers succeed, unified file is written, and all run-specific intermediate files are deleted
  - `partial-failure` if unified file is written but at least one reviewer failed or at least one intermediate file could not be deleted
  - `failed` if dispatch could not start, isolation contract could not be met, no reviewer output exists to unify, or unified file write fails

## Guardrails

- Do not collapse roles into fewer reviewers.
- Do not run reviewers inline in parent as fallback.
- Do not reuse any reviewer subagent for another role.
- Do not overwrite an existing unified file; always allocate the next numeric suffix.
- Do not write outputs outside `output_dir`.
- Do not delete unrelated files; cleanup is limited to intermediate role files produced by this run.
