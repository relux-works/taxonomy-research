"""Focused tests for the eval-time attribution pilot."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "evals" / "attribution_pilot.py"
SPEC = importlib.util.spec_from_file_location("attribution_pilot", MODULE_PATH)
assert SPEC and SPEC.loader
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


class AttributionPilotTests(unittest.TestCase):
    def _load_mutant(self, old: str, new: str):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertEqual(source.count(old), 1, "mutation target must remain unique")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mutant.py"
            path.write_text(source.replace(old, new), encoding="utf-8")
            spec = importlib.util.spec_from_file_location("attribution_pilot_mutant", path)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return module

    # Proves generated annotations are reversible and every declared source
    # fragment resolves uniquely in the pinned real inputs.
    def test_prepare_builds_reversible_fixtures_and_unique_source_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source_map = pilot.prepare_fixtures(output)
            fixtures = output / "fixtures"
            for source in ("original", "semantic"):
                clean = (fixtures / f"{source}-clean.md").read_text()
                instrumented = (fixtures / f"{source}-instrumented.md").read_text()
                self.assertEqual(pilot.TAG_RE.sub("", instrumented), clean)
            self.assertTrue(all(row["match_count"] == 1 for row in source_map["entries"]))
            self.assertNotIn("CAV-SEM-", (fixtures / "semantic-clean.md").read_text())

    # Proves missing and ambiguous anchors fail closed instead of generating a
    # misleading source map.
    def test_instrument_source_rejects_missing_and_ambiguous_anchors(self) -> None:
        base = {"key": "x", "category": "positive-example", "anchor": "same"}
        with self.assertRaisesRegex(pilot.PilotError, "match count 0"):
            pilot.instrument_source("different", "original", [base], "abc", "hash")
        with self.assertRaisesRegex(pilot.PilotError, "match count 2"):
            pilot.instrument_source("same same", "original", [base], "abc", "hash")

    # Mutation controls prove the behavioral tests kill gates weakened to admit
    # one duplicate anchor, one duplicate answer span, or one wrong-arm ID.
    def test_narrowing_mutants_are_killed_by_behavioral_contracts(self) -> None:
        anchor_mutant = self._load_mutant(
            "if match_count != 1:", "if match_count == 0:"
        )
        base = {"key": "x", "category": "positive-example", "anchor": "same"}

        def assert_duplicate_anchor_rejected(module) -> None:
            with self.assertRaises(ValueError):
                module.instrument_source(
                    "same same", "original", [base], "abc", "hash"
                )

        assert_duplicate_anchor_rejected(pilot)
        with self.assertRaises(AssertionError):
            assert_duplicate_anchor_rejected(anchor_mutant)

        span_mutant = self._load_mutant(
            "elif answer.count(span) != 1:", "elif answer.count(span) == 0:"
        )
        repeated_record = {
            "cell": "repeat",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "repeat repeat E_CONN_RESET",
                "annotations": [
                    {"span": "repeat", "rule_id": "EVO-AAAAAAAA-01"}
                ],
            },
        }
        repeated_map = self._map()
        repeated_map["entries"][0]["lexical_any"] = ["repeat"]

        def assert_duplicate_span_rejected(module) -> None:
            checked = module.validate_response(
                repeated_record, self._case(), repeated_map
            )
            self.assertFalse(checked["claims"][0]["structurally_valid"])

        assert_duplicate_span_rejected(pilot)
        with self.assertRaises(AssertionError):
            assert_duplicate_span_rejected(span_mutant)

        arm_mutant = self._load_mutant(
            'if entry["source"] == source',
            'if entry["source"] in {source, "original", "semantic"}',
        )
        wrong_arm_record = {
            "cell": "arm",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "E_CONN_RESET",
                "annotations": [
                    {"span": "E_CONN_RESET", "rule_id": "EVS-BBBBBBBB-01"}
                ],
            },
        }

        def assert_wrong_arm_rejected(module) -> None:
            checked = module.validate_response(
                wrong_arm_record, self._case(), self._map()
            )
            self.assertFalse(checked["claims"][0]["structurally_valid"])

        assert_wrong_arm_rejected(pilot)
        with self.assertRaises(AssertionError):
            assert_wrong_arm_rejected(arm_mutant)

    def _map(self) -> dict:
        return {
            "entries": [
                {
                    "id": "EVO-AAAAAAAA-01",
                    "key": "terse-auth-example",
                    "source": "original",
                    "lexical_any": ["Token expiry"],
                },
                {
                    "id": "EVS-BBBBBBBB-01",
                    "key": "substance-exactness",
                    "source": "semantic",
                    "assessment": "exact-preservation",
                },
            ]
        }

    def _case(self) -> dict:
        return {
            "id": "case",
            "eligible_keys": ["terse-auth-example", "substance-exactness"],
            "required_exact": ["E_CONN_RESET"],
        }

    # Positive control: a known arm-specific ID plus one exact unique span can
    # pass a literal lexical probe without becoming a semantic verdict.
    def test_valid_lexical_overlap_remains_semantically_unassessed(self) -> None:
        record = {
            "cell": "x",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "Token expiry check rejects E_CONN_RESET.",
                "annotations": [
                    {"span": "Token expiry check", "rule_id": "EVO-AAAAAAAA-01"}
                ],
            },
        }
        checked = pilot.validate_response(record, self._case(), self._map())
        claim = checked["claims"][0]
        self.assertTrue(claim["structurally_valid"])
        self.assertEqual(claim["literal_lexical_probe"], "pass")
        self.assertEqual(claim["independent_semantic_assessment"], "needs-review")
        self.assertEqual(claim["provenance"], "unsupported model self-report")

    # Proves semantic exactness cannot self-pass on a case with no independently
    # predeclared exact artifact.
    def test_semantic_exactness_requires_independent_artifact(self) -> None:
        result, reason = pilot.observable_probe(
            "exact-preservation",
            "A technically plausible answer.",
            "plausible answer",
            {"required_exact": []},
        )
        self.assertEqual(result, "fail")
        self.assertIn("no predeclared exact artifact", reason)

    # Proves broad lexical and whole-answer probes stay diagnostics even when
    # they pass on contradictory or nonsensical content.
    def test_probe_passes_never_become_semantic_attribution(self) -> None:
        lexical = {
            "cell": "lexical",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "Token expiry is irrelevant to this failure.",
                "annotations": [
                    {"span": "Token expiry", "rule_id": "EVO-AAAAAAAA-01"}
                ],
            },
        }
        claim = pilot.validate_response(lexical, self._case(), self._map())["claims"][0]
        self.assertEqual(claim["literal_lexical_probe"], "pass")
        self.assertEqual(claim["independent_semantic_assessment"], "needs-review")

        semantic_map = {
            "entries": [
                {
                    "id": "EVS-BBBBBBBB-02",
                    "key": "no-caricature",
                    "source": "semantic",
                    "assessment": "no-caricature",
                },
                {
                    "id": "EVS-BBBBBBBB-03",
                    "key": "artifact-boundary",
                    "source": "semantic",
                    "assessment": "normal-prose-artifact",
                },
            ]
        }
        for answer, span, rule_id, key, case in (
            (
                "The database is purple.",
                "database",
                "EVS-BBBBBBBB-02",
                "no-caricature",
                {"eligible_keys": ["no-caricature"], "required_exact": []},
            ),
            (
                "The migration deletes the backup. A user loses the data.",
                "migration deletes",
                "EVS-BBBBBBBB-03",
                "artifact-boundary",
                {
                    "eligible_keys": ["artifact-boundary"],
                    "required_exact": [],
                    "normal_prose": True,
                },
            ),
        ):
            record = {
                "cell": key,
                "arm": "semantic-instrumented",
                "status": "success",
                "response": {
                    "answer": answer,
                    "annotations": [{"span": span, "rule_id": rule_id}],
                },
            }
            claim = pilot.validate_response(record, case, semantic_map)["claims"][0]
            self.assertEqual(claim["observable_probe"], "pass")
            self.assertEqual(
                claim["independent_semantic_assessment"], "needs-review"
            )

    # Negative controls prove the checker rejects unknown IDs, wrong spans,
    # ambiguous spans, and a planted known-ID trace lacking lexical agreement.
    def test_checker_rejects_incorrect_traces(self) -> None:
        annotations = [
            {"span": "unique", "rule_id": "UNKNOWN"},
            {"span": "missing", "rule_id": "EVO-AAAAAAAA-01"},
            {"span": "repeat", "rule_id": "EVO-AAAAAAAA-01"},
            {"span": "unique", "rule_id": "EVO-AAAAAAAA-01"},
        ]
        record = {
            "cell": "x",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "unique repeat repeat E_CONN_RESET",
                "annotations": annotations,
            },
        }
        checked = pilot.validate_response(record, self._case(), self._map())
        self.assertEqual(
            [c["structurally_valid"] for c in checked["claims"]],
            [False, False, False, True],
        )
        self.assertEqual(checked["claims"][3]["literal_lexical_probe"], "fail")
        self.assertIn("unknown arm-specific ID", checked["claims"][0]["reason"])
        self.assertIn("match count is 0", checked["claims"][1]["reason"])
        self.assertIn("match count is 2", checked["claims"][2]["reason"])
        self.assertIn("no predeclared lexical cue", checked["claims"][3]["reason"])

    # Proves malformed envelopes and forbidden clean-arm annotations remain
    # visible as invalid evidence rather than being silently normalized.
    def test_malformed_and_clean_arm_annotations_are_rejected(self) -> None:
        with self.assertRaisesRegex(pilot.PilotError, "CLI output is not JSON"):
            pilot.parse_cli_output("not-json")
        with self.assertRaisesRegex(pilot.PilotError, "no structured_output"):
            pilot.parse_cli_output('{"result": 42}')

        malformed = {
            "cell": "m",
            "arm": "terse-control",
            "status": "success",
            "response": {
                "answer": "ok",
                "annotations": "not-an-array",
                "unexpected": True,
            },
        }
        checked = pilot.validate_response(malformed, self._case(), self._map())
        self.assertFalse(checked["envelope_valid"])
        self.assertIn("annotations must be an array", checked["envelope_errors"])
        self.assertIn(
            "response has unknown keys: unexpected", checked["envelope_errors"]
        )

        malformed_claim = {
            "cell": "claim",
            "arm": "original-instrumented",
            "status": "success",
            "response": {
                "answer": "Token expiry",
                "annotations": [
                    {
                        "span": "Token expiry",
                        "rule_id": "EVO-AAAAAAAA-01",
                        "extra": True,
                    }
                ],
            },
        }
        checked = pilot.validate_response(
            malformed_claim, self._case(), self._map()
        )
        self.assertFalse(checked["envelope_valid"])
        self.assertIn(
            "annotation 0 has unknown keys: extra", checked["envelope_errors"]
        )

        contaminated = {
            "cell": "c",
            "arm": "terse-control",
            "status": "success",
            "response": {
                "answer": "unique E_CONN_RESET",
                "annotations": [{"span": "unique", "rule_id": "EVO-AAAAAAAA-01"}],
            },
        }
        checked = pilot.validate_response(contaminated, self._case(), self._map())
        self.assertFalse(checked["envelope_valid"])
        self.assertIn(
            "clean/control arm returned forbidden annotations",
            checked["envelope_errors"],
        )
        self.assertFalse(checked["claims"][0]["structurally_valid"])

    # Proves the frozen design contains the required 5 × 8 × 2 complete matrix
    # and deterministic randomization.
    def test_design_freezes_complete_deterministic_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = pilot.freeze_design(Path(first), 260916, 2)
            two = pilot.freeze_design(Path(second), 260916, 2)
        self.assertEqual(one["scheduled_cells"], 80)
        self.assertEqual(one["schedule"], two["schedule"])
        self.assertEqual(set(row["arm"] for row in one["schedule"]), set(pilot.ARMS))

    # Proves normal analysis fails closed on missing, duplicate, unexpected, or
    # inconsistent cells; diagnostic partial mode is explicitly ineligible.
    def test_aggregate_enforces_exact_matrix_multiset_and_identity(self) -> None:
        case = {"id": "exact-preservation", "eligible_keys": [], "required_exact": []}
        design = {
            "cases": [case],
            "schedule": [
                {
                    "repetition": 1,
                    "case_id": "exact-preservation",
                    "arm": "terse-control",
                },
                {
                    "repetition": 2,
                    "case_id": "exact-preservation",
                    "arm": "terse-control",
                },
            ],
            "combined_intervention_limitation": "combined",
            "claim_limit": "claim",
        }
        record = {
            "cell": "r1-exact-preservation-terse-control",
            "arm": "terse-control",
            "case_id": "exact-preservation",
            "repetition": 1,
            "requested_model": "model",
            "status": "success",
            "response": {"answer": "ok", "annotations": []},
            "attempts": [],
        }
        with self.assertRaisesRegex(pilot.PilotError, "matrix mismatch"):
            pilot.aggregate([record], design, {"entries": []})
        partial = pilot.aggregate(
            [record], design, {"entries": []}, strict_matrix=False
        )
        self.assertFalse(partial["publication_eligible_matrix"])
        self.assertEqual(partial["matrix"]["expected_records"], 2)
        self.assertEqual(len(partial["matrix"]["missing"]), 1)
        self.assertEqual(partial["arms"]["terse-control"]["scheduled"], 2)
        self.assertEqual(partial["arms"]["terse-control"]["observed"], 1)

        duplicate = [record, dict(record)]
        with self.assertRaisesRegex(pilot.PilotError, "duplicates=1"):
            pilot.aggregate(duplicate, design, {"entries": []})

        unexpected = dict(record, repetition=99, cell="r99-exact-preservation-terse-control")
        with self.assertRaisesRegex(pilot.PilotError, "unexpected=1"):
            pilot.aggregate([record, unexpected], design, {"entries": []})

        inconsistent = dict(record, cell="wrong-cell")
        with self.assertRaisesRegex(pilot.PilotError, "inconsistent=1"):
            pilot.aggregate([inconsistent], design, {"entries": []})

    # Proves the normal analyze CLI returns nonzero for an incomplete matrix;
    # callers must opt into separately labeled diagnostic partial output.
    def test_analyze_cli_returns_nonzero_for_incomplete_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            design = {
                "cases": [
                    {
                        "id": "exact-preservation",
                        "eligible_keys": [],
                        "required_exact": [],
                    }
                ],
                "schedule": [
                    {
                        "repetition": 1,
                        "case_id": "exact-preservation",
                        "arm": "terse-control",
                    }
                ],
                "combined_intervention_limitation": "combined",
                "claim_limit": "claim",
            }
            (output / "design-freeze.json").write_text(json.dumps(design))
            (output / "source-map.json").write_text('{"entries": []}')
            (output / "results.json").write_text("[]")
            argv = ["attribution_pilot.py", "analyze", "--output", directory]
            with mock.patch.object(pilot.os.sys, "argv", argv), mock.patch.object(
                pilot.os.sys, "stderr", io.StringIO()
            ):
                self.assertEqual(pilot.main(), 1)
            self.assertFalse((output / "aggregate.json").exists())

    # Proves provider success and strict response validity have separate totals.
    def test_aggregate_excludes_invalid_envelope_from_valid_responses(self) -> None:
        case = {"id": "exact-preservation", "eligible_keys": [], "required_exact": []}
        design = {
            "cases": [case],
            "schedule": [
                {
                    "repetition": 1,
                    "case_id": "exact-preservation",
                    "arm": "terse-control",
                }
            ],
            "combined_intervention_limitation": "combined",
            "claim_limit": "claim",
        }
        record = {
            "cell": "r1-exact-preservation-terse-control",
            "arm": "terse-control",
            "case_id": "exact-preservation",
            "repetition": 1,
            "requested_model": "model",
            "status": "success",
            "response": {"answer": 7, "annotations": []},
            "attempts": [],
        }
        arm = pilot.aggregate([record], design, {"entries": []})["arms"][
            "terse-control"
        ]
        self.assertEqual(arm["transport_success"], 1)
        self.assertEqual(arm["valid_responses"], 0)
        self.assertEqual(arm["invalid_envelopes"], 1)

    # Proves subprocess failures are retained through the initial attempt plus
    # three bounded retries, and no failed attempt becomes a fake response.
    @mock.patch.object(pilot.time, "sleep")
    @mock.patch.object(pilot.subprocess, "run")
    def test_failed_subprocess_retains_all_attempts(self, run: mock.Mock, _: mock.Mock) -> None:
        run.return_value = subprocess.CompletedProcess([], 1, "", "provider unavailable")
        with tempfile.TemporaryDirectory() as directory:
            record = pilot.run_one(
                arm="terse-control",
                case={"id": "x", "prompt": "hello"},
                repetition=1,
                model="explicit-model",
                system="system",
                timeout=1,
                raw_dir=Path(directory),
            )
            saved = json.loads((Path(directory) / "r1-x-terse-control.json").read_text())
        self.assertEqual(record["status"], "failed")
        self.assertEqual(len(record["attempts"]), 4)
        self.assertEqual(saved["attempts"][-1]["stderr"], "provider unavailable")

    # Proves isolation arguments disable settings, plugins/MCP customization,
    # tools, and persistence, while sensitive environment values are never
    # serialized into the command.
    def test_command_and_environment_apply_contamination_controls(self) -> None:
        command = pilot.claude_command("model", "system", "prompt")
        joined = " ".join(command)
        for flag in (
            "--safe-mode",
            "--restricted",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--setting-sources",
            "--tools",
            "--system-prompt",
            "--model",
        ):
            self.assertIn(flag, command)
        self.assertNotIn("ANTHROPIC_API_KEY", joined)
        with mock.patch.dict(pilot.os.environ, {"CLAUDE_CONFIG_DIR": "/secret"}):
            self.assertNotIn("CLAUDE_CONFIG_DIR", pilot.sanitized_environment())

    # Proves provider errors retain useful context without persisting common
    # API-key, bearer-token, or password forms.
    def test_error_sanitizer_redacts_credentials(self) -> None:
        error = "api_key=secret Authorization: Bearer abc123 password: hunter2"
        sanitized = pilot.sanitize_error(error)
        self.assertNotIn("secret", sanitized)
        self.assertNotIn("abc123", sanitized)
        self.assertNotIn("hunter2", sanitized)
        self.assertEqual(sanitized.count("<redacted>"), 3)


if __name__ == "__main__":
    unittest.main()
