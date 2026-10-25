from typing import Any

from bench.protocol import A11_FIELD_KEYS, normalize_answer


def score_fields(
    pred: dict[str, str] | None,
    ref: dict[str, str],
    case_points: float = 1.0,
    field_keys: tuple[str, ...] = A11_FIELD_KEYS,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    per_field = {}
    field_scores = {}
    correct = 0
    weights = scoring_field_weights(scoring, field_keys)

    for key in field_keys:
        pred_value = normalize_answer(pred.get(key, "")) if pred else ""
        ref_value = normalize_answer(ref.get(key, ""))
        ok = pred_value == ref_value
        per_field[key] = ok
        field_scores[key] = case_points * weights[key] if ok else 0.0
        correct += int(ok)

    case_score = sum(field_scores.values())

    return {
        "field_correct": per_field,
        "field_scores": field_scores,
        "correct_fields": correct,
        "total_fields": len(field_keys),
        "case_correct": correct == len(field_keys),
        "case_points": case_points,
        "case_score": case_score,
    }


def score_a11_fields(
    pred: dict[str, str] | None,
    ref: dict[str, str],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score A1.1 modality and field-of-view classification fields."""
    return score_fields(pred, ref, case_points=case_points, field_keys=A11_FIELD_KEYS, scoring=scoring)


def split_action_view(value: str) -> tuple[str, str]:
    action, separator, requested_view = normalize_answer(value).partition(":")
    return action, requested_view if separator else ""


def score_a12_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    weights = scoring_field_weights(scoring, ("coverage_codes", "quality_grade"))
    coverage_points = case_points * weights["coverage_codes"]
    quality_points = case_points * weights["quality_grade"]

    pred_coverage = set(pred.get("coverage_codes", [])) if pred else set()
    ref_coverage = set(ref.get("coverage_codes", []))
    coverage_ok = pred_coverage == ref_coverage

    pred_quality = normalize_answer(pred.get("quality_grade", "")) if pred else ""
    ref_quality = normalize_answer(ref.get("quality_grade", ""))
    quality_ok = pred_quality == ref_quality
    case_score = (coverage_points if coverage_ok else 0.0) + (quality_points if quality_ok else 0.0)

    return {
        "field_correct": {
            "coverage_codes": coverage_ok,
            "quality_grade": quality_ok,
        },
        "field_scores": {
            "coverage_codes": coverage_points if coverage_ok else 0.0,
            "quality_grade": quality_points if quality_ok else 0.0,
        },
        "correct_fields": int(coverage_ok) + int(quality_ok),
        "total_fields": 2,
        "case_correct": coverage_ok and quality_ok,
        "case_points": case_points,
        "case_score": case_score,
    }


def score_a13_fields(
    pred: dict[str, str] | None,
    ref: dict[str, str],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    weights = scoring_field_weights(scoring, ("sufficiency", "minimum_necessary_action"))
    sufficiency_points = case_points * weights["sufficiency"]
    action_points = case_points * weights["minimum_necessary_action"]
    action_subscores = scoring_subscores(scoring, "minimum_necessary_action")
    action_code_points = case_points * action_subscores.get("action_code", action_points / 2)
    requested_view_points = case_points * action_subscores.get("requested_view", action_points / 2)

    pred_sufficiency = normalize_answer(pred.get("sufficiency", "")) if pred else ""
    ref_sufficiency = normalize_answer(ref.get("sufficiency", ""))
    sufficiency_ok = pred_sufficiency == ref_sufficiency

    pred_action, pred_view = split_action_view(pred.get("minimum_necessary_action", "") if pred else "")
    ref_action, ref_view = split_action_view(ref.get("minimum_necessary_action", ""))
    needs_view = ref_action == normalize_answer("补充缺失视角")

    action_code_ok = pred_action == ref_action
    requested_view_ok = (pred_view == ref_view) if needs_view else True
    action_ok = action_code_ok and requested_view_ok

    if needs_view:
        action_score = (action_code_points if action_code_ok else 0.0) + (
            requested_view_points if requested_view_ok else 0.0
        )
        field_scores = {
            "sufficiency": sufficiency_points if sufficiency_ok else 0.0,
            "minimum_necessary_action": action_score,
            "action_code": action_code_points if action_code_ok else 0.0,
            "requested_view": requested_view_points if requested_view_ok else 0.0,
        }
        field_correct = {
            "sufficiency": sufficiency_ok,
            "minimum_necessary_action": action_ok,
            "action_code": action_code_ok,
            "requested_view": requested_view_ok,
        }
    else:
        field_scores = {
            "sufficiency": sufficiency_points if sufficiency_ok else 0.0,
            "minimum_necessary_action": action_points if action_ok else 0.0,
        }
        field_correct = {
            "sufficiency": sufficiency_ok,
            "minimum_necessary_action": action_ok,
        }

    correct_fields = int(sufficiency_ok) + int(action_ok)
    case_score = sum(
        score for key, score in field_scores.items() if key in ("sufficiency", "minimum_necessary_action")
    )

    return {
        "field_correct": field_correct,
        "field_scores": field_scores,
        "correct_fields": correct_fields,
        "total_fields": 2,
        "case_correct": sufficiency_ok and action_ok,
        "case_points": case_points,
        "case_score": case_score,
    }


def score_a43_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pred_value = pred.get("surface_grades", []) if pred else []
    ref_value = ref.get("surface_grades", [])
    ok = pred_value == ref_value
    score = case_points if ok else 0.0
    return {
        "field_correct": {"surface_grades": ok},
        "field_scores": {"surface_grades": score},
        "correct_fields": int(ok),
        "total_fields": 1,
        "case_correct": ok,
        "case_points": case_points,
        "case_score": score,
    }


def score_a21_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pred_stage = normalize_answer(pred.get("dentition_stage", "")) if pred else ""
    ref_stage = normalize_answer(ref.get("dentition_stage", ""))
    stage_ok = pred_stage == ref_stage

    configured_weights = scoring_field_configs(scoring)
    stage_config = configured_weights.get("dentition_stage", {})
    stage_weight = stage_config.get("weight", 1.0)
    stage_points = case_points * stage_weight
    case_score = stage_points if stage_ok else 0.0

    return {
        "field_correct": {"dentition_stage": stage_ok},
        "field_scores": {"dentition_stage": stage_points if stage_ok else 0.0},
        "correct_fields": int(stage_ok),
        "total_fields": 1,
        "case_correct": stage_ok,
        "case_points": case_points,
        "case_score": case_score,
    }


def score_a22_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible entry point; geometric scoring lives in localization."""
    from bench.metrics.localization import score_a22_fields as score_localization_a22_fields

    return score_localization_a22_fields(pred, ref, case_points, scoring)


def score_a22_inventory_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pred_teeth = set(pred.get("teeth", [])) if pred else set()
    ref_teeth = set(ref.get("teeth", []))
    true_positive = len(pred_teeth & ref_teeth)
    false_positive = len(pred_teeth - ref_teeth)
    false_negative = len(ref_teeth - pred_teeth)

    precision = true_positive / len(pred_teeth) if pred_teeth else (1.0 if not ref_teeth else 0.0)
    recall = true_positive / len(ref_teeth) if ref_teeth else (1.0 if not pred_teeth else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact_match = pred_teeth == ref_teeth

    case_score = case_points * scoring_field_weights(scoring, ("teeth",))["teeth"] * f1

    return {
        "field_correct": {"teeth": exact_match},
        "field_scores": {"teeth": case_score},
        "correct_fields": int(exact_match),
        "total_fields": 1,
        "case_correct": exact_match,
        "case_points": case_points,
        "case_score": case_score,
        "tooth_metrics": {
            "mode": "inventory",
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
    }


def score_a23_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pred_pairs = tooth_status_pairs(pred.get("teeth", [])) if pred else set()
    ref_pairs = tooth_status_pairs(ref.get("teeth", []))

    true_positive = len(pred_pairs & ref_pairs)
    false_positive = len(pred_pairs - ref_pairs)
    false_negative = len(ref_pairs - pred_pairs)

    precision = true_positive / len(pred_pairs) if pred_pairs else (1.0 if not ref_pairs else 0.0)
    recall = true_positive / len(ref_pairs) if ref_pairs else (1.0 if not pred_pairs else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact_match = pred_pairs == ref_pairs

    ref_by_fdi = {fdi: status for fdi, status in ref_pairs}
    pred_by_fdi = {fdi: status for fdi, status in pred_pairs}
    ref_fdis = set(ref_by_fdi)
    pred_fdis = set(pred_by_fdi)
    evaluated_fdis = sorted(ref_fdis | pred_fdis)
    status_correct = {
        fdi: fdi in ref_by_fdi
        and fdi in pred_by_fdi
        and pred_by_fdi[fdi] == ref_by_fdi[fdi]
        for fdi in evaluated_fdis
    }
    correct_fdi_count = sum(status_correct.values())
    fdi_accuracy = correct_fdi_count / len(evaluated_fdis) if evaluated_fdis else 1.0

    case_score = case_points * scoring_field_weights(scoring, ("teeth",))["teeth"] * fdi_accuracy

    return {
        "field_correct": {"teeth": fdi_accuracy == 1.0},
        "field_scores": {"teeth": case_score},
        "correct_fields": int(exact_match),
        "total_fields": 1,
        "case_correct": fdi_accuracy == 1.0,
        "case_points": case_points,
        "case_score": case_score,
        "tooth_status_metrics": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fdi_accuracy": fdi_accuracy,
            "correct_fdi_count": correct_fdi_count,
            "evaluated_fdi_count": len(evaluated_fdis),
            "evaluated_fdis": evaluated_fdis,
            "missing_fdis": sorted(ref_fdis - pred_fdis),
            "extra_fdis": sorted(pred_fdis - ref_fdis),
            "status_correct_by_fdi": status_correct,
        },
    }


def score_a24_fields(
    pred: dict[str, Any] | None,
    ref: dict[str, Any],
    case_points: float = 1.0,
    scoring: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible entry point; keypoint scoring lives in localization."""
    from bench.metrics.localization import score_a24_fields as score_localization_a24_fields

    return score_localization_a24_fields(pred, ref, case_points, scoring)


def tooth_status_pairs(teeth: list[dict[str, Any]]) -> set[tuple[int, str]]:
    return {(int(item["fdi"]), str(item["status"])) for item in teeth}


def scoring_field_configs(scoring: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    return {
        str(item["key"]): item
        for item in (scoring or {}).get("fields", [])
        if isinstance(item, dict) and "key" in item
    }


def scoring_field_weights(
    scoring: dict[str, Any] | None,
    field_keys: tuple[str, ...],
) -> dict[str, float]:
    configs = scoring_field_configs(scoring)
    configured = {key: float(configs[key].get("weight", 0.0)) for key in field_keys if key in configs}
    if len(configured) == len(field_keys):
        return configured
    default_weight = 1.0 / len(field_keys)
    return {key: configured.get(key, default_weight) for key in field_keys}


def scoring_subscores(scoring: dict[str, Any] | None, field_key: str) -> dict[str, float]:
    configs = scoring_field_configs(scoring)
    raw = configs.get(field_key, {}).get("conditional_subscores", {})
    if not isinstance(raw, dict):
        return {}
    return {str(key): float(value) for key, value in raw.items() if isinstance(value, (int, float))}



