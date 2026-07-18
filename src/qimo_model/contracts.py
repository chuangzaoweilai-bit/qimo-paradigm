"""Data contracts shared by the Qimo runtime and benchmark domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Gap:
    code: str
    message: str
    evidence_required: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    closed: bool
    score: float
    gaps: tuple[Gap, ...]
    evidence: dict[str, Any]
    validated_rules: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "closed": self.closed,
            "score": round(self.score, 4),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "evidence": self.evidence,
            "validated_rules": list(self.validated_rules),
        }


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    domain: str
    origin: str
    terminal: str
    instruction: str
    answer_schema: str
    payload: dict[str, Any]
    max_epochs: int = 3

    def public_contract(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain,
            "origin": self.origin,
            "terminal": self.terminal,
            "instruction": self.instruction,
            "answer_schema": self.answer_schema,
            "input": self.payload["input"],
            "declared_checks": self.payload["declared_checks"],
        }


@dataclass
class EpochRecord:
    epoch: int
    mode: str
    raw_output: str
    candidate: dict[str, Any] | None
    parse_error: str | None
    validation: ValidationResult
    feedback_tasks: list[dict[str, str]] = field(default_factory=list)
    rules_available: list[str] = field(default_factory=list)
    model_claimed_closure: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch": self.epoch,
            "mode": self.mode,
            "raw_output": self.raw_output,
            "candidate": self.candidate,
            "parse_error": self.parse_error,
            "validation": self.validation.to_dict(),
            "feedback_tasks": self.feedback_tasks,
            "rules_available": self.rules_available,
            "model_claimed_closure": self.model_claimed_closure,
        }


@dataclass
class TaskRun:
    task_id: str
    domain: str
    mode: str
    status: str
    epochs: list[EpochRecord]
    committed_rules: list[str]

    @property
    def final_validation(self) -> ValidationResult:
        return self.epochs[-1].validation

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain,
            "mode": self.mode,
            "status": self.status,
            "epochs_used": len(self.epochs),
            "model_calls": len(self.epochs),
            "committed_rules": self.committed_rules,
            "history": [epoch.to_dict() for epoch in self.epochs],
        }


class ModelAdapter(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate one candidate from the unchanged base model."""
