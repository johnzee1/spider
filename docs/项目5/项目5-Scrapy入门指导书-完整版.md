---
title: "项目5-Scrapy 入门"
---

# 项目5：Scrapy 入门

前四章是“自己写请求、自己写循环”。Scrapy 是一个已经准备好请求、并发、导出功能的爬虫框架。本章只使用一个文件，不先引入复杂的项目目录。

> 只使用公开页面；框架并不意味着可以提高访问频率。请遵守网站规则，先少量采集和验证。

## 本章任务

运行一个 Scrapy 爬虫，取出公开健康资讯页面的链接，并导出为 JSON 文件。

## 安装

```bash
pip install scrapy
```

![安装 Scrapy 参考](Pasted%20image%2020260712115257.png)

## 只认识三个词

- `Spider`：爬虫类，告诉 Scrapy 去哪里、取什么。
- `start_urls`：第一个要访问的网址。
- `parse`：网页下载完成后运行的函数。

## 完整代码

保存为 `health_news_spider.py`，或下载本章的[完整代码](health_news_spider.py)。

```python
import scrapy


class HealthNewsSpider(scrapy.Spider):
    name = "health_news"
    start_urls = ["https://health.people.com.cn/"]

    def parse(self, response):
        seen = set()
        for link in response.css("a[href]"):
            title = " ".join(link.css("::text").getall()).strip()
            url = response.urljoin(link.attrib["href"])

            if len(title) < 8 or title in seen:
                continue
            seen.add(title)
            yield {"title": title, "url": url}
```

`yield` 可以理解为“交给 Scrapy 一条数据”。Scrapy 会把很多条数据收集起来，再按命令要求导出。

## 运行

在脚本所在文件夹执行：

```bash
scrapy runspider health_news_spider.py -O health_news.json
```

`-O` 后面是输出文件名。运行后打开 `health_news.json`，每条数据都有 `title` 和 `url`。

![运行命令参考](Pasted%20image%2020260712121739.png)

## 常见问题

| 现象 | 处理 |
|---|---|
| 找不到 `scrapy` 命令 | 使用 `python -m scrapy runspider health_news_spider.py -O health_news.json` |
| 输出中有导航文字 | 把 `a[href]` 改成新闻区域的 CSS 选择器 |
| 想暂停 | 在终端按 `Ctrl + C`，不要强制关闭电脑 |

## 小练习

1. 增加 `source: "人民网健康"` 字段。
2. 用 `-O health_news.csv` 改为导出 CSV。
3. 给爬虫加 `custom_settings = {"DOWNLOAD_DELAY": 1}`，让请求间隔为 1 秒。

## 操作截图参考

![导出结果参考](Pasted%20image%2020260712150525.png)
