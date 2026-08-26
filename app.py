from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.ai import AnalysisError, analyze_post
from src.data import REQUIRED_COLUMNS, load_sample_posts, normalize_posts


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
    st.write("V0.1 · 单条需求识别与证据校验")
    st.caption("下一阶段：批量分析、聚类和机会评分")

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

st.subheader("1. 选择一条社交媒体帖子")
st.dataframe(
    posts[["post_id", "platform", "content", "likes", "comments"]],
    use_container_width=True,
    hide_index=True,
)

selected_id = st.selectbox("帖子编号", posts["post_id"].tolist())
selected = posts.loc[posts["post_id"] == selected_id].iloc[0]
st.markdown(f"> {selected['content']}")
st.caption(f"来源：{selected['platform']} · {selected['source_url']}")

st.subheader("2. 运行 AI 需求识别")
if st.button("开始分析", type="primary", use_container_width=True):
    if not api_key:
        st.error("请先配置 OPENAI_API_KEY。")
    else:
        with st.spinner("正在提取需求、场景和证据……"):
            try:
                analysis = analyze_post(
                    post_id=str(selected["post_id"]),
                    content=str(selected["content"]),
                    api_key=api_key,
                    model=model,
                )
            except AnalysisError as exc:
                st.error(f"分析失败：{exc}")
            else:
                st.session_state["latest_analysis"] = analysis

if analysis := st.session_state.get("latest_analysis"):
    st.subheader("3. 查看结构化结果与证据")
    render_analysis(analysis)

with st.expander("CSV 字段说明"):
    st.code(", ".join(REQUIRED_COLUMNS))
