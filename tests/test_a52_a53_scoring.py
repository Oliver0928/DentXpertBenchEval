import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import run
from bench.metrics.a52_a53 import apply_clinical_judgment, build_a52_judge_messages, parse_a52_judgment, score_a52_fields, score_a53_fields
from bench.metrics.report import summarize_fields
from bench.protocol import build_clinical_prompt, clinical_diagnosis_options, clinical_reference_answer, parse_clinical_answer, validate_clinical_answer


def cases(code):
    return json.loads(run.TASK_SPECS[code]["case_path"].read_text(encoding="utf-8"))["cases"]


class A52A53Tests(unittest.TestCase):
    def test_all_a52_candidate_sets_and_private_labels(self):
        for case in cases("A5.2"):
            with self.subTest(case=case["id"]):
                fields = {f["key"]: f["value"] for f in case["input"]["fields"]}
                entries = case["reference_answer"]["fields"][0]["value"]
                ids = {item["option_id"] for item in entries}
                expected = [item for item in fields["diagnosis_options"] if item["option_id"] in ids]
                self.assertEqual(clinical_diagnosis_options(case), expected)
                prompt = build_clinical_prompt(case)
                option_block = prompt.split("诊断选项：\n", 1)[1].split("\n\n判定与填写规则", 1)[0]
                self.assertEqual(option_block.splitlines(), [item["diagnosis"] for item in expected])
                changed = copy.deepcopy(case)
                for entry in changed["reference_answer"]["fields"][0]["value"]:
                    entry.update(role="PRIVATE_ROLE", reason="PRIVATE_REASON")
                self.assertEqual(build_clinical_prompt(changed), prompt)
                hidden = next(item for item in fields["diagnosis_options"] if item["option_id"] not in ids)
                with self.assertRaisesRegex(ValueError, "outside input options"):
                    validate_clinical_answer({"diagnoses": [hidden["diagnosis"]]}, case)

    def test_bad_candidate_ids_fail_explicitly(self):
        case = copy.deepcopy(cases("A5.2")[0])
        case["reference_answer"]["fields"][0]["value"][0]["option_id"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "candidate IDs"):
            build_clinical_prompt(case)

    def test_a52_scores_and_joint_judge_schema(self):
        row = {"task_code": "A5.2", **score_a52_fields({"diagnoses": ["A"]}, {"diagnoses": ["A", "B"]})}
        self.assertAlmostEqual(row["field_scores"]["diagnoses"], 100 / 3)
        judgment = parse_a52_judgment('{"reason":{"score":2,"explanation":"一致"},"exclude_reason":{"score":1,"explanation":"部分"}}')
        apply_clinical_judgment(row, judgment)
        self.assertEqual(row["field_scores"]["reason"], 25)
        self.assertEqual(row["field_scores"]["exclude_reason"], 12.5)
        self.assertAlmostEqual(row["case_score"], 100 / 3 + 37.5)
        for response in ('{}', '{"reason":{"score":2,"explanation":"x"}}', '{"reason":{"score":2,"explanation":"x"},"exclude_reason":{"score":true,"explanation":"x"}}'):
            with self.assertRaises(ValueError):
                parse_a52_judgment(response)
        ref = clinical_reference_answer(cases("A5.2")[0])
        messages = build_a52_judge_messages(ref, {"diagnoses": ref["diagnoses"], "reason": "预测", "exclude_reason": "排除"})
        self.assertIn(ref["exclude_reason"], messages[1]["content"])

    def test_a53_mapping_and_all_conditional_scores(self):
        for case in cases("A5.3"):
            ref = clinical_reference_answer(case)
            expected = "充足" if ref["diagnosis_support"] == "supported" else "不足"
            self.assertEqual(ref["sufficiency"], expected)
            self.assertTrue(ref["reason"])
            pred = {"sufficiency": expected}
            if expected == "不足":
                pred["reason"] = "理由"
            row = {"task_code": "A5.3", **score_a53_fields(pred, ref)}
            if expected == "充足":
                self.assertEqual(row["case_score"], 100)
                self.assertEqual(row["pending_review_fields"], [])
            else:
                self.assertEqual(row["field_scores"]["sufficiency"], 50)
                apply_clinical_judgment(row, {"score": 1, "explanation": "部分"})
                self.assertEqual(row["case_score"], 75)
            wrong = score_a53_fields({"sufficiency": "不足" if expected == "充足" else "充足"}, ref)
            self.assertEqual(wrong["case_score"], 0)
            self.assertEqual(wrong["pending_review_fields"], [])
        parsed = parse_clinical_answer('{"sufficiency":"不充足","reason":"理由"}', "A5.3")
        self.assertEqual(parsed["sufficiency"], "不足")
        with self.assertRaises(ValueError):
            parse_clinical_answer('{"sufficiency":"充足","reason":"多余"}', "A5.3")
        with self.assertRaises(ValueError):
            parse_clinical_answer('{"sufficiency":"不足"}', "A5.3")
        with self.assertRaises(ValueError):
            parse_clinical_answer(json.dumps({"sufficiency": "不足", "reason": "字" * 101}), "A5.3")

    def execute_task(self, case, prediction, judge_reply=None, judge_error=None):
        scratch = run.PROJECT_ROOT / "preview"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory)
            source, output, config = root / "cases.json", root / "result.jsonl", root / "judge.json"
            source.write_text(json.dumps({"cases": [case]}, ensure_ascii=False), encoding="utf-8")
            config.write_text(json.dumps({"model": "test-judge", "base_url": "http://example.invalid/v1", "requires_api_key": False}), encoding="utf-8")
            args = types.SimpleNamespace(limit=None, workers=1, dry_run=False, judge_model_config=config, run_id="test", run_started_at="test", model="tested", base_url="http://example.invalid/v1", temperature=0, max_tokens=1000, image_root=root, debug=False, api_key=None, timeout=1, retries=0, retry_sleep=0, extra_body={}, mock_response=None)
            spec = {**run.TASK_SPECS[case["task_code"]], "case_path": source, "output_path": output}
            with redirect_stdout(io.StringIO()), patch.object(run, "build_openai_messages", return_value=[]), patch.object(run, "call_with_retry", return_value={"content": json.dumps(prediction, ensure_ascii=False)}), patch.object(run, "chat_completion", return_value={"content": judge_reply, "usage": {"total_tokens": 10}}, side_effect=judge_error) as judge:
                summary = run.run_task(case["task_code"], spec, args)
            row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
            return row, summary, judge.call_count

    def test_a52_runner_one_judge_call_and_failures(self):
        case = cases("A5.2")[0]
        ref = clinical_reference_answer(case)
        pred = {"diagnoses": ref["diagnoses"], "reason": "诊断理由", "exclude_reason": "排除理由"}
        reply = '{"reason":{"score":2,"explanation":"一致"},"exclude_reason":{"score":1,"explanation":"部分"}}'
        row, summary, calls = self.execute_task(case, pred, reply)
        self.assertEqual(calls, 1)
        self.assertEqual(row["case_score"], 87.5)
        self.assertEqual(summary["total_score"], 87.5)
        self.assertEqual(row["reason_judge_model"], "test-judge")
        self.assertEqual(row["reason_judge_token_usage"]["total_tokens"], 10)
        for reply, error in ((None, RuntimeError("offline")), ('{}', None)):
            row, summary, calls = self.execute_task(case, pred, reply, error)
            self.assertIsNone(row["case_score"])
            self.assertEqual(row["field_scores"]["diagnoses"], 50)
            self.assertEqual(row["pending_review_fields"], ["reason", "exclude_reason"])
            self.assertTrue(row["reason_judge_error"])
            self.assertIsNone(summary["total_score"])

    def test_a53_runner_calls_judge_only_for_correct_insufficient(self):
        all_cases = cases("A5.3")
        sufficient = next(c for c in all_cases if clinical_reference_answer(c)["sufficiency"] == "充足")
        insufficient = next(c for c in all_cases if clinical_reference_answer(c)["sufficiency"] == "不足")
        for case, pred, expected in ((sufficient, {"sufficiency": "充足"}, 100), (insufficient, {"sufficiency": "充足"}, 0), (sufficient, {"sufficiency": "不足", "reason": "理由"}, 0)):
            row, summary, calls = self.execute_task(case, pred)
            self.assertEqual(calls, 0)
            self.assertEqual(row["case_score"], expected)
            self.assertEqual(summary["total_score"], expected)
            self.assertEqual(row["reference_answer_native"], case["reference_answer"])
            self.assertIn("reference_label_mapping", row)
        row, summary, calls = self.execute_task(insufficient, {"sufficiency": "不充足", "reason": "理由"}, '{"score":2,"explanation":"一致"}')
        self.assertEqual(calls, 1)
        self.assertEqual(row["case_score"], 100)
        row, summary, calls = self.execute_task(insufficient, {"sufficiency": "不足", "reason": "理由"}, judge_error=RuntimeError("offline"))
        self.assertEqual(row["field_scores"]["sufficiency"], 50)
        self.assertIsNone(row["case_score"])
        self.assertEqual(summary["scoring_status"], "incomplete")
        row, summary, calls = self.execute_task(insufficient, {"sufficiency": "不足"})
        self.assertEqual(calls, 0)
        self.assertEqual(row["scoring_status"], "invalid")
        self.assertEqual(summary["invalid"], 1)


if __name__ == "__main__":
    unittest.main()
