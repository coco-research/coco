#!/usr/bin/env python3
"""Rewrite the homepage product regions from data/products.json.

Run from the repo root. Default mode writes index.html. --check exits 1
and prints a unified diff when index.html differs from the render.
"""
import argparse
import difflib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
INDEX = ROOT / 'index.html'
M0 = ROOT / 'm0' / 'index.html'
DATA = ROOT / 'data' / 'products.json'
ANCHOR = re.compile(r'<a class="inline" href="([^"]*)" rel="noopener">([^<]*)</a>')
ID_OK = re.compile(r'[a-z0-9-]+')
PAGE_OK = re.compile(r'[a-z0-9-]+/')


def require_page(row):
    pid = row['id']
    page = row.get('page', '')
    expected = 'coco/' if pid == 'coco-si' else '%s/' % pid
    if not PAGE_OK.fullmatch(page) or page != expected:
        sys.exit('%s: page must be %s' % (pid, expected))
    return page


def esc_text(value):
    return html.escape(value, quote=False)


def esc_attr(value):
    return html.escape(value, quote=True)


def render_description_html(raw, where):
    """Escape text. Keep only <a class="inline" href rel="noopener"> links."""
    out = []
    pos = 0
    for match in ANCHOR.finditer(raw):
        before = raw[pos:match.start()]
        if '<' in before or '>' in before:
            sys.exit(f'{where}: description_html has a disallowed tag')
        out.append(esc_text(before))
        href = match.group(1)
        if '<' in href or '>' in href or not href.startswith('https://'):
            sys.exit(f'{where}: description_html href must be a plain https:// URL')
        out.append(
            '<a class="inline" href="%s" rel="noopener">%s</a>'
            % (esc_attr(href), esc_text(match.group(2)))
        )
        pos = match.end()
    rest = raw[pos:]
    if '<' in rest or '>' in rest:
        sys.exit(f'{where}: description_html has a disallowed tag')
    out.append(esc_text(rest))
    return ''.join(out)


def art_lines(product):
    expected = 'assets/site/art/%s.svg' % product['id']
    art = product['art']
    if art != expected or '..' in art.split('/'):
        sys.exit('%s: art must be %s' % (product['id'], expected))
    path = ROOT / art
    if not path.is_file():
        sys.exit('%s: missing art file %s' % (product['id'], art))
    raw = path.read_text()
    if not raw.lstrip().startswith('<svg') or '</svg>' not in raw:
        sys.exit('%s: %s is not an svg element' % (product['id'], art))
    return ['            ' + line if line else '' for line in raw.splitlines()]


def render_card(product):
    pid = product['id']
    if not ID_OK.fullmatch(pid):
        sys.exit('bad product id %r' % pid)
    lines = [
        '        <article class="card card-%s" aria-labelledby="t-%s">' % (pid, pid),
        '          <div class="card-art" aria-hidden="true">',
    ]
    lines.extend(art_lines(product))
    page = require_page(product)
    lines.extend([
        '          </div>',
        '          <div class="card-body">',
        '            <h3 id="t-%s"><a class="card-link" href="%s">%s</a></h3>' % (pid, esc_attr(page), esc_text(product['name'])),
        '            <p class="tag">%s</p>' % esc_text(product['tag']),
        '            <p>%s</p>' % render_description_html(product['description_html'], pid),
        '            <div class="card-actions">',
        '              <a class="btn btn-ghost btn-sm" href="%s">Product page<span class="sr-only"> for %s</span></a>' % (esc_attr(page), esc_text(product['name'])),
    ])
    actions = product['actions']
    if not actions:
        sys.exit('%s: needs at least one action' % pid)
    for action in actions:
        kind = action['kind']
        if kind not in ('primary', 'ghost'):
            sys.exit('%s: action kind must be primary or ghost' % pid)
        href = action['href']
        is_rel = href.startswith('/') and not href.startswith('//') and '..' not in href.split('/')
        if '<' in href or '>' in href or not (href.startswith('https://') or is_rel):
            sys.exit('%s: action href must be https:// or a root-relative path' % pid)
        lines.append(
            '              <a class="btn btn-%s btn-sm" href="%s">%s<span class="sr-only">%s</span></a>'
            % (kind, esc_attr(action['href']), esc_text(action['label']), esc_text(action['sr']))
        )
    lines.extend([
        '            </div>',
        '          </div>',
        '        </article>',
    ])
    return lines


