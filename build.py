#!/usr/bin/env python3
"""生成AI新聞 Web版ビルダー。

../ai-news/editions/*.json(日刊)と ../ai-x-weekly-report/reports/(週刊)から
docs/ 以下に静的サイトを生成する。秘密情報は一切扱わない。
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
EDITIONS_DIR = BASE.parent / "ai-news" / "editions"
REPORTS_DIR = BASE.parent / "ai-x-weekly-report" / "reports"
DOCS_DIR = BASE / "docs"

WEEKDAYS = "月火水木金土日"

RECORD_RE = re.compile(r"\*\*\[(?P<title>.+?)\]\((?P<url>https?://[^)\s]+)\)\*\*")


def parse_articles(description):
    """embedのdescription(Markdown)を記事レコードのリストにする。

    編集長形式(見出し+要約+引用+統計)とフォールバック形式(見出し+統計)の
    両方を受け付ける。どちらでもなければ空リスト(呼び出し側が生表示にする)。
    """
    matches = list(RECORD_RE.finditer(description))
    articles = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(description)
        body = description[m.end():end]
        summary, quote, meta = [], [], []
        for line in body.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith(">"):
                quote.append(s.lstrip("> ").strip())
            elif line.startswith("　"):
                meta.append(s.strip("　 "))
            else:
                summary.append(s)
        articles.append({
            "title": m.group("title").strip(),
            "url": m.group("url"),
            "summary": " ".join(summary),
            "quote": " ".join(quote),
            "meta": " ／ ".join(meta),
        })
    return articles
