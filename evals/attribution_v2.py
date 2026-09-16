#!/usr/bin/env python3
"""Run segmented source-aware output diagnostics without provenance claims."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib.util
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
CASES_PATH = EVALS / "prompts" / "attribution_v2_cases.json"
PROTOCOL_PATH = EVALS / "attribution_v2_protocol.json"
CALIBRATION_PATH = EVALS / "attribution_v2_calibration.json"
V1_MODULE_PATH = EVALS / "attribution_pilot.py"
ARMS = (
    "terse-control",
    "original-clean",
    "original-tagged",
    "semantic-clean",
    "semantic-tagged",
)
TAGGED_ARMS = {"original-tagged": "original", "semantic-tagged": "semantic"}
CLEAN_ARMS = {"terse-control", "original-clean", "semantic-clean"}
RELATIONS = {"literal-overlap", "rule-compatible", "uncertain"}

LINK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rule_id", "relation", "source_quote"],
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "relation": {
            "type": "string",
            "enum": sorted(RELATIONS),
        },
        "source_quote": {"type": "string", "minLength": 1},
    },
}
ENVELOPE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["segments"],
    "properties": {
        "segments": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["text", "links"],
                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "links": {"type": "array", "items": LINK_SCHEMA},
                },
            },
        }
    },
}
COMMON_SYSTEM = """You are participating in a bounded source-aware output diagnostic.
Return only the required structured envelope. Build the user-visible answer from
ordered segments. The final answer is the exact concatenation of every `text`
field; preserve natural prose, whitespace, and code bytes inside those fields.

Each segment has `text` and `links`. `links` may always be empty. Never invent a
link merely to fill the schema. In clean/control conditions every `links` array
must be empty. In tagged conditions, a link may use only a listed source ID and
must copy that ID's complete source quote exactly.

Relations:
- `literal-overlap`: a distinctive literal phrase or code token occurs in both
  the output segment and source quote. Common-word coincidence is insufficient.
- `rule-compatible`: the segment appears observably compatible with a general
  instruction. This is a model-reported diagnostic that needs independent review.
- `uncertain`: a relationship may exist but should not be asserted.

