"""Deterministic Qimo training trajectories and disjoint holdout tasks."""

from __future__ import annotations

import json
import random
from typing import Any

from qimo_model.contracts import TaskSpec
from qimo_model.native import stable_topological_order
from qimo_model.runtime import RuleMemory, build_epoch_prompt, feedback_tasks_from_gaps
from qimo_model.tasks import validate_task


SECURITY_FINDINGS = [
    "reentrancy",
    "missing_zero_address_check",
    "tx_origin_authentication",
]


def generate_training_tasks(per_domain: int = 40, seed: int = 1701) -> list[TaskSpec]:
    return _generate_tasks("train", per_domain, seed)


def generate_holdout_tasks(per_domain: int = 10, seed: int = 2607) -> list[TaskSpec]:
    return _generate_tasks("holdout", per_domain, seed)


def _generate_tasks(prefix: str, per_domain: int, seed: int) -> list[TaskSpec]:
    rng = random.Random(seed)
    tasks: list[TaskSpec] = []
    for index in range(per_domain):
        tasks.append(_software_task(prefix, index, rng))
        tasks.append(_security_task(prefix, index, rng))
        tasks.append(_planning_task(prefix, index, rng))
    return tasks


def _software_task(prefix: str, index: int, rng: random.Random) -> TaskSpec:
    if index % 2 == 0:
        collection = rng.choice(["records", "entries", "samples", "events"])
        cursor = rng.choice(["index", "cursor", "position"])
        expected = f"for {cursor} in range(len({collection})):"
        return TaskSpec(
            task_id=f"{prefix}.software.loop-{index:03d}",
            domain="software_repair",
            origin=f"A loop over {collection} skips its final element.",
            terminal="The replacement header visits every valid index exactly once.",
            instruction="Return only the complete corrected for-loop header.",
            answer_schema='answer must be a string containing one complete Python for-loop header',
            payload={
                "input": {
                    "code": (
                        f"def copy_{prefix}_{index}({collection}):\n"
                        "    output = []\n"
                        f"    for {cursor} in range(len({collection}) - 1):\n"
                        f"        output.append({collection}[{cursor}])\n"
                        "    return output"
                    )
                },
                "declared_checks": [
                    "empty input stays empty",
                    "one input item is copied",
                    "the last input item is copied",
                ],
                "expected_answer": expected,
                "failure_feedback": (
                    "The loop bound must cover each integer index from zero through "
                    f"len({collection}) - 1 exactly once."
                ),
            },
        )

    value = rng.choice(["reading", "measurement", "value", "score"])
    low = rng.choice(["floor", "lower", "minimum"])
    high = rng.choice(["ceiling", "upper", "maximum"])
    return TaskSpec(
        task_id=f"{prefix}.software.clamp-{index:03d}",
        domain="software_repair",
        origin="A clamp expression reverses its lower and upper boundary operations.",
        terminal="The replacement line preserves in-range values and clamps both boundaries.",
        instruction="Return only the corrected return statement.",
        answer_schema='answer must be a string containing one Python return statement',
        payload={
            "input": {
                "code": (
                    f"def clamp_{prefix}_{index}({value}, {low}, {high}):\n"
                    f"    return min({low}, max({high}, {value}))"
                )
            },
            "declared_checks": [
                "an in-range value is unchanged",
                "a value below the lower boundary returns the lower boundary",
                "a value above the upper boundary returns the upper boundary",
            ],
            "expected_answer": f"return max({low}, min({high}, {value}))",
            "failure_feedback": "The expression must preserve in-range values and clamp both boundaries.",
        },
    )


def _security_task(prefix: str, index: int, rng: random.Random) -> TaskSpec:
    finding = SECURITY_FINDINGS[index % len(SECURITY_FINDINGS)]
    suffix = rng.randint(100, 999)
    if finding == "reentrancy":
        code = (
            f"function withdraw{suffix}(uint256 amount) external {{\n"
            "  require(credit[msg.sender] >= amount);\n"
            "  (bool sent,) = msg.sender.call{value: amount}(\"\");\n"
            "  require(sent);\n"
            "  credit[msg.sender] -= amount;\n"
            "}"
        )
        feedback = "An external value transfer occurs before the caller balance is reduced."
    elif finding == "missing_zero_address_check":
        code = (
            f"function setGuardian{suffix}(address nextGuardian) external onlyOwner {{\n"
            "  guardian = nextGuardian;\n"
            "}"
        )
        feedback = "A privileged address can be assigned to the zero address without validation."
    else:
        code = (
            f"function privileged{suffix}() external {{\n"
            "  require(tx.origin == owner);\n"
            "  executeSensitiveAction();\n"
            "}"
        )
        feedback = "Authorization relies on tx.origin rather than the immediate caller."

    return TaskSpec(
        task_id=f"{prefix}.contracts.{finding}-{index:03d}",
        domain="smart_contract_audit",
        origin="A Solidity snippet must be mapped to evidenced normalized findings.",
        terminal="The finding list exactly matches the supplied code evidence.",
        instruction="Return only supported normalized findings.",
        answer_schema=(
            "answer must be a JSON list containing only exact identifier strings "
            "from input.allowed_findings"
        ),
        payload={
            "input": {"code": code, "allowed_findings": list(SECURITY_FINDINGS)},
            "declared_checks": [
                "each finding has supplied code evidence",
                "unsupported findings are excluded",
            ],
            "expected_answer": [finding],
            "finding_feedback": {finding: feedback},
        },
    )


