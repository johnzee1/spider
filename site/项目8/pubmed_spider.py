# -*- coding: utf-8 -*-
"""项目8：使用 NCBI E-utilities 批量采集 PubMed 医学文献。"""

import argparse
import csv
import json
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_OUTPUT_DIR = Path("pubmed_data")


def create_session():
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.headers.update({"User-Agent": "medical-data-course/1.0"})
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def node_text(node):
    """读取 XML 节点及其子节点里的全部文字。"""
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def parse_date(article_node):
    article_date = article_node.find(".//ArticleDate")
    if article_date is not None:
        year = node_text(article_date.find("Year"))
        month = node_text(article_date.find("Month"))
        day = node_text(article_date.find("Day"))
        return "-".join(part for part in [year, month, day] if part)

    pub_date = article_node.find(".//JournalIssue/PubDate")
    if pub_date is None:
        return ""
    medline_date = node_text(pub_date.find("MedlineDate"))
    if medline_date:
        return medline_date
    year = node_text(pub_date.find("Year"))
    month = node_text(pub_date.find("Month"))
    return "-".join(part for part in [year, month] if part)


def parse_authors(article_node):
    authors = []
    for author in article_node.findall(".//AuthorList/Author"):
        collective = node_text(author.find("CollectiveName"))
        if collective:
            authors.append(collective)
            continue
        last_name = node_text(author.find("LastName"))
        initials = node_text(author.find("Initials"))
        full_name = " ".join(part for part in [last_name, initials] if part)
        if full_name:
            authors.append(full_name)
    return authors


def parse_abstract(article_node):
    sections = []
    for abstract_node in article_node.findall(".//Abstract/AbstractText"):
        text = node_text(abstract_node)
        if not text:
            continue
        label = abstract_node.attrib.get("Label", "").strip()
        sections.append(f"{label}: {text}" if label else text)
    return "\n".join(sections)


def parse_article(article_node):
    pmid = node_text(article_node.find(".//MedlineCitation/PMID"))
    mesh_terms = [
        node_text(node)
        for node in article_node.findall(".//MeshHeading/DescriptorName")
        if node_text(node)
    ]
    publication_types = [
        node_text(node)
        for node in article_node.findall(".//PublicationTypeList/PublicationType")
        if node_text(node)
    ]
    return {
        "pmid": pmid,
        "title": node_text(article_node.find(".//ArticleTitle")),
        "abstract": parse_abstract(article_node),
        "journal": node_text(article_node.find(".//Journal/Title")),
        "publication_date": parse_date(article_node),
        "authors": parse_authors(article_node),
        "mesh_terms": mesh_terms,
        "publication_types": publication_types,
        "doi": next(
            (
                node_text(node)
                for node in article_node.findall(".//ArticleId")
                if node.attrib.get("IdType") == "doi"
            ),
            "",
        ),
        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def search_pmids(session, term, max_records, email, api_key=""):
    pmids = []
    batch_size = min(100, max_records)
    for start in range(0, max_records, batch_size):
        params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retstart": start,
            "retmax": min(batch_size, max_records - start),
            "sort": "pub date",
            "tool": "medical_data_course",
            "email": email,
        }
        if api_key:
            params["api_key"] = api_key
        response = session.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()["esearchresult"]
        ids = result.get("idlist", [])
        pmids.extend(ids)
        print(f">>> 搜索进度：{len(pmids)}/{min(int(result['count']), max_records)}")
        if not ids or len(pmids) >= int(result["count"]):
            break
        time.sleep(0.4 if not api_key else 0.15)
    return pmids[:max_records]


def fetch_articles(session, pmids, email, api_key=""):
    records = []
    batch_size = 100
    for start in range(0, len(pmids), batch_size):
        batch = pmids[start : start + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
            "tool": "medical_data_course",
            "email": email,
        }
        if api_key:
            params["api_key"] = api_key
        response = session.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        records.extend(parse_article(node) for node in root.findall("PubmedArticle"))
        print(f">>> 详情进度：{len(records)}/{len(pmids)}")
        time.sleep(0.4 if not api_key else 0.15)
    return records


def save_results(records, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "pubmed_articles.json"
    csv_path = output_dir / "pubmed_articles.csv"
    stats_path = output_dir / "pubmed_stats.json"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    csv_records = []
    for record in records:
        row = record.copy()
        row["authors"] = " | ".join(row["authors"])
        row["mesh_terms"] = " | ".join(row["mesh_terms"])
        row["publication_types"] = " | ".join(row["publication_types"])
        csv_records.append(row)
    if csv_records:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=csv_records[0].keys())
            writer.writeheader()
            writer.writerows(csv_records)

    years = Counter(record["publication_date"][:4] for record in records if record["publication_date"])
    journals = Counter(record["journal"] for record in records if record["journal"])
    mesh = Counter(term for record in records for term in record["mesh_terms"])
    stats = {
        "article_count": len(records),
        "with_abstract": sum(bool(record["abstract"]) for record in records),
        "top_years": years.most_common(10),
        "top_journals": journals.most_common(10),
        "top_mesh_terms": mesh.most_common(20),
    }
    with stats_path.open("w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)
    return json_path, csv_path, stats_path


def main():
    parser = argparse.ArgumentParser(description="PubMed 医学文献公开数据爬虫")
    parser.add_argument("--term", default="diabetes[Title/Abstract]", help="PubMed 检索式")
    parser.add_argument("--max-records", type=int, default=100, help="最多采集条数")
    parser.add_argument("--email", required=True, help="按 NCBI 要求填写自己的联系邮箱")
    parser.add_argument("--api-key", default="", help="可选：NCBI API Key")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not 1 <= args.max_records <= 9999:
        parser.error("--max-records 必须在 1 到 9999 之间")

    session = create_session()
    pmids = search_pmids(
        session, args.term, args.max_records, args.email, args.api_key
    )
    print(f">>> 找到 {len(pmids)} 个 PMID，开始批量获取详情")
    records = fetch_articles(session, pmids, args.email, args.api_key)
    paths = save_results(records, args.output_dir)
    print(f">>> 完成，共保存 {len(records)} 篇文献")
    for path in paths:
        print(f"    {path}")


if __name__ == "__main__":
    main()
