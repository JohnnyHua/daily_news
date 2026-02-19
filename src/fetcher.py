#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻获取模块
从 NewsAPI 获取 AI、中国和法国的新闻
"""

import os
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional


class NewsFetcher:
    """新闻获取器"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化新闻获取器

        Args:
            api_key: NewsAPI 密钥，如不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.lookback_hours = int(os.getenv("NEWS_LOOKBACK_HOURS", "24"))

    @staticmethod
    def _parse_published_at(value: str) -> Optional[datetime]:
        """解析 NewsAPI 的发布时间。"""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    def _is_within_lookback(self, published_at: str) -> bool:
        """仅保留最近 lookback_hours 内的新闻。"""
        published_dt = self._parse_published_at(published_at)
        if not published_dt:
            return False
        window_start = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        return published_dt >= window_start

    def get_top_headlines(
        self,
        keyword: str,
        language: str = "en",
        page_size: int = 5
    ) -> List[Dict]:
        """获取关键词相关的热门新闻

        Args:
            keyword: 搜索关键词
            language: 语言代码
            page_size: 返回数量

        Returns:
            新闻列表
        """
        if not self.api_key:
            # 如果没有 API 密钥，返回模拟数据用于测试
            return self._get_mock_news(keyword)

        endpoint = f"{self.base_url}/everything"
        now_utc = datetime.now(timezone.utc)
        from_utc = now_utc - timedelta(hours=self.lookback_hours)
        params = {
            "q": keyword,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "from": from_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "to": now_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "apiKey": self.api_key
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "ok":
                articles = data.get("articles", [])
                filtered_articles = [
                    {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "published_at": article.get("publishedAt", "")
                    }
                    for article in articles
                    if article.get("title") and article.get("title") != "[Removed]"
                ]
                return [a for a in filtered_articles if self._is_within_lookback(a.get("published_at", ""))]
            else:
                print(f"API 返回错误: {data.get('message', '未知错误')}")
                return self._get_mock_news(keyword)

        except requests.RequestException as e:
            print(f"请求错误: {e}")
            return self._get_mock_news(keyword)

    def _get_mock_news(self, keyword: str) -> List[Dict]:
        """获取模拟新闻数据（用于测试或无 API 密钥时）

        Args:
            keyword: 关键词

        Returns:
            模拟新闻列表
        """
        mock_data = {
            "artificial intelligence": [
                {
                    "title": "OpenAI 发布 GPT-5 预览版，带来突破性进展",
                    "description": "新一代大语言模型在推理能力和多模态理解方面取得重大突破",
                    "url": "https://openai.com",
                    "source": "OpenAI",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "Google DeepMind 发布 AlphaFold 3",
                    "description": "蛋白质结构预测精度进一步提升，为药物研发提供更强工具",
                    "url": "https://deepmind.com",
                    "source": "DeepMind",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "Meta 开源 Llama 3 性能超越 GPT-4",
                    "description": "Meta 继续推进开源 AI 发展，新模型在多项基准测试中领先",
                    "url": "https://meta.com",
                    "source": "Meta AI",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "china": [
                {
                    "title": "中国数字经济规模突破 50 万亿元",
                    "description": "2024 年中国数字经济继续保持快速增长，成为经济增长重要引擎",
                    "url": "https://xinhuanet.com",
                    "source": "新华网",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "中国在 AI 领域发表论文数量全球第一",
                    "description": "中国科研机构在人工智能领域的研究产出持续增长",
                    "url": "https://people.com.cn",
                    "source": "人民网",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "中国新能源汽车销量创新高",
                    "description": "比亚迪、蔚来等品牌销量持续攀升，推动汽车产业转型",
                    "url": "https://automotive.com.cn",
                    "source": "汽车之家",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "france": [
                {
                    "title": "巴黎奥运会筹备工作进入最后阶段",
                    "description": "2024 年巴黎奥运会各项准备工作基本完成，预计将吸引全球关注",
                    "url": "https://lemonde.fr",
                    "source": "Le Monde",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "法国科技 startup 融资规模创新高",
                    "description": "法国科技生态系统持续繁荣，AI 和绿色科技领域投资活跃",
                    "url": "https://lefigaro.fr",
                    "source": "Le Figaro",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "法国推动欧盟 AI 监管框架",
                    "description": "法国在欧洲 AI 监管讨论中发挥积极作用，寻求创新与监管平衡",
                    "url": "https://euronews.com",
                    "source": "Euronews",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "chinese in france": [
                {
                    "title": "巴黎华人社区举办春节文化活动",
                    "description": "法国多地华社组织新春庆典，推动中法民间文化交流",
                    "url": "https://www.chinanews.com.cn/",
                    "source": "中国新闻网",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "法国更新外国人居留政策说明",
                    "description": "涉及学生、工作及家庭团聚签证流程，建议在法华人关注官方更新",
                    "url": "https://www.service-public.fr/",
                    "source": "Service-Public.fr",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "中法航线运力恢复，往返出行选择增加",
                    "description": "中法主要航线班次增加，利好在法华人探亲与商务往来",
                    "url": "https://www.airfrance.fr/",
                    "source": "Air France",
                    "published_at": datetime.now().isoformat()
                }
            ]
        }

        # 尝试匹配关键词
        keyword_lower = keyword.lower()
        for key, news in mock_data.items():
            if key in keyword_lower:
                return news

        # 默认返回 AI 新闻
        return mock_data["artificial intelligence"]

    def fetch_all_news(self) -> Dict[str, List[Dict]]:
        """获取所有类别的新闻

        Returns:
            包含所有类别新闻的字典
        """
        # 定义搜索关键词
        topics = {
            "ai": "artificial intelligence OR AI OR machine learning OR deep learning",
            "china": "China OR Chinese",
            "france": "France OR French OR Paris",
            "fr_china": "Chinese in France OR France China relations OR Chinese community in France OR 巴黎 华侨 OR 法国 华人"
        }

        news_data = {}

        for category, keyword in topics.items():
            print(f"正在获取 {category} 类别新闻...")
            news_data[category] = self.get_top_headlines(keyword, page_size=5)
            print(f"获取到 {len(news_data[category])} 条 {category} 新闻")

        return news_data


if __name__ == "__main__":
    # 测试代码
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_news()

    for category, articles in news.items():
        print(f"\n{category} 新闻:")
        for article in articles:
            print(f"  - {article['title']}")
