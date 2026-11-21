# VulBERTa data provenance for RQ1

This is an RQ1-focused excerpt of the
[upstream data README](https://github.com/ICL-ml4csec/VulBERTa/blob/main/data/README.md).
It records the authors' [data archive](https://1drv.ms/u/s!AueKnGqzBuIVkq4B9ESELGQ-VtjIYA?e=f0moEm),
documented as containing `finetune`, `pretrain`, and `tokenizer` directories.

For RQ1, the frozen VulBERTa checkpoint is evaluated on the official CodeXGLUE
Devign test split. Its training and validation splits support the overlap
analysis. The [prepared control data](../../../../../datasets/pruned/controls)
and [control report](../../rq1_priority5_diagnostics.md)
document the actual evaluated inputs and the remaining source-attestation limits.
