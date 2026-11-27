"""Shared constants, helpers, JSON-LD builders and page chrome for render-product-pages.py."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
DATA = ROOT / 'data' / 'products.json'
SPEC_PUBLIC = ROOT / 'data' / 'product-pages-public.json'
SPEC_LAB = ROOT / 'data' / 'product-pages-lab.json'
ANCHOR = re.compile(r'<a class="inline" href="([^"]*)" rel="noopener">([^<]*)</a>')

DIAGRAMS = {
    'editions': '<rect x="34" y="28" width="96" height="84" rx="4"/><rect x="112" y="20" width="96" height="84" rx="4"/><rect x="190" y="36" width="96" height="84" rx="4"/><line x1="34" y1="56" x2="286" y2="56" stroke-opacity=".35"/><circle cx="160" cy="62" r="5" fill="currentColor"/>',
    'frames': '<rect x="52" y="16" width="56" height="108" rx="6" stroke-opacity=".45"/><rect x="132" y="16" width="56" height="108" rx="6"/><rect x="212" y="16" width="56" height="108" rx="6" stroke-opacity=".45"/><path d="M24 72 Q92 26 160 72 T296 72"/><path d="M24 72 Q92 118 160 72 T296 72" stroke-opacity=".5"/>',
    'ripple': '<circle cx="76" cy="70" r="14"/><circle cx="76" cy="70" r="30" stroke-opacity=".6"/><circle cx="76" cy="70" r="48" stroke-opacity=".32"/><rect x="156" y="24" width="132" height="92" rx="7"/><line x1="156" y1="44" x2="288" y2="44" stroke-opacity=".45"/><circle cx="222" cy="76" r="5" fill="currentColor"/>',
    'heliosphere': '<path d="M214 14 Q292 70 214 126"/><path d="M194 26 Q256 70 194 114" stroke-opacity=".45"/><ellipse cx="128" cy="70" rx="74" ry="28" stroke-opacity=".5"/><ellipse cx="128" cy="70" rx="44" ry="16"/><circle cx="128" cy="70" r="6" fill="currentColor"/>',
    'vault': '<polygon points="160,18 208,44 208,96 160,122 112,96 112,44"/><line x1="160" y1="18" x2="160" y2="122" stroke-opacity=".4"/><line x1="112" y1="44" x2="208" y2="96" stroke-opacity=".4"/><line x1="208" y1="44" x2="112" y2="96" stroke-opacity=".4"/><circle cx="48" cy="42" r="6"/><circle cx="272" cy="42" r="6"/><circle cx="48" cy="98" r="6"/><circle cx="272" cy="98" r="6"/><line x1="54" y1="44" x2="112" y2="58" stroke-opacity=".45"/><line x1="266" y1="44" x2="208" y2="58" stroke-opacity=".45"/>',
    'folios': '<rect x="54" y="26" width="180" height="88" rx="4" stroke-opacity=".35"/><rect x="70" y="20" width="180" height="88" rx="4" stroke-opacity=".6"/><rect x="86" y="14" width="180" height="88" rx="4"/><rect x="112" y="46" width="118" height="18" rx="3" fill="currentColor" fill-opacity=".18"/><line x1="32" y1="112" x2="288" y2="28"/>',
    'council': '<ellipse cx="160" cy="74" rx="54" ry="20"/><ellipse cx="160" cy="74" rx="112" ry="44" stroke-opacity=".4"/><circle cx="160" cy="30" r="6" fill="currentColor"/><circle cx="254" cy="52" r="5"/><circle cx="254" cy="96" r="5"/><circle cx="160" cy="118" r="5"/><circle cx="66" cy="96" r="5"/><circle cx="66" cy="52" r="5"/>',
    'router': '<line x1="160" y1="16" x2="160" y2="124"/><circle cx="160" cy="44" r="4" fill="currentColor"/><circle cx="160" cy="70" r="4" fill="currentColor"/><circle cx="160" cy="96" r="4" fill="currentColor"/><circle cx="54" cy="38" r="8"/><circle cx="54" cy="102" r="8"/><circle cx="266" cy="38" r="8"/><circle cx="266" cy="102" r="8"/><path d="M62 38 Q160 20 258 38" stroke-opacity=".55"/><path d="M258 102 Q160 120 62 102" stroke-opacity=".55"/>',
}

WORLD_FALLBACK_MOTIFS = {
    'coco-si': '<g stroke="currentColor" stroke-width="1.4" fill="none"><path d="M650 220 Q790 230 930 370" stroke-opacity=".45"/><path d="M630 300 Q780 306 930 370" stroke-opacity=".4"/><path d="M645 370 L930 370" stroke-opacity=".55"/><path d="M630 440 Q780 434 930 370" stroke-opacity=".4"/><path d="M650 520 Q790 510 930 370" stroke-opacity=".45"/><circle cx="930" cy="370" r="56" stroke-opacity=".38"/><circle cx="930" cy="370" r="24" stroke-opacity=".65"/></g><g fill="currentColor"><circle cx="650" cy="220" r="5"/><circle cx="630" cy="300" r="5"/><circle cx="645" cy="370" r="6"/><circle cx="630" cy="440" r="5"/><circle cx="650" cy="520" r="5"/><circle cx="930" cy="370" r="8"/></g>',
    'voice': '<g fill="currentColor" fill-opacity=".45"><rect x="650" y="330" width="8" height="80" rx="4"/><rect x="676" y="295" width="8" height="150" rx="4"/><rect x="702" y="265" width="8" height="210" rx="4"/><rect x="728" y="310" width="8" height="120" rx="4"/><rect x="754" y="230" width="8" height="280" rx="4" fill-opacity=".7"/><rect x="780" y="280" width="8" height="180" rx="4"/><rect x="806" y="205" width="8" height="330" rx="4" fill-opacity=".85"/><rect x="832" y="260" width="8" height="220" rx="4"/><rect x="858" y="220" width="8" height="300" rx="4" fill-opacity=".75"/><rect x="884" y="285" width="8" height="170" rx="4"/><rect x="910" y="315" width="8" height="110" rx="4"/><rect x="936" y="340" width="8" height="60" rx="4"/></g>',
}

THREE_URL = '../assets/vendor/three/three.module.min.js'
SITE = 'https://cocoresearch.org'
DEFAULT_OG = SITE + '/assets/img/og-coco-research.png'

# (group key, menu title, shape class, products.json bucket)
GROUPS = [
    ('products', 'Products', 'sh-dot', 'products'),
    ('lab', 'In the lab', 'sh-sq', 'lab'),
]
# Pages that are hand-built (not generated). The generator never overwrites them; the tests still hold them to the shared contract.
CUSTOM_PAGES = {'m0'}
NAV_NAMES = {'heliopause': 'Heliopause'}  # menu text only; pages and cards keep "Heliopause by Coco Research"
SLOT_ICON = (
    '<svg class="cap-slot-icon" viewBox="0 0 36 28" fill="none" aria-hidden="true">'
    '<rect x="1.5" y="1.5" width="33" height="25" rx="3" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M9 19l5-6 4 4 3-3 6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
STAGE_PAGES = {
    'products': dict(current='products', motif='products', fallback='editions'),
    'lab': dict(current='lab', motif='lab', fallback='router'),
    'whats-new': dict(current='whats-new', motif='whats-new', fallback='frames'),
}
SEC_CLOSE = '    </div>\n  </section>'


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


def world_fallback_svg(pid, spec):
    if pid in WORLD_FALLBACK_MOTIFS:
        body = WORLD_FALLBACK_MOTIFS[pid]
    else:
        inner = DIAGRAMS[spec['diagram']]
        body = '<g transform="translate(610 250) scale(1.25)" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" stroke-opacity=".55">%s</g>' % inner
    return (
        '<svg class="world-svg-fallback" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" focusable="false">'
        '<circle cx="840" cy="370" r="190" fill="none" stroke="currentColor" stroke-width="1" stroke-opacity=".14" stroke-dasharray="5 8"/>'
        '<line x1="600" y1="370" x2="1080" y2="370" stroke="currentColor" stroke-width="1" stroke-opacity=".12"/>'
        '%s</svg>' % body
    )


def build_jsonld(pid, stage, row, spec):
    if stage not in ('shipped', 'source'):
        return ''
    slug = spec['slug']
    url = 'https://cocoresearch.org/%s/' % slug
    raw_plain = re.sub(r'<[^>]+>', '', row.get('description_html', row.get('description', ''))).strip()
    desc = spec.get('meta_description', raw_plain)
    org = {
        '@type': 'Organization',
        'name': 'Coco Research',
        'url': 'https://cocoresearch.org/',
    }
    crumb = {
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': 1,
                'name': 'Coco Research',
                'item': 'https://cocoresearch.org/',
            },
            {
                '@type': 'ListItem',
                'position': 2,
                'name': row['name'],
                'item': url,
            },
        ],
    }
    if stage == 'shipped':
        entity = {
            '@type': 'SoftwareApplication',
            'name': row['name'],
            'description': desc,
            'url': url,
            'applicationCategory': spec.get('app_category', 'DeveloperApplication'),
            'softwareVersion': spec.get('version', ''),
            'license': spec.get('license_url', spec.get('licence_href', '')),
            'codeRepository': spec.get('code_repository', ''),
            'author': org,
            'publisher': org,
            'offers': {
                '@type': 'Offer',
                'price': '0',
                'priceCurrency': 'USD',
            },
        }
        if spec.get('os'):
            entity['operatingSystem'] = spec['os']
    else:
        entity = {
            '@type': 'SoftwareSourceCode',
            'name': row['name'],
            'description': desc,
            'url': url,
            'codeRepository': spec.get('code_repository', row.get('href', '')),
            'license': spec.get('license_url', spec.get('licence_href', '')),
            'programmingLanguage': spec.get('programming_language', 'Python'),
            'author': org,
        }
        if spec.get('version'):
            entity['version'] = spec['version']
    payload = {
        '@context': 'https://schema.org',
        '@graph': [entity, crumb],
    }
    return ld_script(payload)


def ld_script(payload):
    dumped = json.dumps(payload, indent=2, ensure_ascii=False).replace('<', '\\u003c')
    return '\n<script type="application/ld+json">\n%s\n</script>' % dumped


def breadcrumb(name, url):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Coco Research', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': name, 'item': url}]}


def collection_ld(name, url, desc, items):
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': name, 'url': url, 'description': desc,
         'isPartOf': {'@type': 'WebSite', 'name': 'Coco Research', 'url': SITE + '/'},
         'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items),
                        'itemListElement': [
                            {'@type': 'ListItem', 'position': i, 'name': it['row']['name'], 'url': '%s/%s/' % (SITE, it['spec']['slug'])}
                            for i, it in enumerate(items, 1)]}},
        breadcrumb(name.split(' \u2014 ')[0], url)]}


def human_date(iso):
    y, m, d = iso.split('-')
    return '%d %s %s' % (int(d), MONTHS[int(m) - 1], y)


def build_catalog(data, pub_specs, lab_specs):
    """Return one record per product page (10), in menu order: Products first, then In the lab.

    bucket is the page kind: shipped (Products group), source (a lab project with public code),
    lab (a private lab project). The directory only ever shows two groups.
    """
    items = []
    for group, _title, _shape, key in GROUPS:
        for row in data[key]:
            pid = row['id']
            spec = pub_specs.get(pid) or lab_specs['lab'].get(pid)
            if spec is None:
                sys.exit('missing page spec for %s' % pid)
            if group == 'products':
                bucket = 'shipped'
            else:
                bucket = 'source' if 'href' in row else 'lab'
            items.append(dict(pid=pid, group=group, bucket=bucket, row=row, spec=spec, private=bucket == 'lab'))
    return items


def load_catalog():
    data = json.loads(DATA.read_text())
    pub_specs = json.loads(SPEC_PUBLIC.read_text())
    lab_specs = json.loads(SPEC_LAB.read_text())
    catalog = build_catalog(data, pub_specs, lab_specs)
    for it in catalog:
        it['catalog'] = catalog
    return data, catalog


def counts_ctx():
    c = json.loads((ROOT / 'docs' / 'released-counts.json').read_text())
    return {'personas': c['personas']['total'], 'departments': c['departments']['total'],
            'skills': c['skills']['total'], 'commands': c['commands']['customer_facing'],
            'agents': c['agents']['total']}


def stage_chip_text(it):
    row = it['row']
    if it['bucket'] == 'shipped':
        m = re.search(r'\bv\d+\.\d+\.\d+', row['tag'])
        return 'Available now' + (' \u00b7 %s' % m.group(0) if m else '')
    if it['bucket'] == 'source':
        return 'Archived' if 'archived' in row.get('status', '').lower() else 'Source available'
    return 'In the lab'


def stage_label(it):
    """Short fact label for directory cards (/products/, /lab/): what you can actually do today."""
    row, bucket = it['row'], it['bucket']
    if bucket == 'shipped':
        return stage_chip_text(it)
    status = row['status'].lower()
    if status == 'private, in the lab':
        return 'Private, in the lab'
    if bucket == 'source':
        for key, label in (('early preview', 'Early preview'), ('archived', 'Archived'), ('pre-alpha', 'Pre-alpha')):
            if key in status:
                return label
        return 'Source available'
    return row['status'].split(',')[0]


def stage_shape(it):
    return {'shipped': 'sh-dot', 'source': 'sh-ring', 'lab': 'sh-sq'}[it['bucket']]


def stage_key(it):
    return {'shipped': 'released', 'source': 'source', 'lab': 'beta' if it['spec']['stage']['cls'] == 'beta' else 'lab'}[it['bucket']]


def short_status(it):
    row = it['row']
    return row['tag'] if it['bucket'] == 'shipped' else row['status']


# ---------------------------------------------------------------- shared chrome
def menu_group_html(catalog, indent, prefix):
    """The two menu / drawer groups: Products (2) and In the lab (8). Every row is a link."""
    pad = ' ' * indent
    cols = []
    for group, title, shape, _b in GROUPS:
        lis = []
        members = [it for it in catalog if it['group'] == group]
        for it in members:
            nm = esc(NAV_NAMES.get(it['pid'], it['row']['name']))
            line = esc(it['row']['for_you'])
            badge = '<span class="sn-m-badge">Archived</span>' if 'archived' in it['row'].get('status', '').lower() else ''
            priv = ''
            if it['row'].get('status') == 'Private, in the lab':
                priv = '<span class="sn-m-priv"><span class="sh sh-sq" aria-hidden="true"></span>Private, in the lab</span>'
            lis.append(
                '%s    <li><a class="sn-m-item" href="%s%s/"><span class="sn-m-name">%s%s</span><span class="sn-m-line">%s</span>%s</a></li>'
                % (pad, prefix, it['spec']['slug'], nm, badge, line, priv))
        cols.append(
            '%s<div class="sn-m-group" data-group="%s">\n'
            '%s  <h3 class="sn-m-h g-%s"><span class="sh %s" aria-hidden="true"></span>%s<span class="sn-m-n">%d</span></h3>\n'
            '%s  <ul aria-label="%s">\n%s\n%s  </ul>\n%s</div>'
            % (pad, group, pad, group, shape, esc(title), len(members), pad, attr(title), '\n'.join(lis), pad, pad))
    return '\n'.join(cols)


def nav_html(catalog, current, three, prefix='../', home=False):
    """The one shared top bar + phone drawer. current: products | lab | whats-new | rijul | None.

    prefix is the path back to the site root ('../' from a page folder, './' from the home page).
    home=True is the locked-dark home page: no theme toggle, the 3D chip starts hidden until main.js wires it.
    """
    cur = lambda key: ' aria-current="page"' if current == key else ''
    if home:
        motion, motion_drawer = '\n    <button class="sn-chip" type="button" data-motion-toggle hidden>Pause 3D</button>', '\n      <button class="sn-chip" type="button" data-motion-toggle hidden>Pause 3D</button>'
        theme = theme_drawer = ''
    else:
        motion = '\n    <button class="sn-chip" type="button" data-motion-toggle>Pause 3D</button>' if three else ''
        motion_drawer = ''
        theme = '\n    <button class="sn-chip" type="button" data-theme-toggle>Dark</button>'
        theme_drawer = '<button class="sn-chip" type="button" data-theme-toggle>Dark</button>'
    n = len(catalog)
    menu = menu_group_html(catalog, 6, prefix)
    drawer = menu_group_html(catalog, 4, prefix)
    brand_drawer = ('<span class="sn-brand" id="sn-drawer-title"><i aria-hidden="true"></i><span>Coco Research</span></span>' if home else
                    '<a class="sn-brand" href="%s"><i aria-hidden="true"></i><span>Coco Research</span></a>\n    <h2 class="sr-only" id="sn-drawer-title">Site menu</h2>' % prefix)
    return f"""<header class="site-nav" data-site-nav>
  <a class="sn-brand" href="{prefix}"><i aria-hidden="true"></i><span>Coco Research</span></a>
  <nav class="sn-links" aria-label="Primary">
    <button class="sn-tab" type="button" data-products-trigger aria-expanded="false" aria-controls="site-products-menu"{cur('products')}>Products <span class="sn-caret" aria-hidden="true">\u25be</span></button>
    <a class="sn-tab" href="{prefix}lab/"{cur('lab')}>In the lab</a>
    <a class="sn-tab" href="{prefix}whats-new/"{cur('whats-new')}>What's new</a>
    <a class="sn-tab" href="{prefix}rijul-kalra/"{cur('rijul')}>Rijul Kalra</a>
  </nav>
  <div class="sn-right">{theme}{motion}
    <a class="sn-cta" href="{prefix}coco/">Get Coco</a>
    <button class="sn-menu-btn" type="button" data-drawer-open aria-expanded="false" aria-controls="site-mobile-drawer" aria-label="Open menu">Menu</button>
  </div>
  <div class="sn-menu" id="site-products-menu" data-products-menu hidden>
    <div class="sn-m-grid">
{menu}
    </div>
    <div class="sn-m-foot"><a href="{prefix}products/">Browse all {n} products \u2192</a><a href="{prefix}lab/">In the lab \u2192</a><a href="{prefix}whats-new/">What's new \u2192</a></div>
  </div>
