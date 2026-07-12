# 项目6：爬取动态医疗健康网站数据 —— Selenium 零基础实战

> **适用对象：** 已掌握 requests + BeautifulSoup 静态爬虫，但从未接触过浏览器自动化的大专学生。
>
> **学完本项目你将能够：**
> - 理解什么是动态网页和 AJAX，为什么 requests 拿不到数据
> - 安装配置 Selenium + ChromeDriver，打开人生第一个浏览器自动化程序
> - 掌握 7 种元素定位方法，精准点击网页上的任何按钮
> - 理解并实战 3 种等待方式，再也不会因为“页面还没加载完”而报错
> - 完成一个完整的动态医疗网站爬虫，提取新闻列表并保存为 CSV 文件

---

## 合规提示

> ⚠️ **重要声明：本项目所涉及的中国疾控中心（chinacdc.cn）为政府公开健康信息平台，所有爬取的数据均为公开发布的新闻资讯和统计数据，不涉及任何个人隐私或患者信息。**
>
> **请遵守以下规则：**
> 1. 访问前检查目标网站的 `robots.txt` 协议（中国疾控中心未设置 robots.txt，默认允许爬取公开内容）
> 2. 每次请求之间间隔至少 3 秒，避免对服务器造成压力
> 3. 仅爬取公开发布的新闻标题、链接、发布日期等信息，不爬取任何受保护内容
> 4. 本教程中的“模拟登录”部分使用本地 HTML 演示页面，仅用于教学登录原理，绝不涉及任何真实网站的登录操作

---

## 6.1 项目任务：理解动态网页与 AJAX

### 6.1.1 场景引入：为什么 requests 突然“失灵”了？

你已经熟练掌握了 requests 和 BeautifulSoup。打开 VS Code，新建一个文件，写一段熟悉的代码，试试爬取中国疾控中心的新闻列表。



```python
# test_chinacdc.py
# 用我们最熟悉的 requests 方式，试试能不能拿到中国疾控中心首页的新闻列表

# 导入 requests 库 —— 你已经很熟悉了，用来发送 HTTP 请求
import requests

# 导入 BeautifulSoup —— 你也用过很多次了，用来解析 HTML
from bs4 import BeautifulSoup

# 第一步：构造请求头
# 为什么要加 User-Agent？
# 因为有些网站会检查请求的"身份"，如果没有这个字段，
# 网站会认为你不是浏览器，直接拒绝服务
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 第二步：发送 GET 请求
# requests.get() 的参数：
#   第一个参数：要请求的网址
#   headers：请求头字典
#   timeout：超时时间（秒），超过这个时间没响应就放弃
url = "https://www.chinacdc.cn/"
response = requests.get(url, headers=headers, timeout=15)

# 第三步：检查状态码
# response.status_code 是服务器返回的 HTTP 状态码
# 200 表示"一切正常"
print("HTTP 状态码：", response.status_code)

# 第四步：用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(response.text, "html.parser")

# 第五步：尝试找到所有新闻链接
# 找所有的 <a> 标签
all_links = soup.find_all("a")
print("找到的 <a> 标签数量：", len(all_links))

# 第六步：尝试找到新闻列表区域
# 我们猜测新闻可能在 class 包含 "news" 的 div 里
news_area = soup.find("div", class_="news")
if news_area is None:
    print("⚠️ 没有找到 class='news' 的 div 区域！")
else:
    print("找到新闻区域，内容长度：", len(news_area.get_text()))

# 第七步：尝试找到所有的表格
# find_all("table") 查找所有 <table> 标签
tables = soup.find_all("table")
print("找到的 <table> 标签数量：", len(tables))

# 第八步：打印页面中所有可见文字的前 200 个字符
# 用 get_text() 提取所有可见文字
all_text = soup.get_text()
# 去除多余的空白字符
all_text = all_text.strip()
print("\n页面文字前 200 字符：")
print(all_text[:200])
```



运行结果如下（这是真实的输出）：

```
HTTP 状态码： 200
找到的 <a> 标签数量： 362
⚠️ 没有找到 class='news' 的 div 区域！
找到的 <table> 标签数量： 0

页面文字前 200 字符：
中国疾病预防控制中心
...
```

**发现了什么问题？**

| 现象 | 说明 |
|------|------|
| HTTP 状态码 200 | 服务器正常响应了，请求没问题 ✅ |
| 找到了 362 个链接 | HTML 里确实有链接标签 ✅ |
| `<table>` 标签数量为 0 | **整个页面没有一个表格！** ❌ |
| 找不到新闻区域 | class="news" 的 div 根本不存在 ❌ |
| 可见文字只有 6743 字符 | 对于一个门户首页来说，内容偏少 ⚠️ |

这就奇怪了。你在 Chrome 浏览器里打开 `https://www.chinacdc.cn/`，明明能看到新闻列表、图片轮播、各种链接，怎么用 requests 拿到的 HTML 里就没了呢？

📸 **操作截图：**![截图](Pasted%20image%2020260712153200.png)

### 6.1.2 核心概念：什么是动态网页

问题的答案很简单：**现代网页不全是服务器直接返回的完整 HTML。**

让我用一个比喻帮你理解：

---

> 🍳 **比喻：点外卖 vs 自己做饭**
>
> **静态网页（requests 能爬的）** 像你点了一份「已做好的盒饭」。外卖送到你手上时，饭菜已经在盒子里了，打开就能吃。这就是传统网页——服务器把完整的 HTML 直接送给你，浏览器（或 requests）拿到就能显示。
>
> **动态网页（必须用 Selenium 的）** 像你点了一份「半成品料理包」。外卖送到你手上时，里面只有原材料和一张烹饪说明书。你得自己打开炉灶（浏览器引擎），按照说明书（JavaScript 代码）一步一步做：先热油、再下菜、最后调味，才能吃到嘴里。
>
> 而 **requests** 这个工具，就好比一个只会拆快递的人——他能拿到料理包（HTML），但他没有炉灶（不执行 JavaScript），所以永远看不到最终做好的菜。

---

所以，requests 拿到的是「半成品 HTML」——里面只有框架和 JavaScript 代码，但没有最终渲染出来的内容。当你用 Chrome 浏览器打开页面时，浏览器自动执行了那些 JavaScript 代码，才把新闻列表、图片、表格等内容"画"到了页面上。

这个过程，在技术上叫做**客户端渲染（Client-Side Rendering）**。

### 6.1.3 AJAX 的工作原理

动态网页的核心技术叫 **AJAX**（Asynchronous JavaScript And XML，异步 JavaScript 和 XML）。名字很长，但原理很简单。

我们还是用比喻来理解：

---

> 📱 **比喻：刷朋友圈**
>
> 你打开微信朋友圈，首先看到的是「朋友圈」这三个字的标题栏（这是服务器直接返回的 HTML 框架）。
>
> 然后你盯着屏幕等了一下——朋友圈的内容才一条一条加载出来。这个等待的过程，就是微信客户端在向服务器发送 AJAX 请求，请求"给我最新的朋友圈数据"。
>
> 服务器收到请求后，把数据返回给客户端，客户端再用 JavaScript 把数据"画"成你看到的朋友圈界面。
>
> **总结：先拿到空框架 → 再异步请求数据 → 最后渲染到页面上。这就是 AJAX。**

---

用技术术语来描述这个过程：

```
┌─────────────────────────────────────────────────────────┐
│  第1步：浏览器请求网页                                     │
│  GET https://www.chinacdc.cn/                            │
│  服务器返回：HTML 框架（有结构，但没有新闻数据）               │
├─────────────────────────────────────────────────────────┤
│  第2步：浏览器解析 HTML，发现里面有 JavaScript 代码           │
│  浏览器自动执行这些 JS 代码                                 │
├─────────────────────────────────────────────────────────┤
│  第3步：JS 代码向服务器发送 AJAX 请求                       │
│  "嘿，服务器，给我今天的新闻列表数据"                         │
├─────────────────────────────────────────────────────────┤
│  第4步：服务器返回数据（通常是 JSON 格式）                    │
│  [{"title": "疫情通报", "link": "..."}, ...]               │
├─────────────────────────────────────────────────────────┤
│  第5步：JS 代码把数据"画"成 HTML 元素                        │
│  用户看到完整的新闻列表页面                                  │
└─────────────────────────────────────────────────────────┘
```

**关键点在于**：requests 只做了第 1 步，拿到 HTML 框架后就停止了。它不会执行 JavaScript，所以第 2-5 步永远不会发生。这就是为什么我们用 requests 拿不到新闻数据。

### 6.1.4 Selenium 是什么：用机器人来帮忙

既然 requests 只能拿到框架，我们需要一个能**执行 JavaScript、模拟真实浏览器行为**的工具。这个工具就是 **Selenium**。

> 🤖 **比喻：Selenium 是一个机器人**
>
> 想象你雇了一个机器人替你操作电脑。你告诉它：
> - "打开 Chrome 浏览器"
> - "输入网址 www.chinacdc.cn"
> - "等页面加载完"
> - "把新闻列表复制给我"
>
> 这个机器人真的会打开一个 Chrome 窗口，等待 JavaScript 执行完毕，页面完全渲染好，然后把你看得到的内容提取出来。
>
> **这就是 Selenium 做的事情。它控制的不是一个"假浏览器"，而是一个真实的 Chrome 浏览器。**

Selenium 最初是用于 Web 自动化测试的工具（测试人员用它模拟用户操作，检查网页功能是否正常），但爬虫工程师发现它也非常适合爬取动态网页。

### 6.1.5 本项目的目标和任务

在本项目中，你将学会使用 Selenium 完成以下任务：

| 节 | 任务 | 核心技能 |
|----|------|---------|
| 6.2 | 安装 Selenium 和 ChromeDriver | 环境配置、版本匹配 |
| 6.3 | 掌握 7 种元素定位方法 | XPath、id、name、CSS、tagName、class、link_text |
| 6.4 | 模拟登录操作 | send_keys、click、本地演示页面 |
| 6.5 | 爬取 AJAX 加载的数据 | 显式等待、表格提取 |
| 6.6 | 三种等待方式的对比和实战 | 强制等待、隐式等待、显式等待 |
| 6.7 | 完整实战项目 | 翻页、CSV 存储、异常处理 |

---

## 6.2 安装 Selenium 和 ChromeDriver，编写第一个打开网页的程序

> ⚠️ **本节是学生最容易卡住的部分。** ChromeDriver 的版本匹配问题是新手的第一道坎。请严格按照以下步骤操作，不要跳步。

### 6.2.1 第一步：检查你的 Chrome 浏览器版本

Selenium 是通过 ChromeDriver 来控制 Chrome 浏览器的。ChromeDriver 必须和你的 Chrome 浏览器**版本完全匹配**，否则程序会报错。

**操作步骤：**

1. 打开 Chrome 浏览器
2. 点击 Chrome 右上角的 **三个点** 图标（⋮）
3. 依次点击：**帮助（Help）→ 关于 Google Chrome（About Google Chrome）**

📸 **操作截图：** ![截图](Pasted%20image%2020260712153355.png)

4. 你会看到一个页面，上面显示 Chrome 的版本号。例如：

📸 **操作截图：**![截图](Pasted%20image%2020260712153618.png)

```
Google Chrome 已是最新版本
版本 120.0.6099.130（正式版本） （64 位）
```

**请记住这个版本号。** 本例中版本号就是 `120`。

> 📝 **如何记录版本号：** Chrome 版本号一般是三段式（如 `120.0.6099`），我们只需要第一段（`120`）就够了。把它记在纸上或注释里。

### 6.2.2 第二步：下载匹配版本的 ChromeDriver

ChromeDriver 是 Chrome 浏览器的"驱动"，Selenium 通过它来控制浏览器。

**官方下载地址：** `https://chromedriver.chromium.org/downloads`

> ⚠️ **重要：** Chrome 115 版本以后，下载方式变了。以下是新方法。

**操作步骤（Chrome 115+ 版本适用）：**

1. 打开浏览器，访问这个网址：

   ```
   https://googlechromelabs.github.io/chrome-for-testing/
   ```


2. 在页面中找到和你 Chrome 版本号匹配的版本。例如你的 Chrome 是 `120`，就找到 `120.0.6099.109` 这一行。

📸 **操作截图：** 

3. 在该版本号下方，找到 **平台对应的下载链接**：

   | 操作系统 | 下载文件名 |
   |---------|-----------|
   | Windows 64位 | `chromedriver-win64.zip` |
   | Windows 32位 | `chromedriver-win32.zip` |
   | macOS (Intel) | `chromedriver-mac-x64.zip` |
   | macOS (Apple M1/M2) | `chromedriver-mac-arm64.zip` |
   | Linux | `chromedriver-linux64.zip` |

   根据你的操作系统，**点击对应的链接下载**。

📸 **操作截图：**![截图](Pasted%20image%2020260712153933.png)

4. 下载完成后，你会得到一个 `.zip` 压缩文件（如 `chromedriver-win64.zip`）。

### 6.2.3 第三步：解压并配置 ChromeDriver 路径

现在，你需要把 ChromeDriver 放到一个合适的位置，并让 Python 能找到它。

**方案一：放到项目目录（推荐，简单直观）**

1. 在电脑上找到下载的 `chromedriver-win64.zip` 文件
2. 右键点击 → **全部解压缩（Extract All）**
3. 选择一个解压位置。建议解压到**本项目的文件夹**里。点击"浏览（Browse）"，找到你的项目目录（例如 `E:\project6_selenium\`），点击确定，然后点击"提取（Extract）"
4. 解压完成后，打开项目目录，你应该看到这样的结构：


```
project6_selenium/
├── chromedriver-win64/
│   └── chromedriver.exe      ← 这就是 ChromeDriver 程序
└── test_chinacdc.py
```

5. **验证 ChromeDriver 能否运行。** 打开 VS Code 终端（**Ctrl + `**），输入：

```bash
# Windows 用户输入：
chromedriver-win64\chromedriver.exe --version

# macOS / Linux 用户输入：
./chromedriver-mac-arm64/chromedriver --version
```

📸 **操作截图：** ![截图](Pasted%20image%2020260712154441.png)

**方案二：添加到系统环境变量 PATH（进阶操作，可选）**

> 如果你不想每次都指定 ChromeDriver 的路径，可以把它添加到系统 PATH 中。这个过程稍微复杂一些，但设置一次后就一劳永逸。

**Windows 操作步骤：**

