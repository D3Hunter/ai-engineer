# AGENTS.md

## PR Title Policy

- Never prefix pull request titles with `[codex]` or any other automation tag.
- If the user provides a PR title, use it exactly.
- If the user does not provide a title, generate a plain descriptive title with no bracketed prefix.
- This rule applies to all PR creation workflows, including `gh pr create` and any skill defaults.

## Notes Reference

- For virtualization topics (`virsh`, `virt-install`, `qemu-img`, storage pools, VM networking), check these notes first:
  - `notes/vm-learning-notes.md`
- When related questions are answered, prefer keeping commands/examples consistent with these notes (`"$VM"` style placeholders).

## Git Cleanup Policy

- During branch cleanup, run `git fetch --prune` to remove stale remote-tracking branches before deleting local branches.
