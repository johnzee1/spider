# -*- coding: utf-8 -*-
import csv
import importlib.util
import io
import json
import os
import runpy
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


clinical = load_module(
    "clinical_trials_spider", "docs/项目7/clinical_trials_spider.py"
)
pubmed = load_module("pubmed_spider", "docs/项目8/pubmed_spider.py")
ai_spider = load_module("ai_pubmed_spider", "docs/项目9/ai_pubmed_spider.py")


class FakeAiResponse:
    def __init__(self, result):
        self.result = result
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"message": {"content": json.dumps(self.result, ensure_ascii=False)}}


def fake_ai_post(url, json=None, timeout=None):
    return FakeAiResponse(
        {
            "chinese_title": "示例治疗的效果",
            "study_type": "临床试验",
            "disease": "糖尿病",
            "population": "成年人",
            "intervention": "示例治疗",
            "outcome": "结局改善",
            "key_finding": "治疗改善了结局",
            "evidence_sentence": "The treatment improved the outcome.",
            "confidence": 0.9,
        }
    )


def clinical_study(nct_id, title):
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": title},
            "statusModule": {
                "overallStatus": "COMPLETED",
                "startDateStruct": {"date": "2024-01"},
            },
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 30},
            },
            "conditionsModule": {"conditions": ["Diabetes"]},
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Example University"}
            },
            "contactsLocationsModule": {
                "locations": [
                    {"country": "China"},
                    {"country": "China"},
                    {"country": "United States"},
                ]
            },
            "descriptionModule": {"briefSummary": "A public study."},
        }
    }


PUBMED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1001</PMID>
      <Article>
        <Journal>
          <JournalIssue><PubDate><Year>2026</Year><Month>Jan</Month></PubDate></JournalIssue>
          <Title>Journal of Tests</Title>
        </Journal>
        <ArticleTitle>Effects of <i>Example</i> Treatment</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="RESULTS">The treatment improved the outcome.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Zhang</LastName><Initials>Y</Initials></Author>
          <Author><CollectiveName>Example Group</CollectiveName></Author>
        </AuthorList>
        <PublicationTypeList><PublicationType>Clinical Trial</PublicationType></PublicationTypeList>
      </Article>
      <MeshHeadingList>
        <MeshHeading><DescriptorName>Diabetes Mellitus</DescriptorName></MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList><ArticleId IdType="doi">10.1000/test</ArticleId></ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class FakeApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def send_body(self, body, content_type):
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/studies":
            if "pageToken" in query:
                payload = {"studies": [clinical_study("NCT0002", "Page two")]}
            else:
                payload = {
                    "studies": [clinical_study("NCT0001", "Page one")],
                    "nextPageToken": "page-two",
                }
            self.send_body(json.dumps(payload), "application/json")
            return

        if parsed.path.endswith("/esearch.fcgi"):
            self.send_body(
                json.dumps({"esearchresult": {"count": "1", "idlist": ["1001"]}}),
                "application/json",
            )
            return

        if parsed.path.endswith("/efetch.fcgi"):
            self.send_body(PUBMED_XML, "application/xml")
            return

        if parsed.path == "/api/tags":
            self.send_body(
                json.dumps({"models": [{"name": "qwen3:4b"}]}),
                "application/json",
            )
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        json.loads(self.rfile.read(content_length))
        result = {
            "chinese_title": "示例治疗的效果",
            "study_type": "临床试验",
            "disease": "糖尿病",
            "population": "未提及",
            "intervention": "示例治疗",
            "outcome": "结局改善",
            "key_finding": "治疗改善了结局",
            "evidence_sentence": "The treatment improved the outcome.",
            "confidence": 0.9,
        }
        self.send_body(
            json.dumps({"message": {"content": json.dumps(result)}}),
            "application/json",
        )


class NewProjectsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeApiHandler)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_clinical_trials_cursor_pagination_and_files(self):
        original_url = clinical.API_URL
        clinical.API_URL = f"{self.base_url}/studies"
        try:
            with tempfile.TemporaryDirectory() as directory:
                output_dir = Path(directory)
                records = clinical.crawl(
                    "diabetes", 2, 1, output_dir, resume=False
                )
                self.assertEqual(["NCT0001", "NCT0002"], [r["nct_id"] for r in records])
                self.assertEqual("China | United States", records[0]["countries"])
                self.assertTrue((output_dir / "clinical_trials.csv").exists())
                self.assertFalse((output_dir / "checkpoint.json").exists())
        finally:
            clinical.API_URL = original_url

    def test_clinical_trials_rejects_mismatched_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            (output_dir / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "condition": "asthma",
                        "next_page_token": "page-two",
                        "saved_records": 1,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "断点属于"):
                clinical.crawl("diabetes", 2, 1, output_dir, resume=True)

    def test_pubmed_search_fetch_parse_and_stats(self):
        original_url = pubmed.BASE_URL
        pubmed.BASE_URL = f"{self.base_url}/entrez/eutils"
        try:
            session = pubmed.create_session()
            pmids = pubmed.search_pmids(session, "diabetes", 1, "student@example.com")
            records = pubmed.fetch_articles(session, pmids, "student@example.com")
            self.assertEqual(["1001"], pmids)
            self.assertEqual("Effects of Example Treatment", records[0]["title"])
            self.assertEqual(["Zhang Y", "Example Group"], records[0]["authors"])
            self.assertIn("RESULTS: The treatment improved", records[0]["abstract"])
            self.assertEqual("10.1000/test", records[0]["doi"])

            with tempfile.TemporaryDirectory() as directory:
                paths = pubmed.save_results(records, Path(directory))
                self.assertTrue(all(path.exists() for path in paths))
                stats = json.loads(paths[2].read_text(encoding="utf-8"))
                self.assertEqual(1, stats["with_abstract"])
        finally:
            pubmed.BASE_URL = original_url

    def test_ai_pipeline_structured_output_and_evidence(self):
        articles = [
            {
                "pmid": "1001",
                "title": "Effects of Example Treatment",
                "abstract": "The treatment improved the outcome.",
                "source_url": "https://pubmed.ncbi.nlm.nih.gov/1001/",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            input_path = temp_dir / "articles.json"
            output_dir = temp_dir / "output"
            input_path.write_text(
                json.dumps(articles, ensure_ascii=False), encoding="utf-8"
            )
            ai_spider.run(
                input_path, output_dir, self.base_url, "qwen3:4b", max_articles=1
            )
            records = ai_spider.load_jsonl(output_dir / "ai_results.jsonl")
            self.assertEqual("passed", records[0]["review_status"])
            self.assertTrue(records[0]["evidence_found"])
            self.assertTrue((output_dir / "ai_results.csv").exists())

            # 再运行一次应识别已经完成的 PMID，不重复追加。
            ai_spider.run(
                input_path, output_dir, self.base_url, "qwen3:4b", max_articles=1
            )
            self.assertEqual(
                1, len(ai_spider.load_jsonl(output_dir / "ai_results.jsonl"))
            )

    def test_ai_classroom_steps_run_in_order(self):
        articles = [
            {
                "pmid": str(1000 + number),
                "title": f"Example article {number}",
                "abstract": "The treatment improved the outcome.",
                "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{1000 + number}/",
            }
            for number in range(1, 6)
        ]
        step_files = [
            ROOT / "docs/项目9/step1_chat_with_ai.py",
            ROOT / "docs/项目9/step2_analyze_one.py",
            ROOT / "docs/项目9/step3_analyze_first_pubmed.py",
            ROOT / "docs/项目9/step4_analyze_five.py",
        ]

        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            input_dir = temp_dir / "pubmed_data"
            input_dir.mkdir()
            (input_dir / "pubmed_articles.json").write_text(
                json.dumps(articles, ensure_ascii=False), encoding="utf-8"
            )

            original_cwd = Path.cwd()
            output = io.StringIO()
            try:
                os.chdir(temp_dir)
                with patch("requests.post", side_effect=fake_ai_post):
                    with redirect_stdout(output):
                        for step_file in step_files:
                            runpy.run_path(str(step_file), run_name="__main__")
            finally:
                os.chdir(original_cwd)

            printed = output.getvalue()
            self.assertIn("状态码： 200", printed)
            self.assertIn("证据原句是否存在于摘要： True", printed)
            self.assertIn("保存完成：ai_results_5.csv，共 5 条", printed)

            with (temp_dir / "ai_results_5.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(5, len(rows))
            self.assertTrue(all(row["evidence_found"] == "True" for row in rows))


if __name__ == "__main__":
    unittest.main()
