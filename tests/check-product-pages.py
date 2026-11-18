#!/usr/bin/env python3
"""Assert all static 3D product pages match data/products.json and site invariants.

Run from repo root: python3 tests/check-product-pages.py
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

fail = 0


def fail_(msg):
    global fail
    print('  FAIL: %s' % msg)
    fail = 1


def pass_(msg):
    print('  PASS: %s' % msg)


def check(cond, ok_msg, bad_msg):
    if cond:
        pass_(ok_msg)
    else:
        fail_(bad_msg)


data = json.loads(Path('data/products.json').read_text())
pub_specs = json.loads(Path('data/product-pages-public.json').read_text())
lab_specs = json.loads(Path('data/product-pages-lab.json').read_text())
index_text = Path('index.html').read_text()

css_path = Path('assets/css/product.css')
scene_path = Path('assets/js/product-scene.js')
motifs_a_path = Path('assets/js/product-motifs-a.js')
motifs_b_path = Path('assets/js/product-motifs.js')
for p in (css_path, scene_path, motifs_a_path, motifs_b_path):
    check(p.is_file(), f'{p} exists', f'{p} is missing')

for script in ('scripts/render-product-pages.py', 'scripts/render-site-products.py'):
    proc = subprocess.run([sys.executable, script, '--check'], capture_output=True, text=True)
    if proc.returncode == 0:
        pass_(f'{script} --check passed')
    else:
        fail_(f'{script} --check failed (exit {proc.returncode})')
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)

imp_re = re.compile(r'<script type="importmap">\s*(\{.*?\})\s*</script>', re.S)
idx_imp = json.loads(imp_re.search(index_text).group(1))['imports']['three']
check('@0.170.0/' in idx_imp, f'index.html pins three.js ({idx_imp})', 'index.html missing pinned three.js')

css_text = css_path.read_text()
scene_text = scene_path.read_text()
motifs_text = motifs_a_path.read_text() + '\n' + motifs_b_path.read_text()
check("from 'three'" in scene_text, 'shared scene imports pinned three module', 'scene missing three import')
check('prefers-reduced-motion: reduce' in css_text, 'product.css has prefers-reduced-motion rule', 'product.css missing reduced-motion')
check('prefers-reduced-motion: reduce' in scene_text, 'product-scene.js guards WebGL on prefers-reduced-motion', 'scene missing reduced-motion guard')

for token in ('#03050b', '#2f4bff', '#8fa2ff', '#eceae4', '#f3f2ee', '#1234ff', '#0b0b0b', 'Archivo', 'Martian Mono'):
    check(token.lower() in css_text.lower(), f'product.css includes Signal token {token}', f'product.css missing Signal token {token}')

runtime_net = re.compile(r'\b(fetch\s*\(|XMLHttpRequest\b|navigator\.sendBeacon\b)')
local_path_leak = re.compile(r'/(?:home|Users|private|var/folders)/[A-Za-z0-9._-]+')
roadmap_promise = re.compile(r'\b(coming soon|on the roadmap|roadmap promise|will ship in|launching soon)\b', re.I)

public_pages = []
seen_motifs = set()
for stage in ('shipped', 'source', 'lab'):
    for row in data[stage]:
        pid = row['id']
        expected_page = 'coco/' if pid == 'coco-si' else f'{pid}/'
        check(row.get('page') == expected_page, f'{pid}: page path is {expected_page}', f'{pid}: bad page {row.get("page")!r}')
        check(f'href="{expected_page}"' in index_text, f'index.html links to {expected_page}', f'index.html missing link to {expected_page}')

        page_path = Path(expected_page) / 'index.html'
        public_pages.append(page_path)
        check(page_path.is_file(), f'{page_path} exists', f'{page_path} missing')
        txt = page_path.read_text() if page_path.is_file() else ''

        check(f'data-product="{pid}"' in txt, f'{page_path}: uses motif {pid}', f'{page_path}: missing data-product={pid}')
        check(re.search(rf"(?:['\"]){re.escape(pid)}(?:['\"])\s*\(|(?<!['\"\w]){re.escape(pid)}\s*\(", motifs_text) is not None,
              f'motif generator defines {pid}', f'motif generator missing {pid}')
        seen_motifs.add(pid)
        check('../assets/js/product-scene.js' in txt, f'{page_path}: shares product-scene.js', f'{page_path}: missing shared scene')
        m = imp_re.search(txt)
        p_imp = json.loads(m.group(1))['imports']['three'] if m else ''
        check(p_imp == idx_imp, f'{page_path}: pinned three.js matches index.html', f'{page_path}: importmap mismatch')
        check('prefers-reduced-motion: reduce' in txt, f'{page_path}: reduced-motion head check', f'{page_path}: missing reduced-motion')
        check(f'>{row["name"]}</h1>' in txt, f'{page_path}: h1 matches {row["name"]}', f'{page_path}: h1 mismatch')
        check('Heliopause by Coco Research' in txt and '>Heliopause<' not in txt,
              f'{page_path}: names "Heliopause by Coco Research"', f'{page_path}: bare Heliopause found')
        check(not roadmap_promise.search(txt), f'{page_path}: zero roadmap promises', f'{page_path}: contains roadmap promise wording')

check(len(seen_motifs) == 11, 'all 11 public products have distinct motif ids', f'expected 11 motifs, got {len(seen_motifs)}')
check(not Path('code/index.html').exists() and not Path('site-refs/facts/code.json').exists()
      and 'Coco Code' not in index_text and '"code"' not in Path('data/products.json').read_text(),
      'dropped Coco Code is removed from homepage, catalog and product pages',
      'dropped Coco Code still referenced in site files')
check(not Path('connect/index.html').exists() and not Path('site-refs/facts/connect.json').exists()
      and not Path('assets/site/art/connect.svg').exists() and not Path('assets/site/prod-connect.png').exists()
      and 'Coco Connect' not in index_text and 'coco-connect' not in index_text
      and '"connect"' not in Path('data/products.json').read_text()
      and '"connect"' not in Path('data/product-pages-public.json').read_text(),
      'Coco Connect is completely removed from homepage, catalog, assets and product pages',
      'Coco Connect still referenced in site files')
check('Heliopause by Coco Research' in index_text and '>Heliopause<' not in index_text,
      'index.html names "Heliopause by Coco Research"', 'index.html has bare Heliopause')

# Aloo Mannu: built locally with its own 3D motif, never linked or listed in public pages or data/products.json.
aloo_path = Path('aloomannu/index.html')
check(aloo_path.is_file(), 'aloomannu/index.html exists locally', 'aloomannu/index.html missing')
aloo_txt = aloo_path.read_text() if aloo_path.is_file() else ''
check('data-product="aloomannu"' in aloo_txt and 'noindex, nofollow' in aloo_txt,
      'aloomannu/index.html uses aloomannu motif and noindex, nofollow', 'aloomannu/index.html missing motif or noindex')
check('aloomannu(' in motifs_text, 'motif generator defines aloomannu', 'motif generator missing aloomannu')

aloo_ref = re.compile(r'aloomannu|aloo\s*mannu', re.I)
connect_ref = re.compile(r'coco\s+connect|coco-connect|(?:\.\./|^|")connect/', re.I)
for p in [Path('index.html'), Path('data/products.json'), Path('coco/guardrails/index.html'), *public_pages]:
    txt = p.read_text() if p.is_file() else ''
    check(not aloo_ref.search(txt), f'{p}: zero links or mentions of Aloo Mannu', f'{p}: leaks Aloo Mannu link/mention')
    check(not connect_ref.search(txt), f'{p}: zero links or mentions of Coco Connect', f'{p}: leaks Coco Connect link/mention')

# Assert all 12 product pages render the 5 Signal content sections
all_product_pages = [aloo_path, *public_pages]
expected_windows = {
    'voice': 'Next release in preparation; tagged builds publish on GitHub Releases.',
    'coco': 'Next major release (v2.0) in preparation; updates publish on GitHub Releases and npm.',
}
for p in all_product_pages:
    slug = p.parent.name
    txt = p.read_text() if p.is_file() else ''
    check('id="what-it-is"' in txt and 'What it is</h2>' in txt, f'{p}: has Section 1 (What it is)', f'{p}: missing Section 1')
    check('id="capabilities"' in txt and 'What it can do today</h2>' in txt, f'{p}: has Section 2 (What it can do today)', f'{p}: missing Section 2')
    check('id="cooking"' in txt and 'What’s cooking</h2>' in txt, f'{p}: has Section 3 (What’s cooking)', f'{p}: missing Section 3')
    check('id="stage"' in txt and 'How far along</h2>' in txt, f'{p}: has Section 4 (How far along)', f'{p}: missing Section 4')
    check('id="when"' in txt and 'When</h2>' in txt, f'{p}: has Section 5 (When)', f'{p}: missing Section 5')

    expected_win = expected_windows.get(slug, 'Not dated yet')
    check(expected_win in txt, f'{p}: When window is {expected_win!r}', f'{p}: missing expected launch window {expected_win!r}')

    # Progress bar only where milestones/releases are counted (coco and voice)
    if slug in ('coco', 'voice'):
        check('stage-progress' in txt and 'progress-fill' in txt, f'{p}: has counted milestone progress bar', f'{p}: missing progress bar')
    else:
        check('stage-progress' not in txt, f'{p}: zero speculative progress bar', f'{p}: contains uncounted progress bar')

# Assert all 13 site-refs/facts/<slug>.json files exist, pass hygiene, and resolve in-repo sources
all_slugs = [p.parent.name for p in all_product_pages]
internal_markers = re.compile(r'\b(?:lab-\d{3,5}|hq-\w+)\b')
valid_sections = {'what-it-is', 'capabilities', 'cooking', 'stage', 'when'}
stopwords = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'your', 'into', 'are', 'its', 'not',
    'has', 'have', 'can', 'all', 'one', 'two', 'three', 'four', 'each', 'any', 'only', 'own',
    'out', 'off', 'via', 'per', 'new', 'use', 'used', 'using', 'runs', 'run', 'today', 'next',
    'built', 'local', 'machine', 'computer', 'mac', 'macos', 'coco', 'research',
}
repo_root = Path(__file__).resolve().parents[1]
repo_candidates = {slug: [] for slug in all_slugs}
for in_repo in ('coco', 'signal', 'catalog'):
    repo_candidates[in_repo] = [repo_root]
for entry in re.split(r'[,;]', os.environ.get('SITE_FACTS_ROOTS', '')):
    if '=' in entry:
        k, v = entry.split('=', 1)
        k, v = k.strip(), v.strip()
        if k in repo_candidates and v:
            repo_candidates[k].append(Path(v))


def verify_fact_source(fp, item):
    claim = item.get('claim', '')
    src = item.get('source', '')
    parts = src.split(':')
    prefix = parts[0] if parts else ''
    if prefix in ('launch-window', 'gap', 'measured', 'plan') and len(parts) == 2 and parts[1]:
        return True
    if prefix in repo_candidates and len(parts) == 3 and parts[1] == 'pr' and parts[2].isdigit():
        return int(parts[2]) > 0
    if prefix in repo_candidates and len(parts) == 3 and parts[1] == 'tag' and parts[2]:
        existing = [d for d in repo_candidates[prefix] if d.is_dir()]
        if not existing:
            return True
        out = subprocess.run(['git', '-C', str(existing[0]), 'tag', '-l', parts[2]], capture_output=True, text=True)
        return out.returncode == 0 and parts[2] in out.stdout.splitlines()
    if prefix in repo_candidates and len(parts) == 2 and parts[1]:
        existing = [d for d in repo_candidates[prefix] if d.is_dir()]
        if not existing:
            return True
        return any((d / parts[1]).exists() for d in existing)
    if prefix in repo_candidates and len(parts) == 3 and parts[2].isdigit():
        ln = int(parts[2])
        if ln < 1:
            return False
        existing = [d for d in repo_candidates[prefix] if d.is_dir()]
        if not existing:
            return True
        target = next((d / parts[1] for d in existing if (d / parts[1]).is_file()), None)
        if target is None:
            fail_(f'{fp}: cited file missing for {src}')
            return False
        lines = target.read_text(errors='replace').splitlines()
        if ln > len(lines) or not lines[ln - 1].strip():
            fail_(f'{fp}: cited line invalid or blank for {src}')
            return False
        lo = max(0, ln - 3)
        hi = min(len(lines), ln + 2)
        window = '\n'.join(lines[lo:hi]).lower()
        win_words = set(re.findall(r'[a-z0-9]+', window))
        win_vers = set(re.findall(r'\d+\.\d+(?:\.\d+)?', window))
        synonyms = {'finds': 'detect', 'connected': 'connect'}
        tokens = [t for t in re.findall(r'[a-z0-9]{3,}', claim.lower()) if t not in stopwords]
        vers = [v.lstrip('v') for v in re.findall(r'\bv?\d+\.\d+(?:\.\d+)?\b', claim.lower())]
        matched = any(
            t in win_words or t.rstrip('s') in win_words or (t + 's') in win_words or synonyms.get(t) in win_words
            for t in tokens
        ) or any(v in win_vers for v in vers)
        if (tokens or vers) and not matched:
            fail_(f'{fp}: cited window around {src} lacks claim terms')
            return False
        return True
    fail_(f'{fp}: unrecognised or malformed source {src!r}')
    return False


facts_files = []
for slug in all_slugs:
    fp = Path(f'site-refs/facts/{slug}.json')
    check(fp.is_file(), f'{fp} exists', f'{fp} missing')
    facts_files.append(fp)
    if fp.is_file():
        try:
            items = json.loads(fp.read_text())
            check(isinstance(items, list) and len(items) >= 3, f'{fp}: has >= 3 facts ({len(items)} facts)', f'{fp}: invalid facts list')
            resolved_all = True
            for item in items:
                has_keys = (
                    isinstance(item.get('claim'), str) and bool(item['claim'].strip())
                    and item.get('section') in valid_sections
                    and isinstance(item.get('source'), str) and bool(item['source'].strip())
                )
                if not has_keys or not verify_fact_source(fp, item):
                    resolved_all = False
            check(resolved_all, f'{fp}: all {len(items)} citations resolved and grounded', f'{fp}: citation verification failed')
        except Exception as e:
            fail_(f'{fp}: JSON parse error: {e}')

# Assert key verified content invariants across updated product pages
coco_html = Path('coco/index.html').read_text()
check('10 of 10 milestone releases (v1.0.0 to v1.10.0). v2.0 is next.' in coco_html
      and 'Coco MCP server' in coco_html
      and 'commands running on your disk' not in coco_html,
      'coco/index.html: matches verified SI facts and progress line',
      'coco/index.html: drifted from verified SI facts')

voice_html = Path('voice/index.html').read_text()
voice_before_credits, voice_credits_sep, voice_credits_part = voice_html.partition('<section id="credits"')
check('8 of 8 tagged releases published (0.9.2 to 0.11.0, latest 17 November 2026)' in voice_html
      and 'Available now, v0.11.0' in voice_html
      and 'Meeting notes core with segment citations' in voice_html
      and 'Dedicated Meetings screens' in voice_html
      and 'whisper.cpp' not in voice_html,
      'voice/index.html: matches verified v0.11.0 Voice facts and release count',
      'voice/index.html: drifted from verified v0.11.0 Voice facts')
check('handy' not in index_text.lower()
      and 'handy' not in Path('data/products.json').read_text().lower()
      and 'handy' not in voice_before_credits.lower()
      and bool(voice_credits_sep)
      and 'Credits:' in voice_credits_part
      and 'https://github.com/cjpais/Handy' in voice_credits_part
      and 'MIT License' in voice_credits_part,
      'Handy removed from descriptions/taglines and preserved in one bottom Credits line on voice/index.html',
      'Handy leaked outside bottom Credits line or missing MIT credit line')

m0_html = Path('m0/index.html').read_text()
m0_facts_txt = Path('site-refs/facts/m0.json').read_text()
m0_internal_re = re.compile(
    r'\b(coco-m0d|coco_m0_hook|connect-m0-backend|capture_block|connect_cli|codex_notify|127\.0\.0\.1|daemon|embedder|block list|read door|10 of 10|21 to 53)\b',
    re.I,
)
check('Coco M0' in m0_html and 'Private beta' in m0_html and 'Details soon' in m0_html
      and not m0_internal_re.search(m0_html) and not m0_internal_re.search(m0_facts_txt),
      'm0/index.html and m0.json: free of M0 internals and unlinked benchmark numbers',
      'm0/index.html or m0.json leaked M0 internals or unlinked numbers')

teams_ng_html = Path('teams-ng/index.html').read_text()
check('Private beta' in teams_ng_html and 'Details soon' in teams_ng_html
      and '1,199' not in teams_ng_html and '114 of 150' not in teams_ng_html
      and 'github.com/coco-research/teams-ng' not in teams_ng_html,
      'teams-ng/index.html: states Private beta without unlinked numbers or private repo links',
      'teams-ng/index.html: leaked unlinked numbers or private repo links')

for gap_slug in ('signal', 'mira', 'loops', 'jev-use', 'heliopause', 'm0', 'hermes', 'teams-ng', 'status-zero', 'aloomannu'):
    g_html = Path(f'{gap_slug}/index.html').read_text()
    cook_part = g_html.split('id="cooking"', 1)[1].split('</section>', 1)[0] if 'id="cooking"' in g_html else ''
    check('Details soon' in cook_part, f'{gap_slug}/index.html: cooking section states Details soon honestly',
          f'{gap_slug}/index.html: cooking section missing Details soon')

all_checked_files = [
    css_path, scene_path, motifs_a_path, motifs_b_path,
    Path('scripts/render-product-pages.py'), Path('scripts/render-site-products.py'),
    Path('data/product-pages-public.json'), Path('data/product-pages-lab.json'),
    aloo_path, *public_pages, *facts_files,
]
for p in all_checked_files:
    txt = p.read_text() if p.is_file() else ''
    if p.suffix in ('.html', '.js'):
        check(not runtime_net.search(txt), f'{p}: zero runtime fetch/XHR', f'{p}: contains runtime network call')
    check(not local_path_leak.search(txt), f'{p}: free of host filesystem paths', f'{p}: contains host path')
    check(not internal_markers.search(txt), f'{p}: free of internal ticket markers', f'{p}: contains internal ticket marker')

print()
if fail == 0:
    print('  all 12 3D product pages and homepage link invariants passed')
    sys.exit(0)
sys.exit(1)
