# -*- coding: utf-8 -*-
"""项目9第4步：分析5篇 PubMed 摘要并保存 CSV。"""

import csv
import json
import time

import requests


with open("pubmed_data/pubmed_articles.json", "r", encoding="utf-8") as file:
    all_articles = json.load(file)

# 只选前5篇有摘要的文献，避免第一次批量运行等待太久。
articles = []
for item in all_articles:
    if item.get("abstract"):
        articles.append(item)
    if len(articles) == 5:
        break

schema = {
    "type": "object",
    "properties": {
        "disease": {"type": "string"},
        "study_type": {"type": "string"},
        "key_finding": {"type": "string"},
        "evidence_sentence": {"type": "string"},
    },
    "required": ["disease", "study_type", "key_finding", "evidence_sentence"],
}

records = []

for number, article in enumerate(articles, start=1):
    print("正在分析第", number, "篇，PMID：", article["pmid"])

    prompt = (
        "只能根据下面的标题和摘要提取信息，不得猜测。"
        "没有出现的信息填写‘未提及’。evidence_sentence必须逐字复制原摘要。\n"
        "标题：" + article["title"] + "\n摘要：" + article["abstract"]
    )
    data = {
        "model": "qwen3:4b",
        "stream": False,
        "format": schema,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0},
    }

    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/chat", json=data, timeout=180
        )
        response.raise_for_status()
        result = json.loads(response.json()["message"]["content"])

        evidence = result["evidence_sentence"].strip()
        evidence_found = bool(evidence) and evidence in article["abstract"]

        record = {
            "pmid": article["pmid"],
            "title": article["title"],
            "disease": result["disease"],
            "study_type": result["study_type"],
            "key_finding": result["key_finding"],
            "evidence_sentence": evidence,
            "evidence_found": evidence_found,
            "source_url": article["source_url"],
        }
        records.append(record)
        print("成功，证据是否通过：", evidence_found)
    except Exception as error:
        # 一篇失败时，打印错误并继续处理下一篇。
        print("这一篇处理失败：", error)

    time.sleep(1)

with open("ai_results_5.csv", "w", encoding="utf-8-sig", newline="") as file:
    fieldnames = [
        "pmid", "title", "disease", "study_type", "key_finding",
        "evidence_sentence", "evidence_found", "source_url",
    ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print("保存完成：ai_results_5.csv，共", len(records), "条")
