import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import run
from bench.metrics.a51 import apply_reason_judgment, build_reason_judge_messages, parse_reason_judgment, score_a51_fields
from bench.metrics.report import summarize_fields
from bench.protocol import clinical_reference_answer, parse_clinical_answer


class A51ScoringTests(unittest.TestCase):
    def test_f1_partial_and_judge_point_conversion(self):
        ref = {"diagnoses": ["A", "B"], "reason": "参考"}
        row = score_a51_fields({"diagnoses": ["A"], "reason": "预测"}, ref, 100)
        self.assertAlmostEqual(row["field_scores"]["diagnoses"], 100 / 3)
        self.assertIsNone(row["case_score"])
        apply_reason_judgment(row, {"score": 1, "explanation": "部分一致"})
        self.assertEqual(row["field_scores"]["reason"], 25)
        self.assertAlmostEqual(row["case_score"], 100 / 3 + 25)
        self.assertEqual(row["scoring_status"], "scored")
        wrong = score_a51_fields({"diagnoses": ["C"], "reason": "预测"}, ref)
        self.assertEqual(wrong["field_scores"]["diagnoses"], 0)

    def test_judge_validation_and_prompt(self):
        messages = build_reason_judge_messages("参考依据", "不同表述")
        self.assertIn("参考依据", messages[1]["content"])
        self.assertIn("不同表述", messages[1]["content"])
        for invalid in ('{"score":3,"explanation":"x"}', '{"score":true,"explanation":"x"}', '{"score":1,"explanation":""}'):
            with self.assertRaises(ValueError):
                parse_reason_judgment(invalid)
        self.assertEqual(parse_reason_judgment('{"score":2,"explanation":"一致"}')["score"], 2)
        with self.assertRaises(ValueError):
            parse_clinical_answer(json.dumps({"diagnoses": ["A"], "reason": "字" * 101}, ensure_ascii=False), "A5.1")

    def test_end_to_end_mock_judge_and_missing_box_skip(self):
        cases = json.loads(run.TASK_SPECS["A5.1"]["case_path"].read_text(encoding="utf-8"))["cases"]
        first = cases[0]
        missing = next(c for c in cases if c["id"] == "candidate:e1cf8e01197540aea86895416ae5f8a7")
        ref = clinical_reference_answer(first)
        prediction = {"diagnoses": ref["diagnoses"][:1], "reason": "模型理由"}
        scratch = run.PROJECT_ROOT / "preview"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory)
            case_path, output, config_path = root / "cases.json", root / "results.jsonl", root / "judge.json"
            case_path.write_text(json.dumps({"cases": [first, missing]}, ensure_ascii=False), encoding="utf-8")
            config_path.write_text(json.dumps({"model": "judge", "base_url": "http://example.invalid/v1", "requires_api_key": False}), encoding="utf-8")
            args = types.SimpleNamespace(limit=None, workers=1, dry_run=False, judge_model_config=config_path, run_id="test", run_started_at="test", model="tested", base_url="http://example.invalid/v1", temperature=0, max_tokens=1000, image_root=root, debug=False, api_key=None, timeout=1, retries=0, retry_sleep=0, extra_body={}, mock_response=None)
            spec = {**run.TASK_SPECS["A5.1"], "case_path": case_path, "output_path": output}
            with patch.object(run, "build_openai_messages", return_value=[]), patch.object(run, "call_with_retry", return_value={"content": json.dumps(prediction, ensure_ascii=False)}), patch.object(run, "chat_completion", return_value={"content": '{"score":2,"explanation":"一致"}', "usage": {}}) as judge:
                summary = run.run_task("A5.1", spec, args)
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(judge.call_count, 1)
            self.assertEqual(rows[0]["reason_judgment"]["score"], 2)
            self.assertAlmostEqual(rows[0]["case_score"], 75)
            self.assertEqual(rows[1]["scoring_status"], "skipped")
            self.assertEqual((summary["total"], summary["skipped"], summary["fully_scored"]), (1, 1, 1))
            self.assertAlmostEqual(summary["score_rate"], 0.75)

            with patch.object(run, "build_openai_messages", return_value=[]), patch.object(run, "call_with_retry", return_value={"content": json.dumps(prediction, ensure_ascii=False)}), patch.object(run, "chat_completion", side_effect=RuntimeError("judge unavailable")):
                summary = run.run_task("A5.1", spec, args)
            row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
            self.assertIn("judge unavailable", row["reason_judge_error"])
            self.assertIsNone(row["case_score"])
            self.assertEqual(summary["scoring_status"], "incomplete")
            self.assertIsNone(summary["total_score"])

    def test_unscored_cases_do_not_silently_count_as_zero(self):
        ref = {"diagnoses": ["A"], "reason": "参考"}
        scored = {"task_code": "A5.1", "model_answer": {"diagnoses": ["A"]}, **score_a51_fields({"diagnoses": ["A"]}, ref, 100)}
        apply_reason_judgment(scored, {"score": 2, "explanation": "一致"})
        pending = copy.deepcopy(scored)
        pending.update({"case_score": None, "scoring_status": "pending_review", "pending_review_fields": ["reason"]})
        summary = summarize_fields([scored, pending], ("diagnoses", "reason"))
        self.assertIsNone(summary["total_score"])
        self.assertEqual(summary["scored_average_score"], 100)
        self.assertEqual(summary["unscored"], 1)


if __name__ == "__main__":
    unittest.main()
