# Independent review — v2 attribution study

## Verdict

**REWORK.** V2 is a useful bounded source-aware output diagnostic, and the completed matrix/evidence are internally coherent. Segmentation removes nonexistent-span references by construction, preserves reconstructed natural text/code, and keeps abstention possible. The report correctly disclaims causal provenance, pure compression effects, cross-version improvement, cross-granularity link-count ranking, and publication.

Acceptance is blocked by three concrete interpretation defects: the observable calibration labels are not grounded in their original tasks, the report treats an applicability prior as a semantic verdict, and heuristic sentence/article probes are aggregated as grounded answer violations. These can be repaired offline; no new live calls or expanded study is required.

## Findings

### F1 — High: observable calibration is ungrounded label bookkeeping

- Locations: `evals/attribution_v2_calibration.json:83-116`, `evals/attribution_v2.py:860-913,964-993`, `tests/test_attribution_v2.py:398-421`, `docs/v2-report.md:256-266`.
- The `negation-reversal` fixture labels “must retry” contradicted without supplying an original task that required “must not retry.” The language fixtures label Russian output compatible without supplying the user's language. The scorer never examines segment, source, or task context; it maps supplied `expected_label` plus supplied `emitted` booleans into confusion-matrix cells. The test verifies those arithmetic results only.
- Reproduction: `scored_relationships` accepts two otherwise indistinguishable fixtures with opposite supplied labels and reports one TP plus one FP. The fixture file itself contains no `prompt`, required polarity, or required language fields.
- Impact: the reported 2 TP / 2 FP / 1 TN / 1 FN is not calibration of semantic classification. It is a bookkeeping test over assumed labels. The structural fixture results remain valid for structural acceptance/rejection.
- Recommended fix: add explicit original task/input and independently checkable expected facts to every preservation fixture; derive or independently assert the observable judgment from that context. Keep the confusion-matrix utility described as arithmetic/bookkeeping, not semantic calibration. Add negative controls where identical output changes judgment only because grounded task context changes.
- Repeat-of: none.

### F2 — High: applicability is treated as a semantic oracle

- Locations: `evals/attribution_v2.py:820-831`, `docs/v2-report.md:90-92,162-166`.
- The checker labels every known, exact-quote link outside `applicable_keys` as `misleading-not-applicable`, and the report calls the arithmetic example an “Incorrect relationship.” But `applicable_keys` is a design prior. The arithmetic prompt requires the exact string `17 × 19 = 323`; both Sonnet arithmetic links are observably compatible with the broad “keep all technical substance ... numbers and units” rule. That compatibility is non-discriminative and proves no source influence, but it is not semantically disproved by an empty prior.
- Independent result: of 27 emitted links, 18 are compatible, 7 contradicted, and 2 insufficient-evidence under the declared rubric. This differs from the automatic six-“misleading” count. Conversely, three exactness claims automatically left `rule-compatible-unassessed` are contradicted by explicit case-sensitive task failures, and four `literal-overlap` claims are contradicted by the actual full source fragment.
- Recommended fix: rename the automatic state to `outside-predeclared-applicability` (or equivalent) and keep it non-judgmental. Reserve `contradicted`/`misleading` for an independent contextual assessment. Update the report example and totals accordingly.
- Repeat-of: none.

### F3 — Medium: sentence/article regexes are reported as grounded violations