A link reports an observable relationship only. It is not private chain of
thought, causal provenance, or proof that the source produced the answer.
"""


class V2Error(ValueError):
    """V2 input, matrix, or response cannot support trustworthy diagnostics."""


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise V2Error(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise V2Error(f"expected JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_v1_source_builder():
    spec = importlib.util.spec_from_file_location("attribution_v1_source_builder", V1_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise V2Error("cannot load pinned v1 source builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_sources(output: Path) -> dict[str, Any]:
    """Reuse v1-pinned source fragments while writing only into v2 evidence."""
    source_map = load_v1_source_builder().prepare_fixtures(output, repo=REPO)
    source_map["v2_reuse"] = {
        "purpose": "Reuse v1 pinned fixtures to isolate response-protocol changes",
        "version_confound": (
            "Current original and historical semantic sources differ in version and "
            "contract; comparisons do not isolate compression."
        ),
    }
    write_json(output / "source-map.json", source_map)
    return source_map


def load_cases() -> list[dict[str, Any]]:
    cases = read_object(CASES_PATH).get("cases")
    if not isinstance(cases, list) or len(cases) != 6:
        raise V2Error("v2 requires exactly six cases")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise V2Error("every case needs a string ID")
        if case["id"] in seen:
            raise V2Error(f"duplicate case ID: {case['id']}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise V2Error(f"case {case['id']} needs a prompt")
        if not isinstance(case.get("required_exact"), list):
            raise V2Error(f"case {case['id']} needs required_exact")
        applicable = case.get("applicable_keys")
        if not isinstance(applicable, dict) or set(applicable) != {"original", "semantic"}:
            raise V2Error(f"case {case['id']} needs original/semantic applicable_keys")
        seen.add(case["id"])
    return cases


def source_entries(source_map: dict[str, Any], source: str) -> list[dict[str, Any]]:
    return [entry for entry in source_map["entries"] if entry["source"] == source]


def source_catalog(entries: list[dict[str, Any]]) -> str:
    rows = ["Available reviewed source links:"]
    for entry in entries:
        rows.append(f"- {entry['id']}: {entry['exact_original_snippet']}")
    return "\n".join(rows)


def build_system_inputs(output: Path, source_map: dict[str, Any]) -> dict[str, str]:
    fixtures = output / "fixtures"
    skill_text = {
        "terse-control": "",
        "original-clean": (fixtures / "original-clean.md").read_text(encoding="utf-8"),
        "original-tagged": (fixtures / "original-instrumented.md").read_text(
            encoding="utf-8"
        ),
        "semantic-clean": (fixtures / "semantic-clean.md").read_text(encoding="utf-8"),
        "semantic-tagged": (fixtures / "semantic-instrumented.md").read_text(
            encoding="utf-8"
        ),
    }
    result: dict[str, str] = {}
    for arm in ARMS:
        parts = [COMMON_SYSTEM, "Answer concisely."]
        if skill_text[arm]:
            parts.append(skill_text[arm])
        if arm in TAGGED_ARMS:
            parts.append(source_catalog(source_entries(source_map, TAGGED_ARMS[arm])))
        else:
            parts.append("This is a clean/control condition. Every `links` array must be empty.")
        result[arm] = "\n\n".join(parts)
        path = output / "inputs" / f"{arm}.system.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result[arm], encoding="utf-8")
    return result


def claude_version() -> str:
    binary = shutil.which("claude") or "claude"
    result = subprocess.run(
        [binary, "--version"], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def claude_command(model: str, system: str, prompt: str) -> list[str]:
    return [
        shutil.which("claude") or "claude",
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


def isolated_environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("CLAUDE_") or key in {"MCP_CONFIG", "TASK_BOARD_RUN_ID"}:
            env.pop(key, None)
    env["CLAUDE_CODE_SAFE_MODE"] = "1"
    return env


def sanitize_error(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    patterns = (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s\"']+"),
        re.compile(r"(?i)((?:api[_-]?key|token|password)\s*[:=]\s*)[^\s\"']+"),
        re.compile(r"\b(?:sk-ant-|sk-)[A-Za-z0-9_-]{12,}\b"),
    )
    for pattern in patterns:
        value = pattern.sub(
            lambda match: (match.group(1) if match.groups() else "") + "<redacted>",
            value,
        )
    return value


def parse_cli_output(stdout: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise V2Error(f"CLI output is not JSON: {error}") from error
    if not isinstance(outer, dict):
        raise V2Error("CLI output must be an object")
    response = outer.get("structured_output")
    if response is None:
        raw_result = outer.get("result")
        if not isinstance(raw_result, str):
            raise V2Error("CLI output has no structured_output or string result")
        try:
            response = json.loads(raw_result)
        except json.JSONDecodeError as error:
            raise V2Error(f"model result is not JSON: {error}") from error
    if not isinstance(response, dict):
        raise V2Error("structured response must be an object")
    return response, outer


def run_one(
    *,
    model_label: str,
    model_id: str,
    arm: str,
    case: dict[str, Any],
    repetition: int,
    system: str,
    timeout: float,
    raw_dir: Path,
    retries: int = 3,
) -> dict[str, Any]:
    cell = f"{model_label}--r{repetition}-{case['id']}-{arm}"
    command = claude_command(model_id, system, case["prompt"])
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, retries + 2):
        with tempfile.TemporaryDirectory(prefix="caveman-attribution-v2-") as cwd:
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    env=isolated_environment(),
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
        "model_label": model_label,
        "requested_model": model_id,
        "arm": arm,
        "case_id": case["id"],
        "repetition": repetition,
        "attempts": attempts,
    }
    terminal = attempts[-1]
    if terminal["exit_code"] == 0 and not terminal["timed_out"]:
        try:
            response, outer = parse_cli_output(terminal["stdout"])
            record.update(
                status="transport-success",
                response=response,
                usage=outer.get("usage"),
                model_usage=outer.get("modelUsage"),
            )
        except V2Error as error:
            record.update(status="malformed", parse_error=str(error))
    else:
        record["status"] = "failed"
    write_json(raw_dir / f"{cell}.json", record)
    return record


def exposed_model_identity(record: dict[str, Any], requested: str) -> str:
    usage = record.get("model_usage")
    if not isinstance(usage, dict) or not usage:
        raise V2Error("smoke response exposed no modelUsage identity")
    requested_family = requested.lower()
    candidates = [
        key
        for key, details in usage.items()
        if key.startswith("claude-")
        and (
            requested_family in key.lower()
            or (
                isinstance(details, dict)
                and requested_family in str(details.get("canonicalModel", "")).lower()
            )
        )
    ]
    if not candidates:
        raise V2Error(
            f"smoke response exposed no Claude identity for requested family {requested!r}"
        )
    candidates.sort(key=lambda value: (len(value), value), reverse=True)
    return candidates[0]


def smoke(args: argparse.Namespace) -> dict[str, Any]:
    if args.model != "sonnet":
        raise V2Error("stronger-model discovery smoke must use supported alias 'sonnet'")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_map = prepare_sources(output)
    inputs = build_system_inputs(output, source_map)
    cases = {case["id"]: case for case in load_cases()}
    manifest = {
        "schema_version": 1,
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": "single isolated stronger-model identity discovery smoke",
        "requested_alias": "sonnet",
        "case_id": "exact-negation-artifacts",
        "arm": "semantic-tagged",
        "cases_sha256": sha256(CASES_PATH),
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "system_input_sha256": hashlib.sha256(
            inputs["semantic-tagged"].encode()
        ).hexdigest(),
    }
    write_json(output / "smoke-design.json", manifest)
    record = run_one(
        model_label="stronger-discovery",
        model_id="sonnet",
        arm="semantic-tagged",
        case=cases["exact-negation-artifacts"],
        repetition=1,
        system=inputs["semantic-tagged"],
        timeout=args.timeout,
        raw_dir=output / "smoke-raw",
    )
    write_json(output / "smoke-result.json", record)
    if record["status"] != "transport-success":
        raise V2Error("stronger-model discovery smoke failed")
    identity = {
        "requested_alias": "sonnet",
        "exposed_model_identity": exposed_model_identity(record, "sonnet"),
        "model_usage": record.get("model_usage"),
    }
    write_json(output / "stronger-model-identity.json", identity)
    return identity


def freeze_design(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    if (output / "design-freeze.json").exists():
        raise V2Error("design-freeze.json already exists; refuse to overwrite frozen v2 design")
    source_map = read_object(output / "source-map.json")
    inputs = build_system_inputs(output, source_map)
    cases = load_cases()
    identity = read_object(args.stronger_identity)
    stronger = identity.get("exposed_model_identity")
    if not isinstance(stronger, str) or not stronger or stronger == "sonnet":
        raise V2Error("stronger identity file lacks a pinned exposed model identity")
    models = {
        "haiku": args.haiku_model,
        "stronger": stronger,
    }
    schedule = [
        {
            "model_label": label,
            "model_id": model_id,
            "repetition": repetition,
            "case_id": case["id"],
            "arm": arm,
        }
        for label, model_id in models.items()
        for repetition in (1, 2)
        for case in cases
        for arm in ARMS
    ]
    if len(schedule) != 120:
        raise V2Error(f"v2 schedule must have 120 cells, got {len(schedule)}")
    random.Random(args.seed).shuffle(schedule)
    design = {
        "schema_version": 1,
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": args.seed,
        "repetitions": 2,
        "arms": list(ARMS),
        "models": models,
        "cases": cases,
        "schedule": schedule,
        "scheduled_cells": len(schedule),
        "claude_cli_version": claude_version(),
        "cases_sha256": sha256(CASES_PATH),
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "source_map_sha256": sha256(output / "source-map.json"),
        "system_input_sha256": {
            arm: hashlib.sha256(system.encode()).hexdigest()
            for arm, system in inputs.items()
        },
        "limits": [
            "Links are observable model claims, not chain of thought or causal provenance.",
            "Rule-compatible links require independent semantic review.",
            "Current-original and historical-semantic sources differ in version and contract.",
            "Cross-v1/v2 comparison is exploratory because the response protocol changed.",
            "Raw link counts cannot rank maps with unequal granularity.",
        ],
    }
    write_json(output / "design-freeze.json", design)
    return design


def expected_cell(row: dict[str, Any]) -> str:
    return (
        f"{row['model_label']}--r{row['repetition']}-"
        f"{row['case_id']}-{row['arm']}"
    )


def run_matrix(args: argparse.Namespace) -> list[dict[str, Any]]:
    if not 1 <= args.workers <= 3:
        raise V2Error("workers must be between 1 and 3")
    output = args.output.resolve()
    if (output / "results.json").exists():
        raise V2Error("results.json already exists; refuse to overwrite live v2 evidence")
    design = read_object(output / "design-freeze.json")
    source_map = read_object(output / "source-map.json")
    inputs = build_system_inputs(output, source_map)
    cases = {case["id"]: case for case in design["cases"]}
    futures = []
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in design["schedule"]:
            futures.append(
                pool.submit(
                    run_one,
                    model_label=row["model_label"],
                    model_id=row["model_id"],
                    arm=row["arm"],
                    case=cases[row["case_id"]],
                    repetition=row["repetition"],
                    system=inputs[row["arm"]],
                    timeout=args.timeout,
                    raw_dir=output / "raw",
                )
            )
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
    records.sort(key=lambda record: record["cell"])
    write_json(output / "results.json", records)
    analyze(output)
    return records


def matrix_audit(records: list[dict[str, Any]], design: dict[str, Any]) -> dict[str, Any]:
    expected = Counter(
        (
            row["model_label"],
            row["model_id"],
            row["repetition"],
            row["case_id"],
            row["arm"],
        )
        for row in design["schedule"]
    )
    observed: Counter[tuple[Any, ...]] = Counter()
    inconsistent: list[dict[str, Any]] = []
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            inconsistent.append({"position": position, "reason": "record is not an object"})
            continue
        identity = (
            record.get("model_label"),
            record.get("requested_model"),
            record.get("repetition"),
            record.get("case_id"),
            record.get("arm"),
        )
        observed[identity] += 1
        shape = {
            "model_label": identity[0],
            "repetition": identity[2],
            "case_id": identity[3],
            "arm": identity[4],
        }
        if record.get("cell") != expected_cell(shape):
            inconsistent.append(
                {
                    "position": position,
                    "declared_cell": record.get("cell"),
                    "expected_cell": expected_cell(shape),
                }
            )
    missing = expected - observed
    unexpected = observed - expected
    duplicates = Counter(
        {identity: count - 1 for identity, count in observed.items() if count > 1}
    )

    def render(counter: Counter[tuple[Any, ...]]) -> list[dict[str, Any]]:
        keys = ("model_label", "model_id", "repetition", "case_id", "arm")
        return [
            {**dict(zip(keys, identity, strict=True)), "count": count}
            for identity, count in sorted(counter.items(), key=lambda item: repr(item[0]))
        ]

    return {
        "valid": not missing and not unexpected and not inconsistent,
        "expected_records": sum(expected.values()),
        "observed_records": len(records),
        "missing": render(missing),
        "unexpected": render(unexpected),
        "duplicates": render(duplicates),
        "inconsistent_declared_cells": inconsistent,
    }


def validate_envelope(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return ["response must be an object"]
    errors: list[str] = []
    if set(response) != {"segments"}:
        errors.append("response keys must be exactly: segments")
    segments = response.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty array")
        return errors
    for segment_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            errors.append(f"segment {segment_index} must be an object")
            continue
        if set(segment) != {"text", "links"}:
            errors.append(f"segment {segment_index} keys must be exactly: text, links")
        if not isinstance(segment.get("text"), str) or not segment.get("text"):
            errors.append(f"segment {segment_index} text must be non-empty")
        links = segment.get("links")
        if not isinstance(links, list):
            errors.append(f"segment {segment_index} links must be an array")
            continue
        for link_index, link in enumerate(links):
            prefix = f"segment {segment_index} link {link_index}"
            if not isinstance(link, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if set(link) != {"rule_id", "relation", "source_quote"}:
                errors.append(
                    f"{prefix} keys must be exactly: relation, rule_id, source_quote"
                )
            if not isinstance(link.get("rule_id"), str) or not link.get("rule_id"):
                errors.append(f"{prefix} rule_id must be non-empty")
            if link.get("relation") not in RELATIONS:
                errors.append(f"{prefix} relation is invalid")
            if not isinstance(link.get("source_quote"), str) or not link.get(
                "source_quote"
            ):
                errors.append(f"{prefix} source_quote must be non-empty")
    return errors


def sentence_count(answer: str) -> int:
    return len(re.findall(r"[.!?](?=\s|$)", answer))


def answer_invariants(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    """Check only exact artifacts/answer and explicit output language."""
    missing = [value for value in case["required_exact"] if value not in answer]
    violations: list[str] = []
    if missing:
        violations.append("missing required exact artifacts: " + ", ".join(missing))
    exact_answer = case.get("exact_answer")
    if isinstance(exact_answer, str) and answer != exact_answer:
        violations.append("answer does not equal required exact answer")
    if case.get("language") == "ru" and not re.search(r"[А-Яа-яЁё]", answer):
        violations.append("answer lacks Cyrillic text required by Russian-language case")
    return {
        "passed": not violations,
        "violations": violations,
        "missing_required_exact": missing,
    }


def heuristic_answer_alerts(answer: str, case: dict[str, Any]) -> list[dict[str, Any]]:
    """Return non-ground-truth prose alerts; never change grounded pass/fail."""
    alerts: list[dict[str, Any]] = []
    exact_sentences = case.get("exact_sentences")
    actual_sentences = sentence_count(answer)
    if isinstance(exact_sentences, int) and actual_sentences != exact_sentences:
        alerts.append(
            {
                "kind": "punctuation-sentence-count",
                "observed": actual_sentences,
                "requested": exact_sentences,
                "limit": "abbreviations and punctuation make this a heuristic only",
            }
        )
    if case.get("normal_prose") and not re.search(r"\b(?:a|an|the)\b", answer, re.I):
        alerts.append(
            {
                "kind": "english-article-absence",
                "limit": "grammatical professional prose need not contain a/an/the",
            }
        )
    return alerts


def joining_whitespace_defects(segments: list[Any]) -> list[dict[str, Any]]:
    """Detect punctuation-to-word joins created only by segment concatenation."""
    defects = []
    for index, (left, right) in enumerate(zip(segments, segments[1:])):
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue
        left_text, right_text = left.get("text"), right.get("text")
        if not isinstance(left_text, str) or not isinstance(right_text, str):
            continue
        if re.search(r"[.!?]$", left_text) and re.match(r"[\wА-Яа-яЁё]", right_text):
            defects.append(
                {
                    "boundary_after_segment": index,
                    "left_suffix": left_text[-16:],
                    "right_prefix": right_text[:16],
                }
            )
    return defects


def arm_source(arm: str) -> str | None:
    if arm.startswith("original"):
        return "original"
    if arm.startswith("semantic"):
        return "semantic"
    return None


def validate_record(
    record: dict[str, Any],
    case: dict[str, Any],
    source_map: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "cell": record["cell"],
        "transport_status": record["status"],
        "envelope_valid": False,
        "metadata_valid": False,
        "envelope_errors": [],
        "metadata_errors": [],
        "links": [],
    }
    if record["status"] != "transport-success":
        result["envelope_errors"].append(
            record.get("parse_error", "provider subprocess failed")
        )
        return result
    response = record.get("response")
    result["envelope_errors"] = validate_envelope(response)
    result["envelope_valid"] = not result["envelope_errors"]
    if not isinstance(response, dict) or not isinstance(response.get("segments"), list):
        return result

    segments = response["segments"]
    texts = [
        segment.get("text", "") if isinstance(segment, dict) else ""
        for segment in segments
    ]
    answer = "".join(texts)
    result["answer"] = answer
    result["answer_chars"] = len(answer)
    result["grounded_answer_checks"] = answer_invariants(answer, case)
    result["answer_invariants"] = result["grounded_answer_checks"]
    result["heuristic_answer_alerts"] = heuristic_answer_alerts(answer, case)
    result["joining_whitespace_defects"] = joining_whitespace_defects(segments)
    result["extraneous_source_copies"] = []

    all_entries = {entry["id"]: entry for entry in source_map["entries"]}
    source = arm_source(record["arm"])
    allowed = {
        entry["id"]: entry
        for entry in source_map["entries"]
        if entry["source"] == source
    }
    applicable = set(case["applicable_keys"].get(source or "", []))
    literal_markers = protocol["literal_markers"]

    for entry in source_map["entries"]:
        snippet = entry["exact_original_snippet"]
        if len(snippet) >= 30 and snippet in answer:
            result["extraneous_source_copies"].append(entry["id"])
    if result["extraneous_source_copies"]:
        result["answer_invariants"]["passed"] = False
        result["answer_invariants"]["violations"].append(
            "answer copies full mapped source fragment as extraneous content"
        )

    metadata_chars = 0
    for segment_index, segment in enumerate(segments):
        if not isinstance(segment, dict) or not isinstance(segment.get("links"), list):
            continue
        text = segment.get("text") if isinstance(segment.get("text"), str) else ""
        metadata_chars += len(
            json.dumps(segment["links"], ensure_ascii=False, separators=(",", ":"))
        )
        for link_index, link in enumerate(segment["links"]):
            audit = {
                "cell": record["cell"],
                "model_label": record["model_label"],
                "model_id": record["requested_model"],
                "arm": record["arm"],
                "case_id": case["id"],
                "prompt": case["prompt"],
                "segment_index": segment_index,
                "link_index": link_index,
                "claim_id": None,
                "segment_text": text,
                "rule_id": link.get("rule_id") if isinstance(link, dict) else None,
                "relation": link.get("relation") if isinstance(link, dict) else None,
                "claimed_source_quote": (
                    link.get("source_quote") if isinstance(link, dict) else None
                ),
                "source_fragment": None,
                "known_id": False,
                "arm_specific_id": False,
                "exact_source_quote": False,
                "case_applicable": False,
                "literal_marker_matches": [],
                "applicability_observation": "unknown",
                "independent_semantic_review": "not-performed",
                "relationship_status": "invalid-metadata",
            }
            if not isinstance(link, dict):
                result["metadata_errors"].append(
                    f"segment {segment_index} link {link_index} is not an object"
                )
                result["links"].append(audit)
                continue
            rule_id = link.get("rule_id")
            audit["claim_id"] = f"{record['cell']}::segment-{segment_index}::{rule_id}"
            entry = all_entries.get(rule_id)
            audit["known_id"] = entry is not None
            audit["arm_specific_id"] = rule_id in allowed
            if entry is not None:
                audit["source_fragment"] = entry["exact_original_snippet"]
                audit["case_applicable"] = entry["key"] in applicable
                audit["applicability_observation"] = (
                    "inside-predeclared-applicability"
                    if audit["case_applicable"]
                    else "outside-predeclared-applicability"
                )
                audit["exact_source_quote"] = (
                    link.get("source_quote") == entry["exact_original_snippet"]
                )
            if entry is None:
                result["metadata_errors"].append(
                    f"segment {segment_index} link {link_index} has unknown ID"
                )
            elif rule_id not in allowed:
                result["metadata_errors"].append(
                    f"segment {segment_index} link {link_index} has cross-arm ID"
                )
            if entry is not None and not audit["exact_source_quote"]:
                result["metadata_errors"].append(
                    f"segment {segment_index} link {link_index} has incorrect source quote"
                )

            relation = link.get("relation")
            if entry is not None:
                markers = literal_markers.get(entry["key"], [])
                audit["literal_marker_matches"] = [
                    marker
                    for marker in markers
                    if marker.lower() in text.lower()
                    and marker.lower() in entry["exact_original_snippet"].lower()
                ]
                if entry["exact_original_snippet"] in text:
                    audit["literal_marker_matches"].append(
                        entry["exact_original_snippet"]
                    )
            metadata_ok = (
                audit["known_id"]
                and audit["arm_specific_id"]
                and audit["exact_source_quote"]
                and relation in RELATIONS
            )
            if metadata_ok:
                if relation == "uncertain":
                    audit["relationship_status"] = "uncertain"
                elif relation == "literal-overlap":
                    audit["relationship_status"] = (
                        "literal-overlap-confirmed"
                        if audit["literal_marker_matches"]
                        else "misleading-literal-claim"
                    )
                else:
                    audit["relationship_status"] = "rule-compatible-unassessed"
            result["links"].append(audit)

    for audit in result["links"]:
        audit["independent_answer_checks"] = {
            "grounded": result["grounded_answer_checks"],
            "heuristic_alerts": result["heuristic_answer_alerts"],
            "joining_whitespace_defects": result["joining_whitespace_defects"],
            "extraneous_source_copies": result["extraneous_source_copies"],
        }

    total_links = len(result["links"])
    if record["arm"] in CLEAN_ARMS and total_links:
        result["metadata_errors"].append("clean/control response returned forbidden links")
    result["metadata_chars"] = metadata_chars
    result["link_count"] = total_links
    result["abstained"] = total_links == 0
    result["mapped_source_applicable"] = bool(applicable)
    result["metadata_valid"] = result["envelope_valid"] and not result["metadata_errors"]
    result["response_valid"] = result["envelope_valid"] and result["metadata_valid"]
    return result


def usage_tokens(record: dict[str, Any], key: str) -> int | None:
    usage = record.get("usage")
    if not isinstance(usage, dict):
        return None
    value = usage.get(key)
    return value if isinstance(value, int) else None


def integrate_independent_review(
    checks: list[dict[str, Any]], review_path: Path
) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """Attach immutable independent model-review judgments by stable claim ID."""
    review = read_object(review_path)
    assessments = review.get("emitted_link_assessments")
    omissions = review.get("observable_omissions")
    if not isinstance(assessments, list) or not isinstance(omissions, list):
        raise V2Error("independent review lacks emitted assessments or omissions")
    assessment_map = {row["claim_id"]: row for row in assessments}
    omission_map = {row["claim_id"]: row for row in omissions}
    if len(assessment_map) != len(assessments) or len(omission_map) != len(omissions):
        raise V2Error("independent review contains duplicate claim IDs")
    live_links = [link for check in checks for link in check["links"]]
    live_ids = {link["claim_id"] for link in live_links}
    if live_ids != set(assessment_map):
        raise V2Error("independent emitted-link review does not exactly cover live links")
    counts = Counter()
    for link in live_links:
        row = assessment_map[link["claim_id"]]
        counts[row["judgment"]] += 1
        link["independent_semantic_review"] = "completed-independent-model-review"
        link["independent_model_review"] = {
            "judgment": row["judgment"],
            "rationale": row["rationale"],
            "authority": "independent model review; not human ground truth",
        }
    declared = review["coverage"]["returned_link_judgment_counts"]
    if any(counts[key] != declared.get(key) for key in counts):
        raise V2Error("independent review judgment counts do not match assessments")
    summary = {
        "source_path": str(review_path.resolve()),
        "sha256": sha256(review_path),
        "authority": "independent model review; not human ground truth or causal evidence",
        "emitted_links_reviewed": len(assessments),
        "judgment_counts": dict(counts),
        "observable_omissions": len(omissions),
        "omission_interpretation": "observable diagnostic omissions, not causal false negatives",
        "live_precision": None,
        "live_recall": None,
        "rate_limit": "the complete negative candidate universe was not independently labeled",
    }
    return summary, {**assessment_map, **omission_map}


def scored_relationships(
    fixtures: list[dict[str, Any]], predictions: dict[str, bool]
) -> dict[str, Any]:
    """Score explicit observable labels; insufficient evidence is never coerced."""
    counts = Counter()
    for fixture in fixtures:
        label = fixture["expected_label"]
        emitted = predictions[fixture["id"]]
        if label == "insufficient-evidence":
            counts["insufficient_evidence"] += 1
        elif label == "compatible" and emitted:
            counts["true_positive"] += 1
        elif label == "compatible":
            counts["false_negative"] += 1
        elif label == "contradicted" and emitted:
            counts["false_positive"] += 1
        elif label == "contradicted":
            counts["true_negative"] += 1
        else:
            raise V2Error(f"unknown observable fixture label: {label!r}")
    precision_denominator = counts["true_positive"] + counts["false_positive"]
    recall_denominator = counts["true_positive"] + counts["false_negative"]
    precision = (
        counts["true_positive"] / precision_denominator
        if precision_denominator
        else None
    )
    recall = (
        counts["true_positive"] / recall_denominator
        if recall_denominator
        else None
    )
    return {
        **{
            key: counts[key]
            for key in (
                "true_positive",
                "false_positive",
                "true_negative",
                "false_negative",
                "insufficient_evidence",
            )
        },
        "precision": {
            "value": precision,
            "numerator": counts["true_positive"],
            "denominator": precision_denominator,
        },
        "recall": {
            "value": recall,
            "numerator": counts["true_positive"],
            "denominator": recall_denominator,
        },
        "passes_perfect_fixture_gate": precision == 1.0 and recall == 1.0,
    }


def observe_declared_fixture_property(
    fixture: dict[str, Any], source_entry: dict[str, Any]
) -> dict[str, Any]:
    """Observe only an explicit fixture property; this is not general semantics."""
    prop = fixture["declared_property"]
    kind = prop["kind"]
    text = fixture["segment_text"]
    source = source_entry["exact_original_snippet"]
    if kind == "distinctive-literal-overlap":
        marker = prop["marker"]
        passed = marker in text and marker in source
        evidence = {"marker": marker, "in_segment": marker in text, "in_source": marker in source}
    elif kind == "required-exact-artifacts":
        missing = [item for item in prop["required"] if item not in text]
        passed = not missing
        evidence = {"required": prop["required"], "missing": missing}
    elif kind == "required-polarity":
        phrase = prop["required_phrase"]
        passed = phrase in text
        evidence = {"required_phrase": phrase, "present": passed}
    elif kind == "required-language":
        cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
        latin = len(re.findall(r"[A-Za-z]", text))
        required = prop["language"]
        passed = cyrillic > latin if required == "ru" else latin > cyrillic
        evidence = {"required_language": required, "cyrillic_letters": cyrillic, "latin_letters": latin}
    elif kind == "unsupported-general-semantics":
        return {
            "judgment": "insufficient-evidence",
            "evidence": {"limit": "fixture declares no deterministic observable property"},
        }
    else:
        raise V2Error(f"unknown calibration observer property: {kind!r}")
    return {"judgment": "compatible" if passed else "contradicted", "evidence": evidence}


def run_calibration(output: Path) -> dict[str, Any]:
    """Run post-collection synthetic controls without touching frozen live data."""
    spec = read_object(CALIBRATION_PATH)
    source_map = read_object(output / "source-map.json")
    protocol = read_object(PROTOCOL_PATH)
    cases = {case["id"]: case for case in load_cases()}
    entries = {entry["key"]: entry for entry in source_map["entries"]}
    structural_results = []
    for fixture in spec["structural_fixtures"]:
        links: list[dict[str, Any]] = []
        if not fixture.get("no_link"):
            entry = entries[fixture["source_key"]]
            mode = fixture["quote_mode"]
            rule_id = entry["id"] if mode != "unknown-id" else "UNKNOWN-CALIBRATION-ID"
            quote = entry["exact_original_snippet"]
            if mode == "truncated":
                quote = quote[: max(1, len(quote) // 2)]
            links.append(
                {
                    "rule_id": rule_id,
                    "relation": fixture["relation"],
                    "source_quote": quote,
                }
            )
        record = {
            "cell": f"calibration--{fixture['id']}",
            "model_label": "offline-calibration",
            "requested_model": "none",
            "arm": fixture["arm"],
            "case_id": fixture["case_id"],
            "repetition": 0,
            "status": "transport-success",
            "response": {"segments": [{"text": fixture["text"], "links": links}]},
        }
        check = validate_record(record, cases[fixture["case_id"]], source_map, protocol)
        accepted = bool(check["response_valid"])
        structural_results.append(
            {
                "id": fixture["id"],
                "expected_accept": fixture["expected_accept"],
                "accepted": accepted,
                "false_accept": accepted and not fixture["expected_accept"],
                "false_reject": not accepted and fixture["expected_accept"],
                "envelope_errors": check["envelope_errors"],
                "metadata_errors": check["metadata_errors"],
            }
        )
    observable = spec["observable_fixtures"]
    observer_rows = []
    observer_labels: dict[str, str] = {}
    for fixture in observable:
        observed = observe_declared_fixture_property(
            fixture, entries[fixture["source_key"]]
        )
        observer_labels[fixture["id"]] = observed["judgment"]
        observer_rows.append(
            {
                **fixture,
                "observer_judgment": observed["judgment"],
                "observer_evidence": observed["evidence"],
                "matches_independent_expected_label": (
                    observed["judgment"] == fixture["expected_label"]
                ),
            }
        )
    observed_fixtures = [
        {**fixture, "expected_label": observer_labels[fixture["id"]]}
        for fixture in observable
    ]
    emitted = {fixture["id"]: fixture["emitted"] for fixture in observable}
    always_positive = {fixture["id"]: True for fixture in observable}
    always_empty = {fixture["id"]: False for fixture in observable}
    result = {
        "schema_version": 1,
        "status": spec["status"],
        "unit_of_analysis": spec["unit_of_analysis"],
        "warning": (
            "Fixture scores calibrate checker/audit behavior only. They are not live "
            "model attribution precision and do not observe causal instruction use."
        ),
        "structural": {
            "fixtures": structural_results,
            "expected_accept_denominator": sum(
                fixture["expected_accept"] for fixture in spec["structural_fixtures"]
            ),
            "expected_reject_denominator": sum(
                not fixture["expected_accept"]
                for fixture in spec["structural_fixtures"]
            ),
            "false_accepts": sum(row["false_accept"] for row in structural_results),
            "false_rejects": sum(row["false_reject"] for row in structural_results),
        },
        "observable": {
            "observer_scope": (
                "deterministic checks only for declared literal/artifact/polarity/language "
                "fixture properties; no general semantic classifier"
            ),
            "fixtures": observer_rows,
            "observer_expected_label_mismatches": sum(
                not row["matches_independent_expected_label"] for row in observer_rows
            ),
            "declared_emissions": scored_relationships(observed_fixtures, emitted),
            "always_positive_control": scored_relationships(observed_fixtures, always_positive),
            "always_empty_control": scored_relationships(observed_fixtures, always_empty),
        },
        "live_data": {
            "numeric_false_positive_rate": None,
            "numeric_false_negative_rate": None,
            "reason": (
                "Independent review has not yet labeled the complete live candidate "
                "universe; use all-tagged-segments-audit.json for that review."
            ),
        },
    }
    write_json(output / "calibration.json", result)
    return result


def write_all_tagged_segments_audit(
    output: Path,
    records: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    source_map: dict[str, Any],
    independent_judgments: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Expose every tagged segment and candidate source, including omissions."""
    segments: list[dict[str, Any]] = []
    response_ids: set[str] = set()
    for record, check in zip(records, checks, strict=True):
        if record["arm"] not in TAGGED_ARMS or not check.get("envelope_valid"):
            continue
        response_ids.add(record["cell"])
        source = TAGGED_ARMS[record["arm"]]
        entries = source_entries(source_map, source)
        applicable = set(
            next(case for case in load_cases() if case["id"] == record["case_id"])[
                "applicable_keys"
            ][source]
        )
        response_segments = record["response"]["segments"]
        for index, segment in enumerate(response_segments):
            segment_id = f"{record['cell']}::segment-{index}"
            emitted_links = [
                link for link in check["links"] if link["segment_index"] == index
            ]
            emitted_ids = {link["rule_id"] for link in emitted_links}
            candidates = []
            for entry in entries:
                claim_id = f"{segment_id}::{entry['id']}"
                independent = (independent_judgments or {}).get(claim_id)
                candidates.append({
                    "claim_id": claim_id,
                    "rule_id": entry["id"],
                    "source_key": entry["key"],
                    "source_fragment": entry["exact_original_snippet"],
                    "prior_case_applicable": entry["key"] in applicable,
                    "emitted": entry["id"] in emitted_ids,
                    "independent_observable_judgment": (
                        independent["judgment"] if independent else None
                    ),
                    "reviewer_rationale": (
                        independent["rationale"] if independent else None
                    ),
                    "review_authority": (
                        "independent model review; not human ground truth"
                        if independent
                        else None
                    ),
                })
            segments.append(
                {
                    "segment_id": segment_id,
                    "cell": record["cell"],
                    "model_label": record["model_label"],
                    "model_id": record["requested_model"],
                    "arm": record["arm"],
                    "case_id": record["case_id"],
                    "prompt": next(
                        case["prompt"]
                        for case in load_cases()
                        if case["id"] == record["case_id"]
                    ),
                    "segment_index": index,
                    "segment_text": segment["text"],
                    "emitted_links": emitted_links,
                    "candidate_sources": candidates,
                    "independent_answer_checks": {
                        "grounded": check["grounded_answer_checks"],
                        "heuristic_alerts": check["heuristic_answer_alerts"],
                        "joining_whitespace_defects": check[
                            "joining_whitespace_defects"
                        ],
                        "extraneous_source_copies": check["extraneous_source_copies"],
                    },
                }
            )
    packet = {
        "schema_version": 1,
        "status": "post-collection review packet",
        "unit_of_analysis": "one tagged response segment against one candidate source fragment",
        "warning": (
            "Prior case applicability is routing context, not semantic ground truth. "
            "An omitted observable link is not proof that an instruction had no causal influence."
        ),
        "tagged_response_count": len(response_ids),
        "tagged_segment_count": len(segments),
        "candidate_pair_count": sum(len(row["candidate_sources"]) for row in segments),
        "segments": segments,
    }
    write_json(output / "all-tagged-segments-audit.json", packet)
    return packet


