"""Focused controls for the v2 source-aware response-segment diagnostic."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "attribution_v2", ROOT / "evals" / "attribution_v2.py"
)
assert SPEC and SPEC.loader
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)


class AttributionV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.source_map = v2.prepare_sources(cls.output)
        cls.protocol = v2.read_object(v2.PROTOCOL_PATH)
        cls.cases = {case["id"]: case for case in v2.load_cases()}
        cls.entries = {entry["key"]: entry for entry in cls.source_map["entries"]}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def record(self, arm: str, case_id: str, segments: list[dict]) -> dict:
        return {
            "cell": f"haiku--r1-{case_id}-{arm}",
            "model_label": "haiku",
            "requested_model": "claude-haiku-4-5-20251001",
            "arm": arm,
            "case_id": case_id,
            "repetition": 1,
            "status": "transport-success",
            "response": {"segments": segments},
        }

    def check(self, arm: str, case_id: str, segments: list[dict]) -> dict:
        return v2.validate_record(
            self.record(arm, case_id, segments),
            self.cases[case_id],
            self.source_map,
            self.protocol,
        )

    def link(self, key: str, relation: str = "rule-compatible") -> dict:
        entry = self.entries[key]
        return {
            "rule_id": entry["id"],
            "relation": relation,
            "source_quote": entry["exact_original_snippet"],
        }

    # Proves final answer bytes come only from ordered segment text and an ordinary
    # answer can explicitly abstain; it does not assess semantic quality.
    def test_segments_concatenate_exactly_and_unlinked_answer_is_valid(self) -> None:
        check = self.check(
            "semantic-tagged",
            "ordinary-unlinked",
            [{"text": "17 × ", "links": []}, {"text": "19 = 323", "links": []}],
        )
        self.assertEqual(check["answer"], "17 × 19 = 323")
        self.assertTrue(check["response_valid"])
        self.assertTrue(check["abstained"])
        self.assertTrue(check["answer_invariants"]["passed"])

    # Proves malformed/empty segments are rejected rather than silently repaired.
    def test_malformed_segment_schema_is_rejected(self) -> None:
        self.assertTrue(v2.validate_envelope({"segments": [{"text": "", "links": []}]}))
        self.assertTrue(
            v2.validate_envelope(
                {"segments": [{"text": "ok", "links": [], "claim": "extra"}]}
            )
        )

    # Proves unknown IDs, IDs from the other arm, and inexact source quotes each
    # fail metadata validation while leaving answer checks independently visible.
    def test_invalid_unknown_cross_arm_and_quote_links_are_rejected(self) -> None:
        text = "17 × 19 = 323"
        unknown = {"rule_id": "NOPE", "relation": "uncertain", "source_quote": "x"}
        wrong_arm = self.link("react-full-example", "uncertain")
        wrong_quote = self.link("substance-exactness", "uncertain")
        wrong_quote["source_quote"] += " altered"
        for link, expected in (
            (unknown, "unknown ID"),
            (wrong_arm, "cross-arm ID"),
            (wrong_quote, "incorrect source quote"),
        ):
            with self.subTest(expected=expected):
                check = self.check(
                    "semantic-tagged",
                    "ordinary-unlinked",
                    [{"text": text, "links": [link]}],
                )
                self.assertFalse(check["metadata_valid"])
                self.assertTrue(any(expected in item for item in check["metadata_errors"]))
                self.assertTrue(check["answer_invariants"]["passed"])

    # Proves controls and clean arms cannot emit attribution metadata.
    def test_clean_arm_rejects_returned_link(self) -> None:
        check = self.check(
            "semantic-clean",
            "ordinary-unlinked",
            [{"text": "17 × 19 = 323", "links": [self.link("substance-exactness")]}],
        )
        self.assertIn("clean/control response returned forbidden links", check["metadata_errors"])

    # Positive control: the distinctive React phrase overlaps both source and
    # segment. This proves a literal property only, not causal provenance.
    def test_distinctive_literal_overlap_is_confirmed(self) -> None:
        check = self.check(
            "original-tagged",
            "original-react-example",
            [
                {
                    "text": "An inline object prop creates a New object ref. useMemo fixes it.",
                    "links": [self.link("react-full-example", "literal-overlap")],
                }
            ],
        )
        self.assertEqual(check["links"][0]["relationship_status"], "literal-overlap-confirmed")

    # Deceptive control: a known, exactly quoted source can still be unrelated to
    # the case; identifier and quote validity must not imply applicability.
    def test_applicability_prior_is_neutral_observation(self) -> None:
        check = self.check(
            "original-tagged",
            "ordinary-unlinked",
            [{"text": "17 × 19 = 323", "links": [self.link("react-full-example")]}],
        )
        self.assertEqual(check["links"][0]["relationship_status"], "rule-compatible-unassessed")
        self.assertEqual(check["links"][0]["applicability_observation"], "outside-predeclared-applicability")

    # Deceptive control: copying a real source quote into an unrelated answer does
    # not make the relationship applicable and independently damages answer quality.
    def test_real_source_quote_in_unrelated_output_is_not_promoted(self) -> None:
        entry = self.entries["react-full-example"]
        check = self.check(
            "original-tagged",
            "ordinary-unlinked",
            [{"text": entry["exact_original_snippet"], "links": [self.link("react-full-example", "literal-overlap")]}],
        )
        self.assertEqual(check["links"][0]["relationship_status"], "literal-overlap-confirmed")
        self.assertEqual(check["links"][0]["applicability_observation"], "outside-predeclared-applicability")
        self.assertFalse(check["answer_invariants"]["passed"])
        self.assertIn(entry["id"], check["extraneous_source_copies"])

    # Proves a negation flip is audited even when the model returns no links.
    def test_negation_flip_fails_answer_invariant_without_links(self) -> None:
        answer = (
            "At /srv/app/config.yaml, E_CONN_RESET on v2.4.1 after 250 ms "
            "means the client must retry."
        )
        check = self.check(
            "semantic-tagged", "exact-negation-artifacts", [{"text": answer, "links": []}]
        )
        self.assertTrue(check["abstained"])
        self.assertFalse(check["answer_invariants"]["passed"])
        self.assertIn("must not retry", check["answer_invariants"]["missing_required_exact"])

    # Proves copied instruction text is an answer-quality violation even with no
    # attribution claim, keeping answer and metadata checks separate.
    def test_unlinked_source_rule_copy_is_audited(self) -> None:
        entry = self.entries["artifact-boundary"]
        check = self.check(
            "semantic-tagged",
            "normal-prose-artifact",
            [{"text": entry["exact_original_snippet"], "links": []}],
        )
        self.assertTrue(check["metadata_valid"])
        self.assertFalse(check["answer_invariants"]["passed"])
        self.assertEqual(check["extraneous_source_copies"], [entry["id"]])

    # Proves semantic compatibility remains explicitly unassessed and uncertainty
    # is retained as uncertainty rather than converted into a positive label.
    def test_rule_compatibility_unassessed_and_uncertainty_preserved(self) -> None:
        text = "17 × 19 = 323"
        semantic = self.check(
            "semantic-tagged",
            "ordinary-unlinked",
            [{"text": text, "links": [self.link("substance-exactness")]}],
        )
        uncertain = self.check(
            "semantic-tagged",
            "ordinary-unlinked",
            [{"text": text, "links": [self.link("substance-exactness", "uncertain")]}],
        )
        self.assertEqual(semantic["links"][0]["relationship_status"], "rule-compatible-unassessed")
        self.assertEqual(semantic["links"][0]["applicability_observation"], "outside-predeclared-applicability")
        self.assertEqual(uncertain["links"][0]["relationship_status"], "uncertain")
        self.assertEqual(uncertain["links"][0]["independent_semantic_review"], "not-performed")
        self.assertIn("independent_answer_checks", uncertain["links"][0])

    # Proves punctuation counts alert without becoming grounded truth.
    def test_sentence_count_is_only_a_heuristic_alert(self) -> None:
        case = self.cases["novel-cache-paraphrase"]
        answer = "A cache stampede is dogpile (a.k.a. stampeding herd). request coalescing avoids it."
        self.assertTrue(v2.answer_invariants(answer, case)["passed"])
        self.assertEqual(v2.heuristic_answer_alerts(answer, case)[0]["kind"], "punctuation-sentence-count")

    # Proves grammatical article-less prose is a grounded positive control.
    def test_article_less_professional_prose_is_grounded_positive(self) -> None:
        case = self.cases["normal-prose-artifact"]
        answer = "Before migration, backup completes. After failure, users can restore data."
        self.assertTrue(v2.answer_invariants(answer, case)["passed"])
        self.assertEqual(v2.heuristic_answer_alerts(answer, case)[0]["kind"], "english-article-absence")

    # Proves segment joining whitespace is reported as a distinct output defect.
    def test_joining_whitespace_defect_is_separate(self) -> None:
        defects = v2.joining_whitespace_defects(
            [{"text": "First sentence."}, {"text": "Second sentence."}]
        )
        self.assertEqual(len(defects), 1)

    # Proves incomplete, duplicated, wrong-model, and cell-corrupted matrices fail
    # closed; the positive record demonstrates the checker is not reject-all.
    def test_matrix_audit_detects_corruption(self) -> None:
        row = {
            "model_label": "haiku",
            "model_id": "pinned",
            "repetition": 1,
            "case_id": "ordinary-unlinked",
            "arm": "terse-control",
        }
        design = {"schedule": [row]}
        good = {
            "cell": v2.expected_cell(row),
            "model_label": "haiku",
            "requested_model": "pinned",
            "repetition": 1,
            "case_id": "ordinary-unlinked",
            "arm": "terse-control",
        }
        self.assertTrue(v2.matrix_audit([good], design)["valid"])
        self.assertFalse(v2.matrix_audit([], design)["valid"])
        self.assertFalse(v2.matrix_audit([good, good], design)["valid"])
        self.assertFalse(v2.matrix_audit([{**good, "requested_model": "wrong"}], design)["valid"])
        self.assertFalse(v2.matrix_audit([{**good, "cell": "corrupt"}], design)["valid"])

    # Proves the frozen design is the requested 2×2×6×5 matrix and that clean
    # model inputs require empty links without mutating the v1 evidence directory.
    def test_freeze_design_has_120_randomized_cells(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            source_map = v2.prepare_sources(output)
            identity = output / "identity.json"
            v2.write_json(identity, {"exposed_model_identity": "claude-sonnet-test"})
            args = type(
                "Args",
                (),
                {
                    "output": output,
                    "stronger_identity": identity,
                    "haiku_model": "claude-haiku-test",
                    "seed": 7,
                },
            )()
            with mock.patch.object(v2, "claude_version", return_value="test-cli"):
                design = v2.freeze_design(args)
            self.assertEqual(design["scheduled_cells"], 120)
            self.assertEqual(len({v2.expected_cell(row) for row in design["schedule"]}), 120)
            clean_input = (output / "inputs" / "original-clean.system.txt").read_text()
            self.assertIn("Every `links` array must be empty", clean_input)
            self.assertEqual(source_map["entries"], v2.read_object(output / "source-map.json")["entries"])

    # Proves a multi-model CLI usage record selects the requested stronger family,
    # not a longer auxiliary Haiku identity used internally by the CLI.
    def test_exposed_identity_selects_requested_model_family(self) -> None:
        record = {
            "model_usage": {
                "claude-haiku-4-5-20251001": {"canonicalModel": "claude-haiku-4-5"},
                "claude-sonnet-5": {"canonicalModel": "claude-sonnet-5"},
            }
        }
        self.assertEqual(v2.exposed_model_identity(record, "sonnet"), "claude-sonnet-5")

    # Proves transient failures retain every attempt and retry three times after
    # the initial call; the fourth response is the positive control.
    def test_run_one_retains_failed_attempts_before_success(self) -> None:
        success = json.dumps(
            {
                "structured_output": {"segments": [{"text": "17 × 19 = 323", "links": []}]},
                "usage": {"output_tokens": 5},
                "modelUsage": {"claude-haiku-test": {"provider": "anthropic"}},
            }
        )
        failures = [
            mock.Mock(returncode=1, stdout="", stderr="token=secret-value")
            for _ in range(3)
        ]
        ok = mock.Mock(returncode=0, stdout=success, stderr="")
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            v2.subprocess, "run", side_effect=[*failures, ok]
        ), mock.patch.object(v2.time, "sleep"):
            result = v2.run_one(
                model_label="haiku",
                model_id="claude-haiku-test",
                arm="terse-control",
                case=self.cases["ordinary-unlinked"],
                repetition=1,
                system="system",
                timeout=1,
                raw_dir=Path(directory),
            )
        self.assertEqual(result["status"], "transport-success")
        self.assertEqual(len(result["attempts"]), 4)
        self.assertIn("<redacted>", result["attempts"][0]["stderr"])

    # Proves an invalid source quote cannot erase an independent answer failure
    # from aggregate denominators; envelope and metadata quality stay separate.
    def test_aggregate_counts_answer_violation_despite_invalid_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            v2.write_json(output / "source-map.json", self.source_map)
            row = {
                "model_label": "haiku",
                "model_id": "pinned",
                "repetition": 1,
                "case_id": "exact-negation-artifacts",
                "arm": "semantic-tagged",
            }
            design = {
                "models": {"haiku": "pinned"},
                "schedule": [row],
                "cases": [self.cases["exact-negation-artifacts"]],
                "limits": [],
            }
            v2.write_json(output / "design-freeze.json", design)
            bad_quote = self.link("substance-exactness")
            bad_quote["source_quote"] = "truncated"
            record = {
                **self.record(
                    "semantic-tagged",
                    "exact-negation-artifacts",
                    [{"text": "must retry.", "links": [bad_quote]}],
                ),
                "requested_model": "pinned",
                "attempts": [],
            }
            v2.write_json(output / "results.json", [record])
            aggregate = v2.analyze(output)
            metrics = aggregate["metrics"]["haiku"]["semantic-tagged"]
            self.assertEqual(metrics["well_formed_envelopes"], 1)
            self.assertEqual(metrics["metadata_invalid_responses"], 1)
            self.assertEqual(metrics["grounded_answer_violation_responses"], 1)
            self.assertEqual(metrics["returned_links_response_denominator"], 1)
            self.assertEqual(metrics["returned_links"], 1)
            self.assertEqual(metrics["individually_metadata_valid_links"], 0)
            self.assertEqual(metrics["links_in_metadata_valid_responses"], 0)

    # Proves length deltas use identical reconstructable case/repetition members,
    # including tagged answers whose link metadata is invalid.
    def test_matched_length_comparison_keeps_invalid_metadata_answer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            v2.write_json(output / "source-map.json", self.source_map)
            rows = [
                {
                    "model_label": "haiku",
                    "model_id": "pinned",
                    "repetition": 1,
                    "case_id": "ordinary-unlinked",
                    "arm": arm,
                }
                for arm in ("semantic-clean", "semantic-tagged")
            ]
            design = {
                "models": {"haiku": "pinned"},
                "schedule": rows,
                "cases": [self.cases["ordinary-unlinked"]],
                "limits": [],
            }
            v2.write_json(output / "design-freeze.json", design)
            clean = {
                **self.record(
                    "semantic-clean",
                    "ordinary-unlinked",
                    [{"text": "17 × 19 = 323", "links": []}],
                ),
                "requested_model": "pinned",
                "attempts": [],
                "usage": {"output_tokens": 5},
            }
            bad_quote = self.link("substance-exactness")
            bad_quote["source_quote"] = "truncated"
            tagged = {
                **self.record(
                    "semantic-tagged",
                    "ordinary-unlinked",
                    [{"text": "17 × 19 = 323", "links": [bad_quote]}],
                ),
                "requested_model": "pinned",
                "attempts": [],
                "usage": {"output_tokens": 7},
            }
            v2.write_json(output / "results.json", [clean, tagged])
            comparison = v2.analyze(output)["within_model_clean_vs_tagged"]["haiku"]["semantic"]
            self.assertEqual(comparison["matched_reconstructable_pairs"], 1)
            self.assertEqual(comparison["expected_pairs"], 1)
            self.assertEqual(comparison["answer_char_delta"], 0)
            self.assertEqual(comparison["cli_output_token_delta"], 2)

    # Proves the bounded calibration detects planted false positives/negatives,
    # keeps insufficient evidence separate, and defeats trivial detectors.
    def test_offline_fp_fn_calibration_and_trivial_controls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            v2.write_json(output / "source-map.json", self.source_map)
            result = v2.run_calibration(output)
        structural = result["structural"]
        self.assertEqual(structural["false_accepts"], 0)
        self.assertEqual(structural["false_rejects"], 0)
        self.assertEqual(structural["expected_accept_denominator"], 2)
        self.assertEqual(structural["expected_reject_denominator"], 4)
        observed = result["observable"]["declared_emissions"]
        self.assertEqual(observed["true_positive"], 2)
        self.assertEqual(observed["false_positive"], 3)
        self.assertEqual(observed["true_negative"], 2)
        self.assertEqual(observed["false_negative"], 2)
        self.assertEqual(observed["insufficient_evidence"], 1)
        self.assertEqual(result["observable"]["observer_expected_label_mismatches"], 0)
        self.assertFalse(result["observable"]["always_positive_control"]["passes_perfect_fixture_gate"])
        empty = result["observable"]["always_empty_control"]
        self.assertIsNone(empty["precision"]["value"])
        self.assertEqual(empty["recall"]["value"], 0.0)
        self.assertFalse(empty["passes_perfect_fixture_gate"])
        self.assertIsNone(result["live_data"]["numeric_false_positive_rate"])

    # Proves identical output changes judgment only with explicit task context;
    # the observer does not consume the expected label.
    def test_calibration_paired_context_observer(self) -> None:
        spec = v2.read_object(v2.CALIBRATION_PATH)
        fixtures = {row["id"]: row for row in spec["observable_fixtures"]}
        for positive, negative in (
            ("polarity-pair-positive", "polarity-pair-negative"),
            ("language-pair-positive", "language-pair-negative"),
        ):
            self.assertEqual(fixtures[positive]["segment_text"], fixtures[negative]["segment_text"])
            positive_result = v2.observe_declared_fixture_property(
                fixtures[positive], self.entries[fixtures[positive]["source_key"]]
            )
            negative_result = v2.observe_declared_fixture_property(
                fixtures[negative], self.entries[fixtures[negative]["source_key"]]
            )
            self.assertEqual(positive_result["judgment"], "compatible")
            self.assertEqual(negative_result["judgment"], "contradicted")

    # Proves immutable independent judgments join by stable claim identity and
    # remain explicitly model-review evidence rather than automatic truth.
    def test_independent_review_integration_requires_exact_link_coverage(self) -> None:
        check = self.check(
            "semantic-tagged",
            "ordinary-unlinked",
            [{"text": "17 × 19 = 323", "links": [self.link("substance-exactness")]}],
        )
        claim_id = check["links"][0]["claim_id"]
        review = {
            "coverage": {"returned_link_judgment_counts": {"compatible": 1}},
            "emitted_link_assessments": [
                {"claim_id": claim_id, "judgment": "compatible", "rationale": "Exact required arithmetic preserved."}
            ],
            "observable_omissions": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            v2.write_json(path, review)
            summary, _ = v2.integrate_independent_review([check], path)
        self.assertEqual(summary["judgment_counts"], {"compatible": 1})
        self.assertIsNone(summary["live_precision"])
        self.assertEqual(
            check["links"][0]["independent_model_review"]["authority"],
            "independent model review; not human ground truth",
        )

    # Proves the review packet includes link-free tagged segments and every
    # arm-specific candidate source rather than selecting favorable emissions.
    def test_all_tagged_segment_packet_covers_unlinked_candidates(self) -> None:
        record = self.record(
            "original-tagged",
            "ordinary-unlinked",
            [{"text": "17 × 19 = 323", "links": []}],
        )
        check = v2.validate_record(
            record,
            self.cases["ordinary-unlinked"],
            self.source_map,
            self.protocol,
        )
        with tempfile.TemporaryDirectory() as directory:
            packet = v2.write_all_tagged_segments_audit(
                Path(directory), [record], [check], self.source_map
            )
        self.assertEqual(packet["tagged_response_count"], 1)
        self.assertEqual(packet["tagged_segment_count"], 1)
        row = packet["segments"][0]
        self.assertEqual(row["emitted_links"], [])
        self.assertEqual(
            len(row["candidate_sources"]),
            len(v2.source_entries(self.source_map, "original")),
        )
        self.assertTrue(all(not item["emitted"] for item in row["candidate_sources"]))


if __name__ == "__main__":
    unittest.main()
