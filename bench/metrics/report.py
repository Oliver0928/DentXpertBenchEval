from typing import Any

from bench.protocol import A11_FIELD_KEYS


def summarize_fields(rows: list[dict[str, Any]], field_keys: tuple[str, ...]) -> dict[str, Any]:
    total = len(rows)
    valid = sum(1 for row in rows if row.get("model_answer") is not None)
    total_score = sum(float(row.get("case_score", 0.0)) for row in rows)
    total_points = sum(float(row.get("case_points", 1.0)) for row in rows)
    case_scores = [
        {
            "id": row.get("id"),
            "score": float(row.get("case_score", 0.0)),
            "max_score": float(row.get("case_points", 100.0)),
        }
        for row in rows
    ]

    by_field = {}
    for key in field_keys:
        correct = sum(1 for row in rows if row.get("field_correct", {}).get(key))
        by_field[key] = {
            "correct": correct,
            "total": total,
            "score": sum(float(row.get("field_scores", {}).get(key, 0.0)) for row in rows),
            "accuracy": correct / total if total else 0.0,
        }

    total_fields = total * len(field_keys)
    correct_fields = sum(item["correct"] for item in by_field.values())
    summary = {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "case_scores": case_scores,
        "field_accuracy": correct_fields / total_fields if total_fields else 0.0,
        "total_score": total_score,
        "total_points": total_points,
        "score_rate": total_score / total_points if total_points else 0.0,
        "by_field": by_field,
        "average_score": total_score / total if total else 0.0,
    }
    fdi_metrics = [row.get("tooth_status_metrics", {}) for row in rows]
    evaluated_fdi_count = sum(int(item.get("evaluated_fdi_count", 0)) for item in fdi_metrics)
    correct_fdi_count = sum(int(item.get("correct_fdi_count", 0)) for item in fdi_metrics)
    if evaluated_fdi_count:
        summary["fdi_accuracy"] = correct_fdi_count / evaluated_fdi_count
        summary["fdi_correct"] = correct_fdi_count
        summary["fdi_total"] = evaluated_fdi_count
    return summary


def summarize_a11(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return summarize_fields(rows, A11_FIELD_KEYS)

