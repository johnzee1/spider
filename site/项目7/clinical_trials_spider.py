# -*- coding: utf-8 -*-
"""项目7：批量采集 ClinicalTrials.gov 公开临床试验数据。"""

import argparse
import csv
import json
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_OUTPUT_DIR = Path("clinical_trials_data")


def create_session():
    """创建带自动重试的请求会话。"""
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "medical-data-course/1.0 (classroom learning)",
            "Accept": "application/json",
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def get_nested(data, *keys, default=""):
    """安全读取多层字典，任何一层不存在都返回默认值。"""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current if current is not None else default


def join_values(values):
    """把列表转换成适合 CSV 阅读的文本。"""
    return " | ".join(str(value) for value in (values or []) if value)


def parse_study(study):
    """把官方 API 的深层 JSON 整理成一行扁平数据。"""
    protocol = study.get("protocolSection", {})
    locations = get_nested(
        protocol, "contactsLocationsModule", "locations", default=[]
    )
    countries = sorted(
        {
            location.get("country", "")
            for location in locations
            if location.get("country")
        }
    )

    return {
        "nct_id": get_nested(protocol, "identificationModule", "nctId"),
        "title": get_nested(protocol, "identificationModule", "briefTitle"),
        "official_title": get_nested(
            protocol, "identificationModule", "officialTitle"
        ),
        "status": get_nested(protocol, "statusModule", "overallStatus"),
        "study_type": get_nested(protocol, "designModule", "studyType"),
        "phases": join_values(
            get_nested(protocol, "designModule", "phases", default=[])
        ),
        "conditions": join_values(
            get_nested(protocol, "conditionsModule", "conditions", default=[])
        ),
        "enrollment": get_nested(
            protocol, "designModule", "enrollmentInfo", "count", default=""
        ),
        "sponsor": get_nested(
            protocol,
            "sponsorCollaboratorsModule",
            "leadSponsor",
            "name",
        ),
        "start_date": get_nested(
            protocol, "statusModule", "startDateStruct", "date"
        ),
        "completion_date": get_nested(
            protocol, "statusModule", "completionDateStruct", "date"
        ),
        "countries": join_values(countries),
        "brief_summary": get_nested(
            protocol, "descriptionModule", "briefSummary"
        ),
        "source_url": (
            "https://clinicaltrials.gov/study/"
            + get_nested(protocol, "identificationModule", "nctId")
        ),
    }


def load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_csv(path, records):
    if not records:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def crawl(condition, max_records, page_size, output_dir, resume=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "clinical_trials.json"
    csv_path = output_dir / "clinical_trials.csv"
    checkpoint_path = output_dir / "checkpoint.json"

    records = load_json(json_path, []) if resume else []
    checkpoint = load_json(checkpoint_path, {}) if resume else {}
    saved_condition = checkpoint.get("condition")
    if resume and saved_condition and saved_condition != condition:
        raise ValueError(
            f"断点属于 {saved_condition!r}，不能用 {condition!r} 继续。"
            "请改回原条件，或更换输出目录重新运行。"
        )
    page_token = checkpoint.get("next_page_token")
    seen_ids = {record["nct_id"] for record in records if record.get("nct_id")}
    session = create_session()
    page_number = 0

    print(f">>> 检索疾病/主题：{condition}")
    print(f">>> 本次最多采集：{max_records} 条")

    while len(records) < max_records:
        page_number += 1
        params = {
            "query.cond": condition,
            "pageSize": min(page_size, max_records - len(records)),
            "format": "json",
        }
        if page_token:
            params["pageToken"] = page_token

        print(f">>> 正在请求第 {page_number} 页...", end="")
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        studies = payload.get("studies", [])

        if not studies:
            print("没有更多数据")
            break

        for study in studies:
            record = parse_study(study)
            if record["nct_id"] and record["nct_id"] not in seen_ids:
                records.append(record)
                seen_ids.add(record["nct_id"])
                if len(records) >= max_records:
                    break

        page_token = payload.get("nextPageToken")
        save_json(json_path, records)
        save_csv(csv_path, records)
        save_json(
            checkpoint_path,
            {
                "condition": condition,
                "next_page_token": page_token,
                "saved_records": len(records),
            },
        )
        print(f"已累计 {len(records)} 条")

        if not page_token:
            break
        time.sleep(1)

    if checkpoint_path.exists():
        checkpoint_path.unlink()
    print(f">>> 完成！JSON：{json_path}")
    print(f">>> 完成！CSV ：{csv_path}")
    return records


def main():
    parser = argparse.ArgumentParser(description="ClinicalTrials.gov 公开数据爬虫")
    parser.add_argument("--condition", default="diabetes", help="疾病或研究主题")
    parser.add_argument("--max-records", type=int, default=100, help="最多采集条数")
    parser.add_argument("--page-size", type=int, default=50, help="每页条数")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="输出目录"
    )
    parser.add_argument("--resume", action="store_true", help="从断点继续")
    args = parser.parse_args()

    if args.max_records < 1 or args.page_size < 1:
        parser.error("--max-records 和 --page-size 必须大于 0")

    crawl(
        condition=args.condition,
        max_records=args.max_records,
        page_size=args.page_size,
        output_dir=args.output_dir,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
