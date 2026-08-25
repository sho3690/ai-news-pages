"""build.py のテスト。編集長形式・フォールバック形式・パース不能の3系統を検証する。"""
import json
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


def _make_edition(dirp, day, desc):
    payload = {
        "username": "生成AI新聞",
        "embeds": [
            {"title": f"📰 生成AI新聞 — {day}号", "description": "リード文です。"},
            {"title": "✨ 今号の見どころ", "description": desc},
        ],
    }
    (dirp / f"edition-{day}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_build_site(tmp_path):
    eds = tmp_path / "editions"; eds.mkdir()
    reps = tmp_path / "reports"; reps.mkdir()
    docs = tmp_path / "docs"
    _make_edition(eds, "2026-08-24", EDITORIAL)
    _make_edition(eds, "2026-08-25", FALLBACK)
    (reps / "2026-08-22.md").write_text("# AI Weekly Report\n\n## 概要\n本文です。", encoding="utf-8")
    (reps / "2026-08-22.pdf").write_bytes(b"%PDF-1.4 dummy")

    build.build_site(eds, reps, docs)

    idx = (docs / "index.html").read_text(encoding="utf-8")
    assert "2026年8月25日" in idx       # 最新号がトップ(見出しは和暦表記で出る)
    assert "原文冒頭のテキスト" in idx
    daily = (docs / "daily" / "2026-08-24.html").read_text(encoding="utf-8")
    assert "見出しA" in daily and "引用文" in daily
    arch = (docs / "archive.html").read_text(encoding="utf-8")
    assert "2026-08-24" in arch and "2026-08-25" in arch
    wk = (docs / "weekly" / "2026-08-22.html").read_text(encoding="utf-8")
    assert "本文です。" in wk
    assert (docs / "weekly" / "pdf" / "2026-08-22.pdf").exists()
    assert "2026-08-22" in (docs / "weekly" / "index.html").read_text(encoding="utf-8")


def test_build_site_pdf_only_weekly(tmp_path):
    eds = tmp_path / "editions"; eds.mkdir()
    reps = tmp_path / "reports"; reps.mkdir()
    docs = tmp_path / "docs"
    _make_edition(eds, "2026-08-25", EDITORIAL)
    (reps / "2026-08-15.pdf").write_bytes(b"%PDF-1.4 dummy")

    build.build_site(eds, reps, docs)

    wk_index = (docs / "weekly" / "index.html").read_text(encoding="utf-8")
    assert "2026-08-15" in wk_index and "pdf/2026-08-15.pdf" in wk_index
    assert not (docs / "weekly" / "2026-08-15.html").exists()


def test_build_site_weekly_report_sanitizes_html(tmp_path):
    eds = tmp_path / "editions"; eds.mkdir()
    reps = tmp_path / "reports"; reps.mkdir()
    docs = tmp_path / "docs"
    _make_edition(eds, "2026-08-25", EDITORIAL)
    (reps / "2026-08-22.md").write_text(
        "# AI Weekly Report\n\n<script>alert(1)</script>\n\n## 概要\n本文です。",
        encoding="utf-8")

    build.build_site(eds, reps, docs)

    wk = (docs / "weekly" / "2026-08-22.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in wk
    assert "本文です。" in wk
