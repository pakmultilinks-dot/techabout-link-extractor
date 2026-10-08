#!/usr/bin/env python3
"""
Link Extractor
==============

Reads a saved HTML page (local file) and lists every link found in it.

What counts as a "link":
  - <a href="..."> anchor links (with their visible link text)
  - <link href="..."> stylesheet / icon references
  - <img src="..."> images
  - <script src="..."> scripts
  - <iframe src="..."> frames
  - <video>/<audio>/<source>/<track> src references

Output formats: human-readable text (default), CSV, or JSON.

Usage:
    python link_extractor.py page.html
    python link_extractor.py page.html --format csv --output links.csv
    python link_extractor.py page.html --format json --output links.json
    python link_extractor.py page.html --base https://example.com  (resolve relative URLs)

Notes:
  - Works on SAVED pages only: it never fetches anything from the internet.
  - Pass --base to resolve relative URLs (e.g. "/about") into absolute ones.
  - Empty or non-URL attributes (javascript:, # fragments) are reported but
    marked as skipped, not dropped silently.

TechAbout Python Developer task 1 - Link Extractor (ZR-26-00754).
"""

import argparse
import csv
import io
import json
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


# tag -> attribute that holds the link
LINK_ATTRS = {
    "a": "href",
    "link": "href",
    "img": "src",
    "script": "src",
    "iframe": "src",
    "video": "src",
    "audio": "src",
    "source": "src",
    "track": "src",
    "embed": "src",
    "object": "data",
}

# attributes we deliberately skip even if present
SKIP_PREFIXES = ("javascript:", "data:", "mailto:", "tel:")


class LinkHTMLParser(HTMLParser):
    """Collects every link-bearing tag in document order."""

    def __init__(self):
        super().__init__()
        self.links = []          # dicts: tag, attribute, url, text, line
        self._current_anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        pos = self.getpos()
        if tag == "a":
            self._current_anchor = {
                "tag": "a",
                "attribute": "href",
                "url": (attrs.get("href") or "").strip(),
                "text": "",
                "line": pos[0],
            }
            self.links.append(self._current_anchor)
        elif tag in LINK_ATTRS:
            attr = LINK_ATTRS[tag]
            self.links.append({
                "tag": tag,
                "attribute": attr,
                "url": (attrs.get(attr) or "").strip(),
                "text": "",
                "line": pos[0],
            })

    def handle_endtag(self, tag):
        if tag == "a":
            self._current_anchor = None

    def handle_data(self, data):
        if self._current_anchor is not None:
            self._current_anchor["text"] += data


def classify(url, base):
    """Return (resolved_url, kind, skipped)."""
    if not url:
        return "", "empty", True
    lower = url.lower()
    for prefix in SKIP_PREFIXES:
        if lower.startswith(prefix):
            return url, prefix.rstrip(":"), True
    if url.startswith("#"):
        return url, "fragment", True
    resolved = urljoin(base, url) if base else url
    if base:
        kind = "internal" if urlsplit(resolved).netloc == urlsplit(base).netloc else "external"
    else:
        kind = "relative" if urlsplit(resolved).netloc == "" else "absolute"
    return resolved, kind, False


def extract_links(html, base=""):
    """Parse saved HTML and return a list of link records in document order."""
    parser = LinkHTMLParser()
    parser.feed(html)
    records = []
    for entry in parser.links:
        resolved, kind, skipped = classify(entry["url"], base)
        text = " ".join(entry["text"].split())
        records.append({
            "tag": entry["tag"],
            "attribute": entry["attribute"],
            "url": entry["url"],
            "resolved_url": resolved,
            "text": text,
            "kind": kind,
            "skipped": skipped,
            "line": entry["line"],
        })
    return records


def to_text(records):
    lines = []
    for i, r in enumerate(records, 1):
        status = "SKIPPED (%s)" % r["kind"] if r["skipped"] else r["kind"].upper()
        text = ' "%s"' % r["text"] if r["text"] else ""
        shown = r["resolved_url"] or r["url"]
        lines.append("[%d] <%s %s> %s%s -> %s" %
                     (i, r["tag"], r["attribute"], status, text, shown))
    lines.append("")
    lines.append("Total: %d links (%d kept, %d skipped)" %
                 (len(records),
                  sum(1 for r in records if not r["skipped"]),
                  sum(1 for r in records if r["skipped"])))
    return "\n".join(lines)


def to_csv(records):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "no", "tag", "attribute", "url", "resolved_url",
        "text", "kind", "skipped", "line"])
    writer.writeheader()
    for i, r in enumerate(records, 1):
        writer.writerow({"no": i, **r})
    return buf.getvalue()


def to_json(records):
    return json.dumps({
        "total": len(records),
        "links": records,
    }, indent=2, ensure_ascii=False)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List every link found in a saved HTML page.")
    parser.add_argument("html_file", help="Path to the saved HTML page")
    parser.add_argument("--base", default="",
                        help="Base URL used to resolve relative links, "
                             "e.g. https://example.com")
    parser.add_argument("--format", choices=["text", "csv", "json"],
                        default="text", help="Output format (default: text)")
    parser.add_argument("--output", default="",
                        help="Write output to this file instead of stdout")
    args = parser.parse_args(argv)

    try:
        with open(args.html_file, "r", encoding="utf-8") as fh:
            html = fh.read()
    except FileNotFoundError:
        print("Error: file not found: %s" % args.html_file, file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        with open(args.html_file, "r", encoding="utf-8", errors="replace") as fh:
            html = fh.read()

    records = extract_links(html, args.base)

    if args.format == "csv":
        out = to_csv(records)
    elif args.format == "json":
        out = to_json(records)
    else:
        out = to_text(records)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("Wrote %d links to %s" % (len(records), args.output))
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
