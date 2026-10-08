"""Tests for link_extractor.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from link_extractor import extract_links, to_csv, to_json, to_text

SAMPLE = """
<html>
<head>
  <link rel="stylesheet" href="/static/app.css">
  <script src="https://cdn.example.com/lib.js"></script>
</head>
<body>
  <a href="/about">About <b>us</b></a>
  <a href="https://external.com/x">External</a>
  <a href="#top">Top</a>
  <a href="javascript:void(0)">Noop</a>
  <a>No href</a>
  <img src="logo.png" alt="logo">
  <iframe src="https://player.example.com/e/1"></iframe>
</body>
</html>
"""


class TestLinkExtractor(unittest.TestCase):
    def setUp(self):
        self.records = extract_links(SAMPLE, base="https://example.com")

    def test_counts_all_link_bearing_tags(self):
        # 5 anchors (incl. the no-href one) + link + script + img + iframe = 9
        self.assertEqual(len(self.records), 9)

    def test_document_order_and_tag(self):
        tags = [r["tag"] for r in self.records]
        self.assertEqual(tags[0], "link")
        self.assertEqual(tags[1], "script")
        self.assertEqual(tags[2], "a")

    def test_anchor_text_collected(self):
        anchor = [r for r in self.records if r["text"] == "About us"]
        self.assertEqual(len(anchor), 1)
        self.assertEqual(anchor[0]["url"], "/about")

    def test_relative_url_resolution(self):
        anchor = [r for r in self.records if r["text"] == "About us"][0]
        self.assertEqual(anchor["resolved_url"], "https://example.com/about")
        self.assertEqual(anchor["kind"], "internal")
        self.assertFalse(anchor["skipped"])

    def test_external_classification(self):
        ext = [r for r in self.records if r["text"] == "External"][0]
        self.assertEqual(ext["kind"], "external")
        self.assertFalse(ext["skipped"])

    def test_fragments_and_javascript_skipped(self):
        skipped = {r["kind"] for r in self.records if r["skipped"]}
        self.assertIn("fragment", skipped)
        self.assertIn("javascript", skipped)

    def test_empty_href_recorded(self):
        empty = [r for r in self.records if r["kind"] == "empty"]
        self.assertEqual(len(empty), 1)  # the <a> with no href

    def test_resource_tags_have_correct_attribute(self):
        img = [r for r in self.records if r["tag"] == "img"][0]
        self.assertEqual(img["attribute"], "src")
        self.assertEqual(img["url"], "logo.png")

    def test_no_base_keeps_kinds(self):
        records = extract_links(SAMPLE)
        rel = [r for r in records if r["url"] == "/about"][0]
        self.assertEqual(rel["kind"], "relative")
        self.assertEqual(rel["resolved_url"], "/about")

    def test_text_output_summary(self):
        text = to_text(self.records)
        self.assertIn("Total: 9 links", text)

    def test_csv_has_header_and_rows(self):
        csv_out = to_csv(self.records)
        lines = csv_out.strip().splitlines()
        self.assertTrue(lines[0].startswith("no,tag,attribute"))
        self.assertEqual(len(lines), 10)

    def test_json_is_valid(self):
        import json
        data = json.loads(to_json(self.records))
        self.assertEqual(data["total"], 9)
        self.assertEqual(len(data["links"]), 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
