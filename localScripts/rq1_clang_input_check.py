"""Bounded subprocess checks of Clang lexical preservation under the RQ1 fix."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import subprocess
import sys

import rq1_priority2_audit as audit


def worker(path):
    from clang import cindex
    row=audit.common.read_json(path)
    index=cindex.Index.create()
    clean=audit.cwe.load_preprocessing()['clean_for_vulberta']
    raw=row['code']
    cooked=clean(raw)
    streams={}
    for stage,code in [('raw',raw),('cleaned',cooked)]:
        for language,skip in [('c',True),('c',False),('cpp',True)]:
            streams[(stage,language,skip)]=audit.lexical_clang(index,code,language,skip)
    checks={stage+'_skip_matches_full':streams[(stage,'c',True)]==streams[(stage,'c',False)] for stage in ('raw','cleaned')}
    checks.update({stage+'_c_matches_cpp':streams[(stage,'c',True)]==streams[(stage,'cpp',True)] for stage in ('raw','cleaned')})
    if row['sample_id']=='fixture:body':
        checks['body_retained']=streams[('raw','c',True)].count('BODY_TOKEN')==2
    print(json.dumps(dict(sample_id=row['sample_id'],checks=checks,token_counts={str(k):len(v) for k,v in streams.items()})))


def run(output):
    _,_,datasets=audit.load_data()
    meta=audit.metadata()
    rng=random.Random(42)
    selected=[dict(sample_id='fixture:body',code='int f(){ int BODY_TOKEN=3; return BODY_TOKEN; }'),
              dict(sample_id='fixture:cpp',code='int f(){ auto g=[](){ return 3; }; return g(); }'),
              dict(sample_id='fixture:literal',code='const char *f(){ return "https://host/*literal*/"; }'),
              dict(sample_id='fixture:macro',code='#define VALUE 2\nint f(){ return VALUE; }')]
    for stem,rows in datasets.items():
        for language in ('c','cpp'):
            pool=[]
            for i,r in enumerate(rows):
                code=r['processed_func']
                source=meta[stem][i]['source_language']
                inferred=('cpp' if '::' in code or 'std::' in code else 'c') if source is None else source.lower()
                if inferred in ('c++','CPP'):
                    inferred='cpp'
                if inferred==language and len(code)<5000:
                    pool.append(dict(sample_id=r['sample_id'],dataset=stem,source_language=source,code=code))
            selected.extend(rng.sample(pool,min(4,len(pool))))
    directory=output/'clang_checks'
    directory.mkdir(exist_ok=False)
    paths=[]
    for i,row in enumerate(selected):
        path=directory/(str(i)+'.json')
        audit.common.write_json(path,row)
        paths.append(path)
    def launch(path):
        try:
            r=subprocess.run([sys.executable,__file__,'--worker',str(path)],capture_output=True,text=True,timeout=20)
            if r.returncode:
                return dict(input=path.name,status='error',stderr=r.stderr[-1500:])
            return dict(input=path.name,status='complete',**json.loads(r.stdout))
        except subprocess.TimeoutExpired:
            return dict(input=path.name,status='timeout',seconds=20)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(launch,paths))
    summary=dict(rows=len(results),timeouts=sum(r['status']=='timeout' for r in results),
                 errors=sum(r['status']=='error' for r in results),
                 discrepancies=sum(not all(r.get('checks',{}).values()) for r in results if r['status']=='complete'),
                 results=results,script_sha256=audit.common.sha(Path(__file__)))
    audit.common.write_json(directory/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',type=Path)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker)
    else:
        run(args.output.resolve())
