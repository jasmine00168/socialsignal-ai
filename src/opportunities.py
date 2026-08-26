from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean


DEMAND_TYPE_LABELS = {
    "efficiency": "效率工具",
    "information": "信息获取",
    "creation": "内容创作",
    "commerce": "商业经营",
    "management": "管理协作",
    "communication": "沟通工具",
    "other": "其他需求",
}
WILLINGNESS_WEIGHTS = {"unknown": 0.25, "low": 0.4, "medium": 0.7, "high": 1.0}


def fallback_assignments(analyses: list[dict]) -> list[dict]:
    """Provide deterministic grouping when the clustering request is unavailable."""
    assignments = []
    for analysis in analyses:
        if not analysis.get("is_demand"):
            continue
        demand_type = analysis.get("demand_type", "other")
        assignments.append(
            {
                "post_id": analysis["post_id"],
                "cluster_id": f"type-{demand_type}",
                "cluster_label": DEMAND_TYPE_LABELS.get(demand_type, "其他需求"),
            }
        )
    return assignments


def _number(value: object) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(number, 0.0)


def build_opportunities(analyses: list[dict], assignments: list[dict]) -> list[dict]:
    """Aggregate clusters and calculate a transparent 100-point opportunity score."""
    demands = {item["post_id"]: item for item in analyses if item.get("is_demand")}
    grouped: dict[str, list[dict]] = defaultdict(list)
    labels: dict[str, str] = {}

    for assignment in assignments:
        post_id = assignment["post_id"]
        if post_id not in demands:
            continue
        cluster_id = assignment["cluster_id"]
        grouped[cluster_id].append(demands[post_id])
        labels.setdefault(cluster_id, assignment["cluster_label"])

    if not grouped:
        return []

    max_engagement = max(
        math.log1p(_number(item.get("likes")) + _number(item.get("comments")))
        for item in demands.values()
    )
    opportunities = []

    for cluster_id, items in grouped.items():
        frequency_score = len(items) / len(demands) * 25
        urgency_score = mean(_number(item.get("urgency")) for item in items) / 5 * 20
        willingness_score = mean(
            WILLINGNESS_WEIGHTS.get(str(item.get("willingness_to_pay")), 0.25)
            for item in items
        ) * 20
        confidence_score = mean(_number(item.get("confidence")) for item in items) * 15
        evidence_score = mean(bool(item.get("evidence_verified")) for item in items) * 10
        engagement_value = mean(
            math.log1p(_number(item.get("likes")) + _number(item.get("comments")))
            for item in items
        )
        engagement_score = engagement_value / max_engagement * 10 if max_engagement else 0
        total_score = sum(
            [
                frequency_score,
                urgency_score,
                willingness_score,
                confidence_score,
                evidence_score,
                engagement_score,
            ]
        )

        opportunities.append(
            {
                "cluster_id": cluster_id,
                "cluster_label": labels[cluster_id],
                "post_count": len(items),
                "opportunity_score": round(total_score, 1),
                "frequency_score": round(frequency_score, 1),
                "urgency_score": round(urgency_score, 1),
                "willingness_score": round(willingness_score, 1),
                "confidence_score": round(confidence_score, 1),
                "evidence_score": round(evidence_score, 1),
                "engagement_score": round(engagement_score, 1),
                "avg_urgency": round(mean(_number(item.get("urgency")) for item in items), 1),
                "avg_confidence": round(mean(_number(item.get("confidence")) for item in items), 2),
                "evidence_rate": round(mean(bool(item.get("evidence_verified")) for item in items), 2),
                "post_ids": [item["post_id"] for item in items],
                "items": items,
            }
        )

    return sorted(opportunities, key=lambda item: item["opportunity_score"], reverse=True)
