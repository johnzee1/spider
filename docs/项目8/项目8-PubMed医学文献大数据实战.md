---
title: "项目8-PubMed 医学文献大数据实战"
---

# 项目8：PubMed 医学文献大数据实战

> **适合谁学习：** 已经完成项目7，能用 requests 获取 JSON，但从来没有使用过 PubMed 或 XML 的同学。
>
> **最终成果：** 输入一个医学主题，搜索一批 PubMed 文献，提取 PMID、标题、作者、期刊和摘要，保存为 CSV 与 JSON。
>
> **学习方法：** 本项目仍然使用“小步运行”。先找3个编号，再下载1篇 XML，再解析1篇，最后才处理10篇。

---

## 合规提示

PubMed 是美国国家医学图书馆提供的医学文献检索系统。本项目使用 NCBI 官方 E-utilities API。

1. 只读取公开的文献题录和摘要。
2. 不下载论文全文，不绕过期刊付费页面。
3. API 参数中填写自己的联系邮箱。
4. 没有 API Key 时，每秒不要超过3次请求。本教程每次请求后等待0.4秒。
5. 程序提取的摘要不能替代完整论文，也不能直接作为诊疗依据。

规则有变化时，以 [NCBI E-utilities 官方指南](https://www.ncbi.nlm.nih.gov/books/NBK25497/) 为准。

---

## 8.1 先认识 PubMed、PMID 和 DOI

### 8.1.1 PubMed 像什么

可以把 PubMed 想成一座巨大的医学图书馆目录：

- 它告诉你论文叫什么；
- 谁写了论文；
- 发表在哪本期刊；
- 很多记录还提供摘要；
- 但它不等于所有论文的免费全文仓库。

爬虫的任务是读取“目录卡片”，不是翻墙进入收费书库。

### 8.1.2 PMID 是什么

每条 PubMed 记录都有一个编号，叫 PMID。例如：

```text
41384369
```

把编号放进下面的网址，就能打开原始记录：

```text
https://pubmed.ncbi.nlm.nih.gov/41384369/
```

PMID 就像学生的学号：标题可能相似，编号不会混淆。本项目用 PMID 识别每一篇文献。

### 8.1.3 PMID 和 DOI 不一样

| 编号 | 谁分配 | 用途 |
|---|---|---|
| PMID | PubMed | 标识 PubMed 中的一条记录 |
| DOI | 出版机构 | 标识一篇正式出版物 |

某些老文献没有 DOI，但只要被 PubMed 收录就有 PMID。因此程序首先使用 PMID。

### 8.1.4 为什么这次会遇到两种数据格式

PubMed 把搜索和详情拆成两个工具：

| 工具 | 做什么 | 返回格式 |
|---|---|---|
| ESearch | 根据关键词找 PMID | JSON |
| EFetch | 根据 PMID 取标题、作者和摘要 | XML |

流程像去图书馆：

```text
告诉目录员要找“糖尿病”
        ↓ ESearch
拿到3个书目编号 PMID
        ↓ EFetch
根据编号取回3张详细目录卡
```

### 8.1.5 JSON 和 XML 的外观区别

JSON：

```json
{
  "pmid": "41384369",
  "title": "Example title"
}
```

XML：

```xml
<PubmedArticle>
  <PMID>41384369</PMID>
  <ArticleTitle>Example title</ArticleTitle>
</PubmedArticle>
```

XML 使用一对开始和结束标签包住内容：

```xml
<ArticleTitle>标题文字</ArticleTitle>
```

项目3学过 XPath 的同学会觉得熟悉。没有关系，本项目会从寻找一个标签开始。

### 8.1.6 四步学习路线

| 步骤 | 文件名 | 本步目标 |
|---|---|---|
| 第1步 | `step1_search_pmids.py` | 搜索3个 PMID |
| 第2步 | `step2_fetch_one_xml.py` | 下载1篇文献 XML |
| 第3步 | `step3_parse_one_article.py` | 从 XML 提取标题、作者和摘要 |
| 第4步 | `step4_save_ten_articles.py` | 批量获取10篇并保存 CSV |

---

## 8.2 准备项目文件夹

项目9要继续使用本项目的数据，因此建议创建一个连续使用的文件夹。

### 8.2.1 创建文件夹

1. 在桌面新建文件夹 `pubmed_ai_project`。
2. 打开 VS Code。
3. 点击“文件” -> “打开文件夹”。
4. 选择 `pubmed_ai_project`。
5. 点击“终端” -> “新建终端”。

### 8.2.2 检查 Python

```bash
python --version
```

应该输出 Python 3.8 或更高版本。

### 8.2.3 安装 requests

```bash
python -m pip install requests
```

验证：

```bash
python -c "import requests; print('requests安装成功')"
```

预期输出：

```text
requests安装成功
```

XML 解析器 `xml.etree.ElementTree` 是 Python 自带的，不需要安装 `xml`。

!!! warning "不要执行 pip install xml"
    本项目使用的是 Python 标准库。额外安装名字相似的包反而可能造成冲突。

---

## 8.3 先学会写一个简单检索式

### 8.3.1 最简单的关键词

```text
diabetes
```

这会在 PubMed 的多个字段中搜索，结果很多。

### 8.3.2 指定只找标题和摘要

```text
diabetes[Title/Abstract]
```

方括号中的 `Title/Abstract` 是字段范围，不是 Python 列表。

### 8.3.3 同时满足两个条件

```text
diabetes[Title/Abstract] AND exercise[Title/Abstract]
```

`AND` 表示两边都要满足，必须大写更容易辨认。

### 8.3.4 常见字段

| 写法 | 中文意思 | 示例 |
|---|---|---|
| `[Title/Abstract]` | 标题或摘要 | `asthma[Title/Abstract]` |
| `[MeSH Terms]` | 医学主题词 | `asthma[MeSH Terms]` |
| `[dp]` | 出版日期 | `2025:2026[dp]` |
| `[pt]` | 文献类型 | `clinical trial[pt]` |

第一次练习只使用：

```text
diabetes[Title/Abstract]
```

---

## 8.4 第1步：搜索3个 PMID

### 8.4.1 为什么第一步只拿编号

ESearch 的任务是“查目录”。它能很快告诉我们：

- 一共有多少条符合条件；
- 本次返回了哪些 PMID。

它不会返回完整摘要。完整资料要在第2步用 EFetch 获取。

### 8.4.2 创建文件并修改邮箱

新建文件：

```text
step1_search_pmids.py
```

[下载第1步代码](step1_search_pmids.py){: download }

打开代码后，找到：

```python
my_email = "your_email@example.com"
```

改成你自己的联系邮箱。例如：

```python
my_email = "xiaowang@example.com"
```

这里的邮箱会作为 API 查询参数发给 NCBI，用于标识程序使用者。不要填写密码。

### 8.4.3 完整代码

```python
# -*- coding: utf-8 -*-
"""项目8第1步：在 PubMed 中搜索3个 PMID。"""

import requests

# 请把下面的邮箱改成你自己的邮箱。
my_email = "your_email@example.com"

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",                       # 在 PubMed 数据库中搜索
    "term": "diabetes[Title/Abstract]",   # 检索式
    "retmode": "json",                    # 返回 JSON
    "retmax": 3,                           # 只返回3个编号
    "tool": "medical_data_course",
    "email": my_email,
}

print("正在搜索 PubMed...")
response = requests.get(url, params=params, timeout=30)
print("状态码：", response.status_code)
response.raise_for_status()

data = response.json()
result = data["esearchresult"]

print("符合条件的文献总数：", result["count"])
print("本次拿到的 PMID：", result["idlist"])

for pmid in result["idlist"]:
    print("文献页面：https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/")
```

### 8.4.4 运行

保存后，在终端输入：

```bash
python step1_search_pmids.py
```

### 8.4.5 预期输出

总数和 PMID 会随数据库更新而变化，形式应该类似：

```text
正在搜索 PubMed...
状态码： 200
符合条件的文献总数： 800000
本次拿到的 PMID： ['...', '...', '...']
文献页面：https://pubmed.ncbi.nlm.nih.gov/.../
文献页面：https://pubmed.ncbi.nlm.nih.gov/.../
文献页面：https://pubmed.ncbi.nlm.nih.gov/.../
```

依次复制三个网址到浏览器，确认都能打开 PubMed 页面。

### 8.4.6 逐个认识参数

```python
"db": "pubmed"
```

NCBI 有多个数据库，这行规定只查 PubMed。

```python
"retmax": 3
```

`retmax` 是 return maximum 的缩写，表示最多返回3个编号。

```python
result = data["esearchresult"]
```

搜索结果主要内容放在 `esearchresult` 字典中。

```python
result["count"]
```

这是符合条件的总数，不是本次已下载的数量。

```python
result["idlist"]
```

这是本次真正返回的 PMID 列表，只有3个。

!!! success "第1个检查点"
    状态码是200，终端输出3个 PMID，三个原始页面都能打开。

### 8.4.7 常见错误

#### `IndexError` 或 PMID 列表为空

说明检索式没有结果。先把 `term` 改回教程中的：

```python
"diabetes[Title/Abstract]"
```

#### 状态码400

检查 `db`、`term`、`retmode` 是否拼写正确，英文引号和逗号是否完整。

---

## 8.5 第2步：下载1篇文献的 XML

### 8.5.1 两次请求是怎样接起来的

这个程序要请求两次：

```text
第1次请求 ESearch -> 得到1个 PMID
第2次请求 EFetch  -> 把这个 PMID 交回去 -> 得到详情 XML
```

这叫“两阶段采集”。第1次的输出，是第2次的输入。

### 8.5.2 创建文件

新建：

```text
step2_fetch_one_xml.py
```

[下载第2步代码](step2_fetch_one_xml.py){: download }

同样要把代码开头的邮箱改成自己的。

### 8.5.3 代码分块讲解

第一块搜索一个 PMID：

```python
import requests

my_email = "your_email@example.com"
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

search_params = {
    "db": "pubmed",
    "term": "diabetes[Title/Abstract]",
    "retmode": "json",
    "retmax": 1,
    "tool": "medical_data_course",
    "email": my_email,
}
search_response = requests.get(
    base_url + "/esearch.fcgi", params=search_params, timeout=30
)
search_response.raise_for_status()
pmid = search_response.json()["esearchresult"]["idlist"][0]
print("找到 PMID：", pmid)
```

第二块用这个 PMID 获取 XML：

```python
fetch_params = {
    "db": "pubmed",
    "id": pmid,
    "retmode": "xml",
    "rettype": "abstract",
    "tool": "medical_data_course",
    "email": my_email,
}
fetch_response = requests.get(
    base_url + "/efetch.fcgi", params=fetch_params, timeout=60
)
fetch_response.raise_for_status()
```

注意这次的 `retmode` 是 `xml`，不是 `json`。

第三块打印并保存：

```python
xml_text = fetch_response.text
print("XML长度：", len(xml_text), "个字符")
print("XML开头500个字符：")
print(xml_text[:500])

with open("one_article.xml", "w", encoding="utf-8") as file:
    file.write(xml_text)

print("保存完成：one_article.xml")
```

完整代码已经在下载文件中。

### 8.5.4 运行和预期输出

```bash
python step2_fetch_one_xml.py
```

应该看到：

```text
找到 PMID： ...
XML长度： ... 个字符
XML开头500个字符：
<?xml version="1.0" ...
<PubmedArticleSet>...
保存完成：one_article.xml
```

VS Code 左侧会出现 `one_article.xml`。双击打开，然后按 `Ctrl+F` 搜索：

```text
ArticleTitle
```

应该能找到：

```xml
<ArticleTitle>这里是文献标题</ArticleTitle>
```

再搜索：

```text
AbstractText
```

如果找不到，可能这篇文献本来就没有公开摘要，不是程序错误。

!!! success "第2个检查点"
    项目文件夹中出现 `one_article.xml`，文件开头有 `PubmedArticleSet`，能找到 `ArticleTitle`。

---

## 8.6 第3步：解析1篇 XML

### 8.6.1 ElementTree 是什么

XML 中的标签像一棵树：

```text
PubmedArticle
└── MedlineCitation
    ├── PMID
    └── Article
        ├── ArticleTitle
        ├── AuthorList
        │   └── Author
        └── Abstract
            └── AbstractText
```

`xml.etree.ElementTree` 是 Python 自带的“爬树工具”。它可以沿着标签寻找内容。

### 8.6.2 创建文件

新建：

```text
step3_parse_one_article.py
```

[下载第3步代码](step3_parse_one_article.py){: download }

这个程序必须和 `one_article.xml` 放在同一个文件夹中。

### 8.6.3 先做最小实验：只找标题

可以先输入下面几行：

```python
import xml.etree.ElementTree as ET

tree = ET.parse("one_article.xml")
root = tree.getroot()
title_node = root.find(".//ArticleTitle")
print(title_node.text)
```

运行：

```bash
python step3_parse_one_article.py
```

如果输出一个英文标题，说明 XML 文件读取和标签查找都成功。

### 8.6.4 为什么完整代码不用 `.text`

有些标题内部还包含斜体等子标签：

```xml
<ArticleTitle>Effects of <i>Example</i> Treatment</ArticleTitle>
```

直接使用 `.text` 可能只得到：

```text
Effects of
```

因此完整代码使用：

```python
def get_all_text(node):
    if node is None:
        return ""
    return "".join(node.itertext()).strip()
```

`itertext()` 会把标签内部所有文字依次取出。

### 8.6.5 提取 PMID 和标题

```python
pmid_node = root.find(".//PMID")
title_node = root.find(".//ArticleTitle")

pmid = get_all_text(pmid_node)
title = get_all_text(title_node)
```

`.//ArticleTitle` 的意思是：从当前根节点向下寻找第一个 `ArticleTitle`，中间隔多少层都可以。

### 8.6.6 提取所有作者

```python
authors = []

for author_node in root.findall(".//AuthorList/Author"):
    last_name = get_all_text(author_node.find("LastName"))
    initials = get_all_text(author_node.find("Initials"))
    collective_name = get_all_text(author_node.find("CollectiveName"))

    if collective_name:
        authors.append(collective_name)
    elif last_name:
        authors.append(last_name + " " + initials)
```

`find()` 找第一个，`findall()` 找全部。作者不止一个，因此这里必须使用 `findall()`。

有些“作者”不是个人，而是研究协作组，所以还要检查 `CollectiveName`。

### 8.6.7 提取分段摘要

```python
abstract_parts = []

for abstract_node in root.findall(".//Abstract/AbstractText"):
    label = abstract_node.attrib.get("Label", "")
    text = get_all_text(abstract_node)

    if label:
        abstract_parts.append(label + ": " + text)
    else:
        abstract_parts.append(text)

abstract = "\n".join(abstract_parts)
```

一篇摘要可能分成：

```text
BACKGROUND
METHODS
RESULTS
CONCLUSIONS
```

不能只找第一个 `AbstractText`，否则可能只保存背景，丢掉最重要的结果和结论。

### 8.6.8 运行完整第3步

下载文件中已经包含完整代码。运行：

```bash
python step3_parse_one_article.py
```

预期形式：

```text
PMID： ...
标题： ...
作者： Zhang Y | Li X | Example Study Group
摘要：
BACKGROUND: ...
METHODS: ...
RESULTS: ...
```

如果摘要显示“这篇文献没有公开摘要”，可以回到第2步换一个检索式或稍后处理多篇数据。

!!! success "第3个检查点"
    终端能打印 PMID 和完整标题；作者之间用 `|` 分隔；有摘要时能显示所有段落。

### 8.6.9 常见错误

#### 找不到 XML 文件

```text
FileNotFoundError: one_article.xml
```

检查：

1. 是否完成第2步；
2. 两个文件是否在同一文件夹；
3. 文件名是否完全一致。

#### `AttributeError: 'NoneType' object has no attribute ...`

说明代码没有找到某个标签。使用教程中的 `get_all_text()`，它会在节点不存在时返回空字符串。

---

## 8.7 第4步：批量保存10篇文献

### 8.7.1 批量请求，不是一篇请求一次

低效方法：

```text
请求 PMID 1 -> 等待
请求 PMID 2 -> 等待
请求 PMID 3 -> 等待
```

更合理的方法：

```text
把10个 PMID 用逗号连接 -> 一次交给 EFetch
```

代码：

```python
"id": ",".join(pmids)
```

假设列表是：

```python
["111", "222", "333"]
```

连接结果是：

```text
111,222,333
```

### 8.7.2 创建文件

新建：

```text
step4_save_ten_articles.py
```

[下载第4步代码](step4_save_ten_articles.py){: download }

修改文件开头的邮箱，然后保存。

### 8.7.3 完整流程分成四块

第1块：ESearch 搜索10个 PMID。

```python
search_params = {
    "db": "pubmed",
    "term": "diabetes[Title/Abstract]",
    "retmode": "json",
    "retmax": 10,
    "tool": "medical_data_course",
    "email": my_email,
}
```

第2块：礼貌等待后，一次获取10篇 XML。

```python
time.sleep(0.4)

fetch_params = {
    "db": "pubmed",
    "id": ",".join(pmids),
    "retmode": "xml",
    "rettype": "abstract",
    "tool": "medical_data_course",
    "email": my_email,
}
```

第3块：逐个 `PubmedArticle` 提取字段。

```python
records = []

for article_node in root.findall("PubmedArticle"):
    pmid = get_all_text(article_node.find(".//PMID"))
    title = get_all_text(article_node.find(".//ArticleTitle"))
    journal = get_all_text(article_node.find(".//Journal/Title"))
    # 继续提取摘要并放入 records
```

第4块：使用 `csv.DictWriter` 保存。

```python
with open("pubmed_10.csv", "w", encoding="utf-8-sig", newline="") as file:
    fieldnames = ["pmid", "title", "journal", "abstract", "source_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
```

完整内容请打开下载的课堂代码逐行阅读。

### 8.7.4 运行

```bash
python step4_save_ten_articles.py
```

预期形式：

```text
找到 10 个 PMID
已整理： ... 标题1
已整理： ... 标题2
...
保存完成：pubmed_10.csv
```

打开 `pubmed_10.csv`，检查：

1. 表头下面大约有10行；
2. PMID 不是空白；
3. 标题可以正常阅读；
4. 一部分摘要可能为空，这是正常数据状态；
5. `source_url` 能在浏览器中打开。

!!! success "第4个检查点"
    成功生成 `pubmed_10.csv`，随机检查至少3条，PMID、标题和原始页面一致。

---

## 8.8 再学分页：获取不止一批 PMID

ESearch 使用“起始位置”分页：

```text
第1批：retstart=0，retmax=100
第2批：retstart=100，retmax=100
第3批：retstart=200，retmax=100
```

可以把 `retstart` 想成“从第几条开始拿”。

课堂观察代码：

```python
for start in range(0, 300, 100):
    print(start)
```

输出：

```text
0
100
200
```

放进请求参数：

```python
params["retstart"] = start
params["retmax"] = 100
```

项目7使用服务器返回的 `nextPageToken`；项目8使用自己计算的 `retstart`。看到一个新接口时，必须先查清楚它采用哪种分页方式。

!!! note "课堂版最多取多少"
    本教程工程版把普通偏移量采集限制在9999条以内。需要更大规模时应学习 NCBI History Server，而不是无限增大循环。

---

## 8.9 运行完整工程版

课堂版只保存5个主要字段。工程版额外处理：

- 多批 PMID 搜索；
- 每100篇批量获取详情；
- 网络错误自动重试；
- 多种出版日期格式；
- 集体作者；
- DOI；
- MeSH 医学主题词；
- JSON、CSV 和简单统计文件。

[下载完整工程源码：pubmed_spider.py](pubmed_spider.py){: download }

把它放进 `pubmed_ai_project` 文件夹。

### 8.9.1 第一次只取20篇

把邮箱换成自己的：

```bash
python pubmed_spider.py --email you@example.com --max-records 20
```

注意：`you@example.com` 要替换，不需要在邮箱前后增加中文引号。

预期输出：

```text
>>> 搜索进度：20/20
>>> 找到 20 个 PMID，开始批量获取详情
>>> 详情进度：20/20
>>> 完成，共保存 20 篇文献
```

项目文件夹出现：

```text
pubmed_data/
├── pubmed_articles.json
├── pubmed_articles.csv
└── pubmed_stats.json
```

不要移动 `pubmed_data`。项目9默认从这里读取数据。

### 8.9.2 更换检索式

PowerShell 和 Windows 命令提示符都可以使用一行命令：

```powershell
python pubmed_spider.py --email you@example.com --term "asthma[Title/Abstract]" --max-records 50
```

包含 `AND` 的检索式：

```powershell
python pubmed_spider.py --email you@example.com --term "diabetes[Title/Abstract] AND exercise[Title/Abstract]" --max-records 50
```

整段检索式必须放在英文双引号中，否则终端会把空格后的内容误认为其他参数。

### 8.9.3 三个输出文件分别做什么

| 文件 | 适合做什么 |
|---|---|
| `pubmed_articles.json` | 保留作者和主题词列表，给项目9继续处理 |
| `pubmed_articles.csv` | 用 Excel 浏览和筛选 |
| `pubmed_stats.json` | 查看期刊、年份和 MeSH 的简单统计 |

JSON 中方括号结构要保留，不要为了看起来整齐而手工改成普通文字，否则项目9可能读不到预期数据。

---

## 8.10 完整排错手册

### 8.10.1 `ModuleNotFoundError: requests`

```bash
python -m pip install requests
```

### 8.10.2 `FileNotFoundError: one_article.xml`

先运行第2步，再运行第3步。两个文件必须位于 VS Code 当前打开的同一个文件夹。

### 8.10.3 `ParseError`

表示 XML 不完整或返回内容不是 XML。临时加入：

```python
print(response.status_code)
print(response.text[:500])
```

确认开头是否有 `<?xml` 或 `<PubmedArticleSet>`。

### 8.10.4 状态码429

请求过快：

1. 停止同时运行的其他爬虫；
2. 等待一两分钟；
3. 保留 `time.sleep(0.4)`；
4. 不要用多个终端同时采集。

### 8.10.5 有标题但摘要为空

并非所有 PubMed 记录都有公开摘要。程序应保留该文献并把摘要保存为空字符串，不能根据标题自行编造摘要。

### 8.10.6 作者或日期格式不一致

真实历史数据本来就不完全统一：

- 作者可能是个人或研究组；
- 日期可能只有年份；
- 新文献可能还没有 MeSH；
- 老文献可能没有 DOI。

空值不一定是程序错误，先去 `source_url` 核对原始记录。

### 8.10.7 命令行提示缺少 `--email`

工程版要求填写联系邮箱。正确命令：

```bash
python pubmed_spider.py --email 你的邮箱 --max-records 20
```

### 8.10.8 CSV 打开后摘要挤成一行

CSV 的一个单元格可以包含很长的摘要。用 Excel 打开后开启“自动换行”，或直接查看 JSON 文件。

---

## 8.11 课后练习（带提示）

### 练习1：换成哮喘（必做）

修改：

```python
"term": "asthma[Title/Abstract]"
```

完成标准：得到3个 PMID，原始页面均能打开。

### 练习2：把10篇改成20篇（必做）

提示：修改第4步的 `retmax`。

完成标准：CSV 大约有20条数据。

### 练习3：统计有摘要的数量（进阶）

提示：

```python
with_abstract = 0

for record in records:
    if record["abstract"]:
        with_abstract = with_abstract + 1

print("有摘要：", with_abstract)
```

### 练习4：增加出版类型（进阶）

XML 路径：

```text
.//PublicationTypeList/PublicationType
```

因为可能有多个，要使用 `findall()` 和列表。

### 练习5：比较两个检索式（挑战）

分别运行：

```text
diabetes[Title/Abstract]
diabetes[MeSH Terms]
```

记录两次输出的总数，并用自己的话解释为什么不同。

---

## 项目总结

### 你已经学会

- 知道 PubMed 是文献目录，不等于免费全文网站；
- 能区分 PMID 和 DOI；
- 能写简单的 PubMed 字段检索式；
- 能用 ESearch 搜索 PMID；
- 能用 EFetch 获取 XML 详情；
- 能使用 ElementTree 查找 XML 标签；
- 能正确处理多位作者和分段摘要；
- 能批量请求并保存 CSV；
- 知道为什么必须限速和核对原始页面。

### 离开本项目之前，请逐项自检

- [ ] 能搜索并打印3个 PMID
- [ ] 能生成 `one_article.xml`
- [ ] 能从 XML 中打印标题和作者
- [ ] 能生成 `pubmed_10.csv`
- [ ] 完整工程能生成 `pubmed_data/pubmed_articles.json`
- [ ] 能解释 ESearch 和 EFetch 各自负责什么
- [ ] 能解释为什么空摘要不能让 AI 猜测

项目9会直接使用 `pubmed_articles.json`。确认这个文件存在后再继续。
