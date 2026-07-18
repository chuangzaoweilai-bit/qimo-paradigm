"""Human-readable report rendering for benchmark artifacts."""

from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Qimo Multi-domain Benchmark",
        "",
        f"- Benchmark: `{report['benchmark_id']}`",
        f"- Validator protocol: `{report['validator_protocol_version']}`",
        f"- Base-model control: {report['control']}",
        f"- Base model: `{report['base_model'].get('model_id', report['base_model'].get('adapter', 'unknown'))}`",
        f"- Tasks: {report['task_count']}",
        f"- Domains: {', '.join(report['domains'])}",
        "",
        "## Summary",
        "",
        "| Mode | Closed | Closure rate | Final score | Avg epochs | Model calls | False closure claims |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    if "runtime_seconds" in report:
        lines.insert(6, f"- Runtime: {report['runtime_seconds']:.2f} seconds")
    for mode, mode_result in report["modes"].items():
        summary = mode_result["summary"]
        lines.append(
            "| {mode} | {closed}/{tasks} | {rate:.1%} | {score:.3f} | {epochs:.2f} | {calls} | {false_claims} |".format(
                mode=mode,
                closed=summary["closed_tasks"],
                tasks=summary["tasks"],
                rate=summary["closure_rate"],
                score=summary["average_final_score"],
                epochs=summary["average_epochs"],
                calls=summary["model_calls"],
                false_claims=summary["false_closure_claims"],
            )
        )

    lines.extend(["", "## Task outcomes", ""])
    for mode, mode_result in report["modes"].items():
        lines.append(f"### `{mode}`")
        lines.append("")
        for run in mode_result["runs"]:
            final = run["history"][-1]["validation"]
            lines.append(
                f"- `{run['task_id']}`: **{run['status']}**, score={final['score']:.3f}, epochs={run['epochs_used']}"
            )
        lines.append("")

    lines.extend(["## Interpretation boundary", "", report["boundary"], ""])
    return "\n".join(lines)
