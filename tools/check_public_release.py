#!/usr/bin/env python3
"""Validate the public release candidate without consulting private sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from export_public import ATTEMPT, MODEL_USAGE, TOP_LEVEL, USAGE, content_view, digest


FORBIDDEN_PATH_PARTS = {
    ".task-board", "task-board.config.json", ".agents", ".codex", ".claude",
    ".roles", "agents", "GEMINI.md", "QWEN.md", ".cursor", ".cursorrules",
    "copilot-instructions.md", ".mcp.json", ".planning",
    "agents-attachments-manifest.json",
}
CREDENTIAL_FILENAMES = {"credentials.json", ".env"}
CREDENTIAL_SUFFIXES = {".pem", ".key"}
TEXT_PATTERNS = {
    "absolute local path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "task-board identifier": re.compile(r"\b(?:TASK|STORY|EPIC|RUN)-\d{6}-[a-z0-9]+\b"),
    "session UUID field": re.compile(r'"(?:session_id|uuid)"\s*:'),
}
CREDENTIAL_CONTENT_PATTERNS = {
    "private-key material": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"
    ),
    "OpenAI-style API key": re.compile(
        r"\bsk-(?:(?:proj|svcacct)-)?[A-Za-z0-9_-]{20,}\b"
    ),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "bearer credential": re.compile(
        r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~-]{20,}"
    ),
}


def candidate_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root, text=True, capture_output=True, check=True,
        )
        return sorted(root / line for line in result.stdout.splitlines() if line)
    return sorted(path for path in root.rglob("*") if path.is_file())


def forbidden_release_path(path: Path) -> bool:
    return any(part in FORBIDDEN_PATH_PARTS for part in path.parts) or any(
        re.fullmatch(r"(?:AGENTS|CLAUDE).*\.md", part) for part in path.parts
    )


def forbidden_credential_path(path: Path) -> bool:
    name = path.name
    if name in CREDENTIAL_FILENAMES or name in {".env.local", ".env.production"}:
        return True
    if name.startswith(".env.") and name != ".env.example":
        return True
    return path.suffix.lower() in CREDENTIAL_SUFFIXES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contains_provider_wrapper(value: Any) -> bool:
    if isinstance(value, dict):
        return bool({"stdout", "stderr"} & set(value)) or any(
            contains_provider_wrapper(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(contains_provider_wrapper(item) for item in value)
    return False


def validate_projection(root: Path, entry: dict[str, Any], allowed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    path = root / entry["projection_path"]
    records = json.loads(path.read_text())
    if len(records) != entry["record_count"]:
        errors.append(f"{path}: record count mismatch")
    if sha256(path) != entry["projection_sha256"]:
        errors.append(f"{path}: projection hash mismatch")
    content_hash = digest(content_view(records))
    if entry["raw_allowed_content_sha256"] != entry["projection_allowed_content_sha256"]:
        errors.append(f"{path}: raw-to-projection content hash mismatch")
    if content_hash != entry["projection_allowed_content_sha256"]:
        errors.append(f"{path}: allowed response content hash mismatch")
    top = set(allowed["top_level"]) | {"attempts", "usage", "model_usage"}
    for index, row in enumerate(records):
        extra = set(row) - top
        if extra:
            errors.append(f"{path}:{index}: forbidden top-level fields {sorted(extra)}")
        for attempt in row.get("attempts", []):
            extra = set(attempt) - set(allowed["attempt"])
            if extra:
                errors.append(f"{path}:{index}: forbidden attempt fields {sorted(extra)}")
        if set(row.get("usage", {})) - set(allowed["usage"]):
            errors.append(f"{path}:{index}: forbidden usage field")
        for details in row.get("model_usage", {}).values():
            if set(details) - set(allowed["model_usage"]):
                errors.append(f"{path}:{index}: forbidden model usage field")
    return errors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    files = candidate_files(root)
    for path in files:
        rel = path.relative_to(root)
        if forbidden_credential_path(rel):
            errors.append(f"forbidden credential path: {rel}")
            continue
        if forbidden_release_path(rel):
            errors.append(f"forbidden release path: {rel}")
            continue
        if path.suffix.lower() not in {".md", ".json", ".py", ".txt", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in TEXT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{rel}: {label}")
        for label, pattern in CREDENTIAL_CONTENT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{rel}: detected {label}")
        if rel.parts[:1] == ("artifacts",):
            wrapper_found = bool(re.search(r'"(?:stdout|stderr)"\s*:', text))
            if path.suffix.lower() == ".json":
                try:
                    wrapper_found = wrapper_found or contains_provider_wrapper(json.loads(text))
                except json.JSONDecodeError:
                    errors.append(f"{rel}: malformed JSON")
            if wrapper_found:
                errors.append(f"{rel}: provider wrapper field")
    manifest = json.loads((root / "artifacts/projection-manifest.json").read_text())
    for entry in manifest["exports"]:
        errors.extend(validate_projection(root, entry, manifest["allowed"]))
    source_hashes = {
        "fixtures/sources/caveman-current.md": "0bf09a0a9a017d004a81d4b693e5a2d830e1a28230a5885df773e1ed9c0571cc",
        "fixtures/sources/caveman-historical.md": "86c684041a49da815c9fa5e34e161e36467dd09030986522aaab580fc212ae1c",
    }
    for rel, expected in source_hashes.items():
        if sha256(root / rel) != expected:
            errors.append(f"{rel}: pinned source hash mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = check(args.root.resolve())
    if errors:
        print("\n".join(errors))
        return 1
    print("public release candidate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
