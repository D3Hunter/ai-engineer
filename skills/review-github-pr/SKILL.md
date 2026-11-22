---
name: review-github-pr
description: Use when asked to review a GitHub pull request or its diff for actionable defects and material design risks.
---

# Review GitHub PR

The lead reviewer owns preparation, risk selection, consolidation, delivery, and cleanup. Scale the review to the change; use fresh independent reviewers where they add useful coverage. Return findings directly without intermediate files or a separate formatting skill.

## Pin the Target

Read the PR description and repository instructions. For a PR, record base/head SHAs and review the head against their merge base. Use an existing clone (`project_path` when supplied), obtaining a temporary clone if needed. For a supplied local diff, establish its base and matching code snapshot; disclose missing context.

Ensure the inspected code matches the target. Use a detached temporary worktree when isolation is needed. Preserve the user's checkout and changes, and track resources created by this run.

## Choose Coverage

Review small, localized changes directly. For substantial changes—such as transaction mutations, concurrent lifecycles, public contracts, or interacting subsystems—obtain a fresh independent review when available. Choose a whole-change second opinion or focused specialists according to the risks; there is no fixed reviewer count or mandatory merger agent. The lead checks interactions across assigned scopes.

Read only references relevant to the changed contracts. A change may use several references; reviewer assignments can span them.

| Changed surface | Reference |
| --- | --- |
| Query behavior, SQL, planner rewrites, execution operators | [SQL semantics](references/sql-semantics.md) |
| Persisted state, schema, indexes, transactions | [Data integrity](references/data-integrity.md) |
| Failure handling, retries, concurrency, resource growth, performance | [Runtime reliability](references/runtime-reliability.md) |
| Versioned contracts, upgrades, migrations | [Compatibility](references/compatibility.md) |
| Test changes, regression assertions, determinism, isolation across any review area | [Test quality](references/test-quality.md) |
| Abstraction, layering, names, comments, definition collisions | [Maintainability](references/maintainability.md) |
| Chunked parsing, record framing, stateful readers | [Streaming and framing](references/streaming-framing.md) |

Launch independent reviewers without inherited conversation history (`fork_turns="none"`, `fork_context=false`, or equivalent). Supply this skill's path, the objective, repository instructions, absolute code path, pinned target, and assigned risks/references; withhold other reviewers' findings and the lead's conclusions. Delegated reviewers follow the common static-review, evidence, and reporting contract in **Review and Consolidate** for their assignment and return findings and coverage gaps. They do not launch reviewers, prepare resources, publish, or clean up.

Wait for assigned reviewers; slow progress alone is not a failure. Preserve completed results and retry or explicitly reassign failed coverage when feasible. If independent agents are unavailable, continue the lead review and disclose reduced independence. If an assigned surface remains unreviewed, label the result partial and skip GitHub submission.

## Review and Consolidate

Review statically: do not modify source or run builds, tests, or benchmarks. Inspect changed functions and relevant callers, callees, tests, and unchanged fallback branches. Trace normal and adversarial paths across affected boundaries; use the conditional domain checks above. Report meaningful coverage limits instead of recording a pass or `N/A` for every checklist section.

Keep findings supported by code, a concrete failure scenario, or a material maintenance risk. Distinguish existing problems from issues introduced or worsened by the diff. Repository rules take precedence over personal preferences; naming polish, additional abstraction, or more tests are not findings without a specific consequence. Put uncertain hypotheses and targeted validation requests separately, with a minimal scenario, suggested command, and expected result where practical.

The lead verifies candidate findings against the pinned code, removes unsupported claims, combines reports of the same issue, and resolves severity from impact. A fresh verifier can help resolve disputed or complex candidates; give that role the hypotheses to verify. Keep distinct issues separate even at the same location.

Return one actionable issue per finding: severity, concise title, precise `path:line`, trigger/evidence, impact, and suggested change. Order by `Blocker` (data loss, corruption, or critical contract failure), `Major` (substantial user or operational impact), then `Minor` (bounded impact). Reserve `Info`/`Nit` for explicitly requested polish. A no-findings result should state the reviewed scope and material limitations without implying exhaustive proof.

## Deliver and Clean Up

The user has given standing authorization to publish the completed review on the GitHub PR they ask you to review. A request such as `review <PR URL>` activates that authorization, including when this skill is selected automatically. Submit one GitHub comment review, even when there are no findings, then return the review link and a summary in chat. No separate request to post is needed. Use an approval or changes-requested review only when the user asks for that action.

Honor a draft or chat-only request and deliver a local diff review in chat when no GitHub PR is identified. Anchor actionable findings to valid diff lines and put unanchored findings in the summary. Include brief AI attribution and a manual follow-up note.

Before posting, confirm the PR head still matches the reviewed SHA. If it moved, update the pinned target, inspect the new changes, and revalidate retained findings and affected coverage before posting; otherwise deliver the draft in chat with the stale-target limitation. Attach the review to the reviewed head commit. After an uncertain submission outcome, check existing reviews before retrying to avoid duplicates. Preserve the review if posting fails.

After the posting attempt (or chat delivery when submission is skipped) and once all reviewers stop using the code, attempt cleanup even on failure. Remove only temporary resources created by this run; preserve unexpected changes and report them. Keep findings available in the conversation before removal. Finish with coverage limitations, the submission link when posted, and any cleanup issue.
