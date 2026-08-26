"""Run one paid API request to validate credentials, model access, and schema output."""

from pathlib import Path

from dotenv import load_dotenv

from src.ai import analyze_post


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local")

if __name__ == "__main__":
    import os

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not configured.")

    result = analyze_post(
        post_id="smoke-001",
        content="每天手工整理十几个客户群，经常漏掉重点，希望有工具自动归类。",
        api_key=key,
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
    )
    print(
        {
            "is_demand": result["is_demand"],
            "opportunity_title": result["opportunity_title"],
            "evidence_verified": result["evidence_verified"],
            "model": result["model"],
        }
    )

