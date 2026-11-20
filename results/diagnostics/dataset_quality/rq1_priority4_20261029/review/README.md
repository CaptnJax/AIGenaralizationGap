# Priority 4 independent review package

Status: prepared; independent reviews and adjudication have not been performed.
Give each qualified reviewer only stage1_blinded_code.jsonl and their own blank
reviewer form. Do not give the coordinator key, selections, this audit report,
or model predictions. Code comments/identifiers may themselves reveal provenance;
blinding is therefore best effort, not guaranteed. Then release stage2 evidence,
retaining both initial and evidence-informed judgments separately. Source metadata
can reveal intended labels; record when that happens. Never run untrusted source
on the host. Test evidence needs an isolated environment.

Allowed judgments: vulnerable; non_vulnerable_scoped; uncertain;
insufficient_context. A scoped negative must name the assessed vulnerability
and assumptions; it does not certify universal safety. Provide line references,
patch/test/source evidence, CWE only if justified, confidence, and rationale.
Tags can include label_disagreement, confirmed_label_error, missing_context,
preprocessing_damage, lost_span, unsupported_language, model_miss,
spurious_model_positive. Do not use model-miss tags until predictions are revealed.

Two reviewers work independently before the adjudicator resolves disagreements
with evidence. Blank forms are not negative judgments. Preserve uncertain and
insufficient-context decisions; do not silently coerce them to binary labels.

selection.csv preserves each model/stratum sample probability n/N and weight N/n.
coordinator_key.csv also gives merged-sample union probabilities. For per-job
estimates use that job's selections and weights, not the union or the raw review
fraction. Report unresolved weighted mass separately; use design-aware uncertainty
before estimating population label-error rates. Purposive cases and the external
authors' 100-case sample are separate, with no probability weights invented.

Original source labels and benchmark predictions remain unchanged. No corrected
whole-dataset metrics should be presented before defensible adjudication.
