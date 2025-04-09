# LLM file
from mistralai import Mistral
from newsapi import NewsApiClient

# open-free key
llm_api_key = "nzIyBJcWNddZdaaDObzYqq3nuHFValDR"

maxtokens = 32768

model = "mistral-small"

general_role = {
    "role": "system",
    "content": """
    You are a **Lead Sports Scientist** at Chelsea Football Club, specializing in soccer performance optimization. Your expertise includes:
    - Interpreting GPS, physical capability, and recovery metrics
    - Identifying injury risks and workload mismatches
    - Translating complex metrics into actionable coaching strategies

    **Output Guidelines:**
    1. **Structure**: Use clear sections (Observations, Risks, Recommendations)
    2. **Tone**: Concise, authoritative, and practical
    3. **Focus**: Prioritize actionable insights over raw data description or documentation.
    """,
}

client = Mistral(api_key=llm_api_key)

# https://newsapi.org/account
# news api key
news_api_key='e9a9d2fd902b41aca0a9099b8869de4b'

newsapi = NewsApiClient(api_key=news_api_key)
