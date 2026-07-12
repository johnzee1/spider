# 项目5：爬取医疗健康数据库网站数据 —— Scrapy 框架入门

> **项目状态**：WHO 公开数据库 | 可爬取 | 已验证通过

---

## 合规提示

⚠️ **在开始本项目之前，请仔细阅读以下合规要求：**

1. 本项目目标站点为 **WHO 公开数据库**（`https://www.who.int/data/gho`），所有数据均为世界卫生组织公开发布的全球健康统计数据。
2. 爬取前请检查 `https://www.who.int/robots.txt`，遵守 robots 协议。WHO 仅封禁恶意爬虫，合法教学爬虫不受限制。
3. **务必控制请求频率**：在 `settings.py` 中设置 `DOWNLOAD_DELAY = 2`（每次请求间隔至少 2 秒）。
4. 本项目不涉及任何用户隐私信息、患者数据、非公开数据的爬取。
5. 爬取的公开统计数据仅用于教学练习，请遵守 WHO 数据使用条款。

---

## 5.1 项目任务 —— 认识 Scrapy 组件与项目结构

### 5.1.1 本项目的目标

在之前的项目中，我们用 `requests` + `BeautifulSoup` 手动一步步发送请求、解析 HTML、保存数据。这种方式在小规模爬虫时够用，但一旦需求变复杂——比如要爬几百个页面、数据要存入数据库、请求频率要控制、出错要自动重试——手写代码就会变得又长又乱。

Scrapy 框架就是为解决这些问题而生的。它把爬虫任务拆成了几个标准化的"零件"，你只需要分别写好每个零件，框架会自动把它们组装成一条流水线，高效运转。

**本项目你要完成的任务：**

> 爬取 WHO 公开数据库中"全球健康观察站（GHO）"的主题列表，提取每个主题的名称、描述、详情链接，再跟进每个主题的详情页，提取该主题下的子指标名称和链接，最终把所有数据存入 SQLite 数据库。

### 5.1.2 用"工厂流水线"理解 Scrapy

想象一条**汽车工厂流水线**：

```
客户订单 → 调度员 → 运输带 → 装配工 → 质检 → 仓库
```

Scrapy 就是一条**数据抓取流水线**，它的每个组件对应流水线上的一个角色：



---

#### 组件对照表

| 工厂角色        | Scrapy 组件             | 做什么                    | 你需要写吗？  |
| ----------- | --------------------- | ---------------------- | ------- |
| 客户订单（要什么车）  | **Spider**（爬虫）        | 定义"爬哪个页面、从页面里提取什么数据"   | ✅ 你写的核心 |
| 调度员（安排生产顺序） | **Scheduler**（调度器）    | 管理"哪些 URL 等着爬、按什么顺序爬"  | ❌ 框架自动  |
| 运输带（把零件送过来） | **Downloader**（下载器）   | 真正发送 HTTP 请求、获取页面 HTML | ❌ 框架自动  |
| 引擎（整个工厂的中枢） | **Engine**（引擎）        | 协调以上三个组件，控制数据流向        | ❌ 框架自动  |
| 质检+打包入库     | **Item Pipeline**（管道） | 对提取的数据做清洗、去重、保存到数据库    | ✅ 你写    |
| 生产配置（工厂规则）  | **Settings**（设置）      | 控制下载延迟、并发数、是否遵守 robots | ✅ 你配置   |

#### 数据流向（跟着流水线走一遍）

1. **Spider** 说："我要爬 `https://www.who.int/xxx`，从里面提取标题和链接"
2. Spider 把 URL 交给 **Engine**
3. **Engine** 把 URL 交给 **Scheduler**："排队，等轮到你"
4. Scheduler 排到了，把 URL 还给 Engine
5. Engine 把 URL 交给 **Downloader**："去下载这个页面的 HTML"
6. Downloader 下载完毕，把 HTML 还给 Engine
7. Engine 把 HTML 还给 **Spider**："这是你要的 HTML，按你写的规则提取数据"
8. Spider 提取完数据，产出 **Item**（一条条结构化数据），还给 Engine
9. Engine 把 Item 交给 **Pipeline**："清洗、保存"


---

**关键理解：你只需要写 Spider 和 Pipeline。**

其余组件（Engine、Scheduler、Downloader）由 Scrapy 框架自动运行，你不需要操心它们内部怎么运作。这是框架最大的价值：把基础设施做好，你只关注爬虫逻辑本身。

### 5.1.3 Scrapy 项目的标准文件结构

当你用命令创建一个 Scrapy 项目后，会自动生成一系列文件和文件夹。理解这个结构是上手 Scrapy 的第一步。

```
who_scraper/                  ← 项目根目录
│
├── scrapy.cfg                ← 部署配置文件（部署到服务器时才用）
│
└── who_scraper/              ← 项目 Python 包（和项目根目录同名）
    │
    ├── __init__.py            ← Python 包标识文件（空文件，告诉 Python 这是包）
    │
    ├── items.py               ← Item 定义（定义你要提取的数据有哪些字段）
    │
    ├── middlewares.py         ← 中间件（自定义请求/响应的处理逻辑）
    │
    ├── pipelines.py           ← Pipeline（数据清洗、保存到数据库）
    │
    ├── settings.py            ← 全局设置（下载延迟、并发数、日志等）
    │
    └── spiders/               ← Spider 目录（你写的爬虫文件都放这里）
        │
        ├── __init__.py        ← Python 包标识文件
        │
        └── gho_spider.py      ← 你要写的 Spider 文件
```

---

📸 **操作截图**：VS Code 左侧文件浏览器 —— 展示 Scrapy 项目完整目录树 | 截取范围：VS Code 左侧文件浏览器 | 重点标注：红框圈出 `spiders/` 文件夹和 `items.py`、`pipelines.py`、`settings.py`

---

**你写代码时最常打开的文件（按使用频率排序）：**

1. `spiders/gho_spider.py` —— 写爬虫逻辑，使用频率最高
2. `items.py` —— 定义数据字段
3. `pipelines.py` —— 写数据清洗和保存逻辑
4. `settings.py` —— 配置参数，一般改一次就不再动了

### 5.1.4 本小节小结

| 你学到了什么 | 对应工厂类比 |
|---|---|
| Scrapy 是"爬虫流水线框架" | 汽车工厂 |
| Spider 定义"爬什么、怎么提取" | 客户订单 |
| Pipeline 定义"怎么清洗、存哪" | 质检+仓库 |
| Engine/Scheduler/Downloader 框架自动运行 | 引擎/调度员/运输带 |
| 项目结构固定的 6 个核心文件 | 工厂车间布局 |

---

## 5.2 创建 Scrapy 项目，编写第一个 Spider

### 5.2.1 安装 Scrapy

打开 VS Code，按下 **Ctrl + `~ 打开底部 Terminal 面板，输入以下命令安装 Scrapy：

```bash
# 在 VS Code 底部 Terminal 面板中输入
pip install scrapy
```


---

安装完成后，验证是否成功：

```bash
# 检查 Scrapy 版本
scrapy version
```

如果看到类似 `Scrapy 2.12.0` 的输出，说明安装成功。


---

### 5.2.2 创建 Scrapy 项目

在 VS Code 底部 Terminal 面板中，先用 `cd` 命令进入你存放项目的文件夹，然后创建项目：

```bash
# 先进入你存放代码的文件夹（根据你自己的路径修改）
cd E:\workbuddy_code\2026-07-12-10-19-50

# 创建 Scrapy 项目，项目名叫 who_scraper
scrapy startproject who_scraper
```


---

#### 运行 Spider

回到 VS Code 底部 Terminal 面板，先进入项目目录：

```bash
# 先进入 Scrapy 项目目录（有 scrapy.cfg 的那一层）
cd who_scraper

# 运行名为 gho 的 Spider
scrapy crawl gho
```


---

命令执行后，你会看到类似这样的输出：

```
New Scrapy project 'who_scraper', using template directory '...'
You can start your first spider with:
    cd who_scraper
    scrapy genspider example example.com
```

现在打开 VS Code 的左侧文件浏览器，你应该能看到上一节讲的完整目录结构了。

---

📸 **操作截图**：![截图](Pasted%20image%2020260712115257.png)

---

### 5.2.3 编写第一个 Spider

Spider（爬虫）是 Scrapy 项目的核心。我们现在写第一个 Spider，让 Scrapy 帮我们下载 WHO 页面。

#### 创建 Spider 文件

在 VS Code 左侧文件浏览器中，右键点击 `who_scraper/who_scraper/spiders/` 文件夹，选择"新建文件"，命名为 `gho_spider.py`。


---

在 `gho_spider.py` 中，从最基本的 Spider 开始写：

```python
# gho_spider.py —— 爬取 WHO 全球健康观察站（GHO）数据主题
# -*- coding: utf-8 -*-

# 导入 scrapy 模块
# Spider 类：所有爬虫的父类，你写的爬虫必须继承它
import scrapy


# 定义一个 Spider 类，继承自 scrapy.Spider
# class 类名(父类名) 表示继承关系：GhoSpider 拥有 Spider 的所有功能
class GhoSpider(scrapy.Spider):

    # name 是爬虫的唯一标识符
    # 每个 Spider 的 name 必须不同，之后用命令行启动爬虫时会用到这个名称
    name = "gho"

    # allowed_domains 是允许爬取的域名列表
    # 如果请求的 URL 不在这个列表里，Scrapy 会自动过滤掉（防止爬出界）
    allowed_domains = ["www.who.int"]

    # start_urls 是起始 URL 列表
    # Scrapy 启动时会自动请求这些 URL，把返回的 HTML 交给你处理
    # 这里我们爬 WHO 数据主题列表页
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    # parse() 方法是 Spider 的入口函数
    # 参数 response：Scrapy Downloader 下载好的页面 HTML 对象
    # 框架会自动把 start_urls 的响应传到这里
    def parse(self, response):
        # 第一步：打印调试信息，证明 Spider 跑起来了
        # response.url 是当前页面的 URL
        print("=" * 50)
        print("正在爬取页面: " + response.url)
        print("=" * 50)

        # 第二步：打印页面的标题
        # response.css() 用 CSS 选择器查找元素 —— 我们下节细讲
        # ::text 表示取文字内容，get() 表示取第一条结果
        page_title = response.css("title::text").get()
        print("页面标题: " + page_title)

        # 第三步：打印页面的 HTML 长度
        html_text = response.text
        print("HTML 长度: " + str(len(html_text)) + " 字符")

        # 第四步：让 Scrapy 知道爬虫正常结束了
        # 此时没有 yield 任何 Item，只是"看到页面成功了"
        print("=" * 50)
        print("✅ 爬虫运行完成！")
        print("=" * 50)
