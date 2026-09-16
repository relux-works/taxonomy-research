# General instruction diagnostics v2 report

## Verdict

V2 is useful as an **internal source-aware output diagnostic**, but this run
does not establish semantic precision or causal attribution. The segment
envelope fixes v1's out-of-answer span failure class: answer text is derived
only by concatenating returned segments, and empty links remain valid. Exact
ID, arm, quote, literal-overlap, answer-invariant, and matrix checks are
independently auditable.

The live result also exposes an important limitation. Haiku mostly abstained,
while Sonnet linked nearly every semantic-tagged response. Generator labels
therefore cannot be treated as truth. Independent model review assessed all 27
emitted links as 18 compatible, 7 contradicted, and 2 insufficient-evidence,
and identified 17 observable omissions. Those judgments are not human ground
truth or causal evidence. No live precision/recall is reported because the
complete negative candidate universe was not independently labeled.

Recommendation: retain v2 as a bounded diagnostics prototype. Do not present this run as proof
of provenance, compression superiority, semantic precision, or a globally
accepted/rejected method. Public MR/article decisions remain deferred; a later
article could accurately discuss the diagnostic design and its failure modes.

## Frozen design and execution

- Six predeclared cases: real original example, novel paraphrase, exact
  artifacts/negation, Russian handling, normal-prose artifact, and ordinary
  no-applicable-source arithmetic.
- Five arms per model: terse control, original clean/tagged, semantic
  clean/tagged. Two repetitions produce 120 scheduled cells.
- Models: `claude-haiku-4-5-20251001` and `claude-sonnet-5`. The latter was
  discovered by one isolated `sonnet` smoke and then pinned. The same smoke's
  `modelUsage` also exposed an auxiliary Haiku entry; a readiness-stage selector
  bug initially chose that longer key, then was corrected from the preserved
  smoke without another model call.
- Seed: `2609162`; Claude CLI: `2.1.273`; maximum concurrency: 3; per-call
  timeout: 120 seconds; initial attempt plus at most three bounded retries.
- All calls used explicit model/system inputs, temporary cwd outside the repo,
  safe/restricted mode, empty settings/tools, strict MCP config, and no session
  persistence.
- Execution completed 120/120 cells in 120 attempts: no failures, timeouts,
  retries, missing/unexpected/duplicate rows, inconsistent cell IDs, or repo
  cwd executions. Both pinned identities were confirmed in live `modelUsage`.
- Design SHA-256:
  `3548cb3f8109944c95a45d3290c1b8f312f5d9f1caf33d2ee2b6a8183aedf74f`.
  Results SHA-256:
  `3f2d3ba3db71287a0e7296ecc956bc0cd2ade4db060e3beda779065c6ddd2ec8`.

The v1 pinned original/current and historical-core fixture builder was reused
inside the separate v2 evidence directory. Current and historical sources are
different versions and contracts, so original-versus-semantic does not isolate
compression. Cross-v1/v2 comparison is exploratory because the response
protocol and case set changed.

## Results

Every arm returned 12/12 structurally well-formed segment envelopes. `Meta`
means the exact IDs, source quotes, relations, and arm constraints also passed.
Grounded failures below use only exact answer/artifact and explicit language
contracts. Sentence-count and article-presence regexes are separate heuristic
alerts. `Join` is a direct punctuation-to-word segment-boundary defect.

