# AGENTS.md

## PR Title Policy

- Never prefix pull request titles with `[codex]` or any other automation tag.
- If the user provides a PR title, use it exactly.
- If the user does not provide a title, generate a plain descriptive title with no bracketed prefix.
- This rule applies to all PR creation workflows, including `gh pr create` and any skill defaults.

## PR Description Policy

- Generate PR title and description from the actual diff against `main`.
- Keep descriptions short and include only:
  1. A brief summary of what changed.
  2. A brief summary of tests that were added.
- Do not include process/meta notes in PR descriptions.

## Notes Reference

- For virtualization topics (`virsh`, `virt-install`, `qemu-img`, storage pools, VM networking), check these notes first:
  - `notes/vm-learning-notes.md`
- When related questions are answered, prefer keeping commands/examples consistent with these notes (`"$VM"` style placeholders).

## Shortcut Prompt: Ship And Reset

- If the user intent clearly means "ship and reset" (for example `ship-and-reset`, `ship and reset`, `ship/reset`, `commit pr merge cleanup`, or close variants), run this full flow in one pass:
  1. Run verification and stop if it fails.
  2. Stage all changes, commit with a concise diff-based message, and push the current branch.
  3. Open a PR against `main` with title/description derived from the actual diff.
  4. Merge the PR.
  5. Run cleanup and reset to new work:
     - `git fetch --prune`
     - pull latest `main`
     - switch to a fresh `codex/` branch from updated `main`

## Git Cleanup Policy

- During branch cleanup, run `git fetch --prune` to remove stale remote-tracking branches before deleting local branches.
