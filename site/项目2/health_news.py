import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://health.people.com.cn/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_soup(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_articles(soup, base_url):
    rows = []
    seen = set()
    for tag in soup.select("a[href]"):
        title = tag.get_text(" ", strip=True)
        if len(title) < 8 or title in seen:
            continue
        seen.add(title)
        rows.append({"title": title, "url": urljoin(base_url, tag["href"])})
    return rows[:20]


def main():
    rows = get_articles(get_soup(URL), URL)
    with open("health_news.json", "w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)
    print(f"保存完成，共 {len(rows)} 条")


if __name__ == "__main__":
    main()
