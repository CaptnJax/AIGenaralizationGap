"""Download documented public control/training sources; never execute source code."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

import rq1_priority1_audit as c

RUN = (c.ROOT / os.environ.get('RQ1_CONTROL_RUN', 'reproductions/rq1_controls')).resolve()
if not RUN.is_relative_to(c.ROOT/'reproductions'):
    raise ValueError('RQ1_CONTROL_RUN must be a directory under this checkout\'s reproductions/.')
CG = 'ac74a62802a0dd159b3258c78a2df8ad36cdf2b9'
VB = '75ab355bf8be124751084c0ff3563df24f48fe38'
SOURCES = {
    'devign': ('Devign.json', '1x6hoF7G-tSYxg8AFybggypLZgMGDNHfF'),
    'bigvul_train': ('bigvul_train.csv', '1ldXyFvHG41VMrm260cK_JEPYqeb6e6Yw'),
    'bigvul_valid': ('bigvul_valid.csv', '1yggncqivMcP0tzbh8-8Eu02Edwcs44WZ'),
}


def digest(path):
    with c.input_path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def source_path(filename):
    """Read a run-local source when present, otherwise the shipped source."""
    from rq1_paths import raw_source
    local = RUN / 'sources' / filename
    bundled = raw_source(filename)
    return local if local.exists() or bundled is None else bundled


def protocol_evidence():
    directory=c.HERE/'results/rq1_priority1_20261028_verified/reference_sources'
    notes=[]
    for name in ['vulberta_finetuning.ipynb','vulberta_evaluation.ipynb']:
        path=directory/name
        cells=[''.join(x.get('source',[])) for x in c.read_json(path)['cells']]
        notes.append(dict(file=path.relative_to(c.ROOT).as_posix(),sha256=digest(path),
            relevant_cells=[x for x in cells if any(k in x for k in ["mydataset =='devign'","mydataset=='devign'",'training_args =','trainer ='])]))
    record=dict(documented_procedure=dict(
        linevul='checkpoint-best-f1 saved when evaluation/validation F1 improves; published command supplies separate train/eval/test files',
        vulberta='Devign train.txt for fitting; valid.txt for evaluation; load_best_model_at_end=True; separate evaluation notebook uses test.txt'),
        qualification='Documentation evidence, not actual checkpoint-run attestation. The author OneDrive data/model bundle was not byte-verified. The converted checkpoint names CodeXGLUE Devign; official CodeXGLUE data/splits were used. No control scores selected a checkpoint here.',
        notebooks=notes)
    c.write_json(RUN/'checkpoint_selection.json',record)


def download(name):
    directory = RUN / 'sources'
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = source_path(name + '.manifest.json')
    if manifest_path.exists():
        old = c.read_json(manifest_path)
        data_path = source_path(old['file'])
        if not data_path.exists() and data_path.with_suffix(data_path.suffix + '.gz').exists():
            raise FileNotFoundError('Restore the lossless training CSV first; see datasets/raw/BigVul/README.md.')
        assert digest(data_path) == old['sha256']
        print('Already verified:', name, flush=True)
        return
    if name in SOURCES:
        import gdown
        filename, gid = SOURCES[name]
        url = 'https://drive.google.com/uc?id=' + gid
        dest = directory / filename
        assert not dest.exists(), 'Unmanifested destination; inspect before replacing.'
        temp = directory / (filename + '.partial')
        print('Downloading', name, url, flush=True)
        result = gdown.download(url, str(temp), quiet=True, resume=True)
        assert result and temp.stat().st_size > 10000
        temp.replace(dest)
    else:
        files = [('codexglue_' + split + '.txt', f'https://raw.githubusercontent.com/microsoft/CodeXGLUE/{CG}/Code-Code/Defect-detection/dataset/{split}.txt') for split in ('train', 'valid', 'test')]
        files += [
            ('codexglue_preprocess.py.txt', f'https://raw.githubusercontent.com/microsoft/CodeXGLUE/{CG}/Code-Code/Defect-detection/dataset/preprocess.py'),
            ('vulberta_data_README.md', f'https://raw.githubusercontent.com/ICL-ml4csec/VulBERTa/{VB}/data/README.md'),
            ('vulberta_checkpoint_README.md', f'https://huggingface.co/claudios/VulBERTa-MLP-Devign/raw/{c.VB_REV}/README.md'),
        ]
        entries = []
        for filename, url in files:
            dest = directory / filename
            if not dest.exists():
                with urllib.request.urlopen(url, timeout=90) as response:
                    data = response.read()
                dest.write_bytes(data)
            entries.append(dict(file=filename, url=url, bytes=dest.stat().st_size, sha256=digest(dest)))
        c.write_json(directory / 'documentation.json', entries)
        protocol_evidence()
        print(json.dumps(entries), flush=True)
        return
    entry = dict(file=filename, url=url, bytes=dest.stat().st_size, sha256=digest(dest),
                 provenance='Official documentation download link; content hash records this retrieval, not historical training attestation.')
    c.write_json(directory / (name + '.manifest.json'), entry)
    print(json.dumps(entry), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', choices=[*SOURCES, 'documentation'])
    download(parser.parse_args().source)
