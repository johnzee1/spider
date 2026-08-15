import csv
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.satcm.gov.cn/xwzx/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_html(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_news(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()
    for link in soup.select("a[href]"):
        title = link.get_text(" ", strip=True)
        if len(title) < 8 or title in seen:
            continue
        seen.add(title)
        rows.append({"标题": title, "链接": urljoin(base_url, link["href"])})
    return rows[:20]


def save_csv(rows, filename):
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["标题", "链接"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = parse_news(download_html(URL), URL)
    save_csv(rows, "news.csv")
    print(f"保存完成，共 {len(rows)} 条，文件是 news.csv")


if __name__ == "__main__":
    main()
