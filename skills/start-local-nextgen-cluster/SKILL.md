---
name: start-local-nextgen-cluster
description: Use when starting or preparing the manually managed local NextGen TiKV cluster for realtikvtests, IMPORT INTO, add-index, or TiDB system/user keyspace work.
---

# Start Local NextGen Cluster

## Overview

Use the dedicated binaries and configs in `~/playground/tikv-worker-test`. All paths below are relative to that directory; `./bin/tikv-server`, `./bin/tikv-worker`, and `./bin/pd-server` are symlinks to the dedicated builds. This procedure is authoritative; do not substitute TiDB repository bootstrap scripts, a multi-PD topology, or different binaries.

## Select Components

| Workload | PD + 3 TiKV | TiKV Worker | TiDB |
| --- | --- | --- | --- |
| `realtikvtests` | required | required | do not start |
| `IMPORT INTO` or add-index | required | required | start only the required keyspace server(s) |
| Other storage work | required | only if requested/needed | start only the required keyspace server(s) |

- Start SYSTEM-keyspace TiDB when the task requires SYSTEM KS.
- Start user-keyspace TiDB when the task requires user KS.
- Start both only when the task explicitly needs both.

## Preflight

1. Run `cd ~/playground/tikv-worker-test` in every component's terminal session before running its command.
2. Confirm the referenced binary symlinks resolve to executable files and the config files exist before launching. Use `./bin/` even if similarly named binaries exist in the working directory.
3. Inspect listeners on `2379`, `19000`, and `9000` as applicable. Reuse a matching healthy component; never kill or replace an unrelated process without permission.
4. The worker depends on the existing S3-compatible MinIO endpoint at `http://localhost:9000` and bucket `mybucket`. Do not start or reconfigure MinIO unless separately requested.
5. When TiDB is required, resolve the intended executable from the task or user and create `./bin/tidb-server` as a symlink to that confirmed build. Verify any existing symlink matches the intended build before using it; do not guess among checkouts or builds.

## Start The Cluster

Use separate persistent terminal sessions for long-running commands. Retain each session ID, poll startup output, and leave successful sessions running.

Start PD and three TiKV nodes first:

```bash
tiup playground v8.5.3 --without-monitor --host 0.0.0.0 --tiflash 0 --db 0 --kv 3 --kv.binpath=./bin/tikv-server --kv.config ./tikv-0/tikv.toml --pd.config ./pd-0/pd.toml --pd.binpath=./bin/pd-server
```

When the component table requires TiKV Worker, start it in a second persistent session:

```bash
DFS_PREFIX=next-gen DFS_S3_BUCKET=mybucket DFS_S3_ENDPOINT=http://localhost:9000 DFS_S3_KEY_ID=minioadmin DFS_S3_REGION=local DFS_S3_SECRET_KEY=minioadmin ./bin/tikv-worker --addr=0.0.0.0:19000 --pd-endpoints="http://localhost:2379" --register=true
```

When SYSTEM-keyspace TiDB is required, use the confirmed binary symlink and start:

```bash
./bin/tidb-server --store tikv --path localhost:2379 --config ./systidb.toml
```

When user-keyspace TiDB is required, use the confirmed binary symlink and start:

```bash
./bin/tidb-server --store tikv --path localhost:2379 --config ./tidb-ks1.toml
```

## Verify And Report

- PD must answer at `http://localhost:2379`; confirm its store view contains three TiKV stores.
- When used, TiKV Worker must remain running, listen on `19000`, and log successful PD registration.
- When used, each TiDB process must remain running and report successful PD connection/listening startup. Read its SQL/status ports from the selected config rather than inventing them.
- If any process exits, report its command and terminal output. Do not silently fall back to other launchers, versions, binaries, configs, or topology.
- Report the components started or reused, persistent session IDs, endpoints, and readiness evidence. Do not stop the cluster after verification unless requested.
