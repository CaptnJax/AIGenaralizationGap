# RQ1 dataset-quality review artifacts

The completed dataset-quality audit generated the selection records, code and
source-evidence packets, and blank forms in this folder. No completed independent
reviewer judgments or adjudicated labels are included.

| File | Recorded content |
| --- | --- |
| [selection.csv](selection.csv), [strata.csv](strata.csv) | Model/stratum selections, counts, inclusion probabilities, and sampling weights. |
| [coordinator_key.csv](coordinator_key.csv) | The mapping for the 328 unique review cases, including merged-sample inclusion probabilities. |
| [stage1_blinded_code.jsonl](stage1_blinded_code.jsonl) | Code packets with review IDs and declared language. Comments and identifiers can still reveal provenance. |
| [stage2_source_evidence.jsonl](stage2_source_evidence.jsonl) | The associated source-evidence packets. |
| [purposive_cases.jsonl](purposive_cases.jsonl), [purposive_selection.csv](purposive_selection.csv) | Targeted cases kept separate from the probability sample. |
| [reviewer_1.csv](reviewer_1.csv), [reviewer_2.csv](reviewer_2.csv), [adjudication.csv](adjudication.csv) | Blank forms; empty fields are not negative judgments or completed study outcomes. |

Original source labels and benchmark predictions are unchanged. The published
metrics use the supplied dataset labels; no whole-dataset label-error estimate
was derived from these blank forms. The external authors' 100-case LLMVul review
is separate source evidence, analyzed in the
[completed dataset-quality report](../../rq1_priority4_diagnostics.md).

For completed RQ1 results and replication steps, use the
[repository guide](../../../../../README.md).