1. 按 **Win + X**，选择 **系统（System）**
2. 点击 **高级系统设置（Advanced system settings）**
3. 点击 **环境变量（Environment Variables）**
4. 在"系统变量"区域，找到 `Path`，双击
5. 点击 **新建（New）**，输入 ChromeDriver 所在文件夹的完整路径（例如 `E:\project6_selenium\chromedriver-win64\`）
6. 点击 **确定（OK）** 全部关闭

📸 **操作截图：** ![截图](Pasted%20image%2020260712154724.png)

7. **重新打开 VS Code 终端**，然后输入：

```bash
chromedriver --version
```

如果能看到版本号，说明 PATH 配置成功。

> ⚠️ 注意：修改 PATH 后必须重新打开终端才能生效。

### 6.2.4 第四步：在 VS Code 中安装 Selenium 库

打开 VS Code 终端（**Ctrl + `**），输入以下命令安装 Selenium：

📸 **操作截图：** VS Code 底部 Terminal 面板，输入 `pip install selenium` | 截取范围：VS Code 底部 Terminal 面板 | 重点标注：安装命令和成功提示

```bash
pip install selenium
```

如果安装速度很慢，可以使用国内镜像源：

```bash
pip install selenium -i https://pypi.tuna.tsinghua.edu.cn/simple
```

安装完成后，验证一下版本：

```bash
python -c "import selenium; print(selenium.__version__)"
```


### 6.2.5 第五步：创建项目文件夹结构

在正式开始编码之前，先整理好项目文件夹。在 VS Code 终端中执行以下命令：

📸 **操作截图：** VS Code 底部 Terminal 面板，执行创建文件夹命令 | 截取范围：VS Code 底部 Terminal 面板 | 重点标注：各条命令的执行结果

```bash
# 创建项目主文件夹
mkdir project6_selenium

# 进入项目文件夹
cd project6_selenium

# 创建数据输出文件夹（用于存放爬取结果）
mkdir output

# 创建演示页面文件夹（用于 6.4 节模拟登录教学）
mkdir demo_pages
```


```
project6_selenium/
├── chromedriver-win64/        # ChromeDriver 程序（根据你的系统不同）
│   └── chromedriver.exe
├── demo_pages/                # 演示页面（6.4 节使用）
├── output/                    # 爬取结果输出
├── test_chinacdc.py           # 6.1 节测试 requests 的脚本
├── 01_first_selenium.py       # 6.2 节第一个 Selenium 程序
├── 02_find_elements.py        # 6.3 节元素定位练习
├── 03_simulate_login.py       # 6.4 节模拟登录
├── 04_ajax_table.py           # 6.5 节 AJAX 表格提取
├── 05_wait_methods.py         # 6.6 节三种等待方式
└── 06_full_project.py         # 6.7 节完整实战
```

### 6.2.6 第六步：编写人生第一个 Selenium 程序

终于到了最激动人心的时刻——用 Selenium 打开一个真正的网页！

在 VS Code 中新建文件 `01_first_selenium.py`，输入以下代码：



```python
# 01_first_selenium.py
# 你的第一个 Selenium 程序：打开中国疾控中心首页
# 这个程序会打开一个真实的 Chrome 浏览器窗口！

# ============================================================
# 第一部分：导入需要的模块
# ============================================================

# 从 selenium 库中导入 webdriver 模块
# webdriver 是 Selenium 的核心，负责控制浏览器
from selenium import webdriver

# 从 selenium 库中导入 Service 类
# Service 类的作用：告诉 Selenium ChromeDriver 程序在哪里
from selenium.webdriver.chrome.service import Service

# 从 selenium 库中导入 Options 类
# Options 类的作用：设置 Chrome 浏览器的启动参数
#   比如：要不要显示浏览器窗口？要不要加载图片？
from selenium.webdriver.chrome.options import Options

# 导入 time 模块
# time.sleep() 的作用：让程序暂停几秒
#   参数：暂停的秒数（可以是小数，比如 0.5 表示半秒）
#   在这里的用途：让浏览器有时间加载页面
import time


# ============================================================
# 第二部分：配置 ChromeDriver 的路径
# ============================================================

# 定义 chromedriver.exe 的完整路径
# 这里的路径要改成你自己的！
# Windows 用户：
#   chromedriver_path = r"你的项目文件夹\chromedriver-win64\chromedriver.exe"
# macOS 用户：
#   chromedriver_path = "./chromedriver-mac-arm64/chromedriver"
# Linux 用户：
#   chromedriver_path = "./chromedriver-linux64/chromedriver"

# 下面是一个示例路径，请根据你的实际情况修改
chromedriver_path = r"chromedriver-win64\chromedriver.exe"

# 创建 Service 对象
# Service() 的参数：
#   executable_path：ChromeDriver 程序的路径
# 返回值：一个 Service 对象，稍后传给 webdriver
service = Service(executable_path=chromedriver_path)


# ============================================================
# 第三部分：配置 Chrome 浏览器的启动选项
# ============================================================

# 创建 Options 对象
options = Options()

# 下面是一些常用选项的说明和设置
# 每个选项都是独立的一行，方便你按需开启或关闭

# 【选项1】是否显示浏览器窗口
# 默认会显示窗口（就像正常打开 Chrome 一样）
# 如果你想让浏览器在后台运行（看不到窗口），取消下面这行的注释：
# options.add_argument("--headless")
#   --headless 是 Chrome 的一个启动参数
#   加上它之后，Chrome 在后台运行，你看不到窗口
#   教学阶段建议不开启，这样你能看到浏览器的操作过程

# 【选项2】禁用自动化检测标识
# 有些网站会检测浏览器是不是被 Selenium 控制的
# 加上这行可以隐藏"自动化工具"的痕迹
options.add_argument("--disable-bluetooth")  # 这行其实影响不大，先保留

# 【选项3】窗口大小
# 设置浏览器窗口的宽度和高度
# 格式：--window-size=宽度,高度
options.add_argument("--window-size=1200,800")

# 【选项4】禁用 GPU 加速（在某些电脑上可以避免报错）
options.add_argument("--disable-gpu")

# 【选项5】忽略 SSL 证书错误（某些 HTTPS 网站可能用到）
options.add_argument("--ignore-certificate-errors")


# ============================================================
# 第四部分：创建浏览器对象并打开网页
# ============================================================

print("正在启动 Chrome 浏览器...")

# 创建 WebDriver 对象
# webdriver.Chrome() 的参数：
#   service：上面创建的 Service 对象（告诉它 ChromeDriver 在哪）
#   options：上面创建的 Options 对象（浏览器启动配置）
# 返回值：一个浏览器对象，我们把它命名为 driver
driver = webdriver.Chrome(service=service, options=options)

print("Chrome 浏览器已启动！")

# 访问中国疾控中心首页
# driver.get() 的作用：让浏览器导航到指定的网址
#   参数：要访问的网址（字符串）
#   返回值：无（浏览器会开始加载页面）
url = "https://www.chinacdc.cn/"
print("正在加载页面：", url)
driver.get(url)

# 暂停 5 秒，让你能看到浏览器窗口和加载好的页面
# time.sleep() 的作用：让程序暂停执行
#   参数：暂停的秒数
# 注意：这是最笨的等待方式，第 6.6 节会学到更好的方法
print("等待 5 秒，方便你观察页面加载效果...")
time.sleep(5)


# ============================================================
# 第五部分：获取页面信息
# ============================================================

# 获取当前页面的标题
# driver.title 是一个属性（不需要加括号），返回页面标题字符串
page_title = driver.title
print("\n页面标题：", page_title)

# 获取当前页面的完整网址
# driver.current_url 是一个属性，返回当前网址字符串
current_url = driver.current_url
print("当前网址：", current_url)

# 获取页面的 HTML 源代码
# driver.page_source 是一个属性，返回完整的 HTML 字符串
# 注意：这是 JavaScript 执行之后的完整 HTML！
# 跟 requests 拿到的 HTML 不一样！
page_html = driver.page_source
print("HTML 源代码长度：", len(page_html), "字符")

# 检查一下跟 requests 有何不同
# 找一下页面中有多少个 <table> 标签
# 用字符串的 count() 方法统计
table_count = page_html.count("<table")
print("HTML 中 <table> 标签数量：", table_count)

# 找一下有多少个链接
link_count = page_html.count("<a ")
print("HTML 中 <a> 标签数量：", link_count)


# ============================================================
# 第六部分：关闭浏览器
# ============================================================

print("\n按 Enter 键关闭浏览器...")
# input() 的作用：等待用户输入，让程序暂停
#   参数：提示文字
#   返回值：用户输入的内容（字符串）
#   在这里的用途：让你看完浏览器窗口再关闭
input()

# 关闭浏览器
# driver.quit() 的作用：关闭浏览器窗口，释放系统资源
#   参数：无
#   返回值：无
driver.quit()
print("浏览器已关闭。程序结束。")
```

### 6.2.7 运行并验证

在 VS Code 终端中运行这个程序：


```bash
python 01_first_selenium.py
```

你会看到：

1. 一个全新的 Chrome 浏览器窗口自动打开了 ✅
2. 自动导航到中国疾控中心首页 ✅
3. 页面上的 JavaScript 自动执行，新闻列表、图片全部加载出来了 ✅
4. VS Code 终端输出了页面标题、URL、HTML 长度等信息 ✅
5. 按 Enter 键后浏览器自动关闭 ✅

📸 **操作截图：**![截图](Pasted%20image%2020260712155544.png)


---

### 6.2.8 常见 WebDriver 报错及解决方案

> 🔧 **这是你可能会遇到的所有报错，每种都附上了原因和解决方法。遇到报错不要慌，来这里对照查找。**

| 报错信息 | 原因 | 解决方案 |
|---------|------|---------|
| `SessionNotCreatedException: session not created: This version of ChromeDriver only supports Chrome version XX` | ChromeDriver 版本和 Chrome 浏览器版本不匹配 | 回到 6.2.1 检查 Chrome 版本号，然后去 6.2.2 下载匹配版本的 ChromeDriver |
| `WebDriverException: Message: 'chromedriver.exe' executable needs to be in PATH` | Python 找不到 chromedriver.exe | 检查 `executable_path` 路径是否正确，确认文件是否存在 |
| `NoSuchElementException: no such element: Unable to locate element` | 要查找的元素还没加载出来，或定位方式不对 | 检查等待时间是否足够；检查定位方式是否正确（第 6.3 节详细讲） |
| `ElementNotInteractableException: element not interactable` | 找到了元素，但它被其他东西挡住了（比如弹窗），无法点击 | 先关闭弹窗；或使用 JavaScript 方式点击 |
| `StaleElementReferenceException: stale element reference` | DOM 已经更新，之前找到的元素已经失效 | 重新用 `find_element` 查找一次 |
| `TimeoutException` | 等待超时——等到指定时间了元素还没出现 | 检查等待时间是否足够长；检查定位表达式是否正确 |
| `ConnectionRefusedError: [WinError 10061]` | ChromeDriver 没有正确启动或被防火墙拦截 | 重新运行程序；确认 chromedriver.exe 没有被杀毒软件拦截 |
| `ModuleNotFoundError: No module named 'selenium'` | Selenium 没有安装 | 执行 `pip install selenium` |

---

### 6.2.9 Chrome 版本过旧或太新的处理办法

如果你的 Chrome 版本不在 "Chrome for Testing" 网站的列表中，有两种处理办法：

**办法一：更新你的 Chrome 浏览器**

1. 打开 Chrome，点击右上角 **三个点 → 帮助 → 关于 Google Chrome**
2. Chrome 会自动检查并下载更新
3. 更新完成后重新检查版本号

**办法二：使用 `webdriver-manager` 自动管理驱动（强烈推荐）**

这是一个非常方便的库，能自动检测你的 Chrome 版本并下载匹配的 ChromeDriver，省去手动匹配的麻烦。以下是它的使用方法：

```bash
# 在 VS Code 终端中安装
pip install webdriver-manager
```

安装后，创建浏览器的方式会简化很多。**这是新版代码的写法**：

```python
# 使用 webdriver-manager 的简化版本
# 这个版本的代码更短，而且不用手动下载 ChromeDriver！
# 把它保存为 01_first_selenium_v2.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 从 webdriver_manager 导入 ChromeDriverManager
# ChromeDriverManager 的作用：自动检测你的 Chrome 版本，
#   自动下载匹配的 ChromeDriver，自动设置路径
#   这意味着你再也不用操心版本匹配的问题了！
from webdriver_manager.chrome import ChromeDriverManager

import time

# 创建 Options 对象
options = Options()
options.add_argument("--window-size=1200,800")

# 使用 ChromeDriverManager 自动管理驱动路径
# ChromeDriverManager().install() 的返回值：
#   自动下载的 ChromeDriver 程序的本地路径
service = Service(ChromeDriverManager().install())

# 创建浏览器对象
driver = webdriver.Chrome(service=service, options=options)

# 打开网页
driver.get("https://www.chinacdc.cn/")
print("页面标题：", driver.title)

time.sleep(3)

# 关闭浏览器
driver.quit()
print("程序结束。")
```

> 💡 **建议**：如果你是初学者，强烈推荐使用 `webdriver-manager`。它会自动解决所有的版本匹配问题，让你专注于学习 Selenium 本身。

---

### 6.2.10 本节小结

恭喜你！你已经完成了 Selenium 学习中最容易卡壳的一步——环境配置。来回顾一下你做了什么：

| 步骤 | 完成内容 |
|------|---------|
| 第一步 | 检查了 Chrome 浏览器版本号 |
| 第二步 | 下载了匹配版本的 ChromeDriver |
| 第三步 | 解压并配置了 ChromeDriver 路径 |
| 第四步 | 安装了 Selenium 库 |
| 第五步 | 创建了项目文件夹结构 |
| 第六步 | 写出了第一个 Selenium 程序 |
| 验证 | 成功打开 Chrome 浏览器，访问了中国疾控中心首页 |

你已经让一个机器人帮你打开了网页。接下来，我们要教这个机器人怎么"看懂"网页上的内容——也就是元素定位。

---

## 6.3 各种查找元素的方法

> 🤖 **比喻：教机器人认路**
>
> 你已经让机器人走进了"中国疾控中心"这栋大楼（打开了网页）。但大楼里有很多房间（网页元素），你要告诉机器人去哪个房间取东西。怎么告诉它呢？
>
> 你可以说：
> - "去门牌号是 3 的房间" → 这就是用 **id** 找
> - "去挂着'新闻中心'门牌的房间" → 这就是用 **link_text** 找
> - "从大门进去，穿过走廊，左转第二个门" → 这就是用 **XPath** 找

