#!/usr/bin/env python3
"""Render static 3D product pages from data/products.json and page specs.

Run from the repo root. Default mode writes every product page. --check exits 1
with a unified diff when any rendered page is missing or stale.
"""
import argparse
import difflib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
DATA = ROOT / 'data' / 'products.json'
SPEC_PUBLIC = ROOT / 'data' / 'product-pages-public.json'
SPEC_LAB = ROOT / 'data' / 'product-pages-lab.json'
INDEX = ROOT / 'index.html'
ANCHOR = re.compile(r'<a class="inline" href="([^"]*)" rel="noopener">([^<]*)</a>')
IMPORTMAP_RE = re.compile(r'<script type="importmap">\s*(\{.*?\})\s*</script>', re.S)

DIAGRAMS = {
    'editions': '<rect x="34" y="28" width="96" height="84" rx="4"/><rect x="112" y="20" width="96" height="84" rx="4"/><rect x="190" y="36" width="96" height="84" rx="4"/><line x1="34" y1="56" x2="286" y2="56" stroke-opacity=".35"/><circle cx="160" cy="62" r="5" fill="currentColor"/>',
    'frames': '<rect x="52" y="16" width="56" height="108" rx="6" stroke-opacity=".45"/><rect x="132" y="16" width="56" height="108" rx="6"/><rect x="212" y="16" width="56" height="108" rx="6" stroke-opacity=".45"/><path d="M24 72 Q92 26 160 72 T296 72"/><path d="M24 72 Q92 118 160 72 T296 72" stroke-opacity=".5"/>',
    'torus': '<ellipse cx="160" cy="70" rx="108" ry="36"/><ellipse cx="160" cy="70" rx="68" ry="20" stroke-opacity=".45"/><circle cx="52" cy="70" r="14"/><circle cx="268" cy="70" r="14"/><circle cx="160" cy="34" r="12"/><circle cx="160" cy="106" r="12"/>',
    'ripple': '<circle cx="76" cy="70" r="14"/><circle cx="76" cy="70" r="30" stroke-opacity=".6"/><circle cx="76" cy="70" r="48" stroke-opacity=".32"/><rect x="156" y="24" width="132" height="92" rx="7"/><line x1="156" y1="44" x2="288" y2="44" stroke-opacity=".45"/><circle cx="222" cy="76" r="5" fill="currentColor"/>',
    'heliosphere': '<path d="M214 14 Q292 70 214 126"/><path d="M194 26 Q256 70 194 114" stroke-opacity=".45"/><ellipse cx="128" cy="70" rx="74" ry="28" stroke-opacity=".5"/><ellipse cx="128" cy="70" rx="44" ry="16"/><circle cx="128" cy="70" r="6" fill="currentColor"/>',
    'vault': '<polygon points="160,18 208,44 208,96 160,122 112,96 112,44"/><line x1="160" y1="18" x2="160" y2="122" stroke-opacity=".4"/><line x1="112" y1="44" x2="208" y2="96" stroke-opacity=".4"/><line x1="208" y1="44" x2="112" y2="96" stroke-opacity=".4"/><circle cx="48" cy="42" r="6"/><circle cx="272" cy="42" r="6"/><circle cx="48" cy="98" r="6"/><circle cx="272" cy="98" r="6"/><line x1="54" y1="44" x2="112" y2="58" stroke-opacity=".45"/><line x1="266" y1="44" x2="208" y2="58" stroke-opacity=".45"/>',
    'folios': '<rect x="54" y="26" width="180" height="88" rx="4" stroke-opacity=".35"/><rect x="70" y="20" width="180" height="88" rx="4" stroke-opacity=".6"/><rect x="86" y="14" width="180" height="88" rx="4"/><rect x="112" y="46" width="118" height="18" rx="3" fill="currentColor" fill-opacity=".18"/><line x1="32" y1="112" x2="288" y2="28"/>',
    'council': '<ellipse cx="160" cy="74" rx="54" ry="20"/><ellipse cx="160" cy="74" rx="112" ry="44" stroke-opacity=".4"/><circle cx="160" cy="30" r="6" fill="currentColor"/><circle cx="254" cy="52" r="5"/><circle cx="254" cy="96" r="5"/><circle cx="160" cy="118" r="5"/><circle cx="66" cy="96" r="5"/><circle cx="66" cy="52" r="5"/>',
    'lattice': '<rect x="38" y="24" width="76" height="92" rx="4"/><rect x="206" y="24" width="76" height="92" rx="4"/><line x1="114" y1="42" x2="206" y2="42"/><line x1="114" y1="68" x2="206" y2="68"/><line x1="114" y1="94" x2="154" y2="94" stroke-dasharray="4 4"/><circle cx="164" cy="94" r="5" fill="currentColor"/>',
    'router': '<line x1="160" y1="16" x2="160" y2="124"/><circle cx="160" cy="44" r="4" fill="currentColor"/><circle cx="160" cy="70" r="4" fill="currentColor"/><circle cx="160" cy="96" r="4" fill="currentColor"/><circle cx="54" cy="38" r="8"/><circle cx="54" cy="102" r="8"/><circle cx="266" cy="38" r="8"/><circle cx="266" cy="102" r="8"/><path d="M62 38 Q160 20 258 38" stroke-opacity=".55"/><path d="M258 102 Q160 120 62 102" stroke-opacity=".55"/>',
}


