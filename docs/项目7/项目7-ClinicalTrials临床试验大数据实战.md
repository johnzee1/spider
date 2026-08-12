---
title: "项目7-ClinicalTrials.gov 临床试验大数据保姆级实战"
---

# 项目7：ClinicalTrials.gov 临床试验大数据保姆级实战

> **适合谁学习：** 已经学过项目1和项目2，知道 `requests.get()` 是发送网络请求，但从来没有使用过网站 API 的同学。
>
> **最终成果：** 输入一个疾病名称，自动获取公开临床试验，把编号、标题、状态和疾病保存到 CSV 文件中。
>
> **学习方法：** 本项目拆成4个很小的程序。每完成一步，都要先看到教程中的成功结果，再进入下一步。不要一开始就运行最后的完整工程。

---

## 合规提示

ClinicalTrials.gov 是公开的临床研究登记平台。本教程只读取网站公开提供的数据，不涉及患者病历或个人隐私。

请遵守以下规则：

1. 只使用官方公开 API，不尝试登录、不绕过验证码。
2. 每次只采集课堂需要的少量数据。
3. 翻页时保留等待时间，不连续高速请求。
4. 数据只用于学习和统计，不能代替医生判断。
5. 报告中的研究结论必须回到官方页面核对。

官方 API 说明页面：[ClinicalTrials.gov Data API](https://clinicaltrials.gov/data-api/api)

---

## 7.1 先弄懂：API 到底是什么

### 7.1.1 从去饭店点菜说起

打开一个普通网页，就像顾客坐在饭店里看摆好盘的菜。页面包含导航栏、按钮、图片、广告和文字，这些内容主要是给人看的。

API 更像饭店后厨的取餐窗口：

- 你告诉窗口“我要糖尿病相关的1条临床试验”；
- 窗口不会给你菜单、桌椅和装饰；
- 它只把整理好的数据交给你；
- Python 可以直接读这些数据。

前面项目解析的是 HTML：

```html
<h2>一项糖尿病研究</h2>
```

这个项目得到的是 JSON：

```json
{
  "nctId": "NCT12345678",
  "briefTitle": "一项糖尿病研究"
}
```

JSON 不是新的编程语言，它只是一种数据格式。

### 7.1.2 JSON 中的两个重要符号

初学者先记住两个符号：

| 符号 | Python 中对应什么 | 生活化理解 |
|---|---|---|
| `{ }` | 字典 `dict` | 一个贴了很多标签的文件袋 |
| `[ ]` | 列表 `list` | 按顺序摆放的多个文件袋 |

下面是一个字典：

```python
student = {
    "name": "小王",
    "age": 20,
}

print(student["name"])
```

输出：

```text
小王
```

下面是一个列表：

```python
students = ["小王", "小李", "小张"]

print(students[0])
print(students[1])
```

输出：

```text
小王
小李
```

!!! note "为什么第1个元素写成 [0]"
    Python 从0开始计数。`[0]` 是第1个，`[1]` 是第2个，`[2]` 是第3个。

### 7.1.3 本项目的四步路线

| 步骤 | 文件名 | 只学习一个新知识点 |
|---|---|---|
| 第1步 | `step1_test_api.py` | 请求 API，确认能拿到 JSON |
| 第2步 | `step2_extract_one.py` | 从一条 JSON 中取出字段 |
| 第3步 | `step3_save_csv.py` | 循环处理5条并保存 CSV |
| 第4步 | `step4_pagination.py` | 使用下一页令牌获取3页 |

完成四步后，再运行工程版 `clinical_trials_spider.py`。

---

## 7.2 准备项目文件夹

### 7.2.1 新建文件夹

请按下面的顺序操作：

1. 在桌面空白处单击鼠标右键。
2. 选择“新建” -> “文件夹”。
3. 把文件夹命名为 `clinical_trials_project`。
4. 打开 VS Code。
5. 点击菜单“文件” -> “打开文件夹”。
6. 选择刚才创建的 `clinical_trials_project`。

完成后，VS Code 左侧应该能看到这个空文件夹。

### 7.2.2 打开终端

在 VS Code 顶部菜单中点击：

```text
终端 -> 新建终端
```

窗口下方会出现一个可以输入命令的区域。先输入：

```bash
python --version
```

如果看到类似下面的输出，说明 Python 可以使用：

```text
Python 3.12.4
```

版本号不需要完全相同，只要是 Python 3.8 或更高版本即可。

如果提示“无法识别 python”，先回到项目1的 Python 安装章节，不要继续运行后面的代码。

### 7.2.3 安装 requests

在终端输入：

```bash
python -m pip install requests
```

看到类似下面的文字表示安装成功：

```text
Successfully installed requests-...
```

如果显示：

```text
Requirement already satisfied
```

也表示已经安装，不需要重复安装。

### 7.2.4 验证 requests

在终端输入：

```bash
python -c "import requests; print(requests.__version__)"
```

如果能看到版本号，而且没有红色错误，环境准备完成。

---

## 7.3 先在浏览器里看一次 API

### 7.3.1 打开地址

复制下面的完整地址，粘贴到浏览器地址栏并按回车：

```text
https://clinicaltrials.gov/api/v2/studies?query.cond=diabetes&pageSize=1&format=json
```

这段地址可以拆成两部分：

```text
https://clinicaltrials.gov/api/v2/studies
```

上面是 API 地址。问号后面是查询条件：

```text
query.cond=diabetes&pageSize=1&format=json
```

| 查询条件 | 中文意思 |
|---|---|
| `query.cond=diabetes` | 查询糖尿病相关研究 |
| `pageSize=1` | 只返回1条 |
| `format=json` | 使用 JSON 格式返回 |

### 7.3.2 浏览器中应该看到什么

页面开头会类似这样：

```json
{
  "studies": [
    {
      "protocolSection": {
        "identificationModule": {
          "nctId": "NCT...",
          "briefTitle": "..."
        }
      }
    }
  ],
  "nextPageToken": "..."
}
```

每次查询时具体编号和标题可能变化，这是正常的。你只需要确认页面中能找到：

- `studies`
- `protocolSection`
- `nctId`
- `briefTitle`

!!! success "第0个检查点"
    浏览器能打开地址，并且页面中出现 `studies`，才进入第1步。

如果浏览器也打不开，先检查网络。此时修改 Python 代码没有用，因为问题还没有到 Python 这一层。

---

## 7.4 第1步：用 Python 请求 API

### 7.4.1 创建代码文件

在 VS Code 左侧空白处单击右键：

```text
新建文件 -> 输入 step1_test_api.py -> 按回车
```

也可以直接下载课堂代码：

[下载第1步代码](step1_test_api.py){: download }

### 7.4.2 输入完整代码

把下面的代码完整写入 `step1_test_api.py`：

```python
# -*- coding: utf-8 -*-
"""项目7第1步：请求 ClinicalTrials.gov，并确认能拿到 JSON。"""

import requests

# API 是网站专门留给程序使用的数据入口。
url = "https://clinicaltrials.gov/api/v2/studies"

# params 是要交给网站的查询条件。
params = {
    "query.cond": "diabetes",  # 查询糖尿病
    "pageSize": 1,              # 只要1条，方便第一次观察
    "format": "json",          # 要求网站返回 JSON
}

print("正在连接 ClinicalTrials.gov，请稍等...")

# timeout=30 表示最多等待30秒，避免网络不好时一直卡住。
response = requests.get(url, params=params, timeout=30)

print("状态码：", response.status_code)
print("实际请求地址：", response.url)

# 状态码不是200时，这一行会报错并停止程序。
response.raise_for_status()

# 把服务器返回的 JSON 转成 Python 字典。
data = response.json()

print("JSON最外层的键：", data.keys())
print("本页记录数：", len(data["studies"]))
print("恭喜，第一次 API 请求成功！")
```

### 7.4.3 运行代码

先确认代码文件已经保存。可以按快捷键：

```text
Ctrl + S
```

然后在 VS Code 终端输入：

```bash
python step1_test_api.py
```

### 7.4.4 预期输出

```text
正在连接 ClinicalTrials.gov，请稍等...
状态码： 200
实际请求地址： https://clinicaltrials.gov/api/v2/studies?...
JSON最外层的键： dict_keys(['studies', 'nextPageToken'])
本页记录数： 1
恭喜，第一次 API 请求成功！
```

`nextPageToken` 有时可能不显示，取决于查询结果是否还有下一页。只要状态码是200并且记录数是1，就算成功。

### 7.4.5 逐行理解新代码

#### `params` 是什么

```python
params = {
    "query.cond": "diabetes",
    "pageSize": 1,
    "format": "json",
}
```

这是一个 Python 字典。requests 会自动把它转换成地址栏中的查询条件。不要自己用很多 `+` 号拼接网址。

#### `response` 是什么

```python
response = requests.get(url, params=params, timeout=30)
```

可以把 `response` 想成网站寄回来的包裹。包裹中有：

- `response.status_code`：快递是否送达；
- `response.url`：最终访问了哪个地址；
- `response.text`：原始文字；
- `response.json()`：把 JSON 拆成 Python 字典。

#### `len()` 是什么

```python
len(data["studies"])
```

`len()` 用来数数量。这里是在数 `studies` 列表中有几条记录。

!!! success "第1个检查点"
    终端出现“状态码：200”和“本页记录数：1”。没有成功前，不要进入第2步。

### 7.4.6 本步常见错误

#### 找不到 requests

错误文字：

```text
ModuleNotFoundError: No module named 'requests'
```

解决：

```bash
python -m pip install requests
```

#### 找不到代码文件

错误文字：

```text
can't open file 'step1_test_api.py'
```

原因通常是终端不在项目文件夹中。检查 VS Code 左侧是否打开了 `clinical_trials_project`，文件名是否拼写完全一致。

#### 请求超时

错误中出现：

```text
ReadTimeout
```

先用浏览器重新打开 7.3 节的 API 地址。如果浏览器也慢，等待一会儿再试。

---

## 7.5 第2步：提取一条临床试验

### 7.5.1 先认识“字典套字典”

临床试验 JSON 像一个多层档案柜：

```text
study
└── protocolSection
    ├── identificationModule
    │   ├── nctId
    │   └── briefTitle
    ├── statusModule
    │   └── overallStatus
    └── conditionsModule
        └── conditions
```

如果想找到 `nctId`，就要按顺序打开：

```text
study -> protocolSection -> identificationModule -> nctId
```

对应 Python：

```python
nct_id = study["protocolSection"]["identificationModule"]["nctId"]
```

刚开始觉得长是正常的。我们会先把中间层分别放进变量，让代码更容易读。

### 7.5.2 创建第2个文件

新建：

```text
step2_extract_one.py
```

[下载第2步代码](step2_extract_one.py){: download }

输入完整代码：

```python
# -*- coding: utf-8 -*-
"""项目7第2步：从一条临床试验 JSON 中提取5个字段。"""

import requests

url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "diabetes",
    "pageSize": 1,
    "format": "json",
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

# studies 是列表，[0] 表示取列表中的第1条。
study = data["studies"][0]

# protocolSection 里面放着这项研究的主要资料。
protocol = study["protocolSection"]

# 继续进入不同的小模块，提取需要的字段。
identification = protocol["identificationModule"]
status_module = protocol["statusModule"]
conditions_module = protocol["conditionsModule"]

nct_id = identification["nctId"]
title = identification["briefTitle"]
status = status_module["overallStatus"]
conditions = conditions_module["conditions"]
source_url = "https://clinicaltrials.gov/study/" + nct_id

print("研究编号：", nct_id)
print("研究标题：", title)
print("研究状态：", status)
print("研究疾病：", conditions)
print("原始页面：", source_url)
```

运行：

```bash
python step2_extract_one.py
```

### 7.5.3 预期输出

具体研究每天可能不同，但形式应该类似：

```text
研究编号： NCT01234567
研究标题： A Study of ...
研究状态： COMPLETED
研究疾病： ['Diabetes Mellitus']
原始页面： https://clinicaltrials.gov/study/NCT01234567
```

复制最后一行网址到浏览器中，检查页面上的 NCT 编号和程序输出是否一致。

!!! note "为什么查询 diabetes，某条 conditions 可能不是 Diabetes"
    API 会在临床试验记录的多个相关位置中检索主题，返回结果不保证每条 `conditions` 都和关键词逐字相同。例如一项研究可能在其他字段提到胰岛素或糖尿病相关内容。程序的任务是如实保存网站返回的登记字段，不应擅自把疾病改成“糖尿病”。后续做专题数据集时，还要根据 `conditions` 等字段进行二次筛选并人工抽查。

### 7.5.4 为什么疾病显示方括号

```text
['Diabetes Mellitus', 'Obesity']
```

方括号说明它是列表。一个研究可能同时涉及多个疾病，所以网站不能只放一个普通字符串。

### 7.5.5 用 `json.dumps()`观察完整结构

如果你想看看第1条记录的完整 JSON，可以临时在程序最后加入：

```python
import json

print(json.dumps(study, ensure_ascii=False, indent=2))
```

- `ensure_ascii=False`：中文按正常文字显示；
- `indent=2`：每层缩进2个空格，更容易观察。

观察完可以删除这三行，否则终端会打印很多内容。

!!! success "第2个检查点"
    终端能打印5个字段，最后的网址可以在浏览器中打开。

---

## 7.6 第3步：保存5条 CSV

### 7.6.1 为什么先做5条

如果字段提取写错，爬1000条只会得到1000条错误数据。正确顺序应该是：

```text
先验证1条 -> 再验证5条 -> 最后才扩大数量
```

### 7.6.2 认识 `for` 循环

网站返回5条记录时，我们不应该复制5遍代码。`for` 循环可以逐条处理：

```python
for study in data["studies"]:
    print(study)
```

它的意思是：从 `studies` 列表中每次拿一条，暂时叫作 `study`，然后执行缩进部分。

### 7.6.3 认识 `.get()`

下面两种写法都能取标题：

```python
title = identification["briefTitle"]
title = identification.get("briefTitle", "")
```

区别是：

- 方括号找不到字段时会报 `KeyError`；
- `.get()` 找不到字段时返回我们指定的空字符串。

真实医疗数据并不是每条字段都齐全，因此批量处理时更适合用 `.get()`。

### 7.6.4 创建并运行第3个程序

新建：

```text
step3_save_csv.py
```

[下载第3步代码](step3_save_csv.py){: download }

完整代码较长，请使用上面的下载文件，或逐行输入并对照。代码分成四块：

```python
import csv
import requests

# 第1块：请求5条数据
url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "diabetes",
    "pageSize": 5,
    "format": "json",
}
response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

# 第2块：建立空列表，用来保存整理后的结果
records = []

# 第3块：逐条提取字段
for study in data["studies"]:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    conditions_module = protocol.get("conditionsModule", {})

    nct_id = identification.get("nctId", "")
    title = identification.get("briefTitle", "")
    status = status_module.get("overallStatus", "")
    conditions_list = conditions_module.get("conditions", [])
    conditions_text = " | ".join(conditions_list)

    record = {
        "nct_id": nct_id,
        "title": title,
        "status": status,
        "conditions": conditions_text,
        "source_url": "https://clinicaltrials.gov/study/" + nct_id,
    }
    records.append(record)
    print("已整理：", nct_id, title)

# 第4块：写入CSV文件
with open("clinical_trials_5.csv", "w", encoding="utf-8-sig", newline="") as file:
    fieldnames = ["nct_id", "title", "status", "conditions", "source_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print("保存完成：clinical_trials_5.csv")
```

运行：

```bash
python step3_save_csv.py
```

### 7.6.5 预期输出

```text
已整理： NCT... 标题1
已整理： NCT... 标题2
已整理： NCT... 标题3
已整理： NCT... 标题4
已整理： NCT... 标题5
保存完成：clinical_trials_5.csv
```

VS Code 左侧会出现：

```text
clinical_trials_5.csv
```

双击打开，应该有1行表头和5行数据。

### 7.6.6 三行容易看不懂的代码

#### 把列表变成文字

```python
conditions_text = " | ".join(conditions_list)
```

如果列表是：

```python
["Diabetes", "Obesity"]
```

连接后变成：

```text
Diabetes | Obesity
```

这样可以放进 CSV 的一个单元格。

#### 把一条记录加入总列表

```python
records.append(record)
```

`append()` 可以理解为把一张整理好的表格放进文件夹末尾。

#### 使用 `utf-8-sig`

```python
encoding="utf-8-sig"
```

这是为了让 Windows 中的 Excel 更容易正确识别中文编码。

!!! success "第3个检查点"
    `clinical_trials_5.csv` 能打开，有5条数据，并且每一行的 `source_url` 都能访问。

---

## 7.7 第4步：连续获取3页

### 7.7.1 什么是下一页令牌

项目2可能使用过第1页、第2页这样的页码。ClinicalTrials.gov 使用的是 `nextPageToken`。

可以把它想成银行排队的小票：

1. 第一次取数据时不需要小票；
2. 服务器把第1页数据和下一张小票一起给你；
3. 请求第2页时把小票交回去；
4. 服务器再返回第2页和新小票；
5. 没有新小票时，说明没有下一页。

不能自己编造令牌，也不能一直重复使用旧令牌。

### 7.7.2 创建第4个程序

新建：

```text
step4_pagination.py
```

[下载第4步代码](step4_pagination.py){: download }

核心代码：

```python
import time
import requests

url = "https://clinicaltrials.gov/api/v2/studies"
page_token = None
all_records = []

# range(1, 4) 会产生1、2、3，所以循环3次。
for page_number in range(1, 4):
    params = {
        "query.cond": "diabetes",
        "pageSize": 5,
        "format": "json",
    }

    # 第1页没有令牌；从第2页开始加入上一页令牌。
    if page_token is not None:
        params["pageToken"] = page_token

    print("正在请求第", page_number, "页...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    studies = data.get("studies", [])
    for study in studies:
        identification = (
            study.get("protocolSection", {}).get("identificationModule", {})
        )
        record = {
            "nct_id": identification.get("nctId", ""),
            "title": identification.get("briefTitle", ""),
        }
        all_records.append(record)

    print("本页得到", len(studies), "条，累计", len(all_records), "条")

    page_token = data.get("nextPageToken")
    if page_token is None:
        print("已经没有下一页。")
        break

    time.sleep(1)

print("\n前3条结果：")
for record in all_records[:3]:
    print(record["nct_id"], record["title"])
```

运行：

```bash
python step4_pagination.py
```

### 7.7.3 预期输出

```text
正在请求第 1 页...
本页得到 5 条，累计 5 条
正在请求第 2 页...
本页得到 5 条，累计 10 条
正在请求第 3 页...
本页得到 5 条，累计 15 条

前3条结果：
NCT... 标题...
NCT... 标题...
NCT... 标题...
```

### 7.7.4 理解 `if`

```python
if page_token is not None:
    params["pageToken"] = page_token
```

意思是：“如果手里有下一页小票，才把小票交给服务器。”第1次循环时 `page_token` 是 `None`，因此不会执行缩进代码。

### 7.7.5 理解 `break`

```python
if page_token is None:
    break
```

`break` 表示立即结束整个循环。没有下一页令牌时，继续循环也没有意义。

### 7.7.6 为什么要等待1秒

```python
time.sleep(1)
```

程序暂停1秒再请求下一页。课堂练习不追求最快，稳定和不给服务器造成压力更重要。

!!! success "第4个检查点"
    程序能输出3页进度，累计数量正常增加，没有反复出现同一页。

---

## 7.8 从课堂版升级到完整工程版

前四步已经覆盖了爬虫的主流程：

```text
请求 -> 解析 -> 循环 -> 翻页 -> 保存
```

完整工程版增加了以下能力：

| 能力 | 为什么需要 |
|---|---|
| 命令行参数 | 不改源码就能换疾病和数量 |
| 自动重试 | 临时网络错误时再尝试几次 |
| 安全读取多层字典 | 某条记录缺字段时不让整个任务停止 |
| NCT编号去重 | 防止重复记录 |
| 每页保存 | 运行中断时减少数据损失 |
| 断点续爬 | 下次从中断位置继续 |
| JSON + CSV | 程序处理和 Excel 查看都方便 |

这些是工程提升内容，不要求第一次看懂所有函数。

[下载完整工程源码：clinical_trials_spider.py](clinical_trials_spider.py){: download }

把文件放进 `clinical_trials_project`，先使用默认设置：

```bash
python clinical_trials_spider.py
```

预期出现：

```text
>>> 检索疾病/主题：diabetes
>>> 本次最多采集：100 条
>>> 正在请求第 1 页...已累计 ... 条
...
>>> 完成！JSON：clinical_trials_data\clinical_trials.json
>>> 完成！CSV ：clinical_trials_data\clinical_trials.csv
```

### 7.8.1 换成哮喘

```bash
python clinical_trials_spider.py --condition asthma --max-records 50
```

含有空格的条件要加英文双引号：

```bash
python clinical_trials_spider.py --condition "lung cancer" --max-records 50
```

### 7.8.2 查看帮助

```bash
python clinical_trials_spider.py --help
```

参数说明：

| 参数 | 作用 | 初学建议 |
|---|---|---|
| `--condition` | 疾病或主题 | 先用英文关键词 |
| `--max-records` | 最大条数 | 第一次不超过100 |
| `--page-size` | 每页条数 | 保持默认50 |
| `--output-dir` | 输出文件夹 | 保持默认即可 |
| `--resume` | 从断点继续 | 中断后再使用 |

### 7.8.3 什么是断点续爬

运行过程中按一次 `Ctrl+C`，程序会停止。因为完整工程每页都会保存，已经得到的数据还在。

重新运行原命令并加 `--resume`：

```bash
python clinical_trials_spider.py --condition diabetes --max-records 100 --resume
```

注意：疾病条件必须和中断前相同。程序会主动检查，避免把两个主题混在同一个文件中。

---

## 7.9 完整排错手册

### 7.9.1 状态码不是200

先打印：

```python
print(response.status_code)
print(response.text[:500])
```

常见状态码：

| 状态码 | 意思 | 应该怎么做 |
|---:|---|---|
| 200 | 成功 | 继续解析 |
| 400 | 查询参数有问题 | 检查参数名和内容 |
| 404 | 地址不存在 | 对照教程检查 API 地址 |
| 429 | 请求太快 | 停止程序，稍后再试并增加等待 |
| 500/503 | 服务器临时异常 | 等待后重试 |

### 7.9.2 `JSONDecodeError`

说明返回内容不是正常 JSON。先检查状态码，再打印开头内容：

```python
print(response.status_code)
print(response.text[:500])
```

不要直接删除 `response.json()`，应该先找到服务器为什么没有返回 JSON。

### 7.9.3 `KeyError`

例如：

```text
KeyError: 'officialTitle'
```

说明这条数据没有该字段。批量代码中改用：

```python
title = identification.get("officialTitle", "")
```

### 7.9.4 CSV 中文乱码

确认保存代码包含：

```python
encoding="utf-8-sig"
```

如果文件已经用其他编码生成，修改代码后需要重新运行并覆盖旧文件。

### 7.9.5 结果少于指定数量

可能原因：

- 查询本来就没有那么多结果；
- 已经到最后一页；
- 部分记录缺少唯一编号而被工程版跳过。

这不一定是程序错误。

### 7.9.6 修改代码后运行结果没有变化

检查三件事：

1. 是否按 `Ctrl+S` 保存；
2. 终端运行的文件名是否就是刚修改的文件；
3. VS Code 是否打开了正确项目文件夹。

---

## 7.10 课后练习（带提示）

### 练习1：换一个疾病（必做）

把第3步中的：

```python
"query.cond": "diabetes"
```

改成：

```python
"query.cond": "asthma"
```

重新运行，打开 CSV 检查结果。

### 练习2：把5条改成10条（必做）

提示：只需要修改 `pageSize`。

完成标准：CSV 中除表头外有10行数据。

### 练习3：增加研究类型（进阶）

研究类型的路径：

```text
protocolSection -> designModule -> studyType
```

提示代码：

```python
design_module = protocol.get("designModule", {})
study_type = design_module.get("studyType", "")
```

还要把 `study_type` 加入 `record` 和 `fieldnames`。

### 练习4：统计状态数量（进阶）

使用一个字典记录每种状态出现的次数。例如：

```python
status_count = {}

for record in records:
    status = record["status"]
    status_count[status] = status_count.get(status, 0) + 1

print(status_count)
```

### 练习5：验证下一页没有重复（挑战）

把所有 NCT 编号放入集合：

```python
ids = set()
```

比较 `len(ids)` 和 `len(all_records)`。如果相同，说明编号没有重复。

---

## 项目总结

### 你已经会做什么

- 知道 HTML 页面和 JSON API 的区别；
- 能看懂 JSON 中的字典和列表；
- 能用 `params` 发送查询条件；
- 能从多层字典中提取字段；
- 能用 `for` 循环处理多条记录；
- 能把列表字段整理后写入 CSV；
- 能使用 `nextPageToken` 获取下一页；
- 知道先验证少量数据，再扩大采集规模。

### 离开本项目之前，请逐项自检

- [ ] 第1步能输出状态码200
- [ ] 第2步能打印1条研究的5个字段
- [ ] 第3步能生成包含5条数据的 CSV
- [ ] 第4步能连续获取3页
- [ ] 能用一句话解释 `nextPageToken`
- [ ] 能说出为什么要保留 `time.sleep(1)`

全部完成后，再进入项目8。项目8会使用相同的 API 思想，但服务器返回的详情是 XML。
