#!/usr/bin/env bash
# Skill pages are generated into a throwaway directory and are not committed.
set -euo pipefail
cd "$(dirname "$0")/.."
out=$(mktemp -d)
err=$(mktemp)
fake=$(mktemp -d)
fake_out=$(mktemp -d)
fake_err=$(mktemp)
trap 'rm -rf "$out" "$fake" "$fake_out"; rm -f "$err" "$fake_err"' EXIT

# Show the generator stderr even when it fails, before set -e ends the script.
rc=0
python3 scripts/build-skill-pages.py --out "$out" 2>"$err" || rc=$?
cat "$err" >&2
[ "$rc" -eq 0 ] || { echo "build-skill-pages.py exited $rc" >&2; exit "$rc"; }

discovered=$(python3 - <<'PY'
from pathlib import Path
import subprocess
root = Path('.').resolve()
bundles = subprocess.check_output(['bash', 'scripts/installable-bundles.sh', '--one-per-line'], text=True).split()
n = sum(p.is_file() for p in (root / 'skills').glob('*/SKILL.md'))
for bundle in bundles:
    base = root / 'systems' / bundle
    n += sum(p.is_file() for p in (base / 'skills').glob('*/SKILL.md'))
    n += sum(p.is_file() and p.parent.name != 'skills' for p in base.glob('*/SKILL.md'))
print(n)
PY
)
skipped=$(grep -c '^skip ' "$err" || true)
pages=$(find "$out/coco/skills" -mindepth 2 -maxdepth 2 -type f -name index.html ! -path '*/measured/*' | wc -l | tr -d ' ')
echo "discovered $discovered"; echo "skipped $skipped"; echo "$pages skill pages"
if [[ "$pages" -ne $((discovered - skipped)) ]]; then
  echo "page count $pages != discovered $discovered - skipped $skipped" >&2
  exit 1
fi

page="$out/coco/skills/officecli/index.html"
[[ -f "$page" ]]
grep -F -q '<link rel="canonical" href="https://cocoresearch.org/coco/skills/officecli/">' "$page"
grep -F -q 'https://cocoresearch.org/coco/skills/officecli/' "$out/sitemap.xml"
[[ -f "$out/coco/skills/skills.css" ]]
if grep -R -F --include='*.html' -q '<script' "$out/coco/skills"; then
  echo 'unescaped <script in a generated page' >&2
  exit 1
fi
if grep -R -F -q '{{' "$out"; then
  echo 'unfilled {{ in generated output' >&2
  exit 1
fi
while IFS= read -r -d '' html; do
  if ! grep -F -q 'href="/coco/skills/skills.css"' "$html"; then
    echo "missing stylesheet link: ${html#"$out"/}" >&2
    exit 1
  fi
done < <(find "$out" -name '*.html' -print0)

