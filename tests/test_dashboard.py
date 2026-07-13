from scopelint.checker import ScopeFinding
from scopelint.dashboard import render_html, render_text, summarize
from scopelint.history import HistoryEntry


def _entry(ok, findings=None):
    return HistoryEntry(timestamp="t", task="task", ok=ok, findings=findings or [])


def test_summarize_computes_rate_and_totals():
    entries = [
        _entry(ok=True),
        _entry(ok=False, findings=[ScopeFinding(path="requirements.txt", reason="r")]),
        _entry(ok=False, findings=[ScopeFinding(path="requirements.txt", reason="r")]),
    ]

    summary = summarize(entries)

    assert summary.total_checks == 3
    assert summary.scope_creep_checks == 2
    assert summary.scope_creep_rate == 2 / 3


def test_summarize_ranks_repeat_offender_files():
    entries = [
        _entry(ok=False, findings=[ScopeFinding(path="a.py", reason="r")]),
        _entry(
            ok=False,
            findings=[ScopeFinding(path="a.py", reason="r"), ScopeFinding(path="b.py", reason="r")],
        ),
        _entry(ok=False, findings=[ScopeFinding(path="a.py", reason="r")]),
    ]

    summary = summarize(entries)

    assert summary.top_offenders[0].path == "a.py"
    assert summary.top_offenders[0].count == 3
    assert summary.top_offenders[1].path == "b.py"
    assert summary.top_offenders[1].count == 1


def test_summarize_empty_history():
    summary = summarize([])

    assert summary.total_checks == 0
    assert summary.scope_creep_checks == 0
    assert summary.scope_creep_rate == 0.0
    assert summary.top_offenders == []


def test_render_text_includes_key_numbers():
    entries = [_entry(ok=False, findings=[ScopeFinding(path="a.py", reason="r")])]
    summary = summarize(entries)

    text = render_text(summary)

    assert "1" in text
    assert "a.py" in text


def test_render_html_includes_table_row():
    entries = [_entry(ok=False, findings=[ScopeFinding(path="a.py", reason="r")])]
    summary = summarize(entries)

    html = render_html(summary)

    assert "<table" in html
    assert "a.py" in html
