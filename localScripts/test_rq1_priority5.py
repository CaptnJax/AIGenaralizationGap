"""Focused tests for matching, overlap exclusion, and clustered uncertainty."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import rq1_priority5_analysis as a
from rq1_priority5_profiles import language, line_bin


def row(sid,label=0,lang='c',length='01-10',score=.2):
    return dict(sample_id=sid,label=label,language=lang,length_bin=length,code_sha256=sid,token_sha256=sid,
                project='',commit_url='',cve='',group_id='',models={m:dict(score=score) for m in a.MODELS})


class PriorityFive(unittest.TestCase):
    def test_matching_balances_every_cell_and_excludes_unknown(self):
        left=[row('a'),row('b'),row('c',1),row('d',1),row('unknown',lang='missing')]
        right=[row('x'),row('y',1),row('z',1),row('long',length='101+')]
        out,cells=a.matching({'left':left,'right':right})
        self.assertEqual(len(cells),2)
        for name,(rs,w) in out.items():
            self.assertAlmostEqual(sum(w),3)
            self.assertAlmostEqual(sum(v*r['label'] for r,v in zip(rs,w)),2)
            self.assertTrue(all(r['language']!='missing' and r['length_bin']=='01-10' for r in rs))
        self.assertEqual(out['left'][1].tolist(),[.5,.5,1.,1.])

    def test_no_common_support_is_empty(self):
        out,cells=a.matching({'a':[row('a')],'b':[row('b',lang='cpp')]})
        self.assertEqual(cells,[])
        self.assertTrue(all(len(rs)==len(w)==0 for rs,w in out.values()))

    def test_overlap_uses_own_training_and_validation(self):
        r=row('a');r['overlap']={name:{'token_sha256':False} for name in ['bigvul_train','bigvul_valid','devign_train','devign_valid']}
        r['overlap']['bigvul_valid']['token_sha256']=True
        self.assertFalse(a.novel(r,'linevul'))
        self.assertTrue(a.novel(r,'vulberta'))

    def test_transitive_related_and_task_grouping(self):
        rows=[row(str(i),i%2) for i in range(5)]
        rows[0]['token_sha256']=rows[1]['token_sha256']='duplicate'
        rows[1]['commit_url']=rows[2]['commit_url']='commit'
        rows[3]['group_id']=rows[4]['group_id']='task-family'
        ids,info=a.groups(rows)
        self.assertEqual(info['groups'],2)
        self.assertEqual(ids[0],ids[2]);self.assertEqual(ids[3],ids[4]);self.assertNotEqual(ids[2],ids[3])

    def test_language_basis_and_length_boundaries(self):
        self.assertEqual(language({'file_name':'file.cpp','source_language':'C'}),('cpp','file_extension'))
        self.assertEqual(language({'file_name':'unknown','source_language':None}),('missing','unavailable'))
        self.assertEqual([line_bin(x) for x in [10,11,25,26,50,51,100,101]],['01-10','11-25','11-25','26-50','26-50','51-100','51-100','101+'])

    def test_positive_only_recall_is_defined(self):
        rows=[row('a',1,score=.9),row('b',1,score=.5)]
        value=a.measured(rows,'linevul')
        self.assertEqual(value['recall'],.5)
        self.assertIsNone(value['roc_auc'])

    def test_paired_bootstrap_and_undefined_precision(self):
        rows=[row(str(i),i%2,score=.2) for i in range(8)]
        with tempfile.TemporaryDirectory() as temp,patch.object(a,'RUN',Path(temp)),patch.dict(a.PLAN,bootstrap_repetitions=100):
            out=a.bootstrap(rows,a.MODELS,np.ones(8),'fixture',123)
            self.assertEqual(out['intervals']['linevul']['precision']['undefined_replicates'],100)
            for metric in ['roc_auc','average_precision','f1','brier']:
                ci=out['paired_linevul_minus_vulberta'][metric]
                self.assertEqual(ci['low'],0);self.assertEqual(ci['high'],0)
            self.assertEqual(out,a.bootstrap(rows,a.MODELS,np.ones(8),'fixture',123))


if __name__=='__main__':unittest.main()
