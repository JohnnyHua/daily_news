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
        "tech": "📱",
        "github": "⭐",
        "china": "🇨🇳",
        "france": "🇫🇷",
        "title": "📰",
        "time": "🕐",
        "link": "🔗",
        "star": "⭐",
        "fire": "🔥",
    }

    # 分类名称映射
    CATEGORY_NAMES = {
        "ai": "AI 前沿",
        "tech": "科技要闻",
        "github": "GitHub 热门",
        "france": "法国动态",
        "china": "中国要闻",
    }

    def __init__(self):
        """初始化报告生成器"""
        self.report_data = {}
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _build_openai_summary(
        self, news_data: Dict[str, List[Dict]], github_data: List[Dict]
    ) -> str:
        """使用 OpenAI 生成中文摘要。"""
        if not self.openai_api_key:
            return ""

        items = []
        # 新闻
        for category in ("ai", "tech", "france", "china"):
            cname = self.CATEGORY_NAMES.get(category, category)
            for article in news_data.get(category, [])[:3]:
                items.append(
                    {
                        "type": "新闻",
                        "category": cname,
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                    }
                )

        # GitHub 项目
        for repo in github_data[:5]:
            items.append(
                {
                    "type": "GitHub",
                    "category": "GitHub 热门",
                    "title": repo.get("name", ""),
                    "description": repo.get("description", ""),
                    "stars": repo.get("stars", 0),
                    "url": repo.get("url", ""),
                }
            )

        if not items:
            return ""

        prompt = """你是新闻编辑。请将以下内容整理为精美的中文简报。
要求：
1. 重点突出对程序员/技术爱好者有价值的信息
2. 输出 5-8 条要点，每条必须附上原链接
3. 格式：- 要点内容（[标题](URL)）
4. 如果有 GitHub 项目，说明星标数
5. 用词专业但易懂
6. 不要编造信息"""

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(
                    {
                        "model": self.openai_model,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {
                                "role": "user",
                                "content": json.dumps(items, ensure_ascii=False),
                            },
                        ],
                        "temperature": 0.3,
                    }
                ),
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"⚠️ OpenAI 摘要生成失败: {e}")
            return ""

    def _build_fallback_summary(
        self, news_data: Dict[str, List[Dict]], github_data: List[Dict]
    ) -> str:
        """无 OpenAI 时的规则摘要。"""
        lines = []

        # GitHub 项目
        if github_data:
            lines.append("### 🔥 GitHub 热门项目")
            for repo in github_data[:3]:
                name = repo.get("name", "")
                stars = repo.get("stars", 0)
                url = repo.get("url", "")
                lines.append(f"- [{name}]({url}) ⭐ {stars}")
            lines.append("")

        # 新闻
        for category in ("ai", "tech", "france", "china"):
            cname = self.CATEGORY_NAMES.get(category, category)
            for article in news_data.get(category, [])[:2]:
                title = article.get("title", "无标题")
                url = article.get("url", "")
                if url:
                    lines.append(f"- [{title}]({url})")
                else:
                    lines.append(f"- {title}")

        return "\n".join(lines[:10])

    def generate_markdown_report(
        self, news_data: Dict[str, List[Dict]], github_data: Optional[List[Dict]] = None
    ) -> str:
        """生成精美的 Markdown 格式报告

        Args:
            news_data: 新闻数据字典
            github_data: GitHub 热门项目列表

        Returns:
            Markdown 格式的报告
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        github_data = github_data or []

        md = []

        # ==================== 头部 ====================
        md.append("# 📰 每日新闻简报")
        md.append("")
        md.append(f"**📅 {today}** · **🤖 AI 摘要** · **⭐ GitHub 热门**")
        md.append("")
        md.append("---")
        md.append("")

        # ==================== GitHub 热门项目 ====================
        if github_data:
            md.append("## ⭐ GitHub 热门项目")
            md.append("")
            md.append("| 项目 | 描述 | ⭐ Stars |")
            md.append("|------|------|----------|")
            for repo in github_data[:8]:
                name = repo.get("name", "N/A")
                desc = (repo.get("description") or "暂无描述")[:50]
                stars = repo.get("stars", 0)
                url = repo.get("url", "")
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                if url:
                    md.append(f"| [{name}]({url}) | {desc} | {stars:,} |")
                else:
                    md.append(f"| {name} | {desc} | {stars:,} |")
            md.append("")

        # ==================== AI 新闻 ====================
        md.extend(self._format_markdown_category("ai", news_data.get("ai", [])))

        # ==================== 科技要闻 ====================
        md.extend(self._format_markdown_category("tech", news_data.get("tech", [])))

        # ==================== 法国新闻 ====================
        md.extend(self._format_markdown_category("france", news_data.get("france", [])))

        # ==================== 中国新闻 ====================
        md.extend(self._format_markdown_category("china", news_data.get("china", [])))

        # ==================== AI 摘要 ====================
        md.append("## 🧠 今日要闻摘要")
        md.append("")
        ai_summary = self._build_openai_summary(news_data, github_data)
        if ai_summary:
            md.append(ai_summary)
        else:
            md.append(self._build_fallback_summary(news_data, github_data))
        md.append("")

        # ==================== 底部 ====================
        md.append("---")
        md.append("")
        md.append("> 💡 每天早上自动推送 · 数据来源：RSS 订阅 + GitHub Trending")
        md.append("> ")
        md.append("> 🤖 摘要由 AI 生成 · 📧 邮件发送")

        return "\n".join(md)

    def _format_markdown_category(
        self, category: str, articles: List[Dict]
    ) -> List[str]:
        """格式化单个分类为 Markdown

        Args:
            category: 分类标识
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
            lines.append("> 暂无更新")
            lines.append("")
            return lines

        for article in articles[:5]:
            title = article.get("title", "无标题")
            description = article.get("description", "")
            source = article.get("source", "未知来源")
            url = article.get("url", "")

            if url:
                lines.append(f"**[{title}]({url})**")
            else:
                lines.append(f"**{title}**")

            if description:
                if len(description) > 100:
                    description = description[:100] + "..."
                lines.append(f"> {description}")

            lines.append(f"> 来源: {source}")
            lines.append("")

        return lines

    def generate_html_report(
        self, news_data: Dict[str, List[Dict]], github_data: Optional[List[Dict]] = None
    ) -> str:
        """生成精美的 HTML 格式报告

        Args:
            news_data: 新闻数据字典
            github_data: GitHub 热门项目列表

        Returns:
            HTML 格式的报告
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        github_data = github_data or []

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新闻简报 - {today}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .header h1 {{
            color: #333;
            font-size: 32px;
            margin: 0 0 10px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .date {{
            color: #666;
            font-size: 14px;
        }}
        .badges {{
            margin-top: 10px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin: 0 4px;
            background: #f0f0f0;
            color: #666;
        }}
        .badge.ai {{ background: #e3f2fd; color: #1976d2; }}
        .badge.github {{ background: #fff3e0; color: #f57c00; }}
        
        .github-section {{
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        .github-section h2 {{
            color: #fff;
            margin: 0 0 15px 0;
            font-size: 18px;
        }}
        .github-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .github-table th, .github-table td {{
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid #333;
            color: #ccc;
            font-size: 13px;
        }}
        .github-table th {{
            color: #888;
            font-weight: normal;
        }}
        .github-table a {{
            color: #4fc3f7;
            text-decoration: none;
        }}
        .github-table .stars {{
            color: #ffd700;
        }}
        
        .category {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .category h2 {{
            color: #333;
            font-size: 18px;
            margin: 0 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .category-ai h2 {{ border-color: #1976d2; }}
        .category-tech h2 {{ border-color: #388e3c; }}
        .category-france h2 {{ border-color: #7b1fa2; }}
        .category-china h2 {{ border-color: #d32f2f; }}
        
        .news-item {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .news-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .news-title {{
            font-size: 15px;
            font-weight: 600;
            color: #333;
            margin-bottom: 6px;
        }}
        .news-title a {{
            color: #1976d2;
            text-decoration: none;
        }}
        .news-title a:hover {{
            text-decoration: underline;
        }}
        .news-description {{
            font-size: 13px;
            color: #666;
            margin-bottom: 6px;
            line-height: 1.5;
        }}
        .news-source {{
            font-size: 11px;
            color: #999;
        }}
        
        .summary-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            margin-top: 25px;
            color: white;
        }}
        .summary-section h2 {{
            color: white;
            margin: 0 0 15px 0;
            font-size: 18px;
        }}
        .summary-content {{
            font-size: 14px;
            line-height: 1.8;
        }}
        .summary-content a {{
            color: #4fc3f7;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日新闻简报</h1>
            <div class="date">{today}</div>
            <div class="badges">
                <span class="badge ai">🤖 AI 摘要</span>
                <span class="badge github">⭐ GitHub</span>
            </div>
        </div>
"""

        # GitHub 热门项目
        if github_data:
            html += '<div class="github-section">\n'
            html += "<h2>⭐ GitHub 热门项目</h2>\n"
            html += '<table class="github-table">\n'
            html += "<tr><th>项目</th><th>描述</th><th>Stars</th></tr>\n"
            for repo in github_data[:8]:
                name = repo.get("name", "N/A")
                desc = (repo.get("description") or "暂无描述")[:40]
                stars = repo.get("stars", 0)
                url = repo.get("url", "")
                if len(desc) > 40:
                    desc = desc[:40] + "..."
                html += f"<tr>"
                if url:
                    html += f'<td><a href="{url}" target="_blank">{name}</a></td>'
                else:
                    html += f"<td>{name}</td>"
                html += f"<td>{desc}</td>"
                html += f'<td class="stars">⭐ {stars:,}</td>'
                html += f"</tr>\n"
            html += "</table>\n"
            html += "</div>\n"

        # AI 新闻
        html += self._format_html_category("ai", "🤖 AI 前沿", news_data.get("ai", []))

        # 科技要闻
        html += self._format_html_category(
            "tech", "📱 科技要闻", news_data.get("tech", [])
        )

        # 法国新闻
        html += self._format_html_category(
            "france", "🇫🇷 法国动态", news_data.get("france", [])
        )

        # 中国新闻
        html += self._format_html_category(
            "china", "🇨🇳 中国要闻", news_data.get("china", [])
        )

        # AI 摘要
        ai_summary = self._build_openai_summary(news_data, github_data)
        summary_content = (
            ai_summary
            if ai_summary
            else self._build_fallback_summary(news_data, github_data)
        )

        html_summary = summary_content.replace("\n", "<br>")

        html += f"""
        <div class="summary-section">
            <h2>🧠 今日要闻摘要</h2>
            <div class="summary-content">
                {html_summary}
            </div>
        </div>
"""

        html += """
        <div class="footer">
            <p>每天早上自动推送 · 数据来源：RSS 订阅 + GitHub Trending</p>
            <p>🤖 摘要由 AI 生成 · 📧 邮件发送</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _format_html_category(
        self, category: str, name: str, articles: List[Dict]
    ) -> str:
        """格式化单个分类为 HTML

        Args:
            category: 分类标识
            name: 分类名称
            articles: 文章列表

        Returns:
            HTML 字符串
        """
        html = f'<div class="category category-{category}">\n'
        html += f"    <h2>{name}</h2>\n"

        if not articles:
            html += "    <p>暂无更新</p>\n"
            html += "</div>\n"
            return html

        for article in articles[:5]:
            title = article.get("title", "无标题")
            description = article.get("description", "")
            source = article.get("source", "未知来源")
            url = article.get("url", "")

            html += '    <div class="news-item">\n'
            if url:
                html += f'      <div class="news-title"><a href="{url}" target="_blank">{title}</a></div>\n'
            else:
                html += f'      <div class="news-title">{title}</div>\n'

            if description:
                html += f'      <div class="news-description">{description}</div>\n'

            html += f'      <div class="news-source">来源: {source}</div>\n'
            html += "    </div>\n"

        html += "</div>\n"
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
            f"今日简报：AI {counts.get('ai', 0)}条 | 科技 {counts.get('tech', 0)}条 | "
            f"法国 {counts.get('france', 0)}条 | 中国 {counts.get('china', 0)}条"
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
                "source": "OpenAI",
            }
        ],
        "tech": [
            {
                "title": "苹果发布新品",
                "description": "最新科技产品发布",
                "url": "https://apple.com",
                "source": "Apple",
            }
        ],
        "china": [
            {
                "title": "中国科技发展",
                "description": "数字经济持续增长",
                "url": "https://xinhuanet.com",
                "source": "新华网",
            }
        ],
        "france": [
            {
                "title": "法国新闻",
                "description": "法国最新动态",
                "url": "https://lemonde.fr",
                "source": "Le Monde",
            }
        ],
    }

    github_test = [
        {
            "name": "awesome-chatgpt-plugins",
            "description": "ChatGPT 插件精选列表",
            "stars": 15000,
            "url": "https://github.com/awesome/chatgpt-plugins",
        }
    ]

    print("=== Markdown 报告 ===")
    print(generator.generate_markdown_report(test_data, github_test))
