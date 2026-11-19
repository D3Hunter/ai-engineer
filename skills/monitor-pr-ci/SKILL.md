---
name: monitor-pr-ci
description: Use when the user asks to monitor or watch a GitHub PR, keep an eye on its CI, retest failed checks, or handle repeated CI failures on that PR.
---

# Monitor PR CI

Monitor a PR in the current chat until its actionable CI passes or a stop condition applies. Diagnose persistent failures, keep retesting ordinary flakes and possible flake fixes, and automatically ship only verified, PR-related test-only fixes.

## Authorization and inputs

- Resolve the PR URL/number and repository from the request or current branch; ask only if ambiguous. Check GitHub authentication and read the target repository's instructions.
- An explicit request to monitor using this workflow authorizes `/retest` comments and the test-only commit/push described below. Creating or installing this skill alone does not authorize acting on a live PR. Honor narrower instructions such as “read-only.”
- Notify the user in this chat. Do not post diagnoses to GitHub, send other messages, merge, or change labels/settings unless separately requested.
- Use a supported GitHub connector, or `gh`. Read [references/github-evidence.md](references/github-evidence.md) for CLI collection and mutation examples. Do not create a scheduled automation to watch one PR.

## Always exclude `pull-error-log-review`

This job fails when error-log output changes. Match the exact CI context/job identity `pull-error-log-review`, including a provider wrapper only when its job identity is confirmed. Do not ignore other jobs by substring.

Exclude this job from failure counts, `/retest` triggers, diagnosis, fixes, and stop decisions, regardless of its status. Mention it as ignored in the final report. If it is the only failure, do not retest or change error logs. A bare `/retest` triggered by another job may incidentally rerun it; that does not remove the exception.

## Monitoring and retry ledger

1. Record the open PR's head SHA, base, head repository/branch, and all CI checks and legacy commit statuses, including optional jobs. Distinguish failure, pending, success, skipped/neutral, cancelled, and missing/unknown states. API/auth errors and empty results are not green CI.
2. Maintain a compact ledger in the chat/task state: head SHA; job identity; execution ID/URL and attempt; timestamps and result; failure signature; retest comment URL/time and triggering runs; fix commit, if any. On resume, reconcile with remote runs/comments before mutations. If retry history cannot be reconstructed, stop and notify rather than guess.
3. Poll about every 60 seconds using interruptible waits. Continue while runs are pending or progressing; report meaningful changes. Honor a user deadline. Start a separate 30-minute trigger timer at the retest comment: if no new execution appears, notify and stop as blocked even if other jobs progress. Separately, stop and notify when an actionable pending job has no observable progress for 30 minutes (state, execution/attempt, or provider-reported progress); polling alone does not reset that timer. Report the last observed state, not completion.
4. Re-read the PR state and head before every comment, edit, commit, and push. If closed/merged, stop and report it. If the head changes, discard pending actions based on the old SHA and collect the new head's checks. Old logs remain historical evidence, not current verdicts.

| Current actionable evidence | Action |
| --- | --- |
| First completed failed execution on this head | Post exactly `/retest` once, after the guards below. |
| Retest request still outstanding or replacement execution queued/running | Wait; do not duplicate the comment. |
| Same job fails in at least two distinct executions/attempts on the same head | Diagnose before another retest; apply the diagnosis table below. |
| Newly completed failed retry matches an evidence-backed ordinary flake or the same flake after a possible test-only fix | Post `/retest` again after the guards below; continue monitoring. |
| Retry passes without code changes | Record a transient/flake candidate; continue monitoring other jobs. |
| Every actionable job is successful or legitimately skipped/neutral | Notify and finish; identify any ignored check separately. |
| Cancelled, missing, or unknown check with no replacement | Investigate its status read-only; stop and notify if unresolved. |

Allow **one outstanding `/retest` request at a time**, not one per head SHA. It reruns all eligible failed jobs, so coalesce failures rather than comment per job. Check prior comments, execution times, and attempts, including retests requested by others. Repeated polling of one failed run is one failure. After the requested retry completes with a diagnosed flaky failure, another `/retest` is allowed on the same head; there is no fixed retry-count limit for ordinary flakes. Continue until actionable checks pass, the user cancels/deadline arrives, or a stop condition applies. Before each further retest, inspect the new failure signature: changed signatures or evidence of a deterministic regression require fresh diagnosis. Pagination and provider rerun history matter.

