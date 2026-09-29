#!/bin/bash
# サイトを構築し、差分があればGitHub Pagesへ反映する
# 使い方: publish.sh [--no-push]
set -u
cd "$(dirname "$0")" || exit 1

# 多重実行防止(日刊と週刊が同じクローンを共有するため)
LOCKDIR=".publish.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "別のpublishが実行中のためスキップ"
  exit 1
fi
trap 'rmdir "$LOCKDIR"' EXIT

PY="venv/bin/python"
[ -x "$PY" ] || PY="python3"
"$PY" build.py || exit 1
if [ -z "$(git status --porcelain -- docs newsroom/editions newsroom/featured_urls.txt)" ]; then
  echo "変更なし(プッシュ省略)"
  exit 0
fi
# 号の元データ(newsroom/)も一緒に載せる。GitHub Actions 側の更新と行き違わないよう先に取り込む
git add docs newsroom/editions newsroom/featured_urls.txt
git commit -q -m "サイト更新: $(date '+%Y-%m-%d %H:%M')" || exit 1
if [ "${1:-}" = "--no-push" ]; then
  echo "コミットのみ(--no-push)"
  exit 0
fi
git pull -q --rebase origin main || exit 1
git push -q origin main || exit 1
echo "公開完了"
