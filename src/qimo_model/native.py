"""Qimo-native structural kernel with evidence-bounded repair operators."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol

from qimo_model.contracts import ModelAdapter, TaskSpec, ValidationResult
from qimo_model.runtime import (
    RuleMemory,
    build_epoch_prompt,
    feedback_tasks_from_gaps,
    parse_candidate,
)
from qimo_model.tasks import validate_task


@dataclass(frozen=True)
class RepairOutcome:
    applied: bool
    candidate: dict[str, Any]
    actions: tuple[str, ...] = ()


class RepairOperator(Protocol):
    def apply(
        self,
        task: TaskSpec,
        candidate: dict[str, Any],
        validation: ValidationResult,
    ) -> RepairOutcome:
        """Apply only transformations justified by public contract evidence."""


class PythonSyntaxCompletionOperator:
    def apply(
        self,
        task: TaskSpec,
        candidate: dict[str, Any],
        validation: ValidationResult,
    ) -> RepairOutcome:
        gap_codes = {gap.code for gap in validation.gaps}
        answer = candidate.get("answer")
        if (
            task.domain == "software_repair"
            and "patch_syntax_missing_colon" in gap_codes
            and isinstance(answer, str)
            and not answer.rstrip().endswith(":")
        ):
            repaired = dict(candidate)
            repaired["answer"] = answer.rstrip() + ":"
            return RepairOutcome(
                applied=True,
                candidate=repaired,
                actions=("complete_python_block_header_colon",),
            )
        return RepairOutcome(False, candidate)


class AllowedFindingProjectionOperator:
    def apply(
        self,
        task: TaskSpec,
        candidate: dict[str, Any],
        validation: ValidationResult,
    ) -> RepairOutcome:
        if task.domain != "smart_contract_audit":
            return RepairOutcome(False, candidate)
        unsupported = set(validation.evidence.get("unsupported_findings", []))
        answer = candidate.get("answer")
        if not unsupported or not isinstance(answer, list):
            return RepairOutcome(False, candidate)
        repaired_answer = [item for item in answer if item not in unsupported]
        if repaired_answer == answer:
            return RepairOutcome(False, candidate)
        repaired = dict(candidate)
        repaired["answer"] = repaired_answer
        return RepairOutcome(
            applied=True,
            candidate=repaired,
            actions=("remove_externally_rejected_finding_identifiers",),
        )


class PrecedenceProjectionOperator:
    def apply(
        self,
        task: TaskSpec,
        candidate: dict[str, Any],
        validation: ValidationResult,
    ) -> RepairOutcome:
        if task.domain != "multi_step_planning" or not validation.gaps:
            return RepairOutcome(False, candidate)
        structural_codes = {
            "answer_not_list",
            "duplicate_steps",
            "missing_steps",
            "unknown_steps",
        }
        has_plan_gap = any(
            gap.code in structural_codes or gap.code.startswith("precedence_violation:")
            for gap in validation.gaps
        )
        if not has_plan_gap:
            return RepairOutcome(False, candidate)

        ordered = stable_topological_order(
            task.payload["steps"], task.payload["constraints"]
        )
        if not ordered or candidate.get("answer") == ordered:
            return RepairOutcome(False, candidate)
        repaired = dict(candidate)
        repaired["answer"] = ordered
        return RepairOutcome(
            applied=True,
            candidate=repaired,
            actions=("project_plan_onto_declared_precedence_graph",),
        )


def stable_topological_order(
    steps: list[str], constraints: list[tuple[str, str]]
) -> list[str]:
    position = {step: index for index, step in enumerate(steps)}
    outgoing: dict[str, list[str]] = {step: [] for step in steps}
    indegree = {step: 0 for step in steps}
    for before, after in constraints:
        if before not in outgoing or after not in outgoing:
            return []
        if after not in outgoing[before]:
            outgoing[before].append(after)
            indegree[after] += 1

    ready = sorted((step for step in steps if indegree[step] == 0), key=position.get)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for neighbor in sorted(outgoing[current], key=position.get):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
                ready.sort(key=position.get)
    return ordered if len(ordered) == len(steps) else []


class RepairRegistry:
    def __init__(self) -> None:
        self.operators: tuple[RepairOperator, ...] = (
            PythonSyntaxCompletionOperator(),
            AllowedFindingProjectionOperator(),
            PrecedenceProjectionOperator(),
        )

    def apply(
        self,
        task: TaskSpec,
        candidate: dict[str, Any],
        validation: ValidationResult,
    ) -> RepairOutcome:
        current = candidate
        actions: list[str] = []
        for operator in self.operators:
            outcome = operator.apply(task, current, validation)
            if outcome.applied:
                current = outcome.candidate
                actions.extend(outcome.actions)
                validation = validate_task(task, current)
        return RepairOutcome(bool(actions), current, tuple(actions))


@dataclass
class NativeStep:
    sequence: int
    source: str
    candidate: dict[str, Any] | None
    validation: ValidationResult
    raw_output: str | None = None
    parse_error: str | None = None
    actions: tuple[str, ...] = ()
    feedback_tasks: tuple[dict[str, str], ...] = ()
    repeated_state: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "source": self.source,
            "candidate": self.candidate,
            "raw_output": self.raw_output,
            "parse_error": self.parse_error,
            "actions": list(self.actions),
            "feedback_tasks": list(self.feedback_tasks),
            "repeated_state": self.repeated_state,
            "validation": self.validation.to_dict(),
        }


@dataclass
class NativeRun:
    task_id: str
    domain: str
    status: str
    termination: str
    steps: list[NativeStep]
    model_calls: int
    operator_steps: int
    committed_rules: list[str]

    @property
    def structural_invariants(self) -> dict[str, bool]:
        return {
            "no_false_closure": self.status != "closed" or self.steps[-1].validation.closed,
            "failed_steps_have_gaps": all(
                step.validation.closed or bool(step.validation.gaps) for step in self.steps
            ),
            "closure_is_external": all(
                not (
                    step.candidate
                    and step.candidate.get("closure_claim") is True
                    and not step.validation.closed
                    and self.status == "closed"
                )
                for step in self.steps
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain,
            "status": self.status,
            "termination": self.termination,
            "model_calls": self.model_calls,
            "operator_steps": self.operator_steps,
            "committed_rules": self.committed_rules,
            "structural_invariants": self.structural_invariants,
            "steps": [step.to_dict() for step in self.steps],
        }


def _state_signature(candidate: dict[str, Any] | None, validation: ValidationResult) -> str:
    state = {
        "candidate": candidate,
        "gaps": [gap.code for gap in validation.gaps],
    }
    encoded = json.dumps(state, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


class QimoNativeModel:
    """Hybrid kernel: generative paths plus deterministic structural operators."""

    def __init__(
        self,
        adapter: ModelAdapter,
        memory: RuleMemory | None = None,
        repairs: RepairRegistry | None = None,
    ) -> None:
        self.adapter = adapter
        self.memory = memory or RuleMemory()
        self.repairs = repairs or RepairRegistry()

    def run_task(self, task: TaskSpec) -> NativeRun:
        steps: list[NativeStep] = []
        seen_states: set[str] = set()
        feedback: list[dict[str, str]] = []
        previous_candidate: dict[str, Any] | None = None
        committed_rules: list[str] = []
        model_calls = 0
        operator_steps = 0

        for epoch in range(1, task.max_epochs + 1):
            rules = self.memory.rules_for(task.domain)
            prompt = build_epoch_prompt(
                task,
                "qimo",
                epoch,
                rules,
                previous_candidate,
                feedback,
            )
            if epoch > 1 and steps[-1].repeated_state:
                prompt += (
                    "\nPATH_ESCALATION=The prior candidate and gap state repeated. "
                    "Enumerate the declared constraints, eliminate rejected values, and use a different path.\n"
                )

            raw_output = self.adapter.generate(prompt)
            model_calls += 1
            candidate, parse_error = parse_candidate(raw_output)
            validation = validate_task(task, candidate, parse_error)
            signature = _state_signature(candidate, validation)
            repeated = signature in seen_states
            seen_states.add(signature)
            feedback = feedback_tasks_from_gaps(validation.gaps)
            if repeated:
                feedback.append(
                    {
                        "gap_code": "repeated_state_detected",
                        "task": "The candidate and gap state repeated without progress.",
                        "evidence_required": "Use a different path and change the candidate state.",
                    }
                )
            steps.append(
                NativeStep(
                    sequence=len(steps) + 1,
                    source="base_model",
                    candidate=candidate,
                    raw_output=raw_output,
                    parse_error=parse_error,
                    validation=validation,
                    feedback_tasks=tuple(feedback),
                    repeated_state=repeated,
                )
            )
            if validation.closed:
                committed_rules = self.memory.commit(
                    task.domain, validation.validated_rules
                )
                return self._finish(
                    task, steps, model_calls, operator_steps, committed_rules, "verified_terminal"
                )

            if candidate is not None:
                repair = self.repairs.apply(task, candidate, validation)
                if repair.applied:
                    operator_steps += 1
                    repaired_validation = validate_task(task, repair.candidate)
                    feedback = feedback_tasks_from_gaps(repaired_validation.gaps)
                    steps.append(
                        NativeStep(
                            sequence=len(steps) + 1,
                            source="structural_operator",
                            candidate=repair.candidate,
                            validation=repaired_validation,
                            actions=repair.actions,
                            feedback_tasks=tuple(feedback),
                        )
                    )
                    previous_candidate = repair.candidate
                    if repaired_validation.closed:
                        committed_rules = self.memory.commit(
                            task.domain, repaired_validation.validated_rules
                        )
                        return self._finish(
                            task,
                            steps,
                            model_calls,
                            operator_steps,
                            committed_rules,
                            "verified_terminal_after_structural_repair",
                        )
                    continue
            previous_candidate = candidate

        return self._finish(
            task,
            steps,
            model_calls,
            operator_steps,
            committed_rules,
            "path_budget_exhausted_with_explicit_gaps",
        )

    @staticmethod
    def _finish(
        task: TaskSpec,
        steps: list[NativeStep],
        model_calls: int,
        operator_steps: int,
        committed_rules: list[str],
        termination: str,
    ) -> NativeRun:
        status = "closed" if steps[-1].validation.closed else "not_closed"
        return NativeRun(
            task_id=task.task_id,
            domain=task.domain,
            status=status,
            termination=termination,
            steps=steps,
            model_calls=model_calls,
            operator_steps=operator_steps,
            committed_rules=committed_rules,
        )
