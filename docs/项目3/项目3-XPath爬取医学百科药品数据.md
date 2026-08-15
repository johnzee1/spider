# 项目3：用 XPath 爬取 A+医学百科药品数据

> 难度：★★★☆☆ | 前置知识：BeautifulSoup 基础、Python 基础语法 | 预计学时：4-6 小时

---

## 合规提示

在开始爬取之前，请先阅读并遵守以下规则：

1. **遵守 robots 协议**。A+医学百科的 `robots.txt`（地址：`http://www.a-hospital.com/robots.txt`）允许搜索引擎索引，但建议我们保持礼貌。
2. **控制请求频率**。每次请求之间至少间隔 2-3 秒，不要给服务器造成压力。
3. **仅爬取公开数据**。本教程只涉及网站上公开可见的药品分类、药品名称、适应症等非隐私信息。
4. **学习目的**。本教程中的所有代码仅供学习 XPath 和 Python 爬虫技术使用，请勿用于商业用途。

---

## 3.1 项目任务：认识 XPath

### 3.1.1 什么是 XPath？

想象你在一个巨大的快递分拣中心工作。你的面前堆满了包裹，你需要从里面找到「收件人是张三的那个红色包裹」。你怎么描述这个位置？

- 「从门口开始，走到第 3 排货架，在第 2 层，从左数第 5 个包裹」——这是一条**路径**。
- 「所有红色包裹中，收件人叫张三的那个」——这是一条**筛选条件**。

XPath 做的事情，和你在快递分拣中心做的一模一样。只不过包裹变成了 HTML 标签，货架变成了 DOM 树。

**XPath（XML Path Language）**是一种在 XML 或 HTML 文档中定位元素的语言。它通过「路径表达式」来描述你想找的标签在文档中的位置。

### 3.1.2 为什么学完 BeautifulSoup 还要学 XPath？

这是一个好问题。让我们用一个比喻来理解：

| 对比维度 | CSS 选择器（BeautifulSoup） | XPath |
|---------|---------------------------|-------|
| 比喻 | 用「外貌特征」找人：穿红衣服的、戴眼镜的 | 用「地址」找人：3 楼 5 号房间 |
| 查找方向 | 只能向下找（父→子） | 可以向上找、向旁边找（子→父、兄弟节点） |
| 文本匹配 | 不支持直接按文本内容查找 | 支持 `text()` 函数精确匹配文本 |
| 属性匹配 | 支持，但条件组合有限 | 支持任意属性、任意条件组合 |
| 学习成本 | 低（你已掌握） | 中等（本项目要学的内容） |

**XPath 的核心优势**：你可以从一个元素「反向」找到它的父元素，或者「横向」找到它的兄弟元素。这在爬取复杂页面时非常有用。

举个例子：你想爬取一个药品名称，但这个名称没有 class 也没有 id。它的 HTML 结构是这样的：

```html
<tr>
    <td>青霉素</td>
    <td>抗生素</td>
    <td>华北制药</td>
</tr>
```

用 CSS 选择器，你只能这样写：`soup.select('tr td:nth-child(1)')`。但如果表格结构变了（比如多加了一列），你的代码就失效了。

用 XPath，你可以这样写：`//tr/td[contains(text(), '青霉素')]`——直接按文字内容匹配，不受列位置变化影响。

### 3.1.3 本项目的目标

- **目标网站**：A+医学百科（`http://www.a-hospital.com/`）
- **爬取内容**：药品分类列表、药品名称、适应症、生产厂家、药品属性
- **技术栈**：Python + `requests` + `lxml`（XPath）+ `sqlite3`
- **最终产出**：一个包含药品分类数据的 SQLite 数据库

> **为什么选择 A+医学百科？**
> 
> 我们在写本教程之前，测试了多个医疗公开数据网站：
> - 国家药品监督管理局（NMPA）：返回 HTTP 412，有严格反爬
> - 国家医保局：列表数据通过 AJAX 动态加载，不适合纯静态爬虫教学
> - 药智网：返回 HTTP 403，直接拒绝爬虫
> - 39健康网：连接不稳定，经常断开
> - **A+医学百科**：纯静态 HTML 页面，表格结构清晰，无验证码，是学习 XPath 的理想目标

---

## 3.2 安装 lxml 并装载网页

### 3.2.1 什么是 lxml？

`lxml` 是 Python 中处理 XML 和 HTML 的库。它包含两个重要模块：

- `etree`：用于解析 XML/HTML 并支持 XPath 查询
- `html`：专门用于处理 HTML（会自动修复不规范的 HTML）

简单来说，`lxml` 就是 XPath 的「执行引擎」。你写 XPath 表达式，`lxml` 帮你找到对应的元素。

### 3.2.2 安装 lxml

📸 操作截图：打开 VS Code 终端窗口 | 截取范围：VS Code 窗口底部 Terminal 面板 | 重点标注：红框圈出输入的命令行

**操作步骤：**

1. 打开 VS Code，点击顶部菜单 **Terminal → New Terminal**（或按快捷键 `Ctrl + `` `）打开终端
2. 在终端中输入以下命令：
3. 输入：`pip install lxml`
4. 按 **Enter** 键执行
5. 等待安装完成，看到 `Successfully installed lxml-x.x.x` 即为成功

```
pip install lxml
```

安装完成后，我们还需要 `requests` 库来发送 HTTP 请求：

```
pip install requests
```


### 3.2.3 装载网页：从 URL 到可查询的 HTML 树

让我们写出第一段代码，用 `lxml` 加载一个网页并开始用 XPath 查询。

VS Code 新建 Python 文件----`project3_xpath.py` 文件

