"""Tests for Qimo closure authority, feedback, validators, and rule memory."""

from __future__ import annotations

import json
import unittest

from qimo_model.benchmark import run_benchmark
from qimo_model.dataset import (
    build_training_examples,
    correct_candidate,
    failure_candidate,
    generate_holdout_tasks,
    generate_training_tasks,
    task_fingerprint,
)
from qimo_model.native import QimoNativeModel
from qimo_model.runtime import QimoStructuredModel, RuleMemory, parse_candidate
from qimo_model.tasks import default_task_suite, validate_task


CORRECT_ANSWERS = {
    "software.clamp-boundaries": "return max(low, min(high, value))",
    "software.off-by-one": "for i in range(len(items)):",
    "contracts.withdraw-order": ["reentrancy"],
    "contracts.owner-validation": ["missing_zero_address_check"],
    "planning.release-order": ["spec", "implement", "test", "security_review", "release"],
    "planning.data-pipeline": ["collect", "validate", "transform", "train", "evaluate"],
}


class FeedbackAwareAdapter:
    """Closes only after receiving explicit Qimo gap feedback."""

    def generate(self, prompt: str) -> str:
        marker = "ORIGIN_TERMINAL_CONTRACT_JSON="
        contract_text = prompt.split(marker, 1)[1].split("\n", 1)[0]
        task_id = json.loads(contract_text)["task_id"]
        if "QIMO_GAPS_AND_FEEDBACK_TASKS_JSON=" in prompt:
            answer = CORRECT_ANSWERS[task_id]
            evidence = ["All declared checks are satisfied by the candidate."]
        else:
            answer = [] if task_id.startswith(("contracts.", "planning.")) else "unchanged"
            evidence = []
        return json.dumps(
            {
                "task_id": task_id,
                "answer": answer,
                "evidence": evidence,
                "rules_applied": [],
                "closure_claim": False,
            }
        )


class NativeRegressionAdapter:
    def generate(self, prompt: str) -> str:
        marker = "ORIGIN_TERMINAL_CONTRACT_JSON="
        contract_text = prompt.split(marker, 1)[1].split("\n", 1)[0]
        contract = json.loads(contract_text)
        task_id = contract["task_id"]
        if task_id == "software.clamp-boundaries":
            answer = "return max(low, min(high, value))"
        elif task_id == "software.off-by-one":
            answer = "for i in range(len(items))"
        elif task_id.startswith("contracts."):
            answer = contract["input"]["allowed_findings"]
        elif task_id == "planning.release-order":
            answer = ["spec", "implement", "test", "security_review", "release"]
        else:
            answer = ["collect", "validate", "transform", "train", "evaluate"]
        return json.dumps(
            {
                "task_id": task_id,
                "answer": answer,
                "evidence": ["Candidate is tied to the declared checks."],
                "rules_applied": [],
                "closure_claim": False,
            }
        )


