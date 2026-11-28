#!/usr/bin/env python3
"""Render the whole product surface from data/products.json and the page specs.

Generates the static 3D product pages (<slug>/index.html, 10 products in two groups:
Products and In the lab), /products/, /lab/, /whats-new/, sitemap.xml and llms.txt.
Run from the repo root. Default mode writes every file except the hand-built pages
in CUSTOM_PAGES (m0 today); --include-custom renders those too. --check exits 1
with a unified diff when any generated file is missing or stale.
--print-nav <current> prints the shared top bar + drawer for hand-built pages.
"""
import argparse
import difflib
import importlib.util
import re
import sys
from pathlib import Path


def _load_shared():
    shared_path = Path(__file__).resolve().parent / 'render_product_shared.py'
    spec = importlib.util.spec_from_file_location('render_product_shared', shared_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_shared = _load_shared()

ROOT, SITE, DEFAULT_OG = _shared.ROOT, _shared.SITE, _shared.DEFAULT_OG
GROUPS, CUSTOM_PAGES = _shared.GROUPS, _shared.CUSTOM_PAGES
SLOT_ICON, SEC_CLOSE = _shared.SLOT_ICON, _shared.SEC_CLOSE

esc, attr, require_https, render_desc_html = _shared.esc, _shared.attr, _shared.require_https, _shared.render_desc_html
world_fallback_svg, build_jsonld = _shared.world_fallback_svg, _shared.build_jsonld
ld_script, breadcrumb, collection_ld = _shared.ld_script, _shared.breadcrumb, _shared.collection_ld
human_date, load_catalog, counts_ctx = _shared.human_date, _shared.load_catalog, _shared.counts_ctx
stage_chip_text, stage_label, stage_shape = _shared.stage_chip_text, _shared.stage_label, _shared.stage_shape
stage_key, short_status, STAGES = _shared.stage_key, _shared.short_status, _shared.STAGES
nav_html, footer_html, head_html = _shared.nav_html, _shared.footer_html, _shared.head_html
li_dl, copy_box, part_head = _shared.li_dl, _shared.copy_box, _shared.part_head
stage_page, dir_hero, sec_open = _shared.stage_page, _shared.dir_hero, _shared.sec_open


_NUM_WORDS = (
    'zero', 'one', 'two', 'three', 'four', 'five', 'six',
    'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
)


def _count_word(n, cap=False):
    word = _NUM_WORDS[n] if 0 <= n < len(_NUM_WORDS) else str(n)
    return word.capitalize() if cap else word


def _safe_href(href, where):
    if not href.startswith(('../', '#', 'mailto:')):
        require_https(href, where)
    return href


# ---------------------------------------------------------------- product page
def render_page(it, data):
    pid, row, spec, bucket = it['pid'], it['row'], it['spec'], it['bucket']
    catalog = it['catalog']
    slug = spec['slug']
    name = esc(row['name'])
    page_title = spec.get('page_title', '%s \u2014 Coco Research' % row['name'])
    robots = '\n<meta name="robots" content="noindex, nofollow">' if spec.get('noindex') else ''
    jsonld = build_jsonld(pid, bucket, row, spec)
    private = bucket == 'lab'

    # ---- hero (above the fold) ----
    ta = spec['try_above']
    if ta['kind'] == 'static':
        act = '<span class="p-static-pill"><span class="sh sh-sq" aria-hidden="true"></span>%s</span>' % esc(ta['label'])
    elif ta['kind'] == 'command':
        ib = spec['try']['install']
        act = copy_box(ib['label'], ib['cmd']).replace('try-box', 'try-box p-try-cmd')
    else:
        act = '<a class="btn btn-primary" href="%s">%s</a>' % (attr(_safe_href(ta['href'], '%s.try_above.href' % pid)), esc(ta['label']))
    alt = spec.get('try_alt')
    alt_html = '\n          <a class="btn btn-ghost" href="%s">%s</a>' % (
        attr(_safe_href(alt['href'], '%s.try_alt.href' % pid)), esc(alt['label'])) if alt else ''
    note_html = '\n        <p class="p-try-note">%s</p>' % esc(ta['note']) if ta.get('note') else ''
    cats_stage = spec.get('cats_stage')
    cats_banner = cats_script = ''
    if cats_stage:
        cats_script = '\n<script type="module" src="../assets/js/aloo-cats-scene.js"></script>'
        cats_banner = f"""
      <div class="aloo-banner" role="region" aria-label="3D Three.js Aloo Mannu banner stage">
        <canvas id="aloo-cats-canvas" aria-hidden="true"></canvas>
        <div class="aloo-banner-copy">
          <p class="aloo-banner-title" aria-hidden="true"><span>Aloo</span><span>Mannu</span></p>
          <p class="aloo-banner-tagline">{esc(cats_stage['tagline'])}</p>
        </div>
        <button class="aloo-pause-btn" type="button" data-cats-motion-toggle>Pause motion</button>
      </div>
      <p class="aloo-story">{esc(cats_stage['story'])}</p>"""

    # ---- part 03 ----
    slot_label = spec.get('slot_label') or (
        'Real app capture not yet added \u2014 %s' % row['name'] if bucket == 'shipped'
        else 'Real capture not yet added \u2014 %s' % row['name'])
    caps = []
    for i, (title, desc) in enumerate(spec['does'], 1):
        caps.append(
            '        <article class="cap-card">\n'
            '          <div class="cap-head"><span class="cap-idx">%02d</span><h3 class="cap-title">%s</h3></div>\n'
            '          <p class="cap-desc">%s</p>\n'
            '          <div class="cap-slot" role="img" aria-label="%s">\n'
            '            %s\n'
            '            <span class="cap-slot-tag">%s</span>\n'
            '            <span class="cap-slot-meta">%s</span>\n'
            '          </div>\n'
            '        </article>' % (i, esc(title), esc(desc), attr('Capture slot for ' + title + '. ' + slot_label), SLOT_ICON, esc(slot_label),
                                   'Nothing is mocked up here.' if private else 'Awaiting a real running-app screenshot. Nothing is mocked up here.'))
    cap_items = '\n'.join(caps)

    # ---- part 04 ----
    tr = spec['try']
    parts = ['          <p class="try-lead">%s</p>' % esc(tr['lead'])]
    if tr.get('install'):
        parts.append('          ' + copy_box(tr['install']['label'], tr['install']['cmd']))
    if tr.get('clone'):
        parts.append('          ' + copy_box('Clone %s' % row['name'], 'git clone %s' % tr['clone']))
    if tr.get('downloads'):
        parts.append('          <ul class="try-dl" aria-label="Installers in the release">\n%s\n          </ul>' % li_dl(spec))
    if tr.get('buttons'):
        btns = '\n'.join(
            '            <a class="btn btn-%s" href="%s">%s</a>' % (attr(k), attr(_safe_href(h, '%s.try.buttons' % pid)), esc(l))
            for l, h, k in tr['buttons'])
        parts.append('          <div class="try-actions">\n%s\n          </div>' % btns)
    note = esc(tr['note'])
    if private:
        note = 'Questions: <a class="inline" href="mailto:product@cocoresearch.org">product@cocoresearch.org</a>'
    parts.append('          <p class="try-note">%s</p>' % note)
    try_body = '\n'.join(parts)

    # ---- part 05 ----
    facts = '\n'.join('          <div class="fact"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v)) for k, v in spec['status'])
    st = spec['stage']
    progress_markup = ''
    if 'progress' in spec:
        p = spec['progress']
        progress_markup = (
            '\n        <div class="stage-progress">\n'
            '          <div class="progress-meta"><span class="progress-count">%s</span></div>\n'
            '          <div class="progress-track" role="progressbar" aria-label="%s" aria-valuenow="%s" aria-valuemin="0" aria-valuemax="%s">\n'
            '            <div class="progress-fill" style="width: %s%%"></div>\n'
            '          </div>\n'
            '        </div>' % (esc(p['count']), attr(p['aria_label']), attr(str(p['now'])), attr(str(p['max'])), attr(str(p['pct']))))
    kns = '\n'.join(
        '          <div class="kn"><span class="kn-num">%s</span><span class="kn-lbl">%s</span></div>' % (esc(n), esc(l))
        for n, l in spec['kns'])
    specs_markup = ''
    if spec.get('specs'):
        rows = '\n'.join('          <tr><th>%s</th><td>%s</td></tr>' % (esc(k), esc(v)) for k, v in spec['specs'])
        specs_markup = '\n        <table class="spec-table">\n%s\n        </table>' % rows

    # ---- part 06 ----
    nxt = '\n'.join(
        '        <div class="next-item"><span class="cap-idx">%02d</span><div><h3>%s</h3><p>%s</p></div></div>' % (i, esc(t), esc(d))
        for i, (t, d) in enumerate(spec['next'], 1))

    # ---- part 07 ----
    links = list(spec.get('links', []))
    link_html = []
    for label, href in links:
        safe = _safe_href(href, '%s.links' % pid)
        extra = '' if safe.startswith('../') else ' rel="noopener"'
        link_html.append('        <a class="link-pill" href="%s"%s>%s</a>' % (attr(safe), extra, esc(label)))
    link_html.append('        <a class="link-pill" href="../products/">Browse all %d products</a>' % len(catalog))
    link_html.append('        <a class="link-pill" href="../whats-new/">What\u2019s new</a>')
    links_markup = '\n'.join(link_html)

    credits_sec = ''
    if spec.get('credits_html'):
        credits_sec = (
            '\n  <section id="credits" class="sec sec-credits" aria-label="Credits">\n'
            '    <div class="wrap">\n'
            '      <p class="credits-note">%s</p>\n'
            '    </div>\n'
            '  </section>' % render_desc_html(spec['credits_html'], '%s.credits_html' % pid))

    lic_li = '\n          <li><a href="%s">Licence</a></li>' % attr(
        _safe_href(spec['licence_href'], '%s.licence_href' % pid)) if spec.get('licence_href') else ''

    stage_badge = '<span class="p-badge" data-kind="stage" data-stage="%s">%s</span>' % (
        attr(stage_key(it)), esc(stage_chip_text(it)))
    lic_badge = '<span class="p-badge" data-kind="licence" data-open="%s">%s</span>' % (
        'true' if row['open_source'] else 'false', esc(row['licence_short']))
    head = head_html(title=page_title, desc=spec['meta_description'], slug=slug,
                     og_img=spec.get('og_image', DEFAULT_OG), og_alt=spec.get('og_image_alt', '%s \u2014 Coco Research' % row['name']),
                     robots=robots, jsonld=jsonld, three=True, product_id=pid, own_stage=bool(cats_stage))
    head += cats_script
    who_label = 'Who it\u2019s for'
    whats_next_label = 'What\u2019s next'
    does_title = 'What it does' if private else 'What it does today'
    does_sub = 'Private beta: nothing here is a public release.' if private else 'True of the code and releases available today.'
    return f"""{head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<a class="skip" href="?motion=off">View plain page (no motion)</a>
<div class="world" aria-hidden="true"><canvas id="world"></canvas><div class="hero-point"></div>{world_fallback_svg(pid, spec)}</div>
{nav_html(catalog, None, True)}
<main id="main" class="stage-main p-main">
  <section id="hero" class="hero p-hero" aria-labelledby="h-hero">
    <div class="wrap">{cats_banner}
      <div class="hero-col">
        <h1 id="h-hero" class="display">{name}</h1>
        <p class="p-for-you">{esc(row['for_you'])}</p>
        <div class="p-who"><span class="p-who-k">{who_label}</span><p>{esc(row['who_for'])}</p></div>
        <div class="p-try-above" aria-label="How to try it">
          <div class="cta-row">
          {act}{alt_html}
          </div>{note_html}
          <div class="p-badges" aria-label="Stage and licence">{stage_badge}{lic_badge}</div>
        </div>
      </div>
    </div>
  </section>
  <section id="for-you" class="sec p-part" data-part="01" aria-labelledby="h-p-01">
    <div class="wrap">
{part_head('01', 'Part one', 'What it does for you')}
      <p class="p-lead">{esc(spec['does_for_you'])}</p>
    </div>
  </section>
  <section id="who" class="sec p-part" data-part="02" aria-labelledby="h-p-02">
    <div class="wrap">
{part_head('02', 'Part two', who_label)}
      <p class="p-lead">{esc(row['who_for'])}</p>
      <p class="p-detail">{esc(spec['who_detail'])}</p>
    </div>
  </section>
  <section id="does" class="sec p-part" data-part="03" aria-labelledby="h-p-03">
    <div class="wrap">
{part_head('03', 'Part three', does_title, does_sub)}
      <div class="cap-grid">
{cap_items}
      </div>
    </div>
  </section>
  <section id="try" class="sec p-part" data-part="04" aria-labelledby="h-p-04">
    <div class="wrap">
{part_head('04', 'Part four', tr['heading'] if not private else 'Private, in the lab')}
      <div class="try-panel">
{try_body}
      </div>
    </div>
  </section>
  <section id="status" class="sec p-part" data-part="05" aria-labelledby="h-p-05">
    <div class="wrap">
{part_head('05', 'Part five', 'Status and licence')}
      <div class="stage-card">
        <span class="stage-badge stage-chip stage-chip-{attr(st['cls'])}" data-stage="{attr(st['cls'])}">{esc(st['chip'])}</span>{progress_markup}
        <dl class="facts-grid">
{facts}
        </dl>
        <div class="kns" aria-label="Key facts">
{kns}
        </div>{specs_markup}
      </div>
    </div>
  </section>
  <section id="next" class="sec p-part" data-part="06" aria-labelledby="h-p-06">
    <div class="wrap">
{part_head('06', 'Part six', whats_next_label, 'Honest next steps and limits. No dates are promised.')}
      <div class="next-list">
{nxt}
      </div>
    </div>
  </section>
  <section id="links" class="sec p-part" data-part="07" aria-labelledby="h-p-07">
    <div class="wrap">
{part_head('07', 'Part seven', 'Links')}
      <div class="links-row">
{links_markup}
      </div>
    </div>
  </section>{credits_sec}
</main>
{footer_html(data, lic_li)}
</body>
</html>
"""


# ---------------------------------------------------------------- /products/
def card_html(it):
    row, spec = it['row'], it['spec']
    nm = esc(row['name'])
    slug = attr(spec['slug'])
    if it['bucket'] == 'shipped':
        act = '<a class="btn btn-primary" href="../%s/">Try it<span class="sr-only"> %s</span> <span aria-hidden="true">\u2192</span></a>' % (slug, nm)
    else:
        act = '<a class="btn btn-ghost" href="../%s/">Read more<span class="sr-only"> about %s</span> <span aria-hidden="true">\u2192</span></a>' % (slug, nm)
    return (
        '        <article class="dir-card" data-product-card id="p-%s" data-group="%s" data-stage="%s">\n'
        '          <div class="dir-tags"><span class="stage-chip dir-stage" data-stage="%s"><span class="sh %s" aria-hidden="true"></span>%s</span>'
        '<span class="lic-chip" data-open="%s">%s</span></div>\n'
        '          <h2 class="dir-name">%s</h2>\n'
        '          <p class="dir-line">%s</p>\n'
        '          <p class="dir-meta">%s</p>\n'
        '          <div class="dir-act">%s</div>\n'
        '        </article>' % (
            attr(it['pid']), attr(it['group']), attr(it['group']), attr(stage_key(it)), attr(stage_shape(it)), esc(stage_label(it)),
            'true' if row['open_source'] else 'false', esc(row['licence_short']),
            nm, esc(row['for_you']), esc(short_status(it)), act))


def render_products(catalog, data):
    n = len(catalog)
    counts = {g: sum(1 for it in catalog if it['group'] == g) for g, *_ in GROUPS}
    tabs = [('all', 'All', n, '')] + [(g, t, counts[g], s) for g, t, s, _b in GROUPS]
    tab_html = '\n'.join(
        '      <button class="dir-tab" type="button" role="tab" id="tab-%s" data-filter="%s" aria-selected="%s" aria-controls="dir-grid" tabindex="%d">%s%s <span class="dir-tn">(%d)</span></button>'
        % (k, k, 'true' if i == 0 else 'false', 0 if i == 0 else -1,
           '<span class="sh %s" aria-hidden="true"></span>' % shape if shape else '', esc(label), cnt)
        for i, (k, label, cnt, shape) in enumerate(tabs))
    cards = '\n'.join(card_html(it) for it in catalog)
    desc = 'All %d Coco Research products and what each does for you: %s available now and %s in the lab.' % (
        n, _count_word(counts['products']), _count_word(counts['lab']))
    ld = collection_ld('Products \u2014 Coco Research', SITE + '/products/', desc, catalog)
    hero = dir_hero(
        eyebrow='Products', h1='What we make, and what it does for you',
        for_you='%s products in %s groups. %s you can use today, %s still in the lab, each with its stage stated plainly.' % (
            _count_word(n, cap=True), _count_word(len(GROUPS)), _count_word(counts['products'], cap=True), _count_word(counts['lab'])),
        who_k='How to read this',
        who='Products are available now: install or download them. In the lab is work in progress, from public early previews to private betas.',
        actions=['<a class="btn btn-primary" href="../coco/">Get Coco Super Intelligence</a>',
                 '<a class="btn btn-ghost" href="../voice/">Get Coco Voice</a>',
                 '<a class="btn btn-ghost" href="../lab/">See the lab</a>'],
        badges=[('released', 'Products \u00b7 %d' % counts['products']), ('lab', 'In the lab \u00b7 %d' % counts['lab'])])
    body = sec_open('directory', '01', 'All products', 'Pick one', 'Filter by group. Every card says what it does for you, its licence and whether you can use it today.') + f"""
      <div class="dir-tabs" data-filter-tabs role="tablist" aria-label="Filter products by group">
{tab_html}
      </div>
      <p class="dir-count" data-filter-count aria-live="polite">Showing {n} of {n} products \u00b7 All</p>
      <div class="dir-grid" id="dir-grid" role="tabpanel" aria-labelledby="tab-all" tabindex="0">
{cards}
      </div>
""" + SEC_CLOSE
    return stage_page('products', title='Products \u2014 Coco Research', desc=desc, jsonld=ld_script(ld), hero=hero, body=body, catalog=catalog, data=data)


# ---------------------------------------------------------------- /lab/
LAB_STAGE_KEY = STAGES


def render_lab(catalog, data):
    labs = [it for it in catalog if it['group'] == 'lab']
    pub = [it for it in labs if it['bucket'] == 'source']
    priv = [it for it in labs if it['bucket'] == 'lab']

    def cards(items):
        return '\n'.join(card_html(it) for it in items)

    desc = 'The %d projects Coco Research is working on, from public early previews and source tools to private betas. Each page says plainly what you can use today.' % len(labs)
    ld = collection_ld('In the lab \u2014 Coco Research', SITE + '/lab/', desc, labs)
    hero = dir_hero(
        eyebrow='In the lab', h1='What we are building next',
        for_you='%s projects in progress, from public early previews to private betas. Each one says what you can use today, and what you cannot.' % _count_word(len(labs), cap=True),
        who_k='What this is',
        who='The lab is where work lives before it is a product. Some of it has public code. Some of it is private and used daily by us.',
        actions=['<a class="btn btn-primary" href="../heliopause/">See Heliopause by Coco Research</a>',
                 '<a class="btn btn-ghost" href="../products/">All products</a>',
                 '<a class="btn btn-ghost" href="../whats-new/">What\u2019s new</a>'],
        badges=[('source', 'Public code \u00b7 %d' % len(pub)), ('lab', 'Private \u00b7 %d' % len(priv))])
    key = '\n'.join(
        '          <div class="fact"><dt data-stage="%s"><span class="sh %s" aria-hidden="true"></span>%s</dt><dd>%s</dd></div>'
        % (attr(skey), attr(shape), esc(label), esc(desc_text))
        for label, skey, shape, desc_text in LAB_STAGE_KEY
    )
    body = '\n'.join([
        sec_open('public-code', '01', 'Public code', 'Source you can read', 'Early previews and source tools. Each has a repository you can open today.'),
        '      <div class="dir-grid" role="list" aria-label="Lab projects with public code">',
        cards(pub), '      </div>', SEC_CLOSE,
        sec_open('private-work', '02', 'Private', 'Work that is not released', 'Built and used inside Coco Research. No public download, and no repository link here.'),
        '      <div class="dir-grid" role="list" aria-label="Private lab projects">',
        cards(priv), '      </div>', SEC_CLOSE,
        sec_open('stages', '03', 'Stages', 'How to read a stage', '%s labels, used the same way on every page.' % _count_word(len(LAB_STAGE_KEY), cap=True)),
        '      <dl class="facts-grid" aria-label="Stage key">', key, '      </dl>', SEC_CLOSE])
    return stage_page('lab', title='In the lab \u2014 Coco Research', desc=desc, jsonld=ld_script(ld), hero=hero, body=body, catalog=catalog, data=data)


# ---------------------------------------------------------------- /whats-new/
def render_whats_new(catalog, data, counts):
    releases = [it for it in catalog if it['row'].get('release_date')]
    if not releases:
        sys.exit('whats-new requires at least one dated release')
    releases.sort(key=lambda it: it['row']['release_date'], reverse=True)

    def chip_for(it):
        lic = it['row']['licence_short'].replace(' \u00b7 Open source', '')
        status = it['row'].get('status', '')
        if it['bucket'] == 'shipped':
            lead = 'Released'
        elif 'early preview' in status.lower():
            lead = 'Early preview'
        else:
            lead = 'Source available'
        return '%s \u00b7 %s' % (lead, lic)

    entries = []
    for it in releases:
        r = it['row']
        line = r['whats_new'].format(**counts)
        ver = r['release_version']
        shape = stage_shape(it)
        cls_key = stage_key(it)
        rel_url = _safe_href(r['release_url'], '%s.release_url' % it['pid'])
        entries.append(
            '        <article class="tl-entry">\n'
            '          <time class="tl-date" datetime="%s">%s</time>\n'
            '          <div class="tl-main">\n'
            '            <div class="tl-title-row">\n'
            '              <h3 class="tl-name">%s</h3>\n'
            '              <span class="tl-ver">%s</span>\n'
            '              <span class="stage-chip" data-stage="%s"><span class="sh %s" aria-hidden="true"></span>%s</span>\n'
            '            </div>\n'
            '            <p class="tl-line">%s</p>\n'
            '          </div>\n'
            '          <div class="tl-links">\n'
            '            <a class="btn btn-ghost btn-sm" href="../%s/">Product page<span class="sr-only"> for %s</span></a>\n'
            '            <a class="btn btn-primary btn-sm" href="%s">GitHub release<span class="sr-only"> %s %s</span></a>\n'
            '          </div>\n'
            '        </article>' % (attr(r['release_date']), human_date(r['release_date']), esc(r['name']), esc(ver), attr(cls_key), attr(shape),
                                    esc(chip_for(it)), esc(line), attr(it['spec']['slug']), esc(r['name']), attr(rel_url),
                                    esc(r['name']), esc(ver)))
    active = [it for it in catalog if it['bucket'] == 'source' and not it['row'].get('release_date')]
    active_rows = '\n'.join(
        '          <div class="active-row">\n'
        '            <h3 class="active-name"><a class="inline" href="../%s/">%s</a></h3>\n'
        '            <p>%s</p>\n'
        '            <span class="stage-chip" data-stage="%s"><span class="sh %s" aria-hidden="true"></span>%s</span>\n'
        '          </div>' % (attr(it['spec']['slug']), esc(it['row']['name']), esc(it['row']['for_you']),
                              attr(stage_key(it)), attr(stage_shape(it)), esc(stage_label(it)))
        for it in active)
    priv = [it for it in catalog if it['bucket'] == 'lab']
    priv_li = '\n'.join('              <li><a href="../%s/">%s</a></li>' % (attr(it['spec']['slug']), esc(it['row']['name'])) for it in priv)
    latest = releases[0]['row']
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': "What's new \u2014 Coco Research", 'url': SITE + '/whats-new/',
         'description': 'Latest tagged releases across Coco Research products: version, date, licence and one plain line on what shipped.',
         'isPartOf': {'@type': 'WebSite', 'name': 'Coco Research', 'url': SITE + '/'}},
        breadcrumb("What's new", SITE + '/whats-new/')]}
    desc = 'Latest tagged releases across Coco Research products: version, date, licence and one plain line on what shipped.'
    hero = dir_hero(
        eyebrow='Release log', h1="What's new",
        for_you='Every tagged release across Coco Research, newest first: version, date, licence and one plain line on what shipped.',
        who_k='Latest',
        who='%s %s, released %s.' % (latest['name'], latest['release_version'], human_date(latest['release_date'])),
        actions=['<a class="btn btn-primary" href="#releases">Read the release log</a>',
                 '<a class="btn btn-ghost" href="../lab/">In the lab</a>'],
        badges=[('released', '%d tagged releases' % len(releases)), ('lab', '%d projects in the lab' % sum(1 for it in catalog if it['group'] == 'lab'))])
    hero = (hero
            .replace('<div class="p-try-above" aria-label="Where to start">',
                     '<div class="p-try-above" role="group" aria-label="Where to start">')
            .replace('<div class="p-badges" aria-label="Groups">',
                     '<div class="p-badges" role="group" aria-label="Groups">'))
    body = f"""  <section id="releases" class="sec p-part wn-releases" data-part="01" aria-labelledby="h-rel">
    <div class="wrap">
      <div class="sec-head"><div><p class="eyebrow"><span class="p-part-num">01</span> Tagged public releases</p><h2 id="h-rel" class="sec-title">Newest first</h2></div><p class="sec-sub">Each entry links to the product page and its GitHub release.</p></div>
      <div class="timeline" role="group" aria-label="Latest tagged releases">
{chr(10).join(entries)}
      </div>
    </div>
  </section>
  <section id="also-active" class="sec p-part wn-also" data-part="02" aria-labelledby="h-also">
    <div class="wrap">
      <div class="sec-head"><div><p class="eyebrow"><span class="p-part-num">02</span> Also active</p><h2 id="h-also" class="sec-title">In the lab</h2></div><p class="sec-sub">Public source projects without a packaged release, and private lab work.</p></div>
      <div class="also-grid">
        <div class="active-table" role="group" aria-label="Source projects without a packaged release">
{active_rows}
        </div>
        <aside class="private-summary" aria-label="Private lab status">
          <span class="stage-chip" data-stage="lab"><span class="sh sh-dia" aria-hidden="true"></span>Private, in the lab</span>
          <h3>Not publicly released today</h3>
          <p>These projects are in private development inside Coco Research, with no public download and no announced release date.</p>
          <ul class="private-names">
{priv_li}
          </ul>
        </aside>
      </div>
    </div>
  </section>"""
    return stage_page('whats-new', title="What's new \u2014 Coco Research", desc=desc, jsonld=ld_script(ld), hero=hero, body=body, catalog=catalog, data=data)


