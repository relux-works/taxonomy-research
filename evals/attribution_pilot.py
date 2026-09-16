#!/usr/bin/env python3
"""Build, run, and check the bounded Caveman attribution pilot.

The experiment tests observable model annotations. It does not expose private
reasoning or prove that a tagged source fragment caused any output wording.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


EVALS = Path(__file__).resolve().parent
REPO = EVALS.parent
SPEC = EVALS / "attribution_pilot_spec.json"
CASES = EVALS / "prompts" / "attribution_pilot_cases.json"
ANALYSIS_CORRECTIONS = EVALS / "attribution_pilot_analysis_corrections.json"
ORIGINAL_PATH = Path("skills/caveman/SKILL.md")
VENDORED_SOURCES = REPO / "fixtures" / "sources"
CURRENT_SOURCE = VENDORED_SOURCES / "caveman-current.md"
HISTORICAL_SOURCE = VENDORED_SOURCES / "caveman-historical.md"
CURRENT_COMMIT = "ed37ab132393899c129bbeef2b9743ff3af19c68"
CURRENT_SHA256 = "0bf09a0a9a017d004a81d4b693e5a2d830e1a28230a5885df773e1ed9c0571cc"
HISTORICAL_SHA256 = "86c684041a49da815c9fa5e34e161e36467dd09030986522aaab580fc212ae1c"
ARMS = (
    "terse-control",
    "original-clean",
    "original-instrumented",
    "semantic-clean",
    "semantic-instrumented",
)
OLD_ID_RE = re.compile(
    r"^(#{2,6}\s+.*?)\s+—\s+CAV-SEM-\d+(?:,\s*CAV-SEM-\d+)*$",
    re.MULTILINE,
)
TAG_RE = re.compile(r" \[EVAL-ID:(EV[OS]-[A-F0-9]{8}-\d{2})\]")
ENVELOPE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "annotations"],
    "properties": {
        "answer": {"type": "string"},
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["span", "rule_id"],
                "properties": {
                    "span": {"type": "string"},
                    "rule_id": {"type": "string"},
                },
            },
        },
    },
}
COMMON_SYSTEM = """You are participating in a bounded output-attribution evaluation.
Answer the user's request concisely. Return only the required structured envelope.
The `answer` field contains the answer a user should read.
The `annotations` field must be empty unless the system material below contains
`[EVAL-ID:...]` tags. When tags exist, add an annotation only when a tagged
source fragment materially guided observable answer wording. Copy `span`
verbatim from one unique location in `answer`; copy `rule_id` exactly. Do not
describe private reasoning. Do not claim provenance beyond this annotation.
"""


class PilotError(ValueError):
    """Input or output cannot support a trustworthy pilot result."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PilotError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise PilotError(f"expected JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise PilotError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def strip_historical_ids(text: str) -> str:
    """Remove only old CAV-SEM heading suffixes from the copied candidate."""
    return OLD_ID_RE.sub(r"\1", text)


def generated_id(source: str, clean_hash: str, position: int) -> str:
    family = "O" if source == "original" else "S"
    return f"EV{family}-{clean_hash[:8].upper()}-{position:02d}"


def read_pinned_source(path: Path, expected_sha256: str, label: str) -> bytes:
    value = path.read_bytes()
    actual = sha256_bytes(value)
    if actual != expected_sha256:
        raise PilotError(f"{label} snapshot hash mismatch: {actual}")
    return value


def instrument_source(
    clean: str,
    source: str,
    entries: list[dict[str, Any]],
    raw_commit: str,
    raw_hash: str,
) -> tuple[str, list[dict[str, Any]]]:
    clean_hash = sha256_bytes(clean.encode())
    instrumented = clean
    source_map: list[dict[str, Any]] = []
    for position, entry in enumerate(entries, 1):
        anchor = entry.get("anchor")
        if not isinstance(anchor, str) or not anchor:
            raise PilotError(f"{source} source-map entry {position} lacks anchor")
        match_count = clean.count(anchor)
        if match_count != 1:
            raise PilotError(
                f"{source}:{entry.get('key')} anchor match count {match_count}; expected 1"
            )
        rule_id = generated_id(source, clean_hash, position)
        tag = f" [EVAL-ID:{rule_id}]"
        instrumented = instrumented.replace(anchor, anchor + tag, 1)
        mapped = {
            "id": rule_id,
            "key": entry["key"],
            "source": source,
            "category": entry["category"],
            "exact_original_snippet": anchor,
            "match_count": match_count,
            "raw_commit": raw_commit,
            "raw_sha256": raw_hash,
            "clean_sha256": clean_hash,
        }
        for optional in ("lexical_any", "assessment"):
            if optional in entry:
                mapped[optional] = entry[optional]
        source_map.append(mapped)

    if TAG_RE.sub("", instrumented) != clean:
        raise PilotError(f"{source} annotations are not exactly reversible")
    return instrumented, source_map