## Diagnose persistent failures

For CI diagnosis, use `diagnose-with-subagents` when available: start with a fresh global-view read-only subagent and wait for it before parent incident-evidence reads; then dispatch bounded failure-signature, PR-correlation, and history/infrastructure lanes as needed. Keep diagnostic subagents read-only: no edits, comments, reruns, commits, or pushes. The parent performs authorized remediation only after diagnosis. If that skill is unavailable, collect the same evidence with bounded read-only queries.

Find the earliest causal error from logs/artifacts, the actual command/test, environment, and failure signature. Compare distinct runs, the PR diff and affected callers, and equivalent base-branch/other-PR history or a local base reproduction when useful. Missing logs mean a gap, not a cause. Evaluate **PR-relatedness and flakiness independently**: an intermittent failure can be introduced by this PR; repeated failures alone do not prove either attribution or flakiness.

| Diagnosis | Required outcome |
| --- | --- |
| PR-related; correct fix is exclusively test-only | Apply the guarded fix workflow below. |
| PR-related; production-code change is needed | Stop and notify with evidence and the proposed fix direction. Do not edit production code. |
| Evidence-backed ordinary flake, including a known pre-existing flake unrelated to this PR | Notify once with evidence, then keep `/retest` cycles going. Do not modify unrelated tests. This is the exception to the unrelated-failure stop rule. |
| Same flaky signature recurs after a possible PR-related test-only flake fix | Treat the fix as provisional, continue `/retest` cycles, and report recurrence; do not claim the flake is cured. |
| Unrelated non-flaky failure, including a deterministic infrastructure/configuration failure | Notify with evidence and stop the entire monitor. Do not fix or keep retesting. |
| Attribution or safe fix scope remains uncertain | Notify with confidence and missing evidence; stop without a speculative fix. |

When jobs have mixed outcomes, any stop condition takes precedence over shipping a test-only fix for another job.

## Fix, validate, commit, push, hand off

1. Work from the verified PR head in a clean isolated worktree if needed. Preserve existing user changes. Verify the writable push target is the PR's actual head repository/branch, including forks.
2. Classify by semantic effect. Test cases, test-exclusive helpers/fixtures, and solely test-target generated metadata may qualify. Shared helpers, production build/configuration/dependencies, or generated production outputs do not. If exclusivity cannot be established, stop. Never hide a production defect by deleting/skipping a test, weakening assertions, swallowing errors, or merely increasing timeouts/retries.
3. Reproduce the original failure when feasible; make the smallest coverage-preserving test correction. Validate the affected behavior with the repository-required checks, including failpoint lifecycle, generation/Bazel preparation, integration recording, and delivery lint where applicable. For flakes, use bounded repetitions and report the sample size; one pass does not establish a cure. If required validation cannot be completed, notify and stop without committing/pushing.
4. Review the complete staged diff, including generated files, for test-only scope and unrelated changes. Stage only this fix's explicit paths. Recheck remote head and PR state. If the head moved, do not push the stale fix; re-evaluate against the new head.
5. Commit with a descriptive message and push normally to the exact PR head branch. Do not force push, amend unrelated commits, rebase, merge, or push to the base branch. If rejected or ambiguous, stop and notify; do not retry blindly. Confirm the resulting remote head SHA equals the fix commit before reporting a successful push.
6. Allow at most **one automatic fix commit/push per monitor invocation**. After a confirmed push, immediately notify the user to **perform post verification** and provide the commit and validation evidence. For a possible flaky-test fix, continue monitoring the new head: wait for its CI, and keep retesting if the same diagnosed flake recurs. A flake fix is provisional until verified; do not imply post-push CI already passed. For a non-flaky test fix, stop after the handoff. Continued flaky retries do not authorize a second automatic fix commit; if further code changes are needed, stop and notify with the proposed change.

## Notification contract

Give the PR link/head, outcome and stop reason, failed job/run links, retest comment link if any, causal evidence, PR-relatedness and flakiness assessment with confidence/gaps, and the ignored job's status. After a fix, include changed files, commit/push confirmation, exact validation commands/results, remaining risks or unverified checks, and “Please perform post verification.” A skipped error-log check means “actionable checks passed,” not “all CI passed.”
