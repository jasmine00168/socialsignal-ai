from __future__ import annotations

import json
import re

from src.schemas import DemandAnalysis, DemandAnalysisResult, DemandClusters


SYSTEM_INSTRUCTIONS = """你是社交媒体需求研究员。判断原帖是否表达了可以由软件解决的真实需求。

规则：
1. 只依据原帖，不补充作者没有说过的事实。
2. evidence_quote 必须逐字复制原帖中的一小段；如果没有需求，使用最能说明帖子意图的原文。
3. 区分需求、泛泛抱怨、广告和纯经验分享。
4. 不要把点赞数等受欢迎程度当成需求证据。
5. 输出简洁中文；不确定的信息写“未知”或 null。
6. urgency 表示问题对作者的紧迫程度，不表示市场规模。
"""

CLUSTER_INSTRUCTIONS = """你是产品机会研究员。请把语义相近、目标用户和期望能力相似的软件需求归为一组。

规则：
1. 只能使用输入中已经提取的信息，不补充市场规模或用户事实。
2. 每个 post_id 必须且只能出现一次。
3. 不要为了减少分组而合并本质不同的需求；单条需求可以单独成组。
4. 同一组必须使用完全相同的 cluster_id 和 cluster_label。
5. cluster_label 使用简洁、中性的中文产品机会名称。
"""


class AnalysisError(RuntimeError):
    """Safe, user-facing error for an analysis request."""


def _normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", "", value).strip("“”‘’\"'")


def evidence_is_verbatim(content: str, quote: str) -> bool:
    normalized_quote = _normalize_for_match(quote)
    return bool(normalized_quote) and normalized_quote in _normalize_for_match(content)


def analyze_post(
    *,
    post_id: str,
    content: str,
    api_key: str,
    model: str = "gpt-5.4-mini",
) -> dict:
    from openai import OpenAI

    if not content.strip():
        raise AnalysisError("帖子内容为空。")

    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=2)
    schema = DemandAnalysis.model_json_schema()

    try:
        response = client.responses.create(
            model=model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=f"请分析下面这条帖子：\n\n{content}",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "demand_analysis",
                    "strict": True,
                    "schema": schema,
                }
            },
            reasoning={"effort": "low"},
            max_output_tokens=1200,
            store=False,
        )
        parsed = DemandAnalysis.model_validate(json.loads(response.output_text))
    except Exception as exc:  # SDK errors are translated into a safe UI message.
        message = getattr(exc, "message", None) or str(exc)
        raise AnalysisError(message) from exc

    result = DemandAnalysisResult(
        **parsed.model_dump(),
        post_id=post_id,
        evidence_verified=evidence_is_verbatim(content, parsed.evidence_quote),
        model=model,
    )
    return result.model_dump()


def cluster_demands(
    *,
    analyses: list[dict],
    api_key: str,
    model: str = "gpt-5.4-mini",
) -> list[dict]:
    """Cluster verified demand analyses and validate assignment completeness."""
    from openai import OpenAI

    demands = [analysis for analysis in analyses if analysis.get("is_demand")]
    if not demands:
        return []

    cluster_input = [
        {
            "post_id": item["post_id"],
            "demand_type": item["demand_type"],
            "opportunity_title": item["opportunity_title"],
            "target_user": item["target_user"],
            "pain_point": item["pain_point"],
            "desired_solution": item["desired_solution"],
        }
        for item in demands
    ]
    expected_ids = {item["post_id"] for item in cluster_input}
    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=2)

    try:
        response = client.responses.create(
            model=model,
            instructions=CLUSTER_INSTRUCTIONS,
            input="请聚类以下需求：\n\n" + json.dumps(cluster_input, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "demand_clusters",
                    "strict": True,
                    "schema": DemandClusters.model_json_schema(),
                }
            },
            reasoning={"effort": "low"},
            max_output_tokens=1600,
            store=False,
        )
        parsed = DemandClusters.model_validate(json.loads(response.output_text))
    except Exception as exc:
        message = getattr(exc, "message", None) or str(exc)
        raise AnalysisError(message) from exc

    assignments = [assignment.model_dump() for assignment in parsed.assignments]
    assigned_ids = [assignment["post_id"] for assignment in assignments]
    if len(assigned_ids) != len(set(assigned_ids)) or set(assigned_ids) != expected_ids:
        raise AnalysisError("聚类结果不完整，已切换为规则分组。")

    labels_by_cluster: dict[str, str] = {}
    for assignment in assignments:
        cluster_id = assignment["cluster_id"]
        cluster_label = assignment["cluster_label"]
        previous_label = labels_by_cluster.setdefault(cluster_id, cluster_label)
        if previous_label != cluster_label:
            raise AnalysisError("同一聚类返回了不同名称，已切换为规则分组。")
    return assignments