class QimoModelTests(unittest.TestCase):
    def test_parser_extracts_json_from_wrapped_output(self) -> None:
        candidate, error = parse_candidate('prefix {"answer": [], "evidence": []} suffix')
        self.assertIsNone(error)
        self.assertEqual(candidate["answer"], [])

    def test_model_closure_claim_cannot_override_validator(self) -> None:
        task = default_task_suite()[0]
        validation = validate_task(
            task,
            {"answer": "wrong", "evidence": ["claim"], "closure_claim": True},
        )
        self.assertFalse(validation.closed)

    def test_software_validator_reports_missing_colon_precisely(self) -> None:
        task = next(
            task for task in default_task_suite() if task.task_id == "software.off-by-one"
        )
        validation = validate_task(
            task,
            {
                "answer": "for i in range(len(items))",
                "evidence": ["The range covers every valid index."],
                "closure_claim": False,
            },
        )
        self.assertFalse(validation.closed)
        self.assertEqual(validation.gaps[0].code, "patch_syntax_missing_colon")
        self.assertTrue(validation.evidence["behavior_matches_except_syntax"])

    def test_security_gap_code_does_not_reveal_expected_label(self) -> None:
        task = next(
            task
            for task in default_task_suite()
            if task.task_id == "contracts.owner-validation"
        )
        validation = validate_task(
            task,
            {"answer": ["owner"], "evidence": ["Direct owner assignment."]},
        )
        codes = [gap.code for gap in validation.gaps]
        self.assertIn("missing_required_finding", codes)
        self.assertFalse(any("missing_zero_address_check" in code for code in codes))

    def test_qimo_feedback_closes_where_generic_retry_does_not(self) -> None:
        task = default_task_suite()[0]
        adapter = FeedbackAwareAdapter()
        generic = QimoStructuredModel(adapter).run_task(task, "generic_retry")
        qimo = QimoStructuredModel(adapter).run_task(task, "qimo")
        self.assertEqual(generic.status, "not_closed")
        self.assertEqual(qimo.status, "closed")
        self.assertEqual(len(qimo.epochs), 2)

    def test_rules_commit_only_after_verified_closure(self) -> None:
        tasks = default_task_suite()
        memory = RuleMemory()
        model = QimoStructuredModel(FeedbackAwareAdapter(), memory)
        model.run_task(tasks[0], "one_shot")
        self.assertNotIn(
            "software_patch_must_satisfy_declared_behavior",
            memory.rules_for("software_repair"),
        )
        model.run_task(tasks[0], "qimo")
        self.assertIn(
            "software_patch_must_satisfy_declared_behavior",
            memory.rules_for("software_repair"),
        )

    def test_all_three_domains_have_two_tasks(self) -> None:
        counts: dict[str, int] = {}
        for task in default_task_suite():
            counts[task.domain] = counts.get(task.domain, 0) + 1
        self.assertEqual(
            counts,
            {
                "software_repair": 2,
                "smart_contract_audit": 2,
                "multi_step_planning": 2,
            },
        )
        contract_tasks = [
            task for task in default_task_suite() if task.domain == "smart_contract_audit"
        ]
        self.assertTrue(
            all("input.allowed_findings" in task.answer_schema for task in contract_tasks)
        )

    def test_protocol_benchmark_records_expected_control_result(self) -> None:
        report = run_benchmark(FeedbackAwareAdapter(), default_task_suite())
        self.assertEqual(report["modes"]["one_shot"]["summary"]["closed_tasks"], 0)
        self.assertEqual(report["modes"]["generic_retry"]["summary"]["closed_tasks"], 0)
        self.assertEqual(report["modes"]["qimo"]["summary"]["closed_tasks"], 6)

    def test_native_kernel_closes_regression_suite_without_hidden_answers(self) -> None:
        model = QimoNativeModel(NativeRegressionAdapter())
        runs = [model.run_task(task) for task in default_task_suite()]
        self.assertTrue(all(run.status == "closed" for run in runs))
        self.assertTrue(
            all(all(run.structural_invariants.values()) for run in runs)
        )
        self.assertEqual(sum(run.model_calls for run in runs), 6)
        self.assertEqual(sum(run.operator_steps for run in runs), 3)

    def test_native_kernel_reports_explicit_exhaustion_for_unrepairable_path(self) -> None:
        class RepeatingAdapter:
            def generate(self, prompt: str) -> str:
                task_id = json.loads(
                    prompt.split("ORIGIN_TERMINAL_CONTRACT_JSON=", 1)[1].split("\n", 1)[0]
                )["task_id"]
                return json.dumps(
                    {
                        "task_id": task_id,
                        "answer": "still wrong",
                        "evidence": ["insufficient"],
                        "closure_claim": False,
                    }
                )

        task = default_task_suite()[0]
        run = QimoNativeModel(RepeatingAdapter()).run_task(task)
        self.assertEqual(run.status, "not_closed")
        self.assertEqual(run.termination, "path_budget_exhausted_with_explicit_gaps")
        self.assertTrue(any(step.repeated_state for step in run.steps))
        self.assertTrue(all(run.structural_invariants.values()))

    def test_training_and_holdout_sets_are_disjoint(self) -> None:
        training = generate_training_tasks()
        holdout = generate_holdout_tasks()
        self.assertEqual(len(training), 120)
        self.assertEqual(len(holdout), 30)
        self.assertFalse({task.task_id for task in training} & {task.task_id for task in holdout})
        self.assertFalse(
            {task_fingerprint(task) for task in training}
            & {task_fingerprint(task) for task in holdout}
        )

    def test_generated_trajectory_targets_close_and_failures_remain_open(self) -> None:
        training = generate_training_tasks(per_domain=3)
        for task in training:
            self.assertTrue(validate_task(task, correct_candidate(task)).closed)
            self.assertFalse(validate_task(task, failure_candidate(task)).closed)
        examples = build_training_examples(training)
        self.assertEqual(len(examples), len(training) * 2)
        self.assertTrue(any(example["phase"] == "gap_correction" for example in examples))


if __name__ == "__main__":
    unittest.main()
