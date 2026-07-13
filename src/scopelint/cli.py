import argparse
import sys
from collections.abc import Sequence

from scopelint.checker import ChangedFile, ScopeResult, check_scope
from scopelint.collector import collect_changed_files, collect_pr_changed_files, resolve_repo_slug


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scopelint",
        description="AI 코딩 에이전트의 실제 git diff가 요청한 작업 범위를 벗어났는지 탐지합니다.",
    )
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument("--task", help="에이전트에게 요청한 작업 설명 텍스트")
    task_group.add_argument("--task-file", help="작업 설명 텍스트가 담긴 파일 경로")
    parser.add_argument("--cwd", default=None, help="git diff를 실행할 저장소 경로")
    parser.add_argument("--pr", type=int, default=None, help="검사할 GitHub PR 번호 (gh CLI 필요)")
    parser.add_argument(
        "--repo", default=None, help="owner/repo 형식의 저장소 (기본: 현재 디렉터리에서 자동 추론)"
    )
    return parser


def _read_task(args: argparse.Namespace) -> str:
    if args.task is not None:
        return args.task
    with open(args.task_file, encoding="utf-8") as f:
        return f.read()


def run(
    argv: Sequence[str],
    collect_files=collect_changed_files,
    collect_pr_files=collect_pr_changed_files,
    resolve_repo=resolve_repo_slug,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    task_text = _read_task(args)

    if args.pr is not None:
        repo = args.repo or resolve_repo(cwd=args.cwd)
        changed_files: list[ChangedFile] = collect_pr_files(repo, args.pr, cwd=args.cwd)
    else:
        changed_files = collect_files(cwd=args.cwd)

    result: ScopeResult = check_scope(task_text, changed_files)

    if result.ok:
        print("OK: 모든 변경 사항이 작업 범위 안에 있습니다.")
        return 0

    print("SCOPE CREEP: 작업 범위를 벗어난 변경이 발견되었습니다.")
    for finding in result.findings:
        print(f"- {finding.reason}")
    return 1


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