def esc(val):
    return html.escape(val, quote=False)


def attr(val):
    return html.escape(val, quote=True)


def require_https(href, where):
    if '<' in href or '>' in href or not href.startswith('https://'):
        sys.exit('%s: href must be https://' % where)


def render_desc_html(raw, where):
    out, pos = [], 0
    for m in ANCHOR.finditer(raw):
        before = raw[pos:m.start()]
        if '<' in before or '>' in before:
            sys.exit('%s: disallowed tag' % where)
        out.append(esc(before))
        require_https(m.group(1), where)
        out.append('<a class="inline" href="%s" rel="noopener">%s</a>' % (attr(m.group(1)), esc(m.group(2))))
        pos = m.end()
    rest = raw[pos:]
    if '<' in rest or '>' in rest:
        sys.exit('%s: disallowed tag' % where)
    out.append(esc(rest))
    return ''.join(out)


def read_three_url():
    m = IMPORTMAP_RE.search(INDEX.read_text())
    if not m:
        sys.exit('index.html missing importmap')
    three = json.loads(m.group(1)).get('imports', {}).get('three', '')
    require_https(three, 'importmap three')
    return three


def panel_art(row, spec):
    if 'art' in row:
        svg = (ROOT / row['art']).read_text().strip()
        return '\n'.join('            ' + ln for ln in svg.splitlines())
    inner = DIAGRAMS[spec['diagram']]
    return '            <svg viewBox="0 0 320 140" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % inner


def build_catalog(data, pub_specs, lab_specs):
    items = []
    for stage in ('shipped', 'source', 'lab'):
        spec_map = pub_specs if stage != 'lab' else lab_specs['lab']
        for row in data[stage]:
            pid = row['id']
            if pid not in spec_map:
                sys.exit('missing page spec for %s' % pid)
            items.append((pid, stage, row, spec_map[pid]))
    for pid, u in lab_specs.get('unlinked', {}).items():
        row = {'id': pid, 'name': u['name'], 'status': u['tag'], 'description': u['description']}
        items.append((pid, 'lab', row, u))
    return items


