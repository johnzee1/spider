# -*- coding: utf-8 -*-
"""项目8第1步：在 PubMed 中搜索3个 PMID。"""

import requests


# 请把下面的邮箱改成你自己的邮箱。
my_email = "your_email@example.com"

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",                       # 在 PubMed 数据库中搜索
    "term": "diabetes[Title/Abstract]",   # 在标题或摘要中找 diabetes
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