</header>
<dialog class="sn-drawer" id="site-mobile-drawer" data-mobile-drawer aria-labelledby="sn-drawer-title">
  <div class="sn-d-head">
    {brand_drawer}
    <button class="sn-chip" type="button" data-drawer-close>Close</button>
  </div>
  <div class="sn-d-body">
    <p class="sn-d-label">Products</p>
    <div class="sn-m-grid">
{drawer}
    </div>
    <a class="sn-m-item sn-d-all" href="{prefix}products/"><span class="sn-m-name">Browse all {n} products \u2192</span></a>
    <div class="sn-d-top">
      <a href="{prefix}lab/"{cur('lab')}>In the lab \u2192</a>
      <a href="{prefix}whats-new/"{cur('whats-new')}>What's new \u2192</a>
      <a href="{prefix}rijul-kalra/"{cur('rijul')}>Rijul Kalra \u2192</a>
    </div>
    <div class="sn-d-foot">{motion_drawer}{theme_drawer}<a class="sn-cta" href="{prefix}coco/">Get Coco</a></div>
  </div>
</dialog>"""


def footer_html(data, lic_li):
    def foot_list(group):
        return '\n'.join(
            '          <li><a href="../%s">%s</a>%s</li>'
            % (attr(r['page']), esc(r['name']), ' <span class="sn-badge">Archived</span>' if 'archived' in r.get('status', '').lower() else '')
            for r in data[group])
    return f"""<footer class="foot">
  <div class="foot-inner">
    <div class="foot-brand">
      <a class="brand" href="../"><i aria-hidden="true"></i><span>Coco Research</span></a>
      <p>Governed AI, built in the open. Built by <a class="inline" href="../rijul-kalra/">Rijul Kalra</a>.</p>
      <p>product@cocoresearch.org \u00b7 <a class="inline" href="mailto:product@cocoresearch.org">Email</a></p>
    </div>
    <nav class="foot-cols" aria-label="Footer">
      <div><h2>Products</h2><ul>
{foot_list('products')}
      </ul></div>
      <div><h2>In the lab</h2><ul>
{foot_list('lab')}
      </ul></div>
      <div><h2>Company</h2><ul>
          <li><a href="../products/">All products</a></li>
          <li><a href="../lab/">In the lab</a></li>
          <li><a href="../whats-new/">What's new</a></li>
          <li><a href="../rijul-kalra/">Rijul Kalra</a></li>
          <li><a href="../guides/manage-multiple-ai-coding-agents/">Guides</a></li>
          <li><a href="https://github.com/coco-research/coco/releases">Coco changelog</a></li>
      </ul></div>
      <div><h2>Code</h2><ul>
          <li><a href="https://github.com/coco-research">GitHub</a></li>
          <li><a href="https://www.npmjs.com/package/cocosuperintelligence">npm</a></li>{lic_li}
      </ul></div>
    </nav>
  </div>
  <div class="foot-base">
    <p>\u00a9 2026 Coco Research</p>
  </div>
