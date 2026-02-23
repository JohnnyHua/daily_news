#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信推送模块
支持多种推送方式：ServerChan、企业微信、Webhook
"""

import os
import json
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor


class WeChatNotifier:
    """微信推送器"""

    def __init__(self, serverchan_key: Optional[str] = None):
        """初始化微信推送器

        Args:
            serverchan_key: ServerChan 推送密钥，如不提供则从环境变量读取
        """
        self.serverchan_key = serverchan_key or os.getenv("SERVERCHAN_KEY")
        self.serverchan_url = "https://sctapi.ftqq.com"
        self.serverchan_debug = os.getenv("SERVERCHAN_DEBUG", "0") == "1"
        self.serverchan_channel = os.getenv("SERVERCHAN_CHANNEL")
        self.serverchan_openid = os.getenv("SERVERCHAN_OPENID")

    def _mask_serverchan_key(self) -> str:
        """隐藏敏感 Key，仅输出少量字符用于排查。"""
        if not self.serverchan_key:
            return "<empty>"
        key = self.serverchan_key
        if len(key) <= 8:
            return f"{key[:2]}***{key[-2:]}"
        return f"{key[:4]}***{key[-4:]}"

    def _print_serverchan_debug_info(self, url: str, payload: Dict) -> None:
        """输出 ServerChan 调试信息（不会泄露完整 key）。"""
        if not self.serverchan_debug:
            return

        print("🧪 ServerChan 调试模式已开启")
        print(f"   endpoint: {self.serverchan_url}/<key>.send")
        print(f"   key(脱敏): {self._mask_serverchan_key()}")
        print(f"   request_url(脱敏): {url.replace(self.serverchan_key, '<key>')}")
        print(f"   title_len: {len(payload.get('title', ''))}")
        print(f"   desp_len: {len(payload.get('desp', ''))}")
        print(f"   channel: {payload.get('channel', '<default>')}")
        print(f"   openid: {payload.get('openid', '<default>')}")

    def _query_serverchan_push_status(self, pushid: str, readkey: str) -> Optional[Dict[str, Any]]:
        """查询 ServerChan 推送任务在微信侧的执行状态。"""
        if not pushid or not readkey:
            return None

        url = f"{self.serverchan_url}/push"
        params = {"id": pushid, "readkey": readkey}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            result = response.json()
            if self.serverchan_debug:
                print(f"   push_query_json: {json.dumps(result, ensure_ascii=False)}")
            return result
        except requests.RequestException as e:
            print(f"⚠️ 推送状态查询失败: {e}")
            return None
        except ValueError:
            print(f"⚠️ 推送状态查询返回非 JSON: {response.text[:200]}")
            return None

    @staticmethod
    def _extract_wxstatus(push_result: Dict[str, Any]) -> Optional[str]:
        """尽可能兼容不同字段结构，提取微信状态文本。"""
        data_obj = push_result.get("data") or {}
        wxstatus = data_obj.get("wxstatus")
        if wxstatus:
            return str(wxstatus)

        for key in ("message", "msg", "errmsg"):
            if push_result.get(key):
                return str(push_result[key])
        return None

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
        data = {
            "title": title,
            "desp": content,
        }
        if self.serverchan_channel:
            data["channel"] = self.serverchan_channel
        if self.serverchan_openid:
            data["openid"] = self.serverchan_openid
        self._print_serverchan_debug_info(url, data)

        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            if self.serverchan_debug:
                print(f"   http_status: {response.status_code}")
                print(f"   content_type: {response.headers.get('Content-Type', '未知')}")
            result = response.json()
        except requests.RequestException as e:
            print(f"✗ ServerChan 请求错误: {e}")
            return False
        except ValueError:
            print(f"✗ ServerChan 响应不是有效 JSON: {response.text[:200]}")
            return False

        if self.serverchan_debug:
            print(f"   response_json: {json.dumps(result, ensure_ascii=False)}")

        if result.get("code") == 0:
            print("✓ ServerChan 推送成功")
            data_obj = result.get("data") or {}
            pushid = data_obj.get("pushid")
            readkey = data_obj.get("readkey")
            if self.serverchan_debug:
                print(f"   pushid: {pushid or '<missing>'}")
                print(f"   readkey: {readkey or '<missing>'}")

            # ServerChan code=0 仅表示已进入异步队列，继续轮询微信侧状态。
            if pushid and readkey:
                push_status = None
                wxstatus = None
                for attempt in range(1, 4):
                    push_status = self._query_serverchan_push_status(pushid, readkey)
                    if not push_status:
                        continue
                    wxstatus = self._extract_wxstatus(push_status)
                    if self.serverchan_debug:
                        print(f"   status_poll_{attempt}: {wxstatus or '<empty>'}")
                    if wxstatus:
                        break
                    time.sleep(2)

                if self.serverchan_debug:
                    if wxstatus:
                        print(f"   wxstatus: {wxstatus}")
                    else:
                        print("   wxstatus: <empty>（轮询后仍为空，说明任务可能仍在队列中）")
            elif self.serverchan_debug:
                print("   响应中缺少 pushid/readkey，无法查询微信回执。")

            if self.serverchan_debug:
                print("   提示: 若 wxstatus 成功但仍看不到消息，请检查微信是否关闭服务通知、是否被折叠，或通道接收人是否配置正确。")
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


class EmailNotifier:
    """邮件推送器"""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM", self.smtp_user)
        self.to_email = os.getenv("SMTP_TO")

    def send_email(self, subject: str, content: str) -> bool:
        """发送邮件

        Args:
            subject: 邮件标题
            content: 邮件内容

        Returns:
            是否发送成功
        """
        if not all([self.smtp_user, self.smtp_password, self.to_email]):
            print("错误: 邮件配置不完整")
            print("需要设置: SMTP_USER, SMTP_PASSWORD, SMTP_TO")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            msg.attach(MIMEText(content, 'html', 'utf-8'))

            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"✓ 邮件发送成功 -> {self.to_email}")
            return True

        except Exception as e:
            print(f"✗ 邮件发送失败: {e}")
            return False


class NewsNotifier:
    """新闻报告推送器"""

    def __init__(self):
        self.notifier = WeChatNotifier()
        self.emailer = EmailNotifier()

    def send_daily_report(self, news_content: str, github_data: list = None) -> bool:
        """发送每日新闻报告

        Args:
            news_content: Markdown 格式的新闻报告
            github_data: GitHub 热门项目数据

        Returns:
            是否发送成功
        """
        from generator import ReportGenerator

        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"📰 每日新闻简报 - {today}"

        push_type = os.getenv("PUSH_TYPE", "serverchan")

        if push_type == "email":
            generator = ReportGenerator()
            # 从 news_content 解析出 news_data
            # 这里简化处理：直接用 markdown 作为邮件内容
            # 更好的做法是重构传参
            return self.emailer.send_email(title, news_content)
        else:
            return self.notifier.send(title, news_content, webhook_type=push_type)

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
- 📱 科技要闻
- 🇨🇳 中国要闻
- 🇫🇷 法国动态

祝您阅读愉快！"""

        push_type = os.getenv("PUSH_TYPE", "serverchan")

        if push_type == "email":
            return self.emailer.send_email(title, content)
        else:
            return self.notifier.send(title, content, webhook_type=push_type)


if __name__ == "__main__":
    # 测试代码
    print("=== 发送测试消息 ===")

    notifier = NewsNotifier()
    success = notifier.send_test_message()

    if success:
        print("测试消息已发送，请检查微信")
    else:
        print("发送失败，请检查配置")
