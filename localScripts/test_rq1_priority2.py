"""Checks for input-audit semantics, byte boundaries, and intervention controls."""
import unittest
import rq1_priority2_audit as audit
from rq1_priority2_ablations import pack


class InputAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsers=audit.parsers()
        cls.clean=staticmethod(audit.cwe.load_preprocessing()['clean_for_vulberta'])

    def preserved(self,code,language='cpp'):
        tree=self.parsers[language].parse(code.encode())
        safe=audit.preserve_lexical_code(code,tree)
        self.assertEqual(audit.cwe.lexical_tokens(tree.root_node),
                         audit.cwe.lexical_tokens(self.parsers[language].parse(safe.encode()).root_node))
        return safe

    def test_url_and_cpp_raw_strings_are_preserved(self):
        code='const char *f() { /* note */ return R"tag(https://host/*path*/)tag"; }'
        safe=self.preserved(code)
        self.assertIn('https://host/*path*/',safe)
        self.assertNotEqual(audit.cwe.lexical_tokens(self.parsers['cpp'].parse(code.encode()).root_node),
                            audit.cwe.lexical_tokens(self.parsers['cpp'].parse(self.clean(code).encode()).root_node))

    def test_comment_gaps_and_newline_identifier_boundaries(self):
        code='int f() { int/**/x=0; int\ny=1; return x+y; }'
        safe=self.preserved(code,'c')
        self.assertIn('int\ny',safe)
        self.assertNotIn('intx',safe)
        self.assertIn('intx',self.clean(code))

    def test_preprocessor_line_boundaries_remain(self):
        code='#define N 2\nint f() { return N; } // end\n'
        safe=self.preserved(code,'c')
        self.assertEqual(safe.count('\n'),code.count('\n'))
        self.assertIn('#define N 2\n',safe)

    def test_absent_flaw_annotations_are_unknown(self):
        self.assertEqual(audit.flaw_visibility('int f() { return 1; }',{},999)['status'],'unavailable')

    def test_flaw_annotation_matching_and_utf8_byte_cutoff(self):
        code='// é\nint f() {\n return 1;\n}\n'
        meta={'flaw_line_index':'2','flaw_line':' return 1;'}
        cut=len('// é\nint f() {\n'.encode())
        self.assertEqual(audit.flaw_visibility(code,meta,cut)['partly_or_fully_removed_lines'],1)
        self.assertEqual(audit.flaw_visibility(code,meta,len(code.encode()))['fully_visible_lines'],1)
        meta['flaw_line']='wrong text'
        self.assertEqual(audit.flaw_visibility(code,meta,cut)['status'],'annotation_text_mismatch')

    def test_tail_window_limits_special_tokens_and_control(self):
        self.assertEqual(pack([0,5,6,7,8,9,2],5),[0,5,6,7,2])
        self.assertEqual(pack([0,5,6,7,8,9,2],5,tail=True),[0,7,8,9,2])
        self.assertEqual(pack([0,5,2],5),pack([0,5,2],5,tail=True))
        self.assertEqual(pack([0,5,2],5),[0,5,2,1,1])


if __name__=='__main__':
    unittest.main()
