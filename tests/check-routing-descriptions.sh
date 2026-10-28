#!/usr/bin/env bash
# Description-split routing checks that do not need the embedding server.
# The auto-mode record command is pointed at a closed port and must not write.
#
# COCO_EMBED_URL overrides the router default (http://127.0.0.1:1234/v1/embeddings).
#
# Run from anywhere: bash tests/check-routing-descriptions.sh

set -euo pipefail
cd "$(dirname "$0")/.."

python3 evals/routing/check_items.py

leak=$(mktemp)
log=$(mktemp)
report=$(mktemp)
noreport="${TMPDIR:-/tmp}/routing-desc-no-write-$$.json"
rm -f "$noreport"
trap 'rm -f "$leak" "$log" "$report" "$noreport"' EXIT

leak_id=$(python3 - "$leak" <<'PY'
import json, pathlib, sys
src = pathlib.Path("evals/routing/items-descriptions.jsonl")
dst = pathlib.Path(sys.argv[1])
picked = None
rows = []
for line in src.read_text().splitlines():
    if not line.strip():
        continue
    item = json.loads(line)
    if picked is None and item.get("label") == "ai" and item.get("kind") == "positive":
        item["prompt"] = item["prompt"] + " about ai"
        picked = item["id"]
    rows.append(json.dumps(item, ensure_ascii=True))
if not picked:
    raise SystemExit("no ai positive to plant")
dst.write_text("\n".join(rows) + "\n")
print(picked)
PY
)

set +e
python3 evals/routing/check_items.py "$leak" >"$log" 2>&1
code=$?
set -e
if [ "$code" -eq 0 ]; then
  echo "FAIL: planted leak in $leak_id was accepted"
  exit 1
fi
if ! grep -q "$leak_id" "$log"; then
  echo "FAIL: checker did not name $leak_id"
  cat "$log"
  exit 1
fi

python3 evals/routing/score.py --self-test

if ! python3 evals/routing/score.py \
    --items evals/routing/items-descriptions.jsonl \
    --split-name descriptions \
    --mode keyword \
    --json "$report" >"$log" 2>&1; then
  echo "FAIL: keyword score on the descriptions split"
  cat "$log"
  exit 1
fi
python3 - "$report" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
if report.get("split") != "descriptions":
    raise SystemExit(f"split is {report.get('split')!r}, expected 'descriptions'")
top1 = report.get("top1_accuracy")
if isinstance(top1, bool) or not isinstance(top1, (int, float)) or not 0.0 <= float(top1) <= 1.0:
    raise SystemExit(f"top1_accuracy out of range: {top1!r}")
print(f"descriptions keyword top-1: {top1}")
PY

set +e
COCO_EMBED_URL="http://127.0.0.1:9/v1/embeddings" \
  python3 evals/routing/score.py \
    --items evals/routing/items-descriptions.jsonl \
    --split-name descriptions \
    --mode auto \
    --vs-keyword \
    --json "$noreport" >"$log" 2>&1
code=$?
set -e
if [ "$code" -eq 0 ]; then
  echo "FAIL: auto record command exited 0 against an unreachable embedding server"
  exit 1
fi
if [ -e "$noreport" ]; then
  echo "FAIL: auto record command wrote $noreport"
  exit 1
fi
if ! grep -qiE "not reachable|refusing" "$log"; then
  echo "FAIL: auto record command did not say the embedding server was unreachable"
  cat "$log"
  exit 1
fi

echo "check-routing-descriptions: ok"
