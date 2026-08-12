# -*- coding: utf-8 -*-
"""项目9第2步：让 AI 分析一段固定的示例摘要。"""

import json
import requests


title = "Walking after meals improves glycemic control"
abstract = (
    "Adults with type 2 diabetes were assigned to walk for 10 minutes "
    "after each main meal. Post-meal walking reduced postprandial glucose "
    "compared with a single 30-minute daily walk."
)

system_prompt = (
    "你是医学文献信息整理助手。只能根据给定标题和摘要回答，"
    "不能猜测，不能给出诊疗建议。请只返回JSON。"
)
user_prompt = (
    "请提取下面文献的疾病、研究人群、干预措施和主要发现。\n"
    "标题：" + title + "\n摘要：" + abstract
)

data = {
    "model": "qwen3:4b",
    "stream": False,
    "format": "json",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    "options": {"temperature": 0},
}

response = requests.post(
    "http://127.0.0.1:11434/api/chat", json=data, timeout=180
)
response.raise_for_status()

# content 现在是一段 JSON 字符串，再用 json.loads() 转成字典。
content = response.json()["message"]["content"]
result = json.loads(content)

print("AI返回的字典：")
print(json.dumps(result, ensure_ascii=False, indent=2))
