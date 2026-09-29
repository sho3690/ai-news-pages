# 生成AI新聞 Web版

毎朝8:00に自動生成される「生成AI新聞」と、毎週土曜の「AI Weekly Report」を
読むための静的サイト(新聞風エディトリアルデザイン)。ここが唯一の配信先。

- 公開URL: https://sho3690.github.io/ai-news-pages/
- 毎朝の号は GitHub Actions「今朝の号を出す」(`.github/workflows/daily.yml`)が 6:30 に作って公開する
  (Macを閉じていても動く。7:30/10:00/13:00 は予備)。Macの `ai-news/run_daily.sh`(7/12/18時)も予備として残し、
  号が既にあれば取り込んで公開するだけ
- 号の元データは `newsroom/`(`editions/` 日刊JSON・`featured_urls.txt` 掲載済みURL・`daily-edition.txt` 編集指示)。
  紙面を書く手順は `newsroom/write_edition.sh`(Actions と Mac の共通)
- Actions には Secrets `CLAUDE_CODE_OAUTH_TOKEN`(`claude setup-token` で発行、有効1年)が必要:
  `gh secret set CLAUDE_CODE_OAUTH_TOKEN -R sho3690/ai-news-pages < ~/.config/claude-headless/oauth_token`
- `build.py` が `newsroom/editions/`(日刊JSON)と `../ai-x-weekly-report/reports/`
  (週刊MD/PDF)から `docs/` を生成する
- `publish.sh` = ビルド + 差分があればコミット + プッシュ。
  毎朝の配信ジョブ(`ai-news/run_daily.sh`)と毎週の配信ジョブ
  (`ai-x-weekly-report/run_weekly.sh`)の最後から自動で呼ばれる

## 手動更新

```bash
bash publish.sh
```

## 開発

```bash
python3 -m venv venv && venv/bin/pip install markdown nh3 pytest
venv/bin/python -m pytest
```
