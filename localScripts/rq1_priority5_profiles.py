"""Profile control and documented training data; build auditable overlap screens."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re

import rq1_priority2_audit as p2
import rq1_priority4_audit as p4
from rq1_priority5_controls import RUN, P2, P4, jsonl, prepare
from rq1_priority5_sources import digest

c=p2.common


def language(row):
    suffix=Path(str(row.get('file_name') or '')).suffix.lower()
    if suffix=='.c': return 'c','file_extension'
    if suffix in {'.cc','.cpp','.cxx','.hpp','.hh','.hxx'}: return 'cpp','file_extension'
    declared=str(row.get('source_language') or '').lower()
    if declared in {'c','c++','cpp'}: return ('cpp' if declared in {'cpp','c++'} else 'c'),'source_declaration'
    return 'missing','unavailable'


def line_bin(lines):
    return next(label for upper,label in [(10,'01-10'),(25,'11-25'),(50,'26-50'),(100,'51-100'),(float('inf'),'101+')] if lines<=upper)


def big_rows(path, stem):
    csv.field_size_limit(100000000)
    with path.open(encoding='utf-8',newline='') as f:
        for i,r in enumerate(csv.DictReader(f)):
            yield dict(sample_id=stem+':'+str(i), row=i, dataset=stem, code=r['processed_func'], label=int(r['target']),
                source_language=r['lang'], project=r['project'], commit_url=r['codeLink'], commit_id=r['commit_id'],
                cwe=r['CWE ID'], cve=r['CVE ID'], file_name=r['file_name'], original_index=r['index'], group_id='',
                code_sha256=c.code_sha(r['processed_func']), label_evidence='vulnerability-commit changed-line association', context_scope='unreviewed')


def profile(stem):
    prepare()
    directory=RUN/'profiles'; directory.mkdir(exist_ok=True)
    input_path = RUN/('sources/'+stem+'.csv' if stem.startswith('bigvul_') and stem!='bigvul_test' else 'inputs/'+stem+'.jsonl')
    if stem.startswith('bigvul_') and stem!='bigvul_test':
        assert digest(input_path)==c.read_json(RUN/'sources'/(stem+'.manifest.json'))['sha256']
    source_hash=digest(input_path)
    manifest=directory/(stem+'.manifest.json'); output=directory/(stem+'.jsonl')
    if manifest.exists():
        m=c.read_json(manifest)
        assert m['source_sha256']==source_hash and m['profile_sha256']==digest(output)
        print('Verified existing profiles:',stem,flush=True); return
    implementations=RUN/'implementations';implementations.mkdir(exist_ok=True)
    implementation_hash=digest(__file__)
    (implementations/('profile_'+implementation_hash+'.py')).write_bytes(Path(__file__).read_bytes())
    rows=big_rows(input_path,stem) if input_path.suffix=='.csv' else jsonl(input_path)
    parser_map=p2.parsers(); counts=Counter(); n=0
    with output.open('w',encoding='utf-8') as f:
        for r in rows:
            lang,source=language(r)
            result=p4.token_profile(r.pop('code'),lang,parser_map)
            r.update(result,language=lang,language_basis=source,length_bin=line_bin(result['source_lines']))
            f.write(json.dumps(r,ensure_ascii=False)+'\n'); n+=1; counts[r['label']]+=1
            if n%5000==0: f.flush(); print('Profile',stem,n,flush=True)
    c.write_json(manifest,dict(rows=n,labels=dict(counts),source_sha256=source_hash,profile_sha256=digest(output),
        implementation_sha256=digest(__file__), tokenizer_profile_implementation_sha256=digest(p4.__file__)))
    print('Profile complete:',stem,n,flush=True)


def external_profiles():
    directory=RUN/'profiles'; directory.mkdir(exist_ok=True)
    structure={r['sample_id']:r for r in jsonl(P4/'row_structure.jsonl')}
    for stem in ['primevul_test','llmvul_test','cweval_test']:
        path=directory/(stem+'.jsonl')
        rows=[]
        for old in jsonl(P2/'profiles'/(stem+'.jsonl')):
            r={k:v for k,v in old.items() if k not in ['linevul','vulberta','call_expressions','source_type_references','cve_desc','flaw_line']}
            r.update(structure[r['sample_id']]);r['source_language']=old.get('source_language')
            r['language'],r['language_basis']=language(r);r['length_bin']=line_bin(r['source_lines'])
            r['label_evidence']={'primevul_test':'security-fix / NVD association; row-specific rule absent',
                'llmvul_test':'two-of-three analyzer votes', 'cweval_test':'task-scoped paired intended behavior'}[stem]
            r['context_scope']='unreviewed'
            rows.append(r)
        p4.jsonl_out(path,rows)
        c.write_json(directory/(stem+'.manifest.json'),dict(rows=len(rows),profile_sha256=digest(path),
            source_sha256=digest(P2/'profiles'/(stem+'.jsonl')),structure_sha256=digest(P4/'row_structure.jsonl')))


def overlap():
    """One row per eval/source pair; sample match IDs, totals and label conflicts."""
    external_profiles()
    fields=['code_sha256','token_sha256','structural_sha256']
    eval_sets=['bigvul_test','devign_test','primevul_test','llmvul_test','cweval_test']
    output=RUN/'overlap.jsonl';summary=[];domain=[]
    def metadata_keys(r):
        project=str(r.get('project') or '').strip().lower()
        if project in p4.MISSING: project=''
        commits=re.findall(r'[0-9a-f]{40}',str(r.get('commit_id') or r.get('commit_url') or ''),flags=re.I)
        cves=re.findall(r'CVE-\d{4}-\d{4,}',str(r.get('cve') or ''),flags=re.I)
        return dict(project={project} if project else set(),commit={x.lower() for x in commits},cve={x.upper() for x in cves})
    with output.open('w',encoding='utf-8') as f:
        for train in ['bigvul_train','bigvul_valid','devign_train','devign_valid']:
            path=RUN/'profiles'/(train+'.jsonl')
            assert digest(path)==c.read_json(path.with_suffix('.manifest.json'))['profile_sha256']
            lookup={field:defaultdict(list) for field in fields}; source_rows=0
            meta={key:set() for key in ['project','commit','cve']}
            for r in jsonl(path):
                source_rows+=1
                for field in fields:
                    lookup[field][r[field]].append((r['sample_id'],r['label']))
                for key,values in metadata_keys(r).items():meta[key].update(values)
            for stem in eval_sets:
                counts=Counter();n=0;metadata_counts=Counter()
                for r in jsonl(RUN/'profiles'/(stem+'.jsonl')):
                    n+=1; record=dict(dataset=stem,sample_id=r['sample_id'],label=r['label'],source=train)
                    for key,values in metadata_keys(r).items():
                        metadata_counts[key+'_missing']+=not values
                        metadata_counts[key+'_shared_rows']+=bool(values & meta[key])
                        metadata_counts[key+'_shared_positive']+=r['label']*bool(values & meta[key])
                    for field in fields:
                        hits=lookup[field].get(r[field],[])
                        record[field]=dict(matches=len(hits),sample_ids=[x[0] for x in hits[:5]],label_conflict=any(x[1]!=r['label'] for x in hits))
                        if hits: counts[field]+=1;counts[field+'_positive']+=r['label']
                        if record[field]['label_conflict']: counts[field+'_conflict']+=1
                    f.write(json.dumps(record)+'\n')
                summary.append(dict(dataset=stem,source=train,eval_rows=n,source_rows=source_rows,counts=dict(counts)))
                domain.append(dict(dataset=stem,source=train,eval_rows=n,source_distinct={k:len(v) for k,v in meta.items()},counts=dict(metadata_counts)))
            print('Overlap screened:',train,source_rows,flush=True)
    c.write_json(RUN/'overlap_summary.json',dict(comparisons=summary,artifact_sha256=digest(output),
        scope='Documented fine-tuning train/validation data; no exhaustive pretraining or semantic-clone audit. Structural matches are candidates, not validated duplicates.'))
    c.write_json(RUN/'domain_exposure.json',dict(comparisons=domain,
        scope='Exact normalized project names, full commit IDs and supplied CVEs. Shared provenance is not evidence of direct code duplication or independently verified shortcut learning. Project aliases are not resolved.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['bigvul_test','devign_test','devign_train','devign_valid','bigvul_train','bigvul_valid','external','overlap'])
    stage=parser.parse_args().stage
    if stage=='external': external_profiles()
    elif stage=='overlap': overlap()
    else: profile(stage)