# ---------------------------------------------------------------- SEO files
_ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def render_sitemap(catalog):
    dated = [d for it in catalog for d in (it['row'].get('release_date'),) if isinstance(d, str) and _ISO_DATE_RE.match(d)]
    latest = max(dated) if dated else None
    entries = [(SITE + '/', None), (SITE + '/products/', None), (SITE + '/lab/', None), (SITE + '/whats-new/', latest)]
    for it in catalog:
        if not it['spec'].get('noindex'):
            d = it['row'].get('release_date')
            entries.append(('%s/%s/' % (SITE, it['spec']['slug']), d if isinstance(d, str) and _ISO_DATE_RE.match(d) else None))
    entries += [(SITE + '/rijul-kalra/', None), (SITE + '/coco/guardrails/', None),
                (SITE + '/guides/manage-multiple-ai-coding-agents/', None)]
    body = '\n'.join(
        '  <url>\n    <loc>%s</loc>%s\n  </url>' % (esc(loc), '\n    <lastmod>%s</lastmod>' % esc(lm) if lm else '')
        for loc, lm in entries)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % body


def render_llms(catalog):
    def line(it):
        spec, row = it['spec'], it['row']
        facts = ' '.join('%s: %s%s' % (k, v, '' if v.endswith('.') else '.') for k, v in spec['status'][:3])
        return '- [%s](%s/%s/): %s %s' % (row['name'], SITE, spec['slug'], spec['does_for_you'], facts)
    products = '\n'.join(line(it) for it in catalog if it['group'] == 'products')
    lab = '\n'.join(
        '- [%s](%s/%s/): %s %s' % (it['row']['name'], SITE, it['spec']['slug'], it['row']['for_you'], short_status(it) + '.')
        for it in catalog if it['group'] == 'lab')
    n_lab = sum(1 for it in catalog if it['group'] == 'lab')
    return f"""# Coco Research

> Local-first AI tools and governed agents that run on your own machine, with every stage and licence stated plainly.

- Website: {SITE}/
- Founder: Rijul Kalra ({SITE}/rijul-kalra/)
- Contact: product@cocoresearch.org
- GitHub: https://github.com/coco-research
- All products: {SITE}/products/
- In the lab: {SITE}/lab/
- What's new: {SITE}/whats-new/

## Four Rules

1. Data stays local. Voice runs offline. Our tools run on your machine.
2. Verify, don't average. Dissent is named, not averaged away.
3. Stage is stated plainly. In development means in development.
4. Credit travels with the code. Open-source work we build on is named and linked.

## Products ({len(catalog) - n_lab}, available now)

{products}

## In the lab ({n_lab})

Work in progress: public early previews and source tools, then private projects with no public download.

{lab}

## Guides

- [How to add guardrails to an AI coding agent]({SITE}/coco/guardrails/): Five layers of guardrails for AI coding agents.
- [How to manage multiple AI coding agents]({SITE}/guides/manage-multiple-ai-coding-agents/): Practical coordination patterns for running multiple coding agents with git worktrees.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='exit 1 with a unified diff if any generated file is stale')
    parser.add_argument('--only', help='comma-separated product ids to write')
    parser.add_argument('--include-custom', action='store_true', help='also render the hand-built pages (%s)' % ', '.join(sorted(CUSTOM_PAGES)))
    parser.add_argument('--print-nav', metavar='CURRENT', help='print the shared top bar + drawer for a page folder (current: products|lab|whats-new|rijul|none)')
    args = parser.parse_args()
    data, catalog = load_catalog()
    if args.print_nav:
        cur = None if args.print_nav == 'none' else args.print_nav
        print(nav_html(catalog, cur, True))
        return
    if not (ROOT / 'assets' / 'vendor' / 'three' / 'three.module.min.js').is_file():
        sys.exit('vendored three.module.min.js is missing')
    counts = counts_ctx()
    only = set(args.only.split(',')) if args.only else None

    outputs = []  # (relative path, rendered text)
    for it in catalog:
        if only and it['pid'] not in only:
            continue
        if it['pid'] in CUSTOM_PAGES and not args.include_custom:
            continue
        outputs.append(('%s/index.html' % it['spec']['slug'], render_page(it, data)))
    if not only:
        outputs.append(('products/index.html', render_products(catalog, data)))
        outputs.append(('lab/index.html', render_lab(catalog, data)))
        outputs.append(('whats-new/index.html', render_whats_new(catalog, data, counts)))
        outputs.append(('sitemap.xml', render_sitemap(catalog)))
        outputs.append(('llms.txt', render_llms(catalog)))

    stale = False
    for rel, rendered in outputs:
        target = ROOT / rel
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