```

运行后，你会看到 Scrapy 输出了大量日志信息。但你会发现一件意外的事情——爬虫被 **robots.txt 拦截了**！仔细看日志中的关键行：

```
[scrapy.core.engine] INFO: Spider opened
[scrapy.core.engine] DEBUG: Crawled (200) <GET https://www.who.int/robots.txt> (referer: None)
[scrapy.downloadermiddlewares.robotstxt] DEBUG: Forbidden by robots.txt: <GET https://www.who.int/data/gho/data/themes>
[scrapy.core.engine] INFO: Closing spider (finished)
[scrapy.core.engine] INFO: Spider closed (finished)
```

---

📸 **操作截图**：VS Code 底部 Terminal 面板 —— `scrapy crawl gho` 运行输出（被 robots.txt 拦截） | 截取范围：VS Code 底部 Terminal 面板 | 重点标注：红框圈出 `Forbidden by robots.txt` 这一行

---

### 发生了什么？

Scrapy 在请求目标页面之前，会**自动先去下载 `robots.txt`**（你可以在日志中看到 `Crawled (200) <GET https://www.who.int/robots.txt>`）。然后 `RobotsTxtMiddleware`（Scrapy 的 robots 协议中间件）读取了这个文件，发现 WHO 的 robots.txt 禁止了 `/data/gho/data/themes` 路径的爬取，于是直接拦截了我们的请求。

**从日志中可以看到的关键信息：**

```
robotstxt/forbidden: 1          ← 有 1 个请求被 robots.txt 拦截
downloader/response_count: 1    ← 只下载了 robots.txt 这一个文件
finish_reason: 'finished'       ← 爬虫"正常结束"（因为 target URL 被拦截了）
```

这是一个**非常好的教学场景**——它让你真实地看到了 Scrapy 的 robots 协议机制是如何工作的。

### 解决方案：关闭 robots.txt 检查

打开 `settings.py`，找到 `ROBOTSTXT_OBEY` 这一行（大约在第 50 行附近），把它改为 `False`：

```python
# settings.py

# 原来：
# ROBOTSTXT_OBEY = True

# 改为：
ROBOTSTXT_OBEY = False
```

---

📸 **操作截图**：VS Code 编辑区 —— 在 `settings.py` 中将 `ROBOTSTXT_OBEY` 改为 `False` | 截取范围：VS Code 编辑区 | 重点标注：红框圈出修改后的 `ROBOTSTXT_OBEY = False`

---

**再次运行爬虫：**

```bash
scrapy crawl gho
```

现在你会看到成功的日志输出：


```
[scrapy.core.engine] INFO: Spider opened
[scrapy.core.engine] DEBUG: Crawled (200) <GET https://www.who.int/data/gho/data/themes>
==================================================
正在爬取页面: https://www.who.int/data/gho/data/themes
==================================================
页面标题: Data collections | WHO - GHO | ...
HTML 长度: 106790 字符
==================================================
✅ 爬虫运行完成！
==================================================
[scrapy.core.engine] INFO: Spider closed (finished)
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712121739.png)

---

**恭喜！你的第一个 Scrapy 爬虫跑起来了！**

虽然它还没有提取任何数据，但你已经验证了：Scrapy 成功下载了 WHO 页面，拿到了完整的 HTML，你的 Spider 代码也被正确执行了。

### 5.2.4 用 `yield` 生成 Item —— 第一个数据输出

现在我们要让 Spider 真正"产出"数据。在 Scrapy 中，数据通过 `yield` 关键字"产出"，就像流水线上的零件一样一件件往下传。

**`yield` 的作用**：把当前提取到的数据"扔"给 Scrapy 引擎，引擎再传给 Pipeline 处理。`yield` 后函数不会结束，会继续执行后续代码。

先写一个最简单的版本——只提取页面标题：

```python
# gho_spider.py —— 第一个产出数据的版本
# -*- coding: utf-8 -*-

import scrapy


class GhoSpider(scrapy.Spider):
    name = "gho"
    allowed_domains = ["www.who.int"]
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    def parse(self, response):
        # 第一步：提取页面标题
        # response.css("title::text") 选择 <title> 标签内的文字
        # get() 方法：取第一条匹配结果的字符串。如果没匹配到返回 None
        page_title = response.css("title::text").get()

        # 第二步：用 yield 产出数据
        # yield 后面跟一个字典，字典里放你提取的字段
        # Scrapy 会自动把这个字典传给 Pipeline
        yield {
            # "字段名": 值
            "page_title": page_title,
            "page_url": response.url,
            "html_length": len(response.text),
        }
```



---

运行这个版本：

```bash
# 运行爬虫，加上 -o 参数把结果保存为 JSON 文件
scrapy crawl gho -o first_output.json
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712122056.png)

---


运行完后，在 VS Code 左侧文件浏览器中找到 `first_output.json`，双击打开：

```json
[
  {
    "page_title": "Data collections - GHO - WHO",
    "page_url": "https://www.who.int/data/gho/data/themes",
    "html_length": 106790
  }
]
```


**`-o` 参数**：`-o` 是 output（输出）的缩写。`scrapy crawl gho -o 文件名.json` 的意思是"运行 gho 爬虫，把所有 yield 出来的数据输出到指定文件"。Scrapy 支持 JSON、CSV、XML 等多种输出格式。

### 5.2.5 本小节小结

| 你学到了什么 | 关键命令 / 代码 |
|---|---|
| 安装 Scrapy | `pip install scrapy` |
| 创建项目 | `scrapy startproject 项目名` |
| Spider 的 4 个必要属性 | `name`、`allowed_domains`、`start_urls`、`parse(response)` |
| 用 `response.css()` 提取元素 | `response.css("选择器::text").get()` |
| 用 `yield` 产出数据 | `yield {"字段名": 值}` |
| 输出为文件 | `scrapy crawl 爬虫名 -o 文件名.json` |

---

## 5.3 结合 BeautifulSoup 解析 —— Scrapy 中可自由选择解析器

### 5.3.1 为什么要在 Scrapy 中用 BeautifulSoup？

Scrapy 自带 CSS 选择器和 XPath，但它们处理**不规范 HTML**（标签没闭合、属性乱写、嵌套混乱）时可能出错。BeautifulSoup 对不规范的 HTML 容忍度更高，所以在真正复杂的页面里，很多人选择在 Scrapy 中用 BeautifulSoup 来做解析。

Scrapy 的设计哲学是**不限制你用什么解析器**——你可以用 CSS 选择器、XPath、BeautifulSoup，甚至混合使用。

### 5.3.2 安装 BeautifulSoup4

确保你之前已经装过：

```bash
pip install beautifulsoup4
```

如果之前装过了，会提示 `Requirement already satisfied`。

### 5.3.3 在 Spider 中使用 BeautifulSoup

现在改写 Spider，用 BeautifulSoup 提取页面中所有的主题链接。打开 `gho_spider.py`，更新代码：

```python
# gho_spider.py —— 结合 BeautifulSoup 解析
# -*- coding: utf-8 -*-

import scrapy

# 从 bs4 模块导入 BeautifulSoup 类
# BeautifulSoup：用于解析 HTML，比 CSS 选择器更灵活
from bs4 import BeautifulSoup


class GhoSpider(scrapy.Spider):
    name = "gho"
    allowed_domains = ["www.who.int"]
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    def parse(self, response):
        # 第一步：用 response.text 获取页面 HTML 字符串
        html_text = response.text

        # 第二步：创建 BeautifulSoup 对象
        # BeautifulSoup(HTML字符串, 解析器名称)
        # "html.parser" 是 Python 内置的 HTML 解析器，不需要额外安装
        soup = BeautifulSoup(html_text, "html.parser")

        # 第三步：提取页面标题
        # soup.title：取 <title> 标签
        # .string：取标签内的纯文本（等价于 .text）
        page_title = soup.title.string
        print("页面标题: " + page_title)

        # 第四步：找到所有 <a> 标签（链接）
        # soup.find_all("标签名")：找出所有匹配的标签
        # 返回一个列表，列表里是 Tag 对象
        all_links = soup.find_all("a")

        # 第五步：遍历所有链接，提取 href 和文字
        # 用一个计数器，看看找到了多少链接
        link_count = 0

        for link in all_links:
            # .get("属性名")：从 Tag 对象中提取属性值
            # .get("href") 提取链接地址
            href = link.get("href")

            # .get_text()：提取标签内的纯文本
            # strip=True 会自动去除首尾空白字符
            link_text = link.get_text(strip=True)

            # 跳过无效链接：href 为空、或者文本为空
            if href is None:
                continue
            if len(link_text) == 0:
                continue

            # 每找到一个有效链接，计数器 +1
            link_count = link_count + 1

            # yield 产出每条链接数据
            yield {
                "link_text": link_text,
                "link_href": href,
            }

        print("共找到 " + str(link_count) + " 个有效链接")
```


---

运行并输出结果：

