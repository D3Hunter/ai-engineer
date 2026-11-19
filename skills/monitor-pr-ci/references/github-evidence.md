# GitHub evidence and commands

Use these examples when no suitable connector is available. Replace placeholders with verified values and quote shell arguments. Run `--help` for installed CLI capabilities; do not assume Prow/Jenkins jobs are GitHub Actions runs.

## Resolve and snapshot

```bash
gh auth status
gh pr view <PR_URL> --json url,number,state,headRefOid,baseRefOid,baseRefName,headRefName,headRepository,headRepositoryOwner,isCrossRepository,statusCheckRollup
gh pr checks <PR_URL> --json name,state,bucket,link,startedAt,completedAt,workflow
```

`gh pr checks` can return nonzero for failed checks, or exit 8 for pending checks. Preserve/interpret the structured output and exit status; do not hide transport/authentication errors with `|| true`. Query all checks, not only `--required`. GraphQL `statusCheckRollup` and `gh pr checks` combine check runs and legacy statuses but are snapshots, not sufficient retry history.

Use the base PR repository (not automatically its fork) for PR comments and CI evidence. Inspect provider links and tested SHAs: presubmit jobs can test a synthetic merge commit. Establish its association to the current PR head/base from provider metadata instead of treating every SHA mismatch as stale.

## Runs, attempts, legacy statuses, and comments

```bash
gh api --paginate 'repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs?filter=all&per_page=100'
gh api --paginate 'repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/statuses?per_page=100'
gh api --paginate 'repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/comments?per_page=100'
gh run list --repo <OWNER/REPO> --commit <TESTED_SHA> --limit 100 --json databaseId,headSha,status,conclusion,name,workflowName,url,createdAt,updatedAt
gh run view <RUN_ID> --repo <OWNER/REPO> --json headSha,attempt,status,conclusion,jobs,url
gh run view <RUN_ID> --repo <OWNER/REPO> --attempt <ATTEMPT> --log-failed
gh pr diff <PR_URL>
```

Fetch additional run pages if the bounded Actions list cannot establish history. A GitHub Actions retry can reuse a run ID while incrementing its attempt. For legacy statuses, multiple status records can describe one provider execution; deduplicate by provider run identity, not status-record count. Follow the actual Prow/Jenkins details URL for logs, artifacts, timestamps, run identity, tested head, and history. Bound requests by relevant jobs, attempts, log excerpts, and time windows; redact secrets.

Comments alone may not identify their target SHA. Correlate their timestamps with head commits and provider executions. If ambiguous, do not post a duplicate. A check name alone is not a global job identity: include provider/workflow/context so unrelated jobs are not conflated.

## Authorized mutations

Only use the following after the entrypoint's authorization, head, retry-history, and scope guards pass. Immediately before a comment, re-read head/checks/comments and confirm the failure is still current. Do not infer permission to mutate from these examples alone.

```bash
gh pr comment <PR_URL> --body '/retest'
```

Capture the returned comment URL and observe a new provider execution/attempt. Wait for that retry to complete before posting again. If the newly completed attempt still has the same diagnosed ordinary flaky signature, post `/retest` again, including after a possible test-only flake fix; reconcile the new head after a push. There is no one-comment-per-head cap, but never duplicate a request for the same completed attempts or overlap outstanding requests. Re-diagnose changed signatures before another comment.

This skill deliberately uses the user's requested `/retest`, not `gh run rerun`, job-specific retest variants, or altered CI configuration. If the repository does not support it, report that blocker rather than substituting another mutation. Never repost after a timeout or uncertain write result without checking whether the comment was created.

After a verified test-only fix, inspect and stage explicit paths rather than `git add -A`. Verify `<HEAD_REMOTE>` points to the PR's head repository and use its exact branch. Shell placeholders below represent separate arguments; replace them before execution.

```bash
git status --short
git diff -- <FIX_PATHS>
git add -- <FIX_PATHS>
git diff --cached --check
git diff --cached
git ls-remote <HEAD_REMOTE> refs/heads/<HEAD_BRANCH>
git commit -m '<DESCRIPTIVE_TEST_FIX_MESSAGE>'
git push <HEAD_REMOTE> HEAD:refs/heads/<HEAD_BRANCH>
git rev-parse HEAD
git ls-remote <HEAD_REMOTE> refs/heads/<HEAD_BRANCH>
gh pr view <PR_URL> --json state,headRefOid
```

Compare the pre-push remote SHA to the diagnosed head; compare the post-push remote/PR SHA to the local fix SHA. Ordinary non-force push protects against divergent updates, but a check and push are not atomic. If another author updates concurrently, reconcile read-only and report uncertainty rather than overwriting their branch. Keep the commit/worktree for inspection if push fails.
