import csv
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PAGE_URLS = [
    "https://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0",
    "https://www.a-hospital.com/w/%E9%98%BF%E8%8E%AB%E8%A5%BF%E6%9E%97",
]
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_one_page(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_links(soup, page_url):
    rows = []
    for link in soup.select("a[href]"):
        name = link.get_text(" ", strip=True)
        if len(name) >= 2:
            rows.append({"来源页面": page_url, "名称": name,
                         "链接": urljoin(page_url, link["href"])})
    return rows[:15]


def main():
    all_rows = []
    for number, url in enumerate(PAGE_URLS, start=1):
        print(f"正在处理第 {number} 页：{url}")
        all_rows.extend(parse_links(get_one_page(url), url))
        time.sleep(1)

    with open("medicine_pages.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["来源页面", "名称", "链接"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"保存完成，共 {len(all_rows)} 条")


if __name__ == "__main__":
    main()
