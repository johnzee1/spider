import csv
from urllib.parse import urljoin

import requests
from lxml import html

URL = "https://www.a-hospital.com/w/%E9%9D%92%E9%9C%89%E7%B4%A0"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_tree(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return html.fromstring(response.content)


def get_links(tree, base_url):
    rows = []
    for tag in tree.xpath("//a[@href]"):
        name = " ".join(tag.xpath(".//text()")).strip()
        href = tag.get("href")
        if len(name) >= 2 and href:
            rows.append({"名称": name, "链接": urljoin(base_url, href)})
    return rows[:20]


def main():
    tree = download_tree(URL)
    rows = get_links(tree, URL)
    with open("medicine_links.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["名称", "链接"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"保存完成，共 {len(rows)} 条")


if __name__ == "__main__":
    main()
