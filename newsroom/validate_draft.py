#!/usr/bin/env python3
"""紙面の下書きを検証する(JSON形式・記事本数・ブリーフィングの長さ)。"""
import json
import re
import sys

path = sys.argv[1]
try:
    d = json.load(open(path, encoding="utf-8"))
except Exception as e:
    sys.exit(f"検証NG: JSONとして読めない: {e}")
embeds = d.get("embeds", [])
if len(embeds) < 2:
    sys.exit("検証NG: embedsが2つ未満")
desc = embeds[1].get("description", "")
n = len(re.findall(r"\*\*\[.+?\]\(https?://", desc))
if n < 1:
    sys.exit("検証NG: 記事が1本もない(出力の破損か生成失敗)")
briefing = str(d.get("briefing", "")).strip()
if len(briefing) < 80:
    sys.exit(f"検証NG: ブリーフィングが無いか短すぎる({len(briefing)}字)")
print(f"検証OK: 記事{n}本 / ブリーフィング{len(briefing)}字")
