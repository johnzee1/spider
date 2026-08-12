# -*- coding: utf-8 -*-
"""项目7第4步：使用 nextPageToken 连续获取3页数据。"""

import time
import requests


url = "https://clinicaltrials.gov/api/v2/studies"
page_token = None
all_records = []

# 为了课堂演示，只取3页，每页5条。
for page_number in range(1, 4):
    params = {
        "query.cond": "diabetes",
        "pageSize": 5,
        "format": "json",
    }

    # 第1页没有令牌；从第2页开始使用上一页返回的令牌。
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

    # 记住服务器给出的下一页令牌。
    page_token = data.get("nextPageToken")
    if page_token is None:
        print("已经没有下一页。")
        break

    # 每页之间休息1秒，避免请求过快。
    time.sleep(1)

print("\n前3条结果：")
for record in all_records[:3]:
    print(record["nct_id"], record["title"])
