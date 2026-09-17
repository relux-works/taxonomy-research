# Taxonomy research: observable instruction diagnostics

This repository is a portable, offline publication of two exploratory Caveman
instruction-diagnostic studies. V1 contains 80 completed cells; v2 contains 120
completed cells and 27 emitted links. Independent model review classified those
links as 18 compatible, 7 contradicted, and 2 insufficient-evidence, with 17
observable omissions.

These are descriptive, noncausal diagnostics. They do not expose private
reasoning, establish instruction provenance, support global precision/recall,
or show that one instruction version caused an answer. The current-original
and historical-semantic sources are version-confounded. Clean and tagged arms
share a segmented envelope, so their difference estimates incremental metadata
overhead, not overhead against an unstructured production response.

Research authors: Alexis Grigoryev and Ivan Oparin.

Background: [Caveman](https://github.com/JuliusBrussee/caveman) and the Relux
article [Semantic Core Instead of Phrasebooks](https://relux.works/en/blog/semantic-core-instead-of-phrasebooks/).

## Repository map

- `evals/`: preserved v1/v2 evaluators, case sets, protocols, calibration, and
  the concise instruction-diagnostics method.
- `fixtures/sources/`: an exact pinned current-upstream snapshot and an exact
  unmerged historical research candidate, stored as inert fixtures rather than
  installable skills. `fixtures/negative/` holds deliberate bad hash/anchor test
  inputs.
- `artifacts/v1/` and `artifacts/v2/`: frozen designs, source maps, exact system
  inputs/fixtures, allowlisted response projections, calibrated aggregates, and
  independent judgments.
- `docs/`: candid study reports, independent reviews, and the explicitly
  unexecuted synthetic-robustness proposal.
- `tools/`: deterministic export and public-release verification.
- `tests/`: the original 38 focused tests plus portability/privacy gates.

## Requirements and offline verification

Python 3.11 or newer is sufficient; the repository has no third-party runtime
dependencies. From the repository root:

```sh
python3 -m unittest discover -s tests -p 'test*.py' -v
python3 tools/check_public_release.py --root .
```

Reproduce the accepted analyses without Git objects, the Caveman checkout, or
network access:

```sh
work_dir="$(mktemp -d)"
cp -R artifacts/v1 "$work_dir/v1"
cp artifacts/v1/results.public.json "$work_dir/v1/results.json"
python3 evals/attribution_pilot.py analyze --output "$work_dir/v1"

cp -R artifacts/v2 "$work_dir/v2"
cp artifacts/v2/results.public.json "$work_dir/v2/results.json"
python3 evals/attribution_v2.py analyze \
  --output "$work_dir/v2" \
  --independent-review artifacts/v2/independent-link-review.json
```

Generated reproduction outputs stay under the caller-owned `work_dir`. The
committed accepted artifacts remain unchanged.

Live execution is deliberately not part of CI or reproduction. Commands named
`smoke` and `run` may invoke a configured model CLI and therefore require an
explicit, informed opt-in, provider credentials, and a separate output
directory. Nothing in this repository authorizes new model calls.

## Public export and provenance

`results.public.json` files are allowlisted projections, not copies of the
private raw provider wrappers. Answer/segment text and annotations/links are
preserved, together with experiment identity, model identity, relevant numeric
usage, and safe attempt status. Provider stdout/stderr, session/request IDs,
timestamps, local paths, transcripts, orchestration state, logs, and credentials
are excluded. `artifacts/projection-manifest.json` records the private raw byte
hash, the changed public-export hash, record counts, and a digest of preserved
response content. The offline gate validates the public hashes and schema; it
does not claim that sanitized bytes equal raw bytes.

The source snapshot hashes and upstream locations are documented in
`THIRD_PARTY_NOTICES.md`. Imported research code remains MIT-licensed.

## License

This repository is licensed under the Apache License, Version 2.0; see
`LICENSE` and `NOTICE`. Code and inert snapshots derived from Caveman keep
their MIT notice in `THIRD_PARTY_NOTICES.md`.

## Tools

- `python3 -m unittest discover -s tests -p 'test*.py' -v`: runs focused behavior, negative, portability, and
  privacy tests; normal cache files are ignored.
- `python3 evals/attribution_pilot.py analyze --output DIR`: regenerates v1
  derived analysis into `DIR` from copied public inputs.
- `python3 evals/attribution_v2.py analyze --output DIR --independent-review FILE`:
  regenerates v2 analysis and audit packets into `DIR`.
- `python3 tools/check_public_release.py --root .`: checks the actual Git release
  candidate (or every file in an archive without `.git`) for forbidden agent
  files, known credential filenames, representative high-confidence credential
  formats, private paths, provider wrappers, projection drift, and source drift.
  This bounded gate is not a claim of universal secret detection.
- `python3 tools/export_public.py --v1-raw FILE --v2-raw FILE --root .`: maintainer
  tool for rebuilding allowlisted projections from authorized private raw
  evidence; outputs go to `artifacts/`. It is not needed for reproduction.

## Roadmap boundary

`docs/roadmap/synthetic-robustness-proposal.md` is a proposed future protocol.
It records neither completed work nor authorization to run new experiments.
