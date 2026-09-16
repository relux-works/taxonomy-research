# Focused final re-review — v2 attribution study

## Verdict

**ACCEPT as bounded diagnostic research and implementation.** This accepts the corrected source-aware instruction diagnostic, its preserved exploratory evidence, and its candid negative/limited interpretation. It is not global validation of the method, proof of causal provenance, a semantic-precision claim, or publication approval. Public MR/article decisions remain deferred.

No live calls, new study, or repeat of the completed 27-link / 48-response audit was needed. The immutable independent judgments were reused at SHA-256 `3ed569d02f17a79647fe59ca799d5ba4ba9f3cd56ed7d91f5daef6c9286a2674` after the complete frozen v2 manifest validated the design, source map, fixtures, five model-facing inputs, all 120 raw records, and `results.json`.

## F1–F3 closure

- **F1 resolved — repeat-of: original F1.** Fixtures now include explicit task input and declared literal/artifact/polarity/language properties (`evals/attribution_v2_calibration.json:13-23`). The narrow observer derives judgments without reading `expected_label` (`evals/attribution_v2.py:1008-1041`); mutating a fixture's expected label left its observation unchanged. Same-output polarity and language pairs switch judgment only with changed task context. Confusion matrices are explicitly bookkeeping over this observer, not semantic classification (`evals/attribution_v2.py:1091-1147`, `docs/v2-report.md:254-279`). Insufficient evidence is excluded from binary denominators; independent controls confirmed both zero precision and zero recall denominators return undefined, while always-positive and always-empty strategies fail.
- **F2 resolved — repeat-of: original F2.** Applicability now emits neutral `inside/outside-predeclared-applicability` telemetry and never changes a valid relationship into a semantic rejection (`evals/attribution_v2.py:818-875`). The report calls it a routing prior, treats literal checks separately, and attributes 18 compatible / 7 contradicted / 2 insufficient judgments plus 17 observable omissions to immutable independent model review—not human truth, provenance, or causal false negatives (`docs/v2-report.md:12-23,77-105,281-288`). Live precision/recall remains undefined because the complete negative universe was not independently labeled.
- **F3 resolved — repeat-of: original F3.** Exact answer/artifact and explicit-language checks are grounded; punctuation sentence count and article presence are separate alerts that cannot alter grounded pass/fail (`evals/attribution_v2.py:642-685`). Regression controls keep the `a.k.a.` two-sentence answer and grammatical article-less prose grounded-valid while emitting heuristic alerts (`tests/test_attribution_v2.py:204-216`). Punctuation-to-word segment joins are a separate direct defect (`evals/attribution_v2.py:688-705`); the corrected aggregate retains seven matrix-wide join defects and the report explicitly retains four tagged defects rather than hiding them.

No repeated or new blocking finding remains.

## Method card

`evals/instruction_diagnostics.md` is concise and reusable. It freezes exact source units/maps and task contracts; makes assisted semantic segmentation optional and separately reviewed/frozen; requires matched model generation only for the behavior being evaluated; separates structural, grounded, heuristic, and independent semantic work; audits emitted and omitted relationships; defines FP/FN units, denominators, uncertainty, and zero-denominator behavior; limits comparisons to identical reconstructable pairs; includes paired task perturbations and provider-cost measurement; and applies an explicit usefulness/publication gate. It correctly states that clean segmented arms isolate incremental tagging/link burden, not total overhead against unstructured production, and that causal attribution is out of scope (`evals/instruction_diagnostics.md:3-55`). `evals/README.md:130-185` links the card and distinguishes optional independent review from deterministic analysis/calibration.

## Focused validation

Commands run:

```bash
python3 -m unittest tests.test_attribution_v2 -v
python3 -m py_compile evals/attribution_v2.py
python3 -m json.tool evals/attribution_v2_calibration.json >/dev/null
python3 -m json.tool artifacts/v2/calibration.json >/dev/null
shasum -a 256 -c artifacts/v2/f1-f3-frozen-before.sha256
shasum -a 256 -c historical private immutability manifest
shasum -a 256 -c historical private pre-rework archive/manifest.sha256
```

Result: 23/23 focused v2 tests passed. Read-only bounded controls independently checked observer/expected-label separation, polarity/language paired contexts, insufficient-only and both zero-denominator cases, neutral applicability, abbreviation/article-less positives, join-defect detection, exact 120-cell membership, current aggregate counts, and exact independent-review integration. No evidence or source was rewritten during re-review.

Preserved evidence:

- Frozen design: `3548cb3f8109944c95a45d3290c1b8f312f5d9f1caf33d2ee2b6a8183aedf74f`
- Frozen results: `3f2d3ba3db71287a0e7296ecc956bc0cd2ade4db060e3beda779065c6ddd2ec8`
- Frozen source map: `0d31ab6631fed840bad4390c3203bbf36fc818b6b57efd57f60753cfadfaa3af`
- Original independent review: `3ed569d02f17a79647fe59ca799d5ba4ba9f3cd56ed7d91f5daef6c9286a2674`
- Pre-F1–F3 derived-history manifest: `f69836ddbe5267d455657cb1863265a68ba7aea2b1c6e6061452ff1ea6cff4e1`

Final reviewed hashes:

| Artifact | SHA-256 |
| --- | --- |
| `evals/attribution_v2.py` | `b392afd1e5cce887f472e69054a92685bbc118781efa32e482947bb0eaf9d198` |
| `tests/test_attribution_v2.py` | `71e59ae8e9833656bbdc1aa61bc1d6922022299e4e42aa1e192d0d94f72a1208` |
| `evals/attribution_v2_calibration.json` | `a0405b999638df403883d251a04f3496e01ecc9f6f6ddfbaeaa06d224263f868` |
| `evals/instruction_diagnostics.md` | `4bedd8649bc305f2a3035945658e6506c59d74255a061a9bcb8c759aa4170d9a` |
| `docs/v2-report.md` | `a5abef160df00b049adadc25e2dacb471aeb6170f6fe8c89bc1ca2a4baa15394` |
| `artifacts/v2/aggregate.json` | `65e7e7950913d5bf0b1da466cd1edc96de0c89ac5cacaf1f3cc943c54052e126` |
| `artifacts/v2/calibration.json` | `d49e1f37154a612796d2f74abdb7e4be30b9af5a4f391f5c25b462cd36901347` |

Task status and closure remain with the parent. This re-review created no commit, public message, MR, article, managed run, or CR acceptance.
