# Proposed synthetic robustness extension

Status: proposed; awaiting user approval before implementation or live calls.
Origin: user asked whether custom synthetic examples could reduce sensitivity to statistical noise. Existing v1/v2 evidence and acceptance remain unchanged. No public MR/article is authorized by this proposal.

## Question and limits

Measure how stable observable instruction-diagnostic behavior is across task families, wording, source-map perturbations and repeated model executions. Synthetic coverage does not establish real-world representativeness or causal source attribution. More generated rows do not automatically mean more independent evidence.

## Critical path

1. Implement and independently validate a deterministic synthetic generator, explicit task facts, narrow independent oracles, and leakage/duplicate checks. Use existing diagnostic primitives; avoid a new general semantic evaluation framework.
2. Freeze the corpus, group split, source maps, prompts, primary metrics, analysis seeds, call budget and failure policy before evaluation. Review design before opening holdout responses.
3. Run the bounded matched model experiment, analyze all scheduled cells including failures, independently review findings and preserve a reproducibility packet. Article/MR decisions remain deferred.

## Two separate datasets

- Offline calibration bank: hundreds of deterministic segment/source/task fixtures with deliberate true links, false links, observable omissions, uncertainty and malformed metadata. Independently specified facts cover exact strings, negation/limits, numeric values and units, irrelevant-source decoys and literal matches. Do not count these fixtures as model-generated evidence.
- Live synthetic tasks: distinct source/task families with reviewed natural-language templates. Candidate starting allocation: 24 families, eight development and sixteen held out; two predeclared task/wording variants per family. Related paraphrases, values and source variants stay in the same split. The exact allocation must be frozen after checking family diversity, not selected after seeing scores.

Optional model assistance proposes varied wording only. Generation of IDs, values, schedules, grouping and corruption controls is scripted. Assisted templates and semantic units receive review and are frozen; the generating model does not provide unquestioned ground truth.

## Bounded live matrix proposal

Start with general source-aware diagnostics rather than another confounded original-versus-historical-Caveman comparison. Reuse the two pinned models only after readiness verification. For the sixteen held-out families: two cases per family, matched clean/tagged arms, two models and three repeated executions gives 384 scheduled calls. All repeat calls use identical frozen inputs within a case; wording variation and stochastic repeats must not be conflated. Development uses offline fixtures; any development model calls must be separately budgeted before execution. At most three concurrent calls. Freeze a bounded retry policy and report actual attempts; do not keep extending a run until results look favorable.

The budget is a practical first study, not a power calculation or a promised precision level. If uncertainty remains wide, say so rather than selecting additional cases post hoc. No execution starts merely because this document exists.

## Analysis contract

- Unit of analysis for relationship outcomes: enumerated segment/source/task candidate with a specified relation. Ground decidable expected judgments in explicit input facts; preserve insufficient evidence separately.
- Separate structural checker false accepts/rejects, live observable-link FP/FN, abstention, exact answer violations, heuristic alerts, perturbation effects and cost. A missing ID is not a causal false negative.
- Report TP/FP/TN/FN and denominators for fully judged candidate universes. Precision and recall are undefined for zero denominators. Test always-positive, always-empty, label inversion, and incomplete-matrix controls.
- Report per-family/per-model outcomes, macro summaries and paired clean/tagged differences. Repeated runs and paraphrases from one family are clustered, not independent successes. Record repeat disagreement within identical inputs separately from wording sensitivity.
- Use a predeclared family-level uncertainty procedure for paired effects, retaining each resampled family's complete paired data; disclose the small number of family clusters and conditional interpretation. No blanket claim that intervals have been validated for arbitrary semantic judgments.
- Keep holdout distinct from tuning. If holdout findings cause a checker/protocol change, preserve the initial result, label the correction, and do not continue calling that reused holdout an untouched confirmation set.
- Synthetic results complement, not replace, the existing realistic Caveman cases. Preserve v1/v2 reports separately.

## Methodological references

- NIST/SEMATECH randomized-block design: https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm — supports controlling nuisance differences through matched/block comparisons.
- NIST nested variation: https://www.itl.nist.gov/div898/handbook/pri/section5/pri55.htm — distinguishes multiple experimental-unit levels and within/between variation.
- scikit-learn grouped cross-validation guide: https://scikit-learn.org/stable/modules/cross_validation.html — related groups should not leak across development/evaluation splits. This is an analogous split-design principle, not a requirement to train a classifier here.

No implementation, new live model call, commit, publication, or change to prior accepted results was performed while preparing this proposal.
