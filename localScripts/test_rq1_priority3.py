import unittest
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from rq1_priority3_scores import ScoreCurve, grouping, standardized, reliability, bootstrap, METRICS


class ScoreDiagnosticTests(unittest.TestCase):
    def test_tied_noninterpolated_ap_and_auc(self):
        c=ScoreCurve([1,0,1,0],[.8,.8,.2,.1]); m=c.evaluate()
        self.assertAlmostEqual(m['average_precision'],7/12)
        self.assertAlmostEqual(m['roc_auc'],.625)
        for row in c.table():
            predicted=c.s>row['threshold']
            self.assertEqual(row['tp'],int(sum(predicted*c.y)))
            self.assertEqual(row['fp'],int(sum(predicted*(1-c.y))))

    def test_strict_threshold_and_endpoints(self):
        c=ScoreCurve([1,0,1,0],[.5,.5,1,0]); m=c.evaluate()
        self.assertEqual((m['tp'],m['fp'],m['fn'],m['tn']),(1,0,1,2))
        self.assertEqual(c.table()[0]['tp']+c.table()[0]['fp'],0)
        self.assertEqual(c.table()[-1]['tp']+c.table()[-1]['fp'],4)

    def test_zero_weight_ties_match_independent_library(self):
        y=np.array([1,0,1,0,1,0]); s=np.array([.9,.9,.6,.4,.4,.1]); w=np.array([0,0,2,3,1,0])
        m=ScoreCurve(y,s).evaluate(w)
        self.assertAlmostEqual(m['roc_auc'],roc_auc_score(y,s,sample_weight=w))
        self.assertAlmostEqual(m['average_precision'],average_precision_score(y,s,sample_weight=w))

    def test_recall_budget_does_not_split_tied_scores(self):
        m=ScoreCurve([1,0],[.8,.8]).evaluate()
        self.assertEqual(m['recall_fpr_10'],0)

    def test_connected_groups_keep_duplicates_and_families(self):
        rows=[dict(code_sha256='a',commit_url='u1',cve=None,group_id=None,project='p',label=0),
              dict(code_sha256='b',commit_url='u1',cve='CVE-2020-1234',group_id=None,project='p',label=1),
              dict(code_sha256='b',commit_url='u2',cve=None,group_id=None,project='q',label=0),
              dict(code_sha256='c',commit_url=None,cve='CVE-2020-1234',group_id=None,project='r',label=1),
              dict(code_sha256='d',commit_url='None',cve='None',group_id='family',project=None,label=0),
              dict(code_sha256='e',commit_url=None,cve=None,group_id='family',project=None,label=1)]
        ids,info=grouping(rows)
        self.assertEqual(info['groups'],2)
        self.assertEqual(len(set(ids[:4])),1)
        self.assertEqual(ids[4],ids[5])
        self.assertNotEqual(ids[0],ids[4])

    def test_prevalence_identity_and_all_negative(self):
        self.assertAlmostEqual(standardized(.8,.2,.5)['f1'],.8)
        self.assertAlmostEqual(standardized(1,1,.05)['f1'],.1/1.05)
        self.assertEqual(standardized(0,0,.05)['f1'],0)

    def test_reliability_edges_and_empty_bins(self):
        bins=reliability(np.array([0,1,1]),np.array([0.,.1,1.]),'uniform')
        self.assertEqual(sum(x['count'] for x in bins),3)
        self.assertEqual([bins[i]['count'] for i in [0,1,9]],[1,1,1])
        self.assertIsNone(bins[2]['observed_rate'])

    def test_paired_bootstrap_and_undefined_samples(self):
        c=ScoreCurve([0,1],[.1,.9])
        values=bootstrap({'first':c,'second':c},np.array([0,1]),50,42)
        np.testing.assert_equal(values['first'],values['second'])
        self.assertTrue(np.isnan(values['first'][:,METRICS.index('roc_auc')]).any())


if __name__=='__main__': unittest.main()
