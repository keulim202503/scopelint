import json
import subprocess

from scopelint.checker import ChangedFile


def parse_git_diff_numstat(output: str) -> list[ChangedFile]:
    files = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ins_str, del_str, path = parts
        insertions = int(ins_str) if ins_str.isdigit() else 0
        deletions = int(del_str) if del_str.isdigit() else 0
        files.append(ChangedFile(path=path, insertions=insertions, deletions=deletions))
    return files


def collect_changed_files(cwd: str | None = None) -> list[ChangedFile]:
    result = subprocess.run(
        ["git", "diff", "--numstat"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_git_diff_numstat(result.stdout)


def parse_gh_pr_files(output: str) -> list[ChangedFile]:
    files = []
    for entry in json.loads(output):
        files.append(
            ChangedFile(
                path=entry["filename"],
                insertions=entry.get("additions", 0),
                deletions=entry.get("deletions", 0),
            )
        )
    return files


def collect_pr_changed_files(repo: str, pr_number: int, cwd: str | None = None) -> list[ChangedFile]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{pr_number}/files", "--paginate"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_gh_pr_files(result.stdout)


def resolve_repo_slug(cwd: str | None = None) -> str:
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
