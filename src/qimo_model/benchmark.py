"""Controlled benchmark across modes and machine-verifiable domains."""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean
from typing import Any

from qimo_model.contracts import ModelAdapter, TaskRun, TaskSpec
from qimo_model.runtime import QimoStructuredModel, RuleMemory
from qimo_model.tasks import VALIDATOR_PROTOCOL_VERSION


BENCHMARK_MODES = ("one_shot", "generic_retry", "qimo")


def _mode_summary(runs: list[TaskRun]) -> dict[str, Any]:
    closed = [run for run in runs if run.status == "closed"]
    false_closure_claims = sum(
        1
        for run in runs
        for epoch in run.epochs
        if epoch.model_claimed_closure and not epoch.validation.closed
    )
    return {
        "tasks": len(runs),
        "closed_tasks": len(closed),
        "closure_rate": round(len(closed) / len(runs), 4) if runs else 0.0,
        "average_final_score": round(
            mean(run.final_validation.score for run in runs), 4
        ) if runs else 0.0,
        "average_epochs": round(mean(len(run.epochs) for run in runs), 4) if runs else 0.0,
        "model_calls": sum(len(run.epochs) for run in runs),
        "false_closure_claims": false_closure_claims,
    }


def run_benchmark(
    adapter: ModelAdapter,
    tasks: list[TaskSpec],
    modes: tuple[str, ...] = BENCHMARK_MODES,
) -> dict[str, Any]:
    runs_by_mode: dict[str, list[TaskRun]] = {}
    memories: dict[str, dict[str, Any]] = {}
    for mode in modes:
        memory = RuleMemory()
        model = QimoStructuredModel(adapter, memory)
        runs_by_mode[mode] = [model.run_task(task, mode) for task in tasks]
        memories[mode] = memory.to_dict()

    return {
        "benchmark_id": "qimo-multidomain-v1",
        "validator_protocol_version": VALIDATOR_PROTOCOL_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "claim_scope": "bounded structural inference with deterministic domain validators",
        "control": "same base model and decoding; only the runtime mode changes",
        "domains": sorted({task.domain for task in tasks}),
        "task_count": len(tasks),
        "base_model": getattr(
            adapter,
            "metadata",
            {"adapter": adapter.__class__.__name__, "decoding": "adapter-defined"},
        ),
        "modes": {
            mode: {
                "summary": _mode_summary(runs),
                "rule_memory": memories[mode],
                "runs": [run.to_dict() for run in runs],
            }
            for mode, runs in runs_by_mode.items()
        },
        "boundary": (
            "This benchmark does not demonstrate consciousness, AGI, weight-level learning, "
            "or unlimited self-evolution. It tests whether explicit verified gaps improve "
            "task closure for an unchanged base model."
        ),
    }