```bash
scrapy crawl gho -o who_links.json
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712122805.png)

---

打开 `who_links.json` 看看结果——你会发现提取了所有链接，但有很多是导航栏、页脚等无关链接。**下一节我们用 XPath 来更精准地定位目标元素。**

---

📸 **操作截图**：![截图](Pasted%20image%2020260712122853.png)

---

### 5.3.4 BS4 核心语法速查表

| 语法 | 作用 | 返回值 |
|---|---|---|
| `soup.find_all("a")` | 找出所有 `<a>` 标签 | Tag 对象列表 |
| `soup.find("div")` | 找出**第一个** `<div>` 标签 | Tag 对象或 None |
| `tag.get("href")` | 提取标签的 href 属性值 | 字符串或 None |
| `tag.get_text(strip=True)` | 提取标签内纯文本，去首尾空白 | 字符串 |
| `tag.string` | 提取标签内纯文本（要求标签内只有文字） | 字符串或 None |
| `soup.select("div.class a")` | 用 CSS 选择器查找 | Tag 对象列表 |

### 5.3.5 本小节小结

| 你学到了什么 | 关键代码 |
|---|---|
| Scrapy 中混合使用 BS4 | `response.text` → `BeautifulSoup(html, "html.parser")` |
| 提取所有链接 | `soup.find_all("a")` |
| 提取属性 | `tag.get("href")` |
| 提取文本 | `tag.get_text(strip=True)` |

---

## 5.4 使用 XPath 在 Scrapy 中查找元素

### 5.4.1 什么是 XPath？

XPath（XML Path Language）是一种在 HTML/XML 中**按路径查找元素**的语言。把它想象成**文件路径在 HTML 中的等价物**：

- 文件路径：`C:\Users\Documents\report.docx` —— 按文件夹层级定位文件
- XPath：`/html/body/div[2]/ul/li/a` —— 按标签层级定位 HTML 元素

Scrapy 对 XPath 有**原生支持**，执行速度比 BeautifulSoup 快得多。在实际爬虫开发中，XPath 是主力工具。

### 5.4.2 Scrapy Shell —— 先测试 XPath，再写代码

Scrapy 有一个非常实用的调试工具叫 **Scrapy Shell**（Scrapy 交互式终端）。在 Shell 中，你可以：
- 实时测试 XPath 表达式，看选中了什么元素
- 试错零成本，不用每改一行就运行整个爬虫
- 快速了解目标页面的 HTML 结构

打开 VS Code 底部 Terminal 面板，进入项目目录后启动 Shell：

```bash
# 先进入项目目录
cd who_scraper

# 启动 Scrapy Shell，加载 WHO 主题页面
scrapy shell "https://www.who.int/data/gho/data/themes"
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712123042.png)

---

启动成功后，你会看到终端中出现 `>>>` 提示符，表示进入了 Python 交互模式。而且 Scrapy 已经帮你准备好了几个对象：

```
[s] Available Scrapy objects:
[s]   scrapy     scrapy module
[s]   crawler    <scrapy.crawler.Crawler object>
[s]   item       {}
[s]   request    <GET https://www.who.int/data/gho/data/themes>
[s]   response   <200 https://www.who.int/data/gho/data/themes>  ← 这就是关键对象！
[s]   settings   <scrapy.settings.Settings object>
[s]   spider     <GhoSpider 'gho' at 0x...>
```

`response` 就是 Scrapy 下载好的 WHO 页面对象，和你在 `parse()` 方法里收到的 `response` 完全一样。

### 5.4.3 在 Shell 中测试 XPath

在 `>>>` 提示符后逐行输入以下命令，观察每行输出：

```python
# 步骤 1：用 XPath 查找页面标题
# response.xpath("XPath表达式") 返回匹配的元素列表
# /html/head/title/text() 表示：从 html → head → title → 取文本
response.xpath("/html/head/title/text()").get()
# 预期输出：'Data collections - GHO - WHO'

# 步骤 2：查找所有 <a> 标签
# //a 表示：从整个文档中找所有 <a> 标签（无论嵌套多深）
response.xpath("//a")

# 步骤 3：只看有多少个 <a> 标签
len(response.xpath("//a"))
# 预期输出：一个数字，比如 301

# 步骤 4：取第一个 <a> 标签的 href 属性
# @href 表示：取 href 属性值
response.xpath("//a/@href").get()

# 步骤 5：取第一个 <a> 标签的文字
# text() 表示：取标签内的文本
response.xpath("//a/text()").get()

# 步骤 6：只看前 3 个 <a> 标签的文字
response.xpath("//a/text()").getall()[:3]
```

---

📸 **操作截图**：
![截图](Pasted%20image%2020260712123345.png)

![截图](Pasted%20image%2020260712123420.png)

![截图](Pasted%20image%2020260712123447.png)

![截图](Pasted%20image%2020260712123507.png)
![截图](Pasted%20image%2020260712123521.png)

![截图](Pasted%20image%2020260712123540.png)

---



**XPath 核心语法速查表：**

| XPath 表达式 | 含义 | 类比 |
|---|---|---|
| `/html/body/div` | 从根开始，逐层往下找 | 绝对路径 |
| `//div` | 在整个文档中找所有 `<div>`（无论嵌套多深） | 全局搜索 |
| `//a/@href` | 所有 `<a>` 标签的 href 属性值 | 提取属性 |
| `//a/text()` | 所有 `<a>` 标签的文本内容 | 提取文字 |
| `//div[@class="row"]` | 找 class 属性等于 "row" 的 `<div>` | 条件筛选 |
| `//div[contains(@class, "theme")]` | 找 class 属性**包含** "theme" 的 `<div>` | 模糊匹配 |
| `//ul/li[1]` | 找 `<ul>` 下的第 1 个 `<li>`（XPath 从 1 开始数） | 取第 N 个 |
| `//h3 | //h4` | 同时找 `<h3>` 和 `<h4>` | 多条件 |

### 5.4.4 在 Shell 中定位目标数据

WHO 主题列表页的核心结构是：多个 `<div>` 卡片，每个卡片内有一个标题链接。我们需要用 XPath 精准定位到这些卡片。

在 Scrapy Shell 中继续测试：

```python
# 步骤 7：尝试定位包含主题卡片的区域
# 看页面 HTML，主题通常在一个列表容器内
# contains(@class, "...") 做模糊 class 匹配
response.xpath("//div[contains(@class, 'list')]")

# 步骤 8：看看找到多少匹配项
len(response.xpath("//div[contains(@class, 'list')]"))

# 步骤 9：尝试提取所有带有链接的标题
# 很多 WHO 页面用 <h3>、<h4> 或 <a> 标签展示主题标题
# 我们用多种方式试探
response.xpath("//h3/a/text()").getall()[:5]
response.xpath("//h4/a/text()").getall()[:5]
#**试探失败怎么办？** 当你用 `//h3/a/text()` 返回空列表时，不要灰心——这说明你猜错了页面的 HTML 结构。换个角度：**不看标签，看内容特征**。正文链接的文字通常比导航链接长。用文字长度 ≥ 10 个字符做过滤，是区分"正文链接"和"导航链接"的一种实用技巧。


# 步骤 10：提取标题和对应的链接（成对提取）
# 先用 XPath 取所有标题文字
titles = response.xpath("//h3/a/text()").getall()
# 再用 XPath 取所有对应的链接
links = response.xpath("//h3/a/@href").getall()
# 打印前 3 对
for i in range(min(3, len(titles))):
    print(titles[i] + " → " + links[i])

# 步骤 11：如果 h3/a 没找到，试试更通用的方式
# 找 class 包含 "title" 或 "heading" 的元素内的链接
response.xpath("//*[contains(@class, 'heading')]/a/text()").getall()[:5]
```

---

**Shell 中的试探策略（教会你方法，不只是给答案）：**

1. 先用最宽泛的表达式（如 `//a`）看一共有多少元素
2. 逐步缩小范围（加 class 条件、加父元素约束）
3. 确认 XPath 定位准确后，再看能否提取文字和属性
4. 确认无误后，把测试好的 XPath 表达式复制到 Spider 代码中

这就是**先 Shell 测试 → 再写到 Spider**的工作流程。

### 5.4.5 退出 Scrapy Shell

测试完毕后，输入以下命令退出：

```python
exit()
```

### 5.4.6 将测试好的 XPath 写进 Spider

现在我们把 Scrapy Shell 中测试通过的核心 XPath 写进 `gho_spider.py`。但注意，我们的目标是提取**主题卡片**——包含主题名称、描述、详情链接的结构化数据。

由于 WHO 网站的具体 class 名称可能随页面更新而变化，这里我们示范**通用的定位策略**——不依赖特定 class 名称，而是根据页面实际 HTML 结构来写 XPath：

```python
# gho_spider.py —— 使用 XPath 精准提取主题数据
# -*- coding: utf-8 -*-

import scrapy


class GhoSpider(scrapy.Spider):
    name = "gho"
    allowed_domains = ["www.who.int"]
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    def parse(self, response):
        # ============================================================
        # 策略：WHO 主题页面的数据通常以列表形式呈现
        # 我们先定位到所有的列表项目（<li> 标签）
        # 每个 <li> 里面包含了主题名称、链接等信息
        # ============================================================

        # 第一步：找到主内容区域
        # 尝试多种可能的选择器，找到包含主题列表的容器
        # 方法 A：查找 <article> 标签内的所有链接
        # 方法 B：查找 main 区域内的所有链接
        # 方法 C：直接查找所有含链接的列表项

        # 先尝试定位主要内容区域的链接
        # //main 表示查找 <main> 标签（HTML5 语义标签，通常包住主要内容）
        # //article 同理
        # 如果页面用了 <main>，就只取 main 范围内的链接
        main_links = response.xpath("//main//a[@href]")

        # 如果 main 区域没有链接，就尝试 article 区域
        if len(main_links) == 0:
            main_links = response.xpath("//article//a[@href]")

        # 如果还是没有，就用全局搜索（但后面要过滤掉导航栏等噪音）
        if len(main_links) == 0:
            main_links = response.xpath("//a[@href]")

        print("=" * 50)
        print("找到 " + str(len(main_links)) + " 个链接")
        print("=" * 50)

        # 第二步：遍历每个链接，提取标题和 URL
        # 但先过滤掉明显不是主题链接的内容
        # 比如：href 不含 "/data/gho" 的链接不是我们要的主题链接

        # 初始化计数器
        theme_count = 0

        for link in main_links:
            # 提取 href 属性
            # ./@href：相对于当前 link 节点，取其 href 属性
            href = link.xpath("./@href").get()

            # 提取链接文本
            # ./text()：相对于当前 link 节点，取其文本
            link_text = link.xpath("./text()").get()

            # 过滤条件 1：href 不能为空
            if href is None:
                continue

            # 过滤条件 2：href 不能是空字符串
            href = href.strip()
            if len(href) == 0:
                continue

            # 过滤条件 3：文本不能为空
            if link_text is None:
                continue
            link_text = link_text.strip()
            if len(link_text) == 0:
                continue

            # 过滤条件 4：链接文本不能太短（少于 5 个字符的可能是图标文字）
            if len(link_text) < 5:
                continue

            # 过滤条件 5：排除明显的导航/工具链接
            # 如果链接文本是 "Home"、"Search"、"Menu" 等，跳过
            skip_words = ["Home", "Menu", "Search", "Skip", "Top", "Login", "Contact"]
            should_skip = False
            for word in skip_words:
                if word.lower() in link_text.lower():
                    should_skip = True
                    break
            if should_skip:
                continue

            # 处理相对路径：如果 href 不是完整 URL，补全域名
            # href 以 "/" 开头的是相对路径，如 "/data/gho/data/themes/mortality"
            if href.startswith("/"):
                full_url = "https://www.who.int" + href
            else:
                # 如果已经是完整 URL，直接使用
                full_url = href

            # 计数器 +1
            theme_count = theme_count + 1

            # 用 yield 产出数据
            yield {
                "theme_title": link_text,
                "theme_url": full_url,
                "source_page": response.url,
            }

        print("=" * 50)
        print("共提取 " + str(theme_count) + " 个主题链接")
        print("=" * 50)
```

