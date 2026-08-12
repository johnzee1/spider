# -*- coding: utf-8 -*-
"""项目8第2步：先搜索1个 PMID，再下载这篇文献的 XML。"""

import requests


my_email = "your_email@example.com"  # 改成自己的邮箱
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 第一次请求：搜索1个 PMID。
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

# 第二次请求：用 PMID 获取详情 XML。
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

xml_text = fetch_response.text
print("XML长度：", len(xml_text), "个字符")
print("XML开头500个字符：")
print(xml_text[:500])

with open("one_article.xml", "w", encoding="utf-8") as file:
    file.write(xml_text)

print("保存完成：one_article.xml")
