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
