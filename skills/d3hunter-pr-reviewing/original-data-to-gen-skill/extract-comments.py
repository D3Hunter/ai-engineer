#!/usr/bin/env python3
"""
Fetch PR review comments by a specific GitHub user and output JSON grouped by PR.

Example:
  python v2.py --user D3Hunter --since 2024-01-01 --until 2024-12-31 --max-prs 50 --out d3hunter_comments.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GITHUB_API = "https://api.github.com"
DEFAULT_PER_PAGE = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get PR review comments by a GitHub user and output JSON grouped by PR."
    )
    parser.add_argument("--owner", default="pingcap", help="GitHub org/user (default: pingcap)")
    parser.add_argument("--repo", default="tidb", help="GitHub repo (default: tidb)")
    parser.add_argument("--user", default="D3Hunter", help="Reviewer username (default: D3Hunter)")
    parser.add_argument(
        "--since",
        help="PR created on/after this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--until",
        help="PR created on/before this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=None,
        help="Max number of PRs to scan from search results (default: no limit).",
    )
    parser.add_argument(
        "--out",
        default="review_comments.json",
        help="Output JSON file path (default: review_comments.json).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Total retry attempts for network/server errors (default: 5).",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=1.0,
        help="Retry backoff factor in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress to stderr.",
    )
    return parser.parse_args()


def parse_date(value: Optional[str], field: str) -> Optional[str]:
    if value is None:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid {field} date: {value} (expected YYYY-MM-DD)") from exc
    return value


def get_token() -> Optional[str]:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.getenv(name)
        if token:
            return token.strip()
    # Best-effort fallback to gh auth token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except FileNotFoundError:
        pass
    return None


def make_session(token: str, retries: int, backoff: float) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "v2-pr-review-comments",
        }
    )
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg, file=sys.stderr)


def github_get(
    session: requests.Session, url: str, timeout: int, params: Optional[Dict[str, Any]] = None
) -> requests.Response:
    response = session.get(url, params=params, timeout=timeout)
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        if remaining == "0" and reset:
            reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc).isoformat()
            raise SystemExit(
                "GitHub rate limit exceeded. "
                f"Limit resets at {reset_at}."
            )
    if not response.ok:
        raise SystemExit(
            f"GitHub API error {response.status_code}: {response.text.strip()}"
        )
    return response


def build_search_query(owner: str, repo: str, user: str, since: Optional[str], until: Optional[str]) -> str:
    query = f"repo:{owner}/{repo} is:pr reviewed-by:{user}"
    if since and until:
        query += f" created:{since}..{until}"
    elif since:
        query += f" created:>={since}"
    elif until:
        query += f" created:<={until}"
    return query


def search_prs(
    session: requests.Session,
    owner: str,
    repo: str,
    user: str,
    since: Optional[str],
    until: Optional[str],
    max_prs: Optional[int],
    timeout: int,
    verbose: bool,
) -> Iterable[Dict[str, Any]]:
    query = build_search_query(owner, repo, user, since, until)
    url = f"{GITHUB_API}/search/issues"
    page = 1
    fetched = 0

    while True:
        params = {
            "q": query,
            "sort": "created",
            "order": "asc",
            "per_page": DEFAULT_PER_PAGE,
            "page": page,
        }
        log(f"Searching PRs page {page}...", verbose)
        response = github_get(session, url, timeout, params=params)
        data = response.json()
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            yield item
            fetched += 1
            if max_prs is not None and fetched >= max_prs:
                return
        if len(items) < DEFAULT_PER_PAGE:
            break
        page += 1


def fetch_pr_details(
    session: requests.Session,
    owner: str,
    repo: str,
    pr_number: int,
    timeout: int,
) -> Dict[str, Any]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    response = github_get(session, url, timeout)
    return response.json()


def extract_comment_fields(comment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": comment.get("id"),
        "url": comment.get("html_url"),
        "api_url": comment.get("url"),
        "body": comment.get("body"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "path": comment.get("path"),
        "line": comment.get("line"),
        "original_line": comment.get("original_line"),
        "start_line": comment.get("start_line"),
        "original_start_line": comment.get("original_start_line"),
        "side": comment.get("side"),
        "start_side": comment.get("start_side"),
        "position": comment.get("position"),
        "diff_hunk": comment.get("diff_hunk"),
        "commit_id": comment.get("commit_id"),
        "original_commit_id": comment.get("original_commit_id"),
        "in_reply_to_id": comment.get("in_reply_to_id"),
        "pull_request_review_id": comment.get("pull_request_review_id"),
        "pull_request_review_url": comment.get("pull_request_review_url"),
    }


def fetch_review_comments_by_user(
    session: requests.Session,
    owner: str,
    repo: str,
    pr_number: int,
    user: str,
    timeout: int,
) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    page = 1
    results: List[Dict[str, Any]] = []
    user_lower = user.lower()

    while True:
        params = {"per_page": DEFAULT_PER_PAGE, "page": page}
        response = github_get(session, url, timeout, params=params)
        comments = response.json()
        if not comments:
            break
        for comment in comments:
            login = (comment.get("user") or {}).get("login", "")
            if login.lower() == user_lower:
                results.append(extract_comment_fields(comment))
        if len(comments) < DEFAULT_PER_PAGE:
            break
        page += 1
    return results


def build_pr_summary(pr: Dict[str, Any], comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "url": pr.get("html_url"),
        "state": pr.get("state"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "merged_at": pr.get("merged_at"),
        "is_draft": pr.get("draft"),
        "author": (pr.get("user") or {}).get("login"),
        "base_ref": (pr.get("base") or {}).get("ref"),
        "head_ref": (pr.get("head") or {}).get("ref"),
        "review_comments_count": len(comments),
        "review_comments": comments,
    }


def main() -> int:
    args = parse_args()
    since = parse_date(args.since, "--since")
    until = parse_date(args.until, "--until")

    token = get_token()
    if not token:
        print(
            "Missing GitHub token. Set GITHUB_TOKEN or GH_TOKEN, or login via `gh auth login`.",
            file=sys.stderr,
        )
        return 2

    session = make_session(token, args.retries, args.backoff)
    query = build_search_query(args.owner, args.repo, args.user, since, until)

    log(f"Search query: {query}", args.verbose)

    output: Dict[str, Any] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "repo": f"{args.owner}/{args.repo}",
        "user": args.user,
        "query": query,
        "since": since,
        "until": until,
        "max_prs": args.max_prs,
        "prs": [],
        "totals": {
            "prs_scanned": 0,
            "prs_with_comments": 0,
            "review_comments": 0,
        },
    }

    for item in search_prs(
        session,
        args.owner,
        args.repo,
        args.user,
        since,
        until,
        args.max_prs,
        args.timeout,
        args.verbose,
    ):
        output["totals"]["prs_scanned"] += 1
        pr_number = item.get("number")
        if pr_number is None:
            continue

        log(f"Fetching comments for PR #{pr_number}...", args.verbose)
        comments = fetch_review_comments_by_user(
            session, args.owner, args.repo, pr_number, args.user, args.timeout
        )
        if not comments:
            continue

        log(f"Fetching PR details for #{pr_number}...", args.verbose)
        pr_details = fetch_pr_details(
            session, args.owner, args.repo, pr_number, args.timeout
        )
        summary = build_pr_summary(pr_details, comments)
        output["prs"].append(summary)
        output["totals"]["prs_with_comments"] += 1
        output["totals"]["review_comments"] += len(comments)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=True)
        f.write("\n")

    log(f"Wrote {args.out}", args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
