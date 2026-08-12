# -*- coding: utf-8 -*-
"""项目9第3步：读取项目8的第一篇摘要并进行固定字段抽取。"""

import json
import requests


# 读取项目8生成的 JSON 文件。
with open("pubmed_data/pubmed_articles.json", "r", encoding="utf-8") as file:
    articles = json.load(file)

# 找到第一篇有摘要的文献。
article = None
for item in articles:
    if item.get("abstract"):
        article = item
        break

if article is None:
    print("没有找到带摘要的文献，请先检查项目8的结果。")
    raise SystemExit

# Schema 像一张必须填写的表格，规定AI要返回哪些字段。
schema = {
    "type": "object",
    "properties": {
        "disease": {"type": "string"},
        "population": {"type": "string"},
        "intervention": {"type": "string"},
        "key_finding": {"type": "string"},
        "evidence_sentence": {"type": "string"},
    },
    "required": [
        "disease",
        "population",
        "intervention",
        "key_finding",
        "evidence_sentence",
    ],
}

prompt = (
    "只能根据以下标题和摘要提取信息。没有提到就填写‘未提及’。"
    "evidence_sentence必须逐字复制摘要中的一句英文原文。\n"
    "标题：" + article["title"] + "\n摘要：" + article["abstract"]
)

data = {
    "model": "qwen3:4b",
    "stream": False,
    "format": schema,
    "messages": [{"role": "user", "content": prompt}],
    "options": {"temperature": 0},
}

print("正在分析 PMID：", article["pmid"])
response = requests.post(
    "http://127.0.0.1:11434/api/chat", json=data, timeout=180
)
response.raise_for_status()
result = json.loads(response.json()["message"]["content"])

# 最简单的证据校验：检查证据原句是否真的出现在原摘要中。
evidence = result["evidence_sentence"].strip()
evidence_found = bool(evidence) and evidence in article["abstract"]

print(json.dumps(result, ensure_ascii=False, indent=2))
print("证据原句是否存在于摘要：", evidence_found)
print("原文地址：", article["source_url"])
