# Instruction diagnostics method card

Use this method to inspect observable relationships between supplied source
instructions and generated output. It does not reveal private reasoning or
prove that an instruction caused an answer.

## Procedure

1. **Freeze source units and task contracts.** Record exact source fragments,
   hashes, versions, unique anchors, and case requirements. Keep exact artifacts,
   polarity, language, formatting, and answer constraints explicit. A source
   applicability list is routing context, not semantic truth.
2. **Insert test-time IDs deterministically.** Add reversible IDs only to copied
   evaluation fixtures. Semantic segmentation may be assisted, but the proposed
   units must be reviewed and frozen separately before generation.
3. **Generate matched clean and tagged arms.** Keep model, case, repetition,
   envelope, and execution settings matched. Tagged arms expose the source map;
   clean arms use the same segmented response envelope with empty links.
4. **Validate structure and grounded output facts.** Reconstruct the answer by
   concatenating segment text. Check envelope shape, known arm-specific IDs,
   exact source quotes, literal markers, exact task artifacts, polarity, and
   explicit language. Report prose/sentence heuristics as alerts, not truth.
5. **Audit emitted and omitted relationships independently.** Review actual
   segment, full source fragment, and task context. Label compatible,
   contradicted, or insufficient evidence. Inspect link-free segments too.
   Preserve reviewer identity and rationale; an observable omission is not a
   causal false negative.
6. **Calibrate narrowly.** Declare the unit and candidate universe. Use grounded
   paired fixtures—including same output with changed polarity or language—and
   a deterministic observer limited to those declared properties. Report
   `precision = TP/(TP+FP)` and `recall = TP/(TP+FN)` with exact denominators;
   return undefined for zero denominators and keep insufficient evidence out of
   binary counts. Always-positive and always-empty controls must not pass.
7. **Measure paired effects and cost.** Compare clean/tagged outputs only over
   identical reconstructable `(model, case, repetition)` members. Report answer
   bytes, metadata bytes, provider usage, grounded violations, heuristic alerts,
   and joining defects separately. Paired perturbations can test whether the
   diagnostic reacts to a changed task contract.
8. **Apply the usefulness and publication gate.** The method is useful when it
   creates reviewable claims, catches invalid metadata and observable
   contradictions, retains abstentions/uncertainty, and exposes omissions at an
   acceptable cost. Publish precision/recall or broader conclusions only when
   the complete claimed candidate universe and independent labels justify their
   denominators.

## Interpretation boundary

- Causal attribution and chain-of-thought recovery are out of scope.
- Literal overlap is only a lexical fact; generic compatibility may be real but
  non-discriminative.
- Clean runs sharing the segmented envelope isolate the incremental tagging/link
  burden. They do **not** measure total overhead against an unstructured
  production response.
- Differences between source versions, contracts, or map granularities cannot
  establish pure compression superiority.