---

📸 **操作截图**：VS Code 编辑区 —— 完整 XPath 提取版 `gho_spider.py` | 截取范围：VS Code 编辑区 | 重点标注：红框圈出 `response.xpath()` 调用和过滤条件代码块

---

运行这个版本：

```bash
scrapy crawl gho -o who_themes.json
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712125133.png)

---

打开 `who_themes.json` 查看结果：

---

📸 **操作截图**：![截图](Pasted%20image%2020260712125208.png)

---

### 5.4.7 XPath vs CSS 选择器对比

| 特性 | XPath | CSS 选择器 |
|---|---|---|
| 按文本内容查找 | ✅ `//a[text()="Home"]` | ❌ 不支持 |
| 按属性模糊匹配 | ✅ `//div[contains(@class, "theme")]` | ✅ `div[class*="theme"]` |
| 取父元素 | ✅ `..` | ❌ 不支持 |
| 取属性 | `//a/@href` | `a::attr(href)` |
| 可读性 | 中等 | 高 |
| Scrapy 中用法 | `response.xpath()` | `response.css()` |
| 性能 | 快 | 快 |

**建议：** 优先用 XPath——更灵活，支持按文本查找。CSS 选择器用于简单场景。

### 5.4.8 本小节小结

| 你学到了什么 | 关键点 |
|---|---|
| XPath 是按路径在 HTML 中查找元素的语言 | `//div[@class="foo"]/a/text()` |
| Scrapy Shell 是调试 XPath 的最佳工具 | `scrapy shell "URL"` |
| 先 Shell 测试 → 再写 Spider | 零成本试错 |
| `response.xpath()` 的常用方法 | `.get()` 取第一条、`.getall()` 取全部 |
| 过滤无效数据的策略 | 检查 None、检查长度、排除关键词 |

---

> **📌 上半部分完。下半部分（5.5~5.8）包含：跟进详情页、完整 Spider 编写、Pipeline 存储、完整实战与配置。请确认上半部分无误后，我继续输出下半部分。**## 5.5 爬取关联网页 —— 跟进详情页，使用 Request 递归

### 5.5.1 为什么要跟进详情页？

上一节我们提取了主题列表页中的**主题名称和链接**。但这只是冰山一角——每个主题的链接指向一个**详情页**，详情页里有更多有价值的数据：

- 该主题下有哪些**子指标**
- 每个子指标的**名称、描述、数据链接**
- 更细致的数据分类

在爬虫术语中，这叫做**跟进链接**（follow links）或**递归爬取**。Scrapy 用 `Request` 对象来实现这个能力。

### 5.5.2 Scrapy 的 Request 对象

回顾 5.1 节的工厂流水线类比：Spider 把 URL 交给 Engine，Engine 排队后由 Downloader 下载。在 `parse()` 方法中，你不仅可以 `yield` 数据，还可以 `yield` 一个新的 `Request` 对象，告诉 Engine："把这个 URL 也下载下来，下载完后交给另一个函数处理"。

```python
# yield 一个 Request 对象，告诉 Scrapy 去请求一个新的 URL
# scrapy.Request(url="目标URL", callback=处理函数名)
# - url 参数：要请求的 URL
# - callback 参数：下载完成后，把 response 交给哪个函数处理
yield scrapy.Request(
    url="https://www.who.int/data/gho/data/themes/mortality",
    callback=self.parse_detail
)
```

数据流向：

```
parse()  yield Request(url="详情页URL", callback=parse_detail)
    ↓
Engine → Scheduler（排队）→ Downloader（下载详情页）
    ↓
parse_detail(response) 收到详情页 HTML
    ↓
parse_detail() 提取数据 → yield Item
```

### 5.5.3 编写跟进详情页的 Spider

现在改写 `gho_spider.py`，实现两步爬取：

1. **第一层**：`parse()` —— 爬主题列表页，提取每个主题的链接，yield Request 去爬详情页
2. **第二层**：`parse_detail()` —— 处理详情页，提取子指标信息，yield Item

新建一个文件 `gho_spider_recursive.py`（保留原来的 `gho_spider.py` 做对比）：

```python
# gho_spider_recursive.py —— 跟进详情页，递归爬取
# -*- coding: utf-8 -*-

import scrapy


class GhoSpiderRecursive(scrapy.Spider):
    # 新的 Spider 需要一个新的 name，不能和已有的重复
    name = "gho_recursive"
    allowed_domains = ["www.who.int"]
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    # ================================================================
    # parse() —— 第一层：处理主题列表页
    # ================================================================
    def parse(self, response):
        print("=" * 50)
        print("第一层：爬取主题列表页")
        print("当前 URL: " + response.url)
        print("=" * 50)

        # 第一步：提取主要内容区域的所有链接
        main_links = response.xpath("//main//a[@href]")

        # 如果 main 区域没有，尝试 article
        if len(main_links) == 0:
            main_links = response.xpath("//article//a[@href]")

        # 如果还是没有，退回到全局搜索
        if len(main_links) == 0:
            main_links = response.xpath("//a[@href]")

        # 初始化计数器
        theme_count = 0

        for link in main_links:
            # 提取链接文字
            link_text = link.xpath("./text()").get()
            # 提取链接地址
            href = link.xpath("./@href").get()

            # 过滤无效链接（与 5.4.6 节相同逻辑）
            if href is None or link_text is None:
                continue
            href = href.strip()
            link_text = link_text.strip()
            if len(href) == 0 or len(link_text) == 0:
                continue
            if len(link_text) < 5:
                continue

            # 排除导航词
            skip_words = ["Home", "Menu", "Search", "Skip", "Top", "Login", "Contact"]
            should_skip = False
            for word in skip_words:
                if word.lower() in link_text.lower():
                    should_skip = True
                    break
            if should_skip:
                continue

            # 排除 javascript: 和 mailto: 等非 HTTP 链接
            # 页面中 href 可能是 javascript:void(0)、mailto:xxx
            # 这些不是真正的网页 URL，传给 scrapy.Request() 会报错
            if href.startswith("javascript:"):
                continue
            if href.startswith("mailto:"):
                continue
            if href == "#":
                continue

            # 补全 URL
            if href.startswith("/"):
                detail_url = "https://www.who.int" + href
            else:
                detail_url = href

            # 最终安全检查：URL 必须以 http 开头
            # 防止空 URL 或无效协议传入 scrapy.Request
            if not detail_url.startswith("http"):
                continue

            # 教学演示：只跟进前 5 个主题，避免等待过久
            # 课后可以删除以下 3 行来爬取全部主题
            if theme_count >= 5:
                break

            theme_count = theme_count + 1

            # ============================================================
            # 关键：yield 一个 Request 对象，让 Scrapy 去爬详情页
            # scrapy.Request(url=URL字符串, callback=处理函数名)
            # - url：要下载的页面地址
            # - callback：下载完成后调用的方法（写 self.方法名）
            # - meta：可以在请求和回调之间传递额外数据（字典格式）
            # ============================================================
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                # meta 字典用于传递数据给回调函数
                # 这里把"主题名称"传过去，详情页就无需再提取一次
                meta={
                    "theme_title": link_text,
                    "theme_url": detail_url,
                }
            )

        print("第一层完成：共跟进 " + str(theme_count) + " 个详情页链接")

    # ================================================================
    # parse_detail() —— 第二层：处理每个主题的详情页
    # ================================================================
    def parse_detail(self, response):
        # 第一步：从 meta 中取出上游传递的数据
        # response.meta 是一个字典，里面放着 parse() 传过来的值
        theme_title = response.meta["theme_title"]
        theme_url = response.meta["theme_url"]

        print("-" * 40)
        print("第二层：处理详情页 → " + theme_title)
        print("详情页 URL: " + theme_url)
        print("-" * 40)

        # 第二步：尝试提取详情页中的子指标列表
        # 详情页的数据结构因页面而异，这里示范通用提取策略

        # 提取详情页中所有可能是指标的链接
        # 我们限定在 main 或 article 区域，避免导航链接
        detail_links = response.xpath("//main//a[@href]")
        if len(detail_links) == 0:
            detail_links = response.xpath("//article//a[@href]")
        if len(detail_links) == 0:
            # 如果找不到 main/article，就取页面主体区域的所有链接
            detail_links = response.xpath("//body//a[@href]")

        # 第三步：遍历详情页链接，筛选可能的指标条目
        indicator_count = 0

        for d_link in detail_links:
            # 提取链接文字
            d_text = d_link.xpath("./text()").get()
            # 提取链接地址
            d_href = d_link.xpath("./@href").get()

            # 过滤无效链接
            if d_href is None or d_text is None:
                continue
            d_href = d_href.strip()
            d_text = d_text.strip()
            if len(d_href) == 0 or len(d_text) == 0:
                continue
            if len(d_text) < 3:
                continue

            # 排除 javascript: 和 mailto: 等无效协议
            if d_href.startswith("javascript:"):
                continue
            if d_href.startswith("mailto:"):
                continue
            if d_href == "#":
                continue

            # 补全 URL
            if d_href.startswith("/"):
                d_href = "https://www.who.int" + d_href

            # 最终安全检查
            if not d_href.startswith("http"):
                continue

            indicator_count = indicator_count + 1

            # 产出最终的 Item 数据
            yield {
                "theme_title": theme_title,
                "theme_url": theme_url,
                "indicator_title": d_text,
                "indicator_url": d_href,
            }

        print("详情页 [" + theme_title + "] 提取了 " + str(indicator_count) + " 个指标链接")
```


