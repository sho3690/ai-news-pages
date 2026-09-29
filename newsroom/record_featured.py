#!/usr/bin/env python3
"""投稿済みの号面から記事URLを抜き出して featured_urls.txt に追記する(重複掲載防止)。"""
import json
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "featured_urls.txt")


def canon(url):
    return urllib.parse.unquote(url or "").strip()


edition = json.load(open(sys.argv[1]))
urls = set()
for e in edition.get("embeds", []):
    urls.update(canon(u) for u in re.findall(r"\]\((https?://[^)]+)\)", e.get("description", "")))

known = set()
if os.path.exists(PATH):
    known = {canon(line) for line in open(PATH) if line.strip()}

new = sorted(urls - known)
if new:
    with open(PATH, "a") as f:
        for u in new:
            f.write(u + "\n")
print(f"掲載記録: 新規{len(new)}件")
