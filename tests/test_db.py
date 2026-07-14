from scopelint.checker import ScopeFinding
from scopelint.db import create_team, get_team_by_api_key, insert_check, list_checks
from scopelint.history import HistoryEntry


def test_create_team_returns_team_with_unique_api_key(tmp_path):
    db_path = str(tmp_path / "scopelint.db")

    team_a = create_team(db_path, "team-a")
    team_b = create_team(db_path, "team-b")

    assert team_a.name == "team-a"
    assert team_a.api_key != team_b.api_key
    assert team_a.id != team_b.id


def test_get_team_by_api_key_finds_created_team(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    team = create_team(db_path, "team-a")

    found = get_team_by_api_key(db_path, team.api_key)

    assert found == team


def test_get_team_by_api_key_returns_none_for_unknown_key(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    create_team(db_path, "team-a")

    assert get_team_by_api_key(db_path, "not-a-real-key") is None


def test_insert_check_and_list_checks_round_trip(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    team = create_team(db_path, "team-a")
    entry = HistoryEntry(
        timestamp="2026-07-14T00:00:00+00:00",
        task="로그인 버그 수정",
        ok=False,
        findings=[ScopeFinding(path="requirements.txt", reason="민감 파일 변경")],
    )

    insert_check(db_path, team.id, entry)

    assert list_checks(db_path, team.id) == [entry]


def test_list_checks_scoped_per_team(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    team_a = create_team(db_path, "team-a")
    team_b = create_team(db_path, "team-b")
    entry_a = HistoryEntry(timestamp="t1", task="a", ok=True, findings=[])
    entry_b = HistoryEntry(timestamp="t2", task="b", ok=False, findings=[])

    insert_check(db_path, team_a.id, entry_a)
    insert_check(db_path, team_b.id, entry_b)

    assert list_checks(db_path, team_a.id) == [entry_a]
    assert list_checks(db_path, team_b.id) == [entry_b]


def test_list_checks_empty_for_team_with_no_checks(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    team = create_team(db_path, "team-a")

    assert list_checks(db_path, team.id) == []
