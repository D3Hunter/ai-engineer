---
name: cleanup-pr-diff-worktree
description: Use when a worktree created for PR-diff review should be removed from the target project, including dirty or non-empty directories that require forced cleanup.
---

# Cleanup PR Diff Worktree

## Overview

Remove a previously prepared PR worktree (created by `prepare-pr-diff-worktree`) from a target project and emit one JSON result object.

This skill supports forced cleanup so leftover files inside the worktree do not block removal.

## Input

- Optional: `project_path`
  - absolute path to the target project git repository
  - required when current directory is not inside that project
- Required: one of
  - `work_tree`
    - folder name under `<repo-root>/worktrees/` (for example `pr-12345`)
  - `code_path`
    - absolute path to the worktree directory (for example `/abs/repo/worktrees/pr-12345`)

## Output Contract

Print exactly one JSON object with these fields:

- `code_path`: absolute path to the cleanup target
- `work_tree`: worktree folder name
- `removed`: boolean (`true` if cleanup removed something)
- `used_force`: boolean (`true` when forced deletion path was used)
- `method`: cleanup path (`git-worktree-remove`, `rm-rf-stale-dir`, or `not-found`)

Example:

```json
{"code_path":"/abs/repo/worktrees/pr-12345","work_tree":"pr-12345","removed":true,"used_force":true,"method":"git-worktree-remove"}
```

## Command

If currently inside the target project:

```bash
./cleanup-pr-diff-worktree/scripts/remove_pr_worktree.sh --work-tree <work_tree>
```

Or with `code_path`:

```bash
./cleanup-pr-diff-worktree/scripts/remove_pr_worktree.sh --code-path <code_path>
```

If currently outside the target project:

```bash
./cleanup-pr-diff-worktree/scripts/remove_pr_worktree.sh --project-path <project_path> --work-tree <work_tree>
```

## Notes

- Default behavior is force cleanup (`--force`) to handle extra files in the worktree.
- Use `--no-force` when you want the command to fail on dirty/non-empty worktrees instead of deleting.
- As a safety guard, cleanup is only allowed for paths under `<repo-root>/worktrees/`.