def prepare_fixtures(output: Path, repo: Path = REPO) -> dict[str, Any]:
    """Build fixtures from pinned inert snapshots; ``repo`` is API-compatible only."""
    spec = read_json(SPEC)
    source_specs = spec.get("sources")
    if not isinstance(source_specs, dict):
        raise PilotError("spec.sources must be an object")

    del repo
    head = CURRENT_COMMIT
    original_bytes = read_pinned_source(CURRENT_SOURCE, CURRENT_SHA256, "current")
    original = original_bytes.decode("utf-8")
    original_hash = sha256_bytes(original_bytes)

    historical_commit = spec.get("historical_commit")
    if not isinstance(historical_commit, str):
        raise PilotError("historical_commit must be a string")
    historical_bytes = read_pinned_source(
        HISTORICAL_SOURCE, HISTORICAL_SHA256, "historical"
    )
    historical = historical_bytes.decode("utf-8")
    historical_hash = sha256_bytes(historical.encode())
    semantic_clean = strip_historical_ids(historical)
    if "CAV-SEM-" in semantic_clean:
        raise PilotError("old CAV-SEM IDs remain in semantic clean fixture")

    original_instrumented, original_map = instrument_source(
        original,
        "original",
        source_specs.get("original", []),
        head,
        original_hash,
    )
    semantic_instrumented, semantic_map = instrument_source(
        semantic_clean,
        "semantic",
        source_specs.get("semantic", []),
        historical_commit,
        historical_hash,
    )

    fixtures = output / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    fixture_values = {
        "original-clean.md": original,
        "original-instrumented.md": original_instrumented,
        "semantic-clean.md": semantic_clean,
        "semantic-instrumented.md": semantic_instrumented,
    }
    for name, value in fixture_values.items():
        (fixtures / name).write_text(value, encoding="utf-8")

    source_map = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "current_upstream": {
            "commit": head,
            "path": str(ORIGINAL_PATH),
            "sha256": original_hash,
        },
        "historical_semantic_candidate": {
            "commit": historical_commit,
            "path": str(ORIGINAL_PATH),
            "raw_sha256": historical_hash,
            "clean_sha256": sha256_bytes(semantic_clean.encode()),
            "status": "unmerged historical candidate",
            "removed_old_heading_ids": True,
        },
        "entries": original_map + semantic_map,
    }
    write_json(output / "source-map.json", source_map)
    return source_map


