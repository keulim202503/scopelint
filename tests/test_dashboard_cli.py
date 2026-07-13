from scopelint.checker import ScopeFinding
from scopelint.dashboard_cli import run
from scopelint.history import HistoryEntry


def _fake_loader(entries):
    def load(log_path):
        return entries

    return load


def test_run_prints_summary_text(capsys):
    entries = [
        HistoryEntry(timestamp="t", task="task", ok=False, findings=[ScopeFinding(path="a.py", reason="r")]),
    ]

    exit_code = run(["--log-file", "unused.jsonl"], load=_fake_loader(entries))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "a.py" in captured.out


def test_run_writes_html_report(tmp_path):
    entries = []
    html_path = tmp_path / "report.html"

    exit_code = run(
        ["--log-file", "unused.jsonl", "--html", str(html_path)],
        load=_fake_loader(entries),
    )

    assert exit_code == 0
    assert html_path.exists()
    assert "<table" in html_path.read_text()
