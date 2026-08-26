import unittest

import pandas as pd

from src.data import normalize_posts


class NormalizePostsTests(unittest.TestCase):
    def test_adds_optional_columns(self):
        frame = pd.DataFrame(
            [
                {
                    "post_id": 1,
                    "platform": "test",
                    "content": "a need",
                    "source_url": "https://example.com",
                }
            ]
        )

        result = normalize_posts(frame)

        self.assertEqual(result.loc[0, "post_id"], "1")
        self.assertEqual(result.loc[0, "likes"], 0)

    def test_rejects_missing_required_columns(self):
        with self.assertRaisesRegex(ValueError, "source_url"):
            normalize_posts(
                pd.DataFrame([{"post_id": "1", "platform": "test", "content": "x"}])
            )