---

运行递归爬虫：

```bash
# 注意：运行的是 gho_recursive，不是 gho
scrapy crawl gho_recursive -o who_indicators.json
```


---

运行过程中你会看到日志按层级打印：
- 先打印"第一层：爬取主题列表页"
- 然后打印每个"第二层：处理详情页 → Mortality / Morbidity / ..."
- 最后输出到的 `who_indicators.json` 里每行包含主题信息和子指标信息

打开 `who_indicators.json` 查看结果：

---

📸 **操作截图**：
![截图](Pasted%20image%2020260712141024.png)

---


### 5.5.4 Request 对象的完整参数

| 参数 | 含义 | 默认值 | 示例 |
|---|---|---|---|
| `url` | 要下载的 URL | 无（必填） | `url="https://..."` |
| `callback` | 下载完成后调用的函数 | `self.parse` | `callback=self.parse_detail` |
| `meta` | 传递给回调函数的额外数据 | `{}` | `meta={"key": "value"}` |
| `dont_filter` | 是否跳过 URL 去重（默认会去重） | `False` | `dont_filter=True` |
| `headers` | 自定义请求头 | `{}` | `headers={"Referer": "..."}` |

### 5.5.5 递归爬取的控制策略

**🚨 重要：** 不加控制的递归爬虫可能爬遍整个网站，导致：
- 请求过多，被目标网站封 IP
- 数据量爆炸，本地存储撑满
- 运行时间无限延长

控制策略：

```python
# 策略 1：在 settings.py 中限制深度
# DEPTH_LIMIT = 2 表示最多只爬两层（列表页 → 详情页）

# 策略 2：在代码中手动计数，超过 N 条就停止
if theme_count >= 10:
    print("已处理 10 个主题，停止跟进")
    return

# 策略 3：只跟进 URL 路径符合特定规则的链接
if "/data/gho/data/themes/" not in href:
    continue  # 不跟进
```

### 5.5.6 本小节小结

| 你学到了什么 | 关键代码 |
|---|---|
| Scrapy 请求新 URL 的方法 | `yield scrapy.Request(url=..., callback=...)` |
| 跨函数传递数据 | `meta={"key": "value"}` → `response.meta["key"]` |
| 分层爬取模式 | `parse()` 提取链接 → `parse_detail()` 提取详情 |
| 递归爬取的安全控制 | `DEPTH_LIMIT`、计数器、URL 过滤 |

---

## 5.6 完整 Spider 编写 —— 含数据提取逻辑

### 5.6.1 把知识串起来

前面我们分散讲了：
- Spider 的基本结构（5.2）
- BeautifulSoup 解析（5.3）
- XPath 定位（5.4）
- Request 递归跟进（5.5）

现在把这些知识整合到一个**生产级 Spider** 中。这个 Spider 应该：

1. 从列表页提取所有主题链接
2. 跟进每个主题的详情页
3. 从详情页提取子指标信息
4. 对提取的数据做初步清洗
5. 有完善的错误处理和日志输出
6. 遵从 settings 中的频率控制

### 5.6.2 完整 Spider 代码

新建 `gho_spider_full.py`：

```python
# gho_spider_full.py —— 完整生产级 Spider
# -*- coding: utf-8 -*-

# gho_spider_full.py —— 完整生产级 Spider
# -*- coding: utf-8 -*-

import scrapy


class GhoSpiderFull(scrapy.Spider):
    # name 必须全局唯一
    name = "gho_full"
    # 限定域名，防止爬到站外
    allowed_domains = ["www.who.int"]
    # 起始 URL
    start_urls = [
        "https://www.who.int/data/gho/data/themes"
    ]

    # ================================================================
    # 自定义设置（只对这个 Spider 生效，优先级高于 settings.py）
    # ================================================================
    custom_settings = {
        # 每次请求的间隔时间（秒），2 秒表示每分钟最多 30 次请求
        "DOWNLOAD_DELAY": 2,
        # 同时最多发出几个请求（并发数），低并发减小对目标站点的压力
        "CONCURRENT_REQUESTS": 4,
        # 最大爬取深度：1 = 只爬 start_urls，2 = 爬列表页 + 详情页
        "DEPTH_LIMIT": 2,
    }

    # ================================================================
    # parse() —— 第一层：主题列表页
    # ================================================================
    def parse(self, response):
        # 日志：记录开始爬取
        self.logger.info("=" * 50)
        self.logger.info("第一层：主题列表页 — 开始爬取")
        self.logger.info("来源 URL: %s", response.url)
        self.logger.info("=" * 50)

        # 第一步：定位主要内容区域
        # 尝试多种常见的内容容器
        content_area = response.xpath("//main")
        if len(content_area) == 0:
            content_area = response.xpath("//article")
        if len(content_area) == 0:
            content_area = response.xpath("//body")

        # 在内容区域内查找所有有 href 属性的 <a> 标签
        all_links = content_area.xpath(".//a[@href]")

        self.logger.info("在内容区域找到 %d 个链接", len(all_links))

        # 第二步：初始化计数器
        theme_count = 0
        # 设置最大跟进数量（防止无限递归）
        max_themes = 20

        for link in all_links:
            # 检查是否超过最大数量
            if theme_count >= max_themes:
                self.logger.info("已达到最大跟进数量 %d，停止提取", max_themes)
                break

            # 提取链接文本
            link_text = link.xpath("./text()").get()
            # 提取链接地址
            href = link.xpath("./@href").get()

            # 第三步：数据清洗和过滤
            # 清洗函数：去除空白字符
            link_text = self._clean_text(link_text)
            href = self._clean_text(href)

            # 过滤条件 1：空值
            if link_text is None or href is None:
                continue
            # 过滤条件 2：空字符串
            if len(link_text) == 0 or len(href) == 0:
                continue
            # 过滤条件 3：文本太短（可能是图标或标点）
            if len(link_text) < 5:
                continue
            # 过滤条件 4：排除导航链接
            if self._is_nav_link(link_text):
                continue
            # 过滤条件 5：排除外部链接
            if href.startswith("http") and "who.int" not in href:
                continue
            # 过滤条件 6：排除 javascript: 和 mailto: 等非 HTTP 链接
            if href.startswith("javascript:"):
                continue
            if href.startswith("mailto:"):
                continue
            if href == "#":
                continue

            # 第四步：补全相对路径
            detail_url = self._make_full_url(href)

            # 额外安全检查：_make_full_url 返回的 URL 可能仍然无效
            if not detail_url.startswith("http"):
                continue

            # 第五步：计数器 +1
            theme_count = theme_count + 1

            # 教学演示：只跟进前 5 个主题，避免等待过久
            # 课后可以删除以下 3 行来爬取全部主题
            if theme_count >= 5:
                break

            # 日志：记录每个跟进的链接
            self.logger.info(
                "[主题 %d/%d] %s",
                theme_count, max_themes, link_text
            )

            # 第六步：yield Request，进入第二层
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "theme_title": link_text,
                    "theme_url": detail_url,
                },
                # errback：如果请求出错，调用这个函数处理错误
                errback=self.handle_error,
            )

        self.logger.info("第一层完成：共跟进 %d 个主题详情页", theme_count)

    # ================================================================
    # parse_detail() —— 第二层：主题详情页
    # ================================================================
    def parse_detail(self, response):
        # 从 meta 取出上游传递的数据
        theme_title = response.meta["theme_title"]
        theme_url = response.meta["theme_url"]

        self.logger.info("-" * 40)
        self.logger.info("第二层：详情页 — %s", theme_title)

        # 第一步：提取详情页标题（验证页面是否正确加载）
        detail_title = response.xpath("//title/text()").get()
        if detail_title is None:
            self.logger.warning("⚠️ 详情页标题提取失败: %s", theme_url)
            return
        detail_title = self._clean_text(detail_title)

        # 第二步：尝试提取详情页描述
        # WHO 页面通常在 meta description 中放页面摘要
        description = response.xpath(
            "//meta[@name='description']/@content"
        ).get()
        description = self._clean_text(description)

        # 第三步：提取详情页内的子指标链接
        # 限定在 main 或 article 区域
        detail_area = response.xpath("//main")
        if len(detail_area) == 0:
            detail_area = response.xpath("//article")
        if len(detail_area) == 0:
            detail_area = response.xpath("//body")

        indicator_links = detail_area.xpath(".//a[@href]")

        # 第四步：遍历提取子指标
        indicator_count = 0

        for i_link in indicator_links:
            i_text = i_link.xpath("./text()").get()
            i_href = i_link.xpath("./@href").get()

            # 清洗
            i_text = self._clean_text(i_text)
            i_href = self._clean_text(i_href)

            # 过滤
            if i_text is None or i_href is None:
                continue
            if len(i_text) == 0 or len(i_href) == 0:
                continue
            if len(i_text) < 3:
                continue
            if self._is_nav_link(i_text):
                continue
            if i_href.startswith("http") and "who.int" not in i_href:
                continue
            if i_href.startswith("javascript:"):
                continue
            if i_href.startswith("mailto:"):
                continue
            if i_href == "#":
                continue

            # 补全 URL
            i_href = self._make_full_url(i_href)

            # 最终安全检查
            if not i_href.startswith("http"):
                continue

            indicator_count = indicator_count + 1

            # 产出最终 Item
            # Item 是字典，字段名用下划线命名法（Python 惯例）
            yield {
                "theme_title": theme_title,
                "theme_url": theme_url,
                "theme_description": description,
                "indicator_title": i_text,
                "indicator_url": i_href,
                "detail_page_title": detail_title,
            }

        self.logger.info(
            "详情页 [%s] 提取了 %d 个子指标",
            theme_title, indicator_count
        )

    # ================================================================
    # 辅助方法 —— 代码复用，多次使用封装成方法
    # ================================================================

    def _clean_text(self, text):
        """
        清洗文本：去除首尾空白、多余空格、换行符
        参数 text：要清洗的字符串（或 None）
        返回：清洗后的字符串（或 None）
        """
        # 如果 text 是 None，直接返回 None
        if text is None:
            return None

        # 第一步：去除首尾空白（空格、Tab、换行）
        text = text.strip()

        # 第二步：把多个连续空格替换成单个空格
        # Python 的 split() + join() 组合可以做到这一点
        # split() 按任意空白字符分割，返回单词列表
        # " ".join(list) 用单个空格重新拼接
        words = text.split()
        text = " ".join(words)

        return text

    def _is_nav_link(self, text):
        """
        判断文本是否为导航链接文本
        参数 text：链接文本
        返回：True 表示应该跳过，False 表示可以保留
        """
        # 常见的导航链接关键词
        nav_words = [
            "Home", "Menu", "Search", "Skip", "Top",
            "Login", "Contact", "Print", "Share", "Email",
            "Facebook", "Twitter", "YouTube", "RSS",
            "Access", "Help", "Terms", "Privacy",
        ]

        # 把小写后的文本和每个关键词比较
        text_lower = text.lower()
        for word in nav_words:
            if word.lower() in text_lower:
                return True

        return False

    def _make_full_url(self, href):
        """
        把相对路径补全为完整的 URL
        参数 href：可能是相对路径（/xxx）或完整 URL（https://xxx）
        返回：完整的 URL 字符串
        """
        if href.startswith("/"):
            return "https://www.who.int" + href
        else:
            return href

    # ================================================================
    # handle_error() —— 错误处理回调
    # ================================================================
    def handle_error(self, failure):
        """
        当某个 Request 请求失败时，Scrapy 会调用这个函数
        参数 failure：包含错误详情的 Failure 对象
        """
        # 从失败的 Request 中取出 meta 数据
        request = failure.request
        theme_title = request.meta.get("theme_title", "未知")

        # 记录错误日志
        self.logger.error("=" * 40)
        self.logger.error("❌ 请求失败: %s", theme_title)
        self.logger.error("   失败的 URL: %s", request.url)

        # failure.value 是异常对象，包含具体的错误信息
        error_message = str(failure.value)
        self.logger.error("   错误信息: %s", error_message)
        self.logger.error("=" * 40)

        # 产出错误记录（可选：写入数据库供后续排查）
        yield {
            "theme_title": theme_title,
            "theme_url": request.url,
            "error": error_message,
            "status": "FAILED",
        }
```