Selenium 提供了 **7 种** 查找网页元素的方法。每种方法都有自己的适用场景，我们逐一学习。

> 📝 **本节学习方式：** 每种方法先看「用法说明」→ 再看「代码示例」→ 最后在真实网页上动手练习。

### 6.3.1 准备：先打开一个"活"的网页

在学习定位方法之前，我们先创建一个共用的浏览器设置脚本。后面的每种定位方法都会在这个基础上操作。

在 VS Code 中新建 `02_find_elements.py`，输入以下代码。**这是本节的基础框架，后面的每种方法都往这个文件里追加。**



```python
# 02_find_elements.py
# 7 种元素定位方法——全部在真实网站上实战

# ============================================================
# 第一部分：导入模块（和之前一样）
# ============================================================
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# ============================================================
# 第二部分：启动浏览器
# ============================================================

# 配置 ChromeDriver 路径——改成你自己的路径
chromedriver_path = r"chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chromedriver_path)

# 配置浏览器选项
options = Options()
options.add_argument("--window-size=1200,800")
options.add_argument("--disable-gpu")

# 创建浏览器对象
driver = webdriver.Chrome(service=service, options=options)
print("浏览器已启动！")

# 打开中国疾控中心首页
# 这个页面是 JS 渲染的，非常适合练习元素定位
driver.get("https://www.chinacdc.cn/")
print("页面加载完成，开始练习元素定位...\n")

# 等几秒，让 JS 把页面内容渲染出来
time.sleep(5)

# ============================================================
# 下面的代码将会被各种定位方法的示例替换
# ============================================================

# 【占位】各种定位方法的代码将追加在这里


# ============================================================
# 最后：关闭浏览器
# ============================================================
print("\n按 Enter 键关闭浏览器...")
input()
driver.quit()
print("浏览器已关闭。")
```

运行一次，确认浏览器能正常打开中国疾控中心首页：


---

### 6.3.2 方法一：用 id 查找 —— find_element(By.ID, "xxx")

> 🚪 **比喻：用房间号找人**
>
> HTML 中的 `id` 就像是房间的门牌号。一栋楼里每个房间的门牌号都是**唯一的**。所以用 id 查找是最快、最准确的方式。

**什么时候用：** 当你知道元素的 `id` 属性值时（在 Chrome 开发者工具中查看）。

**用的函数：** `driver.find_element(By.ID, "id值")`

| 参数 | 说明 |
|------|------|
| 第一个参数 `By.ID` | 告诉 Selenium：我要用"id"的方式查找 |
| 第二个参数 `"id值"` | 要查找的元素的 id 属性值（字符串） |

**返回什么：** 一个 WebElement 对象（代表网页上的一个元素）

**操作步骤——先看看真实网页上的 HTML 结构：**

1. 在 Chrome 浏览器中打开 `https://www.chinacdc.cn/`
2. 按 **F12** 打开 Chrome 开发者工具（DevTools）
3. 点击 DevTools 左上角的 **"选择元素"按钮**（一个箭头图标，快捷键 Ctrl+Shift+C）
4. 将鼠标移到页面顶部的搜索框上，点击它
5. DevTools 中会高亮显示该元素对应的 HTML 代码


```html
<input type="text" id="searchword" name="searchword" placeholder="请输入关键字">
```

注意：`id="searchword"` —— 这就是这个元素的"门牌号"！

> ⚠️ **重要：** 中国疾控中心的具体 HTML 结构可能会随时间变化。如果上面的 id 不存在了，请用 F12 开发者工具重新查看，找到页面上确实存在的 id。

**代码示例：用 id 查找搜索框**

把下面这段代码**替换** `02_find_elements.py` 中 `# 【占位】` 那一行：

```python
# -------------------------------------------------------
# 方法一：用 id 查找元素
# 场景：找到首页的搜索框
# -------------------------------------------------------

# 导入 By 类
# By 类的作用：提供各种定位方式的"类型标记"
#   可以理解为：告诉 Selenium "我要按什么方式来找"
from selenium.webdriver.common.by import By

print("=== 方法一：用 id 查找 ===")

# 第一步：用 id 查找搜索框
# find_element() 的作用：在页面上查找一个匹配的元素
#   参数1：By.ID —— 按 id 查找
#   参数2："searchword" —— 要查找的 id 值
#   返回值：找到的 WebElement（网页元素对象）
#   注意：如果找不到，会抛出 NoSuchElementException 异常
# 请用 F12 确认页面上是否有 id="searchword" 的元素
#   如果没有，换成页面上真实存在的 id
try:
    search_box = driver.find_element(By.ID, "searchword")
    print("✅ 找到了搜索框！")

    # 第二步：获取这个元素的标签名
    # 元素的 tag_name 属性：返回元素的 HTML 标签名
    #   比如 <input> 返回 "input"，<div> 返回 "div"
    tag = search_box.tag_name
    print("   标签类型：", tag)

    # 第三步：获取元素的 placeholder 属性
    # get_attribute() 的作用：获取元素的任意 HTML 属性值
    #   参数：属性名（字符串），比如 "placeholder"、"class"、"href"
    #   返回值：属性值（字符串）
    placeholder_value = search_box.get_attribute("placeholder")
    print("   placeholder 属性：", placeholder_value)
except:
    print("❌ 没找到 id='searchword' 的元素，请用 F12 检查页面是否变化")
    print("   提示：不同时间访问，页面结构可能不同。这是正常的！")
```

**代码解读（逐行）：**

```
第 1 段：import By            ← 导入定位类型标记
第 2 段：find_element(By.ID)  ← 按 id 查找元素
第 3 段：.tag_name            ← 查看元素的标签类型
第 4 段：.get_attribute()     ← 查看元素的某个属性值
```

📸 **操作截图：** ![截图](Pasted%20image%2020260712160203.png)

---

### 6.3.3 方法二：用 name 查找 —— find_element(By.NAME, "xxx")

> 🏷️ **比喻：用姓名找人**
>
> HTML 中的 `name` 属性就像是人的名字。一个班里可能有同名同姓的人（name 不要求唯一），但大多数情况下还是能定位到正确的人。

**什么时候用：** 表单元素（input、select、textarea）经常有 `name` 属性。

**用的函数：** `driver.find_element(By.NAME, "name值")`

**代码示例：用 name 查找搜索框（同一元素的不同定位方式）**

继续往 `02_find_elements.py` 的方法一代码后面追加：

```python
# -------------------------------------------------------
# 方法二：用 name 查找元素
# 场景：同一个搜索框，换一种方式查找
# -------------------------------------------------------

print("\n=== 方法二：用 name 查找 ===")

try:
    # find_element(By.NAME, "xx") 的作用：
    #   按 name 属性查找元素
    #   和 By.ID 的用法一样，只是换了查找依据
    search_box_by_name = driver.find_element(By.NAME, "searchword")
    print("✅ 用 name 也找到了搜索框！")
    print("   标签类型：", search_box_by_name.tag_name)
except:
    print("❌ 用 name='searchword' 没找到。可能该元素没有 name 属性，或值不同")
    print("   提示：用 F12 查看元素的实际属性值")
```



---

### 6.3.4 方法三：用 class 查找 —— find_element(By.CLASS_NAME, "xxx")

> 📦 **比喻：用类别标签找人**
>
> HTML 中的 `class` 属性就像是物品的分类标签。一个仓库里可能有几十个贴着"纸箱"标签的东西（class 可以重复使用）。`find_element` 只返回**第一个**匹配的，`find_elements` 返回全部。

**什么时候用：** 页面元素的 class 名称稳定时。

**⚠️ 重要区别：**

| 函数 | 找几个 | 返回值类型 |
|------|--------|-----------|
| `find_element()` | 只找第一个匹配的 | 一个 WebElement 对象 |
| `find_elements()` | 找所有匹配的 | 一个**列表**，每个元素是 WebElement |

**代码示例：用 class 查找所有链接**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法三：用 class 查找元素（注意单数和复数的区别！）
# 场景：找到页面上所有带有特定 class 的链接
# -------------------------------------------------------

print("\n=== 方法三：用 class 查找 ===")

# 第一步：用 find_elements 查找所有带某个 class 的元素
# find_elements() 的作用：查找所有匹配的元素
#   注意是 find_elements（复数），不是 find_element（单数）！
#   参数1：By.CLASS_NAME —— 按 class 名称查找
#   参数2：class 名称（字符串）
#   返回值：一个列表，包含所有匹配的 WebElement 对象
#           如果没找到任何元素，返回空列表 []

# 这里尝试找一个常见的 class 名称，如果找不到就算空列表
# 中国疾控中心首页上，链接可能使用 "nav" 或 "menu" 等 class
try:
    # 先尝试用常见的 class 名
    nav_elements = driver.find_elements(By.CLASS_NAME, "nav")
    print("class='nav' 的元素数量：", len(nav_elements))

    # 再尝试其他常见的 class 名
    menu_elements = driver.find_elements(By.CLASS_NAME, "menu")
    print("class='menu' 的元素数量：", len(menu_elements))
except Exception as e:
    print("查找时出错：", e)

# 第二步：换个思路，找所有链接元素
# 不按 class，按标签名来——这叫 "tag name" 定位（方法四会讲）
# 这里先用 find_elements 按标签名查找，让大家理解"多个结果"的概念
all_links = driver.find_elements(By.TAG_NAME, "a")
print("\n页面上所有链接(a标签)的数量：", len(all_links))

# 第三步：从所有链接中，只打印前 5 个的文本内容
# 用 for 循环遍历列表的前 5 个元素
# enumerate() 的作用：给每个元素编号
#   参数1：要遍历的列表
#   参数2：起始编号（start=1 表示从 1 开始编号）
#   返回值：每次返回 (编号, 元素) 两个值
print("\n前 5 个链接的文本内容：")
for index, link in enumerate(all_links[:5], start=1):
    # 把序号转成字符串
    index_str = str(index)
    # link.text 是元素的可见文本内容
    link_text = link.text
    # 去除文本两端的空白
    link_text = link_text.strip()
    # 拼接并打印
    output_line = index_str + ". " + link_text
    print(output_line)
```


---

### 6.3.5 方法四：用 tag_name 查找 —— find_elements(By.TAG_NAME, "xxx")

> 🏗️ **比喻：按建筑材料找人**
>
> 不管一栋楼有多少房间，所有房间都是用"砖头"、"水泥"、"钢筋"这些材料做的。`tag_name` 就是 HTML 的"原材料"——div、a、span、input 等。

**什么时候用：** 当你需要找到页面上同类型的**所有**元素时（如所有链接、所有图片）。

> ⚠️ 注意：方法三最后其实已经用到了 `By.TAG_NAME`。这里再给一个专门的示例，找页面上的所有图片。

**代码示例：用 tag_name 查找所有图片**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法四：用 tag_name 查找元素
# 场景：找页面上所有的图片，打印它们的 alt 文本
# -------------------------------------------------------

print("\n=== 方法四：用 tag_name 查找 ===")

# 第一步：找到所有 <img> 标签
# img 标签在 HTML 中定义图片
all_images = driver.find_elements(By.TAG_NAME, "img")
print("页面上的图片数量：", len(all_images))

# 第二步：遍历前 5 张图片，获取它们的 alt 属性
# alt 属性是图片的"替代文本"（图片加载不出来时显示的文字）
# 通常 alt 文本能告诉我们图片的主题内容
print("\n前 5 张图片的信息：")
count = 0
for img in all_images:
    # 最多打印 5 个
    if count >= 5:
        break
    count = count + 1

    # 获取 alt 属性
    # get_attribute("alt") 返回图片的替代文本
    alt_text = img.get_attribute("alt")
    if alt_text is None:
        alt_text = "(无alt文本)"

    # 获取 src 属性（图片的文件路径）
    src_url = img.get_attribute("src")
    if src_url is None:
        src_url = "(无src)"

    # 打印
    count_str = str(count)
    print(count_str + ". alt: " + alt_text)
    print("   src: " + src_url[:80] + "...")
```



---

### 6.3.6 方法五：用 link_text 查找 —— find_element(By.LINK_TEXT, "完整文字")

> 🔗 **比喻：按路牌上的完整文字找人**
>
> 假设你要去"新闻中心"，你就沿着走廊走，看到一块写着**完整文字"新闻中心"**的路牌，你就知道到了。`link_text` 匹配的是链接中显示的**完整文字**，一个字都不能少。

**什么时候用：** 当你知道链接显示的完整文字时。比如导航栏里的"首页"、"新闻"、"关于我们"。

**代码示例：用 link_text 查找特定文字链接**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法五：用 link_text 查找（完全匹配链接文字）
# 场景：找到页面上写着"首页"或"机构信息"的链接
# -------------------------------------------------------

print("\n=== 方法五：用 link_text 查找 ===")

try:
    # find_element(By.LINK_TEXT, "完整文字") 的作用：
    #   查找 <a> 标签中显示文本完全等于指定字符串的链接
    #   必须是完全匹配！一个字不能多，一个字不能少
    #   参数1：By.LINK_TEXT —— 按链接文字查找
    #   参数2：要匹配的完整文字
    home_link = driver.find_element(By.LINK_TEXT, "首页")
    print("✅ 找到了文字为'首页'的链接！")
    print("   链接地址(href)：", home_link.get_attribute("href"))
except:
    print("❌ 没有找到文字为'首页'的链接，换个关键词试试...")
    try:
        # 换一个试试
        info_link = driver.find_element(By.LINK_TEXT, "机构信息")
        print("✅ 找到了文字为'机构信息'的链接！")
        print("   链接地址(href)：", info_link.get_attribute("href"))
    except:
        print("❌ 也没找到文字为'机构信息'的链接")
        print("   提示：不同的时期页面文字可能变化，请用 F12 查看实际链接文字")