def load_cases() -> list[dict[str, Any]]:
    document = read_json(CASES)
    cases = document.get("cases")
    if not isinstance(cases, list) or not (6 <= len(cases) <= 8):
        raise PilotError("pilot requires 6-8 cases")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise PilotError("each case needs a string ID")
        if case["id"] in seen:
            raise PilotError(f"duplicate case ID: {case['id']}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise PilotError(f"case {case['id']} needs a prompt")
        if not isinstance(case.get("eligible_keys"), list):
            raise PilotError(f"case {case['id']} needs eligible_keys")
        if not isinstance(case.get("required_exact"), list):
            raise PilotError(f"case {case['id']} needs required_exact")
        seen.add(case["id"])
    return cases


def freeze_design(output: Path, seed: int, repetitions: int) -> dict[str, Any]:
    if repetitions != 2:
        raise PilotError("bounded pilot design requires exactly 2 repetitions")
    cases = load_cases()
    schedule = [
        {"repetition": repetition, "case_id": case["id"], "arm": arm}
        for repetition in range(1, repetitions + 1)
        for case in cases
        for arm in ARMS
    ]
    random.Random(seed).shuffle(schedule)
    design = {
        "schema_version": 1,
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": seed,
        "repetitions": repetitions,
        "arms": list(ARMS),
        "case_count": len(cases),
        "scheduled_cells": len(schedule),
        "combined_intervention_limitation": (
            "Instrumented arms combine source tagging with an annotation request; "
            "the pilot cannot isolate ID causality."
        ),
        "claim_limit": (
            "Annotations are model claims about observable spans, not internal "
            "reasoning or proof of provenance."
        ),
        "go_no_go": {
            "go_only_if": (
                "Raw responses and independent checks yield auditable exact-span "
                "mappings and at least one concrete nontrivial insight, without "
                "material unexplained answer corruption from annotation."
            ),
            "no_go_if": (
                "Mappings are mostly invalid or unsupported, matrix evidence is "
                "incomplete, or annotation materially corrupts required content."
            ),
            "scope": "Exploratory pilot; no significance or equivalence claim.",
        },
        "cases": cases,
        "schedule": schedule,
    }
    write_json(output / "design-freeze.json", design)
    return design


def system_inputs(output: Path) -> dict[str, str]:
    fixture_dir = output / "fixtures"
    skills = {
        "terse-control": "",
        "original-clean": (fixture_dir / "original-clean.md").read_text(),
        "original-instrumented": (
            fixture_dir / "original-instrumented.md"
        ).read_text(),
        "semantic-clean": (fixture_dir / "semantic-clean.md").read_text(),
        "semantic-instrumented": (
            fixture_dir / "semantic-instrumented.md"
        ).read_text(),
    }
    result: dict[str, str] = {}
    for arm, skill in skills.items():
        prefix = COMMON_SYSTEM + "\nAnswer concisely."
        result[arm] = prefix if not skill else f"{prefix}\n\n{skill}"
        path = output / "inputs" / f"{arm}.system.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result[arm], encoding="utf-8")
    return result


def claude_command(model: str, system: str, prompt: str) -> list[str]:
    binary = shutil.which("claude") or "claude"
    return [
        binary,
        "-p",
        "--safe-mode",
        "--restricted",
        "--setting-sources",
        "",
        "--strict-mcp-config",
        "--tools",
        "",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(ENVELOPE_SCHEMA, separators=(",", ":")),
        "--model",
        model,
        "--system-prompt",
        system,
        prompt,
    ]


def sanitized_environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("CLAUDE_") or key in {"MCP_CONFIG", "TASK_BOARD_RUN_ID"}:
            env.pop(key, None)
    env["CLAUDE_CODE_SAFE_MODE"] = "1"
    return env


def sanitize_error(value: str | bytes | None) -> str:
    """Redact common credential forms before persisting provider errors."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    patterns = (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s\"']+"),
        re.compile(
            r"(?i)((?:api[_-]?key|token|password)\s*[:=]\s*)[^\s\"']+"
        ),
        re.compile(r"\b(?:sk-ant-|sk-)[A-Za-z0-9_-]{12,}\b"),
    )
    for pattern in patterns:
        value = pattern.sub(lambda match: (match.group(1) if match.groups() else "") + "<redacted>", value)
    return value


def parse_cli_output(stdout: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise PilotError(f"CLI output is not JSON: {error}") from error
    if not isinstance(outer, dict):
        raise PilotError("CLI output must be an object")
    structured = outer.get("structured_output")
    if structured is None:
        result = outer.get("result")
        if not isinstance(result, str):
            raise PilotError("CLI output has no structured_output or string result")
        try:
            structured = json.loads(result)
        except json.JSONDecodeError as error:
            raise PilotError(f"model result is not JSON: {error}") from error
    if not isinstance(structured, dict):
        raise PilotError("structured model response must be an object")
    return structured, outer


def run_one(
    *,
    arm: str,
    case: dict[str, Any],
    repetition: int,
    model: str,
    system: str,
    timeout: float,
    raw_dir: Path,
    retries: int = 3,
) -> dict[str, Any]:
    cell = f"r{repetition}-{case['id']}-{arm}"
    attempts: list[dict[str, Any]] = []
    command = claude_command(model, system, case["prompt"])
    for attempt_number in range(1, retries + 2):
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        with tempfile.TemporaryDirectory(prefix="caveman-attribution-") as cwd:
            try:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    env=sanitized_environment(),
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                )
                attempt = {
                    "attempt": attempt_number,
                    "started_at": started,
                    "exit_code": result.returncode,
                    "timed_out": False,
                    "cwd_outside_repo": not str(Path(cwd)).startswith(str(REPO)),
                    "stdout": result.stdout,
                    "stderr": sanitize_error(result.stderr),
                }
            except subprocess.TimeoutExpired as error:
                attempt = {
                    "attempt": attempt_number,
                    "started_at": started,
                    "exit_code": None,
                    "timed_out": True,
                    "cwd_outside_repo": not str(Path(cwd)).startswith(str(REPO)),
                    "stdout": error.stdout or "",
                    "stderr": sanitize_error(error.stderr),
                }
        attempts.append(attempt)
        if attempt["exit_code"] == 0 and not attempt["timed_out"]:
            break
        if attempt_number <= retries:
            time.sleep(0.5 * (2 ** (attempt_number - 1)))

    record: dict[str, Any] = {
        "cell": cell,
        "arm": arm,
        "case_id": case["id"],
        "repetition": repetition,
        "requested_model": model,
        "attempts": attempts,
    }
    terminal = attempts[-1]
    if terminal["exit_code"] == 0 and not terminal["timed_out"]:
        try:
            response, outer = parse_cli_output(terminal["stdout"])
            record["status"] = "success"
            record["response"] = response
            record["usage"] = outer.get("usage")
            record["model_usage"] = outer.get("modelUsage")
        except PilotError as error:
            record["status"] = "malformed"
            record["parse_error"] = str(error)
    else:
        record["status"] = "failed"
    write_json(raw_dir / f"{cell}.json", record)
    return record


def known_ids_for_arm(source_map: dict[str, Any], arm: str) -> dict[str, dict[str, Any]]:
    source = "original" if arm.startswith("original") else "semantic"
    if arm in {"terse-control", "original-clean", "semantic-clean"}:
        return {}
    return {
        entry["id"]: entry
        for entry in source_map["entries"]
        if entry["source"] == source
    }


def observable_probe(
    assessment: str, answer: str, span: str, case: dict[str, Any]
) -> tuple[str, str]:
    """Run a narrow observable probe, never a semantic attribution verdict."""
    required = case.get("required_exact", [])
    if assessment == "exact-preservation":
        passed = bool(required) and all(item in answer for item in required) and any(
            item in span for item in required
        )
        reason = (
            "required exact artifacts preserved and represented in span"
            if required
            else "case has no predeclared exact artifact for this observable probe"
        )
        return "pass" if passed else "fail", reason
    if assessment == "polarity-preservation":
        polarity = ("not", "never", "no", "only", "except", "cannot")
        passed = any(re.search(rf"\b{word}\b", span, re.I) for word in polarity)
        return (
            "pass" if passed else "fail",
            "span contains an observable polarity or limit marker",
        )
    if assessment == "no-caricature":
        forbidden = ("me caveman", "caveman think", "Caveman:")
        passed = not any(value.lower() in answer.lower() for value in forbidden)
        return (
            "pass" if passed else "fail",
            "whole-answer absence probe for three predeclared caricature markers",
        )
    if assessment == "language":
        passed = case.get("language") == "ru" and bool(re.search(r"[А-Яа-яЁё]", span))
        return (
            "pass" if passed else "fail",
            "span matches the case's narrow Cyrillic-script probe",
        )
    if assessment == "explicit-warning":
        warning = bool(re.search(r"warning|warn|caution|предупреж", answer, re.I))
        backup = answer.lower().find("backup")
        drop = answer.upper().find("DROP TABLE")
        irreversible = bool(re.search(r"cannot be undone|irreversible|permanent", answer, re.I))
        passed = bool(case.get("explicit_warning")) and warning and 0 <= backup < drop and irreversible
        return (
            "pass" if passed else "fail",
            "whole-answer warning, backup-before-command, and irreversibility probe",
        )
    if assessment == "normal-prose-artifact":
        sentences = len(re.findall(r"[.!?](?:\s|$)", answer))
        article = bool(re.search(r"\b(?:a|an|the)\b", answer, re.I))
        passed = bool(case.get("normal_prose")) and sentences >= 2 and article
        return (
            "pass" if passed else "fail",
            "whole-answer sentence-count and English-article probe",
        )
    return "unassessed", f"unknown observable probe: {assessment}"


def validate_envelope(response: Any, arm: str) -> list[str]:
    """Validate response shape separately from transport success."""
    if not isinstance(response, dict):
        return ["response must be an object"]
    errors: list[str] = []
    expected_keys = {"answer", "annotations"}
    extra = sorted(set(response) - expected_keys)
    missing = sorted(expected_keys - set(response))
    if extra:
        errors.append(f"response has unknown keys: {', '.join(extra)}")
    if missing:
        errors.append(f"response is missing keys: {', '.join(missing)}")
    answer = response.get("answer")
    annotations = response.get("annotations")
    if not isinstance(answer, str):
        errors.append("answer must be a string")
    if not isinstance(annotations, list):
        errors.append("annotations must be an array")
        return errors
    for position, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            errors.append(f"annotation {position} must be an object")
            continue
        annotation_extra = sorted(set(annotation) - {"span", "rule_id"})
        annotation_missing = sorted({"span", "rule_id"} - set(annotation))
        if annotation_extra:
            errors.append(
                f"annotation {position} has unknown keys: {', '.join(annotation_extra)}"
            )
        if annotation_missing:
            errors.append(
                f"annotation {position} is missing keys: {', '.join(annotation_missing)}"
            )
        if not isinstance(annotation.get("span"), str) or not annotation.get("span"):
            errors.append(f"annotation {position} span must be a non-empty string")
        if not isinstance(annotation.get("rule_id"), str) or not annotation.get("rule_id"):
            errors.append(f"annotation {position} rule_id must be a non-empty string")
    if arm in {"terse-control", "original-clean", "semantic-clean"} and annotations:
        errors.append("clean/control arm returned forbidden annotations")
    return errors


def validate_response(
    record: dict[str, Any], case: dict[str, Any], source_map: dict[str, Any]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "cell": record["cell"],
        "transport_status": record["status"],
        "envelope_valid": False,
        "claims": [],
        "envelope_errors": [],
    }
    if record["status"] != "success":
        result["envelope_errors"].append(
            record.get("parse_error", "model subprocess failed")
        )
        return result
    response = record["response"]
    result["envelope_errors"] = validate_envelope(response, record["arm"])
    result["envelope_valid"] = not result["envelope_errors"]
    answer = response.get("answer")
    annotations = response.get("annotations")
    if not isinstance(answer, str):
        return result
    if not isinstance(annotations, list):
        return result
    known = known_ids_for_arm(source_map, record["arm"])
    result["answer_chars"] = len(answer)
    result["annotation_chars"] = len(
        json.dumps(annotations, ensure_ascii=False, separators=(",", ":"))
    )
    missing = [value for value in case.get("required_exact", []) if value not in answer]
    result["exact_preservation_missing"] = missing
    eligible = set(case["eligible_keys"])

    for annotation in annotations:
        claim: dict[str, Any] = {
            "structurally_valid": False,
            "eligible_for_case": False,
            "literal_lexical_probe": "not-applicable",
            "observable_probe": "unassessed",
            "independent_semantic_assessment": "needs-review",
            "provenance": "unsupported model self-report",
        }
        if not isinstance(annotation, dict):
            claim["reason"] = "annotation is not an object"
            result["claims"].append(claim)
            continue
        span = annotation.get("span")
        rule_id = annotation.get("rule_id")
        claim.update({"span": span, "rule_id": rule_id})
        if not isinstance(span, str) or not span:
            claim["reason"] = "span is missing or empty"
        elif answer.count(span) != 1:
            claim["reason"] = f"span match count is {answer.count(span)}; expected 1"
        elif not isinstance(rule_id, str) or rule_id not in known:
            claim["reason"] = "unknown arm-specific ID"
        else:
            claim["structurally_valid"] = True
            entry = known[rule_id]
            claim["source_key"] = entry["key"]
            if entry["key"] not in eligible:
                claim["reason"] = "ID was not predeclared eligible for this case"
            elif entry["source"] == "original":
                claim["eligible_for_case"] = True
                cues = entry.get("lexical_any", [])
                matched = [cue for cue in cues if cue.lower() in span.lower()]
                claim["lexical_matches"] = matched
                claim["literal_lexical_probe"] = "pass" if matched else "fail"
                claim["reason"] = (
                    "literal cue overlaps mapped source fragment"
                    if matched
                    else "no predeclared lexical cue agrees with exact span"
                )
            else:
                claim["eligible_for_case"] = True
                probe, reason = observable_probe(
                    entry.get("assessment", ""), answer, span, case
                )
                claim["observable_probe"] = probe
                claim["reason"] = reason
        result["claims"].append(claim)
    return result


def usage_tokens(record: dict[str, Any], key: str) -> int | None:
    usage = record.get("usage")
    if not isinstance(usage, dict):
        return None
    value = usage.get(key)
    return value if isinstance(value, int) else None


def matrix_audit(records: list[dict[str, Any]], design: dict[str, Any]) -> dict[str, Any]:
    """Compare the exact record multiset and declared identities with the schedule."""
    expected = Counter(
        (row["repetition"], row["case_id"], row["arm"])
        for row in design["schedule"]
    )
    observed: Counter[tuple[Any, Any, Any]] = Counter()
    inconsistent: list[dict[str, Any]] = []
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            inconsistent.append({"position": position, "reason": "record is not an object"})
            continue
        identity = (
            record.get("repetition"),
            record.get("case_id"),
            record.get("arm"),
        )
        observed[identity] += 1
        expected_cell = f"r{identity[0]}-{identity[1]}-{identity[2]}"
        if record.get("cell") != expected_cell:
            inconsistent.append(
                {
                    "position": position,
                    "declared_cell": record.get("cell"),
                    "expected_cell": expected_cell,
                }
            )

    missing_counter = expected - observed
    unexpected_counter = observed - expected
    duplicate_counter = Counter(
        {identity: count - 1 for identity, count in observed.items() if count > 1}
    )

    def rows(counter: Counter[tuple[Any, Any, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "repetition": identity[0],
                "case_id": identity[1],
                "arm": identity[2],
                "count": count,
            }
            for identity, count in sorted(counter.items(), key=lambda item: repr(item[0]))
        ]

    valid = not missing_counter and not unexpected_counter and not inconsistent
    return {
        "valid": valid,
        "expected_records": sum(expected.values()),
        "observed_records": len(records),
        "missing": rows(missing_counter),
        "unexpected": rows(unexpected_counter),
        "duplicates": rows(duplicate_counter),
        "inconsistent_declared_cells": inconsistent,
    }


def aggregate(
    records: list[dict[str, Any]],
    design: dict[str, Any],
    source_map: dict[str, Any],
    *,
    strict_matrix: bool = True,
) -> dict[str, Any]:
    audit = matrix_audit(records, design)
    if strict_matrix and not audit["valid"]:
        raise PilotError(
            "matrix mismatch: "
            f"missing={len(audit['missing'])}, unexpected={len(audit['unexpected'])}, "
            f"duplicates={len(audit['duplicates'])}, "
            f"inconsistent={len(audit['inconsistent_declared_cells'])}"
        )
    cases = {case["id"]: case for case in design["cases"]}
    corrections = read_json(ANALYSIS_CORRECTIONS)
    case_rubrics = corrections["case_rubrics"]
    analyzable = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("case_id") in cases
        and record.get("arm") in ARMS
    ]
    checks = [
        validate_response(record, cases[record["case_id"]], source_map)
        for record in analyzable
    ]
    by_arm: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for record, check in zip(analyzable, checks, strict=True):
        by_arm[record["arm"]].append((record, check))

    expected_by_arm = Counter(row["arm"] for row in design["schedule"])

    arm_results: dict[str, Any] = {}
    for arm in ARMS:
        rows = by_arm[arm]
        claims = [claim for _, check in rows for claim in check["claims"]]
        transport_success = [
            (record, check) for record, check in rows if record["status"] == "success"
        ]
        valid_responses = [
            (record, check) for record, check in transport_success if check["envelope_valid"]
        ]
        annotated_cells = sum(bool(check["claims"]) for _, check in valid_responses)
        structurally_valid_cells = sum(
            any(claim["structurally_valid"] for claim in check["claims"])
            for _, check in valid_responses
        )
        input_tokens = [usage_tokens(record, "input_tokens") for record, _ in transport_success]
        output_tokens = [usage_tokens(record, "output_tokens") for record, _ in transport_success]
        answer_chars = sum(check.get("answer_chars", 0) for _, check in valid_responses)
        annotation_chars = sum(
            check.get("annotation_chars", 0) for _, check in valid_responses
        )
        artifact_violations = [
            check["cell"]
            for record, check in valid_responses
            if case_rubrics[record["case_id"]].get("required_exact_role")
            == "artifact-preservation"
            and check.get("exact_preservation_missing")
        ]
        lexical_probe_misses = [
            check["cell"]
            for record, check in valid_responses
            if case_rubrics[record["case_id"]].get("required_exact_role")
            == "narrow lexical probe only"
            and check.get("exact_preservation_missing")
        ]
        arm_results[arm] = {
            "scheduled": expected_by_arm[arm],
            "observed": len(rows),
            "transport_success": len(transport_success),
            "provider_failed_or_malformed": len(rows) - len(transport_success),
            "valid_responses": len(valid_responses),
            "invalid_envelopes": len(transport_success) - len(valid_responses),
            "responses_with_annotations": annotated_cells,
            "annotation_cell_coverage": {
                "numerator": annotated_cells,
                "denominator": len(valid_responses),
            },
            "structurally_valid_annotation_cell_coverage": {
                "numerator": structurally_valid_cells,
                "denominator": len(valid_responses),
            },
            "claims": len(claims),
            "structurally_valid_claims": sum(bool(c["structurally_valid"]) for c in claims),
            "case_eligible_claims": sum(bool(c["eligible_for_case"]) for c in claims),
            "annotation_failures": sum(
                not c["structurally_valid"] or not c["eligible_for_case"]
                for c in claims
            ),
            "literal_lexical_probe_passes": sum(
                c["literal_lexical_probe"] == "pass" for c in claims
            ),
            "observable_probe_passes": sum(
                c["observable_probe"] == "pass" for c in claims
            ),
            "observable_probe_failures": sum(
                c["observable_probe"] == "fail" for c in claims
            ),
            "semantic_attribution_needs_review": sum(
                c["structurally_valid"] and c["eligible_for_case"] for c in claims
            ),
            "unsupported_causal_provenance_claims": len(claims),
            "artifact_preservation_violations": len(artifact_violations),
            "artifact_preservation_violation_cells": artifact_violations,
            "narrow_lexical_probe_misses": len(lexical_probe_misses),
            "narrow_lexical_probe_miss_cells": lexical_probe_misses,
            "answer_chars": answer_chars,
            "mean_answer_chars": (
                answer_chars / len(valid_responses) if valid_responses else None
            ),
            "annotation_json_chars": annotation_chars,
            "mean_annotation_json_chars": (
                annotation_chars / len(valid_responses) if valid_responses else None
            ),
            "usage": {
                "input_tokens_sum": sum(v for v in input_tokens if v is not None),
                "output_tokens_sum": sum(v for v in output_tokens if v is not None),
                "responses_with_real_usage": sum(v is not None for v in output_tokens),
            },
        }

    comparisons: dict[str, Any] = {}
    for family in ("original", "semantic"):
        clean = arm_results[f"{family}-clean"]
        instrumented = arm_results[f"{family}-instrumented"]
        clean_chars = clean["answer_chars"]
        comparisons[family] = {
            "answer_char_delta": instrumented["answer_chars"] - clean_chars,
            "answer_char_delta_percent": (
                100 * (instrumented["answer_chars"] - clean_chars) / clean_chars
                if clean_chars
                else None
            ),
            "annotation_json_chars": instrumented["annotation_json_chars"],
            "artifact_preservation_violation_delta": (
                instrumented["artifact_preservation_violations"]
                - clean["artifact_preservation_violations"]
            ),
            "cli_output_token_delta": (
                instrumented["usage"]["output_tokens_sum"]
                - clean["usage"]["output_tokens_sum"]
            ),
        }

    model_identities: dict[str, dict[str, Any]] = {}
    for record in analyzable:
        for name, details in (record.get("model_usage") or {}).items():
            if isinstance(details, dict):
                model_identities[name] = {
                    "canonical_model": details.get("canonicalModel"),
                    "provider": details.get("provider"),
                }
    attempts = [attempt for record in records for attempt in record.get("attempts", [])]
    result = {
        "schema_version": 2,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis_corrections": {
            "status": corrections["status"],
            "reason": corrections["reason"],
            "semantic_attribution": corrections["semantic_attribution"],
        },
        "matrix": audit,
        "publication_eligible_matrix": audit["valid"],
        "arms": arm_results,
        "paired_clean_vs_instrumented": comparisons,
        "execution": {
            "requested_models": sorted(
                {record["requested_model"] for record in analyzable}
            ),
            "model_usage_identities": model_identities,
            "attempts": len(attempts),
            "failed_or_timed_out_attempts": sum(
                attempt.get("exit_code") != 0 or attempt.get("timed_out")
                for attempt in attempts
            ),
            "attempts_with_repo_cwd": sum(
                not attempt.get("cwd_outside_repo", False) for attempt in attempts
            ),
        },
        "checks": checks,
        "interpretation_limits": [
            design["combined_intervention_limitation"],
            design["claim_limit"],
            "Post-collection rubric corrections are not described as predeclared.",
            "Observable probes are narrow diagnostics, not semantic attribution verdicts.",
            "Independent semantic attribution remains unassessed and needs review.",
            "Raw ID counts are not compared as quality because rule granularity differs.",
            "Current-original and historical-semantic arms differ in version and contract; this is not a pure compression comparison.",
        ],
    }
    return result


def prepare_all(output: Path, seed: int, repetitions: int) -> tuple[dict[str, Any], dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    source_map = prepare_fixtures(output)
    design = freeze_design(output, seed, repetitions)
    system_inputs(output)
    return source_map, design


def run_matrix(args: argparse.Namespace, smoke: bool = False) -> list[dict[str, Any]]:
    output = args.output.resolve()
    source_map, design = prepare_all(output, args.seed, args.repetitions)
    inputs = system_inputs(output)
    cases = {case["id"]: case for case in design["cases"]}
    schedule = design["schedule"]
    if smoke:
        schedule = [
            {
                "repetition": 1,
                "case_id": "exact-preservation",
                "arm": "semantic-instrumented",
            }
        ]
    if not 1 <= args.workers <= 3:
        raise PilotError("workers must be between 1 and 3")
    raw_dir = output / ("smoke-raw" if smoke else "raw")
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                run_one,
                arm=row["arm"],
                case=cases[row["case_id"]],
                repetition=row["repetition"],
                model=args.model,
                system=inputs[row["arm"]],
                timeout=args.timeout,
                raw_dir=raw_dir,
            )
            for row in schedule
        ]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
    records.sort(key=lambda row: row["cell"])
    write_json(output / ("smoke-results.json" if smoke else "results.json"), records)
    if smoke:
        checks = [validate_response(records[0], cases[records[0]["case_id"]], source_map)]
        write_json(output / "smoke-checks.json", checks)
    else:
        write_json(output / "aggregate.json", aggregate(records, design, source_map))
    return records


def analyze_existing(output: Path, *, allow_partial: bool = False) -> dict[str, Any]:
    source_map = read_json(output / "source-map.json")
    design = read_json(output / "design-freeze.json")
    records_value = json.loads((output / "results.json").read_text(encoding="utf-8"))
    if not isinstance(records_value, list):
        raise PilotError("results.json must contain a list")
    result = aggregate(
        records_value, design, source_map, strict_matrix=not allow_partial
    )
    target = "aggregate.partial.json" if allow_partial else "aggregate.json"
    write_json(output / target, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "smoke", "run", "analyze"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--output", type=Path, required=True)
        if command in {"prepare", "smoke", "run"}:
            sub.add_argument("--seed", type=int, default=260916)
            sub.add_argument("--repetitions", type=int, default=2)
        if command in {"smoke", "run"}:
            sub.add_argument("--model", required=True)
            sub.add_argument("--workers", type=int, default=3)
            sub.add_argument("--timeout", type=float, default=90.0)
        if command == "analyze":
            sub.add_argument(
                "--allow-partial",
                action="store_true",
                help="write a diagnostic incomplete summary; never publication-eligible",
            )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "prepare":
            prepare_all(args.output.resolve(), args.seed, args.repetitions)
        elif args.command == "smoke":
            records = run_matrix(args, smoke=True)
            if records[0]["status"] != "success":
                raise PilotError("isolated model smoke did not succeed")
        elif args.command == "run":
            run_matrix(args)
        else:
            analyze_existing(args.output.resolve(), allow_partial=args.allow_partial)
    except PilotError as error:
        print(f"pilot error: {error}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
