"""Compare raw, structural, and trained Qimo model paths on disjoint holdout tasks."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Any

import modal


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qimo_model.dataset import generate_holdout_tasks  # noqa: E402
from qimo_model.native import NativeRun, QimoNativeModel  # noqa: E402
from qimo_model.runtime import QimoStructuredModel  # noqa: E402


class ModalAdapter:
    def __init__(self, app_name: str, class_name: str, label: str) -> None:
        self.model = modal.Cls.from_name(app_name, class_name)()
        self.label = label

    def generate(self, prompt: str) -> str:
        return self.model.complete.remote(prompt, max_new_tokens=320)


def _native_summary(runs: list[NativeRun]) -> dict[str, Any]:
    closed = sum(run.status == "closed" for run in runs)
    invariant_values = [
        value for run in runs for value in run.structural_invariants.values()
    ]
    return {
        "tasks": len(runs),
        "closed_tasks": closed,
        "closure_rate": round(closed / len(runs), 4),
        "model_calls": sum(run.model_calls for run in runs),
        "operator_steps": sum(run.operator_steps for run in runs),
        "structural_invariant_rate": round(
            sum(invariant_values) / len(invariant_values), 4
        ),
        "explicit_exhaustions": sum(
            run.termination == "path_budget_exhausted_with_explicit_gaps"
            for run in runs
        ),
    }


def _raw_summary(runs) -> dict[str, Any]:
    closed = sum(run.status == "closed" for run in runs)
    failed_have_gaps = all(
        run.status == "closed" or bool(run.final_validation.gaps) for run in runs
    )
    return {
        "tasks": len(runs),
        "closed_tasks": closed,
        "closure_rate": round(closed / len(runs), 4),
        "model_calls": sum(len(run.epochs) for run in runs),
        "operator_steps": 0,
        "structural_invariant_rate": 1.0 if failed_have_gaps else 0.0,
        "explicit_exhaustions": 0,
        "average_final_score": round(
            mean(run.final_validation.score for run in runs), 4
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/qimo-native-holdout-v2")
    parser.add_argument("--per-domain", type=int, default=10)
    args = parser.parse_args()

    tasks = generate_holdout_tasks(per_domain=args.per_domain)
    original = ModalAdapter("qimo-closure-model", "ProposalModel", "original_qwen")
    trained = ModalAdapter("qimo-native-model", "TrainedModel", "qimo_lora")
    started = time.perf_counter()

    raw_model = QimoStructuredModel(original)
    raw_runs = [raw_model.run_task(task, "one_shot") for task in tasks]

    native_original = QimoNativeModel(original)
    native_original_runs = [native_original.run_task(task) for task in tasks]

    native_trained = QimoNativeModel(trained)
    native_trained_runs = [native_trained.run_task(task) for task in tasks]

    report = {
        "benchmark_id": "qimo-native-holdout-v2",
        "holdout_seed": 2607,
        "training_seed": 1701,
        "holdout_tasks": len(tasks),
        "domains": sorted({task.domain for task in tasks}),
        "runtime_seconds": round(time.perf_counter() - started, 4),
        "paths": {
            "original_one_shot": {
                "summary": _raw_summary(raw_runs),
                "runs": [run.to_dict() for run in raw_runs],
            },
            "original_plus_native_kernel": {
                "summary": _native_summary(native_original_runs),
                "runs": [run.to_dict() for run in native_original_runs],
            },
            "qimo_lora_plus_native_kernel": {
                "summary": _native_summary(native_trained_runs),
                "runs": [run.to_dict() for run in native_trained_runs],
            },
        },
        "claim_boundary": (
            "Holdout task closure and structural invariants are reported separately. "
            "A 100% structural invariant rate does not imply 100% task success or AGI."
        ),
    }

    output_base = ROOT / args.output
    output_base.parent.mkdir(parents=True, exist_ok=True)
    output_base.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {name: result["summary"] for name, result in report["paths"].items()},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
