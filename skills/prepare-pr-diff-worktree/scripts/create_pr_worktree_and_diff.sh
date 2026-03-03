#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: create_pr_worktree_and_diff.sh [--project-path <path>] <pr-link-or-number>

Creates an isolated git worktree for the target PR, checks out the PR code,
writes <pr-number>.diff in the worktree root, and prints JSON metadata.

Authentication behavior:
- Preferred: authenticated gh (`gh auth login`)
- Fallback: if gh is unauthenticated, uses git+curl for public GitHub PRs

Execution behavior:
- If run inside a git repository, `--project-path` is optional.
- If run outside a git repository, `--project-path` is required.
USAGE
}

error() {
  echo "Error: $*" >&2
  exit 1
}

is_number() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

parse_pr_url() {
  local input="$1"
  if [[ "$input" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)(/.*)?(\?.*)?$ ]]; then
    printf '%s/%s %s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
    return 0
  fi
  return 1
}

parse_github_repo_from_remote() {
  local remote_url="$1"
  if [[ "$remote_url" =~ ^https?://github\.com/([^/]+)/([^/]+?)(\.git)?$ ]]; then
    printf '%s/%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    return 0
  fi
  if [[ "$remote_url" =~ ^git@github\.com:([^/]+)/([^/]+?)(\.git)?$ ]]; then
    printf '%s/%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

project_path=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-path|-p)
      [[ $# -ge 2 ]] || error "missing value for $1"
      project_path="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -* )
      error "unknown option: $1"
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

pr_input="$1"

command -v git >/dev/null 2>&1 || error "git is required."

if [[ -n "$project_path" ]]; then
  [[ -d "$project_path" ]] || error "project path does not exist: $project_path"
  repo_root="$(git -C "$project_path" rev-parse --show-toplevel 2>/dev/null || true)"
  [[ -n "$repo_root" ]] || error "project path is not inside a git repository: $project_path"
else
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  [[ -n "$repo_root" ]] || error "current directory is not inside a git repository. Re-run with --project-path <repo_path>."
fi

repo_root="$(cd "$repo_root" && pwd -P)"
origin_url="$(git -C "$repo_root" remote get-url origin 2>/dev/null || true)"
remote_owner_repo="$(parse_github_repo_from_remote "$origin_url" 2>/dev/null || true)"

gh_installed=false
gh_authed=false
if command -v gh >/dev/null 2>&1; then
  gh_installed=true
  if gh auth status >/dev/null 2>&1; then
    gh_authed=true
  fi
fi

owner_repo=""
pr_number=""
if parsed="$(parse_pr_url "$pr_input" 2>/dev/null)"; then
  owner_repo="${parsed% *}"
  pr_number="${parsed##* }"
elif is_number "$pr_input"; then
  pr_number="$pr_input"
else
  error "input must be a full GitHub PR URL or numeric PR number: $pr_input"
fi

if [[ -z "$owner_repo" && -n "$remote_owner_repo" ]]; then
  owner_repo="$remote_owner_repo"
fi

if [[ "$gh_authed" != "true" ]]; then
  command -v curl >/dev/null 2>&1 || error "curl is required for unauthenticated fallback mode."
fi

if [[ -z "$pr_number" ]]; then
  error "unable to determine PR number from input: $pr_input"
fi
if [[ -z "$owner_repo" ]]; then
  error "cannot infer GitHub owner/repo from origin remote. Provide a full PR URL or configure origin to GitHub."
fi

mkdir -p "${repo_root}/worktrees"

base_work_tree="pr-${pr_number}"
work_tree="${base_work_tree}"
code_path="${repo_root}/worktrees/${work_tree}"
suffix=1
while [[ -e "$code_path" ]]; do
  work_tree="${base_work_tree}-${suffix}"
  code_path="${repo_root}/worktrees/${work_tree}"
  suffix=$((suffix + 1))
done

created_worktree=false
cleanup_on_error() {
  if [[ "$created_worktree" == "true" ]]; then
    git -C "$repo_root" worktree remove --force "$code_path" >/dev/null 2>&1 || true
  fi
}
trap cleanup_on_error ERR

git -C "$repo_root" worktree add "$code_path" HEAD >/dev/null
created_worktree=true

repo_fetch_url="https://github.com/${owner_repo}.git"
pr_url="https://github.com/${owner_repo}/pull/${pr_number}"
diff_filename="${pr_number}.diff"

checkout_with_git_fallback() {
  (
    cd "$code_path"
    git fetch --no-tags --depth=1 "$repo_fetch_url" "pull/${pr_number}/head" >/dev/null
    git checkout --detach FETCH_HEAD >/dev/null
  )
}

write_diff_with_curl_fallback() {
  command -v curl >/dev/null 2>&1 || error "curl is required for unauthenticated diff export."
  curl -fsSL "${pr_url}.diff" -o "${code_path}/${diff_filename}"
}

if [[ "$gh_authed" == "true" ]]; then
  if ! (
    cd "$code_path"
    gh pr checkout "$pr_input" --detach >/dev/null
  ); then
    checkout_with_git_fallback
  fi
else
  checkout_with_git_fallback
fi

if [[ "$gh_authed" == "true" ]]; then
  if ! (
    cd "$code_path"
    gh pr diff "$pr_input" > "$diff_filename"
  ); then
    write_diff_with_curl_fallback
  fi
else
  write_diff_with_curl_fallback
fi

trap - ERR
created_worktree=false
printf '{"code_path":"%s","diff_filename":"%s","work_tree":"%s"}\n' "$code_path" "$diff_filename" "$work_tree"