```python
"""
项目3：用 XPath + lxml 爬取 A+医学百科药品数据
第一步：加载网页，验证 XPath 可用
"""

# 导入 requests 库
# 它用来发送 HTTP 请求，获取网页的 HTML 内容
import requests

# 从 lxml 库中导入 etree 模块
# etree 是 lxml 的核心模块，负责解析 HTML 并支持 XPath 查询
# 参数说明：import 后面写库名.模块名
# 返回：无返回值，导入后可以直接使用 etree.xxx() 方法
from lxml import etree

# 第一步：定义要爬取的网址
# 我们爬取 A+医学百科的「青霉素类药物」分类页面
# 这个页面有一个表格，列出了所有青霉素类药物的分类和代表药品
url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"

# 第二步：设置请求头，伪装成浏览器
# 很多网站会检查请求头，如果没有 User-Agent，可能被拒绝
# User-Agent 告诉服务器「我是什么浏览器」
headers = {}
headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
# Referer 告诉服务器「我从哪个页面跳转过来的」
# 设置 Referer 可以让请求看起来更自然
headers["Referer"] = "http://www.a-hospital.com/"

# 第三步：发送 GET 请求
# requests.get() 方法：向指定 URL 发送 GET 请求
# 参数1 url：要请求的网址（字符串）
# 参数2 headers：请求头（字典）
# 参数3 timeout：超时时间（秒），如果超过这个时间服务器没响应，就报错
# 返回：一个 Response 对象，包含服务器返回的所有信息
print("正在请求网页...")
response = requests.get(url, headers=headers, timeout=15)
print("请求完成！")

# 第四步：检查请求是否成功
# response.status_code：HTTP 状态码，200 表示成功
# 如果状态码不是 200，说明请求失败了
if response.status_code == 200:
    print("状态码: 200，请求成功")
else:
    print("状态码: " + str(response.status_code) + "，请求可能有问题")

# 第五步：获取网页的 HTML 文本
# response.text：服务器返回的 HTML 内容（字符串格式）
# 注意：某些网站的编码可能不是 UTF-8，这里使用 apparent_encoding 自动检测
# response.encoding：设置编码方式，确保中文不乱码
response.encoding = response.apparent_encoding
html_text = response.text
print("HTML 内容长度: " + str(len(html_text)) + " 个字符")

# 第六步：用 lxml 解析 HTML
# etree.HTML() 方法：把 HTML 字符串解析成一棵「元素树」
# 参数：html_text —— HTML 字符串
# 返回：一个 Element 对象，代表整个 HTML 文档的根节点
# 注意：lxml 会自动修复不规范的 HTML（比如缺少闭合标签）
html_tree = etree.HTML(html_text)
print("HTML 解析完成！")

# 第七步：测试 XPath —— 提取页面标题
# html_tree.xpath() 方法：在 HTML 树中执行 XPath 查询
# 参数：一个 XPath 表达式（字符串）
# 返回：一个列表，包含所有匹配的元素
# 如果没找到任何匹配，返回空列表 []

# 这段 XPath 的意思是：在整个文档中（//）找 h1 标签，
# 并且要求 h1 的 id 属性等于 "firstHeading"
title_list = html_tree.xpath('//h1[@id="firstHeading"]/text()')
print("页面标题: " + str(title_list))

# 第八步：获取标题文本
# title_list 是一个列表，我们用索引 [0] 取第一个元素
if len(title_list) > 0:
    page_title = title_list[0]
    print("成功提取标题: " + page_title)
else:
    print("未找到标题")
```

📸 操作截图：![截图](Pasted%20image%2020260712083049.png)

### 3.2.4 代码逐行解读

我们花了比较多的代码来完成「加载网页」这个看似简单的任务。每一行都有它的作用：

| 代码行 | 作用 | 如果是 BeautifulSoup 你会怎么写 |
|--------|------|-------------------------------|
| `import requests` | 导入 HTTP 请求库 | 相同 |
| `from lxml import etree` | 导入 lxml 解析器 | `from bs4 import BeautifulSoup` |
| `requests.get(url, headers, timeout)` | 发送请求获取网页 | 相同 |
| `response.encoding = ...` | 设置编码防乱码 | 相同 |
| `etree.HTML(html_text)` | 解析 HTML 为元素树 | `BeautifulSoup(html_text, 'html.parser')` |
| `html_tree.xpath('...')` | 执行 XPath 查询 | `soup.select('...')` 或 `soup.find(...)` |

核心区别只有两步：**解析方式**和**查询方式**。BeautifulSoup 用 `soup.select()`，lxml 用 `tree.xpath()`。

---

## 3.3 XPath 基本语法

### 3.3.1 路径语法：`/` 与 `//` 的区别

这是 XPath 最基础也是最重要的概念。我们用「地图导航」来比喻：

#### 绝对路径：`/`

好比你说：「从北京天安门出发，沿着长安街往西走 500 米，右转进入西单北大街，再走 200 米，左手边就是。」

**你必须从起点开始，一步一步描述路径。**如果中间任何一个「地标」变了，整条路就作废了。

```python
# 绝对路径示例
# 从 html 根节点开始，一步一步往下找
# /html/body/div[2]/table/tr[1]/td[1]
# 这个路径的意思是：
#   html 标签
#     → body 标签
#       → 第2个 div 标签
#         → 第一个 table 标签
#           → 第1行 tr
#             → 第1列 td
path_absolute = "/html/body/div[2]/table/tr[1]/td[1]"
```

#### 相对路径：`//`

好比你说：「附近有没有麦当劳？」

**不管你在哪里，只要在文档的任何位置找到这个元素就行。**不限层级，不限位置。

```python
# 相对路径示例
# //table 的意思是：在整个文档中，找到所有 table 标签，不管它们嵌套在多少层里面
path_relative = "//table"
```

#### 对比总结

| 写法 | 含义 | 比喻 | 什么时候用 |
|------|------|------|-----------|
| `/html/body/div` | 从根开始，严格按照层级 | 从天安门导航 | 你知道精确的层级结构，且结构不会变 |
| `//div` | 跳过层级，找所有匹配 | 搜附近的麦当劳 | 不知道层级，或结构可能变化 |

**实际爬虫中，95% 的情况都用 `//`。** 因为网页结构经常调整，绝对路径太脆弱了。

### 3.3.2 Chrome 开发者工具复制 XPath

这是最实用的技巧之一。Chrome 浏览器可以帮你自动生成 XPath 表达式。


📸 操作截图：![截图](Pasted%20image%2020260712083526.png)

📸 操作截图：![截图](Pasted%20image%2020260712083707.png)

**操作步骤：**

1. 打开 Chrome 浏览器，访问 `http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9`
2. 在页面上找到「分类 | 代表药品」那个表格
3. 右键点击表格中的任意位置（比如「天然青霉素类」这几个字）
4. 在弹出的菜单中选择**「检查」**（Inspect）
5. Chrome 开发者工具会自动打开，并高亮显示你点击的 HTML 元素
6. 在高亮的 HTML 代码行上**右键**，选择**Copy → Copy XPath**
7. 粘贴到你的代码中，你会得到类似这样的 XPath：
   ```
   //*[@id="bodyContent"]/table[2]/tbody/tr[2]/td[1]
   ```



> ⚠️ **重要提示**：Chrome 生成的 XPath 是**绝对路径**（从 `id="bodyContent"` 开始一步一步往下），非常脆弱。如果网页多加了一行表格，路径就失效了。
> 
> **最佳实践**：先复制 Chrome 的 XPath，**理解它的结构**，然后自己改写为相对路径。比如把上面那个改成：
> ```
> //table[@class="wikitable"]//tr/td[1]
> ```

### 3.3.3 按属性查找：`@` 符号

`@` 是 XPath 中的「属性前缀」。你可以用它来匹配任何 HTML 属性。

用快递分拣的比喻：`@` 就是快递单上的标签——「收件人」「寄件人」「包裹重量」等。

