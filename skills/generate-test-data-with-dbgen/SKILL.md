---
name: generate-test-data-with-dbgen
description: Generate test data with kennytm/dbgen. Use when the user asks for dbgen, generated table data, CSV dumps, or sized data files. Defaults to CSV and about 256 MiB per file. Downloads dbgen v0.8.0 when it is not already installed.
---

# Generate data with dbgen

Use [kennytm/dbgen](https://github.com/kennytm/dbgen) v0.8.0. Resolve the binary, output directory, schema, and volume from the current machine and the request. Do not assume a cluster, pod, kubeconfig, package manager, or fixed path.

## Defaults

| Item | Default |
| --- | --- |
| Format | CSV, with a header row: `-f csv --headers` |
| File size | 256 MiB (`268435456` bytes) per data file |
| Total size | one 256 MiB file, unless the user gives a total size or row count |
| Timestamps | `--time-zone UTC` |
| Output directory | the directory the user names, otherwise `./dbgen-data` |
| Install directory | `$DBGEN_DIR`, otherwise `./.dbgen` |

Keep the schema file dbgen writes (`*-schema.sql`). Pass `--no-schemas` only when the user does not want it.

For MySQL or TiDB with the default `NO_BACKSLASH_ESCAPES` off, add `--escape-backslash`. Leave it off for other targets.

## Install when missing

1. Use `dbgen` from `PATH` when `dbgen --version` runs.
2. Otherwise run [scripts/install-dbgen.sh](scripts/install-dbgen.sh) and use the binary path it prints.

The only published v0.8.0 binary is Linux x86_64. On that platform the script downloads and unpacks:

```bash
wget https://github.com/kennytm/dbgen/releases/download/v0.8.0/dbgen-v0.8.0-x86_64-unknown-linux-gnu.tar.xz
tar -xJf dbgen-v0.8.0-x86_64-unknown-linux-gnu.tar.xz
chmod +x bin/dbgen
```

`tar -xJf` needs the `xz` program. If it fails with `xz: Cannot exec`, the script installs the `xz` package with `yum`, `dnf`, `apt-get`, or `apk` when one of those exists, then unpacks again. On a yum host that install command is `yum install -y xz`. When no package manager can install `xz`, the script unpacks the archive with Python.

On any other OS or architecture, the script installs the same version with `cargo install dbgen --version 0.8.0` into the install directory. That path needs Rust and network access. The published release has no macOS or non-x86_64 binary.

## Template

Write one `CREATE TABLE`. Put the generator expression for each column in `{{ ... }}`. Use the caller's table and column names.

```sql
CREATE TABLE `events` (
    `id` BIGINT NOT NULL {{ rownum }},
    `name` VARCHAR(64) {{ rand.regex('[A-Za-z0-9]{8,32}') }},
    `created_at` TIMESTAMP {{ TIMESTAMP '2020-01-01 00:00:00' + INTERVAL rand.range(0, 157680000) SECOND }}
);
```

Assign a per-row value inside a column expression. A `{{ ... }}` block before `CREATE TABLE` runs once and is then reused for every row.

```sql
`payload` TEXT {{ @c := rand.regex('[A-Za-z0-9]{1024}'); @c || @c || @c || @c }}
```

Repeat a short random chunk with `||` when a column has to add bulk. Generating one long `rand.regex(...)` is slower. Keep CSV field values free of NUL bytes. Expression and flag details: [Template.md](https://github.com/kennytm/dbgen/blob/v0.8.0/Template.md), [CLI.md](https://github.com/kennytm/dbgen/blob/v0.8.0/CLI.md).

## Size each file to 256 MiB

dbgen accepts row counts, not byte sizes. Calibrate with the same format flags as the final run.

```bash
cal_rows=1000
dbgen -i template.sql -o "$CAL_DIR" -N "$cal_rows" -R "$cal_rows" -f csv --headers --time-zone UTC -q -j 1
```

Measure the numbered data file, not `*-schema.sql`.

```text
row_bytes = data_file_bytes / cal_rows
rows_per_file = max(1, 268435456 / row_bytes)
```

- No total size requested: `-N` and `-R` are both `rows_per_file` (one file).
- Total size requested: `file_count = max(1, round(total_bytes / 268435456))`, then `-R rows_per_file` and `-N rows_per_file * file_count`.
- If one row is already at least 256 MiB, use `-R 1` and report that a file cannot be smaller than one row.

Set `-j` to the CPUs this environment may use (`nproc` when it reflects the limit). Do not let dbgen pick a host CPU count that exceeds a container limit.

## Generate

Check that the output filesystem has room for the planned bytes before a large run.

```bash
dbgen -i template.sql -o "$OUT_DIR" -N "$TOTAL_ROWS" -R "$ROWS_PER_FILE" -f csv --headers --time-zone UTC -j "$JOBS"
```

For a run that should outlive the current session, start it detached and record the pid. Do not assume `ps` exists. On Linux, `/proc/$pid` shows whether it is still running. A zombie there means the process already exited; judge success from the files.

## Check the result

- Numbered data files exist, and `*-schema.sql` exists unless schemas were disabled.
- Finished data files are near 256 MiB. A partial final file is expected only when `-N` is not a multiple of `-R`.
- Read one header row and confirm it matches the template columns.
- Report the output directory, file count, byte total, and the `dbgen --version` string.