| Model | Arm | Envelope | Meta | Links | Outside prior | Unsupported literal | Grounded failures | Heuristic alerts | Join defects |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Haiku | terse control | 12/12 | 12/12 | 0 | 0 | 0 | 2/12 | 1/12 | 1/12 |
| Haiku | original clean | 12/12 | 12/12 | 0 | 0 | 0 | 2/12 | 0/12 | 0/12 |
| Haiku | original tagged | 12/12 | 12/12 | 0 | 0 | 0 | 4/12 | 1/12 | 1/12 |
| Haiku | semantic clean | 12/12 | 12/12 | 0 | 0 | 0 | 4/12 | 0/12 | 0/12 |
| Haiku | semantic tagged | 12/12 | 11/12 | 3 | 0 | 0 | 3/12 | 1/12 | 1/12 |
| Sonnet | terse control | 12/12 | 12/12 | 0 | 0 | 0 | 0/12 | 1/12 | 0/12 |
| Sonnet | original clean | 12/12 | 12/12 | 0 | 0 | 0 | 2/12 | 1/12 | 1/12 |
| Sonnet | original tagged | 12/12 | 12/12 | 3 | 0 | 1 | 3/12 | 2/12 | 2/12 |
| Sonnet | semantic clean | 12/12 | 12/12 | 0 | 0 | 0 | 3/12 | 1/12 | 1/12 |
| Sonnet | semantic tagged | 12/12 | 11/12 | 21 | 3 | 2 | 4/12 | 0/12 | 0/12 |

Across all 27 returned links:

- 27/27 used known, arm-specific IDs; there were no unknown or cross-arm IDs.
- 23/27 copied the complete reviewed source quote exactly. Four links in two
  Russian responses truncated the quote and invalidated those responses'
  metadata, without removing their independent answer checks.
- All-emitted versus valid-only counts are explicit: Haiku semantic tagged
  returned 3 links, 1 individually valid, and 0 inside a fully metadata-valid
  response; Sonnet original tagged returned 3/3/3; Sonnet semantic tagged
  returned 21/19/19. Thus the totals are 27 emitted, 23 individually valid,
  and 22 contained in fully metadata-valid responses.
- One literal-overlap claim had a configured distinctive overlap; three lacked
  that narrow marker. This lexical probe is not a semantic verdict.
- Three links were outside the predeclared applicability prior. This is neutral
  telemetry, not evidence that the relationships were false.
- Immutable independent model review (`SHA-256
  3ed569d02f17a79647fe59ca799d5ba4ba9f3cd56ed7d91f5daef6c9286a2674`)
  assessed 18 emitted links compatible, 7 contradicted, and 2 insufficient.
  It also recorded 17 observable omissions, not causal false negatives.
- No model used the explicit `uncertain` relation. An empty links list, rather
  than a forced link, was common for Haiku and all clean/control arms.

Across the 48 tagged responses, grounded automatic checks identify the same 14
case-sensitive exact-phrase failures reported by independent review. Four
responses have missing inter-segment whitespace; one overlaps the exact-failure
group, producing 17 unique independently confirmed tagged violations. No tagged
answer copied a full source instruction. Sentence/article alerts are not added
to these grounded totals; the `a.k.a.` response is retained as the known
sentence-regex false positive.

## Answer and metadata length

All denominators below are 12 reconstructable, well-formed responses per row.
Every clean/tagged delta uses the identical 12/12 `(case, repetition)` members,
including tagged answers whose link metadata was invalid. Metadata characters
are the exact compact JSON length of segment `links`, so an empty `[]`
contributes two characters. CLI output tokens cover the complete provider
response and cannot be split exactly into answer versus metadata tokens.

| Model | Arm | Answer chars | Metadata chars | CLI output tokens |
| --- | --- | ---: | ---: | ---: |
| Haiku | terse control | 2,503 | 26 | 4,828 |
| Haiku | original clean | 1,727 | 26 | 9,162 |
| Haiku | original tagged | 1,835 | 26 | 9,235 |
| Haiku | semantic clean | 1,719 | 24 | 8,037 |
| Haiku | semantic tagged | 1,967 | 491 | 10,059 |
| Sonnet | terse control | 3,036 | 24 | 1,955 |
| Sonnet | original clean | 1,881 | 26 | 2,347 |
| Sonnet | original tagged | 1,876 | 556 | 3,515 |
| Sonnet | semantic clean | 1,771 | 26 | 2,181 |
| Sonnet | semantic tagged | 1,715 | 4,813 | 5,051 |

