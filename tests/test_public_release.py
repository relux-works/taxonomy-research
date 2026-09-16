from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pilot = load("pilot_public", ROOT / "evals/attribution_pilot.py")
gate = load("public_gate", ROOT / "tools/check_public_release.py")
exporter = load("public_export", ROOT / "tools/export_public.py")


def copy_public_candidate(destination: Path) -> None:
    destination.mkdir()
    for source in gate.candidate_files(ROOT):
        relative = source.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


class PublicReleaseTests(unittest.TestCase):
    # Proves vendored snapshot tampering is rejected before fixture generation.
    def test_prepare_rejects_bad_pinned_hash_fixture(self) -> None:
        bad = ROOT / "fixtures/negative/current-bad-hash.md"
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            pilot, "CURRENT_SOURCE", bad
        ):
            with self.assertRaisesRegex(pilot.PilotError, "current snapshot hash mismatch"):
                pilot.prepare_fixtures(Path(directory))

    # Proves the checked-in duplicate-anchor fixture is refused as ambiguous.
    def test_ambiguous_anchor_fixture_is_rejected(self) -> None:
        value = (ROOT / "fixtures/negative/ambiguous-anchor.md").read_text()
        with self.assertRaisesRegex(pilot.PilotError, "anchor match count 2"):
            pilot.instrument_source(
                value,
                "original",
                [{"key": "negative", "category": "control", "anchor": "duplicate-anchor"}],
                "fixture",
                "0" * 64,
            )

    # Proves the real release entry point detects a planted local-path leak.
    def test_release_gate_known_violation_control(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "candidate"
            copy_public_candidate(copy)
            leaked = copy / "artifacts" / "KNOWN-violation.json"
            planted_path = "/" + "Users/private/source.txt"
            leaked.write_text(json.dumps({"source": planted_path}) + "\n")
            agent_file = copy / ("AGENTS" + ".private.md")
            agent_file.write_text("planted agent instruction\n")
            errors = gate.check(copy)
            self.assertTrue(any("absolute local path" in error for error in errors))
            self.assertTrue(any("forbidden release path" in error for error in errors))

    # Proves semantic JSON inspection catches an escaped key while the searched
    # token still exists harmlessly elsewhere; this defeats a static-token-only gate.
    def test_wrapper_gate_kills_token_preserving_behavior_mutant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "candidate"
            copy_public_candidate(copy)
            planted = copy / "artifacts" / "KNOWN-wrapper.json"
            planted.write_text('{"note":"stdout token retained","st\\u0064out":"wrapper"}\n')
            errors = gate.check(copy)
            self.assertTrue(any("provider wrapper field" in error for error in errors))

    # Proves an extra provider-wrapper field cannot enter a public projection.
    def test_projection_allowlist_rejects_narrowing_bypass(self) -> None:
        manifest = json.loads((ROOT / "artifacts/projection-manifest.json").read_text())
        entry = dict(manifest["exports"][0])
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "results.json"
            rows = json.loads((ROOT / entry["projection_path"]).read_text())
            rows[0]["stdout"] = "planted wrapper"
            copy.write_text(json.dumps(rows))
            entry["projection_path"] = copy.name
            entry["projection_sha256"] = gate.sha256(copy)
            errors = gate.validate_projection(copy.parent, entry, manifest["allowed"])
            self.assertTrue(any("forbidden top-level" in error for error in errors))

    # Proves raw content is hashed before a projector can corrupt it.
    def test_corrupting_projector_is_rejected(self) -> None:
        raw = [{"cell": "c1", "status": "failed", "response": {"error": "invalid"}}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path = root / "raw.json"
            output = root / "artifacts/v1/results.public.json"
            raw_path.write_text(json.dumps(raw))

            def corrupt(records):
                projected = [exporter.project_record(row) for row in records]
                projected[0]["status"] = "success"
                return projected

            with mock.patch.object(exporter, "project_records", side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, "projector changed"):
                    exporter.write_projection(raw_path, output, "control")
            self.assertFalse(output.exists())

    # Proves failed/invalid rows are retained rather than filtered by projection.
    def test_projection_preserves_failed_and_invalid_rows(self) -> None:
        raw = [
            {"cell": "valid", "status": "success", "response": {"answer": "ok"}},
            {"cell": "failed", "status": "failed", "response": {"error": "invalid"}},
        ]
        projected = exporter.project_records(raw)
        self.assertEqual(exporter.content_view(projected), exporter.content_view(raw))
        self.assertEqual([row["status"] for row in projected], ["success", "failed"])

    # Proves known credential paths and high-confidence credential material are
    # rejected without including credential values in diagnostics.
    def test_release_gate_rejects_credentials_without_echoing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "candidate"
            copy_public_candidate(copy)
            credential_dir = copy / "nested"
            credential_dir.mkdir()
            fake_key = "sk-" + "A" * 24
            (credential_dir / "credentials.json").write_text(
                json.dumps({"api_key": fake_key}) + "\n"
            )
            (copy / ".env").write_text("PLACEHOLDER=unset\n")
            (credential_dir / ".env.local").write_text("PLACEHOLDER=unset\n")
            (credential_dir / "identity.pem").write_text("placeholder\n")
            (credential_dir / "identity.key").write_text("placeholder\n")
            material = copy / "artifacts" / "KNOWN-credential.txt"
            private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
            material.write_text("token=" + fake_key + "\n" + private_key_marker + "\n")
            errors = gate.check(copy)
            joined = "\n".join(errors)
            self.assertIn("forbidden credential path", joined)
            for path in (
                "nested/credentials.json", ".env", "nested/.env.local",
                "nested/identity.pem", "nested/identity.key",
            ):
                self.assertIn(path, joined)
            self.assertIn("detected OpenAI-style API key", joined)
            self.assertIn("detected private-key material", joined)
            self.assertNotIn(fake_key, joined)
            self.assertNotIn(private_key_marker, joined)

    # Proves the bounded detector admits a representative harmless near-match.
    def test_release_gate_allows_credential_near_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "candidate"
            copy_public_candidate(copy)
            (copy / "docs" / "near-match.txt").write_text("task-output-source\n")
            (copy / ".env.example").write_text("API_KEY=replace-me\n")
            self.assertEqual(gate.check(copy), [])

    # Proves the candidate itself passes the same production release gate.
    def test_release_candidate_passes(self) -> None:
        self.assertEqual(gate.check(ROOT), [])


if __name__ == "__main__":
    unittest.main()
