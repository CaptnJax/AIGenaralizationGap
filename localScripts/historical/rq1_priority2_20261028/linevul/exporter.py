"""Export frozen LineVul probabilities with exact historical prediction checks."""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import rq1_priority1_audit as common


def run(output):
    os.environ.update(HF_HOME=str(common.CACHE/'huggingface'), HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', USE_TF='0', TOKENIZERS_PARALLELISM='false')
    import torch
    from transformers import RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer, set_seed
    baseline = common.read_json(common.HERE/'reports/rq1_priority1_summary.json')
    output.mkdir(parents=True, exist_ok=True)
    directory = output/'linevul'
    directory.mkdir(exist_ok=False)
    shutil.copyfile(__file__, directory/'exporter.py')
    checkpoint = common.LV/'saved_models/checkpoint-best-f1/12heads_linevul_model.bin'
    jobs = [j for j in baseline['jobs'] if j['model'] == 'linevul']
    for job in jobs:
        assert common.sha(common.ROOT/job['dataset']) == job['dataset_sha256']
        assert common.sha(checkpoint) == job['signature']['checkpoint_sha256']
        assert common.sha(common.LV/'linevul_main_local.py') == job['signature']['implementation_sha256']
    for asset in baseline['assets']:
        assert common.sha(common.ROOT/asset['path']) == asset['sha256']
    set_seed(42)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    sys.path.insert(0, str(common.LV))
    line = common.load_module(common.LV/'linevul_main_local.py', 'score_linevul')
    tokenizer = RobertaTokenizer.from_pretrained(str(common.CB), local_files_only=True)
    config = RobertaConfig.from_pretrained(str(common.CB), local_files_only=True)
    config.num_labels, config.num_attention_heads = 1, 12
    args = SimpleNamespace(use_word_level_tokenizer=False, block_size=512)
    model = line.Model(RobertaForSequenceClassification(config), config, tokenizer, args)
    line._load_local_checkpoint(model, torch.load(checkpoint, map_location='cpu', weights_only=True))
    model.to(device).eval()
    summary = dict(status='running', device=device, batch_size=16, threshold=0.5, seed=42,
                   checkpoint_sha256=common.sha(checkpoint), tokenizer_revision=common.CB_REV,
                   exporter_sha256=common.sha(Path(__file__)), jobs=[])
    common.write_json(directory/'manifest.json', summary)
    cohort = common.read_csv(common.HERE/'results/rq1_priority1_20261028_verified/inference_predictions.csv')
    for job in jobs:
        rows = common.read_csv(common.ROOT/job['dataset'])
        historical = common.read_csv(common.ROOT/job['prediction_file']['path'])
        stem = Path(job['dataset']).stem
        source_indices = (common.read_json(common.CACHE/'data/bigvul_test_sample_2000.selection.json')
                          ['source_row_indices_zero_based'] if stem.startswith('bigvul') else None)
        parity = {int(r['row']):float(r['probability_batch16']) for r in cohort if r['job'] == job['job']}
        changes, max_parity_delta, max_sum_error = [], 0.0, 0.0
        destination = directory/(stem+'.csv')
        with destination.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['row','sample_id','label','prob_vulnerable','prediction','historical_prediction'])
            writer.writeheader()
            for start in range(0, len(rows), 16):
                selected = rows[start:start+16]
                ids = torch.tensor([line.convert_examples_to_features(r['processed_func'], int(r['target']), tokenizer, args).input_ids
                                    for r in selected], device=device)
                with torch.inference_mode():
                    probabilities = model(input_ids=ids)
                assert torch.isfinite(probabilities).all() and (probabilities>=0).all() and (probabilities<=1).all()
                max_sum_error = max(max_sum_error, float((probabilities.sum(-1)-1).abs().max().cpu()))
                for offset, score in enumerate(probabilities[:,1].cpu().tolist()):
                    i = start+offset
                    expected = common.binary(historical[i]['raw_preds'])
                    prediction = int(score > .5)
                    if prediction != expected:
                        changes.append(i)
                    if i in parity:
                        max_parity_delta = max(max_parity_delta, abs(score-parity[i]))
                    writer.writerow(dict(row=i, sample_id=rows[i].get('sample_id', 'bigvul-source:'+str(source_indices[i]) if source_indices else ''),
                                         label=int(rows[i]['target']), prob_vulnerable=score, prediction=prediction, historical_prediction=expected))
                if start % 1024 == 0:
                    handle.flush()
                    print(f'{stem}: {min(start+16,len(rows))}/{len(rows)}; prediction changes={len(changes)}', flush=True)
        result = dict(job=job['job'], rows=len(rows), dataset_sha256=job['dataset_sha256'],
                      prediction_changes=len(changes), changed_rows=changes, max_cohort_score_delta=max_parity_delta,
                      max_class_sum_error=max_sum_error, output_sha256=common.sha(destination))
        summary['jobs'].append(result)
        common.write_json(directory/'manifest.json', summary)
        print(json.dumps(result), flush=True)
    summary['status'] = 'pass' if all(j['prediction_changes']==0 and j['max_cohort_score_delta']<=1e-5
                                               and j['max_class_sum_error']<=1e-6 for j in summary['jobs']) else 'review_required'
    common.write_json(directory/'manifest.json', summary)
    return summary['status']=='pass'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.output.resolve()) else 1)
