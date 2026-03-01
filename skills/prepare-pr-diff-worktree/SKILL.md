---
name: prepare-pr-diff-worktree
description: Use when given a GitHub pull request link and needing to create an isolated worktree, check out PR code, export the PR diff to <pr-number>.diff, and return JSON metadata (`code_path`, `diff_filename`, `work_tree`) even when gh authentication is unavailable or the current directory is outside the target repo.
---

# Prepare PR Diff Worktree

## Overview

Create a new git worktree from a target project, check out the target PR in that worktree, save the PR diff as `<pr-number>.diff`, and emit one JSON object for later steps.

Use the bundled script for deterministic execution.

## Input

- Required: `pr_link`
  - full PR URL, for example `https://github.com/pingcap/tidb/pull/12345`
  - or PR number, for example `12345`
- Optional: `project_path`
  - absolute path to the target project git repository
  - required when current directory is not inside that project

## Output Contract

Print exactly one JSON object with these fields:

- `code_path`: absolute path to the newly created worktree
- `diff_filename`: generated diff filename, always `<pr-number>.diff`
- `work_tree`: worktree name (folder name under `worktrees/`)

Example:

```json
{"code_path":"/abs/repo/worktrees/pr-12345","diff_filename":"12345.diff","work_tree":"pr-12345"}
```

## Command

If currently inside the target project:

```bash
./prepare-pr-diff-worktree/scripts/create_pr_worktree_and_diff.sh <pr_link>
```

If currently outside the target project:

```bash
./prepare-pr-diff-worktree/scripts/create_pr_worktree_and_diff.sh --project-path <project_path> <pr_link>
```

## Authentication Modes

- Preferred mode: authenticated `gh` (`gh auth login`)
  - checks out with `gh pr checkout`
  - exports diff with `gh pr diff`
- Fallback mode (no `gh` auth):
  - fetches PR head with `git fetch https://github.com/<owner>/<repo>.git pull/<pr-number>/head`
  - checks out detached `FETCH_HEAD`
  - downloads diff from `https://github.com/<owner>/<repo>/pull/<pr-number>.diff`

## Workflow Implemented by Script

1. Resolve the target git repository from current directory or `--project-path`.
2. Resolve PR number and owner/repo from PR URL, PR number, and `origin` remote.
3. Create a unique worktree under `<repo-root>/worktrees/`.
4. Check out PR code (preferred `gh`, fallback `git fetch` for public GitHub PRs).
5. Write `<pr-number>.diff` at the worktree root (preferred `gh`, fallback `curl` from `.diff` URL).
6. Print the output JSON object.

## Notes

- This workflow assumes GitHub PRs.
- If using PR number input, `origin` should point to the target GitHub repo.
- Unauthenticated fallback works for public PRs; private PRs still require valid auth.
- If `worktrees/pr-<number>` already exists, the script appends a numeric suffix to create a unique `work_tree`.
