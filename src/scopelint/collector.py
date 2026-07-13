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
