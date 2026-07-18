"""Run the Qimo multi-domain benchmark against the deployed Modal base model."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import modal


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qimo_model.benchmark import run_benchmark  # noqa: E402
from qimo_model.reports import render_markdown  # noqa: E402
from qimo_model.tasks import default_task_suite  # noqa: E402


class ModalBaseModelAdapter:
    metadata = {
        "provider": "Modal",
        "model_id": "Qwen/Qwen3-1.7B",
        "gpu": "NVIDIA T4",
        "max_new_tokens": 320,
        "do_sample": False,
        "temperature": None,
    }

    def __init__(self) -> None:
        deployed_class = modal.Cls.from_name("qimo-closure-model", "ProposalModel")
        self.model = deployed_class()

    def generate(self, prompt: str) -> str:
        return self.model.complete.remote(prompt, max_new_tokens=320)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/qimo-multidomain-v1")
    args = parser.parse_args()

    output_base = ROOT / args.output
    output_base.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    report = run_benchmark(ModalBaseModelAdapter(), default_task_suite())
    report["runtime_seconds"] = round(time.perf_counter() - started, 4)
    output_base.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    output_base.with_suffix(".md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(json.dumps({mode: data["summary"] for mode, data in report["modes"].items()}, indent=2))


if __name__ == "__main__":
    main()