def check_ids(data):
    if sorted(data) != ['lab', 'products']:
        sys.exit('data/products.json must hold exactly two groups: products and lab (got %s)' % ', '.join(sorted(data)))
    seen = set()
    for group in ('products', 'lab'):
        for row in data[group]:
            pid = row['id']
            if not ID_OK.fullmatch(pid):
                sys.exit('bad product id %r' % pid)
            if pid in seen:
                sys.exit('duplicate product id %s' % pid)
            seen.add(pid)


def require_https(href, where):
    if '<' in href or '>' in href or not href.startswith('https://'):
        sys.exit('%s: href must be a plain https:// URL' % where)


def render_deck(data):
    lines = []
    for index, product in enumerate(data['products']):
        if index:
            lines.append('')
        lines.extend(render_card(product))
    return lines


def render_lab_row(row):
    if 'href' in row:
        require_https(row['href'], row['id'])
    page = require_page(row)
    name = '<a class="inline" href="%s">%s</a>' % (esc_attr(page), esc_text(row['name']))
    badge = ' <span class="sn-badge">Archived</span>' if 'archived' in row.get('status', '').lower() else ''
    return (
        '            <li class="lab-item"><h4>%s%s</h4><p>%s<span class="tag">%s</span></p></li>'
        % (name, badge, esc_text(row['description']), esc_text(row['status']))
    )


def render_lab(data):
    lines = ['          <ul>']
    lines.extend(render_lab_row(row) for row in data['lab'])
    lines.append('          </ul>')
    return lines


def render_foot(data, group):
    return [
        '          <li><a href="%s">%s</a>%s</li>'
        % (esc_attr(require_page(row)), esc_text(row['name']),
           ' <span class="sn-badge">Archived</span>' if 'archived' in row.get('status', '').lower() else '')
        for row in data[group]
    ]


def replace_region(text, name, inner, where='index.html'):
    start = '<!-- products:%s:start -->' % name
    end = '<!-- products:%s:end -->' % name
    lines = text.splitlines(keepends=True)
    start_at = end_at = None
    for index, line in enumerate(lines):
        if start in line and start_at is None:
            start_at = index
        elif end in line and start_at is not None:
            end_at = index
            break
    if start_at is None or end_at is None or end_at <= start_at:
        sys.exit('%s is missing products:%s markers' % (where, name))
    block = [line + '\n' for line in inner]
    return ''.join(lines[:start_at + 1] + block + lines[end_at:])


def _load_page_renderer():
    spec = importlib.util.spec_from_file_location('render_product_pages', ROOT / 'scripts' / 'render-product-pages.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_nav(prefix='./'):
    """The shared top bar and phone drawer, from the same generator the product pages use (home: locked dark)."""
    mod = _load_page_renderer()
    _data, catalog = mod.load_catalog()
    return mod.nav_html(catalog, None, True, prefix=prefix, home=True).split('\n')


def render(text, data):
    check_ids(data)
    text = replace_region(text, 'nav', render_nav())
    text = replace_region(text, 'products', render_deck(data))
    text = replace_region(text, 'lab', render_lab(data))
    text = replace_region(text, 'foot-products', render_foot(data, 'products'))
    text = replace_region(text, 'foot-lab', render_foot(data, 'lab'))
    return text


def render_m0(text, data):
    check_ids(data)
    mod = _load_page_renderer()
    _data, catalog = mod.load_catalog()
    nav = mod.nav_html(catalog, None, True, prefix='../', home=False).split('\n')
    foot = mod.footer_html(data, '').split('\n')
    text = replace_region(text, 'nav', nav, where='m0/index.html')
    text = replace_region(text, 'foot', foot, where='m0/index.html')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='exit 1 with a unified diff if index.html is stale')
    args = parser.parse_args()
    data = json.loads(DATA.read_text())
    old = INDEX.read_text()
    new = render(old, data)
    stale = False
    if args.check:
        if new != old:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile='index.html',
                tofile='index.html (rendered)',
            ))
            stale = True
    elif new != old:
        INDEX.write_text(new)
    if not M0.is_file():
        sys.exit('m0/index.html is missing')
    old_m0 = M0.read_text()
    new_m0 = render_m0(old_m0, data)
    if args.check:
        if new_m0 != old_m0:
            sys.stdout.writelines(difflib.unified_diff(
                old_m0.splitlines(keepends=True),
                new_m0.splitlines(keepends=True),
                fromfile='m0/index.html',
                tofile='m0/index.html (rendered)',
            ))
            stale = True
    elif new_m0 != old_m0:
        M0.write_text(new_m0)
    if args.check and stale:
        sys.exit(1)


if __name__ == '__main__':
    main()