</footer>"""


def head_html(*, title, desc, slug, og_img, og_alt, robots, jsonld, three, product_id=None, own_stage=False):
    t_attr, d_attr = attr(title), attr(desc)
    motion_js = (
        "  try { off = sessionStorage.getItem('coco-3d-pause:' + location.pathname) === '1'; } catch (e) {}\n"
        "  if (/[?&]motion=off/.test(location.search)) off = true;\n"
    ) if three else ''
    cls = "' js' + (rm || off ? ' still' : ' cine') + (rm ? ' os-reduced' : '')" if three else "' js'"
    three_links = (
        '<link rel="modulepreload" href="%s">\n' % THREE_URL
    ) if three else ''
    three_tail = (
        '<script type="importmap">\n{ "imports": { "three": "%s" } }\n</script>\n'
        '<script type="module" src="../assets/js/site-nav.js"></script>\n'
        '<script type="module" src="../assets/js/product-scene.js"></script>' % THREE_URL
    ) if three else '<script type="module" src="../assets/js/site-nav.js"></script>'
    return f"""<!doctype html>
<html lang="en"{' data-product="%s"' % attr(product_id) if product_id else ''}{' data-own-stage' if own_stage else ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">{robots}
<title>{esc(title)}</title>
<meta name="description" content="{d_attr}">
<meta name="theme-color" content="#03050b">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:title" content="{t_attr}">
<meta property="og:description" content="{d_attr}">
<meta property="og:url" content="{SITE}/{slug}/">
<meta property="og:image" content="{attr(og_img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{attr(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t_attr}">
<meta name="twitter:description" content="{d_attr}">
<meta name="twitter:image" content="{attr(og_img)}">
<link rel="canonical" href="{SITE}/{slug}/">
<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/site/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/assets/site/site.webmanifest">{jsonld}
<script>
(function () {{
  var d = document.documentElement, rm = false, off = false, th = '';
  try {{ rm = matchMedia('(prefers-reduced-motion: reduce)').matches; }} catch (e) {{}}
{motion_js}  try {{ th = localStorage.getItem('coco-theme') || ''; }} catch (e) {{}}
  var m = /[?&]theme=(light|dark)/.exec(location.search);
  if (m) th = m[1];
  if (th === 'light' || th === 'dark') d.setAttribute('data-theme', th);
  d.className += {cls};
}})();
</script>
<link rel="preload" as="font" type="font/woff2" crossorigin href="../assets/vendor/fonts/archivo-latin-wdth-normal.woff2">
{three_links}<link rel="stylesheet" href="../assets/css/site-nav.css">
<link rel="stylesheet" href="../assets/css/product.css">
{three_tail}"""


def li_dl(spec):
    out = []
    for name, note in spec['try'].get('downloads', []):
        out.append('            <li><code>%s</code><span>%s</span></li>' % (esc(name), esc(note)))
    return '\n'.join(out)


def copy_box(label, cmd):
    return (
        '<div class="install-box try-box" aria-label="%s">\n'
        '            <code class="install-cmd">%s</code>\n'
        '            <button class="copy-btn" type="button" data-copy="%s">Copy</button>\n'
        '            <span class="copy-status" data-copy-status aria-live="polite"></span>\n'
        '          </div>' % (attr(label), esc(cmd), attr(cmd)))


def part_head(num, eyebrow, title, sub=''):
    sub_html = '\n        <p class="sec-sub">%s</p>' % esc(sub) if sub else ''
    return (
        '      <div class="sec-head">\n'
        '        <div><p class="eyebrow"><span class="p-part-num">%s</span> %s</p><h2 id="h-p-%s" class="sec-title">%s</h2></div>%s\n'
        '      </div>' % (num, esc(eyebrow), num, esc(title), sub_html))


def stage_page(slug, *, title, desc, jsonld, hero, body, catalog, data):
    cfg = STAGE_PAGES[slug]
    head = head_html(title=title, desc=desc, slug=slug, og_img=DEFAULT_OG, og_alt=title, robots='',
                     jsonld=jsonld, three=True, product_id=cfg['motif'])
    return f"""{head}
</head>
<body data-page="{slug}">
<a class="skip" href="#main">Skip to content</a>
<a class="skip" href="?motion=off">View plain page (no motion)</a>
<div class="world" aria-hidden="true"><canvas id="world"></canvas><div class="hero-point"></div>{world_fallback_svg(cfg['motif'], {'diagram': cfg['fallback']})}</div>
{nav_html(catalog, cfg['current'], True)}
<main id="main" class="stage-main p-main" data-page-main="{slug}">
{hero}
{body}
</main>
{footer_html(data, '')}
</body>
</html>
"""


def dir_hero(*, eyebrow, h1, for_you, who_k, who, actions, badges):
    acts = '\n            '.join(actions)
    chips = ''.join('<span class="p-badge" data-kind="stage" data-stage="%s">%s</span>' % (attr(k), esc(t)) for k, t in badges)
    return f"""  <section id="hero" class="hero p-hero dir-hero" aria-labelledby="h-hero">
    <div class="wrap">
      <div class="hero-col">
        <p class="eyebrow">{esc(eyebrow)}</p>
        <h1 id="h-hero" class="display">{h1}</h1>
        <p class="p-for-you">{esc(for_you)}</p>
        <div class="p-who"><span class="p-who-k">{esc(who_k)}</span><p>{esc(who)}</p></div>
        <div class="p-try-above" aria-label="Where to start">
          <div class="cta-row">
            {acts}
          </div>
          <div class="p-badges" aria-label="Groups">{chips}</div>
        </div>
      </div>
    </div>
  </section>"""


def sec_open(sec_id, num, eyebrow, title, sub=''):
    sub_html = '\n        <p class="sec-sub">%s</p>' % esc(sub) if sub else ''
    return (
        '  <section id="%s" class="sec p-part" data-part="%s" aria-labelledby="h-%s">\n'
        '    <div class="wrap">\n'
        '      <div class="sec-head">\n'
        '        <div><p class="eyebrow"><span class="p-part-num">%s</span> %s</p><h2 id="h-%s" class="sec-title">%s</h2></div>%s\n'
        '      </div>' % (sec_id, num, sec_id, num, esc(eyebrow), sec_id, esc(title), sub_html))