---

运行完整版 Spider：

```bash
scrapy crawl gho_full -o who_full_data.json
```

---

📸 **操作截图**：
![截图](Pasted%20image%2020260712142714.png)
![截图](Pasted%20image%2020260712142736.png)

---


### 5.6.3 完整 Spider 中的设计模式总结

| 设计点                                              | 为什么这样做                             |
| ------------------------------------------------ | ---------------------------------- |
| `custom_settings` 在 Spider 内                     | 每个 Spider 可以有不同的下载延迟/并发数，不互相干扰     |
| `_clean_text()` 抽成方法                             | 多处需要文本清洗，避免重复代码                    |
| `_is_nav_link()` 抽成方法                            | 过滤逻辑单独封装，方便以后增加关键词                 |
| `_make_full_url()` 抽成方法                          | URL 补全逻辑复用                         |
| `errback=self.handle_error`                      | 处理请求失败场景，不中断整个爬虫                   |
| `self.logger.info()` / `.warning()` / `.error()` | 用 Scrapy 内置日志器，自动带时间戳和 Spider 名称前缀 |

### 5.6.4 本小节小结

| 你学到了什么 | 关键点 |
|---|---|
| 把之前所学整合到一个完整 Spider | 列表页 → 详情页 → 数据提取 |
| 自定义 Spider 级别的设置 | `custom_settings` 字典 |
| 错误处理 | `errback=self.handle_error` |
| 辅助方法抽取 | `_clean_text()`, `_is_nav_link()` 等 |
| 使用 Scrapy 日志器 | `self.logger.info/warning/error()` |

---

## 5.7 Pipeline 存储 —— 定义 Item 类，编写 Pipeline 存入 SQLite

### 5.7.1 Pipeline 的角色回顾

回到 5.1 节的工厂流水线类比：Pipeline 是"质检+仓库"。Spider 产出的 Item（字典）经过 Pipeline 时：

- **清洗**：去除空白、统一格式
- **验证**：检查必填字段不为空
- **去重**：跳过已存在的记录
- **存储**：写入数据库

### 5.7.2 定义 Item 类

到目前为止，我们用字典 `{}` 做 Item。这很方便，但有个问题：**字段名不小心拼错时不会报错**，很难排查。Scrapy 提供了 `Item` 类来定义结构化数据。

打开 `items.py`，清空原有内容，写入：

```python
# items.py —— 定义数据结构
# -*- coding: utf-8 -*-

# 导入 Item 类和 Field 类
# scrapy.Item：数据容器基类
# scrapy.Field：Item 中的字段定义
import scrapy


class GhoThemeItem(scrapy.Item):
    """
    WHO 主题 Item
    每个 Item 对应一个主题，包含名称、URL、描述
    """
    # Field() 定义字段。不需要指定类型，Scrapy 会自动适配
    # 定义一个字段只需要一行：字段名 = scrapy.Field()
    theme_title = scrapy.Field()
    theme_url = scrapy.Field()
    theme_description = scrapy.Field()
    detail_page_title = scrapy.Field()


class GhoIndicatorItem(scrapy.Item):
    """
    WHO 子指标 Item
    每个 Item 对应一个子指标，关联到所属主题
    """
    indicator_title = scrapy.Field()
    indicator_url = scrapy.Field()
    # 关联字段：记录这个指标属于哪个主题
    theme_title = scrapy.Field()
    theme_url = scrapy.Field()
```

---

📸 **操作截图**：VS Code 编辑区 —— 打开 `items.py` 写入 Item 类定义 | 截取范围：VS Code 编辑区 | 重点标注：红框圈出 `GhoThemeItem` 和 `GhoIndicatorItem` 类

---

**字典 vs Item 类的区别：**

```python
# 字典方式（之前用的）
data = {"theme_title": "Mortality", "theme_url": "..."}
# 字段名拼错不会报错
print(data["theme_titel"])  # KeyError 报错，但写的时候不会提示

# Item 方式（推荐）
from who_scraper.items import GhoThemeItem
item = GhoThemeItem()
item["theme_title"] = "Mortality"
item["theme_url"] = "..."
# 访问不存在的字段 → Scrapy 会提示
# item["theme_titel"] → KeyError: 'GhoThemeItem does not support field: theme_titel'
```

### 5.7.3 在 Spider 中使用 Item 类

更新 `gho_spider_full.py` 的顶部 import 和 `parse_detail()` 方法：

```python
# gho_spider_full.py —— 顶部添加 import
# -*- coding: utf-8 -*-

import scrapy

# 导入自定义的 Item 类
# from 项目名.items import 类名
from who_scraper.items import GhoIndicatorItem


class GhoSpiderFull(scrapy.Spider):
    # ... (name, allowed_domains, start_urls, custom_settings, parse 保持不变)

    def parse_detail(self, response):
        # ... (前面提取 theme_title, detail_title, description 不变)

        for i_link in indicator_links:
            # ... (提取 i_text, i_href, 过滤, 清洗 不变)

            # ============================================================
            # 原来：yield 字典
            # yield {"theme_title": ..., "indicator_title": ...}
            #
            # 现在：yield Item 对象
            # ============================================================
            item = GhoIndicatorItem()
            item["theme_title"] = theme_title
            item["theme_url"] = theme_url
            item["theme_description"] = description
            item["indicator_title"] = i_text
            item["indicator_url"] = i_href
            item["detail_page_title"] = detail_title

            yield item
```

### 5.7.4 编写 Pipeline —— 数据清洗 + 存入 SQLite

打开 `pipelines.py`，清空原有内容，写入：

```python
# pipelines.py —— 数据清洗 + 存储到 SQLite 数据库
# -*- coding: utf-8 -*-

# 导入 SQLite3 模块
# sqlite3 是 Python 内置模块，不需要 pip install
import sqlite3
import os


class DataCleaningPipeline:
    """
    数据清洗 Pipeline
    在 Spider yield Item 之后、存储之前，对数据做清理
    """

    def process_item(self, item, spider):
        """
        process_item() 是 Pipeline 的核心方法
        每个 Item 都会经过这个方法
        参数 item：Spider yield 出来的 Item 对象
        参数 spider：产生这个 Item 的 Spider 实例
        返回：处理后的 Item（必须 return，否则下游 Pipeline 收不到）
        """

        # 第一步：对每个文本字段去除首尾空白
        # item.fields 包含所有字段名
        # item.keys() 返回所有有值的字段名
        for field_name in item.keys():
            value = item.get(field_name)
            # 只处理字符串类型的字段
            if isinstance(value, str):
                # 去除首尾空白
                cleaned_value = value.strip()
                # 多个连续空格替换成单个空格
                words = cleaned_value.split()
                cleaned_value = " ".join(words)
                # 写回 item
                item[field_name] = cleaned_value

        # 第二步：验证必填字段不为空
        # 如果 indicator_title 为空，丢弃这个 Item
        indicator_title = item.get("indicator_title", "")
        if len(indicator_title) == 0:
            # 返回 None 表示丢弃这个 Item，不会进入下一个 Pipeline
            spider.logger.warning("⚠️ 丢弃无效 Item：indicator_title 为空")
            return None

        # 传递给下一个 Pipeline（数据库存储）
        return item


class SQLitePipeline:
    """
    SQLite 存储 Pipeline
    把 Item 数据存入 SQLite 数据库文件
    """

    def open_spider(self, spider):
        """
        open_spider() 在 Spider 启动时自动调用（只执行一次）
        适合做数据库连接、建表等初始化操作
        参数 spider：正在启动的 Spider 实例
        """

        # 第一步：确定数据库文件的路径
        # 数据库文件放在项目目录下，名为 who_data.db
        # os.path.dirname(__file__) 是当前文件(pipelines.py)的目录
        # 也就是 who_scraper/who_scraper/
        project_dir = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(project_dir, "who_data.db")

        self.db_path = db_path

        # 第二步：创建数据库连接
        # sqlite3.connect("数据库文件路径") 打开或创建 SQLite 数据库
        # 如果文件不存在，SQLite 会自动创建它
        self.conn = sqlite3.connect(db_path)

        # 第三步：创建游标（cursor）
        # 游标是执行 SQL 语句的工具
        self.cursor = self.conn.cursor()

        # 第四步：建表（如果表不存在）
        # CREATE TABLE IF NOT EXISTS 的意思是"如果表不存在就创建"
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_title TEXT,
                theme_url TEXT,
                theme_description TEXT,
                indicator_title TEXT,
                indicator_url TEXT,
                detail_page_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 第五步：提交建表操作
        self.conn.commit()

        spider.logger.info("✅ SQLite 数据库已就绪: %s", db_path)

    def process_item(self, item, spider):
        """
        把 Item 插入到 SQLite 数据库
        """

        # 第一步：组装 SQL INSERT 语句
        # ? 是占位符，防止 SQL 注入
        insert_sql = """
            INSERT INTO indicators
                (theme_title, theme_url, theme_description,
                 indicator_title, indicator_url, detail_page_title)
            VALUES
                (?, ?, ?, ?, ?, ?)
        """

        # 第二步：组装要插入的值（顺序要和 SQL 中 ? 的顺序一致）
        values = (
            item.get("theme_title", ""),
            item.get("theme_url", ""),
            item.get("theme_description", ""),
            item.get("indicator_title", ""),
            item.get("indicator_url", ""),
            item.get("detail_page_title", ""),
        )

        # 第三步：执行 INSERT
        self.cursor.execute(insert_sql, values)

        # 第四步：提交事务
        # SQLite 需要 commit() 才会真正把数据写入磁盘
        self.conn.commit()

        # 日志：记录插入成功
        spider.logger.info("💾 已保存: %s", item.get("indicator_title", "未知"))

        return item

    def close_spider(self, spider):
        """
        close_spider() 在 Spider 关闭时自动调用（只执行一次）
        适合做关闭数据库连接等清理操作
        """

        # 先关闭游标
        self.cursor.close()
        # 再关闭连接
        self.conn.close()

        spider.logger.info("🔒 SQLite 数据库连接已关闭")
        spider.logger.info("📁 数据库文件位置: %s", self.db_path)
```


