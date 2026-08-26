from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["post_id", "platform", "content", "source_url"]
OPTIONAL_DEFAULTS = {"likes": 0, "comments": 0, "published_at": ""}


def normalize_posts(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV 缺少必要字段：{', '.join(missing)}")

    posts = frame.copy()
    for column, default in OPTIONAL_DEFAULTS.items():
        if column not in posts.columns:
            posts[column] = default
    posts = posts[REQUIRED_COLUMNS + list(OPTIONAL_DEFAULTS)]
    posts["post_id"] = posts["post_id"].astype(str)
    posts["content"] = posts["content"].fillna("").astype(str).str.strip()
    posts = posts[posts["content"].ne("")].drop_duplicates(subset=["post_id"])
    if posts.empty:
        raise ValueError("CSV 中没有可分析的帖子内容。")
    return posts.reset_index(drop=True)


def load_sample_posts(path: Path) -> pd.DataFrame:
    return normalize_posts(pd.read_csv(path))

