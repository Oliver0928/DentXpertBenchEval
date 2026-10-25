import argparse
from pathlib import Path

from bench.convert import load_cases, write_cases


PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert/export DentXpertBench cases into the standard data directory.")
    parser.add_argument("source", type=Path, help="Source JSON exported from the annotation website.")
    parser.add_argument("--task-code", default="A1.1")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "tasks/A1.1/cases.json")
    args = parser.parse_args()

    cases = load_cases(args.source)
    write_cases(args.output, cases, args.task_code)
    print(f"Prepared {len(cases)} cases at {args.output}")


if __name__ == "__main__":
    main()