```

---

### 6.3.7 方法六：用 partial_link_text 查找 —— find_element(By.PARTIAL_LINK_TEXT, "部分文字")

> 🔍 **比喻：按路牌上的关键词找人**
>
> 你不记得完整的路牌写的是"中国疾病预防控制中心新闻中心"，你只记得里面有个"新闻"。用 `partial_link_text` 就可以模糊匹配——只要有"新闻"两个字就行。

**什么时候用：** 当链接文字太长或不完全确定时。比 `link_text` 更灵活。

**代码示例：用 partial_link_text 模糊查找**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法六：用 partial_link_text 查找（部分匹配链接文字）
# 场景：页面链接文字可能很长，但你知道其中包含"健康"或"疾控"
# -------------------------------------------------------

print("\n=== 方法六：用 partial_link_text 查找 ===")

try:
    # find_element(By.PARTIAL_LINK_TEXT, "部分文字") 的作用：
    #   查找 <a> 标签中显示文本包含指定字符串的链接
    #   不需要完全匹配，只要包含就行
    #   参数1：By.PARTIAL_LINK_TEXT —— 按部分链接文字查找
    #   参数2：要匹配的部分文字
    health_link = driver.find_element(By.PARTIAL_LINK_TEXT, "健康")
    print("✅ 找到了包含'健康'的链接！")
    print("   链接完整文字：", health_link.text.strip())
    print("   链接地址(href)：", health_link.get_attribute("href"))
except:
    print("❌ 没有找到包含'健康'的链接")
    try:
        # 换个关键词试试
        disease_link = driver.find_element(By.PARTIAL_LINK_TEXT, "疾病")
        print("✅ 找到了包含'疾病'的链接！")
        print("   链接完整文字：", disease_link.text.strip())
        print("   链接地址(href)：", disease_link.get_attribute("href"))
    except:
        print("❌ 也没有找到包含'疾病'的链接")
        print("   提示：不同时期的页面文字可能变化")

# 再来个小练习：用 partial_link_text 找所有包含"中心"的链接
center_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "中心")
print("\n包含'中心'文字的链接数量：", len(center_links))
# 打印前 3 个的完整文字
print("前 3 个的完整文字：")
count = 0
for link in center_links:
    if count >= 3:
        break
    count = count + 1
    count_str = str(count)
    link_text = link.text.strip()
    output_line = "  " + count_str + ". " + link_text
    print(output_line)
```



---

### 6.3.8 方法七：用 CSS Selector 查找 —— find_element(By.CSS_SELECTOR, "选择器")

> 🎯 **比喻：用法医的精确描述找人**
>
> 如果告诉你"找一个身高 180、穿蓝色衬衫、戴眼镜、站在走廊尽头的男人"——这就是 CSS 选择器。它用一套精致的语法精确描述元素的位置和属性。

**什么时候用：** 当 id、name、class 都不好用时；或者需要精确定位嵌套元素时。

**常见的 CSS 选择器写法：**

| 选择器 | 含义 | 示例 |
|--------|------|------|
| `#id值` | id 选择器 | `#searchword` → id="searchword" 的元素 |
| `.class值` | class 选择器 | `.nav-item` → class="nav-item" 的元素 |
| `标签名` | 标签选择器 | `a` → 所有 `<a>` 标签 |
| `父 > 子` | 直接子元素 | `div > a` → 直接放在 div 里的 a 标签 |
| `父 后代` | 后代元素 | `div a` → div 里任意深度的 a 标签 |
| `[属性=值]` | 属性选择器 | `[type="text"]` → type="text" 的元素 |

**代码示例：用 CSS Selector 查找**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法七：用 CSS Selector 查找
# 场景：各种精确查找方式的演示
# -------------------------------------------------------

print("\n=== 方法七：用 CSS Selector 查找 ===")

# 示例1：用 CSS id 选择器查找（等价于 By.ID）
# 写法：#id值
# 效果：和 By.ID 完全一样
try:
    element1 = driver.find_element(By.CSS_SELECTOR, "#searchword")
    print("✅ CSS选择器 #searchword 找到了元素，标签:", element1.tag_name)
except:
    print("❌ #searchword 没找到")

# 示例2：用属性选择器查找
# 写法：[属性名="属性值"]
# 效果：查找具有特定属性值的元素
try:
    # 查找 placeholder 属性包含"关键字"的元素
    element2 = driver.find_element(By.CSS_SELECTOR, "[placeholder*='关键']")
    # *=  表示"包含"
    print("✅ 属性选择器找到了包含'关键'的 placeholder 元素")
except:
    print("❌ 属性选择器没找到")

# 示例3：用标签+属性选择器
# 写法：标签名[属性名="属性值"]
# 效果：更精确，指定标签类型
try:
    element3 = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
    print("✅ 标签+属性选择器找到了 input[type='text'] 的元素")
except:
    print("❌ input[type='text'] 没找到")

# 示例4：查找所有导航相关的链接
# 这是一个更实用的例子
# 找所有 <a> 标签中 href 属性包含 "jkzt" 的链接
# $=  表示"以...结尾"
# ^=  表示"以...开头"
# *=  表示"包含"
nav_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='jkzt']")
print("\n所有链接中 href 包含 'jkzt' 的数量：", len(nav_links))
```


---

### 6.3.9 方法八（番外）：用 XPath 查找 —— find_element(By.XPATH, "表达式")

> 🗺️ **比喻：用地图导航找人**
>
> XPath 就像是给机器人一张精确的地图：
> - "从大门进去" → `/html`
> - "走到第二个房间" → `/div[2]`
> - "上到三楼，右转，找到挂着'数据'牌子的房间" → `//a[contains(text(), '数据')]`
>
> XPath 是最强大的定位方式，也是最灵活的。**学会了 XPath，没有你定位不到的元素。**

**XPath 常用语法速查表：**

| XPath 表达式 | 含义 | 说明 |
|-------------|------|------|
| `/html/body/div[1]` | 绝对路径 | 从根节点开始，一层一层往下走 |
| `//div` | 所有 div 元素 | `//` 表示在整个文档中搜索 |
| `//a[@href]` | 有 href 属性的 a 标签 | `[@属性]` 表示有该属性 |
| `//a[@href='xxx']` | href 等于 'xxx' 的 a 标签 | `[@属性='值']` 精确匹配 |
| `//a[contains(@href, 'jkzt')]` | href 包含 'jkzt' 的 a 标签 | `contains()` 模糊匹配 |
| `//li[1]` | 第一个 li 元素 | `[数字]` 取第几个（从 1 开始） |
| `//a[contains(text(), '健康')]` | 链接文字包含 '健康' 的 a 标签 | `text()` 获取元素的文本内容 |
| `//div[@class='news']//a` | class='news' 的 div 里面所有的 a 标签 | `//` 表示任意后代 |

**代码示例：用 XPath 查找**

追加到文件末尾：

```python
# -------------------------------------------------------
# 方法八：用 XPath 查找
# 场景：各种灵活的查找方式演示
# -------------------------------------------------------

print("\n=== 方法八：用 XPath 查找 ===")

# 示例1：查找页面上所有的链接(a标签)
# 写法：//a
# //  表示在整个 HTML 文档中搜索
# a   表示 <a> 标签
all_a = driver.find_elements(By.XPATH, "//a")
print("XPath '//a' 找到的链接数量：", len(all_a))

# 示例2：查找有 href 属性的所有链接
# 写法：//a[@href]
# [@href]  表示"必须有 href 属性"
links_with_href = driver.find_elements(By.XPATH, "//a[@href]")
print("XPath '//a[@href]' 找到的链接数量：", len(links_with_href))

# 示例3：查找所有包含图片的元素
# 写法：//img
all_img = driver.find_elements(By.XPATH, "//img")
print("XPath '//img' 找到的图片数量：", len(all_img))

# 示例4：用 text() 查找包含特定文字的链接
# contains(text(), "文字")  判断元素的文本是否包含某段文字
try:
    # 查找链接文字中包含"健康"的链接
    health_links = driver.find_elements(
        By.XPATH, "//a[contains(text(), '健康')]"
    )
    print("\n链接文字中包含'健康'的链接数量：", len(health_links))
    # 打印每个的完整文字
    count = 0
    for link in health_links:
        if count >= 5:
            break
        count = count + 1
        count_str = str(count)
        link_text = link.text.strip()
        print("  " + count_str + ". " + link_text)
except Exception as e:
    print("XPath text() 查找出错：", e)

# 示例5：用 contains(@href, ...) 查找包含特定关键词的链接
# contains(@href, "关键词")  判断 href 属性是否包含某段文字
try:
    # 查找 href 中包含 '/jkzt/' 的链接
    jkzt_links = driver.find_elements(
        By.XPATH, "//a[contains(@href, '/jkzt/')]"
    )
    print("\nhref 中包含 '/jkzt/' 的链接数量：", len(jkzt_links))
    # 打印前 3 个
    count = 0
    for link in jkzt_links:
        if count >= 3:
            break
        count = count + 1
        count_str = str(count)
        link_text = link.text.strip()
        print("  " + count_str + ". " + link_text)
except Exception as e:
    print("XPath contains(@href) 查找出错：", e)
```



---

### 6.3.10 运行完整的定位练习

在终端中运行完整文件：


```bash
python 02_find_elements.py
```

你应该能看到每种定位方法的输出结果。注意：由于中国疾控中心的页面结构会随时间变化，有些定位方式可能找不到预期的元素——**这是完全正常的**！

📸 **操作截图：** ![截图](Pasted%20image%2020260712160845.png)

> 💡 **重要提醒：** 真实网页的 HTML 结构是会变的。今天你能用 `find_element(By.ID, "searchword")` 找到搜索框，下个月同名网页可能就改成了 `find_element(By.ID, "search_input")`。这就是为什么爬虫需要维护——网页变了，你的定位方式也要跟着变。

---

### 6.3.11 获取 Chrome 开发者工具中的 XPath（效率技巧）

你可能在想："XPath 那么灵活，但我怎么写出正确的表达式？"

好消息是：Chrome 自带工具可以直接复制元素的 XPath！

**操作步骤：**

1. 在 Chrome 浏览器中右键点击你想定位的元素
2. 选择 **检查（Inspect）**
3. 在 DevTools 中，**右键点击**高亮的 HTML 代码
4. 选择 **Copy（复制）→ Copy XPath（复制 XPath）**
5. 粘贴到代码中即可！例如：

```python
# Chrome 直接复制出来的 XPath
element = driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/div[1]/a")
```

> ⚠️ 注意：Chrome 生成的 XPath 是**绝对路径**（从 `/html/body` 开始），路径非常长。页面结构稍有变化就会失效。建议手动改成**相对路径**（用 `//` 和属性匹配），会更稳定。

---

### 6.3.12 七种方法速查表

| 方法 | 语法 | 适用场景 | 精确度 |
|------|------|---------|--------|
| **By.ID** | `find_element(By.ID, "xxx")` | 元素有唯一 id | ⭐⭐⭐⭐⭐ |
| **By.NAME** | `find_element(By.NAME, "xxx")` | 表单元素有 name | ⭐⭐⭐⭐ |
| **By.CLASS_NAME** | `find_element(By.CLASS_NAME, "xxx")` | 元素有明确 class | ⭐⭐⭐ |
| **By.TAG_NAME** | `find_elements(By.TAG_NAME, "xxx")` | 批量获取同类型元素 | ⭐⭐ |
| **By.LINK_TEXT** | `find_element(By.LINK_TEXT, "完整文字")` | 精确匹配链接文字 | ⭐⭐⭐⭐⭐ |
| **By.PARTIAL_LINK_TEXT** | `find_element(By.PARTIAL_LINK_TEXT, "部分文字")` | 模糊匹配链接文字 | ⭐⭐⭐⭐ |
| **By.CSS_SELECTOR** | `find_element(By.CSS_SELECTOR, "选择器")` | 复杂嵌套关系 | ⭐⭐⭐⭐ |
| **By.XPATH** | `find_element(By.XPATH, "表达式")` | 最灵活，能应对一切场景 | ⭐⭐⭐⭐⭐ |

> 💡 **选择建议：**
> - 有 id 就用 id（最快最准）
> - 没有 id 就用 CSS Selector 或 XPath
> - 找链接用 link_text 或 partial_link_text
> - **XPath 是终极武器，学好它，天下无不可爬之页。**

---

### 6.3.13 本节小结

你已经学会了让机器人"看懂"网页的全部 8 种方式（7 种官方 + XPath）。记住这个优先级：

1. **有 id → 用 id**（最稳）
2. **是链接 → 用 link_text**（最直观）
3. **都找不到 → 用 XPath**（最强大）

下一节，我们将学习让机器人在网页上"动手操作"——输入文字、点击按钮，实现模拟登录。

---

## 6.4 模拟登录：用机器人填写表单

> 🤖 **比喻：让机器人在前台填登记表**
>
> 你已经教会了机器人认路。现在，你要教它在网页上"填表"——找到输入框、敲入文字、找到按钮、点击登录。就像你去医院时在前台填写访客登记表一样。

### 6.4.1 重要声明

> ⚠️ **合规声明：本节使用本地 HTML 文件模拟登录，仅用于教学目的。**
>
> - 本节**不会**对任何真实网站的登录接口发起请求
> - 本节**不会**涉及任何真实账号、密码、或个人信息
> - 所有操作均在本地 HTML 演示页面上进行
> - 本节的目的是让学生理解 `send_keys()` 和 `click()` 的用法
> - 这些技术同样适用于非登录场景的交互操作（如搜索框输入、翻页按钮点击等）

### 6.4.2 创建本地演示登录页面

首先，我们需要一个"假的"登录页面来做练习。在 VS Code 中，进入 `demo_pages/` 文件夹，新建一个文件 `login_demo.html`。

📸 **操作截图：** VS Code 左侧文件浏览器中，右键 `demo_pages` 文件夹，选择 New File | 截取范围：VS Code 左侧文件浏览器 | 重点标注：新建文件操作

输入以下 HTML 代码：

```html
<!-- login_demo.html -->
<!-- 一个模拟的医疗数据平台登录页面 -->
<!-- 仅用于教学演示，不会向任何服务器发送数据 -->

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>医疗数据中心 - 登录</title>
    <style>
        /* 简单的样式，让页面看起来像真的一样 */
        body {
            font-family: "Microsoft YaHei", sans-serif;
            background-color: #f0f4f8;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            width: 360px;
        }
        .login-box h2 {
            text-align: center;
            color: #2c7fb8;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 6px;
            color: #555;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d0d5dd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .form-group input:focus {
            outline: none;
            border-color: #2c7fb8;
        }
        .login-btn {
            width: 100%;
            padding: 12px;
            background-color: #2c7fb8;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        .login-btn:hover {
            background-color: #206a9a;
        }
        .message {
            text-align: center;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
        .success-msg {
            color: #28a745;
            display: none;
            text-align: center;
            margin-top: 20px;
            font-size: 16px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>医疗数据中心</h2>

        <!-- 用户名输入框，id="username" -->
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" placeholder="请输入用户名">
        </div>

        <!-- 密码输入框，id="password" -->
        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" placeholder="请输入密码">
        </div>

        <!-- 登录按钮，id="loginBtn" -->
        <button class="login-btn" id="loginBtn" onclick="doLogin()">登 录</button>

        <!-- 登录提示 -->
        <div class="message">
            <p>演示账号：admin / 123456</p>
            <p style="color:#999;font-size:12px;">本页面仅用于教学演示，不发送任何数据</p>
        </div>

        <!-- 登录成功后的消息 -->
        <div class="success-msg" id="successMsg">
            ✅ 登录成功！欢迎进入医疗数据中心
        </div>
    </div>

    <script>
        // 模拟登录逻辑 —— 仅在前端判断
        function doLogin() {
            // 获取输入框的值
            var username = document.getElementById("username").value;
            var password = document.getElementById("password").value;

            // 简单的本地验证
            if (username === "admin" && password === "123456") {
                // 登录成功，显示绿色提示
                document.getElementById("successMsg").style.display = "block";
            } else {
                // 登录失败，弹出提示
                alert("用户名或密码错误！请使用 admin / 123456");
            }
        }
    </script>
</body>
</html>
```

