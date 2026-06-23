---
name: diagnose-with-subagents
description: Use when diagnosing CI/Prow/Jenkins failures, TiDB/TiKV/PD/Kubernetes incidents, stuck import/checksum/add-index work, region miss errors, or other read-only incidents where the user asks for fresh subagents, scoped subtasks, or parent coordination.
---

# Diagnose With Subagents

## Overview

Run incident diagnosis as an orchestration problem. The parent agent frames the problem, launches fresh isolated read-only subagents, keeps each investigation scoped, and synthesizes evidence into one diagnosis.

Core rule: diagnose first, mutate never. Do not change CI, Kubernetes, database, local repo, or configuration state unless the user explicitly changes the task from diagnosis to remediation.

## Hard Gates

- Start with one fresh global-view subagent before any deep parent investigation.
- Use `fork_context=false` or the environment's equivalent for every subagent. If fresh isolated subagents are unavailable, stop and say the requested workflow cannot be satisfied.
- Do not reuse old subagents. Do not send multiple diagnostic lanes to one long-lived subagent.
- Keep the parent as coordinator: parse the user request, set guardrails, dispatch, reconcile, and synthesize.
- Let the parent inspect raw evidence only to verify contradictions, fill a precise gap, or prepare a narrow follow-up.
- Treat every diagnosis as read-only by default.

## Read-Only Guardrails

Explicitly pass these guardrails to every subagent:

- Do not run mutation commands: no `kubectl apply/delete/edit/patch/scale/rollout`, no restarts, no job reruns, no CI rebuilds, no PR comments, no issue creation.
- Do not run database writes: no DDL/DML, no `KILL`, no `ADMIN CANCEL`, no `SET GLOBAL`, no `ANALYZE`, no compaction, no scheduler/store changes.
- Do not edit local files, kubeconfig, manifests, scripts, or repo state.
- Use bounded reads: scoped namespaces, explicit pods/components, `--since`/`--tail` log limits, filtered output, and no unbounded watch loops.
- Do not reveal secret values. Report secret names only unless the user explicitly approves deeper inspection.
- Capture facts with commands, timestamps, source paths/URLs, and confidence. Separate evidence from hypotheses.

## Workflow

1. Parse the request and constraints.
   - Identify target URL/path/cluster, working directory, `KUBECONFIG`, component names, pod patterns, symptoms, and "do not change" wording.
   - Do only this parsing in the parent before the global-view subagent.

2. Launch the global-view subagent.
   - Scope it to broad read-only discovery, not root-cause analysis.
   - Ask for topology, timeline, failing/stuck operation, involved components, first visible symptoms, and likely diagnostic lanes.
   - Require it to list exact commands or sources used and to mark unknowns.

3. Normalize the problem frame in the parent.
   - State what is stuck or failing, where, since when, and what evidence is missing.
   - Convert broad questions like "why is it stuck" into hypotheses and scoped lanes.

4. Dispatch scoped subagents in parallel when lanes are independent.
   - One lane per fresh subagent.
   - Each lane must have: question, allowed reads, forbidden actions, output contract, and stop boundary.
   - Start all ready lanes before waiting on one lane.

5. Reconcile and iterate.
   - Compare reports for first abnormal signal, repeated IDs, timestamps, and contradictions.
   - Launch follow-up subagents only for precise gaps, such as one table ID, region ID, pod, stage, or time window.

6. Produce the final diagnosis.
   - Include probable cause, supporting evidence, ruled-out causes, residual uncertainty, and next read-only checks or remediation suggestions.
   - If evidence is insufficient, say what is missing instead of inventing a cause.

## Subagent Prompt Contract

Use this shape for each subagent:

```text
You are a fresh read-only diagnostic subagent. Run with fork_context=false.

Problem: <one sentence>
Context: <URL/path/cluster/KUBECONFIG/component/time window>
Scope: <exact lane; do not investigate outside it>
Allowed reads: <commands/sources/classes of evidence>
Forbidden actions: no mutations, no writes, no restarts, no reruns, no broad scraping
Output:
- facts with source/command and timestamp
- hypothesis assessment with confidence
- what this lane rules out
- missing evidence or recommended next narrow read-only probe
```

## Lane Recipes

For CI/Prow/Jenkins failures, choose lanes from:

| Lane | Question |
| --- | --- |
| Failure signature | What is the earliest causal error, not downstream noise? |
| Stage/test context | Which stage, node, test, command, or artifact owns the failure? |
| Change correlation | Which PR changes or dependencies plausibly touch that path? |
| Flake/history | Does the same signature appear in recent runs or related jobs? |
| Infrastructure | Are there timeouts, agent failures, pod/node issues, cache/download failures, or resource limits? |

For TiDB/TiKV/PD/Kubernetes stuck work, choose lanes from:

| Lane | Question |
| --- | --- |
| TiDB-side operation | Which session, DDL, checksum, import, table, index, key range, or owner is stalled? |
| TiDB logs | Where are `region miss`, backoff, schema sync, checksum, DDL, or import messages emitted? |
| PD/region metadata | Are regions unavailable, moving, splitting, merging, stale, or rapidly changing? |
| TiKV/store health | Are stores unhealthy, overloaded, missing leaders, disk pressured, or stuck on raft/apply/ingest? |
| Kubernetes resources | Are pods restarting, unready, throttled, evicted, or on unhealthy nodes/PVCs? |
| Job provenance | What initiated the import/checksum/add-index work and with which config? |
| Timeline correlation | Which component produced the first abnormal signal, and do retries make progress? |

## Output Shape

Keep the final response evidence-oriented:

- Summary: one paragraph with the most likely cause and confidence.
- Timeline: key timestamps and first abnormal signal.
- Evidence: per-lane facts with source pointers.
- Ruled out: plausible causes that the evidence does not support.
- Gaps: exact missing evidence, if any.
- Next steps: narrow read-only checks first; remediation only as recommendations.

## Compact Example

For a prompt like:

```text
under /path/to/case with KUBECONFIG=kubeconfig.yml diagnose why import checksum on tc1-tidb-0 is stuck and keeps reporting region miss; don't change thing
```

Do not inspect TiDB logs in the parent first. Launch one global-view subagent for topology, timeline, involved pods, and likely lanes. Then dispatch scoped fresh subagents such as TiDB-side checksum behavior, PD/region metadata, TiKV/store health, job provenance, and timeline correlation. Every prompt must include the read-only guardrails and `KUBECONFIG=kubeconfig.yml`.

## Red Flags

- "I'll just inspect the logs first" before global discovery.
- "This subagent can cover everything" instead of scoped lanes.
- "Read-only exec is harmless" without a narrow reason and parent approval.
- "The fix is obvious" before timeline and first abnormal signal are established.
- "No need to mention forbidden commands" in subagent prompts.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Parent starts reading logs before the global-view subagent | Stop and launch the fresh global-view subagent first. |
| One subagent gets "diagnose everything" | Split into bounded lanes after global discovery. |
| Subagents mutate while "just checking" | Put forbidden commands directly in every prompt. |
| Log collection is too broad | Require component, namespace, time window, and tail/filter limits. |
| Final answer jumps to a fix | Separate facts, hypotheses, confidence, and missing evidence. |
