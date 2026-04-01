---
name: parallel-design-doc-role-review
description: Use when reviewing a database design doc with cross-functional role perspectives, and each role must run in isolated subagents with bounded parallel batches and write one report file under docs/design/reviews.
---

# Parallel Design Doc Role Review

## Overview

Run one fresh review subagent per role with strict context isolation, dispatched in bounded parallel batches.

Hard requirements for this skill:
- dispatch all role reviews using parallel batches (size bounded by `max_parallel_subagents`)
- each review runs in a subagent with `fork_context=false`
- each review uses a fresh subagent (no subagent reuse across batches)
- each subagent writes exactly one review file under `docs/design/reviews/`
- output filename must include both input design-doc base name and role slug to avoid collisions

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

## Output Filename Contract

1. Compute `doc_slug` from `design_doc_path`:
   - take basename without extension
   - lowercase
   - replace every non `[a-z0-9]` run with `-`
   - trim leading and trailing `-`
   - if empty, use `design-doc`
2. For each role, write to:
   - `<output_dir>/<doc_slug>--<role_slug>.md`
3. Ensure `output_dir` exists (`mkdir -p`).

Example:
- input: `docs/design/txn-pipeline-v2.md`
- output for Security Engineer:
  - `docs/design/reviews/txn-pipeline-v2--security-engineer.md`

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
7. Return a summary:
   - `design_doc_path`
   - reviewer count
   - succeeded roles
   - failed roles
   - output file paths

## Required Subagent Prompt

Use this prompt shape per role:

```text
You are the <Role> reviewer for a database design doc.

Inputs:
- design_doc_path: <design_doc_path>
- role: <Role>
- role_slug: <role_slug>
- output_file: <output_dir>/<doc_slug>--<role_slug>.md

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

## Failure Handling

- If one reviewer fails, continue waiting for the rest in the current batch.
- Continue dispatching later batches even if earlier batches had failures.
- Do not cancel healthy running reviewers because another reviewer failed.
- Final status:
  - `success` if all 12 files are written
  - `partial-failure` if at least one reviewer failed
  - `failed` if dispatch could not start or isolation contract could not be met

## Guardrails

- Do not collapse roles into fewer reviewers.
- Do not run reviewers inline in parent as fallback.
- Do not reuse any reviewer subagent for another role.
- Do not change filename contract.
- Do not write outputs outside `output_dir`.
