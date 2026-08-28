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
        # 収集元のデータにHTMLエンティティ(&gt;等)が混ざることがあるので、
        # ここで一度実体に戻す(表示時にエスケープするのは描画側の責務)
        articles.append({
            "title": html.unescape(m.group("title").strip()),
            "url": m.group("url"),
            "summary": html.unescape(" ".join(summary)),
            "quote": html.unescape(" ".join(quote)),
            "meta": html.unescape(" ／ ".join(meta)),
        })
    return articles


try:
    import markdown as _markdown
except ImportError:            # markdown が無くても週刊は <pre> で読める
    _markdown = None

try:
    import nh3 as _nh3
except ImportError:
    _nh3 = None

SITE_TITLE = "生成AI新聞"
FOOTER_TEXT = "生成AI新聞 — XとRedditで話題の生成AIトピックを毎朝8:00に更新"
FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Crect width='64' height='64' rx='12' fill='%23023e8a'/%3E"
           "%3Ctext x='32' y='47' font-size='40' text-anchor='middle'"
           " fill='%23f9f7f2' font-family='serif'%3E%E6%96%B0%3C/text%3E%3C/svg%3E")


def jp_date(day):
    """'2026-08-24' -> '2026年8月24日（月）'"""
    d = date.fromisoformat(day)
    return f"{d.year}年{d.month}月{d.day}日（{WEEKDAYS[d.weekday()]}）"


def jp_md(day):
    """'2026-08-24' -> '8月24日'(号送りナビ用の短い表記)"""
    d = date.fromisoformat(day)
    return f"{d.month}月{d.day}日"


def md_inline(text):
    """最終フォールバック用: エスケープ後にリンクと太字だけHTML化する。"""
    out = html.escape(text)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                 r'<a href="\2" target="_blank" rel="noopener">\1</a>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return out.replace("\n", "<br>\n")


def page_shell(title, body, root, active):
    """全ページ共通の外枠。root はサイトルートへの相対プレフィックス(''か'../')。

    ナビは置かない(ユーザー指示: 題字だけ)。activeは互換のため受け取るが未使用。
    """
    del active
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f9f7f2">
<title>{html.escape(title)}</title>
<link rel="icon" href="{FAVICON}">
<link rel="apple-touch-icon" sizes="180x180" href="{root}assets/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="{SITE_TITLE}">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<header class="masthead">
  <div class="masthead-inner">
    <a class="brand" href="{root}index.html">{SITE_TITLE}</a>
  </div>
