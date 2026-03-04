#!/usr/bin/env python3
"""Merge review-output-format JSON files and submit one GitHub PR review."""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {
    "Blocker": 0,
    "Major": 1,
    "Minor": 2,
    "Info": 3,
    "Nit": 4,
}

SEVERITY_EMOJI = {
    "Blocker": "🚨",
    "Major": "⚠️",
    "Minor": "🟡",
    "Info": "ℹ️",
    "Nit": "🧹",
}

PR_LINK_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)(?:/.*|\?.*)?$"
)
SCOPE_ANCHOR_RE = re.compile(
    r"(?P<path>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+):(?P<line>\d+)"
)


class InputError(RuntimeError):
    """Input contract violation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge review-output-format files and submit one PR review with "
            "one inline comment per finding."
        )
    )
    parser.add_argument(
        "--pr-link",
        required=True,
        help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Input JSON file (repeatable).",
    )
    parser.add_argument(
        "--input-glob",
        action="append",
        default=[],
        help="Input JSON glob pattern (repeatable).",
    )
    parser.add_argument(
        "--merged-output",
        default="merged-review-output.json",
        help="Output path for merged findings JSON.",
    )
    parser.add_argument(
        "--payload-output",
        default="github-review-payload.json",
        help="Output path for GitHub review payload.",
    )
    parser.add_argument(
        "--event",
        default="COMMENT",
        help="Review event passed to GitHub review API (default: COMMENT).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate outputs only; do not submit to GitHub.",
    )
    return parser.parse_args()


def parse_pr_link(pr_link: str) -> tuple[str, str, int]:
    match = PR_LINK_RE.match(pr_link.strip())
    if not match:
        raise InputError(
            "--pr-link must be a full GitHub pull request URL: "
            "https://github.com/<owner>/<repo>/pull/<number>"
        )
    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))
    return owner, repo, number


def collect_input_files(inputs: list[str], input_globs: list[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[str] = set()

    for raw in inputs:
        path = Path(raw).expanduser()
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            collected.append(path)
            seen.add(key)

    for pattern in input_globs:
        matches = sorted(glob.glob(pattern, recursive=True))
        if not matches:
            raise InputError(f"--input-glob pattern matched no files: {pattern}")
        for raw in matches:
            path = Path(raw).expanduser()
            key = str(path.resolve()) if path.exists() else str(path)
            if key not in seen:
                collected.append(path)
                seen.add(key)

    if not collected:
        raise InputError("Provide at least one --input or --input-glob")

    for path in collected:
        if not path.exists():
            raise InputError(f"Input file does not exist: {path}")
        if not path.is_file():
            raise InputError(f"Input path is not a file: {path}")

    return collected


def load_findings_from_file(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise InputError(f"Top-level JSON in {path} must be an object")

    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise InputError(f"`findings` must be an array in {path}")

    typed_findings: list[dict[str, Any]] = []
    for idx, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            raise InputError(f"finding #{idx} in {path} must be an object")
        typed_findings.append(finding)
    return typed_findings


def severity_rank(finding: dict[str, Any]) -> int:
    severity = finding.get("severity")
    if not isinstance(severity, str):
        return len(SEVERITY_ORDER)
    return SEVERITY_ORDER.get(severity, len(SEVERITY_ORDER))


def dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for finding in findings:
        marker = json.dumps(finding, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(finding)
    return deduped


def normalize_path(path: str) -> str:
    value = path.strip()
    if value.startswith("./"):
        value = value[2:]
    return value


def parse_line(raw: Any) -> int | None:
    if isinstance(raw, int) and raw > 0:
        return raw
    if isinstance(raw, str) and raw.isdigit():
        line = int(raw)
        return line if line > 0 else None
    return None


def extract_anchor(finding: dict[str, Any]) -> dict[str, Any] | None:
    path = finding.get("path")
    line = parse_line(finding.get("line"))

    if isinstance(path, str) and line is not None:
        side = finding.get("side") if isinstance(finding.get("side"), str) else "RIGHT"
        side = side if side in {"LEFT", "RIGHT"} else "RIGHT"

        anchor: dict[str, Any] = {
            "path": normalize_path(path),
            "line": line,
            "side": side,
        }

        start_line = parse_line(finding.get("start_line"))
        start_side = finding.get("start_side") if isinstance(finding.get("start_side"), str) else None
        if start_line is not None and start_side in {"LEFT", "RIGHT"}:
            anchor["start_line"] = start_line
            anchor["start_side"] = start_side
        return anchor

    scope = finding.get("scope")
    if isinstance(scope, str):
        match = SCOPE_ANCHOR_RE.search(scope.replace("`", ""))
        if match:
            return {
                "path": normalize_path(match.group("path")),
                "line": int(match.group("line")),
                "side": "RIGHT",
            }

    return None


def get_severity(finding: dict[str, Any]) -> str:
    severity = finding.get("severity")
    if isinstance(severity, str) and severity in SEVERITY_ORDER:
        return severity
    return "Info"


def get_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        return text if text else fallback
    return fallback


def format_finding_markdown(finding: dict[str, Any], fallback_scope: str = "") -> str:
    severity = get_severity(finding)
    emoji = SEVERITY_EMOJI.get(severity, "ℹ️")
    title = get_text(finding.get("title"), "Untitled finding")

    fields: list[tuple[str, str]] = []

    why = get_text(finding.get("why"))
    if why:
        fields.append(("Why", why))

    scope = get_text(finding.get("scope"), fallback_scope)
    if scope:
        fields.append(("Scope", scope))

    risk = get_text(finding.get("risk_if_unchanged"))
    if risk:
        fields.append(("Risk if unchanged", risk))

    evidence = get_text(finding.get("evidence"))
    if evidence:
        fields.append(("Evidence", evidence))

    change_request = get_text(finding.get("change_request"), "Please address this finding.")
    fields.append(("Change request", change_request))

    lines: list[str] = [f"#### {emoji} **[{severity}]** {title}", ""]
    for label, value in fields:
        lines.append(f"**{label}**")
        lines.append(value)
        lines.append("")

    return "\n".join(lines).rstrip()


def build_summary(findings: list[dict[str, Any]], inline_count: int, summary_only: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "**AI-generated review based on @D3Hunter's standards; manual review will be performed after all comments are resolved.**",
        "",
        "### Summary",
        "",
        f"- Total findings: {len(findings)}",
        f"- Inline comments: {inline_count}",
        f"- Summary-only findings (no inline anchor): {len(summary_only)}",
        "",
    ]

    lines.append("<details>")
    lines.append("<summary>Findings (highest risk first)</summary>")
    lines.append("")

    if not findings:
        lines.append("No findings.")
        lines.append("")
    else:
        grouped_findings: dict[str, list[dict[str, Any]]] = {severity: [] for severity in SEVERITY_ORDER}
        for finding in findings:
            grouped_findings[get_severity(finding)].append(finding)

        for severity in SEVERITY_ORDER:
            severity_findings = grouped_findings[severity]
            if not severity_findings:
                continue

            emoji = SEVERITY_EMOJI.get(severity, "ℹ️")
            lines.append(f"#### {emoji} **[{severity}]** ({len(severity_findings)})")
            lines.append("")

            for idx, finding in enumerate(severity_findings, start=1):
                title = get_text(finding.get("title"), "Untitled finding")
                scope = get_text(finding.get("scope"))
                scope_suffix = f" (`{scope}`)" if scope else ""
                lines.append(f"{idx}. {title}{scope_suffix}")
            lines.append("")

    lines.append("</details>")
    lines.append("")

    if summary_only:
        lines.extend(["### Unanchored findings", ""])

        grouped_unanchored: dict[str, list[dict[str, Any]]] = {severity: [] for severity in SEVERITY_ORDER}
        for finding in summary_only:
            grouped_unanchored[get_severity(finding)].append(finding)

        for severity in SEVERITY_ORDER:
            severity_findings = grouped_unanchored[severity]
            if not severity_findings:
                continue

            emoji = SEVERITY_EMOJI.get(severity, "ℹ️")
            lines.append(f"#### {emoji} **[{severity}]** ({len(severity_findings)})")
            lines.append("")

            for idx, finding in enumerate(severity_findings, start=1):
                title = get_text(finding.get("title"), "Untitled finding")
                lines.append(f"{idx}. {title}")
                scope = get_text(finding.get("scope"))
                if scope:
                    lines.append(f"   - Scope: `{scope}`")
                change_request = get_text(finding.get("change_request"))
                if change_request:
                    lines.append(f"   - Request: {change_request}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_payload(event: str, findings: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    comments: list[dict[str, Any]] = []
    summary_only: list[dict[str, Any]] = []

    for finding in findings:
        anchor = extract_anchor(finding)
        if anchor is None:
            summary_only.append(finding)
            continue

        fallback_scope = f"{anchor['path']}:{anchor['line']}"
        comment = {
            "path": anchor["path"],
            "line": anchor["line"],
            "side": anchor["side"],
            "body": format_finding_markdown(finding, fallback_scope=fallback_scope),
        }

        if "start_line" in anchor and "start_side" in anchor:
            comment["start_line"] = anchor["start_line"]
            comment["start_side"] = anchor["start_side"]

        comments.append(comment)

    payload = {
        "event": event,
        "body": build_summary(findings, inline_count=len(comments), summary_only=summary_only),
        "comments": comments,
    }
    return payload, summary_only


def run_gh_auth_check() -> None:
    result = subprocess.run(
        ["gh", "auth", "status"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        message = stderr if stderr else "gh auth status failed"
        raise RuntimeError(
            f"GitHub CLI is not authenticated. Run `gh auth login` first. Details: {message}"
        )


def submit_review(owner: str, repo: str, pr_number: int, payload_path: Path) -> dict[str, Any]:
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    result = subprocess.run(
        [
            "gh",
            "api",
            endpoint,
            "--method",
            "POST",
            "-H",
            "Accept: application/vnd.github+json",
            "--input",
            str(payload_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Failed to submit review via gh api: {details}")

    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub API returned non-JSON output: {result.stdout}") from exc


def main() -> int:
    args = parse_args()

    try:
        owner, repo, pr_number = parse_pr_link(args.pr_link)
        input_files = collect_input_files(args.input, args.input_glob)

        merged_findings: list[dict[str, Any]] = []
        for input_file in input_files:
            merged_findings.extend(load_findings_from_file(input_file))

        merged_findings = dedupe_findings(merged_findings)
        merged_findings = sorted(
            enumerate(merged_findings),
            key=lambda item: (severity_rank(item[1]), item[0]),
        )
        merged_findings = [finding for _, finding in merged_findings]

        merged_output_path = Path(args.merged_output)
        payload_output_path = Path(args.payload_output)

        merged_output_path.parent.mkdir(parents=True, exist_ok=True)
        payload_output_path.parent.mkdir(parents=True, exist_ok=True)

        merged_output_path.write_text(
            json.dumps({"findings": merged_findings}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        payload, summary_only = build_payload(args.event, merged_findings)
        payload_output_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        submitted = False
        review_id = None
        review_url = None

        if not args.dry_run:
            run_gh_auth_check()
            response = submit_review(owner, repo, pr_number, payload_output_path)
            submitted = True
            review_id = response.get("id")
            review_url = response.get("html_url")

        result = {
            "pr_link": args.pr_link,
            "inputs": [str(path) for path in input_files],
            "merged_output": str(merged_output_path),
            "payload_output": str(payload_output_path),
            "total_findings": len(merged_findings),
            "inline_comments": len(payload["comments"]),
            "summary_only_findings": len(summary_only),
            "submitted": submitted,
            "review_id": review_id,
            "review_url": review_url,
        }
        print(json.dumps(result, ensure_ascii=True))
        return 0

    except (InputError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