Within-model tagged-minus-clean deltas were: Haiku original `+108` answer,
`+0` metadata, `+73` CLI output tokens; Haiku semantic `+248`, `+467`,
`+2,022`; Sonnet original `-5`, `+530`, `+1,168`; Sonnet semantic `-56`,
`+4,787`, `+2,870`. These are protocol overhead observations, not a ranking of
broad semantic rules against narrow original examples.

## Representative complete responses

### Mechanically valid and independently compatible

`stronger--r1-exact-negation-artifacts-semantic-tagged` preserved all explicit
artifacts and exact negation, used valid IDs and complete quotes, and produced
two model-reported compatibility links. Independent model review judged both
compatible with the explicit artifact/polarity task; this still does not prove
provenance.

```json
{
  "segments": [
    {
      "text": "`v2.4.1` reads `/srv/app/config.yaml`, hits `E_CONN_RESET` at `250 ms`, must not retry.",
      "links": [
        {
          "rule_id": "EVS-17D60B4C-01",
          "relation": "rule-compatible",
          "source_quote": "Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units."
        },
        {
          "rule_id": "EVS-17D60B4C-02",
          "relation": "rule-compatible",
          "source_quote": "Never drop not/never/no/only/except: polarity and limits control meaning."
        }
      ]
    }
  ]
}
```

### Outside prior but independently compatible

`stronger--r2-ordinary-unlinked-semantic-tagged` answered correctly and linked
the arithmetic output to a broad exactness rule outside the predeclared
applicability prior. Independent model review judged it observably compatible
because the exact required string was preserved, while also noting that the
generic match is non-discriminative and proves no source influence.

```json
{
  "segments": [
    {
      "text": "17 × 19 = 323",
      "links": [
        {
          "rule_id": "EVS-17D60B4C-01",
          "relation": "rule-compatible",
          "source_quote": "Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units."
        }
      ]
    }
  ]
}
```

### Ordinary valid unlinked answer

`haiku--r1-ordinary-unlinked-original-tagged` demonstrates explicit abstention:

```json
{
  "segments": [
    {
      "text": "17 × 19 = 323",
      "links": []
    }
  ]
}
```

### Invalid exact quote retained for audit

`stronger--r2-russian-language-semantic-tagged` returned natural Russian text,
but both claimed quotes were truncated and both literal-overlap claims lacked a
configured distinctive marker. The envelope remains well formed; metadata is
invalid and answer checks remain independently counted.

```json
{
  "segments": [
    {
      "text": "HTTP 429 требует exponential backoff — иначе повторные запросы подряд лишь усиливают перегрузку сервера.",
      "links": [
        {
          "rule_id": "EVS-17D60B4C-01",
          "relation": "literal-overlap",
          "source_quote": "Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units."
        }
      ]
    },
    {
      "text": " Используй Retry-After: жди указанное в нём время перед следующей попыткой.",
      "links": [
        {
          "rule_id": "EVS-17D60B4C-01",
          "relation": "literal-overlap",
          "source_quote": "Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units."
        }
      ]
    }
  ]
}
```

## Exploratory v1 comparison

V1 Haiku returned 14 claims across 80 cells; ten were structurally valid and
case-applicable but semantically unassessed. V2 Haiku returned three links
across 60 cells, all in one response whose two truncated quotes invalidated its
metadata. Independent model review later judged all three observable
relationships compatible while preserving the separate metadata failures.
V2 prevents the specific v1 failure where a separately supplied quoted span did
not occur in the answer, because links now live on answer segments. It does not
prevent wrong meanings, invalid quotes, missing links, over-linking, or
unsupported compatibility labels. Because cases and response protocol changed,
the difference in link rate is not an effectiveness comparison.

## Offline false-positive / false-negative calibration

This post-collection calibration does not modify or rerun the live matrix. It
separates structural acceptance, observable segment-source judgments, and
unobservable causal use of an instruction.

