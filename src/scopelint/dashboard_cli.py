import argparse
import sys
from collections.abc import Sequence

from scopelint.dashboard import render_html, render_text, summarize
from scopelint.history import load_history


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scopelint-dashboard",
        description="scopelint --log-file로 쌓인 기록을 집계해 반복되는 스코프 크립 패턴을 보여줍니다.",
    )
    parser.add_argument("--log-file", required=True, help="scopelint --log-file로 기록된 JSONL 경로")
    parser.add_argument("--html", default=None, help="HTML 리포트를 저장할 경로 (선택)")
    return parser


def run(argv: Sequence[str], load=load_history) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    entries = load(args.log_file)
    summary = summarize(entries)

    print(render_text(summary))

    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(summary))
        print(f"\nHTML 리포트 저장됨: {args.html}")

    return 0


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
