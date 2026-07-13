from scopelint.checker import ChangedFile
from scopelint.cli import run


def _fake_collector(files: list[ChangedFile]):
    def collect_files(cwd=None):
        return files

    return collect_files


def test_run_returns_zero_when_changes_are_in_scope():
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    collect_files = _fake_collector(files)

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘"],
        collect_files=collect_files,
    )

    assert exit_code == 0


def test_run_returns_nonzero_when_scope_creep_detected():
    files = [
        ChangedFile(path="src/auth/login.py", insertions=10, deletions=2),
        ChangedFile(path="src/billing/invoice.py", insertions=40, deletions=0),
    ]
    collect_files = _fake_collector(files)

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘"],
        collect_files=collect_files,
    )

    assert exit_code == 1


def test_run_reads_task_from_file(tmp_path):
    task_file = tmp_path / "task.txt"
    task_file.write_text("로그인(login) 버그를 수정해줘")
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    collect_files = _fake_collector(files)

    exit_code = run(
        ["--task-file", str(task_file)],
        collect_files=collect_files,
    )

    assert exit_code == 0
