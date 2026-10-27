import argparse
import json
from pathlib import Path
from typing import Any

from bench.metrics.report import summarize_fields
from bench.protocol import (
    A11_FIELD_KEYS,
    A12_FIELD_KEYS,
    A13_FIELD_KEYS,
    A21_FIELD_KEYS,
    A22_FIELD_KEYS,
    A23_FIELD_KEYS,
    A24_FIELD_KEYS,
    A31_FIELD_KEYS,
    A32_FIELD_KEYS,
    A33_FIELD_KEYS,
    A34_FIELD_KEYS,
    CLINICAL_FIELD_KEYS,
)


TASK_FIELD_KEYS = {
    "A1.1": A11_FIELD_KEYS,
    "A1.2": A12_FIELD_KEYS,
    "A1.3": A13_FIELD_KEYS,
    "A2.1": A21_FIELD_KEYS,
    "A2.2": A22_FIELD_KEYS,
    "A2.3": A23_FIELD_KEYS,
    "A2.4": A24_FIELD_KEYS,
    "A3.1": A31_FIELD_KEYS,
    "A3.2": A32_FIELD_KEYS,
    "A3.3": A33_FIELD_KEYS,
    "A3.4": A34_FIELD_KEYS,
    **CLINICAL_FIELD_KEYS,
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute DentXpertBench metrics from saved JSONL predictions.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--task", choices=TASK_FIELD_KEYS.keys(), default=None)
    args = parser.parse_args()

    rows = load_jsonl(args.path)
    task_code = args.task or (rows[0].get("task_code") if rows else None)
    if task_code not in TASK_FIELD_KEYS:
        raise SystemExit(f"Cannot infer supported task from {args.path}. Pass --task.")

    summary = summarize_fields(rows, TASK_FIELD_KEYS[task_code])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