- Structural unit: one response envelope. Two independently specified valid
  controls were accepted and four malformed/wrong-ID/cross-arm/wrong-quote
  controls were rejected: 0/4 false accepts and 0/2 false rejects. These counts
  calibrate the structural checker, not model attribution precision.
- Observable unit: one explicitly grounded task-output-source fixture. Ten
  fixtures include exact artifacts, distinctive literal overlap, and paired
  contexts where identical output is evaluated under changed required polarity
  or language. A deterministic observer reads only those declared properties;
  it does not consume expected labels and is not a general semantic classifier.
  It agrees with all independently declared fixture labels.
- The confusion matrix is bookkeeping over that narrow observer. Against the
  deliberately mixed emitted/not-emitted pattern it reports 2 TP, 3 FP, 2 TN,
  2 FN, and 1 insufficient: fixture precision 2/5 (0.40), fixture recall 2/4
  (0.50). These planted fixture rates are not live-model rates.
- Always-positive scores precision 4/9 and always-empty has undefined precision
  (0/0) with recall 0/4. Neither passes. Insufficient evidence stays outside
  binary denominators.
- Causal use has no observable ground truth here. A missing link is at most an
  observable diagnostic omission under a declared rubric, never proof that the
  model did not use an instruction.

The all-tagged audit packet covers all 48 tagged live responses, all 56 returned
segments (21 with emitted links, 35 without), and all 309 arm-specific
segment-source candidate pairs. It preserves complete source fragments, prompt,
case, prior applicability routing, emitted links, and independent answer checks.
Independent judgments are integrated for all 27 emitted claims and the 17
reviewed omissions. The other candidates remain unlabeled. Because the complete
negative universe was not independently judged, live FP/FN precision and recall
remain undefined and are not published.

## Controls, corrections, and limits

### Independent-review rework mapping

- **F1:** calibration fixtures now carry explicit task input and declared
  literal/artifact/polarity/language facts. A narrow deterministic observer is
  independent of expected labels; same-output polarity and language pairs prove
  context sensitivity. Confusion matrices are labeled bookkeeping only.
- **F2:** automatic applicability output is neutral
  `outside-predeclared-applicability`; it no longer asserts semantic falsity.
  Exact metadata, literal probes, prior flags, and immutable independent model
  judgments are separate. The arithmetic example and automatic totals are
  corrected to the 18/7/2 review result plus 17 observable omissions.
- **F3:** grounded exact-answer/artifact/language failures, sentence/article
  heuristic alerts, segment joining-whitespace defects, and independent review
  findings are reported separately. Abbreviation and grammatical article-less
  positive controls prevent either heuristic becoming ground truth.

- Focused v1+v2 regression suite passed. V2 has executable positive and
  deceptive controls for reversible fixtures, literal overlap, ordinary
  abstention, malformed/empty segments, unknown/cross-arm IDs, wrong quotes,
  neutral prior handling, unrelated copied source quote, negation flip with
  no links, copied-rule answer pollution, heuristic controls, retries, model
  identity selection, and matrix corruption.
- The first aggregate implementation incorrectly excluded answer checks when
  metadata was invalid. This was found before reporting. The pre-fix aggregate
  and audit packets are retained; only aggregation/audit rendering was changed.
  Frozen design and results hashes remained identical before/after the fix.
- Deterministic lexical checks establish only exact quote or distinctive-overlap
  properties. Applicability is a routing prior. General semantic compatibility
  remains independent-review work beyond the narrow grounded properties.
- Two repetitions and two models are bounded exploratory evidence, not a
  statistical benchmark. No extra runs or models were added to chase a result.
- The historical semantic fixture is an old candidate, not current upstream.
  No pure compression-superiority claim is supported.

## Evidence and exact validation commands

