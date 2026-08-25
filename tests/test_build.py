"""build.py のテスト。編集長形式・フォールバック形式・パース不能の3系統を検証する。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build

EDITORIAL = (
    "**[見出しA](https://x.com/i/status/1)**\n要約文A。\n> 引用文\n　8,483いいね・77.9万表示（8/4）\n\n"
    "**[見出しB](https://www.reddit.com/r/test/1)**\n要約文B。\n　624pt・179コメント（8/4）"
)
FALLBACK = (
    "**[原文冒頭のテキスト](https://x.com/i/status/2)**\n　17,368いいね（8/22）\n\n"
    "**[Two](https://x.com/i/status/3)**\n　100いいね（8/23）"
)


def test_parse_editorial():
    arts = build.parse_articles(EDITORIAL)
    assert len(arts) == 2
    assert arts[0]["title"] == "見出しA"
    assert arts[0]["url"] == "https://x.com/i/status/1"
    assert arts[0]["summary"] == "要約文A。"
    assert arts[0]["quote"] == "引用文"
    assert "いいね" in arts[0]["meta"]
    assert arts[1]["quote"] == ""


def test_parse_fallback():
    arts = build.parse_articles(FALLBACK)
    assert len(arts) == 2
    assert arts[0]["summary"] == ""
    assert "いいね" in arts[0]["meta"]


def test_parse_junk():
    assert build.parse_articles("ただのテキスト。リンクなし。") == []
