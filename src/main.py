#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日新闻报告机器人
主入口文件
"""

import os
import sys
from datetime import datetime

from fetcher import NewsFetcher
from generator import ReportGenerator
from notifier import NewsNotifier


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 每日新闻报告机器人启动")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # 步骤 1: 获取新闻
        print("\n📥 步骤 1: 获取新闻数据...")
        fetcher = NewsFetcher()
        news_data = fetcher.fetch_all_news()

        if not news_data:
            print("⚠️ 警告: 未能获取到新闻数据")
            return False

        # 统计新闻数量
        total_news = sum(len(articles) for articles in news_data.values())
        print(f"✅ 成功获取 {total_news} 条新闻")

        # 步骤 2: 生成报告
        print("\n📝 步骤 2: 生成新闻报告...")
        generator = ReportGenerator()

        # 生成 Markdown 格式（适合微信推送）
        report_content = generator.generate_markdown_report(news_data)
        report_summary = generator.generate_summary(news_data)

        print(f"✅ 报告生成完成")
        print(f"   摘要: {report_summary}")

        # 步骤 3: 发送推送
        print("\n📤 步骤 3: 发送微信推送...")
        notifier = NewsNotifier()

        success = notifier.send_daily_report(report_content)

        if success:
            print("\n" + "=" * 50)
            print("✅ 每日新闻报告发送成功！")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ 发送失败，请检查配置")
            print("=" * 50)
            return False

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mode():
    """测试模式：发送测试消息"""
    print("=" * 50)
    print("🧪 测试模式：发送测试消息")
    print("=" * 50)

    try:
        notifier = NewsNotifier()
        success = notifier.send_test_message()

        if success:
            print("\n✅ 测试消息发送成功！")
        else:
            print("\n❌ 测试消息发送失败")

        return success

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 测试模式
        success = test_mode()
    else:
        # 正常运行模式
        success = main()

    # 退出代码
    sys.exit(0 if success else 1)