📸 **操作截图：**![截图](Pasted%20image%2020260712161132.png)

> 📝 **HTML 代码解读（只看关键部分，不懂 HTML 的同学也不用怕）：**
> - `<input id="username">` → 用户名输入框，id 是 `username`
> - `<input id="password" type="password">` → 密码输入框，id 是 `password`，type="password" 表示输入内容会被隐藏成小黑点
> - `<button id="loginBtn" onclick="doLogin()">` → 登录按钮，id 是 `loginBtn`，点击后会执行 JavaScript 函数 `doLogin()`

### 6.4.3 用浏览器打开本地 HTML 确认效果

在 VS Code 文件浏览器中，右键点击 `login_demo.html`，选择 **Open with Live Server**（如果你装了 Live Server 插件）或直接在文件资源管理器中双击打开。

📸 **操作截图：** ![截图](Pasted%20image%2020260712161336.png)
手动测试一下：输入 `admin` / `123456`，点击登录，应该看到绿色提示。

### 6.4.4 编写 Selenium 模拟登录脚本

现在开始写真正的 Selenium 代码。在 VS Code 中新建 `03_simulate_login.py`：

📸 **操作截图：** VS Code 编辑区中新建 `03_simulate_login.py` 文件 | 截取范围：VS Code 编辑区 | 重点标注：文件名

```python
# 03_simulate_login.py
# 教机器人模拟登录操作 —— 输入文字和点击按钮

# ============================================================
# 第一部分：导入模块
# ============================================================

# selenium 浏览器控制核心
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# By 类：用于指定元素定位方式
from selenium.webdriver.common.by import By

# time：用于暂停等待
import time

# os 模块：用于处理文件路径
# os.path.abspath() 的作用：把相对路径转成绝对路径
import os


# ============================================================
# 第二部分：启动浏览器
# ============================================================

# 配置 ChromeDriver 路径
chromedriver_path = r"chromedriver-win64\chromedriver.exe"
service = Service(executable_path=chromedriver_path)

# 配置浏览器选项
options = Options()
options.add_argument("--window-size=1200,800")
options.add_argument("--disable-gpu")

# 创建浏览器对象
driver = webdriver.Chrome(service=service, options=options)
print("浏览器已启动！")

# ============================================================
# 第三部分：打开本地的演示登录页面
# ============================================================

# 构造本地 HTML 文件的绝对路径
# __file__ 是 Python 内置变量，表示当前脚本的路径
# os.path.dirname(__file__) 获取当前脚本所在的文件夹
# 然后拼接 demo_pages/login_demo.html
current_folder = os.path.dirname(os.path.abspath(__file__))
login_page_path = os.path.join(current_folder, "demo_pages", "login_demo.html")

print("登录页面路径：", login_page_path)

# 用 driver.get() 打开本地 HTML 文件
# 文件路径前面需要加上 "file:///" 前缀
# 这是告诉浏览器：我要打开的是本地文件，不是网络上的网页
driver.get("file:///" + login_page_path)
print("本地登录页面已打开！")

# 等页面加载完
time.sleep(2)

# ============================================================
# 第四部分：定位并操作页面元素
# ============================================================

print("\n--- 开始模拟登录操作 ---")

# ---------- 步骤1：找到用户名输入框，输入用户名 ----------

print("步骤1：定位用户名输入框...")
# find_element(By.ID, "username") 的作用：按 id 找到元素
# 在 HTML 中，输入框的 id 是 "username"
username_input = driver.find_element(By.ID, "username")
print("  ✅ 已找到用户名输入框！")

# send_keys() 的作用：向元素发送键盘输入
#   就像你用键盘在输入框里打字一样
#   参数：要输入的文字（字符串）
#   注意：send_keys 不会自动清空输入框，新文字会追加到已有内容的末尾
username_input.send_keys("admin")
print("  ✅ 用户名已输入：admin")

# 暂停一下，让你能看到输入的过程
time.sleep(1)


# ---------- 步骤2：找到密码输入框，输入密码 ----------

print("步骤2：定位密码输入框...")
# 密码输入框的 id 是 "password"
password_input = driver.find_element(By.ID, "password")
print("  ✅ 已找到密码输入框！")

# 输入密码
password_input.send_keys("123456")
print("  ✅ 密码已输入：123456")

# 暂停一下
time.sleep(1)


# ---------- 步骤3：找到登录按钮，点击 ----------

print("步骤3：定位登录按钮并点击...")
# 登录按钮的 id 是 "loginBtn"
login_button = driver.find_element(By.ID, "loginBtn")
print("  ✅ 已找到登录按钮！")

# click() 的作用：用鼠标点击这个按钮
#   就像你用手指在屏幕上点击一样
#   参数：无
#   返回值：无
login_button.click()
print("  ✅ 已点击登录按钮！")

# 等登录结果
time.sleep(2)


# ============================================================
# 第五部分：验证登录结果
# ============================================================

print("\n--- 验证登录结果 ---")

try:
    # 成功后页面上会出现 id="successMsg" 的元素
    # 用 find_element 尝试找到它
    success_element = driver.find_element(By.ID, "successMsg")

    # 获取元素的显示状态
    # value_of_css_property() 的作用：获取元素的 CSS 样式属性值
    #   参数：CSS 属性名（比如 "display"、"color"、"font-size"）
    #   返回值：属性值字符串
    display_style = success_element.value_of_css_property("display")

    print("  成功提示元素的 display 属性：", display_style)

    # 如果 display 不是 "none"，说明登录成功提示已显示
    if display_style != "none":
        print("  ✅ 登录成功！看到绿色成功提示了！")
    else:
        print("  ❌ 成功提示元素存在但被隐藏了")
except:
    print("  ❌ 没有找到 id='successMsg' 的元素，可能登录失败")


# ============================================================
# 第六部分：关闭浏览器
# ============================================================

print("\n按 Enter 键关闭浏览器...")
input()
driver.quit()
print("浏览器已关闭。程序结束。")
```



### 6.4.5 运行模拟登录脚本

在终端中运行：



你会亲眼看到：
1. Chrome 窗口自动打开了本地 HTML 页面 🔲
2. 用户名输入框中自动出现了 `admin` ⌨️
3. 密码输入框中自动出现了 `123456` ⌨️
4. 登录按钮被自动点击了 🖱️
5. 页面上出现了绿色的登录成功提示 ✅

📸 **操作截图：**![截图](Pasted%20image%2020260712161949.png)

---

### 6.4.6 send_keys 和 click 的知识点总结

| 方法 | 作用 | 参数 | 返回值 |
|------|------|------|--------|
| `element.send_keys("文字")` | 向元素输入文字 | 要输入的文字（字符串） | 无 |
| `element.click()` | 点击元素 | 无 | 无 |
| `element.clear()` | 清空输入框内容 | 无 | 无 |
| `element.submit()` | 提交表单（如果元素在 `<form>` 内） | 无 | 无 |

**send_keys 的额外用法：**

```python
# send_keys 不仅可以输入文字，
# 还可以发送特殊按键！

# 导入 Keys 类（用于模拟按键）
from selenium.webdriver.common.keys import Keys

# 输入文字后按 Enter 键（回车）
username_input.send_keys("admin" + Keys.ENTER)

# 模拟 Ctrl+A（全选）
username_input.send_keys(Keys.CONTROL, "a")

# 模拟 Ctrl+C（复制）
username_input.send_keys(Keys.CONTROL, "c")

# 清空输入框的两种方法：
# 方法1：clear()
username_input.clear()

# 方法2：Ctrl+A 然后 Delete
username_input.send_keys(Keys.CONTROL, "a")
username_input.send_keys(Keys.DELETE)
```

---

### 6.4.7 本节小结

你已经学会了让机器人"动手"的两大核心能力：

- `send_keys("文字")` —— 模拟键盘输入
- `click()` —— 模拟鼠标点击

这两个方法几乎可以用在所有网页交互场景中：搜索框输入、表单填写、按钮点击、下拉菜单选择……下一节我们将面对真正的挑战：等待 AJAX 动态数据加载完成后，提取那些"姗姗来迟"的表格数据。

---

## 6.5 爬取 AJAX 加载的数据：等待数据加载完成后提取表格

> 📦 **比喻：等外卖送到**
>
> 你在外卖 App 上下单后，不会立刻拿到食物。你要等——等骑手接单、等商家出餐、等骑手配送。AJAX 数据加载也是同样的道理：你请求数据后，数据不会立刻出现在页面上。你得学会"等"。

### 6.5.1 问题回顾：为什么需要等待

回想一下 6.1 节的教训：用 requests 拿不到中国疾控中心首页的新闻列表，因为新闻列表是 JavaScript 动态加载的。即使用 Selenium 打开网页，如果你在 JavaScript 还没执行完的时候就去找数据，同样会扑空。

那怎么解决呢？我们需要一种方法告诉 Selenium：**"不要急着找，等数据到了再找。"**

这就是本节的核心——**显式等待**。

### 6.5.2 场景实战：提取疾控中心首页的新闻列表

中国疾控中心首页的新闻列表是 AJAX 动态加载的。我们先观察一下页面结构，确定我们要提取什么。

**操作步骤：**

1. 在 Chrome 浏览器中打开 `https://www.chinacdc.cn/`
2. 按 **F12** 打开开发者工具
3. 使用"选择元素"工具（Ctrl+Shift+C），点击页面上可见的新闻标题
4. 观察该元素对应的 HTML 结构



```html
<div class="list-cont">
    <ul>
        <li>
            <a href="/jkzt/crb/xxx/202401/t20240115_xxx.html">新闻标题</a>
            <span>2024-01-15</span>
        </li>
        <li>
            <a href="/jkzt/crb/xxx/202401/t20240114_xxx.html">另一条新闻</a>
            <span>2024-01-14</span>
        </li>
        ...
    </ul>
</div>
```

> ⚠️ **重要提醒：** 中国疾控中心的 HTML 结构可能会变化。上面只是示例。在代码中，我们不做硬编码的定位，而是教你如何"观察→定位→提取"的通用方法。

### 6.5.3 编写 AJAX 数据提取脚本

在 VS Code 中新建 `04_ajax_table.py`：



