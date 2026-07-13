import json
from unittest.mock import MagicMock, patch

from scopelint.collector import collect_pr_changed_files, parse_git_diff_numstat, parse_gh_pr_files, resolve_repo_slug


def test_parses_single_file_numstat():
    output = "12\t3\tsrc/foo.py\n"
    files = parse_git_diff_numstat(output)

    assert len(files) == 1
    assert files[0].path == "src/foo.py"
    assert files[0].insertions == 12
    assert files[0].deletions == 3


def test_parses_multiple_files():
    output = "5\t0\ta.py\n0\t7\tb.py\n"
    files = parse_git_diff_numstat(output)

    assert [f.path for f in files] == ["a.py", "b.py"]


def test_handles_binary_file_dash_markers():
    output = "-\t-\tassets/logo.png\n"
    files = parse_git_diff_numstat(output)

    assert len(files) == 1
    assert files[0].path == "assets/logo.png"
    assert files[0].insertions == 0
    assert files[0].deletions == 0


def test_empty_output_returns_no_files():
    assert parse_git_diff_numstat("") == []


def test_parses_gh_pr_files_json():
    output = json.dumps(
        [
            {"filename": "src/foo.py", "additions": 12, "deletions": 3},
            {"filename": "src/bar.py", "additions": 0, "deletions": 5},
        ]
    )
    files = parse_gh_pr_files(output)

    assert len(files) == 2
    assert files[0].path == "src/foo.py"
    assert files[0].insertions == 12
    assert files[0].deletions == 3
    assert files[1].path == "src/bar.py"


def test_parses_gh_pr_files_empty_array():
    assert parse_gh_pr_files("[]") == []


@patch("scopelint.collector.subprocess.run")
def test_collect_pr_changed_files_invokes_gh_api(mock_run):
    mock_run.return_value = MagicMock(
        stdout=json.dumps([{"filename": "src/foo.py", "additions": 1, "deletions": 0}])
    )

    files = collect_pr_changed_files("owner/repo", 42)

    assert len(files) == 1
    assert files[0].path == "src/foo.py"
    called_args = mock_run.call_args.args[0]
    assert called_args[:2] == ["gh", "api"]
    assert "repos/owner/repo/pulls/42/files" in called_args


@patch("scopelint.collector.subprocess.run")
def test_resolve_repo_slug_invokes_gh_repo_view(mock_run):
    mock_run.return_value = MagicMock(stdout="owner/repo\n")

    slug = resolve_repo_slug()

    assert slug == "owner/repo"
    called_args = mock_run.call_args.args[0]
    assert called_args[:3] == ["gh", "repo", "view"]
