#!/bin/bash
# サイトを構築し、差分があればGitHub Pagesへ反映する
# 使い方: publish.sh [--no-push]
set -u
cd "$(dirname "$0")"
PY="venv/bin/python"
[ -x "$PY" ] || PY="python3"
"$PY" build.py || exit 1
if [ -z "$(git status --porcelain -- docs)" ]; then
  echo "変更なし(プッシュ省略)"
  exit 0
fi
git add docs
git commit -q -m "サイト更新: $(date '+%Y-%m-%d %H:%M')"
if [ "${1:-}" = "--no-push" ]; then
  echo "コミットのみ(--no-push)"
  exit 0
fi
git push -q origin main
echo "公開完了"
