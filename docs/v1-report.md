# Eval-time attribution pilot report

## Recommendation

**No-go for a public method claim from this pilot; diagnostic usefulness is promising but inconclusive.** Temporary IDs elicited auditable model-reported span-to-source claims in some cells, and exact validation caught invalid claims. That is useful internal diagnostic behavior. Coverage was sparse, two semantic claims pointed to text absent from the answer, one original claim used an inapplicable ID, and independent semantic attribution was not established.

This decision is not based only on the impossible causal-provenance claim. The pilot also lacks enough independently assessed, cross-model evidence to claim that the method reliably produces useful semantic traces. Every annotation remains a model self-report. No production skill, blog, or follow-up publication is recommended from this run.

## Frozen design and execution

- Five matched arms: terse-only control, original clean, original instrumented, semantic clean, semantic instrumented.
- Eight predeclared cases, two repetitions, deterministic randomized schedule (`seed=260916`): 80 cells.
- Categories: near examples, novel paraphrase, exact code/path/error/number/negation preservation, Russian language handling, normal-prose artifact boundary, destructive-operation clarity, and neutral arithmetic.
- One common structured envelope across all arms: `answer` plus `annotations`. Clean arms were required to return an empty annotation list.
- Instrumented arms combined source tagging with the annotation request. This is one combined intervention; the design cannot isolate an ID-only effect.
- Model calls ran from temporary directories outside repositories with `--safe-mode`, `--restricted`, empty setting sources and tools, strict MCP config, no session persistence, explicit system prompt, explicit model, and a 90-second timeout.
- Concurrency was capped at three. Each subprocess failure allowed the initial attempt plus three bounded retries. All attempts were retained.
- Smoke passed before the matrix. The full run completed 80/80 cells in 80 attempts, with no timeout, retry, malformed response, missing cell, duplicate cell, or repository cwd.
- Requested model: `claude-haiku-4-5`. Claude CLI `2.1.273` exposed `claude-haiku-4-5-20251001` and its canonical alias `claude-haiku-4-5` in every cell's `modelUsage`.

Independent prereview found checker defects after collection. The original frozen design, prompts, generated model-facing inputs, fixtures, `results.json`, and 80 raw records remain byte-identical. Corrected analysis is explicitly post-collection and stored in `evals/attribution_pilot_analysis_corrections.json`; it is not retroactively described as predeclared.

## Pinned inputs

- Current upstream skill: commit `ed37ab132393899c129bbeef2b9743ff3af19c68`, `skills/caveman/SKILL.md`, SHA-256 `0bf09a0a9a017d004a81d4b693e5a2d830e1a28230a5885df773e1ed9c0571cc`.
- Historical semantic candidate: unmerged object `7c188c58dd58c7b99f18eb6d350ec9fead546d9e`, raw SHA-256 `86c684041a49da815c9fa5e34e161e36467dd09030986522aaab580fc212ae1c`; this does not claim upstream adoption.
- The copied semantic fixture removed old `CAV-SEM-*` heading suffixes before instrumentation. Its clean SHA-256 is `17d60b4c9bdbe60309fcd28c9826d09764063e66307c5e2d9df41a016356313e`.
- Fresh IDs were generated from source family, clean content hash, and source-map order, for example `EVO-0BF09A0A-04` and `EVS-17D60B4C-02`.
- Current upstream was not represented as a fictional dictionary. Its source map labels one literal replacement-pair fragment, one negative example, and three positive example lines. Every anchor matched exactly once.
- Removing only the generated `[EVAL-ID:...]` tags reproduces each clean fixture byte-for-byte. Missing or ambiguous anchors fail closed.

The two skill versions are different contracts, not compressed and uncompressed forms of one contract. Current upstream adds ASD-STE clarity/register rules, detailed tool-call behavior, stronger language-priority wording, grammatical-marker handling, and expanded anti-caricature guidance. The historical candidate groups a smaller semantic core and differs in auto-clarity and artifact-boundary wording. Original-versus-semantic differences therefore mix version, contract, granularity, and instrumentation effects; they cannot isolate compression.

