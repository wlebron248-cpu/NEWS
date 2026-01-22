import os
import feedparser
import requests
from datetime import datetime, timedelta
from openai import OpenAI

# ========== 配置 ==========
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PUSH_PKEY = os.getenv("PUSH_PKEY")

client = OpenAI(api_key=OPENAI_KEY)

# ========== 新闻源 ==========
RSS_SOURCES = {
    "Reuters World": "https://www.reuters.com/world/rss",
    "Reuters Markets": "https://www.reuters.com/markets/rss",
    "Reuters Tech": "https://www.reuters.com/technology/rss",
    "Reuters Commodities": "https://www.reuters.com/markets/commodities/rss"
}

# ========== 抓新闻 ==========
def fetch_news():
    cutoff = datetime.utcnow() - timedelta(hours=24)
    news_list = []

    for name, url in RSS_SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6])
            if published > cutoff:
                news_list.append(f"[{name}] {entry.title}")

    return "\n".join(news_list[:25])  # 控制 token

# ========== AI 分析 ==========
def analyze(news_text):
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
Role:
你是一位拥有 20 年经验的全球宏观策略首席分析师与量化策略专家，
擅长“美股映射”与“产业链传导”，语言冷峻、专业、直击要害。

Task:
基于北京时间 {today} 过去 24 小时全球新闻，输出 A 股交易早报。

新闻原文：
{news_text}

请严格按格式输出：

🛡️ 模块一：全球宏观避雷针（Global Macro Scan）
- 核心事件：
- 资产定价逻辑：

📊 模块二：行业深度映射（Industry Linkage Table）
用表格形式输出：
领域 | 24H 核心事件 | 美股->A股逻辑 | A股标的 | 影响评分(1-10)

🚨 模块三：【突发预警】（仅当评分>=8）
- 事件名称
- 定性
- 博弈策略
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 稳定、便宜、分析够用
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content

# ========== 推送 ==========
def push(content):
    url = "https://api2.pushdeer.com/message/push"
    params = {"pushkey": PUSH_PKEY, "text": content}
    requests.get(url, params=params, timeout=10)

# ========== 主入口 ==========
if __name__ == "__main__":
    news = fetch_news()
    result = analyze(news)
    push(result)