```python
"""
XPath 属性查找示例
"""

import requests
from lxml import etree

url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# ============================================
# 属性查找的各种写法
# ============================================

# 写法1：精确匹配 class 属性
# [@class="wikitable"] 的意思是：class 属性的值必须完全等于 "wikitable"
# 注意：如果 class 有多个值（如 class="wikitable sortable"），这样写会匹配失败！
tables = html_tree.xpath('//table[@class="wikitable"]')
print("精确匹配 class='wikitable' 的表格数量: " + str(len(tables)))

# 写法2：匹配任意属性
# 你也可以匹配 id、href、src 等任何属性
# 找到所有 href 属性包含 "药品" 的链接
links = html_tree.xpath('//a[contains(@href, "药品")]')
print("href 包含'药品'的链接数量: " + str(len(links)))

# 写法3：匹配多个属性
# 同时要求 class 和 id 都满足
# and 关键字：两个条件都要满足
elements = html_tree.xpath('//div[@class="content" and @id="main"]')
print("同时满足 class 和 id 的元素数量: " + str(len(elements)))

# 写法4：获取属性值
# 找到所有链接的 href 属性值
# 注意：/@href 是取属性值，不是取元素
all_hrefs = html_tree.xpath('//a/@href')
print("页面上所有链接的 href 属性数量: " + str(len(all_hrefs)))
# 打印前5个链接
for href in all_hrefs[:5]:
    print("  链接: " + href)
```

📸 操作截图：![截图](Pasted%20image%2020260712084034.png)
### 3.3.4 获取文本内容：`text()` 函数

`text()` 是 XPath 中获取元素文本内容的函数。它拿到的是元素内部**直接包含的文本**。

```python
"""

text() 函数用法示例

"""

import requests

from lxml import etree

  
url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# ============================================
# text() 的各种用法
# ============================================
# 用法1：获取表格中所有 th 标签的文本（表头）
# //th/text() 的意思是：找到所有 th 标签，取它们的文本内容

header_texts = html_tree.xpath('//table[@class="wikitable"]//th/text()')
print("表格表头: " + str(header_texts))
  
# 用法2：获取第一行（td[1]）的所有文本

# //table[@class="wikitable"]//tr[2]/td/a/text()
first_hang = html_tree.xpath('//table[@class="wikitable"]//tr[2]/td/a/text()')

print("第一行药品）: " + str(first_hang))

# 用法3：获取第二行（tr[2]）的所有文本
second_hang = html_tree.xpath('//table[@class="wikitable"]//tr[3]/td/a/text()')
print("第二行药品: " + str(second_hang))

# 用法4：text() 只取「直接文本」，不包含子元素中的文本

# 举例说明：

# <td>青霉素<a href="...">详情</a></td>

# td/text() 只返回 "青霉素"，不返回子元素 a 标签中的 "详情"

# 如果要获取包含子元素的所有文本，用 string() 函数（稍后介绍）
```

📸 操作截图：![截图](Pasted%20image%2020260712091127.png)
### 3.3.5 处理动态 class：`contains()` 函数

网页的 class 属性经常变化，比如：
- `class="list-item-12345"`（后面带数字）
- `class="drug-card active"`（多个 class 值）
- `class="drug_card_v2"`（版本号）

`contains()` 函数可以帮你应对这种变化。它检查字符串是否**包含**某个子串，而不是精确匹配。

```python
"""
contains() 函数用法示例
"""

import requests
from lxml import etree

url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# ============================================
# contains() —— 处理动态 class
# ============================================

# 场景1：class 有多个值，如 class="navbox hlist"
# 用精确匹配 [@class="navbox"] 会失败，因为 class 的值是 "navbox hlist"
# 用 contains() 就能匹配
tables_contains = html_tree.xpath('//table[contains(@class, "navbox")]')
print("class 包含 'navbox' 的表格数量: " + str(len(tables_contains)))

# 场景2：找包含特定文字的链接
# 找到所有文本内容包含「青霉素」的链接
penicillin_links = html_tree.xpath('//a[contains(text(), "青霉素")]')
print("文本包含'青霉素'的链接数量: " + str(len(penicillin_links)))
for link in penicillin_links:
    # 获取链接文本
    link_text = link.xpath('text()')
    # 获取链接地址
    link_href = link.xpath('@href')
    if len(link_text) > 0 and len(link_href) > 0:
        print("  " + link_text[0] + " -> " + link_href[0])

# 场景3：contains() 用于属性值
# 找到所有 href 属性包含 "药品" 的链接
drug_links = html_tree.xpath('//a[contains(@href, "%E8%8D%AF")]/@href')
print("href 包含'药品'相关编码的链接数量: " + str(len(drug_links)))

# 场景4：contains() 用于文本内容
# 找到所有段落中包含「抗生素」的
antibiotic_paras = html_tree.xpath('//p[contains(text(), "抗生素")]')
print("包含'抗生素'的段落数量: " + str(len(antibiotic_paras)))
```

📸 操作截图：![截图](Pasted%20image%2020260712091239.png)
#### `contains()` 与精确匹配的对比

| 写法 | 含义 | 适用场景 |
|------|------|----------|
| `[@class="wikitable"]` | class 必须完全等于 "wikitable" | class 值固定不变 |
| `[contains(@class, "wikitable")]` | class 包含 "wikitable" 即可 | class 可能有多个值，或动态变化 |
| `[contains(text(), "青霉素")]` | 文本内容包含 "青霉素" | 不确定文本的完整内容 |

### 3.3.6 XPath 轴（Axes）：向上、向旁边找元素

XPath 最强大的特性之一就是**轴**。它允许你从当前元素出发，向任意方向查找：

| 轴名称 | 方向 | 含义 | 比喻 |
|--------|------|------|------|
| `parent::` | 向上 | 找父元素 | 从你的办公室找到你所在的楼层 |
| `child::` | 向下 | 找子元素 | 从楼层找到这层所有办公室 |
| `following-sibling::` | 向右 | 找后面的兄弟元素 | 从你的办公室找到隔壁的办公室 |
| `preceding-sibling::` | 向左 | 找前面的兄弟元素 | 从你的办公室找到左边的办公室 |
| `ancestor::` | 一直向上 | 找所有祖先元素 | 从你的办公室找到整栋楼 |

