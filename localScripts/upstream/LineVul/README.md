# LineVul source reference for RQ

This README is an RQ-focused excerpt adapted from the
[upstream LineVul documentation](https://github.com/awsm-research/LineVul).

## Checkpoint and inputs

RQ evaluates the frozen `12heads_linevul_model.bin` checkpoint with the
`microsoft/codebert-base` tokenizer and the original LineVul model wrapper.
The runner uses a 512-token input limit, seed 42, and `p(vulnerable) > 0.5`
for function-level classification.

The prepared CSVs provide `processed_func` as source code and `target` as the
binary label. `sample_id` preserves prediction alignment. Empty `flaw_line` and
`flaw_line_index` fields are compatibility placeholders; the RQ evaluation uses
function-level predictions.

## Reproduce RQ

Follow the [local evaluation instructions](../../README.md) for environment
setup, model downloads, dataset extraction, evaluation, and resuming.
Both frozen models are evaluated on PrimeVul and LLMVul. The full official
BigVul test set supplies the original-dataset control for LineVul.

- [Prepared dataset formats](../../../datasets/pruned/README.md).
- [BigVul source data and restoration](../../../datasets/raw/BigVul/README.md).
- [RQ findings and control results](../../../results/findings/rq1_answer.md).

## License

LineVul is distributed under the
[MIT License](https://github.com/awsm-research/LineVul/blob/main/LICENSE).

## Citation

```bibtex
@inproceedings{fu2022linevul,
  title={LineVul: A Transformer-based Line-Level Vulnerability Prediction},
  author={Fu, Michael and Tantithamthavorn, Chakkrit},
  booktitle={2022 IEEE/ACM 19th International Conference on Mining Software Repositories (MSR)},
  year={2022},
  organization={IEEE}
}
```