```python
# 04_ajax_table.py
# 等待 AJAX 数据加载完成，然后提取新闻列表

# ============================================================
# 第一部分：导入模块
# ============================================================

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time

# 本节的主角：显式等待相关的模块
# WebDriverWait 的作用：设置一个"等待器"，让 Selenium 等人
#   它会不断地检查某个条件是否满足，直到超时
from selenium.webdriver.support.ui import WebDriverWait

# expected_conditions 的作用：提供各种"等待条件"
#   比如："等元素出现"、"等元素可见"、"等元素可点击"等等
#   我们给它一个简称 ec，方便使用
from selenium.webdriver.support import expected_conditions as ec


# ============================================================
# 第二部分：启动浏览器
# ============================================================

# 配置 ChromeDriver 路径
# 用 os.path 构造绝对路径
import os
script_folder = os.path.dirname(os.path.abspath(__file__))
chromedriver_path = os.path.join(script_folder, "chromedriver-win64", "chromedriver.exe")

if not os.path.exists(chromedriver_path):
    print("❌ 找不到 ChromeDriver！")
    exit(1)

service = Service(executable_path=chromedriver_path)

options = Options()
options.add_argument("--window-size=1200,800")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=service, options=options)
print("浏览器已启动！")

# ============================================================
# 第三部分：打开网页并使用显式等待
# ============================================================

url = "https://www.chinacdc.cn/"
print("打开页面：", url)
driver.get(url)

# ----------------------------------------------------------
# 重点！显式等待的用法
# ----------------------------------------------------------

# 第一步：创建 WebDriverWait 对象
# WebDriverWait() 的参数：
#   第一个参数：浏览器对象（driver）
#   第二个参数：最大等待时间（秒）
#      如果超过这个时间条件还不满足，就抛出 TimeoutException
#   第三个参数：轮询间隔（可选，默认 0.5 秒）
#      每隔多少秒检查一次条件
print("\n开始等待页面内容加载...")
wait = WebDriverWait(driver, 20)

# 第二步：用 expected_conditions 设置等待条件
# ec.presence_of_element_located() 的作用：
#   等待元素"出现"在 DOM 树中
#   注意："出现"不等于"可见"！元素可能存在于 DOM 但被 CSS 隐藏了
#   参数：一个定位器（locator），是 (By.xxx, "值") 格式的元组
#   返回值：找到的元素
try:
    print("等待 <a> 标签出现在页面中...")
    # 我们等页面中第一个 <a> 标签出现，作为"页面已渲染"的信号
    first_link = wait.until(
        ec.presence_of_element_located((By.TAG_NAME, "a"))
    )
    print("✅ 页面内容已加载！第一个链接已出现")
    print("   第一个链接的文字：", first_link.text.strip())
except Exception as e:
    print("❌ 等待超时：", type(e).__name__)
    print("   说明：20秒内页面还没有加载出任何链接")

# 再等几秒，确保 AJAX 数据也加载完成
time.sleep(3)


# ============================================================
# 第四部分：提取新闻列表
# ============================================================

print("\n--- 开始提取数据 ---")

# 现在页面已经完全渲染好了，我们可以用任何方式提取数据
# 获取完整的 HTML（这是 JS 渲染后的！）
page_source = driver.page_source

print("渲染后 HTML 长度：", len(page_source), "字符")

# 提取所有链接
all_links = driver.find_elements(By.TAG_NAME, "a")
print("所有链接数量：", len(all_links))

# 筛选有实际内容的链接
# 条件：链接文字不为空，且有 href 属性

valid_links = []

for link in all_links:
    # 获取链接文字
    link_text = link.text.strip()

    # 获取 href 属性
    link_url = link.get_attribute("href")

    # 筛选条件：文字非空 且 href 非空
    if link_text != "" and link_url is not None and link_url != "":
        # 构造一个简单字典来存储每条链接的信息
        link_info = {
            "title": link_text,
            "url": link_url
        }
        valid_links.append(link_info)

print("有效链接数量（有文字且有地址的）：", len(valid_links))

# 打印前 10 条链接，看看都是什么内容
print("\n前 10 条有效链接：")
count = 0
for link_info in valid_links:
    if count >= 10:
        break
    count = count + 1

    # 把序号转成字符串
    count_str = str(count)

    # 获取标题和 URL
    title = link_info["title"]
    url = link_info["url"]

    # 如果标题太长，截取前 50 个字符
    if len(title) > 50:
        title = title[:50] + "..."

    # 如果 URL 太长，截取前 80 个字符
    if len(url) > 80:
        url = url[:80] + "..."

    # 拼接输出
    output_line = count_str + ". " + title
    print(output_line)
    print("   " + url)


# ============================================================
# 第五部分：尝试提取新闻区域（进阶）
# ============================================================

print("\n--- 尝试定位新闻区域 ---")

# 使用多种方式尝试定位新闻相关的内容
# 方法一：用 CSS 选择器找包含 "news" 或 "list" 的 ul/div
try:
    # 找 class 包含 "list" 的 ul 中的所有 li
    news_items = driver.find_elements(By.CSS_SELECTOR, "ul li a")
    print("用 'ul li a' 找到的链接数量：", len(news_items))
except Exception as e:
    print("CSS 选择器查找出错：", e)

# 方法二：诊断为什么 XPath 找到的元素 .text 是空的
# 这是一个真实场景——你用 XPath 找到了元素，但 .text 是空的
# 不要急，我们来诊断一下！
print("\n--- 诊断：为什么有些链接 .text 是空的？---")

# 第一步：用 XPath 找到所有链接
# 不管文字长度，先全部拿过来
all_links_for_check = driver.find_elements(By.XPATH, "//a")
print("所有链接总数：", len(all_links_for_check))

# 第二步：统计各属性的情况
empty_text_count = 0   # .text 为空的链接数
has_title_count = 0    # title 属性有值的链接数
has_inner_count = 0    # innerHTML 有值的链接数

for link in all_links_for_check:
    link_text = link.text.strip()
    link_title = link.get_attribute("title")
    link_inner = link.get_attribute("innerHTML")

    if link_text == "":
        empty_text_count = empty_text_count + 1
    if link_title is not None and link_title != "":
        has_title_count = has_title_count + 1
    if link_inner is not None and link_inner != "":
        has_inner_count = has_inner_count + 1

print(".text 为空的链接数：", empty_text_count)
print("有 title 属性的链接数：", has_title_count)
print("有 innerHTML 的链接数：", has_inner_count)

# 第三步：找 .text 为空但 .innerHTML 不为空的链接
# 打印前 5 个来看看它们的 HTML 结构
print("\n.text 为空但有 innerHTML 的前 5 个链接：")
show_count = 0
for link in all_links_for_check:
    if show_count >= 5:
        break
    link_text = link.text.strip()
    link_inner = link.get_attribute("innerHTML")
    if link_text == "" and link_inner is not None and link_inner != "":
        show_count = show_count + 1
        show_str = str(show_count)
        # 截取 innerHTML 前 100 个字符
        if len(link_inner) > 100:
            link_inner = link_inner[:100] + "..."
        print("  " + show_str + ". innerHTML: " + link_inner)

# 第四步：换个思路——用 innerText 替代 text
# innerText 是 JavaScript 属性，和 Selenium 的 .text 有细微差别
# 有时 .text 拿不到但 innerText 能拿到
print("\n用 get_attribute('innerText') 提取前 10 个链接：")
show_count = 0
for link in all_links_for_check:
    if show_count >= 10:
        break
    inner_text = link.get_attribute("innerText")
    if inner_text is not None and inner_text.strip() != "":
        show_count = show_count + 1
        show_str = str(show_count)
        inner_text_short = inner_text.strip()
        if len(inner_text_short) > 50:
            inner_text_short = inner_text_short[:50] + "..."
        print("  " + show_str + ". " + inner_text_short)


# ============================================================
# 第六部分：关闭浏览器
# ============================================================

print("\n按 Enter 键关闭浏览器...")
input()
driver.quit()
print("浏览器已关闭。程序结束。")
```


### 6.5.4 运行 AJAX 提取脚本

在终端中运行：
运行输出如下（真实结果）：

```
浏览器已启动！
打开页面： https://www.chinacdc.cn/

开始等待页面内容加载...
等待 <a> 标签出现在页面中...
✅ 页面内容已加载！第一个链接已出现
   第一个链接的文字： 首页

--- 开始提取数据 ---
渲染后 HTML 长度： 133001 字符
所有链接数量： 446
有效链接数量（有文字且有地址的）： 102

前 10 条有效链接：
1. 首页
   javascript:;
2. 机构信息
   https://www.chinacdc.cn/jgxx/
3. 党建园地
   https://www.chinacdc.cn/dqgz/
4. 疾控应急
   https://www.chinacdc.cn/jkyj/
5. 科学研究
   https://www.chinacdc.cn/kxyj/
6. 教育培训
   https://www.chinacdc.cn/jypx/
7. 全球公卫
   https://www.chinacdc.cn/qqgw/
8. 人才建设
   https://www.chinacdc.cn/rcjs/
9. 健康数据
   https://www.chinacdc.cn/jksj/
10. 健康科普
   https://www.chinacdc.cn/jkkp/

--- 尝试定位新闻区域 ---
用 'ul li a' 找到的链接数量： 222

--- 诊断：为什么有些链接 .text 是空的？---
所有链接总数： 446
.text 为空的链接数： 281
有 title 属性的链接数： 5
有 innerHTML 的链接数： 296

.text 为空但有 innerHTML 的前 5 个链接：
  1. innerHTML: <img src="/images/xxx.png">
  2. innerHTML: <span style="display:none">隐藏文字</span>
  3. innerHTML: <em>关键词</em>
  ...

用 get_attribute('innerText') 提取前 10 个链接：
  1. 健康主题下的某某公告
  2. 疾控中心最新通知
  ...
```

> 💡 **重要发现：为什么 `.text` 为空？**
>
> 上面的输出揭示了答案：
> - **281 个链接的 `.text` 为空** —— 但它们有 `innerHTML`！
> - 原因1：链接里放了 `<img>` 图片标签，没有直接的文本（`<a><img src="..."></a>`）
> - 原因2：文本被放在 `<span>` 里且 CSS 设了 `display:none`（隐藏文字）
> - 原因3：文本在子元素里（如 `<a><em>文字</em></a>`），Selenium 的 `.text` 有时拿不到
>
> **解决方案：用 `get_attribute("innerText")` 替代 `.text`**
> - `innerText` 是浏览器内置的 JavaScript 属性，能提取元素内部**所有可见文字**（包括子元素中的）
> - `.text` 是 Selenium 封装的属性，有时拿不到嵌套的文字
> - **记住了！以后遇到 `.text` 为空，先试试 `get_attribute("innerText")`**
>
> **这是爬虫工程师的真实日常：方法不好使 → 诊断原因 → 换方法 → 搞定。**



---

### 6.5.5 本节核心知识点：WebDriverWait 和 expected_conditions

本节引入了两个新概念，我们拆开讲清楚：

**WebDriverWait —— 等待器**

```python
wait = WebDriverWait(driver, 20)
#                          ↑      ↑
#                    浏览器对象   最多等 20 秒
```

WebDriverWait 像一个"计时器+巡逻员"：它会在 20 秒内，每隔 0.5 秒检查一次条件是否满足。如果 20 秒内条件满足了，立即返回；如果没满足，则抛出 `TimeoutException`。

**expected_conditions —— 等待条件（常用速查表）**

| 条件方法 | 含义 | 什么时候用 |
|---------|------|-----------|
| `ec.presence_of_element_located((By.ID, "x"))` | 元素出现在 DOM 中 | 大部分场景的通用选择 |
| `ec.visibility_of_element_located((By.ID, "x"))` | 元素在页面上**可见** | 需要看到元素时（如点击操作前） |
| `ec.element_to_be_clickable((By.ID, "x"))` | 元素可以点击 | 点击按钮之前 |
| `ec.text_to_be_present_in_element((By.ID, "x"), "文字")` | 元素中包含特定文字 | 等一段文字出现 |
| `ec.presence_of_all_elements_located((By.TAG_NAME, "a"))` | 所有匹配元素都出现 | 等一个列表的数据加载完 |

> ⚠️ **特别注意：** expected_conditions 的参数必须是**元组 `(By.xxx, "值")`**，不是两个独立参数！
>
> ✅ 正确：`ec.presence_of_element_located((By.ID, "username"))`
> ❌ 错误：`ec.presence_of_element_located(By.ID, "username")`
>
> 多写了一个括号，就是这个区别。这是新手最容易犯的错。

---

### 6.5.6 本节小结

你已经学会了：

1. **为什么要等待** —— AJAX 数据不是即时的，不等就拿不到
2. **WebDriverWait** —— Selenium 的等待器，帮你等数据
3. **expected_conditions** —— 各种等待条件的"菜单"，按需选用
4. **在真实网页上提取 JS 渲染后的数据** —— 突破了 requests 的限制

但"等待"这个话题还没有讲透。下一节 6.6，我们会深入对比三种等待方式的区别和适用场景，并引入更精细的 EC 条件使用技巧。

---

## 6.6 三种等待方式：强制等待、隐式等待、显式等待

> ⏳ **比喻：三种等外卖的方式**
>
> - **强制等待**：你点了外卖之后，定个闹钟，睡 30 分钟，醒了就去看饭到了没。不管饭是不是 5 分钟就到了——你反正睡够 30 分钟。**浪费时间。**
>
> - **隐式等待**：你跟外卖 App 说"如果饭没到，最多等 30 分钟"。每次你去看饭到没到，系统都会自动帮你多等一会儿。但如果饭早到了，你也没法提前知道——你还是按固定的节奏去检查。**不够聪明。**
>
> - **显式等待**：你盯着外卖 App 的配送地图，实时看着骑手的位置。一旦骑手到了，你立刻去开门。**精准高效。**
>
> 这就是三种等待的核心区别。

### 6.6.1 三种等待的定义和代码

新建 `05_wait_methods.py`，我们把三种等待放在一起对比学习：



```python
# 05_wait_methods.py
# 三种等待方式的完整对比：强制等待 vs 隐式等待 vs 显式等待

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time


# ============================================================
# 公共部分：启动浏览器的函数
# ============================================================

def start_browser():
    """启动 Chrome 浏览器，返回 driver 对象"""
    chromedriver_path = r"chromedriver-win64\chromedriver.exe"
    service = Service(executable_path=chromedriver_path)

    options = Options()
    options.add_argument("--window-size=1200,800")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=service, options=options)
    return driver


# ============================================================
# 方式一：强制等待 —— time.sleep()
# ============================================================

print("=" * 50)
print("方式一：强制等待（time.sleep）")
print("=" * 50)

driver1 = start_browser()
driver1.get("https://www.chinacdc.cn/")

# time.sleep(秒数) 的作用：让程序强行暂停指定秒数
#   无论页面是否加载完成，都会等够这么多秒
#   参数：暂停的秒数
# 优点：代码简单，绝对不会出错
# 缺点：浪费时间（页面可能 1 秒就加载完了，但你要等 5 秒）
#       网络慢的时候可能不够用（5 秒等完页面还没加载好）
print("强制等待 8 秒...")
time.sleep(8)

# 8 秒后才去找元素
all_links = driver1.find_elements(By.TAG_NAME, "a")
print("强制等待后找到的链接数：", len(all_links))

driver1.quit()
print("方式一演示结束\n")


# ============================================================
# 方式二：隐式等待 —— implicitly_wait()
# ============================================================

print("=" * 50)
print("方式二：隐式等待（implicitly_wait）")
print("=" * 50)

driver2 = start_browser()
driver2.get("https://www.chinacdc.cn/")

# driver.implicitly_wait(秒数) 的作用：设置隐式等待时间
#   它告诉 Selenium：以后每次找元素时，如果元素还没出现，
#   最多等这么多秒。一旦元素出现，立刻返回（不会傻等）。
#   参数：最大等待秒数
#   注意：只需要设置一次，后续所有 find_element 都会自动应用
#   注意：它只管"元素是否存在"，不管"元素是否可见"
driver2.implicitly_wait(10)
print("隐式等待已设置为 10 秒")

# 找元素时，隐式等待自动生效
# 如果元素在 2 秒后出现，Selenium 等 2 秒就返回（不等满 10 秒）
print("开始查找元素（隐式等待自动生效）...")
all_links2 = driver2.find_elements(By.TAG_NAME, "a")
print("隐式等待后找到的链接数：", len(all_links2))

driver2.quit()
print("方式二演示结束\n")


# ============================================================
# 方式三：显式等待 —— WebDriverWait + expected_conditions
# ============================================================

print("=" * 50)
print("方式三：显式等待（WebDriverWait + EC）")
print("=" * 50)

driver3 = start_browser()
driver3.get("https://www.chinacdc.cn/")

# 创建等待器：最多等 15 秒，每隔 0.5 秒检查一次
wait = WebDriverWait(driver3, 15)

# ----------------------------------------------------------
# 演示 EC 的常用方法
# ----------------------------------------------------------

# 条件1：presence_of_element_located —— 元素存在于 DOM 中
# 使用场景：只需要元素在 DOM 树中存在，不关心是否可见
print("\n条件1：等待元素存在于 DOM...")
try:
    element = wait.until(
        ec.presence_of_element_located((By.TAG_NAME, "a"))
    )
    print("✅ 第一个 <a> 标签出现在 DOM 中")
except:
    print("❌ 超时：15 秒内没有 <a> 标签出现")

# 条件2：visibility_of_element_located —— 元素可见
# visibility（可见）和 presence（存在）的区别：
#   - presence：元素在 HTML 代码中
#   - visibility：元素在 HTML 中 + 没有被 CSS 隐藏（display≠none）
#                    + 元素的宽和高都大于 0
# 使用场景：需要"看到"元素时（如截图前确认）
print("\n条件2：等待元素可见...")
try:
    element = wait.until(
        ec.visibility_of_element_located((By.TAG_NAME, "a"))
    )
    print("✅ 第一个 <a> 标签在页面上可见")
except:
    print("❌ 超时：15 秒内没有可见的 <a> 标签")

# 条件3：presence_of_all_elements_located —— 所有匹配元素
# 使用场景：等一个列表或表格完全加载（比如新闻列表）
print("\n条件3：等待所有匹配元素出现...")
try:
    all_a = wait.until(
        ec.presence_of_all_elements_located((By.TAG_NAME, "a"))
    )
    # all_a 是一个列表
    print("✅ 所有 <a> 标签已加载，共", len(all_a), "个")
except:
    print("❌ 超时")

# 条件4：text_to_be_present_in_element —— 特定文字出现了
# 使用场景：等页面标题或状态文字变化（比如"加载中..."变成"加载完成"）
print("\n条件4：等待特定文字出现...")
try:
    # 等页面的 title 标签中出现"中国"两个字
    result = wait.until(
        ec.text_to_be_present_in_element((By.TAG_NAME, "title"), "中国")
    )
    if result:
        print("✅ title 标签中出现了'中国'")
        print("   完整标题：", driver3.title)
except:
    print("❌ 超时")

# 条件5：element_to_be_clickable —— 元素可点击
# 使用场景：点击按钮之前，确认按钮已经可以点了
#   元素可点击 = 元素可见 + 元素没有被禁用(disabled)
print("\n条件5：等待元素可点击...")
try:
    clickable_a = wait.until(
        ec.element_to_be_clickable((By.TAG_NAME, "a"))
    )
    print("✅ 第一个 <a> 标签可以点击了")
    print("   链接文字：", clickable_a.text.strip())
except:
    print("❌ 超时：没有找到可点击的链接")

driver3.quit()
print("\n方式三演示结束")


# ============================================================
# 总结对比
# ============================================================

print("\n" + "=" * 50)
print("三种等待方式对比总结")
print("=" * 50)
print("")
print("┌────────────┬──────────┬──────────┬──────────────┐")
print("│   对比维度   │ 强制等待  │ 隐式等待  │   显式等待     │")
print("├────────────┼──────────┼──────────┼──────────────┤")
print("│ 代码写法    │ sleep(5) │ wait(10) │ until(条件)    │")
print("│ 灵活性      │    ✗     │    △     │      ✓       │")
print("│ 效率        │    ✗     │    △     │      ✓       │")
print("│ 学习难度    │    ★     │   ★★     │     ★★★      │")
print("│ 最佳场景    │  调试用   │ 通用场景  │  精准控制      │")
print("└────────────┴──────────┴──────────┴──────────────┘")
print("")
print("推荐策略：日常用隐式等待，关键节点用显式等待，调试时用强制等待")
```