def analyze(
    output: Path,
    *,
    allow_partial: bool = False,
    independent_review_path: Path | None = None,
) -> dict[str, Any]:
    design = read_object(output / "design-freeze.json")
    source_map = read_object(output / "source-map.json")
    protocol = read_object(PROTOCOL_PATH)
    try:
        records = json.loads((output / "results.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise V2Error(f"cannot read results.json: {error}") from error
    if not isinstance(records, list):
        raise V2Error("results.json must contain an array")
    audit = matrix_audit(records, design)
    if not allow_partial and not audit["valid"]:
        raise V2Error(
            "matrix mismatch: "
            f"missing={len(audit['missing'])}, unexpected={len(audit['unexpected'])}, "
            f"duplicates={len(audit['duplicates'])}, "
            f"inconsistent={len(audit['inconsistent_declared_cells'])}"
        )
    cases = {case["id"]: case for case in design["cases"]}
    analyzable = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("case_id") in cases
        and record.get("arm") in ARMS
        and record.get("model_label") in design["models"]
    ]
    checks = [
        validate_record(
            record, cases[record["case_id"]], source_map, protocol
        )
        for record in analyzable
    ]
    independent_review = None
    independent_judgments = None
    if independent_review_path is not None:
        independent_review, independent_judgments = integrate_independent_review(
            checks, independent_review_path
        )
    grouped: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = (
        defaultdict(list)
    )
    for record, check in zip(analyzable, checks, strict=True):
        grouped[(record["model_label"], record["arm"])].append((record, check))
    scheduled = Counter(
        (row["model_label"], row["arm"]) for row in design["schedule"]
    )

    metrics: dict[str, dict[str, Any]] = {}
    for model_label in design["models"]:
        metrics[model_label] = {}
        for arm in ARMS:
            rows = grouped[(model_label, arm)]
            transport = [row for row in rows if row[0]["status"] == "transport-success"]
            well_formed = [row for row in transport if row[1].get("envelope_valid")]
            metadata_valid = [row for row in well_formed if row[1].get("metadata_valid")]
            links = [link for _, check in well_formed for link in check["links"]]
            applicable = [
                row for row in well_formed if row[1]["mapped_source_applicable"]
            ]
            no_applicable = [
                row for row in well_formed if not row[1]["mapped_source_applicable"]
            ]
            answers = sum(check.get("answer_chars", 0) for _, check in well_formed)
            metadata = sum(check.get("metadata_chars", 0) for _, check in well_formed)
            input_tokens = [usage_tokens(record, "input_tokens") for record, _ in transport]
            output_tokens = [usage_tokens(record, "output_tokens") for record, _ in transport]
            relationship_counts = Counter(link["relationship_status"] for link in links)
            valid_response_links = [
                link for _, check in metadata_valid for link in check["links"]
            ]
            metrics[model_label][arm] = {
                "scheduled": scheduled[(model_label, arm)],
                "observed": len(rows),
                "transport_success": len(transport),
                "provider_failed_or_malformed": len(rows) - len(transport),
                "well_formed_envelopes": len(well_formed),
                "invalid_envelopes": len(transport) - len(well_formed),
                "metadata_valid_responses": len(metadata_valid),
                "metadata_invalid_responses": len(well_formed) - len(metadata_valid),
                "well_formed_and_metadata_valid": len(metadata_valid),
                "invalid_envelope_or_metadata": len(transport) - len(metadata_valid),
                "responses_with_links": sum(
                    check.get("link_count", 0) > 0 for _, check in well_formed
                ),
                "responses_with_links_and_valid_metadata": sum(
                    check.get("link_count", 0) > 0 for _, check in metadata_valid
                ),
                "returned_links": len(links),
                "returned_links_response_denominator": len(well_formed),
                "individually_metadata_valid_links": sum(
                    link["relationship_status"] != "invalid-metadata"
                    for link in links
                ),
                "links_in_metadata_valid_responses": len(valid_response_links),
                "unknown_ids": sum(not link["known_id"] for link in links),
                "cross_arm_ids": sum(
                    link["known_id"] and not link["arm_specific_id"] for link in links
                ),
                "invalid_source_quotes": sum(
                    link["known_id"] and not link["exact_source_quote"] for link in links
                ),
                "uncertain_links": relationship_counts["uncertain"],
                "unsupported_literal_claims": relationship_counts[
                    "misleading-literal-claim"
                ],
                "outside_predeclared_applicability_links": sum(
                    link["applicability_observation"]
                    == "outside-predeclared-applicability"
                    for link in links
                ),
                "rule_compatible_unassessed": relationship_counts[
                    "rule-compatible-unassessed"
                ],
                "literal_overlap_confirmed": relationship_counts[
                    "literal-overlap-confirmed"
                ],
                "abstentions_all_responses": {
                    "numerator": sum(check.get("abstained") for _, check in well_formed),
                    "denominator": len(well_formed),
                },
                "abstentions_when_mapped_source_applicable": {
                    "numerator": sum(check["abstained"] for _, check in applicable),
                    "denominator": len(applicable),
                },
                "links_when_no_mapped_source_applicable": {
                    "numerator": sum(not check["abstained"] for _, check in no_applicable),
                    "denominator": len(no_applicable),
                },
                "grounded_answer_violation_responses": sum(
                    not check["grounded_answer_checks"]["passed"]
                    for _, check in well_formed
                ),
                "heuristic_alert_responses": sum(
                    bool(check["heuristic_answer_alerts"])
                    for _, check in well_formed
                ),
                "punctuation_sentence_alert_responses": sum(
                    any(
                        alert["kind"] == "punctuation-sentence-count"
                        for alert in check["heuristic_answer_alerts"]
                    )
                    for _, check in well_formed
                ),
                "article_absence_alert_responses": sum(
                    any(
                        alert["kind"] == "english-article-absence"
                        for alert in check["heuristic_answer_alerts"]
                    )
                    for _, check in well_formed
                ),
                "joining_whitespace_defect_responses": sum(
                    bool(check["joining_whitespace_defects"])
                    for _, check in well_formed
                ),
                "extraneous_source_copy_responses": sum(
                    bool(check["extraneous_source_copies"])
                    for _, check in well_formed
                ),
                "answer_chars": answers,
                "mean_answer_chars": (
                    answers / len(well_formed) if well_formed else None
                ),
                "metadata_chars": metadata,
                "mean_metadata_chars": (
                    metadata / len(well_formed) if well_formed else None
                ),
                "usage": {
                    "input_tokens_sum": sum(v for v in input_tokens if v is not None),
                    "output_tokens_sum": sum(v for v in output_tokens if v is not None),
                    "responses_with_real_usage": sum(v is not None for v in output_tokens),
                },
            }

    comparisons: dict[str, Any] = {}
    for model_label in design["models"]:
        comparisons[model_label] = {}
        for family in ("original", "semantic"):
            clean = metrics[model_label][f"{family}-clean"]
            tagged = metrics[model_label][f"{family}-tagged"]
            clean_rows = {
                (record["repetition"], record["case_id"]): (record, check)
                for record, check in grouped[(model_label, f"{family}-clean")]
                if check.get("envelope_valid")
            }
            tagged_rows = {
                (record["repetition"], record["case_id"]): (record, check)
                for record, check in grouped[(model_label, f"{family}-tagged")]
                if check.get("envelope_valid")
            }
            paired_keys = sorted(clean_rows.keys() & tagged_rows.keys())
            clean_answer_chars = sum(
                clean_rows[key][1]["answer_chars"] for key in paired_keys
            )
            tagged_answer_chars = sum(
                tagged_rows[key][1]["answer_chars"] for key in paired_keys
            )
            clean_metadata_chars = sum(
                clean_rows[key][1]["metadata_chars"] for key in paired_keys
            )
            tagged_metadata_chars = sum(
                tagged_rows[key][1]["metadata_chars"] for key in paired_keys
            )
            clean_output_tokens = sum(
                usage_tokens(clean_rows[key][0], "output_tokens") or 0
                for key in paired_keys
            )
            tagged_output_tokens = sum(
                usage_tokens(tagged_rows[key][0], "output_tokens") or 0
                for key in paired_keys
            )
            comparisons[model_label][family] = {
                "matched_reconstructable_pairs": len(paired_keys),
                "expected_pairs": scheduled[(model_label, f"{family}-clean")],
                "pair_membership": [
                    {"repetition": key[0], "case_id": key[1]} for key in paired_keys
                ],
                "clean_answer_chars": clean_answer_chars,
                "tagged_answer_chars": tagged_answer_chars,
                "answer_char_delta": tagged_answer_chars - clean_answer_chars,
                "clean_metadata_chars": clean_metadata_chars,
                "tagged_metadata_chars": tagged_metadata_chars,
                "metadata_char_delta": tagged_metadata_chars - clean_metadata_chars,
                "grounded_answer_violation_delta": (
                    tagged["grounded_answer_violation_responses"]
                    - clean["grounded_answer_violation_responses"]
                ),
                "clean_cli_output_tokens": clean_output_tokens,
                "tagged_cli_output_tokens": tagged_output_tokens,
                "cli_output_token_delta": tagged_output_tokens - clean_output_tokens,
            }

    attempts = [attempt for record in analyzable for attempt in record.get("attempts", [])]
    model_identities: dict[str, dict[str, Any]] = {}
    for record in analyzable:
        for name, details in (record.get("model_usage") or {}).items():
            if isinstance(details, dict):
                model_identities[name] = {
                    "canonical_model": details.get("canonicalModel"),
                    "provider": details.get("provider"),
                }
    result = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "matrix": audit,
        "publication_analysis_matrix_complete": audit["valid"],
        "models": design["models"],
        "actual_model_identities": model_identities,
        "metrics": metrics,
        "within_model_clean_vs_tagged": comparisons,
        "execution": {
            "attempts": len(attempts),
            "failed_or_timed_out_attempts": sum(
                attempt.get("exit_code") != 0 or attempt.get("timed_out")
                for attempt in attempts
            ),
            "attempts_with_repo_cwd": sum(
                not attempt.get("cwd_outside_repo", False) for attempt in attempts
            ),
        },
        "interpretation_limits": design["limits"],
        "independent_model_review": independent_review,
        "checks": checks,
    }
    write_json(
        output / ("aggregate.partial.json" if allow_partial else "aggregate.json"),
        result,
    )
    write_audit_packet(output, checks, source_map)
    write_all_tagged_segments_audit(
        output, analyzable, checks, source_map, independent_judgments
    )
    return result


