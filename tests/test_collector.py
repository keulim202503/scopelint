from scopelint.collector import parse_git_diff_numstat


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
