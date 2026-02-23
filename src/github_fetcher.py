#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 热门项目获取
"""

import os
import requests
from typing import List, Dict, Optional


class GitHubTrendingFetcher:
    """GitHub Trending 抓取器"""

    def __init__(self):
        self.language = os.getenv("GITHUB_TRENDING_LANGUAGE", "python")

    def fetch_trending(self, limit: int = 10) -> List[Dict]:
        """获取 GitHub 热门项目

        Args:
            limit: 返回数量

        Returns:
            项目列表
        """
        url = f"https://api.github.com/search/repositories"
        params = {
            "q": f"language:{self.language} pushed:>2025-12-01",
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            repos = []
            for item in data.get("items", [])[:limit]:
                repos.append(
                    {
                        "name": item.get("full_name", ""),
                        "description": item.get("description", ""),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "url": item.get("html_url", ""),
                        "language": item.get("language", ""),
                    }
                )

            return repos

        except Exception as e:
            print(f"⚠️ GitHub Trending 获取失败: {e}")
            return []

    def fetch_multi_language(
        self, languages: List[str] = None, limit_per_lang: int = 5
    ) -> List[Dict]:
        """获取多语言的热门项目

        Args:
            languages: 语言列表，如 ["python", "javascript", "go"]
            limit_per_lang: 每种语言的数量

        Returns:
            合并后的项目列表（按星标排序）
        """
        languages = languages or ["python", "javascript"]
        all_repos = []

        headers = {"Accept": "application/vnd.github.v3+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        for lang in languages:
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"language:{lang} pushed:>2025-12-01",
                "sort": "stars",
                "order": "desc",
                "per_page": limit_per_lang,
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", [])[:limit_per_lang]:
                    all_repos.append(
                        {
                            "name": item.get("full_name", ""),
                            "description": item.get("description", ""),
                            "stars": item.get("stargazers_count", 0),
                            "forks": item.get("forks_count", 0),
                            "url": item.get("html_url", ""),
                            "language": item.get("language", ""),
                        }
                    )
            except Exception as e:
                print(f"⚠️ 获取 {lang} 失败: {e}")
                continue

        all_repos.sort(key=lambda x: x["stars"], reverse=True)
        return all_repos[:20]


if __name__ == "__main__":
    print("=== GitHub Trending 测试 ===\n")

    fetcher = GitHubTrendingFetcher()
    repos = fetcher.fetch_multi_language(limit_per_lang=5)

    for i, repo in enumerate(repos[:10], 1):
        print(f"{i}. {repo['name']}")
        print(f"   ⭐ {repo['stars']:,} | {repo['language']}")
        print(f"   {repo['description'][:60]}...")
        print(f"   {repo['url']}")
        print()