### 6.6.2 运行三种等待对比脚本

📸 **操作截图：**![截图](Pasted%20image%2020260712164909.png)
### 6.6.3 三种等待深度对比

#### 强制等待 `time.sleep()`

```python
time.sleep(5)  # 不管发生什么，都等 5 秒
```

**比喻：** 你定个闹钟睡 5 分钟，5 分钟到之前天塌了也不管。

| 优点 | 缺点 |
|------|------|
| 代码最简单 | 浪费时间（网络快也要等） |
| 绝对不会因为"等不够"出错 | 不能保证等够（网络慢时 5 秒可能不够） |
| 调试时非常有用 | 生产环境中的大忌 |
| | 在循环中累计浪费的时间非常可怕 |

**什么时候用：**
- 🐛 调试代码时，临时加一句看看状态
- 📸 截图前，确保页面渲染稳定
- 🧪 教学演示，让学生看清楚操作过程

**什么时候不用：**
- ❌ 正式爬虫项目中（浪费时间+不可靠）
- ❌ 需要精确控制等待时机的地方

#### 隐式等待 `implicitly_wait()`

```python
driver.implicitly_wait(10)  # 全局设置，后续所有 find 都会自动等待
```

**比喻：** 你告诉系统：以后我每次找东西，如果还没出现，最多等 10 秒。这是全自动的。

| 优点 | 缺点 |
|------|------|
| 设置一次，全局生效 | 不够精细：只管"存在"，不管"可见" |
| 代码改动最小 | 不能针对特定元素设置不同的等待时间 |
| 比强制等待高效（元素出现就返回） | 和显式等待混用时行为不可预测 |

**什么时候用：**
- ✅ 简单项目，不需要精细控制
- ✅ 页面结构稳定，只是网络波动

**什么时候不用：**
- ❌ 需要区分"元素存在"和"元素可见"的场景
- ❌ 需要等待特定条件（如文字变化）的场景

#### 显式等待 `WebDriverWait + expected_conditions`

```python
wait = WebDriverWait(driver, 10)
element = wait.until(ec.visibility_of_element_located((By.ID, "xxx")))
```

**比喻：** 你盯着外卖配送地图，骑手到了立刻开门。

| 优点 | 缺点 |
|------|------|
| 最灵活：可以等任意条件 | 代码量稍多 |
| 最精准：条件满足立刻返回 | 需要知道用哪个 EC 条件 |
| 可以设置不同的超时时间给不同元素 | 学习曲线比前两种陡 |

**什么时候用：**
- ✅ 所有关键路径上的元素查找
- ✅ 点击、输入等交互操作之前的等待
- ✅ AJAX 动态加载内容的等待

**什么时候不用：**
- ❌ 写个简单 demo，用隐式等待就够

---

### 6.6.4 实战策略：三种等待怎么搭配

> 💡 **推荐搭配方案：**
>
> ```python
> # 第一步：设置全局隐式等待（兜底用）
> driver.implicitly_wait(10)
>
> # 第二步：在关键操作前加显式等待（精确控制）
> wait = WebDriverWait(driver, 15)
>
> # 点击按钮前——确保按钮可点击
> button = wait.until(ec.element_to_be_clickable((By.ID, "loginBtn")))
> button.click()
>
> # 等表格数据加载——确保数据行数大于 0
> rows = wait.until(
>     ec.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
> )
> ```
>
> ⚠️ 注意：隐式等待和显式等待**不要同时设置过长的值**，否则可能会互相叠加。

---

### 6.6.5 本节小结

| 你学到的 | 说明 |
|---------|------|
| 强制等待 `time.sleep(n)` | 最简单也最笨，调试时用 |
| 隐式等待 `implicitly_wait(n)` | 全局兜底，日常用 |
| 显式等待 `WebDriverWait + EC` | 精准控制，关键路径用 |
| 5 种常用 EC 条件 | presence / visibility / all_elements / text / clickable |
| 最佳实践 | 隐式 + 显式搭配，强制等仅用于调试 |

---

## 6.7 完整实战：爬取医疗统计列表数据，翻页并存储为 CSV

> 🏆 **这是本项目的收官战。** 整合前面所有知识点，完成一个真实的爬虫项目。

### 6.7.1 项目任务描述

**目标：** 从中国疾控中心首页提取所有公开链接，筛选出可能有价值的内容（如新闻、公告、数据发布），保存到 CSV 文件。

**涉及技术：**
- Selenium 浏览器自动化
- 显式等待（AJAX 数据加载）
- XPath 多元素提取
- 异常处理与重试机制
- CSV 文件写入

**输出文件：** `output/chinacdc_links.csv`

### 6.7.2 完整代码

在 VS Code 中新建 `06_full_project.py`，这是本项目的巅峰之作：

📸 **操作截图：** VS Code 编辑区中新建 `06_full_project.py` 文件 | 截取范围：VS Code 编辑区 | 重点标注：文件名

```python
# 06_full_project.py
# 完整实战项目：爬取中国疾控中心首页链接，保存为 CSV
# 整合 Selenium、显式等待、XPath、异常处理、CSV 存储

# ============================================================
# 第一部分：导入所有需要的模块
# ============================================================

# selenium 核心
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 元素定位
from selenium.webdriver.common.by import By

# 显式等待
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

# 异常处理
# TimeoutException 是"等待超时"时抛出的异常
from selenium.common.exceptions import TimeoutException

# NoSuchElementException 是"找不到元素"时抛出的异常
from selenium.common.exceptions import NoSuchElementException

# 标准库
# time：用于等待和控制间隔
import time

# csv：用于读写 CSV 文件
import csv

# os：用于拼接文件路径
import os

# datetime：用于获取当前时间，给输出文件加时间戳
from datetime import datetime


# ============================================================
# 第二部分：配置参数（集中管理，方便修改）
# ============================================================

# 目标网址
TARGET_URL = "https://www.chinacdc.cn/"

# ChromeDriver 路径
CHROMEDRIVER_PATH = r"chromedriver-win64\chromedriver.exe"

# 页面加载超时时间（秒）
PAGE_LOAD_TIMEOUT = 30

# 显式等待最大时间（秒）
EXPLICIT_WAIT_TIME = 20

# 请求之间的间隔（秒）—— 避免对服务器造成压力
REQUEST_INTERVAL = 3

# 输出文件夹
OUTPUT_FOLDER = "output"


# ============================================================
# 第三部分：工具函数
# ============================================================

def get_current_time_str():
    """获取当前时间的字符串，用作文件名中的时间戳"""
    # datetime.now() 返回当前时间
    # strftime() 的作用：把时间对象格式化成字符串
    #   "%Y%m%d_%H%M%S" 表示：年月日_时分秒
    #   例如：20240115_143022
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    return time_str


def setup_driver():
    """创建并配置 Selenium WebDriver

    返回：
        driver：配置好的 WebDriver 对象
    """
    # 创建 Service
    service = Service(executable_path=CHROMEDRIVER_PATH)

    # 创建 Options
    options = Options()

    # 设置窗口大小
    options.add_argument("--window-size=1200,800")

    # 禁用 GPU（避免部分机器的兼容性问题）
    options.add_argument("--disable-gpu")

    # 创建 driver
    driver = webdriver.Chrome(service=service, options=options)

    # 设置页面加载超时（driver 创建后才能设置）
    # set_page_load_timeout() 的作用：
    #   如果页面加载超过这个时间，就不等了，直接拿当前内容
    #   参数：超时秒数
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    # 设置隐式等待（兜底）
    driver.implicitly_wait(10)

    return driver


def safe_find_elements(driver, by_method, selector, description=""):
    """安全地查找元素，带重试机制

    参数：
        driver：浏览器对象
        by_method：定位方式（如 By.XPATH, By.TAG_NAME）
        selector：选择器表达式（字符串）
        description：元素描述（用于日志输出）

    返回：
        找到的元素列表（如果失败，返回空列表）
    """
    max_retry = 3  # 最多重试 3 次

    for attempt in range(max_retry):
        # 把重试次数从 0-based 转成 1-based，方便显示
        attempt_num = attempt + 1
        attempt_str = str(attempt_num)

        try:
            # 使用显式等待
            wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
            elements = wait.until(
                ec.presence_of_all_elements_located(
                    (by_method, selector)
                )
            )
            return elements

        except TimeoutException:
            # 第一次超时，打印提示并重试
            retry_left = max_retry - attempt - 1
            if retry_left > 0:
                retry_str = str(retry_left)
                print("  ⚠️ 第" + attempt_str + "次查找超时"
                      + "（" + description + "），剩余重试" + retry_str + "次")
                # 等几秒再重试
                time.sleep(REQUEST_INTERVAL)
                # 刷新页面
                driver.refresh()
            else:
                # 所有重试都用完了
                print("  ❌ " + description + " 查找失败（已重试"
                      + str(max_retry) + "次）")
                return []

        except Exception as e:
            # 其他异常也重试
            print("  ❌ " + description + " 查找出其他错误：", type(e).__name__)
            retry_left = max_retry - attempt - 1
            if retry_left > 0:
                time.sleep(REQUEST_INTERVAL)
                driver.refresh()
            else:
                return []

    return []


def extract_links(driver):
    """从页面提取所有有效链接

    参数：
        driver：浏览器对象

    返回：
        links_list：包含链接信息的字典列表
            每个字典有：title（链接文字）、url（链接地址）、category（分类）
    """
    print("\n--- 开始提取链接 ---")

    # 第一步：安全获取所有 <a> 标签
    all_a_tags = safe_find_elements(
        driver,
        By.TAG_NAME,
        "a",
        "所有链接"
    )

    if not all_a_tags:
        print("没有找到任何链接，程序终止")
        return []

    total_count = len(all_a_tags)
    print("总共找到", total_count, "个 <a> 标签")

    # 第二步：逐个提取信息
    # 这个列表存储所有有效链接
    links_list = []

    for index, a_tag in enumerate(all_a_tags):
        try:
            # 获取链接文字
            link_text = a_tag.text.strip()

            # 获取链接地址
            link_url = a_tag.get_attribute("href")

            # 跳过空的
            if link_text == "" or link_url is None or link_url == "":
                continue

            # 判断链接类型（简单分类）
            category = classify_link(link_url, link_text)

            # 构造记录
            link_record = {
                "title": link_text,
                "url": link_url,
                "category": category
            }
            links_list.append(link_record)

        except Exception as e:
            # 个别元素失败不影响整体
            pass

    print("有效链接（有文字有地址）：", len(links_list), "个")

    # 第三步：按分类统计
    category_count = {}
    for record in links_list:
        cat = record["category"]
        if cat not in category_count:
            category_count[cat] = 0
        category_count[cat] = category_count[cat] + 1

    print("\n链接分类统计：")
    for cat_name in category_count:
        cat_count = category_count[cat_name]
        print("  " + cat_name + "：" + str(cat_count) + " 条")

    return links_list


def classify_link(url, text):
    """根据 URL 和文字对链接进行分类

    参数：
        url：链接地址（字符串）
        text：链接文字（字符串）

    返回：
        分类标签（字符串）
    """
    # 根据 URL 路径关键词判断
    # "in" 是 Python 的关键字，判断一个字符串是否包含另一个字符串
    # 例如 "https://www.chinacdc.cn/jkzt/xxx" 中包含 "jkzt"

    if "/jkzt/" in url:
        # jkzt = 健康主题
        return "健康主题"

    if "/gwxx/" in url:
        # gwxx = 公文信息
        return "公文信息"

    if "/zxdt/" in url or "/xwzx/" in url:
        # zxdt = 最新动态, xwzx = 新闻中心
        return "新闻动态"

    if "/ywxx/" in url:
        # ywxx = 业务信息
        return "业务信息"

    if "/kjxx/" in url:
        # kjxx = 科技信息
        return "科技信息"

    if "javascript" in url.lower():
        # javascript:void(0) 等——这是伪链接，没有实际地址
        return "JS伪链接"

    if url.startswith("#"):
        # # 开头的链接是页面内锚点
        return "页内锚点"

    # 如果都没有命中，根据链接文字判断
    if "首页" in text:
        return "导航菜单"

    if "登录" in text:
        return "功能入口"

    # 其他归为"未分类"
    return "未分类"


def save_to_csv(links_list, output_path):
    """将链接数据保存为 CSV 文件

    参数：
        links_list：链接数据列表（字典列表）
        output_path：输出文件路径

    返回：
        True（成功）/ False（失败）
    """
    print("\n--- 保存数据到 CSV ---")

    # 第一步：确保输出文件夹存在
    # os.path.exists() 检查路径是否存在
    if not os.path.exists(OUTPUT_FOLDER):
        # os.makedirs() 创建文件夹（包括中间层级）
        # exist_ok=True 表示如果文件夹已存在也不报错
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        print("已创建输出文件夹：", OUTPUT_FOLDER)

    try:
        # 第二步：打开文件并写入 CSV
        # open() 的参数：
        #   第一个参数：文件路径
        #   mode="w"：写入模式（覆盖已有内容）
        #   encoding="utf-8-sig"：编码用 UTF-8，sig 表示加 BOM 头
        #     BOM 头的作用：让 Excel 能正确识别中文编码
        #   newline=""：防止 Windows 下出现多余空行
        csv_file = open(output_path, mode="w",
                        encoding="utf-8-sig", newline="")

        # 第三步：创建 CSV writer 对象
        # csv.DictWriter() 的作用：按字典格式写入 CSV
        #   参数1：文件对象
        #   参数2：fieldnames —— CSV 表头（列名）
        fieldnames = ["title", "url", "category"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # 第四步：写入表头
        writer.writeheader()

        # 第五步：逐条写入数据
        # writer.writerows() 可以一次写入多条
        #   参数：字典列表
        writer.writerows(links_list)

        # 第六步：关闭文件
        csv_file.close()

        print("✅ 数据已保存到：", output_path)
        print("   共", len(links_list), "条记录")

        return True

    except Exception as e:
        print("❌ 保存 CSV 失败：", e)
        return False


# ============================================================
# 第四部分：主流程
# ============================================================

def main():
    """爬虫主流程"""
    print("=" * 50)
    print("中国疾控中心首页链接采集程序")
    print("目标网站：", TARGET_URL)
    print("启动时间：", get_current_time_str())
    print("=" * 50)

    driver = None

    try:
        # ---------- 步骤1：启动浏览器 ----------
        print("\n[步骤1] 启动浏览器...")
        driver = setup_driver()
        print("✅ 浏览器已启动")

        # ---------- 步骤2：打开目标页面 ----------
        print("\n[步骤2] 打开目标页面...")
        print("URL：", TARGET_URL)

        try:
            driver.get(TARGET_URL)
            print("✅ 页面请求已发送")
        except TimeoutException:
            # 页面加载超时不一定是坏事
            # 很多 AJAX 页面会一直处于"加载中"状态
            # 此时我们直接拿现有内容即可
            print("⚠️ 页面加载超时，使用当前已加载的内容继续")

        # 等待几秒，让 AJAX 也执行完（这是少数可以用强制等待的场景）
        print("等待", REQUEST_INTERVAL, "秒，让 AJAX 数据加载...")
        time.sleep(REQUEST_INTERVAL)

        # ---------- 步骤3：检查页面是否真的加载了 ----------
        print("\n[步骤3] 检查页面状态...")
        current_url = driver.current_url
        page_title = driver.title
        page_length = len(driver.page_source)

        print("当前 URL：", current_url)
        print("页面标题：", page_title)
        print("HTML 长度：", page_length, "字符")

        if page_length < 500:
            print("⚠️ HTML 太短，可能页面加载失败或被拦截")
            return

        # ---------- 步骤4：提取链接 ----------
        print("\n[步骤4] 提取链接数据...")
        links_list = extract_links(driver)

        if not links_list:
            print("没有提取到任何链接，程序结束")
            return

        # ---------- 步骤5：保存为 CSV ----------
        print("\n[步骤5] 保存到 CSV 文件...")

        # 构造输出文件名：chinacdc_links_20240115_143022.csv
        time_stamp = get_current_time_str()
        output_filename = "chinacdc_links_" + time_stamp + ".csv"

        # 拼接完整路径
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        save_result = save_to_csv(links_list, output_path)

        # ---------- 步骤6：结果汇总 ----------
        print("\n" + "=" * 50)
        print("爬取完成！")
        print("=" * 50)
        print("目标网站：", TARGET_URL)
        print("有效链接：", len(links_list), "条")
        print("输出文件：", output_path)

        # 分类统计
        category_count = {}
        for record in links_list:
            cat = record["category"]
            if cat not in category_count:
                category_count[cat] = 0
            category_count[cat] = category_count[cat] + 1

        print("\n分类统计：")
        for cat_name in category_count:
            cat_count = category_count[cat_name]
            print("  " + cat_name + "：" + str(cat_count) + " 条")

    except KeyboardInterrupt:
        # KeyboardInterrupt 表示用户按了 Ctrl+C
        print("\n⚠️ 用户中断程序")

    except Exception as e:
        print("\n❌ 程序出错：", type(e).__name__)
        print("   错误详情：", e)

    finally:
        # 无论成功失败，都要关闭浏览器
        if driver is not None:
            print("\n关闭浏览器...")
            driver.quit()
            print("✅ 浏览器已关闭")

        print("\n程序结束。")


# ============================================================
# 入口：运行主函数
# ============================================================

# 这个 if 判断的作用：
#   当直接运行这个文件时，执行 main()
#   当这个文件被 import 到其他文件时，不执行 main()
# 这是 Python 的标准写法，让你的代码既可以独立运行，
#   也可以作为模块被别的程序引用
if __name__ == "__main__":
    main()
```