## Results

| Arm | Transport success | Valid envelopes | Annotated cells | Claims | Structurally valid | Annotation failures | Literal-probe passes | Observable-probe pass / fail | Semantic assessment |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Terse control | 16/16 | 16/16 | 0/16 | 0 | 0 | 0 | 0 | 0 / 0 | n/a |
| Original clean | 16/16 | 16/16 | 0/16 | 0 | 0 | 0 | 0 | 0 / 0 | n/a |
| Original instrumented | 16/16 | 16/16 | 3/16 | 3 | 2 | 2 | 1 | 0 / 0 | 1 needs review |
| Semantic clean | 16/16 | 16/16 | 0/16 | 0 | 0 | 0 | 0 | 0 / 0 | n/a |
| Semantic instrumented | 16/16 | 16/16 | 9/16 | 11 | 9 | 2 | 0 | 7 / 2 | 9 need review |

Transport success means the provider returned parseable structured output. Envelope validity separately enforces exact top-level and annotation keys/types and forbids clean-arm annotations. A wrong ID, non-output span, or case-inapplicable ID is an annotation failure, not a provider failure. All 80 transport responses and envelopes were valid; four annotation claims failed exact-span, arm-ID, or case-applicability checks.

Literal and observable probes are diagnostics only. They do not become semantic verdicts when they pass. Independent semantic attribution for all ten structurally valid, case-applicable claims remains `needs-review`. All 14 emitted claims retain unsupported causal provenance.

The frozen auth and React expectations are now reported only as narrow lexical probes. Terse control missed the auth probe twice; original instrumented missed it once. These are not correctness or artifact-preservation failures. The original-instrumented auth answer also contains mutually inconsistent predicate advice about equality, so the report does not characterize it as fully plausible or correct. Across the cases that explicitly requested artifact preservation, every valid response preserved the required artifacts.

## Output length and usage

| Arm | Answer chars | Mean answer chars | Annotation JSON chars | CLI input tokens | CLI output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Terse control | 8,852 | 553.25 | 32 | 21,938 | 9,858 |
| Original clean | 5,284 | 330.25 | 32 | 58,888 | 18,978 |
| Original instrumented | 5,350 | 334.38 | 294 | 60,602 | 26,487 |
| Semantic clean | 6,355 | 397.19 | 32 | 43,147 | 10,564 |
| Semantic instrumented | 6,479 | 404.94 | 1,210 | 48,411 | 21,252 |

The clean-arm annotation count is the two characters in `[]` per response. Instrumentation increased answer characters by 66 (+1.25%) for original and 124 (+1.95%) for semantic. Exposed CLI output usage increased by 7,509 tokens for original and 10,688 for semantic. These are real CLI usage values for the whole structured call, including any provider-reported thinking/agent overhead; the provider did not expose an exact token split between answer and annotation strings. Character counts provide the exact separate text lengths.

Raw ID counts are not a quality comparison. Original and semantic source maps have unequal rule granularity, and the original map deliberately covers literal examples rather than broad behavior rules.

## Representative full responses

### Structurally valid original claim with literal overlap

`r2-react-near-example-original-instrumented` mapped an exact answer span to the actual current-upstream React example:

```json
{
  "answer": "Inline object prop = new ref each render. React compares props by reference. New ref triggers child re-render. Wrap in `useMemo`:\n\n```javascript\nconst Parent = () => {\n  const data = useMemo(() => ({ foo: 'bar' }), []);\n  return <Child data={data} />;\n};\n```",
  "annotations": [
    {
      "span": "Wrap in `useMemo`",
      "rule_id": "EVO-0BF09A0A-04"
    }
  ]
}
```

The span occurs once and contains the predeclared literal cue `` `useMemo` ``. This is an auditable model-reported association with lexical overlap. Its semantic attribution remains unassessed.

