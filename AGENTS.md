# Project Rules

Project: SocialSignal AI

Goal:
Build an AI product that extracts software-related user demands from social media posts, clusters similar demands, preserves source evidence, and generates opportunity reports.

Tech stack:
- Python
- Streamlit
- pandas
- LLM API

Development rules:
1. Keep the architecture simple.
2. Make small, incremental changes.
3. Do not add new frameworks unless necessary.
4. Do not modify unrelated files.
5. Never hard-code API keys.
6. LLM output should be structured whenever possible.
7. AI-generated insights must preserve source evidence.
8. Explain major changes before implementing them.
9. Test each feature before moving to the next milestone.

Current MVP:
Upload data
→ detect demand
→ extract structured information
→ cluster similar demands
→ inspect source evidence
→ generate opportunity report