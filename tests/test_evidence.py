import unittest

from src.ai import evidence_is_verbatim


class EvidenceTests(unittest.TestCase):
    def test_quote_is_verified_despite_whitespace(self):
        content = "希望有工具能保留语气，自动改写。"

        self.assertTrue(evidence_is_verbatim(content, "希望有工具能保留语气"))

    def test_paraphrased_evidence_is_not_verified(self):
        content = "希望有工具能自动改写。"

        self.assertFalse(evidence_is_verbatim(content, "作者需要智能内容工具"))

