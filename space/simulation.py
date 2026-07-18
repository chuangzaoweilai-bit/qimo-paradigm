"""Bounded closure simulation used by the public Qimo Paradigm demo."""

from __future__ import annotations

from dataclasses import dataclass, field


REQUIRED_UNITS = (
    "origin_modeling",
    "terminal_modeling",
    "path_generation",
    "forbidden_path_rejection",
    "quality_gate",
    "gap_detection",
    "feedback_task_generation",
    "semantic_memory_update",
    "rule_update",
    "cross_domain_transfer",
)

QUALITY_GATES = (
    "has_origin",
    "has_terminal",
    "records_allowed_paths",
    "records_forbidden_paths",
    "has_verification",
    "feeds_gaps_back",
)

LEARNING_PLAN = {
    1: {
        "units": ("origin_modeling", "terminal_modeling"),
        "gates": ("has_origin", "has_terminal"),
    },
    2: {
        "units": ("path_generation", "forbidden_path_rejection"),
        "gates": ("records_allowed_paths", "records_forbidden_paths"),
    },
    3: {
        "units": ("quality_gate", "gap_detection"),
        "gates": ("has_verification",),
    },
    4: {
        "units": ("feedback_task_generation", "semantic_memory_update"),
        "gates": ("feeds_gaps_back",),
    },
    5: {
        "units": ("rule_update", "cross_domain_transfer"),
        "gates": (),
    },
}


@dataclass
class ClosureState:
    origin: str
    terminal: str
    units: set[str] = field(default_factory=set)
    gates: set[str] = field(default_factory=set)
    rules: list[str] = field(default_factory=lambda: ["no_silent_success"])

    def audit(self) -> dict:
        missing_units = [item for item in REQUIRED_UNITS if item not in self.units]
        missing_gates = [item for item in QUALITY_GATES if item not in self.gates]
        return {
            "origin": self.origin,
            "terminal": self.terminal,
            "coverage": round(1 - len(missing_units) / len(REQUIRED_UNITS), 2),
            "gate_coverage": round(1 - len(missing_gates) / len(QUALITY_GATES), 2),
            "missing_units": missing_units,
            "missing_gates": missing_gates,
            "status": "closed" if not missing_units and not missing_gates else "not_closed",
        }

    def apply_epoch(self, epoch: int) -> dict:
        plan = LEARNING_PLAN.get(epoch, {"units": (), "gates": ()})
        self.units.update(plan["units"])
        self.gates.update(plan["gates"])
        if "rule_update" in plan["units"]:
            self.rules.append("failed_path_must_generate_new_task")
        if "cross_domain_transfer" in plan["units"]:
            self.rules.append("closed_structure_can_transfer_domains")
        return {"units": list(plan["units"]), "gates": list(plan["gates"])}


def _feedback_tasks(audit: dict) -> list[str]:
    tasks = [f"Close semantic gap: {item}" for item in audit["missing_units"][:2]]
    tasks.extend(f"Add quality gate: {item}" for item in audit["missing_gates"][:1])
    return tasks


def _table_row(mode: str, epoch: int, audit: dict, feedback: list[str]) -> list:
    return [
        mode,
        epoch,
        int(audit["coverage"] * 100),
        int(audit["gate_coverage"] * 100),
        len(audit["missing_units"]),
        len(audit["missing_gates"]),
        audit["status"],
        " | ".join(feedback) if feedback else "None",
    ]


def run_comparison(origin: str, terminal: str, max_epochs: int = 6) -> dict:
    """Compare a fixed-output baseline with a Qimo gap-feedback loop."""

    origin = (origin or "A system wants to improve its semantic competence.").strip()
    terminal = (
        terminal
        or "The system reaches a verified closed semantic structure."
    ).strip()
    max_epochs = max(1, min(int(max_epochs), 6))

    baseline = ClosureState(
        origin=origin,
        terminal=terminal,
        units={"origin_modeling", "path_generation"},
        gates={"has_origin"},
    )
    baseline_history = []
    table_rows = []
    for epoch in range(1, max_epochs + 1):
        audit = baseline.audit()
        record = {
            "epoch": epoch,
            "audit": audit,
            "feedback_tasks": [],
            "note": "The process repeats without converting gaps into tasks.",
        }
        baseline_history.append(record)
        table_rows.append(_table_row("Fixed-output baseline", epoch, audit, []))

    qimo = ClosureState(origin=origin, terminal=terminal)
    qimo_history = []
    for epoch in range(1, max_epochs + 1):
        before = qimo.audit()
        feedback = _feedback_tasks(before)
        learned = qimo.apply_epoch(epoch)
        after = qimo.audit()
        record = {
            "epoch": epoch,
            "before": before,
            "feedback_tasks": feedback,
            "learned": learned,
            "rules": list(qimo.rules),
            "after": after,
        }
        qimo_history.append(record)
        table_rows.append(_table_row("Qimo feedback loop", epoch, after, feedback))
        if after["status"] == "closed":
            break

    baseline_final = baseline_history[-1]["audit"]
    qimo_final = qimo_history[-1]["after"]
    qimo_closed_epoch = next(
        (item["epoch"] for item in qimo_history if item["after"]["status"] == "closed"),
        None,
    )

    if qimo_closed_epoch is None:
        qimo_result = (
            f"NOT CLOSED after {max_epochs} epoch(s), but coverage reached "
            f"{int(qimo_final['coverage'] * 100)}%."
        )
    else:
        qimo_result = f"CLOSED at epoch {qimo_closed_epoch} with all quality gates satisfied."

    summary = (
        "### Closure result\n"
        f"**Fixed-output baseline:** NOT CLOSED after {max_epochs} epoch(s); "
        f"semantic coverage remains {int(baseline_final['coverage'] * 100)}%.\n\n"
        f"**Qimo feedback loop:** {qimo_result}\n\n"
        "> This bounded simulation demonstrates the encoded feedback mechanism. "
        "It is not empirical proof of consciousness, AGI, or unlimited autonomous evolution."
    )

    details = {
        "claim_scope": "bounded, verifiable structural self-evolution",
        "origin": origin,
        "terminal": terminal,
        "closure_rule": "success requires every semantic unit and quality gate",
        "fixed_output_baseline": baseline_history,
        "qimo_feedback_loop": qimo_history,
        "conclusion": (
            "Within this declared model, the Qimo loop converts explicit gaps into "
            "feedback tasks, updates memory and rules, and verifies closure."
        ),
    }
    return {"summary": summary, "rows": table_rows, "details": details}