```python
"""
XPath 轴（Axes）用法示例
"""

import requests
from lxml import etree

url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# ============================================
# 轴的使用示例
# ============================================

# 场景：找到文本是「分类」的 th 标签，然后找到它所在的 tr 下面所有的 td
# 这个场景在实际爬虫中非常常见——你通过某个关键词定位到一行，然后提取这一行的其他数据

# 第一步：找到包含「分类」文字的 th 标签
# 注意：这里用 . 开头的相对 XPath，而不是重复 //th
category_th = html_tree.xpath('//th[contains(text(), "分类")]')
print("找到包含'分类'的 th 标签数量: " + str(len(category_th)))

if len(category_th) > 0:
    # 第二步：从这个 th 出发，向上找父元素 tr
    # parent::tr 就是「向上找 tr 标签」
    parent_row = category_th[0].xpath('parent::tr')
    print("父元素 tr 数量: " + str(len(parent_row)))
    
    if len(parent_row) > 0:
        # 第三步：在父元素内，向下找所有 td
        # child::td 的意思是「找直接子元素中的 td」
        td_cells = parent_row[0].xpath('child::td')
        print("子元素 td 数量: " + str(len(td_cells)))
        
        for i, td in enumerate(td_cells):
            td_text = td.xpath('text()')
            if len(td_text) > 0:
                print("  第" + str(i+1) + "列: " + td_text[0].strip()[:50])

# ============================================
# following-sibling 示例
# ============================================

# 找到「分类」th 后面的兄弟 th（同一行中后面的列头）
sibling_th = html_tree.xpath('//th[contains(text(), "分类")]/following-sibling::th')
print("'分类'后面的兄弟 th 数量: " + str(len(sibling_th)))
for th in sibling_th:
    th_text = th.xpath('text()')
    if len(th_text) > 0:
        print("  兄弟列头: " + th_text[0])
```

📸 操作截图：![截图](Pasted%20image%2020260712091329.png)
### 3.3.7 XPath 在线测试工具

在实际写爬虫之前，你可以在浏览器中测试 XPath 表达式，确保它们正确。推荐两个工具：

#### 工具1：Chrome 开发者工具自带（推荐）

📸 操作截图：Chrome Console 中输入 XPath | 截取范围：Chrome 开发者工具 Console 面板 | 重点标注：红框圈出 `$x()` 表达式和返回结果

**操作步骤：**

1. 在 Chrome 中打开目标页面
2. 按 `F12` 打开开发者工具
3. 点击 **Console** 标签
4. 输入 `$x('你的 XPath 表达式')`，按 Enter
5. 浏览器会返回匹配的元素列表

例如：
```javascript
// 在 Chrome Console 中测试 XPath
$x('//table[@class="wikitable"]//tr/td[1]/text()')
// 返回所有匹配的文本节点
```

📸 操作截图：
![截图](Pasted%20image%2020260712092924.png)

#### 工具2：XPath Helper 浏览器插件

📸 操作截图：
![截图](Pasted%20image%2020260712093434.png)
![截图](Pasted%20image%2020260712093451.png)

![截图](Pasted%20image%2020260712094008.png)


![截图](Pasted%20image%2020260712094035.png)

**安装步骤：**

1. 打开 Chrome 应用商店（需要科学上网）
2. 搜索「XPath Helper」
3. 点击「添加至 Chrome」
4. 安装完成后，地址栏右侧会出现 XPath Helper 图标

📸 操作截图：![截图](Pasted%20image%2020260712094445.png)

**使用方法：**

1. 打开目标网页
2. 点击 XPath Helper 图标
3. 在左侧 **Query** 输入框中输入 XPath 表达式
4. 右侧 **Results** 区域会实时显示匹配结果
5. 匹配到的元素在网页上会高亮显示

### 3.3.8 常见 XPath 报错及解决方案

新手在使用 XPath 时，最常遇到的是 `IndexError: list index out of range`。这个错误不是说 XPath 写错了，而是**没有匹配到任何元素，返回了空列表，你却试图取空列表的第一个元素**。

```python
"""
常见 XPath 错误及解决方案
"""

import requests
from lxml import etree

url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# ============================================
# 错误1：IndexError: list index out of range
# ============================================

# 错误写法：直接取索引 [0]，不做检查
# 如果 XPath 没匹配到任何元素，result 是空列表 []，result[0] 就会报错
# result = html_tree.xpath('//table[@class="不存在的class"]//tr/td[1]/text()')
# first_item = result[0]  # 这里会报错 IndexError！

# 正确写法：先检查列表长度，再取索引
result = html_tree.xpath('//table[@class="不存在的class"]//tr/td[1]/text()')
if len(result) > 0:
    first_item = result[0]
    print("找到数据: " + first_item)
else:
    print("未找到匹配数据，请检查 XPath 表达式")

# ============================================
# 错误2：命名空间问题
# ============================================

# 有些网页的 HTML 标签带有命名空间，如 <html xmlns="...">
# 这时候直接用 //div 可能匹配不到
# 解决方案：使用本地名称匹配
# elements = html_tree.xpath('//*[local-name()="div"]')

# ============================================
# 错误3：text() 返回空字符串
# ============================================

# 原因：元素内部有子元素，文本在子元素中
# 比如 <td><a href="...">青霉素</a></td>
# td/text() 返回空，因为文本在子元素 a 里面
# 解决方案：用 //td//text()（注意是双斜杠）获取所有后代文本
# 或者用 string() 函数

# 对比演示
# 假设 HTML 结构是：
# <td class="drug-name"><a href="/drug/123">青霉素</a></td>

# 写法1：td/text() → 返回空（直接文本在 a 标签里）
# 写法2：td//text() → 返回 ["青霉素"]（取了所有后代文本）
# 写法3：string(//td[@class="drug-name"]) → 返回 "青霉素"

# ============================================
# 错误4：XPath 语法错误
# ============================================

# 常见语法错误：
# 1. 忘记加 @ 符号：//a[href="..."] → 正确：//a[@href="..."]
# 2. 忘记加引号：//div[@class=content] → 正确：//div[@class="content"]
# 3. 路径末尾多写 /：//table//tr/ → 正确：//table//tr
# 4. text() 后面加东西：//td/text()/something → 错误！text() 是终点

print("XPath 错误演示完成")
```

📸 操作截图：![截图](Pasted%20image%2020260712094541.png)
### 3.3.9 定位药品名称、适应症、生产企业

现在我们把前面学的内容整合起来，在 A+医学百科上实战定位药品信息。