</header>
<main class="wrap">
{body}
<footer class="site-footer">{FOOTER_TEXT}<br>
<a class="footer-link" href="{root}archive.html">過去号一覧</a></footer>
</main>
</body>
</html>
"""


def source_label(url):
    """X/Redditだけチップ表示する(それ以外のWeb記事はメタ行の出典名に任せる)。"""
    if "reddit.com" in url:
        return "Reddit"
    if "x.com" in url or "twitter.com" in url:
        return "X"
    return ""


def render_article(a, no):
    """記事1本を新聞の段組風(番号+本文)にレンダリングする。"""
    parts = [f'<h2 class="story-title"><a href="{html.escape(a["url"], quote=True)}"'
             f' target="_blank" rel="noopener">{html.escape(a["title"])}</a></h2>']
    if a["summary"]:
        parts.append(f'<p class="story-summary">{html.escape(a["summary"])}</p>')
    if a["quote"]:
        parts.append(f'<blockquote class="story-quote">{html.escape(a["quote"])}</blockquote>')
    label = source_label(a["url"])
    meta = f'<span class="story-source">{label}</span>' if label else ""
    if a["meta"]:
        meta += html.escape(a["meta"])
    if not meta:
        meta = "&nbsp;"
    parts.append(f'<p class="story-meta">{meta}</p>')
    return (f'<article class="story"><span class="story-no">{no:02d}</span>'
            f'<div class="story-body">' + "".join(parts) + "</div></article>")


def load_editions(editions_dir):
    """editions/*.json を読み、新しい順の号リストを返す。"""
    editions = []
    for path in sorted(editions_dir.glob("edition-????-??-??.json")):
        day = path.stem.replace("edition-", "")
        try:
            date.fromisoformat(day)
        except ValueError:
            continue
        try:
            embeds = json.loads(path.read_text(encoding="utf-8")).get("embeds", [])
        except (json.JSONDecodeError, OSError):
            continue
        descriptions = [e.get("description", "") for e in embeds[1:]]
        articles = []
        for desc in descriptions:
            articles.extend(parse_articles(desc))
        editions.append({
            "day": day,
            "articles": articles,
            "raw": "\n\n".join(d for d in descriptions if d),
        })
    editions.sort(key=lambda e: e["day"], reverse=True)
    return editions


def edition_head(title_html, aside):
    return (f'<div class="edition-head">{title_html}'
            f'<span class="edition-count">{aside}</span></div>')


def render_edition_body(ed, prev_ed, next_ed, root):
    n = len(ed["articles"])
    aside = f"全{n}本" if n else "紙面"
    body = [edition_head(f'<h1 class="edition-date">{jp_date(ed["day"])}号</h1>', aside)]
    if ed["articles"]:
        body += [render_article(a, i + 1) for i, a in enumerate(ed["articles"])]
    elif ed["raw"]:
        body.append(f'<div class="story-raw">{md_inline(ed["raw"])}</div>')
    else:
        body.append('<p class="empty-note">この号のデータを読み込めませんでした。</p>')
    older = (f'<a href="{root}daily/{prev_ed["day"]}.html">← 前の号（{jp_md(prev_ed["day"])}）</a>'
             if prev_ed else "<span></span>")
    newer = (f'<a href="{root}daily/{next_ed["day"]}.html">次の号（{jp_md(next_ed["day"])}） →</a>'
             if next_ed else "<span></span>")
    body.append(f'<nav class="edition-nav">{older}{newer}</nav>')
    return "\n".join(body)


def load_reports(reports_dir):
    """reports/ の YYYY-MM-DD.md / .pdf を週ごとにまとめ、新しい順で返す。"""
    reports = {}
    if reports_dir.is_dir():
        for path in reports_dir.iterdir():
            m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.(md|pdf)", path.name)
            if m:
                reports.setdefault(m.group(1), {})[m.group(2)] = path
    return [{"day": k, **v} for k, v in sorted(reports.items(), reverse=True)]


EXEC_SUMMARY_RE = re.compile(r"##\s*エグゼクティブサマリー\s*\n(.*?)(?=\n##\s)", re.S)


def render_weekly_section(reports, root):
    """トップページ下部の週刊レポート常設欄。要点を先に見せ、全文はその場で開ける。"""
    parts = ['<section id="weekly" class="weekly-section">',
             '<div class="edition-head"><h2 class="edition-date">週刊AIレポート</h2>'
             '<span class="edition-count">毎週土曜更新</span></div>']
    latest = next((r for r in reports if "md" in r), None)
    if latest is None:
        parts.append('<p class="empty-note">週刊レポートは毎週土曜のお昼にここへ届きます。</p>')
    else:
        day = latest["day"]
        md_text = latest["md"].read_text(encoding="utf-8")
        parts.append(f'<p class="weekly-date">{jp_date(day)}号</p>')
        m = EXEC_SUMMARY_RE.search(md_text)
        if m:
            parts.append(f'<div class="prose weekly-summary">{render_report_html(m.group(1).strip())}</div>')
        parts.append('<details class="weekly-full"><summary>全文をここで読む</summary>'
                     f'<div class="prose">{render_report_html(md_text)}</div></details>')
        extras = []
        if "pdf" in latest:
            extras.append(f'<a href="{root}weekly/pdf/{day}.pdf">PDF版</a>')
        older = [r for r in reports if r is not latest and "md" in r][:8]
        if older:
            extras.append("過去分: " + "・".join(
                f'<a href="{root}weekly/{r["day"]}.html">{jp_md(r["day"])}号</a>' for r in older))
        if extras:
            parts.append(f'<p class="weekly-older">{"　".join(extras)}</p>')
    parts.append("</section>")
    return "\n".join(parts)


def render_report_html(md_text):
    if _markdown is not None:
        converted = _markdown.markdown(md_text, extensions=["extra"])
        if _nh3 is not None:
            return _nh3.clean(converted)
        # nh3 が無い場合はサニタイズできないので生HTMLを返さず安全側にフォールバック
        return f"<pre style='white-space:pre-wrap'>{html.escape(md_text)}</pre>"
    return f"<pre style='white-space:pre-wrap'>{html.escape(md_text)}</pre>"


def build_site(editions_dir, reports_dir, docs_dir):
    (docs_dir / "daily").mkdir(parents=True, exist_ok=True)
    (docs_dir / "weekly" / "pdf").mkdir(parents=True, exist_ok=True)

    editions = load_editions(editions_dir)
    reports = load_reports(reports_dir)

    # 各号ページ(daily/)。editionsは新しい順: i+1が前の号、i-1が次の号
    for i, ed in enumerate(editions):
        prev_ed = editions[i + 1] if i + 1 < len(editions) else None
        next_ed = editions[i - 1] if i > 0 else None
        html_text = page_shell(f'{jp_date(ed["day"])}号 | {SITE_TITLE}',
                               render_edition_body(ed, prev_ed, next_ed, "../"),
                               "../", "")
        (docs_dir / "daily" / f'{ed["day"]}.html').write_text(html_text, encoding="utf-8")

    # トップ = 最新号 + 週刊レポート常設欄
    if editions:
        latest, rest = editions[0], editions[1:]
        prev_ed = rest[0] if rest else None
        body = render_edition_body(latest, prev_ed, None, "")
    else:
        body = '<p class="empty-note">まだ号がありません。</p>'
    body += "\n" + render_weekly_section(reports, "")
    (docs_dir / "index.html").write_text(
        page_shell(SITE_TITLE, body, "", "latest"), encoding="utf-8")

    # 過去号一覧(月ごとに罫線で区切る)
    items = [edition_head('<h1 class="edition-date">過去号</h1>', f"全{len(editions)}号")]
    cur_month = None
    for ed in editions:
        d = date.fromisoformat(ed["day"])
        mkey = f"{d.year}年{d.month}月"
        if mkey != cur_month:
            items.append(f'<h2 class="month-head">{mkey}</h2>')
            cur_month = mkey
        n = len(ed["articles"])
        count = f"{n}本" if n else "紙面"
        items.append(f'<a class="issue-row" href="daily/{ed["day"]}.html">'
                     f'<span>{d.day}日（{WEEKDAYS[d.weekday()]}）号</span>'
                     f'<span class="count">{count}</span></a>')
    (docs_dir / "archive.html").write_text(
        page_shell(f"過去号 | {SITE_TITLE}", "\n".join(items), "", "archive"),
        encoding="utf-8")

    # 週刊レポート(個別ページと一覧は過去分の置き場として残す)
    rows = [edition_head('<h1 class="edition-date">週刊レポート</h1>', f"全{len(reports)}号")]
    for rep in reports:
        day = rep["day"]
        links = []
        if "md" in rep:
            md_text = rep["md"].read_text(encoding="utf-8")
            report_body = f'<div class="prose">{render_report_html(md_text)}</div>'
            if "pdf" in rep:
                report_body = (f'<p class="pdf-link"><a href="pdf/{day}.pdf">'
                               f'PDF版をダウンロード</a></p>') + report_body
            (docs_dir / "weekly" / f"{day}.html").write_text(
                page_shell(f"AI Weekly Report {day} | {SITE_TITLE}",
                           report_body, "../", "weekly"),
                encoding="utf-8")
            links.append(f'<a href="{day}.html">本文を読む</a>')
        if "pdf" in rep:
            shutil.copyfile(rep["pdf"], docs_dir / "weekly" / "pdf" / f"{day}.pdf")
            links.append(f'<a href="pdf/{day}.pdf">PDF</a>')
        rows.append(f'<article class="report-item">'
                    f'<h2 class="story-title">AI Weekly Report — {jp_date(day)}</h2>'
                    f'<p class="story-summary">X(Twitter)で話題になった1週間のAIトピックまとめ</p>'
                    f'<p class="report-links">{"・".join(links)}</p></article>')
    if not reports:
        rows.append('<p class="empty-note">週刊レポートはまだありません。'
                    '毎週土曜のお昼に追加されます。</p>')
    (docs_dir / "weekly" / "index.html").write_text(
        page_shell(f"週刊レポート | {SITE_TITLE}", "\n".join(rows), "../", "weekly"),
        encoding="utf-8")


def main():
    build_site(EDITIONS_DIR, REPORTS_DIR, DOCS_DIR)
    print("ビルド完了:", DOCS_DIR)


if __name__ == "__main__":
    main()
