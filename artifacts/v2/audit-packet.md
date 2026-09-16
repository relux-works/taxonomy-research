# V2 returned-link audit packet

Independent model-review judgments attached: **27/27**. They are not human ground truth or causal evidence.

Returned links: 27

## Link 1: `haiku--r2-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `invalid-metadata`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment preserves HTTP 429 and exponential backoff exactly; the truncated source_quote makes metadata invalid but does not negate observable exactness.
- Output segment:

```text
HTTP 429 требует exponential backoff, чтобы не перегружать сервер повторными запросами при регулировании трафика.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `False`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[{'kind': 'punctuation-sentence-count', 'observed': 1, 'requested': 2, 'limit': 'abbreviations and punctuation make this a heuristic only'}]`
- Joining whitespace defects: `[{'boundary_after_segment': 0, 'left_suffix': 'ровании трафика.', 'right_prefix': 'Используй значен'}]`
- Extraneous source copies: `[]`

## Link 2: `haiku--r2-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-04`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The task is explicitly Russian and this emitted line is Russian while retaining the requested technical terms.
- Output segment:

```text
HTTP 429 требует exponential backoff, чтобы не перегружать сервер повторными запросами при регулировании трафика.
```

- Source fragment:

```text
Preserve user's dominant language in every emitted line. Compress style, not language.
```

- Claimed source quote:

```text
Preserve user's dominant language in every emitted line. Compress style, not language.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[{'kind': 'punctuation-sentence-count', 'observed': 1, 'requested': 2, 'limit': 'abbreviations and punctuation make this a heuristic only'}]`
- Joining whitespace defects: `[{'boundary_after_segment': 0, 'left_suffix': 'ровании трафика.', 'right_prefix': 'Используй значен'}]`
- Extraneous source copies: `[]`

## Link 3: `haiku--r2-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `invalid-metadata`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment preserves Retry-After exactly; its source_quote is truncated, so structural metadata validity is a separate failure.
- Output segment:

```text
Используй значение заголовка Retry-After из ответа сервера как интервал ожидания перед следующей попыткой.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Preserve inline code, identifiers, API names.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `False`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[{'kind': 'punctuation-sentence-count', 'observed': 1, 'requested': 2, 'limit': 'abbreviations and punctuation make this a heuristic only'}]`
- Joining whitespace defects: `[{'boundary_after_segment': 0, 'left_suffix': 'ровании трафика.', 'right_prefix': 'Используй значен'}]`
- Extraneous source copies: `[]`

## Link 4: `stronger--r1-exact-negation-artifacts-semantic-tagged`

- Case: `exact-negation-artifacts`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: All five task-required artifacts are preserved exactly in the reconstructed answer.
- Output segment:

```text
`v2.4.1` reads `/srv/app/config.yaml`, hits `E_CONN_RESET` at `250 ms`, must not retry.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Return one sentence that exactly preserves `/srv/app/config.yaml`, `E_CONN_RESET`, `250 ms`, `v2.4.1`, and the phrase `must not retry`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 5: `stronger--r1-exact-negation-artifacts-semantic-tagged`

- Case: `exact-negation-artifacts`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-02`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The explicit phrase must not retry preserves the task's required negative polarity.
- Output segment:

```text
`v2.4.1` reads `/srv/app/config.yaml`, hits `E_CONN_RESET` at `250 ms`, must not retry.
```

- Source fragment:

```text
Never drop not/never/no/only/except: polarity and limits control meaning.
```

- Claimed source quote:

```text
Never drop not/never/no/only/except: polarity and limits control meaning.
```

- Prompt:

```text
Return one sentence that exactly preserves `/srv/app/config.yaml`, `E_CONN_RESET`, `250 ms`, `v2.4.1`, and the phrase `must not retry`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 6: `stronger--r1-normal-prose-artifact-semantic-tagged`

- Case: `normal-prose-artifact`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-06`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The task explicitly targets a persisted README and the answer is two complete professional prose sentences.
- Output segment:

```text
A backup is automatically created before the migration process begins. If the migration fails, users can restore the backup to return the system to its previous working state.
```

- Source fragment:

```text
Persisted outside chat: write normal prose for code comments, commits, documentation, issue/PR/MR/defect/ticket/bug-report text, memory files, and third-party messages.
```

- Claimed source quote:

```text
Persisted outside chat: write normal prose for code comments, commits, documentation, issue/PR/MR/defect/ticket/bug-report text, memory files, and third-party messages.
```

- Prompt:

```text
Write exactly two complete, normal professional English sentences for a persisted README. State that a backup is created before migration and that users can restore it if migration fails. Include the words backup, migration, and restore.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 7: `stronger--r1-novel-cache-paraphrase-semantic-tagged`

- Case: `novel-cache-paraphrase`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The task requires exact lowercase cache stampede, but the answer uses capitalized Cache stampede; that contradicts the cited exactness rule.
- Output segment:

```text
Cache stampede: popular key expires, many concurrent requests miss at once, all slam backend simultaneously, overload it. Fix: request coalescing — one request fetches, rest wait, reuse result.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Explain a cache stampede to an experienced engineer in two concise sentences. Include the exact terms `cache stampede` and `request coalescing`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: cache stampede']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 8: `stronger--r1-ordinary-unlinked-semantic-tagged`

- Case: `ordinary-unlinked`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `False`
- Applicability observation: `outside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The task requires one exact arithmetic string and the segment preserves every symbol and number. The applicability prior says none, but that is not a semantic oracle.
- Output segment:

```text
17 × 19 = 323
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Calculate 17 × 19. Return exactly `17 × 19 = 323` and no other answer text.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 9: `stronger--r1-original-react-example-original-tagged`

- Case: `original-react-example`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVO-0BF09A0A-04`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment expresses both the new-reference/re-render mechanism and the useMemo remedy from the full source example; the prompt independently supplies the same content, so no provenance follows.
- Output segment:

```text
Each render, inline object prop makes new object reference, so child sees prop change and re-renders. Wrap object in `useMemo` to keep same reference across renders.
```

- Source fragment:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Claimed source quote:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `['New object ref', 'Inline object prop', '`useMemo`']`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 10: `stronger--r1-original-react-example-semantic-tagged`

- Case: `original-react-example`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The task requires exact lowercase inline object prop, but the answer begins with capitalized Inline; an exactness claim is therefore false even though the explanation is semantically sound.
- Output segment:

```text
Inline object prop creates new object reference each parent render, so child sees changed prop and re-renders. Wrap object in `useMemo` to keep same reference across renders, skip re-render.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 11: `stronger--r1-original-react-example-semantic-tagged`

- Case: `original-react-example`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-03`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `insufficient-evidence`
- Independent model-review rationale: No caricature word is apparent, but the source also claims compression must not grow output and no appropriate baseline establishes that property.
- Output segment:

```text
Inline object prop creates new object reference each parent render, so child sees changed prop and re-renders. Wrap object in `useMemo` to keep same reference across renders, skip re-render.
```

- Source fragment:

```text
Never ADD word to sound caveman. Compression must not grow output.
```

- Claimed source quote:

```text
Never ADD word to sound caveman. Compression must not grow output.
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 12: `stronger--r1-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: This segment preserves HTTP 429 and exponential backoff exactly as explicitly required.
- Output segment:

```text
HTTP 429 значит сервер перегружен, мгновенный повтор только вредит — нужен exponential backoff, чтобы пауза между попытками росла.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 13: `stronger--r1-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: This segment preserves Retry-After exactly as explicitly required.
- Output segment:

```text
 Если в ответе есть Retry-After, бери оттуда точное время ожидания вместо своего расчёта.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 14: `stronger--r1-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-04`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The prompt is explicitly Russian and the segment is natural Russian with the required technical term intact.
- Output segment:

```text
 Если в ответе есть Retry-After, бери оттуда точное время ожидания вместо своего расчёта.
```

- Source fragment:

```text
Preserve user's dominant language in every emitted line. Compress style, not language.
```

- Claimed source quote:

```text
Preserve user's dominant language in every emitted line. Compress style, not language.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 15: `stronger--r2-exact-negation-artifacts-semantic-tagged`

- Case: `exact-negation-artifacts`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: All five explicitly required artifacts are preserved exactly.
- Output segment:

```text
`/srv/app/config.yaml` v2.4.1 hit `E_CONN_RESET` after 250 ms; must not retry.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Return one sentence that exactly preserves `/srv/app/config.yaml`, `E_CONN_RESET`, `250 ms`, `v2.4.1`, and the phrase `must not retry`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 16: `stronger--r2-exact-negation-artifacts-semantic-tagged`