```python
"""
实战：用 XPath 定位药品信息
目标页面：A+医学百科 - 青霉素类药物
"""

import requests
from lxml import etree

# 第一步：加载页面
url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://www.a-hospital.com/"
}
print("正在请求: " + url)
response = requests.get(url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)
print("页面加载完成，大小: " + str(len(response.text)) + " 字符")

# ============================================
# 第二步：提取药品分类和代表药品
# ============================================

# 找到 wikitable 表格中的所有行
# 注意：这个表格的实际结构是每行只有一个 td
# td 里面用 <a> 标签列出每种药品，药品之间用顿号「、」分隔
all_rows = html_tree.xpath('//table[@class="wikitable"]//tr')
print("表格行数: " + str(len(all_rows)))

# 遍历每一行，提取分类和药品名称
drug_data = []
for row in all_rows:
    # 第一步：提取这一行的 th 标签文本（分类名称）
    # th 标签内容是「天然青霉素类」「耐青霉素酶青霉素类」等
    th_list = row.xpath('th//text()')
    
    # 第二步：提取这一行 td 的完整文本（代表药品）
    # 用 string() 函数可以拿到 td 内所有文本的拼接
    # 结果是「青霉素、普鲁卡因青霉素、苄星青霉素...」这样的字符串
    td_list = row.xpath('td')
    
    # 检查是否都提取到了内容
    if len(th_list) > 0 and len(td_list) > 0:
        # th 的文本是分类名
        category_name = th_list[0]
        category_name = category_name.strip()
        
        # 用 string() 获取 td 的完整文本（包含所有 a 标签中的药品名+顿号）
        drug_names = td_list[0].xpath("string()")
        drug_names = drug_names.strip()
        
        # 跳过表头行（分类名为「分类」的就是表头）
        if category_name == "分类":
            continue
        
        # 存入列表
        drug_data.append({"分类": category_name, "代表药品": drug_names})

# 第三步：打印提取结果
print("共提取到 " + str(len(drug_data)) + " 条药品分类数据")
print("")
for item in drug_data:
    print("分类: " + item["分类"])
    print("  代表药品: " + item["代表药品"])
    print("")

# ============================================
# 第四步：提取页面中所有药品链接
# ============================================

# 找到所有 a 标签，它们的文本中包含药品关键词
# //a：所有 a 标签
# [contains(text(), ...)]：文本内容包含指定关键词
all_drug_links = html_tree.xpath('//a[contains(text(), "素") or contains(text(), "青霉素") or contains(text(), "头孢")]')
print("找到药品相关链接: " + str(len(all_drug_links)) + " 个")

for link in all_drug_links[:10]:
    # 提取链接文本
    link_text_list = link.xpath('text()')
    # 提取链接 href
    link_href_list = link.xpath('@href')
    
    if len(link_text_list) > 0 and len(link_href_list) > 0:
        link_text = link_text_list[0]
        link_href = link_href_list[0]
        
        # 拼出完整 URL（如果是相对路径）
        if link_href.startswith('/'):
            full_url = "http://www.a-hospital.com" + link_href
        else:
            full_url = link_href
        
        print("  药品: " + link_text + " -> " + full_url)
```

📸 操作截图：![截图](Pasted%20image%2020260712094932.png)

---

## 3.4 完整实战：爬取多页药品数据并存入 SQLite

### 3.4.1 项目整体设计

在开始写代码之前，我们先梳理清楚这个完整项目的结构：

```
项目流程：
┌─────────────────────────────────────────────────┐
│  1. 从分类列表页提取所有药品分类的链接          │
│     ↓                                           │
│  2. 遍历每个分类链接，进入分类详情页            │
│     ↓                                           │
│  3. 在每个分类详情页中提取表格数据              │
│     ↓                                           │
│  4. 对提取的数据进行去重处理                    │
│     ↓                                           │
│  5. 将数据存入 SQLite 数据库                    │
│     ↓                                           │
│  6. 从数据库读取数据，验证结果                  │
└─────────────────────────────────────────────────┘
```

### 3.4.2 爬取多个药品分类页面

我们先爬取几个不同的药品分类页面，演示多页爬取。

```python
"""
完整实战：爬取 A+医学百科多页药品分类数据
第一步：爬取多个分类页面
"""

import requests
from lxml import etree
# 导入 time 模块，用于控制请求间隔
# time.sleep() 函数：让程序暂停执行指定的秒数
# 参数：秒数（可以是小数，如 0.5 表示半秒）
import time

# 定义要爬取的药品分类页面列表
# 每个分类页面都有 wikitable 表格，包含子分类和代表药品
category_urls = [
    {
        "name": "青霉素类药物",
        "url": "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
    {
        "name": "头孢菌素类药物",
        "url": "http://www.a-hospital.com/w/%E5%A4%B4%E5%AD%A2%E8%8F%8C%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
    {
        "name": "大环内酯类药物",
        "url": "http://www.a-hospital.com/w/%E5%A4%A7%E7%8E%AF%E5%86%85%E9%85%AF%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
]

# 设置请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://www.a-hospital.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 存储所有提取到的药品数据
# 用一个列表来装所有数据，每条数据是一个字典
all_drugs = []

# 遍历每个分类页面
for category in category_urls:
    category_name = category["name"]
    category_url = category["url"]
    
    print("=" * 60)
    print("正在爬取: " + category_name)
    print("URL: " + category_url)
    
    # 发送请求
    # 用 try/except 可以捕获网络错误，不会因为一个页面失败就让整个程序崩溃
    try:
        response = requests.get(category_url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        
        # 检查是否成功
        if response.status_code != 200:
            print("  请求失败，状态码: " + str(response.status_code))
            continue  # 跳过这个页面，继续下一个
        
        # 解析 HTML
        html_tree = etree.HTML(response.text)
        
        # 第一步：提取表格中的所有行
        all_rows = html_tree.xpath('//table[@class="wikitable"]//tr')
        print("  找到 " + str(len(all_rows)) + " 行数据")
        
        # 第二步：遍历每一行，提取数据
        for row in all_rows:
            # 提取这一行的 th 标签文本（子分类名称）
            # 注意：每个 tr 包含一个 th（分类名）和一个 td（药品列表）
            col1_list = row.xpath('th//text()')
            
            # 提取这一行的 td 标签，用 string() 获取完整药品列表文本
            td_list = row.xpath('td')
            
            # 检查是否都提取到了
            if len(col1_list) > 0 and len(td_list) > 0:
                sub_category = col1_list[0].strip()
                # 用 td.xpath("string()") 获取 td 内所有文本的拼接
                # 效果：'青霉素、普鲁卡因青霉素、苄星青霉素...'
                drug_names = td_list[0].xpath("string()")
                drug_names = drug_names.strip()
                
                # 跳过表头行（如果第一列是「分类」）
                if sub_category == "分类":
                    continue
                
                # 构造一条数据记录
                record = {
                    "大类": category_name,
                    "子类": sub_category,
                    "代表药品": drug_names,
                    "来源URL": category_url
                }
                
                all_drugs.append(record)
                print("  提取: " + sub_category + " → " + drug_names[:50])
        
        print("  本页提取完成，共 " + str(len(all_drugs)) + " 条记录")
        
    except Exception as e:
        print("  爬取失败: " + str(e))
    
    # 控制请求间隔：每次请求后等待 2 秒
    # 这是爬虫的基本礼仪，避免给服务器造成压力
    print("  等待 2 秒后再请求下一个页面...")
    time.sleep(2)

print("=" * 60)
print("全部爬取完成！")
print("共提取 " + str(len(all_drugs)) + " 条药品数据")
```

📸 操作截图：![截图](Pasted%20image%2020260712095205.png)

### 3.4.3 数据去重

在爬取多个页面时，可能会遇到同一个药品在多个分类中出现的情况。比如「青霉素」可能同时出现在「青霉素类药物」和「抗生素」两个分类中。

我们需要对数据进行去重。

