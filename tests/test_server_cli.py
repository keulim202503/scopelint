from scopelint.db import get_team_by_api_key
from scopelint.server_cli import run


def test_create_team_prints_api_key_and_persists_team(tmp_path, capsys):
    db_path = str(tmp_path / "scopelint.db")

    exit_code = run(["create-team", "team-a", "--db-path", db_path])

    assert exit_code == 0
    printed = capsys.readouterr().out
    team = get_team_by_api_key(db_path, printed.strip().splitlines()[-1])
    assert team is not None
    assert team.name == "team-a"


def test_run_subcommand_invokes_injected_serve(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    calls = []

    def fake_serve(app, host, port):
        calls.append((host, port))

    exit_code = run(
        ["run", "--db-path", db_path, "--host", "0.0.0.0", "--port", "9000"],
        serve=fake_serve,
    )

    assert exit_code == 0
    assert calls == [("0.0.0.0", 9000)]


def test_run_subcommand_defaults_host_and_port(tmp_path):
    db_path = str(tmp_path / "scopelint.db")
    calls = []

    def fake_serve(app, host, port):
        calls.append((host, port))

    run(["run", "--db-path", db_path], serve=fake_serve)

    assert calls == [("127.0.0.1", 8000)]
