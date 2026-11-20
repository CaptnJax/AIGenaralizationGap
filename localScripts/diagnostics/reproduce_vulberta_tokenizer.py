import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
import sys, time, json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'tmp/vulberta_diagnostic_libs'))
import pandas as pd
from tokenizers import Tokenizer, NormalizedString
from tokenizers.pre_tokenizers import PreTokenizer
from clang import cindex

class ClangPreTokenizer:
    cidx = cindex.Index.create()
    def clang_split(self, i, normalized_string):
        print('  CLANG PARSE', flush=True)
        tu = self.cidx.parse('tmp.c', args=[''],
            unsaved_files=[('tmp.c', str(normalized_string.original))], options=int(os.environ.get('CLANG_OPTIONS','0')))
        print('  CLANG TOKENS', flush=True)
        tokens=[NormalizedString(t.spelling.strip()) for t in tu.get_tokens(extent=tu.cursor.extent) if t.spelling.strip()]
        print('  CLANG COMPLETE',len(tokens), flush=True)
        return tokens
    def pre_tokenize(self, pretok):
        pretok.split(self.clang_split)

tokenizer=Tokenizer.from_str((root/'tmp/vulberta_tokenizer.json').read_text(encoding='utf-8-sig'))
tokenizer.pre_tokenizer=PreTokenizer.custom(ClangPreTokenizer())
tokenizer.enable_truncation(max_length=1024)
tokenizer.enable_padding(length=1024, pad_id=1, pad_token='<pad>')
df=pd.read_csv(root/'prepared_datasets/vulberta/llmvul_test.csv',keep_default_na=False)
start=int(sys.argv[1]) if len(sys.argv)>1 else 9680
stop=int(sys.argv[2]) if len(sys.argv)>2 else 9744
for i in range(start,stop):
    print('START',i,df.iloc[i].sample_id,flush=True)
    t=time.monotonic()
    result=tokenizer.encode(df.iloc[i].func)
    print('DONE',i,round(time.monotonic()-t,3),len(result.ids),flush=True)
