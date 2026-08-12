# -*- coding: utf-8 -*-
"""项目9第1步：向本机 Ollama 发送第一条消息。"""

import requests


url = "http://127.0.0.1:11434/api/chat"

data = {
    "model": "qwen3:4b",
    "stream": False,
    "messages": [
        {
            "role": "user",
            "content": "请用一句中文解释什么是医学文献摘要。",
        }
    ],
}

print("正在等待本地 AI 回答，第一次运行可能较慢...")
response = requests.post(url, json=data, timeout=180)
print("状态码：", response.status_code)
response.raise_for_status()

answer = response.json()["message"]["content"]
print("AI回答：")
print(answer)
