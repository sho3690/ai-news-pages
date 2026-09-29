#!/bin/bash
# 今日の号を書く(Claude CodeがWebSearchで調査 → 検証 → editions/ に保存 → 掲載URLを記録)
# GitHub Actions(毎朝の本番)と Mac の run_daily.sh(予備)の両方から呼ばれる。
# 終了コード: 0=号あり(今回書いた or 既にあった) / 1=2回試行して失敗
# 2026-09-29: Macを閉じていると実行が止まるため、GitHub Actionsへ移すにあたり共通化
set -u
cd "$(dirname "$0")" || exit 1

TODAY=$(TZ=Asia/Tokyo date +%F)
EDITION="editions/edition-$TODAY.json"
DRAFT="$EDITION.draft"

if [ -f "$EDITION" ]; then
  echo "本日の号は既に存在するため生成をスキップ: $EDITION"
  exit 0
fi

rm -f "$DRAFT"
for attempt in 1 2; do
  echo "--- 紙面作成 試行${attempt}/2 ---"
  PROMPT=$(sed -e "s|{{TODAY}}|$TODAY|g" -e "s|{{EDITION_PATH}}|$DRAFT|g" daily-edition.txt)
  # ツールは Read/Write/WebSearch/WebFetch のみ許可(シェル実行は許可しない)
  if claude -p "$PROMPT" --model sonnet \
      --allowedTools "Read,Write,WebSearch,WebFetch" \
      --disallowedTools "Agent,Task,Bash" \
      && python3 validate_draft.py "$DRAFT"; then
    mv "$DRAFT" "$EDITION"
    echo "号面: $EDITION"
    python3 record_featured.py "$EDITION" || echo "掲載記録に失敗(明日の号で同じ記事が再掲される可能性)"
    exit 0
  fi
done
echo "号面生成失敗(2回試行)"
exit 1
