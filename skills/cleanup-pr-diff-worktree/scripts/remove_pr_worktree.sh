#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: remove_pr_worktree.sh [--project-path <path>] (--work-tree <name> | --code-path <path>) [--force|--no-force]

Removes a PR worktree under <repo-root>/worktrees and prints JSON metadata.

Execution behavior:
- If run inside a git repository, --project-path is optional.
- If run outside a git repository, --project-path is required.

Removal behavior:
- Default uses force cleanup.
- --no-force fails when the worktree is dirty or non-empty.
USAGE
}

error() {
  echo "Error: $*" >&2
  exit 1
}

project_path=""
work_tree=""
code_path=""
force=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-path|-p)
      [[ $# -ge 2 ]] || error "missing value for $1"
      project_path="$2"
      shift 2
      ;;
    --work-tree|-w)
      [[ $# -ge 2 ]] || error "missing value for $1"
      work_tree="$2"
      shift 2
      ;;
    --code-path|-c)
      [[ $# -ge 2 ]] || error "missing value for $1"
      code_path="$2"
      shift 2
      ;;
    --force)
      force=true
      shift
      ;;
    --no-force)
      force=false
      shift
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
      error "unexpected positional argument: $1"
      ;;
  esac
done

if [[ -z "$work_tree" && -z "$code_path" ]]; then
  usage >&2
  error "one of --work-tree or --code-path is required"
fi

if [[ -n "$work_tree" && -n "$code_path" ]]; then
  error "--work-tree and --code-path are mutually exclusive"
fi

command -v git >/dev/null 2>&1 || error "git is required"

if [[ -n "$project_path" ]]; then
  [[ -d "$project_path" ]] || error "project path does not exist: $project_path"
  repo_root="$(git -C "$project_path" rev-parse --show-toplevel 2>/dev/null || true)"
  [[ -n "$repo_root" ]] || error "project path is not inside a git repository: $project_path"
else
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  [[ -n "$repo_root" ]] || error "current directory is not inside a git repository. Re-run with --project-path <repo_path>."
fi

repo_root="$(cd "$repo_root" && pwd -P)"
worktrees_root="${repo_root}/worktrees"

if [[ -n "$work_tree" ]]; then
  [[ "$work_tree" != */* ]] || error "--work-tree must be a folder name, not a path: $work_tree"
  [[ "$work_tree" != "." && "$work_tree" != ".." ]] || error "--work-tree is invalid: $work_tree"
  code_path="${worktrees_root}/${work_tree}"
else
  if [[ "$code_path" != /* ]]; then
    code_path="${repo_root}/${code_path}"
  fi
  code_path="${code_path%/}"
  work_tree="$(basename "$code_path")"
fi

if [[ "$code_path" != "${worktrees_root}/"* ]]; then
  error "cleanup target must be under ${worktrees_root}: ${code_path}"
fi

if [[ "$code_path" == *"/../"* || "$code_path" == *"/.." || "$code_path" == *"/./"* || "$code_path" == *"/." ]]; then
  error "cleanup target must be normalized without '.' or '..' path segments: ${code_path}"
fi

if [[ "$code_path" == "$worktrees_root" ]]; then
  error "cleanup target cannot be the worktrees root directory"
fi

removed=false
used_force=false
method="not-found"

registered=false
if git -C "$repo_root" worktree list --porcelain | grep -Fx "worktree $code_path" >/dev/null 2>&1; then
  registered=true
fi

if [[ "$registered" == "true" ]]; then
  if [[ "$force" == "true" ]]; then
    git -C "$repo_root" worktree remove --force "$code_path" >/dev/null
    used_force=true
  else
    git -C "$repo_root" worktree remove "$code_path" >/dev/null
  fi
  removed=true
  method="git-worktree-remove"
elif [[ -e "$code_path" ]]; then
  if [[ "$force" == "true" ]]; then
    rm -rf "$code_path"
    removed=true
    used_force=true
    method="rm-rf-stale-dir"
  else
    error "target exists but is not a registered worktree: ${code_path}. Re-run with --force to remove stale files."
  fi
fi

git -C "$repo_root" worktree prune >/dev/null 2>&1 || true
printf '{"code_path":"%s","work_tree":"%s","removed":%s,"used_force":%s,"method":"%s"}\n' "$code_path" "$work_tree" "$removed" "$used_force" "$method"