def render_page(pid, stage, row, spec, data, three_url):
    slug = spec['slug']
    name = esc(row['name'])
    tag = esc(row['tag'] if stage == 'shipped' else row['status'])
    desc_html = render_desc_html(row['description_html'], pid) if stage == 'shipped' else esc(row['description'])
    raw_plain = re.sub(r'<[^>]+>', '', row.get('description_html', row.get('description', ''))).strip()
    meta_desc = attr(spec.get('meta_description', raw_plain))
    og_img = attr(spec.get('og_image', 'https://cocoresearch.org/assets/img/og-cinematic.jpg'))
    robots = '\n<meta name="robots" content="noindex, nofollow">' if spec.get('noindex') else ''

    if stage == 'shipped':
        nav_href = attr(row['actions'][0]['href'])
        ctas = '\n'.join(
            '          <a class="btn btn-%s" href="%s">%s<span class="sr-only">%s</span></a>'
            % (a['kind'], attr(a['href']), esc(a['label']), esc(a['sr']))
            for a in row['actions']
        )
    elif stage == 'source':
        require_https(row['href'], pid)
        nav_href = attr(row['href'])
        ctas = '\n'.join([
            '          <a class="btn btn-primary" href="%s">View source on GitHub</a>' % attr(row['href']),
            '          <a class="btn btn-ghost" href="../#lab">All products</a>',
        ])
    else:
        nav_href = '../#lab'
        ctas = '\n'.join([
            '          <a class="btn btn-primary" href="../#lab">In the lab roll call</a>',
            '          <a class="btn btn-ghost" href="../#rules">Read our four rules</a>',
        ])

    kns = '\n'.join(
        '          <div class="kn"><span class="kn-num">%s</span><span class="kn-lbl">%s</span></div>' % (esc(n), esc(l))
        for n, l in spec['kns']
    )
    extra = ''
    if spec.get('extra_links'):
        links = ''.join('<a class="inline" href="%s">%s</a>' % (attr(u), esc(lbl)) for lbl, u in spec['extra_links'])
        extra = '\n          <div class="extra-links">%s</div>' % links

    secs = spec['sections']
    what = secs['what_it_is']
    what_tagline = esc(what['tagline'])
    what_paragraph = esc(what['paragraph'])

    cap_rows = []
    for c in secs['capabilities']:
        cap_rows.append(
            '        <div class="signal-item">\n'
            '          <span class="signal-num">%s</span>\n'
            '          <div class="signal-body">\n'
            '            <h3>%s</h3>\n'
            '            <p>%s</p>\n'
            '          </div>\n'
            '        </div>' % (esc(c['num']), esc(c['title']), esc(c['desc']))
        )
    cap_items = '\n'.join(cap_rows)

    cook_rows = []
    for c in secs['cooking']:
        cook_rows.append(
            '        <div class="signal-item">\n'
            '          <span class="signal-num">%s</span>\n'
            '          <div class="signal-body">\n'
            '            <h3>%s</h3>\n'
            '            <p>%s</p>\n'
            '          </div>\n'
            '        </div>' % (esc(c['num']), esc(c['title']), esc(c['desc']))
        )
    cooking_items = '\n'.join(cook_rows)

    st = secs['stage']
    chip_label = esc(st['chip'])
    chip_class = attr(st['class'])
    stage_desc = esc(st['desc'])
    progress_markup = ''
    if 'progress' in st:
        p = st['progress']
        progress_markup = (
            '\n          <div class="stage-progress">\n'
            '            <div class="progress-meta"><span class="progress-count">%s</span></div>\n'
            '            <div class="progress-track" role="progressbar" aria-valuenow="%s" aria-valuemin="0" aria-valuemax="%s">\n'
            '              <div class="progress-fill" style="width: %s%%"></div>\n'
            '            </div>\n'
            '          </div>' % (esc(p['count']), attr(str(p['now'])), attr(str(p['max'])), attr(str(p['pct'])))
        )

    when_text = esc(secs['when'])

    specs_sec = ''
    if spec.get('specs'):
        rows = '\n'.join('        <tr><th>%s</th><td>%s</td></tr>' % (esc(k), esc(v)) for k, v in spec['specs'])
        specs_sec = """
  <section id="specs" class="sec" aria-labelledby="h-specs">
    <div class="wrap">
      <div class="sec-head"><div><p class="eyebrow">Release figures</p><h2 id="h-specs" class="sec-title">By the numbers.</h2></div><p class="sec-sub">Figures match the latest tagged release.</p></div>
      <table class="spec-table">
%(rows)s
      </table>
    </div>
  </section>""" % {'rows': rows}

    credits_sec = ''
    if spec.get('credits_html'):
        credits_sec = (
            '\n  <section id="credits" class="sec sec-credits" aria-label="Credits">\n'
            '    <div class="wrap">\n'
            '      <p class="credits-note">%s</p>\n'
            '    </div>\n'
            '  </section>' % render_desc_html(spec['credits_html'], '%s.credits_html' % pid)
        )

    def foot_list(group):
        return '\n'.join('          <li><a href="../%s">%s</a></li>' % (attr(r['page']), esc(r['name'])) for r in data[group])

    lic_li = '\n          <li><a href="%s">Licence</a></li>' % attr(spec['licence_href']) if spec.get('licence_href') else ''
    cats_script = ''
    cats_banner = ''
    if spec.get('cats_stage'):
        cs = spec['cats_stage']
        cats_script = '\n<script type="module" src="../assets/js/aloo-cats-scene.js"></script>'
        cats_banner = """
      <div class="aloo-banner" role="region" aria-label="3D Three.js Aloo Mannu banner stage">
        <canvas id="aloo-cats-canvas" aria-hidden="true"></canvas>
        <div class="aloo-banner-copy">
          <p class="aloo-banner-title" aria-hidden="true"><span>Aloo</span><span>Mannu</span></p>
          <p class="aloo-banner-tagline">%s</p>
        </div>
        <button class="aloo-pause-btn" type="button" data-cats-motion-toggle>Pause motion</button>
      </div>
      <p class="aloo-story">%s</p>""" % (esc(cs['tagline']), esc(cs['story']))
    return """<!doctype html>
<html lang="en" data-product="%(pid)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">%(robots)s
<title>%(name)s — Coco Research</title>
<meta name="description" content="%(meta_desc)s">
<meta name="theme-color" content="#03050b">
<meta name="color-scheme" content="dark light">
<meta property="og:type" content="website">
<meta property="og:title" content="%(name)s — Coco Research">
<meta property="og:description" content="%(meta_desc)s">
<meta property="og:url" content="https://cocoresearch.org/%(slug)s/">
<meta property="og:image" content="%(og_img)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:description" content="%(meta_desc)s">
<link rel="canonical" href="https://cocoresearch.org/%(slug)s/">
<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/site/favicon-32.png">
<script>
(function () {
  var d = document.documentElement, rm = false, off = false, th = '';
  try { rm = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  try { off = localStorage.getItem('coco-motion') === 'off'; } catch (e) {}
  try { th = localStorage.getItem('coco-theme') || ''; } catch (e) {}
  if (/[?&]motion=off/.test(location.search)) off = true;
  var m = /[?&]theme=(light|dark)/.exec(location.search);
  if (m) th = m[1];
  if (th === 'light' || th === 'dark') d.setAttribute('data-theme', th);
  d.className += ' js ' + (rm || off ? 'static' : 'cine') + (rm ? ' os-reduced' : '');
})();
</script>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="preload" as="font" type="font/woff2" crossorigin href="https://cdn.jsdelivr.net/npm/@fontsource-variable/archivo@5.3.0/files/archivo-latin-wdth-normal.woff2">
<link rel="stylesheet" href="../assets/css/product.css">
<script type="importmap">
{ "imports": { "three": "%(three_url)s" } }
</script>
<script type="module" src="../assets/js/product-scene.js"></script>%(cats_script)s
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<a class="skip" href="?motion=off">View plain page (no motion)</a>
<div class="world" aria-hidden="true"><canvas id="world"></canvas><div class="hero-point"></div></div>
<header class="nav">
  <a class="brand" href="../"><i aria-hidden="true"></i><span>Coco Research</span></a>
  <div class="nav-right">
    <button class="chip-btn" type="button" data-theme-toggle aria-pressed="false">Light theme</button>
    <a class="btn btn-primary btn-sm nav-cta-hide" href="%(nav_href)s">%(nav_cta)s</a>
  </div>
</header>
<main id="main" class="stage-main">
  <section id="hero" class="hero" aria-labelledby="h-hero">
    <div class="wrap">%(cats_banner)s
      <div class="hero-col">
        <p class="mark-line"><span class="mark-dot" data-stage="%(stage)s" aria-hidden="true"></span>%(tag)s</p>
        <h1 id="h-hero" class="display">%(name)s</h1>
        <p class="lede">%(desc_html)s</p>
        <div class="cta-row">
%(ctas)s
        </div>
        <div class="kns" aria-label="Key facts">
%(kns)s
        </div>
      </div>
    </div>
  </section>
  <section id="what-it-is" class="sec" aria-labelledby="h-what-it-is">
    <div class="wrap">
      <div class="sec-head">
        <div><p class="eyebrow">Overview</p><h2 id="h-what-it-is" class="sec-title">What it is</h2></div>
        <p class="sec-sub">%(tag)s</p>
      </div>
      <div class="panel-grid">
        <div class="panel">
          <div class="wave-art" aria-hidden="true">
%(art_svg)s
          </div>
          <p class="sec-sub">%(panel_note)s</p>%(extra)s
        </div>
        <div class="panel">
          <p class="section-tagline">%(what_tagline)s</p>
          <p class="section-para">%(what_paragraph)s</p>
        </div>
      </div>
    </div>
  </section>
  <section id="capabilities" class="sec" aria-labelledby="h-capabilities">
    <div class="wrap">
      <div class="sec-head">
        <div><p class="eyebrow">Capabilities</p><h2 id="h-capabilities" class="sec-title">What it can do today</h2></div>
        <p class="sec-sub">Provably true of the code and releases available today.</p>
      </div>
      <div class="signal-list">
%(cap_items)s
      </div>
    </div>
  </section>
  <section id="cooking" class="sec" aria-labelledby="h-cooking">
    <div class="wrap">
      <div class="sec-head">
        <div><p class="eyebrow">Roadmap</p><h2 id="h-cooking" class="sec-title">What’s cooking</h2></div>
        <p class="sec-sub">The next milestones sourced from active work and release roadmaps.</p>
      </div>
      <div class="signal-list">
%(cooking_items)s
      </div>
    </div>
  </section>
  <section id="stage" class="sec" aria-labelledby="h-stage">
    <div class="wrap">
      <div class="sec-head">
        <div><p class="eyebrow">Maturity</p><h2 id="h-stage" class="sec-title">How far along</h2></div>
        <p class="sec-sub">Current development and release milestone tracking.</p>
      </div>
      <div class="stage-card">
        <div class="stage-badge-row">
          <span class="stage-chip stage-chip-%(chip_class)s">%(chip_label)s</span>%(progress_markup)s
        </div>
        <p class="sec-sub">%(stage_desc)s</p>
      </div>
    </div>
  </section>
  <section id="when" class="sec" aria-labelledby="h-when">
    <div class="wrap">
      <div class="sec-head">
        <div><p class="eyebrow">Launch window</p><h2 id="h-when" class="sec-title">When</h2></div>
        <p class="sec-sub">Public release and availability schedule.</p>
      </div>
      <div class="when-card">
        <p class="when-window">%(when_text)s</p>
      </div>
    </div>
  </section>%(specs_sec)s%(credits_sec)s
</main>
<footer class="foot">
  <div class="foot-inner">
    <div class="foot-brand">
      <a class="brand" href="../"><i aria-hidden="true"></i><span>Coco Research</span></a>
      <p>Governed AI, built in the open. Built by Rijul Kalra.</p>
    </div>
    <nav class="foot-cols" aria-label="Footer">
      <div><h2>Products</h2><ul>
%(foot_shipped)s
      </ul></div>
      <div><h2>Source available</h2><ul>
%(foot_source)s
      </ul></div>
      <div><h2>In the lab (private)</h2><ul>
%(foot_lab)s
      </ul></div>
      <div><h2>Company</h2><ul>
          <li><a href="../#built-by">About</a></li>
          <li><a href="https://github.com/coco-research/coco/releases">Coco changelog</a></li>
      </ul></div>
      <div><h2>Code</h2><ul>
          <li><a href="https://github.com/coco-research">GitHub</a></li>
          <li><a href="https://www.npmjs.com/package/cocosuperintelligence">npm</a></li>%(lic_li)s
      </ul></div>
    </nav>
  </div>
  <div class="foot-base">
    <p>© 2026 Coco Research</p>
    <div class="foot-ctrls">
      <button class="link-btn" type="button" data-theme-toggle>Light theme</button>
      <button class="link-btn" type="button" data-motion-toggle>Reduce motion</button>
    </div>
  </div>
</footer>
</body>
</html>
""" % {
        'pid': attr(pid), 'slug': attr(slug), 'robots': robots, 'name': name, 'meta_desc': meta_desc,
        'og_img': og_img, 'three_url': attr(three_url), 'nav_href': nav_href, 'nav_cta': esc(spec['nav_cta']),
        'stage': attr(stage), 'tag': tag, 'desc_html': desc_html, 'ctas': ctas, 'kns': kns,
        'art_svg': panel_art(row, spec), 'panel_note': esc(spec['panel_note']), 'extra': extra,
        'what_tagline': what_tagline, 'what_paragraph': what_paragraph,
        'cap_items': cap_items, 'cooking_items': cooking_items,
        'chip_label': chip_label, 'chip_class': chip_class,
        'progress_markup': progress_markup, 'stage_desc': stage_desc,
        'when_text': when_text, 'specs_sec': specs_sec, 'credits_sec': credits_sec,
        'foot_shipped': foot_list('shipped'), 'foot_source': foot_list('source'), 'foot_lab': foot_list('lab'),
        'lic_li': lic_li, 'cats_script': cats_script, 'cats_banner': cats_banner,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='exit 1 with a unified diff if any page is stale')
    parser.add_argument('--only', help='comma-separated product ids to write')
    args = parser.parse_args()
    data = json.loads(DATA.read_text())
    pub_specs = json.loads(SPEC_PUBLIC.read_text())
    lab_specs = json.loads(SPEC_LAB.read_text())
    three_url = read_three_url()
    only = set(args.only.split(',')) if args.only else None

    stale = False
    for pid, stage, row, spec in build_catalog(data, pub_specs, lab_specs):
        if only and pid not in only:
            continue
        rel = '%s/index.html' % spec['slug']
        target = ROOT / rel
        rendered = render_page(pid, stage, row, spec, data, three_url)
        old = target.read_text() if target.is_file() else ''
        if args.check:
            if old != rendered:
                stale = True
                sys.stdout.writelines(difflib.unified_diff(
                    old.splitlines(keepends=True), rendered.splitlines(keepends=True),
                    fromfile=rel, tofile='%s (rendered)' % rel,
                ))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if old != rendered:
                target.write_text(rendered)
    if args.check and stale:
        sys.exit(1)


if __name__ == '__main__':
    main()
