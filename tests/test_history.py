from scopelint.checker import ScopeFinding
from scopelint.history import HistoryEntry, load_history, record_result


def test_record_and_load_round_trip(tmp_path):
    log_path = tmp_path / "history.jsonl"
    entry = HistoryEntry(
        timestamp="2026-07-14T00:00:00+00:00",
        task="로그인 버그 수정",
        ok=False,
        findings=[ScopeFinding(path="requirements.txt", reason="민감 파일 변경")],
    )

    record_result(str(log_path), entry)
    loaded = load_history(str(log_path))

    assert loaded == [entry]


def test_record_appends_multiple_entries(tmp_path):
    log_path = tmp_path / "history.jsonl"
    entry1 = HistoryEntry(timestamp="t1", task="a", ok=True, findings=[])
    entry2 = HistoryEntry(timestamp="t2", task="b", ok=False, findings=[])

    record_result(str(log_path), entry1)
    record_result(str(log_path), entry2)

    assert load_history(str(log_path)) == [entry1, entry2]


def test_load_history_missing_file_returns_empty_list(tmp_path):
    log_path = tmp_path / "does-not-exist.jsonl"

    assert load_history(str(log_path)) == []


def test_record_result_creates_parent_directories(tmp_path):
    log_path = tmp_path / "nested" / "dir" / "history.jsonl"
    entry = HistoryEntry(timestamp="t1", task="a", ok=True, findings=[])

    record_result(str(log_path), entry)

    assert load_history(str(log_path)) == [entry]
