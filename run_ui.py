"""현재 작업 폴더와 무관하게 가변 휠 UI를 실행하는 launcher."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from app import main as run_application


def build_parser() -> argparse.ArgumentParser:
    """Launcher command line parser를 생성한다."""

    parser = argparse.ArgumentParser(description="가변 휠 기본 제어 UI 실행")
    parser.add_argument(
        "--check",
        action="store_true",
        help="UI를 열지 않고 module import 상태만 확인합니다.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """명령행 옵션을 처리하고 UI를 실행한다."""

    args = build_parser().parse_args(argv)
    if args.check:
        print("UI launcher import check: OK")
        return 0

    run_application()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
