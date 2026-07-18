"""Machine-verifiable tasks spanning three benchmark domains."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from qimo_model.contracts import Gap, TaskSpec, ValidationResult


Validator = Callable[[TaskSpec, dict[str, Any] | None, str | None], ValidationResult]
VALIDATOR_PROTOCOL_VERSION = "1.0.0"


def _evidence_gap(candidate: dict[str, Any] | None) -> list[Gap]:
    if not candidate or not isinstance(candidate.get("evidence"), list):
        return [
            Gap(
                "missing_evidence",
                "The candidate does not contain an evidence list.",
                "Provide at least one observable reason tied to a declared check.",
            )
        ]
    evidence = [item for item in candidate["evidence"] if isinstance(item, str) and item.strip()]
    if not evidence:
        return [
            Gap(
                "missing_evidence",
                "The evidence list is empty.",
                "Provide at least one observable reason tied to a declared check.",
            )
        ]
    return []


def _parse_gap(parse_error: str | None) -> ValidationResult | None:
    if not parse_error:
        return None
    return ValidationResult(
        closed=False,
        score=0.0,
        gaps=(
            Gap(
                "invalid_json",
                parse_error,
                "Return one JSON object matching the declared answer schema.",
            ),
        ),
        evidence={"parse_error": parse_error},
    )


def _normalize_patch(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", "", value.strip().rstrip(";"))


def validate_software_patch(
    task: TaskSpec,
    candidate: dict[str, Any] | None,
    parse_error: str | None,
) -> ValidationResult:
    parsed = _parse_gap(parse_error)
    if parsed:
        return parsed

    candidate = candidate or {}
    raw_answer = candidate.get("answer")
    expected_answer = task.payload["expected_answer"]
    observed = _normalize_patch(raw_answer)
    expected = _normalize_patch(expected_answer)
    gaps = _evidence_gap(candidate)
    patch_matches = observed == expected
    missing_required_colon = (
        isinstance(raw_answer, str)
        and expected_answer.rstrip().endswith(":")
        and not raw_answer.rstrip().endswith(":")
        and _normalize_patch(raw_answer.rstrip() + ":") == expected
    )
    if missing_required_colon:
        gaps.append(
            Gap(
                "patch_syntax_missing_colon",
                "The proposed Python for-loop header is syntactically incomplete because it does not end with a colon.",
                "Return a complete Python for-loop header ending with a colon.",
            )
        )
    elif not patch_matches:
        gaps.append(
            Gap(
                "patch_behavior_mismatch",
                task.payload["failure_feedback"],
                "Return one replacement line that satisfies every declared behavior check.",
            )
        )

    evidence_ok = not any(gap.code == "missing_evidence" for gap in gaps)
    closed = patch_matches and evidence_ok
    patch_score = 0.8 if patch_matches else (0.6 if missing_required_colon else 0.0)
    return ValidationResult(
        closed=closed,
        score=patch_score + (0.2 if evidence_ok else 0.0),
        gaps=tuple(gaps),
        evidence={
            "patch_matches_reference": patch_matches,
            "behavior_matches_except_syntax": missing_required_colon,
            "declared_checks": task.payload["declared_checks"],
        },
        validated_rules=("software_patch_must_satisfy_declared_behavior",) if closed else (),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def validate_security_findings(
    task: TaskSpec,
    candidate: dict[str, Any] | None,
    parse_error: str | None,
) -> ValidationResult:
    parsed = _parse_gap(parse_error)
    if parsed:
        return parsed

    candidate = candidate or {}
    observed = _string_list(candidate.get("answer"))
    expected = list(task.payload["expected_answer"])
    observed_set = set(observed)
    expected_set = set(expected)
    missing = expected_set - observed_set
    unexpected = observed_set - expected_set
    gaps = _evidence_gap(candidate)
    if not isinstance(candidate.get("answer"), list):
        gaps.append(
            Gap(
                "answer_not_list",
                "The answer is not a list of normalized finding identifiers.",
                "Return the answer as a JSON list.",
            )
        )
    for finding in sorted(missing):
        gaps.append(
            Gap(
                "missing_required_finding",
                task.payload["finding_feedback"][finding],
                (
                    "Select the exact identifier from input.allowed_findings whose semantics "
                    "match the cited code evidence."
                ),
            )
        )
    if unexpected:
        gaps.append(
            Gap(
                "unsupported_findings",
                f"Unsupported finding identifiers were produced: {sorted(unexpected)}.",
                "Remove findings that cannot be tied to the supplied code.",
            )
        )

    evidence_ok = not any(gap.code == "missing_evidence" for gap in gaps)
    answer_ok = not missing and not unexpected and isinstance(candidate.get("answer"), list)
    union = expected_set | observed_set
    finding_score = len(expected_set & observed_set) / len(union) if union else 1.0
    closed = answer_ok and evidence_ok
    return ValidationResult(
        closed=closed,
        score=0.8 * finding_score + (0.2 if evidence_ok else 0.0),
        gaps=tuple(gaps),
        evidence={
            "matched_findings": sorted(expected_set & observed_set),
            "missing_count": len(missing),
            "unsupported_count": len(unexpected),
            "unsupported_findings": sorted(unexpected),
        },
        validated_rules=("security_finding_requires_code_evidence",) if closed else (),
    )


def validate_plan(
    task: TaskSpec,
    candidate: dict[str, Any] | None,
    parse_error: str | None,
) -> ValidationResult:
    parsed = _parse_gap(parse_error)
    if parsed:
        return parsed

    candidate = candidate or {}
    plan = _string_list(candidate.get("answer"))
    expected_steps = list(task.payload["steps"])
    expected_set = set(expected_steps)
    observed_set = set(plan)
    gaps = _evidence_gap(candidate)

    if not isinstance(candidate.get("answer"), list):
        gaps.append(
            Gap(
                "answer_not_list",
                "The plan is not a JSON list.",
                "Return an ordered JSON list of step identifiers.",
            )
        )
    if len(plan) != len(observed_set):
        gaps.append(
            Gap(
                "duplicate_steps",
                "At least one plan step appears more than once.",
                "Use every declared step exactly once.",
            )
        )
    missing = expected_set - observed_set
    unknown = observed_set - expected_set
    if missing:
        gaps.append(
            Gap(
                "missing_steps",
                f"The plan omits declared steps: {sorted(missing)}.",
                "Include every declared step exactly once.",
            )
        )
    if unknown:
        gaps.append(
            Gap(
                "unknown_steps",
                f"The plan contains undeclared steps: {sorted(unknown)}.",
                "Remove all undeclared steps.",
            )
        )

    index = {step: position for position, step in enumerate(plan)}
    passed_constraints = 0
    for before, after in task.payload["constraints"]:
        if before in index and after in index and index[before] < index[after]:
            passed_constraints += 1
        else:
            gaps.append(
                Gap(
                    f"precedence_violation:{before}:{after}",
                    f"The plan does not place {before} before {after}.",
                    f"Produce evidence that {before} precedes {after}.",
                )
            )

    evidence_ok = not any(gap.code == "missing_evidence" for gap in gaps)
    structure_checks = 3 + len(task.payload["constraints"])
    structure_passed = (
        int(isinstance(candidate.get("answer"), list))
        + int(len(plan) == len(observed_set))
        + int(not missing and not unknown)
        + passed_constraints
    )
    closed = structure_passed == structure_checks and evidence_ok
    return ValidationResult(
        closed=closed,
        score=0.8 * (structure_passed / structure_checks) + (0.2 if evidence_ok else 0.0),
        gaps=tuple(gaps),
        evidence={
            "steps_present": sorted(observed_set & expected_set),
            "precedence_passed": passed_constraints,
            "precedence_total": len(task.payload["constraints"]),
        },
        validated_rules=("plan_must_cover_steps_and_respect_precedence",) if closed else (),
    )


VALIDATORS: dict[str, Validator] = {
    "software_repair": validate_software_patch,
    "smart_contract_audit": validate_security_findings,
    "multi_step_planning": validate_plan,
}


def validate_task(
    task: TaskSpec,
    candidate: dict[str, Any] | None,
    parse_error: str | None = None,
) -> ValidationResult:
    return VALIDATORS[task.domain](task, candidate, parse_error)


def default_task_suite() -> list[TaskSpec]:
    return [
        TaskSpec(
            task_id="software.clamp-boundaries",
            domain="software_repair",
            origin="A clamp function returns incorrect values at both boundaries.",
            terminal="One replacement return line satisfies all declared clamp checks.",
            instruction="Return only the corrected return statement for the buggy line.",
            answer_schema='answer must be a string; example shape: "return expression"',
            payload={
                "input": {
                    "code": "def clamp(value, low, high):\n    return min(low, max(high, value))",
                },
                "declared_checks": [
                    "clamp(5, 0, 10) == 5",
                    "clamp(-2, 0, 10) == 0",
                    "clamp(12, 0, 10) == 10",
                ],
                "expected_answer": "return max(low, min(high, value))",
                "failure_feedback": (
                    "The replacement does not preserve an in-range value while clamping "
                    "values below low and above high to their respective boundaries."
                ),
            },
        ),
        TaskSpec(
            task_id="software.off-by-one",
            domain="software_repair",
            origin="The loop skips the final item in every non-empty list.",
            terminal="One replacement loop header visits every valid list index exactly once.",
            instruction="Return only the corrected for-loop header.",
            answer_schema='answer must be a string; example shape: "for ...:"',
            payload={
                "input": {
                    "code": "def collect(items):\n    out = []\n    for i in range(len(items) - 1):\n        out.append(items[i])\n    return out",
                },
                "declared_checks": [
                    "collect([]) == []",
                    "collect(['a']) == ['a']",
                    "collect(['a', 'b']) == ['a', 'b']",
                ],
                "expected_answer": "for i in range(len(items)):",
                "failure_feedback": (
                    "The proposed loop bound does not visit each valid index from zero "
                    "through len(items) - 1 exactly once."
                ),
            },
        ),
        TaskSpec(
            task_id="contracts.withdraw-order",
            domain="smart_contract_audit",
            origin="A Solidity withdrawal function performs an external call before accounting is finalized.",
            terminal="The normalized finding list exactly matches the vulnerabilities evidenced by the code.",
            instruction="Return normalized security finding identifiers supported by the code.",
            answer_schema=(
                "answer must be a JSON list containing only exact identifier strings "
                "from input.allowed_findings"
            ),
            payload={
                "input": {
                    "code": (
                        "function withdraw(uint256 amount) external {\n"
                        "  require(balances[msg.sender] >= amount);\n"
                        "  (bool ok,) = msg.sender.call{value: amount}(\"\");\n"
                        "  require(ok);\n"
                        "  balances[msg.sender] -= amount;\n"
                        "}"
                    ),
                    "allowed_findings": [
                        "reentrancy",
                        "missing_zero_address_check",
                        "tx_origin_authentication",
                    ],
                },
                "declared_checks": [
                    "Every finding must cite supplied code evidence.",
                    "No unsupported finding identifier is allowed.",
                ],
                "expected_answer": ["reentrancy"],
                "finding_feedback": {
                    "reentrancy": (
                        "The audit has not accounted for external value transfer occurring "
                        "before the sender balance is reduced."
                    )
                },
            },
        ),
        TaskSpec(
            task_id="contracts.owner-validation",
            domain="smart_contract_audit",
            origin="An ownership transfer accepts any address without validating it.",
            terminal="The normalized finding list exactly matches the evidenced access-control risk.",
            instruction="Return normalized security finding identifiers supported by the code.",
            answer_schema=(
                "answer must be a JSON list containing only exact identifier strings "
                "from input.allowed_findings"
            ),
            payload={
                "input": {
                    "code": "function transferOwnership(address newOwner) external onlyOwner { owner = newOwner; }",
                    "allowed_findings": [
                        "reentrancy",
                        "missing_zero_address_check",
                        "tx_origin_authentication",
                    ],
                },
                "declared_checks": [
                    "Every finding must cite supplied code evidence.",
                    "No unsupported finding identifier is allowed.",
                ],
                "expected_answer": ["missing_zero_address_check"],
                "finding_feedback": {
                    "missing_zero_address_check": (
                        "The audit has not accounted for ownership being assignable to the zero address."
                    )
                },
            },
        ),
        TaskSpec(
            task_id="planning.release-order",
            domain="multi_step_planning",
            origin="A release has five declared steps and four precedence constraints.",
            terminal="The plan contains every step exactly once and satisfies every precedence constraint.",
            instruction="Return one valid ordered list of the declared step identifiers.",
            answer_schema="answer must be an ordered JSON list of step identifier strings",
            payload={
                "input": {
                    "steps": ["spec", "implement", "test", "security_review", "release"],
                    "constraints": [
                        "spec before implement",
                        "implement before test",
                        "implement before security_review",
                        "test and security_review before release",
                    ],
                },
                "declared_checks": [
                    "Use every step exactly once.",
                    "Satisfy every precedence constraint.",
                ],
                "steps": ["spec", "implement", "test", "security_review", "release"],
                "constraints": [
                    ("spec", "implement"),
                    ("implement", "test"),
                    ("implement", "security_review"),
                    ("test", "release"),
                    ("security_review", "release"),
                ],
            },
        ),
        TaskSpec(
            task_id="planning.data-pipeline",
            domain="multi_step_planning",
            origin="A data pipeline must order collection, validation, transformation, training, and evaluation.",
            terminal="The plan contains every step exactly once and satisfies every data dependency.",
            instruction="Return one valid ordered list of the declared step identifiers.",
            answer_schema="answer must be an ordered JSON list of step identifier strings",
            payload={
                "input": {
                    "steps": ["collect", "validate", "transform", "train", "evaluate"],
                    "constraints": [
                        "collect before validate",
                        "validate before transform",
                        "transform before train",
                        "train before evaluate",
                    ],
                },
                "declared_checks": [
                    "Use every step exactly once.",
                    "Satisfy every precedence constraint.",
                ],
                "steps": ["collect", "validate", "transform", "train", "evaluate"],
                "constraints": [
                    ("collect", "validate"),
                    ("validate", "transform"),
                    ("transform", "train"),
                    ("train", "evaluate"),
                ],
            },
        ),
    ]
