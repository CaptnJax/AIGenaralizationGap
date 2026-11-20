import os
os.environ['TOKENIZERS_PARALLELISM']='false'
import sys, multiprocessing as mp, json, random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tmp/vulberta_diagnostic_libs'))

def worker(conn, options):
    from clang import cindex
    from tokenizers import Tokenizer, NormalizedString
    from tokenizers.pre_tokenizers import PreTokenizer
    class Lex:
        cidx=cindex.Index.create()
        def split(self,i,s):
            tu=self.cidx.parse('tmp.c',args=[''],unsaved_files=[('tmp.c',str(s.original))],options=options)
            return [NormalizedString(t.spelling.strip()) for t in tu.get_tokens(extent=tu.cursor.extent) if t.spelling.strip()]
        def pre_tokenize(self,p): p.split(self.split)
    t=Tokenizer.from_str((root/'tmp/vulberta_tokenizer.json').read_text(encoding='utf-8-sig'))
    t.pre_tokenizer=PreTokenizer.custom(Lex())
    t.no_padding(); t.no_truncation()
    conn.send('ready')
    while True:
        code=conn.recv()
        if code is None: break
        try: conn.send({'ids':t.encode(code).ids})
        except Exception as e: conn.send({'error':repr(e)})

def start(options):
    a,b=mp.Pipe();p=mp.Process(target=worker,args=(b,options));p.start()
    assert a.poll(20) and a.recv()=='ready'
    return a,p

if __name__=='__main__':
    import pandas as pd
    contexts=[start(0),start(64)]
    report={'compared':0,'identical':0,'mismatches':[], 'timeouts':[], 'errors':[]}
    try:
        for name in ['primevul_test','llmvul_test']:
            df=pd.read_csv(root/f'prepared_datasets/vulberta/{name}.csv',keep_default_na=False)
            indices=set(random.Random(42).sample(range(len(df)),256))
            if name=='llmvul_test': indices.update(range(9680,9744))
            for i in sorted(indices):
                row=df.iloc[i]
                for conn,p in contexts: conn.send(row.func)
                values=[]
                for j,(conn,p) in enumerate(contexts):
                    if conn.poll(3): values.append(conn.recv())
                    else:
                        report['timeouts'].append({'dataset':name,'row':i,'id':row.sample_id,'options':j*64})
                        p.terminate();p.join();conn.close();contexts[j]=start(j*64)
                        values.append(None)
                report['compared']+=1
                if all(v is not None and 'ids' in v for v in values):
                    if values[0]['ids']==values[1]['ids']: report['identical']+=1
                    else: report['mismatches'].append({'dataset':name,'row':i,'id':row.sample_id,'lengths':[len(v['ids']) for v in values]})
                elif any(v is not None and 'error' in v for v in values): report['errors'].append({'dataset':name,'row':i,'values':values})
        print(json.dumps(report,indent=2),flush=True)
        (root/'tmp/vulberta_tokenizer_fix_check.json').write_text(json.dumps(report,indent=2))
    finally:
        for conn,p in contexts:
            p.terminate();p.join();conn.close()
