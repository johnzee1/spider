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