```python
"""
数据去重处理
"""

# 假设 all_drugs 是上面爬取到的所有数据
# 去重策略：以「代表药品」字段作为去重依据

# 第一步：创建一个集合，用来记录已经见过的药品名
# 集合（set）的特点：同一个元素只会出现一次
seen_drugs = set()

# 第二步：创建一个新列表，存储去重后的数据
unique_drugs = []

# 第三步：遍历所有数据，只保留第一次出现的
for record in all_drugs:
    drug_name = record["代表药品"]
    
    # 检查这个药品名是否已经出现过
    if drug_name not in seen_drugs:
        # 第一次出现：记录到集合中
        seen_drugs.add(drug_name)
        # 保存到去重后的列表
        unique_drugs.append(record)
    else:
        # 已经出现过：跳过
        print("  跳过重复: " + drug_name)

# 第四步：打印去重结果
print("去重前数据量: " + str(len(all_drugs)) + " 条")
print("去重后数据量: " + str(len(unique_drugs)) + " 条")
print("重复数据量: " + str(len(all_drugs) - len(unique_drugs)) + " 条")

# 第五步：更智能的去重 —— 如果药品名相同但分类不同，合并分类信息
# 这种方法适合需要保留多维分类信息的场景
merged_drugs = {}

for record in all_drugs:
    drug_name = record["代表药品"]
    
    if drug_name not in merged_drugs:
        # 第一次出现：直接存储
        merged_drugs[drug_name] = {
            "代表药品": drug_name,
            "大类列表": [record["大类"]],
            "子类列表": [record["子类"]]
        }
    else:
        # 已经出现过：合并分类信息
        # 检查大类是否已存在，不存在才添加
        if record["大类"] not in merged_drugs[drug_name]["大类列表"]:
            merged_drugs[drug_name]["大类列表"].append(record["大类"])
        # 检查子类是否已存在，不存在才添加
        if record["子类"] not in merged_drugs[drug_name]["子类列表"]:
            merged_drugs[drug_name]["子类列表"].append(record["子类"])

# 打印合并后的结果
print("")
print("合并后数据量: " + str(len(merged_drugs)) + " 条")
print("")
print("前5条合并数据:")
count = 0
for drug_name, info in merged_drugs.items():
    if count >= 5:
        break
    print("药品: " + drug_name)
    print("  大类: " + "、".join(info["大类列表"]))
    print("  子类: " + "、".join(info["子类列表"]))
    print("")
    count = count + 1
```

📸 操作截图：![截图](Pasted%20image%2020260712095435.png)
### 3.4.4 存入 SQLite 数据库

SQLite 是一个轻量级的数据库，不需要安装，不需要配置，Python 自带的 `sqlite3` 模块就能直接使用。**数据库文件就是一个 `.db` 文件**，你可以把它复制到任何地方。

```python
"""
将爬取数据存入 SQLite 数据库
"""

# 导入 sqlite3 模块
# sqlite3 是 Python 标准库的一部分，不需要 pip install
# 它用来操作 SQLite 数据库
import sqlite3

# 第一步：连接数据库（如果文件不存在会自动创建）
# sqlite3.connect() 函数：打开或创建一个 SQLite 数据库文件
# 参数：数据库文件的路径（字符串）
# 返回：一个 Connection 对象，代表数据库连接
database_file = "drug_data.db"
connection = sqlite3.connect(database_file)

# 第二步：创建游标
# 游标（Cursor）是用来执行 SQL 语句的对象
# connection.cursor() 方法：创建一个游标对象
# 返回：一个 Cursor 对象
cursor = connection.cursor()

# 第三步：创建数据表
# 如果表已经存在，先删除（避免重复运行时报错）
# CREATE TABLE IF NOT EXISTS：如果表不存在就创建，存在就跳过
# 这是一种更安全的写法
create_table_sql = """
CREATE TABLE IF NOT EXISTS drug_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    big_category TEXT,
    sub_category TEXT,
    drug_names TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
# cursor.execute() 方法：执行一条 SQL 语句
# 参数：SQL 语句（字符串）
# 返回：无
cursor.execute(create_table_sql)

# 第四步：清空旧数据（可选，避免重复插入）
# 如果你不想每次运行都清空，可以删除下面这行
cursor.execute("DELETE FROM drug_categories")

# 第五步：插入数据
# 使用参数化查询防止 SQL 注入
# ? 是占位符，execute() 会用第二个参数列表中的值替换它
insert_sql = "INSERT INTO drug_categories (big_category, sub_category, drug_names, source_url) VALUES (?, ?, ?, ?)"

insert_count = 0
for record in unique_drugs:
    # 准备插入的参数
    params = (
        record["大类"],
        record["子类"],
        record["代表药品"],
        record["来源URL"]
    )
    
    # 执行插入
    cursor.execute(insert_sql, params)
    insert_count = insert_count + 1

# 第六步：提交事务
# 在 SQLite 中，INSERT/UPDATE/DELETE 操作需要 commit() 才会真正写入磁盘
# connection.commit() 方法：提交所有未保存的更改
# 如果不调用 commit()，数据不会保存！
connection.commit()
print("成功插入 " + str(insert_count) + " 条数据到数据库")

# 第七步：查询验证
# 从数据库中读取数据，验证是否插入成功
select_sql = "SELECT * FROM drug_categories LIMIT 10"
cursor.execute(select_sql)

# cursor.fetchall() 方法：获取查询结果的所有行
# 返回：一个列表，每行是一个元组
all_rows = cursor.fetchall()
print("查询到 " + str(len(all_rows)) + " 条数据（前10条）")
print("")

# 打印查询结果
for row in all_rows:
    # row 是一个元组，按 SELECT 的顺序排列
    # row[0] = id, row[1] = big_category, row[2] = sub_category, ...
    row_id = row[0]
    big_cat = row[1]
    sub_cat = row[2]
    drug = row[3]
    
    print("ID: " + str(row_id))
    print("  大类: " + big_cat)
    print("  子类: " + sub_cat)
    print("  药品: " + drug[:60])
    print("")

# 第八步：关闭连接
# 使用完毕后一定要关闭数据库连接
cursor.close()
connection.close()
print("数据库连接已关闭")
print("数据库文件位置: " + database_file)
```

📸 操作截图：![截图](Pasted%20image%2020260712095819.png)

### 3.4.5 查询数据库中的数据

数据库建好之后，你可以随时查询，不需要重新爬取。

