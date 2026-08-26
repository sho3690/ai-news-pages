# 生成AI新聞 Web版

毎朝8:00に自動生成される「生成AI新聞」と、毎週土曜の「AI Weekly Report」を
読むための静的サイト(新聞風エディトリアルデザイン)。ここが唯一の配信先。

- 公開URL: https://sho3690.github.io/ai-news-pages/
- `build.py` が `../ai-news/editions/`(日刊JSON)と `../ai-x-weekly-report/reports/`
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
