import json
from pathlib import Path
from typing import Any


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("cases", []))


def write_cases(path: Path, cases: list[dict[str, Any]], task_code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"task_code": task_code, "cases": cases}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

