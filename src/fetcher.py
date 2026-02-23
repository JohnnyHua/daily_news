#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻获取模块
支持多个免费 RSS 源：tldr.tech, TechCrunch, Reddit 热门
"""

import os
import re
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from urllib.parse import urljoin


class NewsFetcher:
    """新闻获取器 - RSS 方案（免费）"""

    # RSS 源配置
    RSS_SOURCES = {
        "ai": {
            "name": "AI 前沿",
            "feeds": [
                # tldr.ai - 每日 AI 新闻
                "https://tldr.tech/ai/feed",
                # Hacker News AI
                "https://hnrss.org/newest?q=AI&q=machine%20learning",
            ],
        },
        "tech": {
            "name": "科技要闻",
            "feeds": [
                # TechCrunch
                "https://techcrunch.com/feed/",
                # The Verge Tech
                "https://www.theverge.com/rss/index.xml",
            ],
        },
        "france": {
            "name": "法国动态",
            "feeds": [
                # 法国新闻 RSS
                "https://www.lemonde.fr/rss/une.xml",
                # Euronews
                "https://www.euronews.com/rss",
            ],
        },
        "china": {
            "name": "中国要闻",
            "feeds": [
                # 联合早报
                "https://www.zaobao.com.sg/rss/znews/china.xml",
            ],
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """初始化新闻获取器"""
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.lookback_hours = int(os.getenv("NEWS_LOOKBACK_HOURS", "24"))
        self.allow_mock_news = os.getenv("ALLOW_MOCK_NEWS", "0") == "1"

    def _parse_date(self, entry) -> Optional[datetime]:
        """解析 RSS 条目的日期"""
        # 尝试多个日期字段
        for date_field in ("published_parsed", "updated_parsed", "dc_date"):
            if hasattr(entry, date_field):
                try:
                    from time import mktime

                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    return dt
                except:
                    continue

        # 尝试解析原始日期字符串
        for field in ("published", "updated", "dc_date"):
            if hasattr(entry, field):
                try:
                    value = getattr(entry, field)
                    if value:
                        # 尝试 ISO 格式
                        if "T" in value:
                            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                            return dt.astimezone(timezone.utc)
                except:
                    continue
        return None

    def _is_recent(self, entry) -> bool:
        """检查条目是否在时间范围内"""
        published_dt = self._parse_date(entry)
        if not published_dt:
            return True  # 无法解析日期时保留
        window_start = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        return published_dt >= window_start

    def _clean_html(self, html: str) -> str:
        """清理 HTML 标签"""
        if not html:
            return ""
        # 移除 HTML 标签
        clean = re.sub(r"<[^>]+>", "", html)
        # 移除多余空白
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _fetch_feed(self, feed_url: str, limit: int = 10) -> List[Dict]:
        """获取单个 RSS 源"""
        try:
            headers = {"User-Agent": "DailyNewsBot/1.0"}
            response = requests.get(feed_url, headers=headers, timeout=8)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            articles = []
            for entry in feed.entries[:limit]:
                if not self._is_recent(entry):
                    continue

                # 提取标题和链接
                title = getattr(entry, "title", "无标题")
                link = getattr(entry, "link", "")

                # 尝试获取摘要
                description = ""
                for desc_field in ("summary", "description", "content"):
                    if hasattr(entry, desc_field):
                        raw_desc = getattr(entry, desc_field)
                        if raw_desc:
                            description = self._clean_html(raw_desc)
                            break

                # 获取发布时间
                published = ""
                if hasattr(entry, "published"):
                    published = entry.published
                elif hasattr(entry, "updated"):
                    published = entry.updated

                # 来源
                source = ""
                if hasattr(feed, "feed") and hasattr(feed.feed, "title"):
                    source = feed.feed.title

                articles.append(
                    {
                        "title": title,
                        "description": description[:200] if description else "",
                        "url": link,
                        "source": source or feed_url,
                        "published_at": published,
                    }
                )

            return articles

        except Exception as e:
            print(f"  ⚠️ 获取失败 {feed_url}: {e}")
            return []

    def get_top_headlines(
        self, keyword: str, language: str = "en", page_size: int = 5
    ) -> List[Dict]:
        """获取关键词相关的热门新闻（兼容原接口）"""
        # 映射关键词到分类
        category_map = {
            "ai": "ai",
            "artificial intelligence": "ai",
            "machine learning": "ai",
            "tech": "tech",
            "technology": "tech",
            "france": "france",
            "french": "france",
            "paris": "france",
            "china": "china",
            "chinese": "china",
        }

        keyword_lower = keyword.lower()
        category = category_map.get(keyword_lower, "tech")

        return self.fetch_category_news(category, limit)

    def fetch_category_news(self, category: str, limit: int = 10) -> List[Dict]:
        """获取指定分类的新闻"""
        if category not in self.RSS_SOURCES:
            print(f"  ⚠️ 未知分类: {category}")
            return []

        config = self.RSS_SOURCES[category]
        all_articles = []

        print(f"  正在获取 {config['name']} 新闻...")

        for feed_url in config["feeds"]:
            articles = self._fetch_feed(feed_url, limit)
            all_articles.extend(articles)
            if len(all_articles) >= limit:
                break

        # 去重并限制数量
        seen = set()
        unique_articles = []
        for article in all_articles:
            title = article["title"].lower()
            if title not in seen and title != "无标题":
                seen.add(title)
                unique_articles.append(article)

        print(f"  获取到 {len(unique_articles)} 条新闻")
        return unique_articles[:limit]

    def fetch_all_news(self) -> Dict[str, List[Dict]]:
        """获取所有类别的新闻"""
        news_data = {}

        for category in self.RSS_SOURCES.keys():
            news_data[category] = self.fetch_category_news(category, limit=5)

        return news_data


if __name__ == "__main__":
    # 测试代码
    print("=== RSS 新闻获取测试 ===\n")

    fetcher = NewsFetcher()
    news = fetcher.fetch_all_news()

    for category, articles in news.items():
        print(f"\n【{category.upper()}】")
        for i, article in enumerate(articles[:3], 1):
            print(f"  {i}. {article['title']}")
            print(f"     {article['url']}")
