#!/usr/bin/env python3
"""Create and verify allowlisted public projections of historical eval records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


TOP_LEVEL = (
    "cell", "model_label", "requested_model", "arm", "case_id", "repetition",
    "status", "response",
)
USAGE = (
    "input_tokens", "output_tokens", "cache_creation_input_tokens",
    "cache_read_input_tokens", "output_tokens_details", "service_tier", "speed",
)
MODEL_USAGE = (
    "canonicalModel", "provider", "inputTokens", "outputTokens",
    "cacheReadInputTokens", "cacheCreationInputTokens", "thinkingTokens",
)
ATTEMPT = ("attempt", "exit_code", "timed_out", "cwd_outside_repo")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def project_record(record: dict[str, Any]) -> dict[str, Any]:
    projected = {key: record[key] for key in TOP_LEVEL if key in record}
    projected["attempts"] = [
        {key: attempt[key] for key in ATTEMPT if key in attempt}
        for attempt in record.get("attempts", [])
    ]
    projected["usage"] = {
        key: record.get("usage", {})[key]
        for key in USAGE
        if key in record.get("usage", {})
    }
    projected["model_usage"] = {
        name: {key: details[key] for key in MODEL_USAGE if key in details}
        for name, details in record.get("model_usage", {}).items()
        if isinstance(details, dict)
    }
    return projected


def project_records(records: Any) -> list[dict[str, Any]]:
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("raw results must be an array of objects")
    return [project_record(row) for row in records]


def content_view(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "cell": row.get("cell"),
            "response": row.get("response"),
            "status": row.get("status"),
        }
        for row in records
    ]


def write_projection(raw_path: Path, output_path: Path, version: str) -> dict[str, Any]:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    if not isinstance(raw, list) or not all(isinstance(row, dict) for row in raw):
        raise ValueError("raw results must be an array of objects")
    raw_allowed_content_sha256 = digest(content_view(raw))
    projected = project_records(raw)
    projection_allowed_content_sha256 = digest(content_view(projected))
    if raw_allowed_content_sha256 != projection_allowed_content_sha256:
        raise ValueError("projector changed cell, status, or response content")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(projected, ensure_ascii=False, indent=2) + "\n")
    return {
        "version": version,
        "record_count": len(projected),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "projection_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "raw_allowed_content_sha256": raw_allowed_content_sha256,
        "projection_allowed_content_sha256": projection_allowed_content_sha256,
        "projection_path": output_path.relative_to(output_path.parents[2]).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-raw", type=Path, required=True)
    parser.add_argument("--v2-raw", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    entries = [
        write_projection(args.v1_raw, root / "artifacts/v1/results.public.json", "v1"),
        write_projection(args.v2_raw, root / "artifacts/v2/results.public.json", "v2"),
    ]
    manifest = {
        "schema_version": 1,
        "projection_policy": "allowlist-v1",
        "notice": "Public projections are not byte-identical to private provider wrappers.",
        "excluded": [
            "provider stdout/stderr wrappers", "session and request identifiers",
            "timestamps", "local paths", "agent transcripts and launch logs",
        ],
        "allowed": {
            "top_level": list(TOP_LEVEL), "usage": list(USAGE),
            "model_usage": list(MODEL_USAGE), "attempt": list(ATTEMPT),
        },
        "exports": entries,
    }
    (root / "artifacts/projection-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
