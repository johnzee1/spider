# -*- coding: utf-8 -*-
"""项目8第4步：搜索并保存10篇 PubMed 文献。"""

import csv
import time
import xml.etree.ElementTree as ET

import requests


my_email = "your_email@example.com"  # 改成自己的邮箱
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def get_all_text(node):
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


# 第一步：搜索10个 PMID。
search_params = {
    "db": "pubmed",
    "term": "diabetes[Title/Abstract]",
    "retmode": "json",
    "retmax": 10,
    "tool": "medical_data_course",
    "email": my_email,
}
response = requests.get(
    base_url + "/esearch.fcgi", params=search_params, timeout=30
)
response.raise_for_status()
pmids = response.json()["esearchresult"]["idlist"]
print("找到", len(pmids), "个 PMID")

# 礼貌等待0.4秒，再发送详情请求。
time.sleep(0.4)

# 第二步：一次提交10个 PMID，批量获取详情。
fetch_params = {
    "db": "pubmed",
    "id": ",".join(pmids),
    "retmode": "xml",
    "rettype": "abstract",
    "tool": "medical_data_course",
    "email": my_email,
}
response = requests.get(
    base_url + "/efetch.fcgi", params=fetch_params, timeout=60
)
response.raise_for_status()
root = ET.fromstring(response.content)

# 第三步：逐篇提取字段。
records = []
for article_node in root.findall("PubmedArticle"):
    pmid = get_all_text(article_node.find(".//PMID"))
    title = get_all_text(article_node.find(".//ArticleTitle"))
    journal = get_all_text(article_node.find(".//Journal/Title"))

    abstract_parts = []
    for part in article_node.findall(".//Abstract/AbstractText"):
        abstract_parts.append(get_all_text(part))
    abstract = " ".join(abstract_parts)

    record = {
        "pmid": pmid,
        "title": title,
        "journal": journal,
        "abstract": abstract,
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/",
    }
    records.append(record)
    print("已整理：", pmid, title)

# 第四步：保存 CSV。
with open("pubmed_10.csv", "w", encoding="utf-8-sig", newline="") as file:
    fieldnames = ["pmid", "title", "journal", "abstract", "source_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print("保存完成：pubmed_10.csv")
