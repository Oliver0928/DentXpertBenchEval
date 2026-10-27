"""Objective comparisons; free responses await clinical review, not string match."""

from typing import Any


def score_clinical_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 100.0,
    scoring: dict[str, Any] | None = None,
    *,
    task_code: str,
) -> dict[str, Any]:
    objective = {}
    pending = []
    if task_code in {"A5.1", "A5.2", "A6.2"}:
        expected = set(ref["diagnoses"])
        actual = set(pred["diagnoses"]) if pred else set()
        tp = len(expected & actual)
        objective["diagnoses"] = {
            "exact_match": pred is not None and actual == expected,
            "true_positive": tp,
            "false_positive": len(actual - expected),
            "false_negative": len(expected - actual),
        }
        pending = ["reason"] + (["exclude_reason"] if task_code == "A5.2" else [])
    elif task_code == "A6.1":
        objective["total"] = {"exact_match": pred is not None and pred["total"] == ref["total"]}
        objective["images"] = {"exact_match": pred is not None and pred["images"] == ref["images"]}
    elif task_code == "A5.3":
        pending = ["sufficiency", "reason"]
    elif task_code == "A6.3":
        pending = ["conditions"]
    elif task_code == "A7.1":
        pending = ["plans"]
    # Existing task definitions contain copied surface_grades weights. They do
    # not specify a valid A5-A7 rubric. Report comparisons, never invent points.
    return {
        "objective_metrics": objective,
        "pending_review_fields": pending,
        "scoring_status": "pending_review" if pending else "objective_only",
        "scoring_note": (
            "A5.3 reference labels describe diagnostic support, not information sufficiency."
            if task_code == "A5.3" else
            "Objective matches are reported separately; final points require an approved task rubric."
        ),
        "field_correct": {key: item["exact_match"] for key, item in objective.items()},
        "field_scores": {},
        "correct_fields": sum(item["exact_match"] for item in objective.values()),
        "total_fields": len(objective),
        "case_correct": None,
        "case_points": case_points,
        "case_score": None,
    }