- Case: `exact-negation-artifacts`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-02`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The answer preserves must not retry and therefore the required polarity.
- Output segment:

```text
`/srv/app/config.yaml` v2.4.1 hit `E_CONN_RESET` after 250 ms; must not retry.
```

- Source fragment:

```text
Never drop not/never/no/only/except: polarity and limits control meaning.
```

- Claimed source quote:

```text
Never drop not/never/no/only/except: polarity and limits control meaning.
```

- Prompt:

```text
Return one sentence that exactly preserves `/srv/app/config.yaml`, `E_CONN_RESET`, `250 ms`, `v2.4.1`, and the phrase `must not retry`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 17: `stronger--r2-exact-negation-artifacts-semantic-tagged`

- Case: `exact-negation-artifacts`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-03`
- Case applicable: `False`
- Applicability observation: `outside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `insufficient-evidence`
- Independent model-review rationale: The compact wording is not caricatured, but output-growth compatibility cannot be established without a declared baseline; prior inapplicability alone does not contradict it.
- Output segment:

```text
`/srv/app/config.yaml` v2.4.1 hit `E_CONN_RESET` after 250 ms; must not retry.
```

- Source fragment:

```text
Never ADD word to sound caveman. Compression must not grow output.
```

- Claimed source quote:

```text
Never ADD word to sound caveman. Compression must not grow output.
```

- Prompt:

```text
Return one sentence that exactly preserves `/srv/app/config.yaml`, `E_CONN_RESET`, `250 ms`, `v2.4.1`, and the phrase `must not retry`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 18: `stronger--r2-normal-prose-artifact-semantic-tagged`

- Case: `normal-prose-artifact`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-06`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The supplied task is a persisted README and the answer is complete professional prose.
- Output segment:

```text
A backup is automatically created before the migration process begins. If the migration fails for any reason, users can restore the backup to return their data to its previous state.
```

- Source fragment:

```text
Persisted outside chat: write normal prose for code comments, commits, documentation, issue/PR/MR/defect/ticket/bug-report text, memory files, and third-party messages.
```

- Claimed source quote:

```text
Persisted outside chat: write normal prose for code comments, commits, documentation, issue/PR/MR/defect/ticket/bug-report text, memory files, and third-party messages.
```

- Prompt:

```text
Write exactly two complete, normal professional English sentences for a persisted README. State that a backup is created before migration and that users can restore it if migration fails. Include the words backup, migration, and restore.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 19: `stronger--r2-novel-cache-paraphrase-semantic-tagged`

- Case: `novel-cache-paraphrase`
- Relation: `literal-overlap`
- Status: `misleading-literal-claim`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The emitted literal-overlap relation is absent from the generic source fragment, and capitalized Cache stampede also violates the task's exact lowercase requirement.
- Output segment:

```text
Cache stampede: key expires, many concurrent requests miss cache same time, all hit backend/DB at once, load spikes hard.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Explain a cache stampede to an experienced engineer in two concise sentences. Include the exact terms `cache stampede` and `request coalescing`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: cache stampede']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 20: `stronger--r2-novel-cache-paraphrase-semantic-tagged`

- Case: `novel-cache-paraphrase`
- Relation: `literal-overlap`
- Status: `misleading-literal-claim`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: request coalescing is preserved, but it does not occur in the cited source fragment; the emitted literal-overlap relation is false.
- Output segment:

```text
 Fix with request coalescing: only one request rebuilds cache, others wait/reuse result.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Explain a cache stampede to an experienced engineer in two concise sentences. Include the exact terms `cache stampede` and `request coalescing`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: cache stampede']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 21: `stronger--r2-ordinary-unlinked-semantic-tagged`

- Case: `ordinary-unlinked`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `False`
- Applicability observation: `outside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The exact arithmetic answer preserves all task substance. This is broad compatibility, not evidence that the rule caused the answer.
- Output segment:

