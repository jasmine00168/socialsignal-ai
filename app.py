from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.ai import AnalysisError, analyze_post, cluster_demands
from src.data import REQUIRED_COLUMNS, load_sample_posts, normalize_posts
from src.opportunities import build_opportunities, fallback_assignments


ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env.local")

st.set_page_config(
    page_title="SocialSignal AI",
    page_icon="📡",
    layout="wide",
)


def get_api_key() -> str | None:
    """Read a key locally or from Streamlit Community Cloud secrets."""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except (FileNotFoundError, KeyError):
        return None


def render_analysis(result: dict) -> None:
    confidence = f"{result['confidence']:.0%}"
    cols = st.columns(4)
    cols[0].metric("识别结果", "存在需求" if result["is_demand"] else "非需求")
    cols[1].metric("置信度", confidence)
    cols[2].metric("紧迫度", f"{result['urgency']}/5")
    cols[3].metric("证据校验", "通过" if result["evidence_verified"] else "待复核")

    st.subheader(result["opportunity_title"])
    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown("**核心痛点**")
        st.write(result["pain_point"])
        st.markdown("**期望解决方案**")
        st.write(result["desired_solution"])
        st.markdown("**目标用户 / 场景**")
        st.write(f"{result['target_user']} · {result['usage_context']}")
    with right:
        st.markdown("**原文证据**")
        st.info(result["evidence_quote"] or "未找到可验证的原文证据")
        st.markdown("**AI 判断摘要**")
        st.write(result["reasoning_summary"])

    with st.expander("查看结构化 JSON（AI 产品的数据契约）"):
        st.json(result)


def render_opportunity_radar(batch_result: dict) -> None:
    analyses = batch_result["analyses"]
    opportunities = build_opportunities(analyses, batch_result["assignments"])
    batch_result["opportunities"] = opportunities
    demand_count = sum(bool(item["is_demand"]) for item in analyses)
    evidence_count = sum(bool(item["evidence_verified"]) for item in analyses)

    metrics = st.columns(4)
    metrics[0].metric("已分析帖子", len(analyses))
    metrics[1].metric("识别出需求", demand_count)
    metrics[2].metric("机会聚类", len(opportunities))
    metrics[3].metric("证据通过率", f"{evidence_count / len(analyses):.0%}" if analyses else "0%")

    if not opportunities:
        st.info("本批帖子中没有识别出明确的软件需求，可更换数据后重试。")
        return

    summary = pd.DataFrame(
        [
            {
                "排名": rank,
                "机会主题": item["cluster_label"],
                "机会分": item["opportunity_score"],
                "需求数": item["post_count"],
                "平均紧迫度": item["avg_urgency"],
                "平均置信度": f"{item['avg_confidence']:.0%}",
                "证据通过率": f"{item['evidence_rate']:.0%}",
            }
            for rank, item in enumerate(opportunities, start=1)
        ]
    )
    st.dataframe(summary, width="stretch", hide_index=True)
    st.caption(
        "机会分（100分）= 本批需求占比25 + 紧迫度20 + 付费意愿20 + AI置信度15 + 证据完整度10 + 互动量10。"
        "互动量仅作辅助信号，不作为需求证据。"
    )

    st.subheader("机会详情与原文证据")
    for rank, opportunity in enumerate(opportunities, start=1):
        title = f"#{rank} {opportunity['cluster_label']} · {opportunity['opportunity_score']} 分"
        with st.expander(title, expanded=rank == 1):
            breakdown = st.columns(6)
            breakdown[0].metric("频次", f"{opportunity['frequency_score']}/25")
            breakdown[1].metric("紧迫", f"{opportunity['urgency_score']}/20")
            breakdown[2].metric("付费", f"{opportunity['willingness_score']}/20")
            breakdown[3].metric("置信", f"{opportunity['confidence_score']}/15")
            breakdown[4].metric("证据", f"{opportunity['evidence_score']}/10")
            breakdown[5].metric("互动", f"{opportunity['engagement_score']}/10")

            for item in opportunity["items"]:
                st.markdown(f"**{item['post_id']} · {item['platform']} · {item['opportunity_title']}**")
                st.info(item["evidence_quote"] or "未找到可验证的原文证据")
                st.write(item["reasoning_summary"])
                st.caption(f"原帖：{item['source_url']}")

    with st.expander("查看完整批量分析 JSON"):
        st.json(batch_result)


def safe_int(value: object) -> int:
    try:
        return int(float(value)) if not pd.isna(value) else 0
    except (TypeError, ValueError):
        return 0


st.title("📡 SocialSignal AI")
st.caption("从社交媒体原帖中识别软件需求，保留证据，并形成可验证的机会洞察。")

