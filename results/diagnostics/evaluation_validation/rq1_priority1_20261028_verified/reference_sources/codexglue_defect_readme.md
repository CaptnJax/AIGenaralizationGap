# CodeXGLUE Devign data for RQ1

This is an RQ1-focused guide adapted from the
[upstream dataset documentation](https://github.com/microsoft/CodeXGLUE/tree/ac74a62802a0dd159b3258c78a2df8ad36cdf2b9/Code-Code/Defect-detection).
The official Devign test split is the original-dataset control for the frozen
VulBERTa checkpoint; training and validation splits support overlap checks.

## Supplied files

Files are under `datasets/raw/Devign/` relative to the repository root:

- `Devign.json`: original function records, including `func`, `target`, project, and commit.
- `codexglue_train.txt`, `codexglue_valid.txt`, `codexglue_test.txt`: official source-row indices.
- `codexglue_preprocess.py.txt`: archived upstream preprocessing reference.
- `devign.manifest.json`: source identity, size, and hash.

| Split | Functions |
| --- | ---: |
| Train | 21,854 |
| Validation | 2,732 |
| Test | 2,732 |

`target=1` is the supplied vulnerable label; `target=0` is the supplied
non-vulnerable label. Retain the official indices and source order.

## Inspect the official test split

Run this Python 3.12 example from the repository root; no model libraries are needed.

```python
import json
from pathlib import Path

root = Path('datasets/raw/Devign')
source = json.loads((root / 'Devign.json').read_text(encoding='utf-8'))
splits = {name: set(map(int, (root / f'codexglue_{name}.txt').read_text().split()))
          for name in ('train', 'valid', 'test')}
assert [len(splits[s]) for s in ('train', 'valid', 'test')] == [21854, 2732, 2732]
assert not (splits['train'] & splits['valid'] or splits['train'] & splits['test'] or splits['valid'] & splits['test'])
assert set.union(*splits.values()) == set(range(len(source)))
test = [source[i] for i in sorted(splits['test'])]
print(f"Devign test: {len(test)} functions; {sum(row['target'] for row in test)} vulnerable")
```

The [prepared control inputs](../../../../../datasets/pruned/controls) contain the
JSONL records used for the saved evaluation. See the
[saved-metric verification](../../../../evaluation_runs/README.md#recalculate-the-published-metrics)
for recalculating its scores and the
[diagnostic reproduction requirements](../../../README.md#reproduction-requirements)
for rerunning the full control analysis.

## Reference
<pre><code>@inproceedings{zhou2019devign,
  title={Devign: Effective vulnerability identification by learning comprehensive program semantics via graph neural networks},
  author={Zhou, Yaqin and Liu, Shangqing and Siow, Jingkai and Du, Xiaoning and Liu, Yang},
  booktitle={Advances in Neural Information Processing Systems},
  pages={10197--10207},
  year={2019}
}</code></pre>