def _planning_task(prefix: str, index: int, rng: random.Random) -> TaskSpec:
    verbs = rng.sample(
        [
            "collect",
            "inspect",
            "normalize",
            "approve",
            "package",
            "publish",
            "monitor",
            "archive",
        ],
        6,
    )
    steps = [f"{verb}_{prefix}_{index}" for verb in verbs]
    constraints = [
        (steps[0], steps[1]),
        (steps[1], steps[2]),
        (steps[1], steps[3]),
        (steps[2], steps[4]),
        (steps[3], steps[4]),
        (steps[4], steps[5]),
    ]
    public_constraints = [f"{before} before {after}" for before, after in constraints]
    return TaskSpec(
        task_id=f"{prefix}.planning.workflow-{index:03d}",
        domain="multi_step_planning",
        origin="A workflow has six declared steps and dependency constraints.",
        terminal="Every step appears exactly once and every dependency is satisfied.",
        instruction="Return one valid ordered list of all declared step identifiers.",
        answer_schema="answer must be an ordered JSON list of exact step identifier strings",
        payload={
            "input": {"steps": steps, "constraints": public_constraints},
            "declared_checks": [
                "use every declared step exactly once",
                "satisfy every precedence constraint",
            ],
            "steps": steps,
            "constraints": constraints,
        },
    )


def correct_candidate(task: TaskSpec) -> dict[str, Any]:
    if task.domain in {"software_repair", "smart_contract_audit"}:
        answer = task.payload["expected_answer"]
    else:
        answer = stable_topological_order(
            task.payload["steps"], task.payload["constraints"]
        )
    return {
        "task_id": task.task_id,
        "answer": answer,
        "evidence": [f"Satisfied check: {check}" for check in task.payload["declared_checks"]],
        "rules_applied": ["external_validator_controls_closure"],
        "closure_claim": False,
    }


def failure_candidate(task: TaskSpec) -> dict[str, Any]:
    if task.domain == "software_repair":
        expected = task.payload["expected_answer"]
        answer = expected[:-1] if expected.endswith(":") else "return None"
    elif task.domain == "smart_contract_audit":
        answer = list(task.payload["input"]["allowed_findings"])
    else:
        answer = list(reversed(task.payload["steps"]))
    return {
        "task_id": task.task_id,
        "answer": answer,
        "evidence": ["Initial candidate requires external validation."],
        "rules_applied": [],
        "closure_claim": False,
    }


def build_training_examples(tasks: list[TaskSpec]) -> list[dict[str, Any]]:
    memory = RuleMemory()
    examples: list[dict[str, Any]] = []
    for task in tasks:
        rules = memory.rules_for(task.domain)
        correct = correct_candidate(task)
        initial_prompt = build_epoch_prompt(task, "qimo", 1, rules, None, [])
        examples.append(
            {
                "example_id": f"{task.task_id}.origin",
                "phase": "origin_candidate",
                "task_id": task.task_id,
                "prompt": initial_prompt,
                "target": json.dumps(correct, ensure_ascii=True, separators=(",", ":")),
            }
        )

        failed = failure_candidate(task)
        validation = validate_task(task, failed)
        feedback = feedback_tasks_from_gaps(validation.gaps)
        correction_prompt = build_epoch_prompt(
            task, "qimo", 2, rules, failed, feedback
        )
        examples.append(
            {
                "example_id": f"{task.task_id}.feedback",
                "phase": "gap_correction",
                "task_id": task.task_id,
                "prompt": correction_prompt,
                "target": json.dumps(correct, ensure_ascii=True, separators=(",", ":")),
            }
        )
    return examples


def task_fingerprint(task: TaskSpec) -> str:
    public = json.dumps(task.public_contract(), ensure_ascii=True, sort_keys=True)
    return public
