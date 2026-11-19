Extend the maintainability reference in `skills/review-github-pr/references/maintainability.md`. Keep review guidance in the single `review-github-pr` skill rather than creating another scope skill.

Inputs:

- `code_path`: absolute path to the codebase to inspect.
- Review target: a supplied diff (file or prompt content), or pinned base/head revisions.

Follow the common evidence, severity, reporting, and static-review contract in `skills/review-github-pr/SKILL.md` instead of duplicating it in the reference.

Add only guidance that changes review decisions: concrete risk triggers, non-obvious invariants, and useful counterexamples. Apply checks when the diff touches their contracts. Treat naming and abstraction preferences as prompts to investigate, not automatic defects.

Reuse existing conditional references when relevant, especially `streaming-framing.md` for chunked record handling. Avoid exhaustive completion/N/A requirements, phrase banks, fixed reviewer counts, and intermediate output schemas.

Use the following raw materials to build a focused checklist:
