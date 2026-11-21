# CWEval source reference for RQ

This README is an RQ-focused excerpt adapted from
[CWEval](https://github.com/Co1lin/CWEval/tree/e9a2a124c8c53679b6d8d27adfd2f6c40e7576d7),
revision `e9a2a124c8c53679b6d8d27adfd2f6c40e7576d7`.

## Role in RQ

The supplied C/C++ reference and intentionally unsafe implementations form a
supplementary diagnostic for the frozen LineVul and VulBERTa checkpoints.
The three source Parquets contain 52 tasks and 104 candidate implementations:
`core_c-00000-of-00001.parquet`, `core_cpp-00000-of-00001.parquet`, and
`lang_c-00000-of-00001.parquet`.

The prepared cohort retains 58 functions in 29 complete reference/unsafe pairs.
Reference implementations receive label 0 and intentionally unsafe implementations
receive label 1. These are benchmark labels; a reference implementation is not
a guarantee of safety for every vulnerability. The complete candidate catalog,
exclusions, provenance, and tokenizer checks are retained in the
[prepared bundle](../../../../../../datasets/pruned/cweval/README.md).

Both models evaluate the same ordered functions. The paired analysis is a small,
filtered diagnostic; it does not establish a causal effect of LLM authorship.
See the [consolidated RQ findings and CWEval pair analysis](../../../../../findings/rq1_answer.md#cweval-pair-analysis).

## License and citation

CWEval uses the [Apache 2.0 license](../../../../../../datasets/pruned/cweval/UPSTREAM_LICENSE).

```bibtex
@misc{peng2025cwevaloutcomedrivenevaluationfunctionality,
  title={CWEval: Outcome-driven Evaluation on Functionality and Security of LLM Code Generation},
  author={Jinjun Peng and Leyi Cui and Kele Huang and Junfeng Yang and Baishakhi Ray},
  year={2025},
  eprint={2501.08200},
  archivePrefix={arXiv},
  primaryClass={cs.SE},
  url={https://arxiv.org/abs/2501.08200},
}
```
