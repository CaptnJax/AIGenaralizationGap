---
license: mit
arxiv: 2205.12424
datasets:
- code_x_glue_cc_defect_detection
metrics:
- accuracy
- precision
- recall
- f1
- roc_auc
model-index:
  - name: VulBERTa MLP
    results:
      - task:
          type: defect-detection
        dataset:
          name: codexglue-devign
          type: codexglue-devign
        metrics:
          - name: Accuracy
            type: Accuracy
            value: 64.71
          - name: Precision
            type: Precision
            value: 64.80
          - name: Recall
            type: Recall
            value: 50.76
          - name: F1
            type: F1
            value: 56.93
          - name: ROC-AUC
            type: ROC-AUC
            value: 71.02
pipeline_tag: text-classification
tags:
- devign
- defect detection
- code
---

# VulBERTa MLP Devign

This is an RQ1-focused excerpt of the [upstream checkpoint card](https://huggingface.co/claudios/VulBERTa-MLP-Devign/blob/fecabdee24a3ef6e804d7629d6eed03dc6b4f61e/README.md).
The benchmark metadata above is retained for checkpoint provenance.

## VulBERTa: Simplified Source Code Pre-Training for Vulnerability Detection

![VulBERTa architecture](https://raw.githubusercontent.com/ICL-ml4csec/VulBERTa/main/VB.png)

## Overview
This model is the unofficial HuggingFace version of "[VulBERTa](https://github.com/ICL-ml4csec/VulBERTa/tree/main)" with an MLP classification head, trained on CodeXGlue Devign (C code), by Hazim Hanif & Sergio Maffeis (Imperial College London). I simplified the tokenization process by adding the cleaning (comment removal) step to the tokenizer and added the simplified tokenizer to this model repo as an AutoClass.

## RQ1 evaluation

RQ1 uses the frozen `claudios/VulBERTa-MLP-Devign` checkpoint at revision
`fecabdee24a3ef6e804d7629d6eed03dc6b4f61e`. The local runner loads its custom
tokenizer, applies the authors' explicit cleaning step and the Clang tokenizer
fix, and uses a 1,024-token input limit, seed 42, and `p(vulnerable) > 0.5`.

Follow the [RQ1 runner instructions](../../../../../localScripts/README.md) for
the installed dependencies and evaluation commands. The
[authors' evaluation notebook](https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb)
provides the preprocessing reference. Completed results, including the official
Devign test control, are summarized in the
[RQ1 findings](../../../../findings/rq1_answer.md).

## Citation

Accepted as conference paper (oral presentation) at the International Joint Conference on Neural Networks (IJCNN) 2022.  
Link to paper: https://ieeexplore.ieee.org/document/9892280  


```bibtex
@INPROCEEDINGS{hanif2022vulberta,
  author={Hanif, Hazim and Maffeis, Sergio},
  booktitle={2022 International Joint Conference on Neural Networks (IJCNN)}, 
  title={VulBERTa: Simplified Source Code Pre-Training for Vulnerability Detection}, 
  year={2022},
  volume={},
  number={},
  pages={1-8},
  doi={10.1109/IJCNN55064.2022.9892280}
  
}
```
