---
title: "项目3-XPath爬取医学百科药品数据"
---

# 项目3：用 XPath 爬取医学百科药品数据

XPath 是“在 HTML 树里找位置”的另一种写法。它不是新爬虫，只是换了一种定位标签的方法。

> 本章只做公开资料整理。采集到的药品信息不能代替医生、药师或说明书。

## 本章任务

下载一个公开医学百科页面，用 XPath 取出页面标题和前 20 个链接文字，保存为 CSV。

## 安装

```bash
pip install requests lxml
```

![安装 lxml 参考](Pasted%20image%2020260712083049.png)

## XPath 只记住三种写法

```python
tree.xpath("//h1/text()")        # 所有 h1 标签里的文字
tree.xpath("//a/@href")           # 所有 a 标签的 href 属性
tree.xpath("//a[@href]/text()")  # 有 href 的 a 标签里的文字
```

- `//` 表示从整张网页里找。
- `/text()` 表示要标签里的文字。
- `/@href` 表示要标签的 href 属性值。

## 完整代码

保存为 `xpath_medicine.py`，或下载本章的[完整代码](xpath_medicine.py)。页面地址可以换成任意公开的医学百科页面。

```python
import csv
from urllib.parse import urljoin

import requests
from lxml import html

URL = "https://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_tree(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return html.fromstring(response.content)


def get_links(tree, base_url):
    rows = []
    for tag in tree.xpath("//a[@href]"):
        name = " ".join(tag.xpath(".//text()")).strip()
        href = tag.get("href")
        if len(name) >= 2 and href:
            rows.append({"名称": name, "链接": urljoin(base_url, href)})
    return rows[:20]


def main():
    tree = download_tree(URL)
    title = tree.xpath("string(//title)").strip()
    print("页面标题：", title)

    rows = get_links(tree, URL)
    with open("medicine_links.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["名称", "链接"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"保存完成，共 {len(rows)} 条")


if __name__ == "__main__":
    main()
```

这里最重要的一行是 `tree.xpath("//a[@href]")`。它返回许多 `<a>` 元素；接着我们从每个元素取文字和 `href` 属性。

![XPath 定位参考](Pasted%20image%2020260712092924.png)

## 运行和排错

```bash
python xpath_medicine.py
```

| 现象 | 处理 |
|---|---|
| `No module named lxml` | 执行 `pip install lxml` |
| 标题为空 | 先打印 `response.status_code`，确认网页是否成功打开 |
| 链接太多 | 把 XPath 改成某个内容区域，例如 `//div[@id='content']//a[@href]` |
| 中文乱码 | CSV 文件必须使用 `utf-8-sig` 编码 |

## 小练习

1. 把 `rows[:20]` 改为 `rows[:10]`。
2. 用 `//h1/text()` 再取一次一级标题，和 `<title>` 比较。
3. 只保留链接地址中包含 `/w/` 的项目。

## 操作截图参考

![运行结果参考](Pasted%20image%2020260712100128.png)
