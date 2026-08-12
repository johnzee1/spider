# -*- coding: utf-8 -*-
"""项目9：用本地 Ollama 大模型结构化分析 PubMed 公开摘要。"""

import argparse
import csv
import json
import os
import time
from pathlib import Path

import requests


DEFAULT_INPUT = Path("pubmed_data/pubmed_articles.json")
DEFAULT_OUTPUT_DIR = Path("ai_pubmed_data")
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("AI_MODEL", "qwen3:4b")

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "chinese_title": {"type": "string"},
        "study_type": {"type": "string"},
        "disease": {"type": "string"},
        "population": {"type": "string"},
        "intervention": {"type": "string"},
        "outcome": {"type": "string"},
        "key_finding": {"type": "string"},
        "evidence_sentence": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "chinese_title",
        "study_type",
        "disease",
        "population",
        "intervention",
        "outcome",
        "key_finding",
        "evidence_sentence",
        "confidence",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """你是医学文献数据整理助手，不是医生。
只能根据用户提供的标题和摘要抽取信息，不得补充常识、猜测或给出诊疗建议。
信息未出现时填写“未提及”。evidence_sentence 必须逐字摘自原摘要；如果摘要没有
能支持 key_finding 的句子，则 evidence_sentence 填写空字符串，并降低 confidence。
除 evidence_sentence 保留原文外，其余字段使用简洁中文。"""


def load_articles(path):
    with path.open("r", encoding="utf-8") as file:
        articles = json.load(file)
    if not isinstance(articles, list):
        raise ValueError("输入 JSON 的最外层必须是列表")
    return articles


def check_ollama(base_url, model):
    response = requests.get(f"{base_url}/api/tags", timeout=10)
    response.raise_for_status()
    names = {item.get("name", "") for item in response.json().get("models", [])}
    if model not in names and not any(name.startswith(model + ":") for name in names):
        raise RuntimeError(f"没有找到模型 {model}，请先运行：ollama pull {model}")


def build_user_prompt(article):
    return (
        f"PMID: {article.get('pmid', '')}\n"
        f"标题: {article.get('title', '')}\n"
        f"摘要:\n{article.get('abstract', '')}"
    )


def call_ollama(article, base_url, model, retries=3):
    payload = {
        "model": model,
        "stream": False,
        "format": OUTPUT_SCHEMA,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(article)},
        ],
        "options": {"temperature": 0},
    }
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                f"{base_url}/api/chat", json=payload, timeout=180
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            return json.loads(content)
        except (requests.RequestException, KeyError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"模型调用失败：{last_error}")


def normalize_text(text):
    return " ".join((text or "").split()).lower()


def validate_result(article, result):
    missing = [key for key in OUTPUT_SCHEMA["required"] if key not in result]
    if missing:
        raise ValueError("模型缺少字段：" + ", ".join(missing))

    confidence = float(result["confidence"])
    result["confidence"] = max(0.0, min(1.0, confidence))
    evidence = normalize_text(result.get("evidence_sentence", ""))
    abstract = normalize_text(article.get("abstract", ""))
    evidence_found = bool(evidence) and evidence in abstract
    result["review_status"] = "passed" if evidence_found else "needs_review"
    result["evidence_found"] = evidence_found
    return result


def append_jsonl(path, data):
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def save_csv(path, records):
    if not records:
        return
    fields = [
        "pmid",
        "source_url",
        "original_title",
        *OUTPUT_SCHEMA["required"],
        "evidence_found",
        "review_status",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def run(input_path, output_dir, base_url, model, max_articles):
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "ai_results.jsonl"
    csv_path = output_dir / "ai_results.csv"
    error_path = output_dir / "errors.jsonl"

    check_ollama(base_url, model)
    articles = [item for item in load_articles(input_path) if item.get("abstract")]
    articles = articles[:max_articles]
    records = load_jsonl(jsonl_path)
    finished = {record["pmid"] for record in records if record.get("pmid")}

    print(f">>> 待分析文献：{len(articles)} 篇，已完成：{len(finished)} 篇")
    for index, article in enumerate(articles, start=1):
        pmid = article.get("pmid", "")
        if pmid in finished:
            print(f">>> [{index}/{len(articles)}] PMID {pmid} 已完成，跳过")
            continue
        try:
            result = validate_result(
                article, call_ollama(article, base_url, model)
            )
            record = {
                "pmid": pmid,
                "source_url": article.get("source_url", ""),
                "original_title": article.get("title", ""),
                **result,
            }
            append_jsonl(jsonl_path, record)
            records.append(record)
            finished.add(pmid)
            print(
                f">>> [{index}/{len(articles)}] PMID {pmid}："
                f"{record['review_status']}"
            )
        except (RuntimeError, ValueError) as error:
            append_jsonl(error_path, {"pmid": pmid, "error": str(error)})
            print(f">>> [{index}/{len(articles)}] PMID {pmid} 失败：{error}")

    save_csv(csv_path, records)
    print(f">>> 完成！结果：{csv_path}")
    print(f">>> 其中需人工复核：{sum(r['review_status'] == 'needs_review' for r in records)} 篇")


def main():
    parser = argparse.ArgumentParser(description="AI + PubMed 医学文献结构化抽取")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-articles", type=int, default=20)
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"找不到输入文件：{args.input}，请先完成项目8")
    if args.max_articles < 1:
        parser.error("--max-articles 必须大于 0")
    run(
        args.input,
        args.output_dir,
        args.ollama_url.rstrip("/"),
        args.model,
        args.max_articles,
    )


if __name__ == "__main__":
    main()
