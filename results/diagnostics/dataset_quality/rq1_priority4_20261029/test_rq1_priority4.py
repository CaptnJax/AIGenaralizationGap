"""Numerical and parsing edge cases for the label/construction audit."""
import unittest
import rq1_priority4_audit as a


class Priority4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsers=a.p2.parsers()

    def test_all_analyzer_combinations(self):
        expected={'000':'safe','001':'uncertain','010':'uncertain','100':'uncertain',
                  '011':'vulnerable','101':'vulnerable','110':'vulnerable','111':'vulnerable'}
        for pattern, result in expected.items():
            self.assertEqual(a.ensemble(pattern),result)

    def test_literals_and_token_boundaries(self):
        def h(code):return a.token_profile(code,'c',self.parsers)['token_sha256']
        self.assertEqual(h('int f(){return 1;}'),h('int /* note */ f ( ) { return 1 ; }'))
        self.assertNotEqual(h('void f(){puts("a b");}'),h('void f(){puts("ab");}'))
        self.assertNotEqual(h('void f(){a+ +b;}'),h('void f(){a++b;}'))
        self.assertNotEqual(h('void f(){puts("http://x");}'),h('void f(){puts("http://y");}'))

    def test_structural_candidates_preserve_risk_changes(self):
        def h(code):return a.token_profile(code,'c',self.parsers)['structural_sha256']
        self.assertEqual(h('int f(int a){return a+1;}'),h('int g(int b){return b+1;}'))
        self.assertNotEqual(h('int f(int a){return a+1;}'),h('int f(int a){return a-1;}'))
        self.assertNotEqual(h('int f(int a){return a+1;}'),h('int f(int a){return a+2;}'))

    def test_one_vote_weighting_does_not_choose_a_label(self):
        rows=[dict(label=1,score=.9,code_sha256='same'),dict(label=0,score=.9,code_sha256='same'),
              dict(label=1,score=.1,code_sha256='other')]
        m=a.weighted_metrics(rows,'code_sha256')
        self.assertAlmostEqual(m['tp'],.5); self.assertAlmostEqual(m['fp'],.5)
        self.assertAlmostEqual(m['fn'],1); self.assertAlmostEqual(m['f1'],.4)
        self.assertAlmostEqual(m['effective_weight'],2)

    def test_duplicate_expansion_invariance(self):
        base=[dict(label=1,score=.9,code_sha256='a'),dict(label=1,score=.1,code_sha256='b'),dict(label=0,score=.8,code_sha256='c')]
        expanded=base+[base[0]]*9
        self.assertAlmostEqual(a.weighted_metrics(base)['f1'],a.weighted_metrics(expanded,'code_sha256')['f1'])

    def test_strict_boundary_and_one_class(self):
        rows=[dict(label=1,score=.5),dict(label=1,score=.6)]
        m=a.weighted_metrics(rows)
        self.assertEqual(m['tp'],1); self.assertEqual(m['fn'],1)
        self.assertAlmostEqual(m['f1'],2/3)
        self.assertTrue(a.np.isnan(m['roc_auc']))

    def test_review_sample_short_stratum_and_repeatability(self):
        rows=[dict(sample_id=str(i),error='fn') for i in range(30)] + [dict(sample_id='fp'+str(i),error='fp') for i in range(3)]
        picked,strata=a.select_sample(rows,42)
        self.assertEqual((picked,strata),a.select_sample(rows,42))
        self.assertEqual(len(picked),23);self.assertEqual(len({r['sample_id'] for r in picked}),23)
        self.assertEqual(strata[0]['inclusion_probability'],2/3)
        self.assertEqual(strata[1]['inclusion_probability'],1)
        self.assertEqual(strata[2]['population'],0)

    def test_missing_metadata_strings(self):
        for v in [None,'None','nan','null','','N/A',[]]:self.assertFalse(a.present(v))
        for v in ['CVE-2020-1234',['CWE-120'],'qemu']:self.assertTrue(a.present(v))


if __name__=='__main__':unittest.main()