---

### 5.7.5 在 settings.py 中启用 Pipeline

Pipeline 写好后，必须**在 settings.py 中注册**才会生效。打开 `settings.py`，找到 `ITEM_PIPELINES` 这一段：

```python
# settings.py —— 启用 Pipeline

# ITEM_PIPELINES 是一个字典
# 键：Pipeline 类的完整路径（项目名.文件名.类名）
# 值：优先级数字（0-1000，数字越小越先执行）
ITEM_PIPELINES = {
    "who_scraper.pipelines.DataCleaningPipeline": 100,  # 先清洗
    "who_scraper.pipelines.SQLitePipeline": 200,        # 再存储
}
```

---

📸 **操作截图**：![截图](Pasted%20image%2020260712144012.png)

---

**关于优先级的解释：**

```
DataCleaningPipeline(100) → SQLitePipeline(200)
         ↓                          ↓
      先执行                    后执行
    （清洗数据）               （存入数据库）
```

数字越小越先执行。DataCleaningPipeline 做完清洗后返回 Item，然后传给 SQLitePipeline。

### 5.7.6 用 DB Browser 查看 SQLite 数据

数据存入 SQLite 后，如何查看？推荐安装 **DB Browser for SQLite**（免费开源的可视化工具）。

1. 下载地址：`https://sqlitebrowser.org/dl/`
2. 安装后打开 DB Browser
3. 点击"打开数据库" → 选择 `who_scraper/who_data.db`
4. 点击"浏览数据"标签页 → 选择 `indicators` 表

---

📸 **操作截图**：![截图](Pasted%20image%2020260712145015.png)
![截图](Pasted%20image%2020260712145449.png)


---


### 5.7.7 Pipeline 生命周期方法对照

| 方法 | 调用时机 | 调用次数 | 适合做什么 |
|---|---|---|---|
| `open_spider(self, spider)` | Spider 启动时 | 1 次 | 打开数据库连接、建表、打开文件 |
| `process_item(self, item, spider)` | 每个 Item 产出时 | N 次 | 清洗数据、验证、写入数据库 |
| `close_spider(self, spider)` | Spider 关闭时 | 1 次 | 关闭数据库连接、关闭文件、发送邮件通知 |

### 5.7.8 本小节小结

| 你学到了什么 | 关键点 |
|---|---|
| Item 类 vs 字典 | 字段名拼写有保护，推荐用 Item 类 |
| Pipeline 的作用 | 清洗 → 验证 → 存储 |
| `process_item()` | 每个 Item 都经过此方法 |
| `open_spider()` / `close_spider()` | 启动/关闭时的初始化与清理 |
| SQLite 存储 | `sqlite3.connect()` → `cursor.execute()` → `conn.commit()` |
| 启用 Pipeline | `settings.py` 中设置 `ITEM_PIPELINES` 字典 |

---

## 5.8 完整实战 —— 整合所有，含 settings 配置

### 5.8.1 最终项目文件一览

在开始完整实战之前，确认你的项目文件结构正确：

```
who_scraper/
├── scrapy.cfg
├── who_data.db                  ← SQLite 数据库（运行后自动生成）
└── who_scraper/
    ├── __init__.py
    ├── items.py                 ← 5.7.2 定义的 Item 类
    ├── pipelines.py             ← 5.7.4 编写的数据清洗+SQLite Pipeline
    ├── settings.py              ← 本节要配置的全局设置
    ├── middlewares.py           ← Scrapy 自动生成的中间件文件（保留不动）
    └── spiders/
        ├── __init__.py
        ├── gho_spider.py        ← 5.4.6 的基本版本（保留做对比）
        ├── gho_spider_recursive.py  ← 5.5.3 的递归版本（保留做对比）
        └── gho_spider_full.py   ← 5.6.2 的完整版本（主力 Spider）
```

---



---

### 5.8.2 settings.py 完整配置

打开 `settings.py`，根据以下说明逐项配置。**每一项都不要跳过——每项配置都影响整个爬虫的行为。**

```python
# settings.py —— 完整生产配置
# -*- coding: utf-8 -*-

# ================================================================
# Scrapy settings for who_scraper project
# ================================================================

# 1. 项目名称（自动生成，不用改）
BOT_NAME = "who_scraper"

# 2. Spider 模块位置（自动生成，不用改）
SPIDER_MODULES = ["who_scraper.spiders"]
NEWSPIDER_MODULE = "who_scraper.spiders"

# ================================================================
# 3. 遵守 robots.txt 协议
# True：遵守 robots.txt 规则（WHO 允许合法爬虫，建议设为 True）
# False：忽略 robots.txt（不推荐，有法律风险）
# ================================================================
ROBOTSTXT_OBEY = False

# ================================================================
# 4. 请求频率控制
# DOWNLOAD_DELAY：每次请求之间的等待时间（秒）
# 设 2 秒 = 每分钟最多请求 30 次
# 对公开网站保持礼貌是最基本的爬虫礼仪
# ================================================================
DOWNLOAD_DELAY = 2

# ================================================================
# 5. 并发请求数
# CONCURRENT_REQUESTS：同时进行多少个请求
# 数字越小对目标服务器越友好，建议不超 8
# ================================================================
CONCURRENT_REQUESTS = 4

# 对同一个域名的并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# 对同一个 IP 的并发请求数（一般和 per_domain 相同）
#CONCURRENT_REQUESTS_PER_IP = 4

# ================================================================
# 6. 自动限速（AutoThrottle）—— 智能调节请求速度
# 开启后，Scrapy 会根据服务器响应速度自动调整延迟
# ================================================================
AUTOTHROTTLE_ENABLED = True

# 初始下载延迟（秒），自动限速的起点
AUTOTHROTTLE_START_DELAY = 2

# 最大下载延迟（秒），延迟不会超过这个值
AUTOTHROTTLE_MAX_DELAY = 10

# 目标并发请求数（面向服务器的每秒请求数）
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# ================================================================
# 7. 重试设置 —— 处理请求失败的情况
# RETRY_ENABLED：是否自动重试失败的请求
# RETRY_TIMES：最大重试次数
# RETRY_HTTP_CODES：哪些 HTTP 状态码需要重试
# ================================================================
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ================================================================
# 8. 下载超时（秒）
# 超过这个时间没有响应，视为请求失败
# ================================================================
DOWNLOAD_TIMEOUT = 30

# ================================================================
# 9. User-Agent（浏览器标识）
# 如果不设置，Scrapy 默认用 "Scrapy/版本号"，可能被某些网站拒绝
# 这里设置成常见的 Chrome 浏览器标识
# ================================================================
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ================================================================
# 10. Cookie 设置
# COOKIES_ENABLED = False 表示不使用 Cookie（对公共数据爬取一般不需要）
# ================================================================
COOKIES_ENABLED = False

# ================================================================
# 11. 日志设置
# LOG_LEVEL：控制日志详细程度
#   DEBUG   — 最详细，显示所有调试信息（开发用）
#   INFO    — 信息级别，显示关键进度（推荐）
#   WARNING — 只显示警告和错误
#   ERROR   — 只显示错误
#
# LOG_FILE：把日志写入文件（方便事后查看）
# ================================================================
LOG_LEVEL = "INFO"

# 把日志输出到文件（可选，注释掉就在 Terminal 显示）
# LOG_FILE = "scrapy.log"

# 日志时间格式
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# ================================================================
# 12. Pipeline 注册（已在 5.7.5 配置过）
# ================================================================
ITEM_PIPELINES = {
    "who_scraper.pipelines.DataCleaningPipeline": 100,
    "who_scraper.pipelines.SQLitePipeline": 200,
}

# ================================================================
# 13. 爬取深度限制（已在 Spider 的 custom_settings 中设置过）
# 这里可以设全局深度上限
# ================================================================
DEPTH_LIMIT = 3

# ================================================================
# 14. Feed Export（输出文件编码）
# 确保输出的 JSON/CSV 文件中文字符正确显示
# ================================================================
FEED_EXPORT_ENCODING = "utf-8"

# ================================================================
# 15. 其他推荐设置
# ================================================================

# Telnet 控制台（调试用，生产环境建议关闭）
TELNETCONSOLE_ENABLED = False

# 请求头中的默认 Referer（来源页）设置
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
```


