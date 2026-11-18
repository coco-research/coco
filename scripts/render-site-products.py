#!/usr/bin/env python3
"""Rewrite the homepage product regions from data/products.json.

Run from the repo root. Default mode writes index.html. --check exits 1
and prints a unified diff when index.html differs from the render.
"""
import argparse
import difflib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
INDEX = ROOT / 'index.html'
DATA = ROOT / 'data' / 'products.json'
ANCHOR = re.compile(r'<a class="inline" href="([^"]*)" rel="noopener">([^<]*)</a>')
ID_OK = re.compile(r'[a-z0-9-]+')


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
    lines.extend([
        '          </div>',
        '          <div class="card-body">',
        '            <h3 id="t-%s">%s</h3>' % (pid, esc_text(product['name'])),
        '            <p class="tag">%s</p>' % esc_text(product['tag']),
        '            <p>%s</p>' % render_description_html(product['description_html'], pid),
        '            <div class="card-actions">',
    ])
    actions = product['actions']
    if not actions:
        sys.exit('%s: needs at least one action' % pid)
    for action in actions:
        kind = action['kind']
        if kind not in ('primary', 'ghost'):
            sys.exit('%s: action kind must be primary or ghost' % pid)
        if not action['href'].startswith('https://'):
            sys.exit('%s: action href must be https://' % pid)
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
    seen = set()
    for group in ('shipped', 'source', 'lab'):
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


def render_shipped(data):
    lines = []
    for index, product in enumerate(data['shipped']):
        if index:
            lines.append('')
        lines.extend(render_card(product))
    return lines


def render_source_row(row):
    pid = row['id']
    require_https(row['href'], pid)
    name = '<a class="inline" href="%s" rel="noopener">%s</a>' % (esc_attr(row['href']), esc_text(row['name']))
    return (
        '            <li class="lab-item"><h4>%s</h4><p>%s<span class="tag">%s</span></p></li>'
        % (name, esc_text(row['description']), esc_text(row['status']))
    )


def render_lab_row(row):
    if 'href' in row:
        sys.exit('%s: lab rows have no href' % row['id'])
    return (
        '            <li class="lab-item"><h4>%s</h4><p>%s<span class="tag">%s</span></p></li>'
        % (esc_text(row['name']), esc_text(row['description']), esc_text(row['status']))
    )


def render_lab(data):
    lines = ['          <h3 class="lab-group">Source available</h3>', '          <ul>']
    lines.extend(render_source_row(row) for row in data['source'])
    lines.append('          </ul>')
    lines.append('          <h3 class="lab-group">Private, in the lab</h3>')
    lines.append('          <ul>')
    lines.extend(render_lab_row(row) for row in data['lab'])
    lines.append('          </ul>')
    return lines


def render_foot_shipped(data):
    return [
        '          <li><a href="%s">%s</a></li>' % (esc_attr(row['footer_href']), esc_text(row['name']))
        for row in data['shipped']
    ]


def render_foot_source(data):
    lines = []
    for row in data['source']:
        require_https(row['href'], row['id'])
        lines.append('          <li><a href="%s">%s</a></li>' % (esc_attr(row['href']), esc_text(row['name'])))
    return lines


def render_foot_lab(data):
    return [
        '          <li><a href="#lab" data-goto="lab">%s</a></li>' % esc_text(row['name'])
        for row in data['lab']
    ]


def replace_region(text, name, inner):
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
        sys.exit('index.html is missing products:%s markers' % name)
    block = [line + '\n' for line in inner]
    return ''.join(lines[:start_at + 1] + block + lines[end_at:])


def render(text, data):
    check_ids(data)
    text = replace_region(text, 'shipped', render_shipped(data))
    text = replace_region(text, 'lab', render_lab(data))
    text = replace_region(text, 'foot-shipped', render_foot_shipped(data))
    text = replace_region(text, 'foot-source', render_foot_source(data))
    text = replace_region(text, 'foot-lab', render_foot_lab(data))
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='exit 1 with a unified diff if index.html is stale')
    args = parser.parse_args()
    data = json.loads(DATA.read_text())
    old = INDEX.read_text()
    new = render(old, data)
    if args.check:
        if new != old:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile='index.html',
                tofile='index.html (rendered)',
            ))
            sys.exit(1)
        return
    if new != old:
        INDEX.write_text(new)


if __name__ == '__main__':
    main()