python3 - "$out" <<'PY'
import html, importlib.util, re, sys
from pathlib import Path
from urllib.parse import unquote
out = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('build_skill_pages', 'scripts/build-skill-pages.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
names, failed = mod.persona_names(), False
href_re = re.compile(r'href="([^"]*)"')
def complain(message):
    global failed
    failed = True
    print(message, file=sys.stderr)
_ABBREV = re.compile(r'(?i)(?:e\.g|i\.e|etc|vs|mr|mrs|dr|st|jr|sr|fig|cf|al)\.$')
_INITIALS = re.compile(r'(?:[A-Za-z]\.){2,}$')
_LEADIN = re.compile(r'(Use proactively when|Use this when|Trigger when|Use when)\b', re.I)
_LEADIN_AT = re.compile(
    r'(?:(?<=^)|(?<=[.!?;])\s+|(?<=,)\s+)'
    r'(Use proactively when|Use this when|Trigger when|Use when)\b', re.I)
_STOP = {'the', 'a', 'an', 'you', 'your', 'when', 'use', 'this', 'to', 'and', 'or', 'for', 'if', 'someone', 'user', 'users'}
_MACHINE = ('~/', '/Users/', '/home/', 'C:\\')
def one_line(text):
    return ' '.join(text.split())
def first_sentence(text):
    text, index = one_line(text), 0
    while text:
        idx = text.find('. ', index)
        if idx == -1:
            return text.strip()
        word, nxt = text[:idx + 1].split()[-1], text[idx + 2:idx + 3]
        if _ABBREV.match(word) or _INITIALS.match(word) or (len(word) >= 2 and word[-2].isdigit() and nxt.isdigit()):
            index = idx + 2
            continue
        if nxt.isupper() or nxt.isdigit() or nxt == '':
            return text[:idx + 1].strip()
        index = idx + 2
    return ''
def file_h1(text):
    lines, fence = text.splitlines(), False
    if lines and lines[0].strip() == '---':
        for index in range(1, len(lines)):
            if lines[index].strip() == '---':
                lines = lines[index + 1:]
                break
    for line in lines:
        if line.strip().startswith('```'):
            fence = not fence
            continue
        if not fence and line.startswith('# ') and not line.startswith('##'):
            return one_line(line[2:])
    return ''
def bad_ending(text):
    return text.rstrip().endswith((',', '...', '…'))
def machine_text(text):
    return (text or '').startswith('You have access') or any(token in (text or '') for token in _MACHINE)
for path in sorted(out.rglob('*.html')):
    raw = path.read_text(encoding='utf-8')
    hit = mod.matched_name(html.unescape(raw), names)
    if hit:
        complain(f'{path.relative_to(out)}: roster name {hit}')
    for href in href_re.findall(raw):
        href = html.unescape(href)
        if href.startswith('https://github.com/') and not href.startswith('https://github.com/coco-research/'):
            complain(f'{path.relative_to(out)}: {href}')
sources = {skill['slug']: skill for skill in mod.discover(mod.installable_bundles())}
pages = {}
for path in sorted((out / 'coco' / 'skills').glob('*/index.html')):
    slug, raw = path.parent.name, path.read_text(encoding='utf-8')
    if slug == 'measured':
        continue
    h1 = html.unescape(re.search(r'<h1>(.*?)</h1>', raw, re.S).group(1)).strip()
    lede = html.unescape(re.search(r'<p class="lede">(.*?)</p>', raw, re.S).group(1)).strip()
    meta = re.search(r'<meta name="description" content="([^"]*)"', raw)
    meta_text = html.unescape(meta.group(1)) if meta else ''
    if not meta or meta_text != lede:
        complain(f'{slug}: meta description is not the summary')
    if h1.startswith('/') or ' — ' in h1:
        complain(f'{slug}: title {h1!r}')
    for token in (*_MACHINE, 'You have access'):
        if token in lede or token in meta_text:
            complain(f'{slug}: summary contains {token!r}')
    source = sources[slug]
    expect_title = mod.title_source(file_h1(Path(source['rel']).read_text(encoding='utf-8')), slug)[1]
    if h1 != expect_title or h1 == slug:
        complain(f'{slug}: title {h1!r} != {expect_title!r}')
    if f'/ {slug}</p>' not in raw:
        complain(f'{slug}: breadcrumb dropped the slug')
    sentence = first_sentence(source['description'])
    if sentence and not _LEADIN.match(sentence) and not bad_ending(sentence) and not machine_text(sentence):
        expect = sentence if re.search(r'[.!?]"?$', sentence) or sentence.endswith(('."', ".'")) else sentence + '.'
        if lede != expect:
            complain(f'{slug}: summary is not the first sentence')
        for token in ('.json', 'e.g.', 'i.e.', 'v1.2'):
            if token in sentence and token not in lede:
                complain(f'{slug}: summary split inside {token}')
    if _LEADIN.match(lede) or bad_ending(lede) or re.search(r'(?:e\.g|i\.e|etc)\.$', lede):
        complain(f'{slug}: summary {lede[-40:]!r}')
    has_clause, has_section = bool(_LEADIN_AT.search(source['description'])), '<h2>Use it when</h2>' in raw
    if has_clause != has_section:
        complain(f'{slug}: use-it-when section present={has_section} clause={has_clause}')
    block = re.search(r'<ul class="when">(.*?)</ul>', raw, re.S)
    items = [html.unescape(re.sub(r'<[^>]+>', '', item)).strip()
             for item in re.findall(r'<li>(.*?)</li>', block.group(1) if block else '', re.S)]
    if len(items) > 6:
        complain(f'{slug}: {len(items)} when items')
    for item in items:
        if len(item) > 80 or _LEADIN.match(item) or bad_ending(item):
            complain(f'{slug}: when item {item!r}')
        if not item[:1].isupper() and not item[:1].isdigit():
            complain(f'{slug}: when item {item!r}')
        if item.count('(') != item.count(')') or item.count('"') % 2:
            complain(f'{slug}: when item broke a token {item!r}')
    if len(items) > 1:
        for item in items:
            word = re.match(r'["\']*([A-Za-z]+)', item)
            if word and word.group(1).lower() in _STOP:
                complain(f'{slug}: when item does not start with a verb {item!r}')
    pages[slug] = (h1, lede)
index = (out / 'coco' / 'skills' / 'index.html').read_text(encoding='utf-8')
index_h1 = html.unescape(re.search(r'<h1>(.*?)</h1>', index, re.S).group(1)).strip()
index_lede = html.unescape(re.search(r'<p class="lede">(.*?)</p>', index, re.S).group(1)).strip()
index_meta = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', index).group(1))
if index_h1.startswith('/') or ' — ' in index_h1:
    complain(f'index: title {index_h1!r}')
for token in (*_MACHINE, 'You have access'):
    if token in index_lede or token in index_meta:
        complain(f'index: summary contains {token!r}')
rows = {unquote(href.rstrip('/').rsplit('/', 1)[-1]): (html.unescape(title), html.unescape(summary or ''))
        for href, title, summary in re.findall(r'<li><a href="([^"]+)">([^<]*)</a>(?: — (.*?))?</li>', index, re.S)}
if set(rows) != set(pages):
    complain('index rows do not match skill pages')
for slug, pair in pages.items():
    row = rows.get(slug)
    if row != pair:
        complain(f'{slug}: index row {row!r} != page {pair!r}')
    if row and _LEADIN.match(row[1]):
        complain(f'{slug}: index summary starts with a use-when lead-in')
if failed:
    sys.exit(1)
PY

measured="$out/coco/skills/measured/index.html"
[[ -f "$measured" ]]
grep -F -q '<link rel="canonical" href="https://cocoresearch.org/coco/skills/measured/">' "$measured"
grep -F -q 'https://cocoresearch.org/coco/skills/measured/' "$out/sitemap.xml"
grep -F -q 'Measured: 0.88 on 24 held-out tasks · Oct 21' "$out/coco/skills/c4-architecture/index.html"
if grep -F -q 'noindex' "$measured"; then
  echo 'measured page carries noindex' >&2
  exit 1
fi
if grep -F -q 'Layout sample' "$measured" || grep -F -q 'SAMPLE' "$measured"; then
  echo 'measured page carries sample text' >&2
  exit 1
fi

# A committed record the generator rejects is a repo bug: name it here, before the row count.
if grep -F 'bad record' "$err" >&2; then
  echo 'a committed eval record is malformed (see above)' >&2
  exit 1
fi

expected=$(python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('.').resolve()
shas = {}
for pattern in ('skills/*/SKILL.md', 'systems/*/skills/*/SKILL.md', 'systems/*/*/SKILL.md'):
    for path in root.glob(pattern):
        if path.is_file():
            shas[path.parent.name] = hashlib.sha256(path.read_bytes()).hexdigest()
def rate(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1
def count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
def load(path):
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None
evals, rows = root / 'evals' / 'skills', 0
for path in sorted(evals.iterdir()):
    baseline_path = path / 'runs' / 'baseline-heldout.json'
    if not path.is_dir() or path.name.startswith('_') or not baseline_path.is_file(): continue
    sha = shas.get(path.name)
    if not sha: continue
    shown = []
    for record_path in sorted((path / 'runs').glob('*-heldout.json')):
        stem, record = record_path.name[:-len('-heldout.json')], load(record_path)
        if not record or record.get('split') != 'heldout' or record.get('skill_sha256') != sha: continue
        if stem != 'baseline':
            outcome = (load(evals / '_rounds' / path.name / (stem + '.json')) or {}).get('outcome')
            if outcome != 'kept': continue
        shown.append(record)
    if not shown: continue
    chosen, baseline = max(shown, key=lambda r: str(r.get('date') or '')), load(baseline_path)
    if baseline and rate(baseline.get('mean')) and count(baseline.get('n')) and rate(chosen.get('mean')) and count(chosen.get('n')):
        rows += 1
runs = root / 'evals' / 'routing' / 'runs'
for record_path in (sorted(runs.glob('*.json')) if runs.is_dir() else []):
    data = load(record_path) or {}
    run = data.get('run') if isinstance(data.get('run'), dict) else {}
    vs = run.get('vs_keyword') if isinstance(run.get('vs_keyword'), dict) else {}
    if rate(data.get('top1_accuracy')) and rate(vs.get('baseline_top1')) and count(run.get('n_labelled')):
        rows += 1
        break
print(rows)
PY
)
actual=$(grep -c 'data-label="Skill"' "$measured" || true)
if [[ "$actual" -ne "$expected" ]]; then
  echo "measured rows $actual != expected $expected" >&2
  exit 1
fi

mkdir -p "$fake/skills/zz-fake/runs" "$fake/skills/c4-architecture/runs"
zeros=$(python3 -c 'print("0" * 64)')
sha=$(python3 -c 'import hashlib; print(hashlib.sha256(open("skills/c4-architecture/SKILL.md", "rb").read()).hexdigest())')
cat > "$fake/skills/zz-fake/runs/baseline-heldout.json" <<JSON
{"date": "2026-10-21", "split": "heldout", "executor": "ollama", "model": "qwen3:4b-instruct-2507-q4_K_M", "n": 24, "mean": 0.5, "skill_sha256": "$zeros"}
JSON
cat > "$fake/skills/c4-architecture/runs/baseline-heldout.json" <<JSON
{"date": "2026-10-21", "split": "heldout", "executor": "ollama", "model": "qwen3:4b-instruct-2507-q4_K_M", "n": 24, "mean": 2, "skill_sha256": "$sha"}
JSON
python3 scripts/build-skill-pages.py --out "$fake_out" --evals "$fake" 2>"$fake_err"
grep -F -q 'measured skip zz-fake: no run for the current SKILL.md' "$fake_err"
grep -F -q 'measured skip c4-architecture: bad record ' "$fake_err"
grep -F -q '<p class="empty">No measured skills yet.</p>' "$fake_out/coco/skills/measured/index.html"
if grep -F -q 'data-label="Skill"' "$fake_out/coco/skills/measured/index.html"; then
  echo 'a fake record became a measured row' >&2
  exit 1
fi

tracked=$(git ls-files coco/skills sitemap.xml)
if [[ -n "$tracked" ]]; then
  echo 'generated pages are tracked:' >&2
  printf '%s\n' "$tracked" >&2
  exit 1
fi