---

### 5.8.3 设置项速查表

| 设置项 | 含义 | 推荐值（教学/生产） |
|---|---|---|
| `ROBOTSTXT_OBEY` | 遵守 robots 协议 | `True` |
| `DOWNLOAD_DELAY` | 请求间隔（秒） | `2` |
| `CONCURRENT_REQUESTS` | 并发请求数 | `4`（教学）/ `16`（生产） |
| `AUTOTHROTTLE_ENABLED` | 自动限速 | `True` |
| `RETRY_ENABLED` | 失败自动重试 | `True` |
| `RETRY_TIMES` | 最大重试次数 | `3` |
| `DOWNLOAD_TIMEOUT` | 下载超时（秒） | `30` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DEPTH_LIMIT` | 最大爬取深度 | `2`~`3` |
| `COOKIES_ENABLED` | 是否使用 Cookie | `False`（公共数据） |
| `FEED_EXPORT_ENCODING` | 输出文件编码 | `utf-8` |

### 5.8.4 完整运行流程

现在所有文件都准备好了，按以下步骤跑一次完整流程：

**第一步：在 VS Code 底部 Terminal 面板中，确保在项目目录：**

```bash
cd who_scraper
```

**第二步：运行完整版 Spider：**

```bash
scrapy crawl gho_full
```

因为 Pipeline 已经注册了，数据会自动存入 SQLite，不需要 `-o` 参数。

---

📸 **操作截图**：![截图](Pasted%20image%2020260712150525.png)

---

**第三步：如果还想同时导出 JSON 做备份：**

```bash
scrapy crawl gho_full -o who_backup.json
```


---

### 5.8.5 终端操作速查

以下是本项目用到的所有终端命令汇总，方便快速查阅：

```bash
# === 创建与安装 ===
pip install scrapy                  # 安装 Scrapy
scrapy version                      # 检查版本
scrapy startproject who_scraper     # 创建项目

# === 调试 ===
scrapy shell "URL"                  # 启动交互式 Shell
# 在 Shell 中：response.xpath("...").get()
#             exit() 退出

# === 运行爬虫 ===
cd who_scraper                      # 进入项目目录
scrapy crawl gho                    # 运行基础版 Spider
scrapy crawl gho_recursive          # 运行递归版 Spider
scrapy crawl gho_full               # 运行完整版 Spider（含 Pipeline）

# 加 -o 参数导出为文件
scrapy crawl gho_full -o result.json
scrapy crawl gho_full -o result.csv

# === 查看爬虫列表 ===
scrapy list                         # 列出所有可用的 Spider
```

### 5.8.6 本小节小结

| 你学到了什么 | 关键点 |
|---|---|
| 完整的 settings.py 配置 | 15 个核心设置项，覆盖频率、重试、日志、编码 |
| 自动限速（AutoThrottle） | `AUTOTHROTTLE_ENABLED = True` |
| 终端的完整操作流程 | 创建 → Shell 调试 → 运行 → 查看数据库 |
| 生产级爬虫需要的所有组件 | Spider + Item + Pipeline + Settings |

---

## 常见 Scrapy 错误及解决表

| 错误信息 | 原因 | 解决方法 |
|---|---|---|
| `ImportError: No module named 'win32api'` | Windows 缺少 pywin32 | `pip install pywin32` |
| `scrapy: command not found` | Scrapy 未安装或 PATH 问题 | `pip install scrapy`，检查是否在正确的 Python 环境中 |
| `AttributeError: 'NoneType' object has no attribute 'strip'` | `.get()` 返回了 `None`，直接调用 `.strip()` | 先用 `if value is not None:` 判断再操作 |
| `DEBUG: Filtered offsite request to 域名` | URL 不在 `allowed_domains` 中 | 添加到 `allowed_domains` 或检查是否爬到了站外链接 |
| `DEBUG: Filtered duplicate request` | URL 已经被爬过，Scrapy 自动去重 | 这是正常行为。如需重爬，加 `dont_filter=True` |
| `WARNING: Dropped: ...` | Item 在 Pipeline 中返回了 `None` | 检查 Pipeline 的 `process_item()` 是否在某些条件下返回了 `None` |
| `twisted.internet.error.TimeoutError` | 请求超时 | 增加 `DOWNLOAD_TIMEOUT` 值，或检查网络连接 |
| `[scrapy.downloadermiddlewares.retry] DEBUG: Retrying ...` | 请求失败，正在自动重试 | 正常行为。如果反复重试，可能是目标网站不可达 |
| `[scrapy.core.engine] DEBUG: Crawled (403)` | 目标网站返回 403 禁止访问 | 检查 `ROBOTSTXT_OBEY`、更换 `USER_AGENT`、降低请求频率 |
| `[scrapy.core.engine] DEBUG: Crawled (429)` | 请求频率过高，被限流 | 增加 `DOWNLOAD_DELAY`，开启 `AUTOTHROTTLE` |
| `KeyError: 'xxx does not support field: yyy'` | Item 类中未定义该字段 | 在 `items.py` 中添加对应的 `Field()` |
| `sqlite3.OperationalError: no such table` | 数据库表还没创建 | 检查 Pipeline 的 `open_spider()` 是否包含 CREATE TABLE 语句 |
| 中文输出为 `\uXXXX` 格式 | JSON 默认使用 ASCII 编码 | 在 `settings.py` 中设置 `FEED_EXPORT_ENCODING = "utf-8"` |



---

## 项目总结

### 你在这个项目中学到了什么

| 小节 | 核心技能 | 对应工厂类比 |
|---|---|---|
| 5.1 | 理解 Scrapy 组件和项目结构 | 认识工厂布局 |
| 5.2 | 创建项目、编写 Spider、使用 `yield` | 启动第一条流水线 |
| 5.3 | 在 Scrapy 中集成 BeautifulSoup 解析 | 引入外部工具 |
| 5.4 | 使用 Scrapy Shell 测试 XPath，精准定位元素 | 质检工具 |
| 5.5 | 用 `Request` 递归跟进详情页 | 扩展流水线到多工序 |
| 5.6 | 编写完整 Spider，包含错误处理和辅助方法 | 生产级工序设计 |
| 5.7 | 定义 Item 类，编写 Pipeline 存入 SQLite | 质检+仓库自动化 |
| 5.8 | 完整 settings 配置，跑通全流程 | 工厂参数优化 |

### 从 requests + BS4 到 Scrapy 的转变

| 对比维度 | requests + BS4 方式 | Scrapy 框架方式 |
|---|---|---|
| 并发请求 | 需要自己写多线程/协程 | 框架内置，只需配置 `CONCURRENT_REQUESTS` |
| URL 去重 | 需要自己维护一个 set | 框架内置，自动去重 |
| 请求失败重试 | 需要自己写 try/except | 框架内置，配置 `RETRY_TIMES` |
| 限速 | 需要自己写 time.sleep | 框架内置 AutoThrottle |
| 数据存储 | 手动写文件/数据库 | Pipeline 统一管理 |
| 日志 | 自己写 print | 框架内置分级日志 |
| 代码量 | 小项目少，大项目爆炸增长 | 始终结构清晰 |

### Scrapy 框架的核心价值

> **你只写"爬什么、怎么提取"——框架帮你管"怎么请求、怎么调度、怎么存"。**

---

## 课后练习

### 练习 1：修改起始 URL（★☆☆☆☆ 简单）

把 `start_urls` 改为 WHO GHO 数据门户首页：

```
https://www.who.int/data/gho
```

观察 Spider 的输出有什么不同？页面结构变了，你的 XPath 还能正常工作吗？

### 练习 2：增加一个新的 Pipeline（★★☆☆☆ 中等）

在 `pipelines.py` 中新增一个 `JsonExportPipeline`，把每个 Item 同时追加到一个 JSON Lines 文件（`.jsonl`）：

- 每个 Item 在文件中占一行
- 用 `open_spider()` 打开文件
- 用 `process_item()` 写入一行 `json.dumps(dict(item))`
- 用 `close_spider()` 关闭文件
- 在 `settings.py` 中注册新的 Pipeline

### 练习 3：给 Spider 添加翻页功能（★★★☆☆ 中等）

WHO 主题列表可能不止一页。观察页面底部是否有"加载更多"按钮或分页链接：

- 在 `parse()` 中，用 XPath 找到"下一页"链接
- 如果没有翻页链接，尝试通过 URL 参数模拟翻页（如 `?page=2`）
- 用 `yield scrapy.Request()` 递归请求下一页
- 控制最大翻页数（比如最多翻 5 页）

### 练习 4：增加数据去重逻辑（★★★☆☆ 较难）

在 `SQLitePipeline` 的 `process_item()` 中，先查询数据库：

```python
# 查询是否已有相同的 indicator_url
self.cursor.execute(
    "SELECT id FROM indicators WHERE indicator_url = ?",
    (item.get("indicator_url"),)
)
existing = self.cursor.fetchone()
if existing:
    # 已存在，跳过
    spider.logger.info("⏭️ 跳过重复: %s", item.get("indicator_title"))
    return item
```

### 练习 5：改造 Spider 使用 CSS 选择器混合 XPath（★★★★☆ 较难）

把 `gho_spider_full.py` 中全部使用 XPath 的部分，替换为一半 CSS 选择器、一半 XPath 的混合写法。体会两者的差异和适用场景。提示：

```python
# XPath 写法
response.xpath("//main//a[@href]")

# CSS 选择器写法
response.css("main a[href]")
response.css("a::attr(href)").get()
```

### 练习 6：替换目标站点（★★★★★ 挑战）

尝试把本项目的 Spider 改造为爬取另一个公开医疗网站。前提是：

1. 先做网站可爬取性验证（参考本教程开头的验证流程）
2. 用 Scrapy Shell 试探页面结构
3. 找到合适的 XPath 定位方式
4. 修改 Spider 和 Item 类
5. 调整 settings 参数

---

> **恭喜完成项目 5！你现在掌握了 Scrapy 框架的核心能力：从创建项目、编写 Spider 和 Pipeline、配置 settings，到完整的生产级爬虫实战。**", "file_path": "E:\\workbuddy_code\\2026-07-12-10-19-50\\output\\项目5-Scrapy入门指导书-下.md"}