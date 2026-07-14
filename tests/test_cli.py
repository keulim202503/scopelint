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


def _fake_pr_collector(files: list[ChangedFile]):
    def collect_pr_files(repo, pr_number, cwd=None):
        return files

    return collect_pr_files


def test_run_with_pr_uses_pr_collector_and_explicit_repo():
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    collect_pr_files = _fake_pr_collector(files)

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘", "--pr", "42", "--repo", "owner/repo"],
        collect_pr_files=collect_pr_files,
    )

    assert exit_code == 0


def test_run_with_pr_resolves_repo_when_not_given():
    files = [ChangedFile(path="src/billing/invoice.py", insertions=40, deletions=0)]
    collect_pr_files = _fake_pr_collector(files)
    resolve_repo_calls = []

    def resolve_repo(cwd=None):
        resolve_repo_calls.append(cwd)
        return "owner/repo"

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘", "--pr", "7"],
        collect_pr_files=collect_pr_files,
        resolve_repo=resolve_repo,
    )

    assert exit_code == 1
    assert resolve_repo_calls == [None]


def test_run_writes_log_entry_when_log_file_given(tmp_path):
    files = [ChangedFile(path="src/billing/invoice.py", insertions=40, deletions=0)]
    collect_files = _fake_collector(files)
    log_path = tmp_path / "history.jsonl"
    recorded = []

    def fake_record(path, entry):
        recorded.append((path, entry))

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘", "--log-file", str(log_path)],
        collect_files=collect_files,
        record=fake_record,
    )

    assert exit_code == 1
    assert len(recorded) == 1
    logged_path, entry = recorded[0]
    assert logged_path == str(log_path)
    assert entry.ok is False
    assert entry.findings


def test_run_does_not_record_when_log_file_not_given():
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    collect_files = _fake_collector(files)
    recorded = []

    def fake_record(path, entry):
        recorded.append((path, entry))

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘"],
        collect_files=collect_files,
        record=fake_record,
    )

    assert exit_code == 0
    assert recorded == []


def test_run_posts_to_remote_when_remote_url_and_api_key_given():
    files = [ChangedFile(path="src/billing/invoice.py", insertions=40, deletions=0)]
    collect_files = _fake_collector(files)
    posted = []

    def fake_post_result(remote_url, api_key, entry):
        posted.append((remote_url, api_key, entry))

    exit_code = run(
        [
            "--task",
            "로그인(login) 버그를 수정해줘",
            "--remote-url",
            "https://scopelint.example.com",
            "--api-key",
            "test-key",
        ],
        collect_files=collect_files,
        post_result=fake_post_result,
    )

    assert exit_code == 1
    assert len(posted) == 1
    remote_url, api_key, entry = posted[0]
    assert remote_url == "https://scopelint.example.com"
    assert api_key == "test-key"
    assert entry.ok is False
    assert entry.findings


def test_run_does_not_post_when_remote_url_not_given():
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    collect_files = _fake_collector(files)
    posted = []

    def fake_post_result(remote_url, api_key, entry):
        posted.append((remote_url, api_key, entry))

    exit_code = run(
        ["--task", "로그인(login) 버그를 수정해줘"],
        collect_files=collect_files,
        post_result=fake_post_result,
    )

    assert exit_code == 0
    assert posted == []


def test_run_exits_with_error_when_remote_url_given_without_api_key(capsys):
    exit_code = None
    try:
        run(["--task", "로그인(login) 버그를 수정해줘", "--remote-url", "https://scopelint.example.com"])
    except SystemExit as e:
        exit_code = e.code

    assert exit_code == 2
    assert "--api-key" in capsys.readouterr().err
