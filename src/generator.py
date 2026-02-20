#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成模块
将新闻数据格式化为精美的报告
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional


class ReportGenerator:
    """报告生成器"""

    # Emoji 映射
    EMOJI = {
        "ai": "🤖",
        "china": "🇨🇳",
        "france": "🇫🇷",
        "title": "📰",
        "time": "🕐",
        "link": "🔗",
        "divider": "─" * 30
    }

    # 分类名称映射
    CATEGORY_NAMES = {
        "ai": "AI 前沿",
        "china": "中国要闻",
        "france": "法国动态",
        "fr_china": "在法华人相关"
    }

    def __init__(self):
        """初始化报告生成器"""
        self.report_data = {}
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _build_openai_summary(self, news_data: Dict[str, List[Dict]]) -> str:
        """使用 OpenAI 生成摘要（包含原链接）。"""
        if not self.openai_api_key:
            return ""

        items = []
        for category in ("ai", "china", "france", "fr_china"):
            cname = self.CATEGORY_NAMES.get(category, category)
            for article in news_data.get(category, [])[:5]:
                items.append({
                    "category": cname,
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", "")
                })

        if not items:
            return ""

        prompt = (
            "你是新闻编辑。请将输入新闻整理为中文简报，重点突出对‘住在法国的中国人’有价值的信息。"
            "输出 5-8 条要点，每条必须附上原链接，格式为：- 要点（来源：[标题](URL)）。"
            "不要编造信息。"
        )

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": self.openai_model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json.dumps(items, ensure_ascii=False)}
                    ],
                    "temperature": 0.2
                }),
                timeout=45
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(f"⚠️ OpenAI 摘要生成失败，回退为规则摘要: {e}")
            return ""

    def _build_fallback_summary(self, news_data: Dict[str, List[Dict]]) -> str:
        """无 OpenAI 或失败时的规则摘要（包含链接）。"""
        lines = []
        for category in ("fr_china", "france", "china", "ai"):
            cname = self.CATEGORY_NAMES.get(category, category)
            for article in news_data.get(category, [])[:2]:
                title = article.get("title", "无标题")
                url = article.get("url", "")
                source = article.get("source", "未知来源")
                if url:
                    lines.append(f"- [{cname}] {title}（来源: {source}，链接: {url}）")
                else:
                    lines.append(f"- [{cname}] {title}（来源: {source}）")
        return "\n".join(lines[:8])

    def generate_text_report(self, news_data: Dict[str, List[Dict]]) -> str:
        """生成纯文本格式的报告

        Args:
            news_data: 新闻数据字典

        Returns:
            格式化的报告文本
        """
        # 获取日期
        today = datetime.now().strftime("%Y年%m月%d日")
        time_str = datetime.now().strftime("%H:%M")

        # 构建报告
        lines = []

        # 标题
        lines.append(f"{self.EMOJI['title']} 每日新闻简报")
        lines.append(f"📅 {today} {self.EMOJI['time']}")
        lines.append("")
        lines.append(self.EMOJI['divider'])

        # AI 新闻
        lines.extend(self._format_category("ai", news_data.get("ai", [])))

        # 中国新闻
        lines.extend(self._format_category("china", news_data.get("china", [])))

        # 法国新闻
        lines.extend(self._format_category("france", news_data.get("france", [])))

        # 在法华人相关
        lines.extend(self._format_category("fr_china", news_data.get("fr_china", [])))

        # 底部信息
        lines.append("")
        lines.append(self.EMOJI['divider'])
        lines.append("💡 每天早上自动推送 | 数据来源：NewsAPI")

        return "\n".join(lines)

    def _format_category(self, category: str, articles: List[Dict]) -> List[str]:
        """格式化单个分类的新闻

        Args:
            category: 分类名称
            articles: 文章列表

        Returns:
            格式化的行列表
        """
        lines = []
        emoji = self.EMOJI.get(category, "📌")
        name = self.CATEGORY_NAMES.get(category, category)

        lines.append("")
        lines.append(f"{emoji} **{name}**")
        lines.append("")

        if not articles:
            lines.append("> 暂无新闻更新")
            return lines

        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "无标题")
            description = article.get("description", "")
            source = article.get("source", "未知来源")
            url = article.get("url", "")

            # 添加标题
            lines.append(f"{i}. {title}")

            # 如果有描述，添加描述
            if description:
                # 截断过长的描述
                if len(description) > 100:
                    description = description[:100] + "..."
                lines.append(f"   > {description}")

            # 添加来源
            lines.append(f"   来源: {source}")
            lines.append("")

        return lines

    def generate_markdown_report(self, news_data: Dict[str, List[Dict]]) -> str:
        """生成 Markdown 格式的报告（用于企业微信等支持 Markdown 的平台）

        Args:
            news_data: 新闻数据字典

        Returns:
            Markdown 格式的报告
        """
        today = datetime.now().strftime("%Y年%m月%d日")

        md = []

        # 标题
        md.append(f"# 📰 每日新闻简报")
        md.append(f"**📅 {today}**")
        md.append("")
        md.append("---")
        md.append("")

        # AI 新闻
        md.extend(self._format_markdown_category("ai", news_data.get("ai", [])))

        # 中国新闻
        md.extend(self._format_markdown_category("china", news_data.get("china", [])))

        # 法国新闻
        md.extend(self._format_markdown_category("france", news_data.get("france", [])))

        # 在法华人相关
        md.extend(self._format_markdown_category("fr_china", news_data.get("fr_china", [])))

        # 生成摘要（优先 OpenAI）
        md.append("## 🧠 今日重点摘要（含原链接）")
        md.append("")
        ai_summary = self._build_openai_summary(news_data)
        if ai_summary:
            md.append(ai_summary)
        else:
            md.append(self._build_fallback_summary(news_data))
        md.append("")

        # 底部
        md.append("---")
        md.append("")
        md.append("> 💡 每天早上 10:00 自动推送")

        return "\n".join(md)

    def _format_markdown_category(self, category: str, articles: List[Dict]) -> List[str]:
        """格式化单个分类为 Markdown

        Args:
            category: 分类名称
            articles: 文章列表

        Returns:
            Markdown 行列表
        """
        emoji = self.EMOJI.get(category, "📌")
        name = self.CATEGORY_NAMES.get(category, category)

        lines = []
        lines.append(f"## {emoji} {name}")
        lines.append("")

        if not articles:
            lines.append("> 暂无新闻更新")
            lines.append("")
            return lines

        for article in articles[:5]:
            title = article.get("title", "无标题")
            description = article.get("description", "")
            source = article.get("source", "未知来源")
            url = article.get("url", "")

            # 使用 Markdown 链接格式
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")

            if description:
                if len(description) > 80:
                    description = description[:80] + "..."
                lines.append(f"  > {description}")

            lines.append(f"  > 来源: {source}")
            lines.append("")

        return lines

    def generate_html_report(self, news_data: Dict[str, List[Dict]]) -> str:
        """生成 HTML 格式的报告

        Args:
            news_data: 新闻数据字典

        Returns:
            HTML 格式的报告
        """
        today = datetime.now().strftime("%Y年%m月%d日")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新闻简报 - {today}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .date {{
            color: #666;
            font-size: 14px;
        }}
        .category {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .category h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .category-ai h2 {{ border-color: #007AFF; }}
        .category-china h2 {{ border-color: #FF3B30; }}
        .category-france h2 {{ border-color: #5856D6; }}
        .news-item {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .news-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .news-title {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}
        .news-title a {{
            color: #007AFF;
            text-decoration: none;
        }}
        .news-description {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            line-height: 1.5;
        }}
        .news-source {{
            font-size: 12px;
            color: #999;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 每日新闻简报</h1>
        <div class="date">{today}</div>
    </div>
"""

        # AI 新闻
        html += self._format_html_category("ai", "AI 前沿", news_data.get("ai", []))

        # 中国新闻
        html += self._format_html_category("china", "中国要闻", news_data.get("china", []))

        # 法国新闻
        html += self._format_html_category("france", "法国动态", news_data.get("france", []))

        # 在法华人相关
        html += self._format_html_category("fr_china", "在法华人相关", news_data.get("fr_china", []))

        html += """
    <div class="footer">
        <p>每天早上 10:00 自动推送 | 数据来源：NewsAPI</p>
    </div>
</body>
</html>
"""

        return html

    def _format_html_category(self, category: str, name: str, articles: List[Dict]) -> str:
        """格式化单个分类为 HTML

        Args:
            category: 分类标识
            name: 分类名称
            articles: 文章列表

        Returns:
            HTML 字符串
        """
        emoji = self.EMOJI.get(category, "📌")

        html = f'<div class="category category-{category}">\n'
        html += f'    <h2>{emoji} {name}</h2>\n'

        if not articles:
            html += '    <p>暂无新闻更新</p>\n'
            html += '</div>\n'
            return html

        for article in articles[:5]:
            title = article.get("title", "无标题")
            description = article.get("description", "")
            source = article.get("source", "未知来源")
            url = article.get("url", "")

            html += '    <div class="news-item">\n'
            html += f'      <div class="news-title"><a href="{url}" target="_blank">{title}</a></div>\n'

            if description:
                html += f'      <div class="news-description">{description}</div>\n'

            html += f'      <div class="news-source">来源: {source}</div>\n'
            html += '    </div>\n'

        html += '</div>\n'
        return html

    def generate_summary(self, news_data: Dict[str, List[Dict]]) -> str:
        """生成新闻摘要（用于推送标题等简短场景）

        Args:
            news_data: 新闻数据字典

        Returns:
            摘要文本
        """
        counts = {k: len(v) for k, v in news_data.items()}
        total = sum(counts.values())

        return (
            f"今日简报：AI {counts.get('ai', 0)}条 | 中国 {counts.get('china', 0)}条 | "
            f"法国 {counts.get('france', 0)}条 | 在法华人 {counts.get('fr_china', 0)}条"
        )


if __name__ == "__main__":
    # 测试代码
    generator = ReportGenerator()

    # 模拟数据
    test_data = {
        "ai": [
            {
                "title": "OpenAI 发布新模型",
                "description": "新一代 AI 模型带来重大突破",
                "url": "https://openai.com",
                "source": "OpenAI"
            }
        ],
        "china": [
            {
                "title": "中国科技发展",
                "description": "数字经济持续增长",
                "url": "https://xinhuanet.com",
                "source": "新华网"
            }
        ],
        "france": [
            {
                "title": "法国新闻",
                "description": "法国最新动态",
                "url": "https://lemonde.fr",
                "source": "Le Monde"
            }
        ]
    }

    print("=== 文本报告 ===")
    print(generator.generate_text_report(test_data))

    print("\n=== Markdown 报告 ===")
    print(generator.generate_markdown_report(test_data))
