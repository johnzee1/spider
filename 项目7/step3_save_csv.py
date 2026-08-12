# -*- coding: utf-8 -*-
"""项目7第3步：提取5条临床试验并保存为CSV。"""

import csv
import requests


url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "diabetes",
    "pageSize": 5,
    "format": "json",
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
data = response.json()

records = []

for study in data["studies"]:
    # get() 找不到键时返回空字典，不会立刻报 KeyError。
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    conditions_module = protocol.get("conditionsModule", {})

    nct_id = identification.get("nctId", "")
    title = identification.get("briefTitle", "")
    status = status_module.get("overallStatus", "")
    conditions_list = conditions_module.get("conditions", [])

    # CSV的一个单元格适合放文字，把列表连接成普通字符串。
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

# utf-8-sig 可以减少中文在 Excel 中显示乱码的情况。
with open("clinical_trials_5.csv", "w", encoding="utf-8-sig", newline="") as file:
    fieldnames = ["nct_id", "title", "status", "conditions", "source_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print("保存完成：clinical_trials_5.csv")