### Structurally valid semantic claims with narrow observable probes

`r2-exact-preservation-semantic-instrumented` preserved every requested artifact and emitted two exact spans:

```json
{
  "answer": "On v2.4.1, `/srv/app/config.yaml` must not retry `E_CONN_RESET` after exactly `250 ms`.",
  "annotations": [
    {
      "span": "must not retry",
      "rule_id": "EVS-17D60B4C-02"
    },
    {
      "span": "`E_CONN_RESET` after exactly `250 ms`",
      "rule_id": "EVS-17D60B4C-01"
    }
  ]
}
```

Narrow probes observe a polarity marker and requested exact artifacts. They do not assess whether either rule semantically explains the span. The user prompt itself required the same content.

### Invalid span claim

`r1-auth-near-example-semantic-instrumented` returned an internally inconsistent boundary explanation and annotated source text that did not occur anywhere in the answer:

```json
{
  "answer": "Token is still valid at expiry boundary by convention. Middleware incorrectly uses `>=` or `<=` instead of `>` or `<`, rejecting at equality.\n\n**Buggy:**\n```python\nif current_time >= token_expiry:\n    reject()\n```\n\nAt `current_time = token_expiry`, condition is true → rejected (wrong).\n\n**Fix:**\n```python\nif current_time > token_expiry:\n    reject()\n```\n\nAt `current_time = token_expiry`, condition is false → accepted (correct).\n\nAlternatively, if check is phrased as \"is expired\":\n- Buggy: `if token_expiry < current_time`\n- Fix: `if token_expiry <= current_time`\n\nThe boundary operator must allow equality, not cross it.",
  "annotations": [
    {
      "span": "Never drop not/never/no/only/except: polarity and limits control meaning.",
      "rule_id": "EVS-17D60B4C-02"
    }
  ]
}
```

The checker rejected this claim because the purported span had zero matches in `answer`. The same failure occurred in the second repetition. This is direct evidence that a model may echo a tagged source rule instead of producing a valid output-span annotation.

## Strengths

- The experiment used real isolated model calls, not synthetic outputs.
- Source hashes, exact snippets, generated fixtures, system inputs, prompts, schedule, raw outputs, errors, attempts, usage, and checks are retained.
- Exact-span and arm-specific-ID checks are deterministic and fail closed.
- The planted wrong trace test proves the checker rejects the intended violation rather than merely accepting any known ID.
- Narrow lexical and observable probes are separated from independent semantic assessment.
- Clean/control arms produced no annotations, so no cross-arm ID contamination appeared.
- Semantic tags yielded nine structurally valid claims across seven of sixteen cells; narrow probes passed for seven claims. This supports further internal method work, not a public reliability claim.

## Acceptance-criteria coverage and gate controls

**5 of 6 AC rows were driven through production entry points; 1 of 6 is a stated external-side-effect bound.**

| AC row | Production call site | Evidence |
| --- | --- | --- |
| Reproducible five-arm repeated pilot | `main` → `run_matrix` → `freeze_design` | Deterministic 80-cell schedule test plus complete live run |
| Temporary IDs only in eval copies | `prepare_fixtures` → `instrument_source` | Real-input reversibility and unique-anchor test; production skill hash unchanged |
| Positive and negative map/trace controls | `validate_envelope`, `validate_response`, and `observable_probe` | Known literal overlap, planted wrong trace, contradictory-probe controls, unknown/wrong-arm ID, missing/duplicate span, extra keys, and malformed envelopes |
| Preserve raw outputs, provenance, and failures | `run_one`, `matrix_audit`, and `aggregate` | Four-attempt failure retention, fail-closed multiset/identity checks, 80 raw live records, and explicit unsupported-provenance field |
| Independent checks and publication decision | `aggregate` plus this report | Lexical probes, narrow observable probes, unassessed semantic attribution, and post-collection rubric correction are reported separately |
| No public publication before parent review | External-side-effect bound | No commit, push, PR, comment, blog edit, or production skill edit performed |

