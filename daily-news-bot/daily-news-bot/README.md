---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3046022100c6516f0ede76ec33b0de42cf7ef58bcca2eede3a6faeaf3e855e70b86c33ad140221008244c2453d65d4f97bf609bacd1a8383588c2355356e09062501d573da858721
    ReservedCode2: 3046022100a727cd595abb6528e1a35504947b5b5ed7eb081fe41aa9093bc6c7673ba1a188022100a72c0b59d675a3b151b98d9a370754a7d3f4e770d7b25dce9c500283b557bef9
---

# 每日新闻报告系统

这是一个基于 GitHub Actions 的定时新闻报告机器人，每天早上自动获取并推送 AI、中国和法国的新闻。

## 功能特点

- 🤖 **AI 前沿**：每日获取最新人工智能领域新闻
- 🇨🇳 **中国要闻**：获取中国国内重要新闻
- 🇫🇷 **法国动态**：获取法国地区重要新闻
- ⏰ **定时推送**：每天早上 10 点自动发送

## 支持的推送方式

1. **ServerChan（微信推送）** - 推荐个人用户使用
2. **企业微信 Webhook** - 适合企业用户
3. **自定义 Webhook** - 支持其他 HTTP POST 接口

## 快速开始

### 1. Fork 本仓库

### 2. 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|----------|
| `SERVERCHAN_KEY` | ServerChan 微信推送密钥 | [ServerChan 官网](https://sct.ftqq.com/) |
| `NEWS_API_KEY` | 新闻 API 密钥（可选） | [NewsAPI 官网](https://newsapi.org/) |
| `OPENAI_API_KEY` | OpenAI API 密钥（可选） | 用于 AI 摘要优化 |

### 3. 启用 Actions

在 GitHub 仓库的 Actions 页面启用 Workflows。

### 4. 手动测试

可以在 Actions 页面手动触发 "Daily News Report" workflow 进行测试。

## 项目结构

```
.
├── .github/
│   └── workflows/
│       └── daily_news.yml      # GitHub Actions 配置
├── src/
│   ├── main.py                  # 主入口
│   ├── fetcher.py               # 新闻获取
│   ├── generator.py             # 报告生成
│   └── notifier.py             # 微信推送
├── requirements.txt             # Python 依赖
└── README.md                    # 说明文档
```

## 配置说明

### 修改新闻关键词

在 `src/fetcher.py` 中可以修改搜索的关键词：

```python
TOPICS = {
    "ai": ["artificial intelligence", "AI", "machine learning"],
    "china": ["China news", "Chinese economy"],
    "france": ["France news", "Paris"]
}
```

### 修改推送时间

在 `.github/workflows/daily_news.yml` 中修改 cron 表达式：

```yaml
schedule:
  # 北京时间 10:00 = UTC 02:00
  - cron: '0 2 * * *'
```

### 修改推送内容

在 `src/generator.py` 中自定义报告格式。

## 常见问题

**Q: 为什么收不到推送？**
A: 检查 Secrets 配置是否正确，确保 ServerChan 密钥有效。

**Q: 如何修改推送时间？**
A: 修改 `.github/workflows/daily_news.yml` 中的 cron 表达式。

**Q: 可以推送给自己吗？**
A: 可以，ServerChan 支持绑定微信后推送给自己。

## 许可证

MIT License