```text
17 × 19 = 323
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Calculate 17 × 19. Return exactly `17 × 19 = 323` and no other answer text.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 22: `stronger--r2-original-react-example-original-tagged`

- Case: `original-react-example`
- Relation: `literal-overlap`
- Status: `literal-overlap-confirmed`
- Rule ID: `EVO-0BF09A0A-04`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment has meaningful overlap with the source's inline-object/new-reference/re-render mechanism; the task itself supplies the same terms, so origin remains unidentifiable.
- Output segment:

```text
Inline object prop creates new object reference on every render, so React sees prop changed and child re-renders.
```

- Source fragment:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Claimed source quote:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `['New object ref', 'Inline object prop']`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[{'kind': 'punctuation-sentence-count', 'observed': 1, 'requested': 2, 'limit': 'abbreviations and punctuation make this a heuristic only'}]`
- Joining whitespace defects: `[{'boundary_after_segment': 0, 'left_suffix': 'hild re-renders.', 'right_prefix': 'Wrap object in u'}]`
- Extraneous source copies: `[]`

## Link 23: `stronger--r2-original-react-example-original-tagged`

- Case: `original-react-example`
- Relation: `literal-overlap`
- Status: `misleading-literal-claim`
- Rule ID: `EVO-0BF09A0A-04`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment repeats the source example's useMemo remedy and stable-reference meaning. This observable match is fully confounded by the prompt.
- Output segment:

```text
Wrap object in useMemo so reference stays stable across renders, skipping unneeded re-render.
```

- Source fragment:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Claimed source quote:

```text
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[{'kind': 'punctuation-sentence-count', 'observed': 1, 'requested': 2, 'limit': 'abbreviations and punctuation make this a heuristic only'}]`
- Joining whitespace defects: `[{'boundary_after_segment': 0, 'left_suffix': 'hild re-renders.', 'right_prefix': 'Wrap object in u'}]`
- Extraneous source copies: `[]`

## Link 24: `stronger--r2-original-react-example-semantic-tagged`

- Case: `original-react-example`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The task requires exact lowercase inline object prop, but the segment begins with capitalized Inline; the cited exactness rule is not satisfied.
- Output segment:

```text
Inline object prop creates new object reference each parent render, causing child to re-render even if data same.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 25: `stronger--r2-original-react-example-semantic-tagged`

- Case: `original-react-example`
- Relation: `rule-compatible`
- Status: `rule-compatible-unassessed`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `compatible`
- Independent model-review rationale: The segment preserves useMemo exactly and accurately states the stable-reference remedy, although the term is also supplied by the prompt.
- Output segment:

```text
 Wrap object in useMemo to keep stable reference across renders.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
In exactly two concise sentences, explain why a React child re-renders when its parent passes an inline object prop and give the `useMemo` fix. Include the exact phrases `inline object prop`, `new object reference`, and `useMemo`.
```

- Exact source quote: `True`
- Literal markers: `[]`
- Independent answer invariants passed: `False`
- Independent answer invariant violations: `['missing required exact artifacts: inline object prop']`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 26: `stronger--r2-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `literal-overlap`
- Status: `invalid-metadata`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The segment is compatible with exact-term preservation, but the emitted literal-overlap relation is false because HTTP 429 and exponential backoff do not occur in the cited source fragment; the quote is also truncated.
- Output segment:

```text
HTTP 429 требует exponential backoff — иначе повторные запросы подряд лишь усиливают перегрузку сервера.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `False`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`

## Link 27: `stronger--r2-russian-language-semantic-tagged`

- Case: `russian-language`
- Relation: `literal-overlap`
- Status: `invalid-metadata`
- Rule ID: `EVS-17D60B4C-01`
- Case applicable: `True`
- Applicability observation: `inside-predeclared-applicability`
- Independent semantic review: `completed-independent-model-review`
- Independent model-review judgment: `contradicted`
- Independent model-review rationale: The segment preserves Retry-After, but that token does not occur in the cited source fragment; the emitted literal-overlap relation is false and the quote is truncated.
- Output segment:

```text
 Используй Retry-After: жди указанное в нём время перед следующей попыткой.
```

- Source fragment:

```text
Keep all technical substance. Technical terms exact. Code blocks unchanged. Errors quoted exact. Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Claimed source quote:

```text
Preserve inline code, identifiers, API names, CLI commands, quoted errors, numbers, and units.
```

- Prompt:

```text
Ответь ровно двумя краткими предложениями на русском языке: почему HTTP 429 требует exponential backoff и как использовать Retry-After. Сохрани HTTP 429, exponential backoff и Retry-After без изменений.
```

- Exact source quote: `False`
- Literal markers: `[]`
- Independent answer invariants passed: `True`
- Independent answer invariant violations: `[]`
- Heuristic alerts: `[]`
- Joining whitespace defects: `[]`
- Extraneous source copies: `[]`
