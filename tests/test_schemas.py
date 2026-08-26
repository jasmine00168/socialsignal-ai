import unittest

from pydantic import ValidationError

from src.schemas import DemandClusters


class ClusterSchemaTests(unittest.TestCase):
    def test_cluster_contract_rejects_extra_fields(self):
        payload = {
            "assignments": [
                {
                    "post_id": "demo-001",
                    "cluster_id": "cluster-01",
                    "cluster_label": "客户需求归类",
                    "invented_market_size": "100亿元",
                }
            ]
        }

        with self.assertRaises(ValidationError):
            DemandClusters.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
