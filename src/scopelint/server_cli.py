import argparse
import sys
from collections.abc import Sequence

from scopelint.db import create_team as db_create_team

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000


def _uvicorn_serve(app, host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scopelint-server",
        description="ScopeLint 팀 대시보드 백엔드 서버",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_team_parser = subparsers.add_parser("create-team", help="새 팀을 생성하고 API 키를 발급합니다")
    create_team_parser.add_argument("name", help="팀 이름")
    create_team_parser.add_argument("--db-path", default="scopelint.db", help="SQLite DB 경로")

    run_parser = subparsers.add_parser("run", help="서버를 실행합니다")
    run_parser.add_argument("--db-path", default="scopelint.db", help="SQLite DB 경로")
    run_parser.add_argument("--host", default=_DEFAULT_HOST, help="바인딩할 호스트")
    run_parser.add_argument("--port", type=int, default=_DEFAULT_PORT, help="바인딩할 포트")

    return parser


def run(argv: Sequence[str], create_team=db_create_team, serve=_uvicorn_serve) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create-team":
        team = create_team(args.db_path, args.name)
        print(f"팀 생성됨: {team.name}")
        print(team.api_key)
        return 0

    from scopelint.server import create_app

    app = create_app(args.db_path)
    serve(app, args.host, args.port)
    return 0


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
