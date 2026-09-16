# Final independent review — v1 attribution study

## Verdict

**ACCEPT as completed exploratory research.** The corrected checker and report resolve prereview findings F1-F5. The retained 80-cell single-model pilot supports a candid no-go/inconclusive publication decision. Acceptance does not authorize a public method claim, production-skill change, MR, or blog follow-up.

No blocking finding remains. The study is intentionally small; cross-model evidence is not required to accept this clearly bounded negative/inconclusive result.

## Prior finding disposition

- **F1 resolved:** broad checks are labeled literal or narrow observable probes. They never become semantic attribution verdicts; case-applicable claims remain `needs-review`, and causal provenance remains unsupported.
- **F2 resolved:** provider transport success, strict envelope validity, and annotation validity have separate fields and totals. An invalid synthetic envelope produced `transport_success=1`, `valid_responses=0`, and `invalid_envelopes=1`.
- **F3 resolved:** strict analysis rejects missing, duplicate, unexpected, and identity-inconsistent rows. The prior repetition-99 attack now fails with `matrix mismatch`; partial mode is explicit and publication-ineligible.
- **F4 resolved:** auth, React, and neutral literals are recorded as post-collection narrow lexical probes and excluded from correctness and artifact-preservation totals. The 30 genuine artifact-preservation cells have zero violations; the three auth lexical misses remain diagnostics only.
- **F5 resolved:** the report explicitly states that current-original and historical-semantic fixtures differ in version, contract, granularity, and instrumentation, so this is not a pure compression or rewrite-benefit comparison.

## Direct evidence check

Independent reconstruction from the raw directory found 80 JSON records, 80 unique cells, 80 matching `results.json` records, and an exact match to the frozen schedule. All 80 records have provider status `success`; they contain 80 total attempts, zero failed or timed-out attempts, 80 valid envelopes, and zero invalid envelopes. Recomputed aggregation matches `aggregate.json` byte-for-byte apart from `generated_at`.

Report arm counts match the raw records: each arm has 16/16 transport successes and 16/16 valid envelopes. Original-instrumented has 3 annotated cells and 3 claims; 2 spans are structurally valid, 1 is case-applicable, and 2 claims are annotation failures. Semantic-instrumented has 9 annotated cells and 11 claims; 9 are structurally valid and case-applicable, with 2 annotation failures, 7 observable-probe passes, and 2 observable-probe failures. Clean/control arms emitted no annotations. Total emitted claims: 14.

## Annotation inspection

All 14 annotations were inspected against their raw answers, source map, and corrected checks:

- **Four demonstrably invalid claims:** three claimed spans do not occur in their answers (`r1-auth-near-example-semantic-instrumented`, `r2-auth-near-example-original-instrumented`, and `r2-auth-near-example-semantic-instrumented`); one exact-answer span uses a case-inapplicable original ID (`r1-exact-preservation-original-instrumented`).
- **One original literal compatibility check:** `r2-react-near-example-original-instrumented` has an exact unique span with the predeclared `` `useMemo` `` overlap. This is lexical compatibility, not semantic attribution.
- **Seven semantic narrow-probe passes:** the destructive-warning claim; two polarity claims; two Russian-language claims; and two exact-artifact claims. These are observable compatibility checks whose content was also requested by the user prompts.
- **Two semantic narrow-probe failures:** cache/XFetch and React/new-reference claims do not satisfy the applicable exact-artifact probe. A failed narrow probe does not itself prove the semantic association false.

The ten structurally valid, case-applicable claims remain semantically unassessed. All 14 claims remain unsupported model self-reports for causal provenance. The report states these distinctions accurately.

## Validation run

- `python3 -m unittest tests.test_attribution_pilot -v` — 15/15 passed on the final reviewed test file.
- Replayed prereview attacks: contradictory lexical overlap and broad whole-answer checks stay diagnostic and `needs-review`; empty-ground-truth exactness now fails; invalid envelopes are excluded from valid-response totals; unexpected matrix rows are rejected.
- Direct raw/result/schedule reconstruction and stored-aggregate comparison passed.
- Before, after, and final preservation manifests are identical. Independent recomputation matches their raw, input, and fixture directory digests.
- No live model calls were made.

## Publication and method boundary

The final report recommends no public claim because diagnostic coverage is sparse and independent semantic attribution was not established. The conditional public MR and separate blog follow-up must therefore not be published from this pilot. General instruction instrumentation, deterministic identifier insertion, optional reviewed semantic segmentation, structural validation, surface probes, and independent semantic assessment are correctly recorded as separate stages for future work; Caveman is only the case study.

## Reviewed evidence identity

Snapshot: `2026-09-16T11:23:33Z`. SHA-256:

- `evals/attribution_pilot.py`: `49dd94e31c91d2bb2dd6653452cbc4da59e81a0efd8fab70f1bf3cb416767ceb`
- `tests/test_attribution_pilot.py`: `049b17d2165c742b6a9eba4f3210e53dd46f0ee908f26a08e1d2886fed2bae45`
- `evals/attribution_pilot_analysis_corrections.json`: `e1ba3cecb4e712fa5c61aa72bee81b2ef22adce205eb15f4ad06f26ae3d5ba18`
- `evals/attribution_pilot_spec.json`: `52ae6cc0fe4bbab54c58550f703afb1e1101ac6e2506a7d9fc7293a3baeb89ab`
- `evals/prompts/attribution_pilot_cases.json`: `7b0ccc738494dce775d0363c3577bf071915564d92ab0b0b0d94fcef23ff34c5`
- `docs/v1-report.md`: `4ca088f14c0529d2c1e0cfcb37d647883be90ce5feda1dda91edbd999188eb66`
- `historical private rework outcome`: `bd1dedbe9444f54d671c32eab9a53492b08282efd8336afa92250892d87687c0`
- `artifacts/v1/aggregate.json`: `9647d975b12bf2bb522d58d9bf0ae0f397859d23b5e83139a2c01d12b2f1277f`
- `artifacts/v1/results.json`: `d11847b032509b66caaed85b99a4f3aa662d05dca704e4a846aeca960db4c3c1`
- `artifacts/v1/design-freeze.json`: `de9bc1f412b89f60dd8cb30a35d36b62f2e3ab595bfe2c3809e06a1bac4dc2cb`
- `artifacts/v1/source-map.json`: `35eed126fbb2369ac49117224271538d51c86cc2079e10af45a94105b56b4829`
- Raw directory, 80 files: manifest SHA-256 `46b48719db5b99af36ff065719c46bd4c0d0b640488d76862dad59951e3fb3c8`
- Model-facing inputs, 5 files: manifest SHA-256 `1d1bdd36ff51cbb3f26c9d3292e4f2a74c45f5c1b69cd483eb960ebebc91d08a`
- Generated fixtures, 4 files: manifest SHA-256 `8ce57e904b1ae32a618868f2da0a3b0f8e2b873005f5559460d861a466ca2bba`
- Each preservation manifest: `b46ee2f3e76d739189c9f57ceeaee7dfd07a7b3fd90b6bd3c4f83cc65bdf419c`

Directory manifest hashes are SHA-256 over sorted `shasum -a 256` lines, including relative paths.
