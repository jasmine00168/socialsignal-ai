import unittest

from src.opportunities import build_opportunities, fallback_assignments


class OpportunityScoringTests(unittest.TestCase):
    def test_fallback_groups_only_demands_by_type(self):
        analyses = [
            {"post_id": "a", "is_demand": True, "demand_type": "efficiency"},
            {"post_id": "b", "is_demand": True, "demand_type": "efficiency"},
            {"post_id": "c", "is_demand": False, "demand_type": "none"},
        ]

        assignments = fallback_assignments(analyses)

        self.assertEqual([item["post_id"] for item in assignments], ["a", "b"])
        self.assertEqual({item["cluster_id"] for item in assignments}, {"type-efficiency"})

    def test_score_is_transparent_and_preserves_items(self):
        analyses = [
            {
                "post_id": "a",
                "is_demand": True,
                "urgency": 4,
                "willingness_to_pay": "medium",
                "confidence": 0.8,
                "evidence_verified": True,
                "likes": 0,
                "comments": 0,
            },
            {
                "post_id": "b",
                "is_demand": True,
                "urgency": 4,
                "willingness_to_pay": "medium",
                "confidence": 0.8,
                "evidence_verified": False,
                "likes": 0,
                "comments": 0,
            },
        ]
        assignments = [
            {"post_id": "a", "cluster_id": "cluster-01", "cluster_label": "自动归类"},
            {"post_id": "b", "cluster_id": "cluster-01", "cluster_label": "自动归类"},
        ]

        opportunities = build_opportunities(analyses, assignments)

        self.assertEqual(len(opportunities), 1)
        result = opportunities[0]
        self.assertEqual(result["opportunity_score"], 72.0)
        self.assertEqual(result["frequency_score"], 25.0)
        self.assertEqual(result["evidence_score"], 5.0)
        self.assertEqual(result["post_ids"], ["a", "b"])

    def test_higher_scoring_cluster_ranks_first(self):
        analyses = [
            {
                "post_id": "high",
                "is_demand": True,
                "urgency": 5,
                "willingness_to_pay": "high",
                "confidence": 1,
                "evidence_verified": True,
                "likes": 100,
                "comments": 20,
            },
            {
                "post_id": "low",
                "is_demand": True,
                "urgency": 1,
                "willingness_to_pay": "unknown",
                "confidence": 0.2,
                "evidence_verified": False,
                "likes": 0,
                "comments": 0,
            },
        ]
        assignments = [
            {"post_id": "high", "cluster_id": "high-cluster", "cluster_label": "高机会"},
            {"post_id": "low", "cluster_id": "low-cluster", "cluster_label": "低机会"},
        ]

        opportunities = build_opportunities(analyses, assignments)

        self.assertEqual(opportunities[0]["cluster_id"], "high-cluster")
        self.assertGreater(opportunities[0]["opportunity_score"], opportunities[1]["opportunity_score"])

    def test_frequency_score_uses_share_of_all_demands(self):
        analyses = [
            {"post_id": "a", "is_demand": True, "urgency": 1, "confidence": 0},
            {"post_id": "b", "is_demand": True, "urgency": 1, "confidence": 0},
            {"post_id": "c", "is_demand": True, "urgency": 1, "confidence": 0},
        ]
        assignments = [
            {"post_id": "a", "cluster_id": "large", "cluster_label": "两条需求"},
            {"post_id": "b", "cluster_id": "large", "cluster_label": "两条需求"},
            {"post_id": "c", "cluster_id": "small", "cluster_label": "一条需求"},
        ]

        opportunities = build_opportunities(analyses, assignments)
        by_id = {item["cluster_id"]: item for item in opportunities}

        self.assertEqual(by_id["large"]["frequency_score"], 16.7)
        self.assertEqual(by_id["small"]["frequency_score"], 8.3)


if __name__ == "__main__":
    unittest.main()