```python
"""
从 SQLite 数据库读取数据
"""

import sqlite3

# 第一步：连接数据库
database_file = "drug_data.db"
connection = sqlite3.connect(database_file)
cursor = connection.cursor()

# ============================================
# 查询1：统计每个大类下的药品数量
# ============================================
print("=" * 60)
print("各分类药品数量统计")
print("=" * 60)

# GROUP BY 语句：按某列分组
# COUNT(*) 函数：统计每组有多少行
count_sql = "SELECT big_category, COUNT(*) as count FROM drug_categories GROUP BY big_category"
cursor.execute(count_sql)
count_results = cursor.fetchall()

for row in count_results:
    category_name = row[0]
    drug_count = row[1]
    print("  " + category_name + ": " + str(drug_count) + " 种")

# ============================================
# 查询2：搜索包含特定关键词的药品
# ============================================
print("")
print("=" * 60)
print("搜索包含'青霉素'的药品")
print("=" * 60)

# LIKE 语句：模糊匹配，% 表示任意字符
# 参数化查询中用 ? 占位符
search_keyword = "%青霉素%"
search_sql = "SELECT big_category, sub_category, drug_names FROM drug_categories WHERE drug_names LIKE ?"
cursor.execute(search_sql, (search_keyword,))
search_results = cursor.fetchall()

for row in search_results:
    print("  [" + row[0] + "] " + row[1] + " → " + row[2][:60])

# ============================================
# 查询3：导出数据到 CSV 文件
# ============================================
print("")
print("=" * 60)
print("导出数据到 CSV 文件")
print("=" * 60)

# 导入 csv 模块
# csv 是 Python 标准库，用于读写 CSV 文件
import csv

# 查询所有数据
export_sql = "SELECT big_category, sub_category, drug_names, source_url FROM drug_categories"
cursor.execute(export_sql)
all_data = cursor.fetchall()

# 写 CSV 文件
# open() 函数：打开文件
# 参数1：文件路径（字符串）
# 参数2：模式，"w" 表示写入（会覆盖已有内容），encoding="utf-8-sig" 确保中文正常
csv_file = "drug_data.csv"
csv_handle = open(csv_file, "w", encoding="utf-8-sig", newline="")

# csv.writer() 函数：创建一个 CSV 写入器
# 参数：文件对象
csv_writer = csv.writer(csv_handle)

# 写表头
csv_writer.writerow(["大类", "子类", "代表药品", "来源URL"])

# 写数据行
for row in all_data:
    csv_writer.writerow(row)

# 关闭文件
csv_handle.close()

print("数据已导出到: " + csv_file)
print("共导出 " + str(len(all_data)) + " 条记录")

# 关闭数据库连接
cursor.close()
connection.close()
```

📸 操作截图：![截图](Pasted%20image%2020260712095911.png)

### 3.4.6 完整项目代码汇总

下面是把所有步骤整合在一起的完整代码。你可以直接复制到 VS Code 中运行。

📸 操作截图：在 VS Code 中新建 `drug_spider_complete.py` 文件 | 截取范围：VS Code 左侧文件浏览器 | 重点标注：红框圈出新创建的文件名

```python
"""
项目3：XPath 爬取 A+医学百科药品数据 —— 完整代码
功能：爬取多个药品分类页面 → 提取表格数据 → 去重 → 存入 SQLite
"""

import requests
from lxml import etree
import time
import sqlite3
import csv

# ============================================
# 第一部分：配置
# ============================================

# 要爬取的药品分类页面列表
category_urls = [
    {
        "name": "青霉素类药物",
        "url": "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
    {
        "name": "头孢菌素类药物",
        "url": "http://www.a-hospital.com/w/%E5%A4%B4%E5%AD%A2%E8%8F%8C%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
    {
        "name": "大环内酯类药物",
        "url": "http://www.a-hospital.com/w/%E5%A4%A7%E7%8E%AF%E5%86%85%E9%85%AF%E7%B1%BB%E8%8D%AF%E7%89%A9"
    },
]

# 请求头，伪装成浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://www.a-hospital.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ============================================
# 第二部分：爬取数据
# ============================================

all_drugs = []  # 存储所有爬取到的数据

print("=" * 50)
print("开始爬取 A+医学百科药品数据")
print("=" * 50)
print("")

for category in category_urls:
    category_name = category["name"]
    category_url = category["url"]
    
    print("正在爬取: " + category_name)
    
    try:
        # 发送请求
        response = requests.get(category_url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        
        if response.status_code != 200:
            print("  请求失败: " + str(response.status_code))
            continue
        
        # 解析 HTML
        html_tree = etree.HTML(response.text)
        
        # 提取表格数据
        # 找到 wikitable 表格中的所有行
        all_rows = html_tree.xpath('//table[@class="wikitable"]//tr')
        print("  找到 " + str(len(all_rows)) + " 行")
        
        page_count = 0
        for row in all_rows:
            # 提取 th（子分类名称）
            col1_list = row.xpath('th//text()')
            # 提取 td，用 string() 获取完整药品列表
            td_list = row.xpath('td')
            
            if len(col1_list) > 0 and len(td_list) > 0:
                sub_category = col1_list[0].strip()
                # td.xpath("string()") 获取整个 td 的完整文本
                drug_names = td_list[0].xpath("string()")
                drug_names = drug_names.strip()
                
                # 跳过表头
                if sub_category == "分类":
                    continue
                
                # 保存数据
                record = {
                    "大类": category_name,
                    "子类": sub_category,
                    "代表药品": drug_names,
                    "来源URL": category_url
                }
                all_drugs.append(record)
                page_count = page_count + 1
        
        print("  提取 " + str(page_count) + " 条记录")
        
    except Exception as e:
        print("  出错: " + str(e))
    
    # 礼貌等待
    time.sleep(2)

print("")
print("爬取完成，共 " + str(len(all_drugs)) + " 条原始数据")

# ============================================
# 第三部分：数据去重
# ============================================

print("")
print("=" * 50)
print("开始数据去重")
print("=" * 50)

seen_drugs = set()
unique_drugs = []

for record in all_drugs:
    drug_name = record["代表药品"]
    if drug_name not in seen_drugs:
        seen_drugs.add(drug_name)
        unique_drugs.append(record)

print("去重前: " + str(len(all_drugs)) + " 条")
print("去重后: " + str(len(unique_drugs)) + " 条")
print("去除重复: " + str(len(all_drugs) - len(unique_drugs)) + " 条")

# ============================================
# 第四部分：存入 SQLite
# ============================================

print("")
print("=" * 50)
print("存入 SQLite 数据库")
print("=" * 50)

# 连接数据库
connection = sqlite3.connect("drug_data.db")
cursor = connection.cursor()

# 创建表
create_table_sql = """
CREATE TABLE IF NOT EXISTS drug_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    big_category TEXT,
    sub_category TEXT,
    drug_names TEXT,
    source_url TEXT
)
"""
cursor.execute(create_table_sql)

# 清空旧数据
cursor.execute("DELETE FROM drug_categories")

# 插入数据
insert_sql = "INSERT INTO drug_categories (big_category, sub_category, drug_names, source_url) VALUES (?, ?, ?, ?)"

for record in unique_drugs:
    params = (
        record["大类"],
        record["子类"],
        record["代表药品"],
        record["来源URL"]
    )
    cursor.execute(insert_sql, params)

# 提交
connection.commit()
print("成功插入 " + str(len(unique_drugs)) + " 条数据")

# 关闭连接
cursor.close()
connection.close()

# ============================================
# 第五部分：验证 + 导出 CSV
# ============================================

print("")
print("=" * 50)
print("验证数据并导出 CSV")
print("=" * 50)

# 重新连接数据库
connection = sqlite3.connect("drug_data.db")
cursor = connection.cursor()

# 查询统计
cursor.execute("SELECT big_category, COUNT(*) FROM drug_categories GROUP BY big_category")
stats = cursor.fetchall()
print("各分类药品数量:")
for row in stats:
    print("  " + row[0] + ": " + str(row[1]) + " 种")

# 导出 CSV
cursor.execute("SELECT big_category, sub_category, drug_names, source_url FROM drug_categories")
all_data = cursor.fetchall()

csv_file = open("drug_data.csv", "w", encoding="utf-8-sig", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["大类", "子类", "代表药品", "来源URL"])

for row in all_data:
    csv_writer.writerow(row)

csv_file.close()
print("已导出 CSV 文件: drug_data.csv")

cursor.close()
connection.close()

print("")
print("=" * 50)
print("全部完成！")
print("=" * 50)
print("生成文件:")
print("  1. drug_data.db   - SQLite 数据库")
print("  2. drug_data.csv  - CSV 表格文件")
```

