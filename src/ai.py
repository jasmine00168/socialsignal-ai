from __future__ import annotations

import json
import re

from src.schemas import DemandAnalysis, DemandAnalysisResult


SYSTEM_INSTRUCTIONS = """你是社交媒体需求研究员。判断原帖是否表达了可以由软件解决的真实需求。

规则：
1. 只依据原帖，不补充作者没有说过的事实。
2. evidence_quote 必须逐字复制原帖中的一小段；如果没有需求，使用最能说明帖子意图的原文。
3. 区分需求、泛泛抱怨、广告和纯经验分享。
4. 不要把点赞数等受欢迎程度当成需求证据。
5. 输出简洁中文；不确定的信息写“未知”或 null。
6. urgency 表示问题对作者的紧迫程度，不表示市场规模。
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