def write_audit_packet(
    output: Path, checks: list[dict[str, Any]], source_map: dict[str, Any]
) -> None:
    links = [link for check in checks for link in check["links"]]
    reviewed = sum("independent_model_review" in link for link in links)
    packet = {
        "schema_version": 1,
        "independent_semantic_review": (
            "complete-independent-model-review" if reviewed == len(links) else "not-performed"
        ),
        "warning": (
            "Generator relation labels are not truth. Review segment, source fragment, "
            "case prompt, applicability, and independent answer invariants."
        ),
        "returned_link_count": len(links),
        "links": links,
    }
    write_json(output / "audit-packet.json", packet)
    lines = [
        "# V2 returned-link audit packet",
        "",
        f"Independent model-review judgments attached: **{reviewed}/{len(links)}**. "
        "They are not human ground truth or causal evidence.",
        "",
        f"Returned links: {len(links)}",
        "",
    ]
    for index, link in enumerate(links, 1):
        lines.extend(
            [
                f"## Link {index}: `{link['cell']}`",
                "",
                f"- Case: `{link['case_id']}`",
                f"- Relation: `{link['relation']}`",
                f"- Status: `{link['relationship_status']}`",
                f"- Rule ID: `{link['rule_id']}`",
                f"- Case applicable: `{link['case_applicable']}`",
                f"- Applicability observation: `{link['applicability_observation']}`",
                f"- Independent semantic review: `{link['independent_semantic_review']}`",
                f"- Independent model-review judgment: "
                f"`{link.get('independent_model_review', {}).get('judgment', 'not-reviewed')}`",
                f"- Independent model-review rationale: "
                f"{link.get('independent_model_review', {}).get('rationale', 'not reviewed')}",
                "- Output segment:",
                "",
                "```text",
                link["segment_text"],
                "```",
                "",
                "- Source fragment:",
                "",
                "```text",
                link["source_fragment"] or "<unknown>",
                "```",
                "",
                "- Claimed source quote:",
                "",
                "```text",
                link["claimed_source_quote"] or "<missing>",
                "```",
                "",
                "- Prompt:",
                "",
                "```text",
                link["prompt"],
                "```",
                "",
                f"- Exact source quote: `{link['exact_source_quote']}`",
                f"- Literal markers: `{link['literal_marker_matches']}`",
                "- Independent answer invariants passed: "
                f"`{link['independent_answer_checks']['grounded']['passed']}`",
                "- Independent answer invariant violations: "
                f"`{link['independent_answer_checks']['grounded']['violations']}`",
                "- Heuristic alerts: "
                f"`{link['independent_answer_checks']['heuristic_alerts']}`",
                "- Joining whitespace defects: "
                f"`{link['independent_answer_checks']['joining_whitespace_defects']}`",
                "- Extraneous source copies: "
                f"`{link['independent_answer_checks']['extraneous_source_copies']}`",
                "",
            ]
        )
    (output / "audit-packet.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--output", type=Path, required=True)
    smoke_parser.add_argument("--model", required=True)
    smoke_parser.add_argument("--timeout", type=float, default=120.0)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--stronger-identity", type=Path, required=True)
    prepare_parser.add_argument(
        "--haiku-model", default="claude-haiku-4-5-20251001"
    )
    prepare_parser.add_argument("--seed", type=int, default=2609162)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--workers", type=int, default=3)
    run_parser.add_argument("--timeout", type=float, default=120.0)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.add_argument("--allow-partial", action="store_true")
    analyze_parser.add_argument("--independent-review", type=Path)

    calibrate_parser = subparsers.add_parser("calibrate")
    calibrate_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "smoke":
            smoke(args)
        elif args.command == "prepare":
            freeze_design(args)
        elif args.command == "run":
            run_matrix(args)
        elif args.command == "analyze":
            analyze(
                args.output.resolve(),
                allow_partial=args.allow_partial,
                independent_review_path=args.independent_review,
            )
        else:
            run_calibration(args.output.resolve())
    except V2Error as error:
        print(f"v2 error: {error}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