📸 操作截图：![截图](Pasted%20image%2020260712100036.png)

除了分类列表页，我们还可以进一步爬取每个药品的详情页，获取更多的药品属性信息。

```python
"""
进阶：爬取药品详情页
从药品分类页面找到具体药品链接，进入详情页提取更多信息
"""

import requests
from lxml import etree
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://www.a-hospital.com/",
}

# 第一步：从分类页面获取药品详情页链接
list_url = "http://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0%E7%B1%BB%E8%8D%AF%E7%89%A9"
response = requests.get(list_url, headers=headers, timeout=15)
response.encoding = response.apparent_encoding
html_tree = etree.HTML(response.text)

# 提取表格中所有链接
# 这些链接指向具体的药品详情页
drug_links = html_tree.xpath('//table[@class="wikitable"]//a/@href')
print("找到药品链接: " + str(len(drug_links)) + " 个")

# 第二步：访问每个药品详情页
# 为了演示，我们只爬取前2个
detail_urls = []
for href in drug_links[:2]:
    if href.startswith("/"):
        full_url = "http://www.a-hospital.com" + href
    else:
        full_url = href
    detail_urls.append(full_url)

for detail_url in detail_urls:
    print("")
    print("=" * 50)
    print("爬取药品详情: " + detail_url)
    
    try:
        response = requests.get(detail_url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        html_tree = etree.HTML(response.text)
        
        # 提取药品名称（页面标题）
        title_list = html_tree.xpath('//h1[@id="firstHeading"]/text()')
        if len(title_list) > 0:
            print("药品名称: " + title_list[0])
        
        # 提取所有 th 标签和对应的 td 标签
        # 这是 MediaWiki 药品页面的常见结构
        # <tr><th>属性名</th><td>属性值</td></tr>
        info_rows = html_tree.xpath('//table[contains(@class, "wikitable")]//tr')
        
        for row in info_rows:
            th_list = row.xpath('th//text()')
            td_list = row.xpath('td//text()')
            
            if len(th_list) > 0 and len(td_list) > 0:
                property_name = th_list[0].strip()
                property_value = td_list[0].strip()
                if len(property_name) > 1 and len(property_value) > 1:
                    print("  " + property_name + ": " + property_value[:60])
        
        time.sleep(2)
        
    except Exception as e:
        print("  出错: " + str(e))

print("")
print("详情页爬取完成")
```

📸 操作截图：![截图](Pasted%20image%2020260712100128.png)

---


## 项目总结

### 你学到了什么

| 知识点 | 说明 |
|--------|------|
| **XPath 基本语法** | `//` 相对路径、`/` 绝对路径、`@` 属性、`text()` 文本 |
| **XPath 高级用法** | `contains()` 模糊匹配、轴（Axes）方向查找 |
| **lxml 库** | `etree.HTML()` 解析、`xpath()` 查询 |
| **Chrome 开发者工具** | 复制 XPath、Console 中测试 `$x()` |
| **多页爬取** | 循环遍历 URL 列表、`time.sleep()` 控制频率 |
| **数据去重** | 用 `set()` 去重、合并多源分类信息 |
| **SQLite 存储** | 建表、插入、查询、提交事务 |
| **CSV 导出** | `csv.writer()` 写入结构化数据 |
| **请求伪装** | User-Agent、Referer 设置 |
| **错误处理** | `try/except`、空列表检查、状态码判断 |

### XPath 与 BeautifulSoup 的选择建议

| 场景 | 推荐工具 |
|------|----------|
| 页面结构简单，class/id 明确 | BeautifulSoup（CSS 选择器） |
| 需要按文本内容查找 | XPath |
| 需要向上或横向查找 | XPath |
| 页面结构复杂，多层嵌套 | XPath |
| 快速原型开发 | BeautifulSoup |
| 精确控制、性能优先 | lxml + XPath |

两者不是互斥的，你可以先用 BeautifulSoup 快速定位，再用 XPath 精确提取。**真正的爬虫工程师两个都会用。**

---

## 课后练习

### 练习1：爬取更多分类（基础）

在 `category_urls` 列表中添加更多药品分类页面，例如：
- 氨基糖苷类药物
- 四环素类药物
- 喹诺酮类药物

**提示**：在 A+医学百科的「抗生素」相关页面中找到这些分类的链接，提取 URL 并添加到列表中。

### 练习2：提取药品批准文号（进阶）

A+医学百科的某些药品详情页包含批准文号信息。修改「爬取药品详情页」的代码，尝试提取每个药品的批准文号。

**提示**：批准文号的格式通常是「国药准字HXXXXXXXX」或「国药准字ZXXXXXXXX」。

### 练习3：实现增量爬取（综合）

修改数据库存储逻辑，实现「增量爬取」：
- 爬取前先检查数据库，如果某条记录已存在，就跳过
- 新爬取到的数据才插入
- 记录每次爬取的时间

**提示**：使用 `SELECT COUNT(*) FROM drug_categories WHERE drug_names = ?` 检查是否已存在。

### 练习4：用 XPath 轴提取兄弟元素（挑战）

在药品详情页中，找到 th 标签文本为「适应症」的行，然后提取它后面一个兄弟 td 标签中的内容。

**提示**：使用 `following-sibling::td[1]` 轴。

---

> 恭喜你完成了项目3！你已经掌握了 XPath 这个强大的数据提取工具。在下一个项目中，我们将学习如何处理需要登录和 Cookie 的网站。