```bash
python3 -m unittest tests.test_attribution_pilot tests.test_attribution_v2 -v
python3 -m py_compile evals/attribution_v2.py
python3 evals/attribution_v2.py analyze \
  --output artifacts/v2 \
  --independent-review artifacts/v2/independent-link-review.json
python3 evals/attribution_v2.py calibrate --output artifacts/v2
diff -u \
  artifacts/v2/post-run-frozen-before.sha256 \
  artifacts/v2/post-run-frozen-after.sha256
shasum -a 256 -c historical private immutability manifest
shasum -a 256 -c artifacts/v2/f1-f3-frozen-before.sha256
```

Key artifacts:

- `artifacts/v2/design-freeze.json`: cases, pinned models, schedule,
  system-input hashes, CLI version, and limits.
- `artifacts/v2/source-map.json`, `fixtures/`, and `inputs/`:
  deterministic reviewed map and exact model-facing inputs.
- `artifacts/v2/smoke-result.json` and
  `stronger-model-identity.json`: preserved alias discovery evidence.
- `artifacts/v2/raw/` and `results.json`: all 120 raw records and
  retained attempts.
- `artifacts/v2/aggregate.json`: strict matrix, answer, metadata,
  length, usage, and relationship summaries.
- `artifacts/v2/audit-packet.json` and `audit-packet.md`: every
  returned link with actual segment, source fragment, claimed quote, relation,
  prompt/case, applicability, literal checks, and independent answer checks.
- `artifacts/v2/all-tagged-segments-audit.json`: every segment from
  all 48 tagged responses and all 309 candidate source pairs, including 35
  segments with no emitted link, ready for independent observable review.
- `evals/attribution_v2_calibration.json` and
  `artifacts/v2/calibration.json`: post-collection structural and
  observable FP/FN fixtures, scores, trivial-detector controls, and explicit
  refusal to report unreviewed live rates.
- `artifacts/v2/independent-link-review.json`: immutable independent model-review
  evidence integrated by stable claim ID and SHA-256, never rewritten.
- `historical private pre-rework archive/` and
  `artifacts/v2/history/pre-f1-f3-rework/`: preserved derived report,
  aggregate, audit packets, and calibration from before F1-F3 correction.
- `evals/instruction_diagnostics.md`: concise reusable method card and
  publication boundary.
- `artifacts/v2/aggregate.pre-analysis-fix.json` and matching
  pre-fix audit packets: retained post-collection correction trail.


## Final F1-F3 artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `evals/attribution_v2.py` | `b392afd1e5cce887f472e69054a92685bbc118781efa32e482947bb0eaf9d198` |
| `tests/test_attribution_v2.py` | `71e59ae8e9833656bbdc1aa61bc1d6922022299e4e42aa1e192d0d94f72a1208` |
| `evals/attribution_v2_calibration.json` | `a0405b999638df403883d251a04f3496e01ecc9f6f6ddfbaeaa06d224263f868` |
| `evals/instruction_diagnostics.md` | `4bedd8649bc305f2a3035945658e6506c59d74255a061a9bcb8c759aa4170d9a` |
| Frozen `design-freeze.json` | `3548cb3f8109944c95a45d3290c1b8f312f5d9f1caf33d2ee2b6a8183aedf74f` |
| Frozen `results.json` | `3f2d3ba3db71287a0e7296ecc956bc0cd2ade4db060e3beda779065c6ddd2ec8` |
| Corrected `aggregate.json` | `65e7e7950913d5bf0b1da466cd1edc96de0c89ac5cacaf1f3cc943c54052e126` |
| Corrected `audit-packet.json` | `b3fe4764acb146f78a9a8949d20fcbe6e28dece1cb1785a34d9c7a47e1147b49` |
| Corrected `all-tagged-segments-audit.json` | `ba7306d50c7249a5ae97c0dfcb85081867e7548a108ff56a534ee40ba203b3d3` |
| Corrected `calibration.json` | `d49e1f37154a612796d2f74abdb7e4be30b9af5a4f391f5c25b462cd36901347` |
| Immutable independent review | `3ed569d02f17a79647fe59ca799d5ba4ba9f3cd56ed7d91f5daef6c9286a2674` |