Gate mutation controls execute the behavioral contracts, not a static token search. They weaken source-anchor uniqueness to admit one duplicated anchor, output-span uniqueness to admit one duplicated span, and arm-specific ID lookup to admit one wrong-arm ID. `test_narrowing_mutants_are_killed_by_behavioral_contracts` confirms each weakened implementation is killed. `test_instrument_source_rejects_missing_and_ambiguous_anchors` is also a token-preserving source-input mutant: it duplicates the exact searched anchor and verifies rejection.

## Limitations

- Two repetitions and one model are exploratory, not statistical or cross-model evidence.
- Tagging and requesting annotations changed the prompt together. No result isolates the causal effect of IDs.
- The producing model self-selected whether to annotate. Absence of an annotation says nothing about whether a rule influenced the answer.
- Literal probes validate only predeclared shared wording. Observable probes check narrow surface properties, not semantic attribution or whole-answer correctness.
- A prompt can itself demand the same wording as a semantic rule. Exact agreement therefore cannot establish source provenance.
- Auth/React/neutral frozen literals are post-collection classified as lexical probes, not correctness or preservation rubrics.
- Provider usage covers the complete structured call. Only characters, not provider tokens, can be separated exactly between answer and annotation text.
- The historical semantic candidate is unmerged and is not current upstream behavior.
- Current-original versus historical-semantic is an exploratory comparison of concrete versions, not a pure compression or rewrite-benefit experiment.

## General method boundary

The method can instrument rules, examples, prohibitions, exceptions, document sections, and lexical replacements. Caveman is one case study, not the method's boundary. Identifier insertion can be deterministic from headings, bullets, exact anchors, or a reviewed source map. An LLM may optionally propose semantic segmentation for unstructured prose, but that map requires human review and frozen versioning. Segmentation, ID insertion, response annotation, structural validation, surface probes, and independent semantic assessment are separate stages.

## Reproduction and evidence

Focused tests and checker regeneration:

```bash
python3 -m unittest tests.test_attribution_pilot -v
python3 evals/attribution_pilot.py analyze --output artifacts/v1
```

Real smoke and full matrix:

```bash
python3 evals/attribution_pilot.py smoke --output reproduction/v1 --model claude-haiku-4-5 --workers 1 --timeout 90
python3 evals/attribution_pilot.py run --output reproduction/v1 --model claude-haiku-4-5 --workers 3 --timeout 90
```

Evidence index:

- `artifacts/v1/design-freeze.json`: pre-call cases, checks, schedule, and go/no-go rule.
- `artifacts/v1/source-map.json`: pinned versions, hashes, exact snippets, generated IDs, and match counts.
- `artifacts/v1/fixtures/`: reversible clean and instrumented eval-only skill copies.
- `artifacts/v1/inputs/`: exact per-arm system inputs.
- `artifacts/v1/smoke-results.json` and `smoke-checks.json`: real isolated smoke.
- `artifacts/v1/raw/`: all 80 raw cell records, including retained attempts and sanitized stderr.
- `artifacts/v1/results.json`: complete result set.
- `artifacts/v1/aggregate.pre-rework.json`: original checker output retained for before/after audit.
- `artifacts/v1/aggregate.json`: corrected envelope, annotation, lexical-probe, observable-probe, preservation, length, usage, and strict matrix checks.
- `evals/attribution_pilot_analysis_corrections.json`: explicit post-collection rubric correction.
- `artifacts/v1/rework-preservation-before.sha256` and `rework-preservation-after.sha256`: identical hashes for frozen design, source map, results, raw outputs, inputs, and fixtures.
- `historical private validation log`, `historical private validation log`, `historical private validation log`, `historical private validation log`, `historical private validation log`, `historical private validation log`, `historical private validation log`, and `historical private matrix log`: validation logs.