with st.sidebar:
    st.header("分析设置")
    model = st.text_input("模型", value=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"))
    api_key = get_api_key()
    if api_key:
        st.success("OpenAI API 已连接")
    else:
        st.warning("尚未配置 OpenAI API")
    st.divider()
    st.markdown("**当前里程碑**")
    st.write("V0.2 · 批量需求聚类与机会评分")
    st.caption("已完成：API 接入、结构化输出、证据校验")

source_mode = st.radio(
    "选择数据来源",
    ["使用演示数据", "上传 CSV"],
    horizontal=True,
)

if source_mode == "上传 CSV":
    upload = st.file_uploader("上传 UTF-8 CSV", type=["csv"])
    if upload is None:
        st.info("CSV 至少需要 post_id、platform、content、source_url 四列。")
        st.stop()
    try:
        posts = normalize_posts(pd.read_csv(upload))
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
else:
    posts = load_sample_posts(ROOT / "data" / "sample_posts.csv")

st.subheader("1. 查看待分析数据")
st.dataframe(
    posts[["post_id", "platform", "content", "likes", "comments"]],
    width="stretch",
    hide_index=True,
)

single_tab, batch_tab = st.tabs(["单条需求验证", "批量机会雷达"])

with single_tab:
    st.subheader("2. 选择一条帖子并验证")
    selected_id = st.selectbox("帖子编号", posts["post_id"].tolist())
    selected = posts.loc[posts["post_id"] == selected_id].iloc[0]
    st.markdown(f"> {selected['content']}")
    st.caption(f"来源：{selected['platform']} · {selected['source_url']}")

    if st.button("开始单条分析", type="primary", width="stretch"):
        if not api_key:
            st.error("请先配置 OPENAI_API_KEY。")
        else:
            with st.spinner("正在提取需求、场景和证据……"):
                try:
                    analysis = analyze_post(
                        post_id=str(selected["post_id"]),
                        content=str(selected["content"]),
                        api_key=api_key,
                        model=model.strip() or "gpt-5.4-mini",
                    )
                except AnalysisError as exc:
                    st.error(f"分析失败：{exc}")
                else:
                    st.session_state["latest_analysis"] = analysis

    if analysis := st.session_state.get("latest_analysis"):
        st.subheader("3. 查看结构化结果与证据")
        render_analysis(analysis)

with batch_tab:
    st.subheader("2. 批量识别、聚类并排序")
    max_batch = min(len(posts), 10)
    min_batch = 1 if max_batch == 1 else 2
    batch_size = st.slider("本次分析帖子数", min_value=min_batch, max_value=max_batch, value=max_batch)
    st.caption(f"本次最多调用 {batch_size} 次需求识别和 1 次聚类；小批量运行便于控制 API 成本。")

    if st.button("生成机会雷达", type="primary", width="stretch"):
        if not api_key:
            st.error("请先配置 OPENAI_API_KEY。")
        else:
            progress = st.progress(0, text="正在逐条识别需求……")
            analyses = []
            failures = []
            batch_rows = posts.head(batch_size)

            for position, (_, row) in enumerate(batch_rows.iterrows(), start=1):
                try:
                    analysis = analyze_post(
                        post_id=str(row["post_id"]),
                        content=str(row["content"]),
                        api_key=api_key,
                        model=model.strip() or "gpt-5.4-mini",
                    )
                except AnalysisError as exc:
                    failures.append(f"{row['post_id']}: {exc}")
                else:
                    analysis.update(
                        {
                            "platform": str(row["platform"]),
                            "content": str(row["content"]),
                            "source_url": str(row["source_url"]),
                            "likes": safe_int(row["likes"]),
                            "comments": safe_int(row["comments"]),
                            "published_at": str(row["published_at"]),
                        }
                    )
                    analyses.append(analysis)
                progress.progress(position / (batch_size + 1), text=f"已完成 {position}/{batch_size} 条")

            clustering_mode = "AI 语义聚类"
            if analyses:
                progress.progress(batch_size / (batch_size + 1), text="正在聚类相似需求……")
                try:
                    assignments = cluster_demands(
                        analyses=analyses,
                        api_key=api_key,
                        model=model.strip() or "gpt-5.4-mini",
                    )
                except AnalysisError as exc:
                    assignments = fallback_assignments(analyses)
                    clustering_mode = "规则降级分组"
                    st.warning(f"语义聚类暂时不可用，已自动切换规则分组：{exc}")
            else:
                assignments = []

            batch_result = {
                "analyses": analyses,
                "assignments": assignments,
                "opportunities": build_opportunities(analyses, assignments),
                "clustering_mode": clustering_mode,
                "failures": failures,
                "model": model.strip() or "gpt-5.4-mini",
            }
            st.session_state["batch_result"] = batch_result
            progress.progress(1.0, text="机会雷达已生成")
            if failures:
                st.warning(f"有 {len(failures)} 条分析失败，其余结果仍已保留。")

    if batch_result := st.session_state.get("batch_result"):
        st.caption(f"聚类方式：{batch_result['clustering_mode']} · 模型：{batch_result['model']}")
        render_opportunity_radar(batch_result)

with st.expander("CSV 字段说明"):
    st.code(", ".join(REQUIRED_COLUMNS))
