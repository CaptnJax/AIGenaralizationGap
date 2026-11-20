"""Preserve compact priority-one results outside the ignored run directory."""
import hashlib
import json
from pathlib import Path
import subprocess

run = Path(__file__).resolve().parent
root = run.parents[2]

def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

artifact = json.loads((run/'artifact_audit.json').read_text(encoding='utf-8'))
inference = json.loads((run/'inference_audit.json').read_text(encoding='utf-8'))
assert artifact['status'] == inference['status'] == 'pass'
upstream = root/'localScripts/.cache/LineVul'
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip()
assert commit == '9401ec6e60b762a9308645961268203244bee048'
upstream_files = []
for relative in ('linevul/linevul_main.py', 'linevul/linevul_model.py'):
    blob = subprocess.check_output(['git', 'show', f'{commit}:{relative}'], cwd=upstream)
    local = (upstream/relative).read_bytes()
    assert blob.replace(b'\r\n', b'\n') == local.replace(b'\r\n', b'\n')
    upstream_files.append(dict(path=relative, current_sha256=sha(upstream/relative),
                               git_blob_sha256=hashlib.sha256(blob).hexdigest(), normalized_content_matches=True))
sources = [
    ('vulberta_finetuning.ipynb', 'https://github.com/ICL-ml4csec/VulBERTa/blob/main/Finetuning_VulBERTa-MLP.ipynb'),
    ('vulberta_evaluation.ipynb', 'https://github.com/ICL-ml4csec/VulBERTa/blob/main/Evaluation_VulBERTa-MLP.ipynb'),
    ('codexglue_defect_readme.md', 'https://github.com/microsoft/CodeXGLUE/blob/main/Code-Code/Defect-detection/README.md'),
]
semantics = dict(
    reviewed_date='2026-10-28',
    mapping={'0': 'non-vulnerable/reference for the specified task', '1': 'vulnerable/unsafe'},
    evidence=[dict(file='reference_sources/'+name, url=url, sha256=sha(run/'reference_sources'/name)) for name, url in sources],
    model_card_url='https://huggingface.co/claudios/VulBERTa-MLP-Devign',
    method='Read source-label conversion, upstream training/evaluation code, CodeXGLUE label definition, and two source-matched CWEval pairs.',
    findings=[
        'LineVul passes integer target directly to cross entropy and explicitly treats class 1 as vulnerable.',
        'VulBERTa Devign training uses target unchanged with class-indexed cross entropy; upstream evaluation uses probability column 1.',
        'CodeXGLUE documents label 1 as insecure and label 0 as secure; the conversion model card identifies the Devign checkpoint.',
        'CWEval y_negative is the unsafe variant name and correctly maps to positive label 1.',
        'CWE-120 reference uses destination buffer_size as snprintf bound; unsafe variant uses source-name length instead.',
        'CWE-476 reference checks malloc failure before access; unsafe variant omits the null check. The reference is only scoped to this CWE.',
    ],
    limitations=['Upstream documentation was retrieved at main/current, not independently linked byte-for-byte to the original training execution.',
                 'Original-author weights were not compared byte-for-byte with the unofficial converted checkpoint.',
                 'CWEval source inspection corroborates label meaning; security tests and human label adjudication were not performed.'])
(run/'label_semantics.json').write_text(json.dumps(semantics, indent=2), encoding='utf-8')
summary = dict(
    date='2026-10-28', scope='RQ1 diagnostic plan priority 1 only',
    conclusion='No binary-evaluation defect detected; historical provenance is partially incomplete.',
    run_directory=run.relative_to(root).as_posix(),
    artifact_check_count=len(artifact['checks']), inference_check_count=len(inference['checks']),
    failures=0, evaluated_prediction_rows=sum(j['rows'] for j in artifact['jobs']),
    selected_model_function_cases=sum(j['selected_rows'] for j in inference['jobs']),
    reproduced_original_batch_rows=sum(j['original_batch_rows'] for j in inference['jobs']),
    environment=dict(python=artifact['python'], packages=artifact['packages'], device=inference['device'], gpu=inference['gpu']),
    jobs=artifact['jobs'], inference=inference, artifact_checks=artifact['checks'], assets=artifact['assets'],
    label_semantics=semantics, linevul_upstream=dict(commit=commit, files=upstream_files),
    test_suite=dict(command='.\\localScripts\\.venv\\Scripts\\python.exe -m unittest discover -s localScripts -p test_local.py -v',
                    tests=10, failures=0, errors=0, note='Sandbox blocked temporary-file I/O; approved unrestricted rerun passed all ten tests.'),
    limitations=artifact['limitations']+[
        'Exact early LineVul launcher bytes (three jobs) could not be recovered; exact inference implementation bytes are available for all seven.',
        'Inference cohort is stratified and not a statistical sample for estimating full-dataset performance.',
        'No dataset-wide semantic preprocessing/truncation audit or independent ground-truth review was performed in priority 1.'],
    initial_audit_note='The first audit assumed tokenizer bos/eos properties were populated. VulBERTa backend inserts IDs 0/2 despite null properties. The assertion was corrected to actual checkpoint token IDs; initial outputs are retained in the sibling run directory.',
    artifact_files={name:sha(run/name) for name in ('artifact_audit.json', 'inference_audit.json', 'cohort.json', 'inference_predictions.csv', 'checks.csv', 'label_semantics.json')})
target = root/'localScripts/reports/rq1_priority1_summary.json'
assert not target.exists()
target.write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n', encoding='utf-8')
print(json.dumps(dict(summary=str(target), checks=summary['artifact_check_count']+summary['inference_check_count'], failures=0)))