- Locations: `evals/attribution_v2.py:642-665`, `tests/test_attribution_v2.py:201-208`, `docs/v2-report.md:58-74,97-101`.
- `sentence_count` counts punctuation before whitespace/end, so `a.k.a.` creates extra “sentences.” The article check makes presence of `a|an|the` necessary for professional prose, which the task does not justify. These are useful probes, but neither is a sufficient or universally necessary prose assessment.
- Reproduction: `A cache stampede is also called dogpile (a.k.a. stampeding herd). request coalescing avoids it.` is two natural sentences satisfying both exact terms, but the checker reports three. This is the sole clear false positive among the 34 aggregate answer-violation responses (`stronger--r2-novel-cache-paraphrase-terse-control`). `Before migration, backup completes. After failure, users can restore data.` is grammatical, contains all required terms in two sentences, and fails only the article probe.
- The 48 tagged-response review found 17 genuine task violations: 14 responses violated explicitly case-sensitive exact phrases, four had missing whitespace between concatenated segments, and one response is in both groups. No tagged answer copied a source instruction, and no additional independently checkable answer violation was found.
- Recommended fix: report sentence/article outputs as probes, separately from grounded exact-answer/exact-artifact/language constraints. Do not include a probe failure in an “answer violation” total without manual or stronger task-specific confirmation. Add abbreviation and grammatical article-less positive controls.
- Repeat-of: none.

## Independent link and omission review

The complete claim table is in `v2-independent-link-review.json`. I inspected all 27 returned links using the actual segment, full source fragment, and task prompt, and inspected all 48 tagged responses / 56 segments for observable omissions and answer pollution.

| Independent judgment | Emitted links |
| --- | ---: |
| Compatible | 18 |
| Contradicted | 7 |
| Insufficient evidence | 2 |

Seventeen un-emitted relationships were independently observable under the bounded rubric: exact artifact/polarity preservation, explicitly Russian output, persisted-README prose, the React example's actual mechanism/remedy, and exact preservation of the arithmetic string. They are diagnostic omissions, not evidence that the model failed to use an instruction. No live precision/recall is reported because the remaining candidate pairs were not converted into claimed human ground truth; the JSON enumerates every emitted judgment and every rubric-positive omission.

Important examples:

- `stronger--r1-novel-cache-paraphrase-semantic-tagged` claims exactness while changing required lowercase `cache stampede` to `Cache stampede`: contradicted.
- `stronger--r2-novel-cache-paraphrase-semantic-tagged::segment-1` preserves `request coalescing`, but its claimed `literal-overlap` is false because that phrase is absent from the cited generic source.
- Both Sonnet semantic arithmetic links are broadly compatible with exact preservation even though the prior marks no mapped source applicable; they remain useless as provenance evidence.
- Both original React responses with emitted links are observably compatible with the full example, but the prompt itself supplies `inline object prop`, `new object reference`, and `useMemo`; the overlap cannot distinguish prompt from skill origin.
- No output contains a full copied source instruction. Segmented reconstruction exposed four tagged responses with missing inter-segment whitespace; schema validity alone does not guarantee unpolluted or natural answer text.

## Matrix, identity, denominator, and preservation checks

- Direct recount from all 120 raw records: 120 unique expected cells (2 models × 2 repetitions × 6 cases × 5 arms), no missing/unexpected/duplicate/inconsistent rows, 120 transport successes in 120 attempts, and no retry/fallback.
- Every per-cell raw JSON object is byte-semantically identical to its entry in `results.json`; all 120 strict envelopes reconstruct answers. Metadata is valid for 118 responses; two Russian tagged responses have truncated quotes.
- All-returned counts are preserved independently of metadata validity: 27 links in 15 responses, 23 individually metadata-valid links, and 22 links inside fully metadata-valid responses. Answer/metadata lengths use all 12 reconstructable responses per arm. Every clean/tagged comparison uses the same 12 `(case, repetition)` members, including metadata-invalid tagged answers.
- Requested models are exactly `claude-haiku-4-5-20251001` for 60 cells and `claude-sonnet-5` for 60 cells. Every stronger record exposes Sonnet 5 as the selected model. Auxiliary Haiku usage appears in 59 stronger records but is not selected as the main identity. No fallback/retry occurred.
- The design's cases, protocol, source map, and all five model-facing input hashes match current files. The before/after v2 preservation manifests are byte-identical and both validate the frozen design/results. The v1 immutability manifest validates every listed v1 report, design, map, fixture, input, aggregate, result, and raw record; v1 analysis changes remain distinguishable from its preserved live inputs/results.
- The report uses within-model clean/tagged comparisons only and explicitly disclaims isolated v1→v2 improvement, current-upstream versus historical-core compression effects, unequal map granularity, causal provenance, and publication. Public MR/article decisions remain deferred.

