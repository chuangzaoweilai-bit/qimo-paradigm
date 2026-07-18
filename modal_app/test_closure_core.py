"""Unit tests for the deterministic Modal proposal boundary."""

from __future__ import annotations

import unittest

from modal_app.closure_core import (
    RequestError,
    normalize_request,
    parse_model_json,
    validate_candidate,
)


class ClosureCoreTests(unittest.TestCase):
    def test_normalize_computes_gaps_from_present_state(self) -> None:
        request = normalize_request(
            {
                "present_units": ["origin_modeling"],
                "present_gates": ["has_origin"],
                "epoch": 2,
            }
        )
        self.assertNotIn("origin_modeling", request["missing_units"])
        self.assertNotIn("has_origin", request["missing_gates"])
        self.assertIn("terminal_modeling", request["missing_units"])

    def test_unknown_state_value_is_rejected(self) -> None:
        with self.assertRaises(RequestError):
            normalize_request({"present_units": ["invented_unit"]})

    def test_markdown_wrapped_json_is_parsed(self) -> None:
        parsed = parse_model_json('```json\n{"closure_claim": false}\n```')
        self.assertIs(parsed["closure_claim"], False)

    def test_valid_bounded_candidate_is_accepted(self) -> None:
        request = normalize_request({"epoch": 1})
        result = validate_candidate(
            {
                "feedback_tasks": [
                    {
                        "target": "origin_modeling",
                        "task": "Represent the declared origin as structured data.",
                        "evidence_required": "A schema-valid origin record.",
                    }
                ],
                "semantic_updates": [
                    {
                        "unit": "origin_modeling",
                        "content": "Candidate structured origin representation.",
                    }
                ],
                "rule_updates": ["Reject an origin without schema evidence."],
                "quality_checks": ["Validate the origin record against its schema."],
                "closure_claim": False,
            },
            request,
        )
        self.assertEqual(result["verdict"], "accepted")

    def test_model_cannot_claim_closure(self) -> None:
        request = normalize_request({"epoch": 1})
        result = validate_candidate(
            {
                "feedback_tasks": [
                    {
                        "target": "origin_modeling",
                        "task": "Create origin evidence.",
                        "evidence_required": "A validated record.",
                    }
                ],
                "semantic_updates": [],
                "rule_updates": [],
                "quality_checks": [],
                "closure_claim": True,
            },
            request,
        )
        self.assertEqual(result["verdict"], "rejected")
        self.assertIn("closure_claim must be false", result["errors"])


if __name__ == "__main__":
    unittest.main()
