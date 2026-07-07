---
name: diagnose-with-subagents
description: Use when diagnosing production, CI, Prow, Jenkins, TiDB, TiKV, PD, Kubernetes, Clinic, Loki, metrics, stuck import/checksum/add-index work, region miss errors, or read-only incidents needing coordinated evidence lanes.
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

## Parent Evidence Embargo

Until the first global-view subagent returns, the parent MUST NOT inspect incident evidence.

Allowed before the global-view result:

- Parse the user request and constraints.
- Read required local instructions and this skill.
- Discover the subagent tool if needed.
- Spawn the global-view subagent.
- Wait for the global-view subagent.

Forbidden before the global-view result:

- No log, metrics, production API, database, Kubernetes, CI, cloud, or repository code evidence commands.
- No `clinic`, Loki, Prometheus, `kubectl`, `gh`, SQL, object-store, or code-search queries about the incident.
- No "quick read-only check" while the subagent runs.

The usual habit of doing background work while an agent runs does not apply here. This skill is stricter: wait for the global-view subagent before investigating.

## Parent Raw Evidence Exception

The parent may inspect raw evidence only after all are true:

1. The global-view subagent has returned.
2. The parent has normalized the problem frame.
3. The parent has dispatched scoped lanes or identified a precise contradiction/gap.
4. The parent states the exact reason the read cannot be delegated or must be verified directly.
5. The read answers one named question with a bounded command/query.

Allowed parent reads are exception reads, not investigation lanes. If the parent needs more than one or two related commands, spawn a fresh scoped subagent instead.

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

## Coordination Ledger

For non-trivial diagnoses, maintain a visible checklist with these phases:

1. Frame request and constraints.
2. Spawn global-view subagent.
3. Wait for global-view result.
4. Normalize problem frame.
5. Dispatch scoped lanes.
6. Reconcile lane reports.
7. Run only justified parent exception reads, if needed.
8. Final synthesis.

Do not mark a phase complete until its required evidence exists. Do not begin parent evidence collection while the global-view subagent is still running.

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
- "While the subagent runs, I will check..."
- "This is just a quick Loki/Clinic/metrics/code query."
- "This is only read-only."
- "I need one broad query to orient myself."
- "This subagent can cover everything" instead of scoped lanes.
- "Read-only exec is harmless" without a narrow reason and parent approval.
- "The fix is obvious" before timeline and first abnormal signal are established.
- "No need to mention forbidden commands" in subagent prompts.

When a red flag appears, do not run the command. Either wait for the current subagent or dispatch a fresh scoped subagent.

## Parent Rationalization Traps

| Rationalization | Reality |
| --- | --- |
| "It is read-only, so it is safe." | Read-only can still violate this workflow. Safety is not the only requirement; orchestration discipline is required. |
| "I will just inspect logs while the global subagent runs." | That duplicates the global-view lane and breaks the parent/coordinator boundary. Wait. |
| "I need to understand the code first." | Code correlation is a scoped lane unless the global-view result identifies a precise gap. |
| "I am only checking command syntax." | Use help text only when needed to formulate subagent prompts; do not query incident evidence. |
| "This will be faster if I do it myself." | This skill optimizes correctness and auditability, not parent speed. Spawn lanes. |
| "The parent is allowed to fill gaps." | Only after the global result and scoped lanes define a specific gap or contradiction. |

## Violation Recovery

If the parent runs broad evidence collection before the global-view subagent returns:

1. Stop immediately.
2. Do not continue building on parent-collected evidence.
3. Close or wait for active subagents as appropriate.
4. Tell the user the workflow was violated.
5. Restart from the global-view result or ask whether to continue with a corrected lane-based workflow.

Do not silently fold parent-collected evidence into the diagnosis.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Parent starts reading logs, metrics, code, or Clinic/Loki evidence before the global-view subagent returns | Stop, disclose the violation, and restart from a corrected lane-based workflow. |
| One subagent gets "diagnose everything" | Split into bounded lanes after global discovery. |
| Subagents mutate while "just checking" | Put forbidden commands directly in every prompt. |
| Log collection is too broad | Require component, namespace, time window, and tail/filter limits. |
| Final answer jumps to a fix | Separate facts, hypotheses, confidence, and missing evidence. |
