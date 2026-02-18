#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信推送模块
支持多种推送方式：ServerChan、企业微信、Webhook
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict


class WeChatNotifier:
    """微信推送器"""

    def __init__(self, serverchan_key: Optional[str] = None):
        """初始化微信推送器

        Args:
            serverchan_key: ServerChan 推送密钥，如不提供则从环境变量读取
        """
        self.serverchan_key = serverchan_key or os.getenv("SERVERCHAN_KEY")
        self.serverchan_url = "https://sctapi.ftqq.com"

    def send_via_serverchan(self, title: str, content: str) -> bool:
        """通过 ServerChan 发送消息

        Args:
            title: 消息标题
            content: 消息内容

        Returns:
            是否发送成功
        """
        if not self.serverchan_key:
            print("错误: 未配置 ServerChan Key")
            print("请设置 SERVERCHAN_KEY 环境变量")
            return False

        url = f"{self.serverchan_url}/{self.serverchan_key}.send"
        # 使用 ServerChan 默认推送通道，避免固定 channel/openid 导致“接口成功但未送达”。
        data = {
            "title": title,
            "desp": content,
        }

        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as e:
            print(f"✗ ServerChan 请求错误: {e}")
            return False
        except ValueError:
            print(f"✗ ServerChan 响应不是有效 JSON: {response.text[:200]}")
            return False

        if result.get("code") == 0:
            print("✓ ServerChan 推送成功")
            return True

        print(
            "✗ ServerChan 推送失败: "
            f"code={result.get('code')}, message={result.get('message', '未知错误')}"
        )
        return False

    def send_via_wecom_webhook(
        self,
        webhook_url: str,
        content: str,
        mentioned_ids: Optional[list] = None,
        mentioned_mobile_list: Optional[list] = None
    ) -> bool:
        """通过企业微信 Webhook 发送消息

        Args:
            webhook_url: 企业微信 Webhook URL
            content: 消息内容
            mentioned_ids: @成员 ID 列表
            mentioned_mobile_list: @成员手机号列表

        Returns:
            是否发送成功
        """
        url = webhook_url

        # 企业微信支持 Markdown
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content,
                "mentioned_list": mentioned_ids or [],
                "mentioned_mobile_list": mentioned_mobile_list or []
            }
        }

        try:
            response = requests.post(url, data=json.dumps(data), timeout=30)
            result = response.json()

            if result.get("errcode") == 0:
                print("✓ 企业微信推送成功")
                return True
            else:
                print(f"✗ 企业微信推送失败: {result.get('errmsg', '未知错误')}")
                return False

        except requests.RequestException as e:
            print(f"✗ 企业微信请求错误: {e}")
            return False

    def send_via_webhook(
        self,
        webhook_url: str,
        payload: Dict,
        headers: Optional[Dict] = None
    ) -> bool:
        """通过自定义 Webhook 发送消息

        Args:
            webhook_url: Webhook URL
            payload: 请求载荷
            headers: 请求头

        Returns:
            是否发送成功
        """
        url = webhook_url
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)

        try:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=default_headers,
                timeout=30
            )

            # 假设 2xx 为成功
            if 200 <= response.status_code < 300:
                print("✓ Webhook 推送成功")
                return True
            else:
                print(f"✗ Webhook 推送失败: HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            print(f"✗ Webhook 请求错误: {e}")
            return False

    def send(
        self,
        title: str,
        content: str,
        webhook_url: Optional[str] = None,
        webhook_type: str = "serverchan"
    ) -> bool:
        """发送消息的通用接口

        Args:
            title: 消息标题
            content: 消息内容
            webhook_url: Webhook URL（用于非 ServerChan 方式）
            webhook_type: 推送类型：serverchan、wecom、webhook

        Returns:
            是否发送成功
        """
        # 根据类型选择发送方式
        if webhook_type == "serverchan":
            return self.send_via_serverchan(title, content)
        elif webhook_type == "wecom":
            if not webhook_url:
                print("错误: 企业微信推送需要提供 webhook_url")
                return False
            return self.send_via_wecom_webhook(webhook_url, content)
        elif webhook_type == "webhook":
            if not webhook_url:
                print("错误: Webhook 推送需要提供 webhook_url")
                return False
            # 默认使用文本格式
            payload = {"text": content}
            return self.send_via_webhook(webhook_url, payload)
        else:
            print(f"错误: 不支持的推送类型 {webhook_type}")
            return False


class NewsNotifier:
    """新闻报告推送器"""

    def __init__(self):
        """初始化新闻推送器"""
        self.notifier = WeChatNotifier()

    def send_daily_report(self, news_content: str) -> bool:
        """发送每日新闻报告

        Args:
            news_content: 新闻报告内容

        Returns:
            是否发送成功
        """
        # 生成标题
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"📰 每日新闻简报 - {today}"

        # 发送消息
        return self.notifier.send(title, news_content, webhook_type="serverchan")

    def send_test_message(self) -> bool:
        """发送测试消息

        Returns:
            是否发送成功
        """
        title = "🧪 测试消息"
        content = """这是一条测试消息。

如果收到这条消息，说明新闻推送系统配置正确！

✅ 系统状态：正常
⏰ 定时任务：已启用
📝 消息格式：Markdown

每天早上 10:00 您将收到：
- 🤖 AI 前沿新闻
- 🇨🇳 中国要闻
- 🇫🇷 法国动态

祝您阅读愉快！"""

        return self.notifier.send(title, content, webhook_type="serverchan")


if __name__ == "__main__":
    # 测试代码
    print("=== 发送测试消息 ===")

    notifier = NewsNotifier()
    success = notifier.send_test_message()

    if success:
        print("测试消息已发送，请检查微信")
    else:
        print("发送失败，请检查配置")