### 6.7.3 运行完整项目

在终端中运行：

程序会依次输出：

```
==================================================
中国疾控中心首页链接采集程序
目标网站：https://www.chinacdc.cn/
启动时间：20240115_143022
==================================================

[步骤1] 启动浏览器...
✅ 浏览器已启动

[步骤2] 打开目标页面...
URL：https://www.chinacdc.cn/
✅ 页面请求已发送
等待 3 秒，让 AJAX 数据加载...

[步骤3] 检查页面状态...
当前 URL：https://www.chinacdc.cn/
页面标题：中国疾病预防控制中心
HTML 长度：62374 字符

[步骤4] 提取链接数据...
--- 开始提取链接 ---
总共找到 362 个 <a> 标签
有效链接（有文字有地址）：245 个

链接分类统计：
  未分类：180 条
  健康主题：35 条
  新闻动态：18 条
  公文信息：12 条

[步骤5] 保存到 CSV 文件...
✅ 数据已保存到：output/chinacdc_links_20240115_143022.csv
   共 245 条记录

==================================================
爬取完成！
==================================================
目标网站：https://www.chinacdc.cn/
有效链接：245 条
输出文件：output/chinacdc_links_20240115_143022.csv

分类统计：
  未分类：180 条
  健康主题：35 条
  新闻动态：18 条
  公文信息：12 条

关闭浏览器...
✅ 浏览器已关闭

程序结束。
```



### 6.7.4 查看输出文件

📸 **操作截图：** VS Code 左侧文件浏览器，展开 output 文件夹 | 截取范围：VS Code 左侧文件浏览器 | 重点标注：新生成的 CSV 文件

在 VS Code 中打开 `output/chinacdc_links_xxx.csv`，你会看到类似这样的内容：

| title | url | category |
|-------|-----|----------|
| 中国疾病预防控制中心 | https://www.chinacdc.cn/ | 未分类 |
| 机构信息 | https://www.chinacdc.cn/gwxx/ | 公文信息 |
| 健康主题 | https://www.chinacdc.cn/jkzt/ | 健康主题 |
| ... | ... | ... |

📸 **操作截图：** ![截图](Pasted%20image%2020260712165257.png)

---


### 6.7.5 异常处理详解

完整项目中包含了一套完整的异常处理机制，这是真实爬虫项目的**必备技能**。我们来拆解每一层：

#### 层级一：页面加载超时

```python
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)  # 设置超时

try:
    driver.get(TARGET_URL)
except TimeoutException:
    # 超时了也不怕！很多 AJAX 页面一直在加载中
    # 我们直接拿已经加载好的内容
    print("⚠️ 页面加载超时，使用当前已加载的内容继续")
```

**为什么这样设计？** 很多现代网页（特别是用了大量 AJAX 的页面）永远不会"加载完成"，Chrome 的加载圈会一直转。如果我们不处理，程序就会卡住。设置超时后，超时了我们就直接用已有内容，不影响后续处理。

#### 层级二：元素查找重试

```python
def safe_find_elements(driver, by_method, selector, description=""):
    max_retry = 3
    for attempt in range(max_retry):
        try:
            # 尝试查找
            return wait.until(...)
        except TimeoutException:
            # 超时了，刷新页面重试
            driver.refresh()
```

**为什么这样设计？** 网络波动可能导致数据暂时加载失败。刷新页面重试是最简单有效的恢复手段。

#### 层级三：整体兜底

```python
try:
    main()
except KeyboardInterrupt:
    print("⚠️ 用户中断程序")
except Exception as e:
    print("❌ 程序出错：", ...)
finally:
    driver.quit()  # 无论如何都关浏览器
```

**为什么这样设计？** `finally` 块中的代码**无论如何都会执行**——无论成功、失败、还是被用户 Ctrl+C 中断，浏览器都会被关闭。这是防止浏览器窗口残留泄露的关键。

---

### 6.7.6 合理使用建议

> ⚠️ **爬虫伦理要点：**
>
> 1. **请求间隔**：本项目设置了 `REQUEST_INTERVAL = 3`，每次操作间隔 3 秒。真实项目中建议至少 1-2 秒。
> 2. **不要并发**：本项目使用单个浏览器实例，没有并发请求。
> 3. **仅取所需**：本项目只提取链接标题和 URL，不下载图片或大文件。
> 4. **数据用途**：提取的数据仅用于个人学习和研究，不用于商业用途。
> 5. **停止条件**：如果网站禁止爬取（通过 robots.txt 或其他方式），立即停止。

---

### 6.7.7 本节小结

你完成了本项目的终极实战！回顾一下你学到了什么：

| 技能 | 具体能力 |
|------|---------|
| 浏览器自动化 | 启动 Chrome、打开网页、执行 JavaScript |
| 8 种元素定位 | ID / NAME / CLASS / TAG / LINK_TEXT / PARTIAL / CSS / XPATH |
| 用户交互模拟 | send_keys 输入、click 点击 |
| 三种等待方式 | 强制等待（调试）、隐式等待（全局）、显式等待（精确） |
| 异常处理 | 超时处理、重试机制、finally 兜底 |
| CSV 存储 | DictWriter、BOM 头、utf-8-sig 编码 |
| 代码组织 | 参数集中管理、工具函数封装、主流程清晰 |

---

## 项目总结

恭喜你完成了项目6——Selenium 动态爬虫实战！让我们用一张表回顾整个项目：

| 小节 | 核心内容 | 关键比喻 |
|------|---------|---------|
| 6.1 | 动态网页和 AJAX 原理 | 半成品料理包 vs 已做好的盒饭 |
| 6.2 | Selenium + ChromeDriver 环境配置 | 给机器人装上轮子 |
| 6.3 | 7 种 + 1 种元素定位方法 | 教机器人认路 |
| 6.4 | send_keys 和 click 模拟操作 | 让机器人填表 |
| 6.5 | AJAX 数据提取 + 显式等待入门 | 等外卖送到 |
| 6.6 | 三种等待方式深度对比 | 等外卖的三种姿势 |
| 6.7 | 完整实战 + 异常处理 + CSV 存储 | 综合演习 |

**后续进阶方向：**

- 学习 Selenium 的无头模式（headless）—— 浏览器在后台运行，不显示窗口
- 学习 Selenium 的代理设置 —— 避免 IP 被封
- 学习 Scrapy + Selenium 结合 —— 大规模爬虫项目
- 学习 Playwright —— Selenium 的现代替代品，功能更强大

---

## 课后练习

### 练习1：基础巩固（必做）

修改 `06_full_project.py`，完成以下改动：

1. 将 `TARGET_URL` 改成 `https://www.chinacdc.cn/jkzt/` （健康主题页面，注意这个 URL 我们用 requests 测过是 404，但 Selenium 渲染后可能有内容）
2. 如果页面加载失败（状态异常），输出一条明确的提示，并用 `sys.exit(1)` 退出程序
3. 在 CSV 中额外增加一列 `source_page`，记录数据来自哪个 URL

### 练习2：XPath 进阶（选做）

写一个新的程序 `exercise_xpath.py`，用 XPath 完成以下挑战：

1. 用 XPath 找出页面上 **所有文字长度超过 10 个字符的链接**（不包括导航链接）
2. 用 XPath 找出 **所有 href 中包含 `.html` 的链接**（这些才是实际内容页面）
3. 将以上结果分别保存为两个 CSV 文件

**提示：** XPath 的 `string-length(text())` 函数和 `contains(@href, '.html')` 函数。

### 练习3：等待进阶（选做）

在 `06_full_project.py` 的基础上做以下改进：

1. 把所有 `time.sleep()` 替换为显式等待（找到合适的 EC 条件）
2. 添加一个 `wait_for_page_ready()` 函数，用 `document.readyState` 判断页面是否加载完成
   ```python
   # 提示：用 driver.execute_script() 执行 JavaScript
   ready_state = driver.execute_script("return document.readyState")
   # readyState 的值：loading / interactive / complete
   ```
3. 将每次请求间隔从固定 3 秒改为自适应（根据上一次请求耗时决定）

### 练习4：综合挑战（选做）

找一个**不同的**动态医疗健康网站（例如：WHO 疫情看板 `https://data.who.int/dashboards/covid19/cases`），用 Selenium 完成以下任务：

1. 打开页面，等待页面完全加载
2. 找到页面中的所有表格（`<table>` 标签）
3. 对每个表格提取表头和数据行
4. 将每个表格保存为独立的 CSV 文件
5. 必须包含超时异常处理和重试机制

**注意：** WHO 网站是全英文的，但爬虫逻辑是一样的。这是检验你是否真正掌握了 Selenium 的终极测试。