## Tests and bounded controls run

```bash
python3 -m unittest tests.test_attribution_pilot tests.test_attribution_v2 -v
python3 -m py_compile evals/attribution_v2.py
python3 -m json.tool artifacts/v2/independent-link-review.json >/dev/null
shasum -a 256 -c historical private immutability manifest
cmp -s artifacts/v2/post-run-frozen-before.sha256 artifacts/v2/post-run-frozen-after.sha256
shasum -a 256 -c artifacts/v2/post-run-frozen-after.sha256
```

Result: 34/34 focused v1+v2 tests passed. Read-only Python recounts re-ran matrix membership/identity validation, strict-envelope and link validation across all 120 records, per-arm aggregate comparisons, raw/result equality, all-link identity coverage, omission-candidate existence, and the bounded abbreviation/article/calibration controls described above. No live model call was made.

## Reviewed hashes (SHA-256)

| Artifact | SHA-256 |
| --- | --- |
| `evals/attribution_v2.py` | `4b5bb8b64f054116f7aad8778790614b66ae99dcf54f452d61484b854c456150` |
| `tests/test_attribution_v2.py` | `e3a75393de8efd386734489bb59c1a2c585b7d7b2a7aae59c29847e3db698a1f` |
| `evals/attribution_v2_calibration.json` | `22585b3b0ff2c2a56fd9b844423b21744e6eb461d042e19e722126a45f054ba0` |
| `evals/attribution_v2_protocol.json` | `0aca90398206e9727fcd15d347d7a4336c65f1177d2f475341b10fce5c7ec1c5` |
| `evals/prompts/attribution_v2_cases.json` | `d4e9dfbaaf41ae769a618668ec918838ddad590a18daffd16626593d1cba7b1f` |
| `docs/v2-report.md` | `67627342c083da16b69df045247fcdbbd3511c672188db19911689758140e265` |
| `artifacts/v2/design-freeze.json` | `3548cb3f8109944c95a45d3290c1b8f312f5d9f1caf33d2ee2b6a8183aedf74f` |
| `artifacts/v2/source-map.json` | `0d31ab6631fed840bad4390c3203bbf36fc818b6b57efd57f60753cfadfaa3af` |
| `artifacts/v2/results.json` | `3f2d3ba3db71287a0e7296ecc956bc0cd2ade4db060e3beda779065c6ddd2ec8` |
| `artifacts/v2/aggregate.json` | `d9c4b4759ef9fa1eca840887a3b30b5c921f42edc5139c27dfad9e80b0b9a26c` |
| `artifacts/v2/audit-packet.json` | `b201af38eeb0f58902e05e2884abed65670a1743a3c6841db80a579fd6abe3e9` |
| `artifacts/v2/all-tagged-segments-audit.json` | `cba5d122f3d44274e158662c3f58fab4c4afcf0f246d6161cb3c0cd76b9ead3f` |
| `artifacts/v2/calibration.json` | `d7e2791e70164fe09b104be8c093149f2b05b43f6e9c57878a568d406d5cdfb9` |
| `artifacts/v2/stronger-model-identity.json` | `b4e730695c2f70935c78e991b42b4030923518c5d5d971ff49698b398239caa7` |
| `artifacts/v2/post-run-frozen-before.sha256` | `46ef6797b312dd85a441b961096f35264917b7d7e8e56e1c64dc9b90d7c20678` |
| `artifacts/v2/post-run-frozen-after.sha256` | `46ef6797b312dd85a441b961096f35264917b7d7e8e56e1c64dc9b90d7c20678` |
| `historical private immutability manifest` | `dfb283c5b0039b4502f552796ff7c6d0a5b2a360a5a65757074a58bd47ff54f7` |

No source, frozen input, evidence, task status, commit, public message, MR, or article was changed by this review.
