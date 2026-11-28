#!/usr/bin/env python3
"""Unit tests for scripts/render-product-pages.py."""
import contextlib
from html.parser import HTMLParser
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'render-product-pages.py'


def _load_renderer():
    spec = importlib.util.spec_from_file_location('render_product_pages', SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load_renderer()
S = M._shared


def _parse_jsonld(html_text):
    m = re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>', html_text, re.S)
    if not m:
        raise AssertionError('missing JSON-LD script tag')
    return json.loads(m.group(1))


def _sample_fixtures():
    data = {
        'products': [{
            'id': 'demo-prod', 'name': 'Demo <Prod> & Co', 'page': 'demo-prod/',
            'tag': 'Available now, v1.2.3, on npm', 'open_source': False,
            'licence_short': 'Open-core (Apache-2.0 core)', 'for_you': 'Fast & <safe> helper',
            'who_for': 'Builders & teams', 'description_html': 'Uses <b>open</b> tools.',
            'release_version': 'v1.2.3', 'release_date': '2026-11-26',
            'release_url': 'https://example.org/prod/v1.2.3', 'whats_new': '{personas} personas and {skills} skills.',
        }],
        'lab': [
            {
                'id': 'demo-prev', 'name': 'Demo Preview', 'page': 'demo-prev/',
                'href': 'https://example.org/prev', 'status': 'Source available, early preview',
                'open_source': True, 'licence_short': 'Apache-2.0 \u00b7 Open source',
                'for_you': 'Early preview tool', 'who_for': 'Early adopters', 'description': 'Preview tool.',
                'release_version': 'v0.7.0', 'release_date': '2026-10-15',
                'release_url': 'https://example.org/prev/v0.7.0', 'whats_new': 'First preview with {commands} commands.',
            },
            {
                'id': 'demo-src-rel', 'name': 'Demo Source Rel', 'page': 'demo-src-rel/',
                'href': 'https://example.org/srcrel', 'status': 'Source available, beta',
                'open_source': True, 'licence_short': 'MIT \u00b7 Open source',
                'for_you': 'Tagged source tool', 'who_for': 'Developers', 'description': 'Tagged source.',
                'release_version': 'v0.2.0', 'release_date': '2026-11-01',
                'release_url': 'https://example.org/srcrel/v0.2.0', 'whats_new': 'Source release with {agents} agents.',
            },
            {
                'id': 'demo-src', 'name': 'Demo Source', 'page': 'demo-src/',
                'href': 'https://example.org/src', 'status': 'Source available, no release',
                'open_source': True, 'licence_short': 'AGPL-3.0 \u00b7 Open source',
                'for_you': 'Undated source repo', 'who_for': 'Hackers', 'description': 'Source only.',
            },
            {
                'id': 'm0', 'name': 'Demo M0', 'page': 'm0/', 'status': 'Private beta, used daily',
                'open_source': False, 'licence_short': 'Private',
                'for_you': 'Private memory layer', 'who_for': 'Internal lab', 'description': 'Private beta.',
            },
            {
                'id': 'demo-cats', 'name': 'Demo Cats', 'page': 'demo-cats/', 'status': 'Private, in the lab',
                'open_source': False, 'licence_short': 'Private',
                'for_you': 'Local message bus', 'who_for': 'Multi-agent setups', 'description': 'Private lab.',
            },
        ],
    }
    base = {
        'diagram': 'router', 'does_for_you': 'Does the job cleanly.', 'who_detail': 'Detailed audience notes.',
        'does': [('Feature <A>', 'Handles A & B')], 'kns': [('10', 'Units')], 'next': [('Step one', 'Keep shipping.')],
        'try': {'heading': 'Install it', 'lead': 'Run one command.', 'note': 'Public note.'},
        'stage': {'cls': 'released', 'chip': 'Available now'}, 'meta_description': 'Meta desc for demo & <tests>.',
        'status': [('Stage', 'Available now.'), ('Licence', 'Open-core'), ('Tests', 'Green'), ('Extra', 'Omitted in llms')],
    }
    pub_specs = {
        'demo-prod': {
            **base, 'slug': 'demo-prod', 'og_image': 'https://example.org/og-prod.png', 'og_image_alt': 'Demo Prod OG',
            'app_category': 'DeveloperApplication', 'os': 'macOS, Linux', 'version': '1.2.3',
            'code_repository': 'https://example.org/prod', 'license_url': 'https://example.org/prod#licence',
            'licence_href': 'https://example.org/prod#licence', 'slot_label': 'Custom slot label',
            'try_above': {'kind': 'command', 'label': 'Install', 'note': 'Requires Node 20'},
            'try_alt': {'label': 'Docs', 'href': 'https://example.org/docs'},
            'try': {
                'heading': 'Install Demo', 'lead': 'Install from npm.',
                'install': {'label': 'Install', 'cmd': 'npx demo-prod'}, 'clone': 'https://example.org/prod.git',
                'downloads': [('macOS', 'prod.dmg')], 'buttons': [('Release', 'https://example.org/prod/v1.2.3', 'primary')],
                'note': 'SHA256SUMS included.',
            },
            'progress': {'count': '3 of 5 milestones', 'aria_label': 'Progress', 'now': 3, 'max': 5, 'pct': 60},
            'specs': [('Runtime', 'Python & Node')], 'links': [('Repo', 'https://example.org/prod'), ('Guide', '../guides/demo/')],
            'credits_html': 'Built on <a class="inline" href="https://example.org/upstream" rel="noopener">Upstream</a>.',
        },
        'demo-prev': {
            **base, 'slug': 'demo-prev', 'page_title': 'Custom Preview Title',
            'code_repository': 'https://example.org/prev', 'license_url': 'https://example.org/prev/LICENSE', 'version': '0.7.0',
            'try_above': {'kind': 'primary', 'label': 'View source', 'href': 'https://example.org/prev'},
            'stage': {'cls': 'source', 'chip': 'Early preview'},
        },
        'demo-src-rel': {
            **base, 'slug': 'demo-src-rel',
            'try_above': {'kind': 'primary', 'label': 'Source', 'href': '#try'}, 'stage': {'cls': 'source', 'chip': 'Source available'},
        },
        'demo-src': {
            **base, 'slug': 'demo-src',
            'try_above': {'kind': 'primary', 'label': 'Source', 'href': 'https://example.org/src'}, 'stage': {'cls': 'source', 'chip': 'Source available'},
        },
    }
    lab_specs = {'lab': {
        'm0': {**base, 'slug': 'm0', 'try_above': {'kind': 'static', 'label': 'Private beta'}, 'stage': {'cls': 'beta', 'chip': 'Private beta'}},
        'demo-cats': {
            **base, 'slug': 'demo-cats', 'noindex': True,
            'try_above': {'kind': 'static', 'label': 'Private, in the lab'}, 'stage': {'cls': 'lab', 'chip': 'Private, in the lab'},
            'cats_stage': {'tagline': 'Two cats, zero cloud.', 'story': 'Named after two cats.'},
        },
    }}
    catalog = S.build_catalog(data, pub_specs, lab_specs)
    for it in catalog:
        it['catalog'] = catalog
    counts = {'personas': 70, 'departments': 10, 'skills': 130, 'commands': 80, 'agents': 12}
    return data, pub_specs, lab_specs, catalog, counts


class RenderProductPagesTest(unittest.TestCase):
    def test_safe_href_allows_safe_and_rejects_unsafe(self):
        for ok in ('https://example.org/x', '../products/', '#try', 'mailto:a@b.org'):
            self.assertEqual(M._safe_href(ok, 't'), ok)
        for bad in ('http://example.org/x', 'javascript:alert(1)', 'data:text/html,hi'):
            with self.assertRaises(SystemExit):
                M._safe_href(bad, 't')

    def test_render_page_shipped_command_all_fields(self):
        data, _pub, _lab, catalog, _counts = _sample_fixtures()
        html = M.render_page(catalog[0], data)
        for needle in (
            '<title>Demo &lt;Prod&gt; &amp; Co \u2014 Coco Research</title>',
            'content="Meta desc for demo &amp; &lt;tests&gt;."',
            'property="og:image" content="https://example.org/og-prod.png"',
            'property="og:image:alt" content="Demo Prod OG"',
            'try-box p-try-cmd', 'npx demo-prod', 'href="https://example.org/docs">Docs</a>',
            '<p class="p-try-note">Requires Node 20</p>', 'data-kind="stage" data-stage="released"',
            'data-kind="licence" data-open="false"', 'Custom slot label', 'Awaiting a real running-app screenshot.',
            'git clone https://example.org/prod.git', 'prod.dmg', 'SHA256SUMS included.',
            'aria-valuenow="3" aria-valuemin="0" aria-valuemax="5"', 'style="width: 60%"',
            '<tr><th>Runtime</th><td>Python &amp; Node</td></tr>',
            'href="https://example.org/prod" rel="noopener">Repo</a>', 'href="../guides/demo/">Guide</a>',
            'Browse all 6 products', 'id="credits"', 'href="https://example.org/upstream"',
            '<li><a href="https://example.org/prod#licence">Licence</a></li>',
        ):
            self.assertIn(needle, html)
        self.assertNotIn('noindex, nofollow', html)
        ent = _parse_jsonld(html)['@graph'][0]
        self.assertEqual(ent['@type'], 'SoftwareApplication')
        self.assertEqual(ent['license'], 'https://example.org/prod#licence')
        self.assertEqual(ent['operatingSystem'], 'macOS, Linux')
        self.assertEqual(ent['softwareVersion'], '1.2.3')
        self.assertEqual(ent['codeRepository'], 'https://example.org/prod')

    def test_render_page_source_primary_and_page_title(self):
        data, _pub, _lab, catalog, _counts = _sample_fixtures()
        html = M.render_page(catalog[1], data)
        for needle in (
            '<title>Custom Preview Title</title>',
            '<a class="btn btn-primary" href="https://example.org/prev">View source</a>',
            'Real capture not yet added \u2014 Demo Preview',
            'data-kind="stage" data-stage="source"', 'data-kind="licence" data-open="true"',
        ):
            self.assertIn(needle, html)
        for absent in ('stage-progress', 'spec-table', 'id="credits"', '>Licence</a></li>'):
            self.assertNotIn(absent, html)
        ent = _parse_jsonld(html)['@graph'][0]
        self.assertEqual((ent['@type'], ent['codeRepository'], ent['version']),
                         ('SoftwareSourceCode', 'https://example.org/prev', '0.7.0'))

    def test_render_page_lab_private_cats_stage_and_noindex(self):
        data, _pub, _lab, catalog, _counts = _sample_fixtures()
        html = M.render_page(catalog[5], data)
        for needle in (
            '<meta name="robots" content="noindex, nofollow">', 'src="../assets/js/aloo-cats-scene.js"',
            'id="aloo-cats-canvas"', 'Two cats, zero cloud.', 'Named after two cats.',
            'data-product="demo-cats" data-own-stage>', '<span class="p-static-pill">',
            'What it does</h2>', 'Private, in the lab</h2>', 'mailto:product@cocoresearch.org',
        ):
            self.assertIn(needle, html)
        for absent in ('What it does today', 'Public note.', 'Awaiting a real running-app screenshot.', 'application/ld+json'):
            self.assertNotIn(absent, html)

    def test_render_page_rejects_unsafe_hrefs(self):
        for field in ('try_above', 'try_alt', 'buttons', 'links', 'licence_href'):
            data, _pub, _lab, catalog, _counts = _sample_fixtures()
            it = catalog[1] if field == 'try_above' else catalog[0]
            spec = it['spec']
            if field == 'try_above':
                spec['try_above'] = {'kind': 'primary', 'label': 'Bad', 'href': 'javascript:x()'}
            elif field == 'try_alt':
                spec['try_alt'] = {'label': 'Bad', 'href': 'http://insecure.example/'}
            elif field == 'buttons':
                spec['try']['buttons'] = [('Bad', 'javascript:x()', 'primary')]
            elif field == 'links':
                spec['links'] = [('Bad', 'http://insecure.example/')]
            else:
                spec['licence_href'] = 'javascript:x()'
            with self.assertRaises(SystemExit, msg=field):
                M.render_page(it, data)

    def test_card_html_render_products_and_render_lab(self):
        data, _pub, _lab, catalog, _counts = _sample_fixtures()
        self.assertIn('Try it<span class="sr-only"> Demo &lt;Prod&gt; &amp; Co</span>', M.card_html(catalog[0]))
        self.assertIn('Read more<span class="sr-only"> about Demo Preview</span>', M.card_html(catalog[1]))
        self.assertIn('Private, in the lab<span class="sr-only"> Demo M0</span>', M.card_html(catalog[4]))
        prod_html = M.render_products(catalog, data)
        for needle in ('All <span class="dir-tn">(6)</span>', 'Products <span class="dir-tn">(1)</span>', 'In the lab <span class="dir-tn">(5)</span>'):
            self.assertIn(needle, prod_html)
        self.assertEqual(_parse_jsonld(prod_html)['@graph'][0]['mainEntity']['numberOfItems'], 6)
        lab_html = M.render_lab(catalog, data)
        self.assertIn('Public code \u00b7 3', lab_html)
        self.assertIn('Private \u00b7 2', lab_html)
        for label, skey, shape, _desc in M.LAB_STAGE_KEY:
            self.assertIn('<dt data-stage="%s"><span class="sh %s" aria-hidden="true"></span>%s</dt>' % (skey, shape, label), lab_html)
        self.assertEqual(_parse_jsonld(lab_html)['@graph'][0]['mainEntity']['numberOfItems'], 5)

    def test_render_whats_new_sorting_chips_counts_and_guards(self):
        data, _pub, _lab, catalog, counts = _sample_fixtures()
        wn = M.render_whats_new(catalog, data, counts)
        for needle in (
            "<title>What's new \u2014 Coco Research</title>",
            '<meta property="og:title" content="What&#x27;s new \u2014 Coco Research">',
            '<meta name="twitter:title" content="What&#x27;s new \u2014 Coco Research">',
            '<h1 id="h-hero" class="display">What\'s new</h1>',
            '<div class="p-try-above" role="group" aria-label="Where to start">',
            '<div class="p-badges" role="group" aria-label="Groups">',
            '<div class="timeline" role="group" aria-label="Latest tagged releases">',
            '<div class="active-table" role="group" aria-label="Source projects without a packaged release">',
            'Demo &lt;Prod&gt; &amp; Co v1.2.3, released 26 Nov 2026.', '70 personas and 130 skills.',
            'First preview with 80 commands.', 'Source release with 12 agents.',
            'Released \u00b7 Open-core (Apache-2.0 core)', 'Early preview \u00b7 Apache-2.0',
            'Source available \u00b7 MIT', 'href="../demo-src/">Demo Source</a>',
            '<li><a href="../demo-cats/">Demo Cats</a></li>', '3 tagged releases',
        ):
            self.assertIn(needle, wn)
        self.assertNotIn('What\u2019s new', wn)
        ld = _parse_jsonld(wn)['@graph']
        self.assertEqual(ld[0]['name'], "What's new \u2014 Coco Research")
        self.assertEqual(ld[1]['itemListElement'][-1]['name'], "What's new")
        self.assertLess(wn.index('2026-11-26'), wn.index('2026-11-01'))
        self.assertLess(wn.index('2026-11-01'), wn.index('2026-10-15'))
        # Archived source row in /whats-new/ active table uses archived key and bar shape.
        catalog[3]['row']['status'] = 'Source available, AGPL-3.0, archived'
        wn_arch = M.render_whats_new(catalog, data, counts)
        self.assertIn('<span class="stage-chip" data-stage="archived"><span class="sh sh-bar" aria-hidden="true"></span>Archived</span>', wn_arch)
        catalog[0]['row']['release_url'] = 'http://insecure.example/r'
        with self.assertRaises(SystemExit):
            M.render_whats_new(catalog, data, counts)
        for it in catalog:
            it['row'].pop('release_date', None)
        with self.assertRaises(SystemExit):
            M.render_whats_new(catalog, data, counts)

    def test_count_words_follow_catalog_and_stage_key(self):
        self.assertEqual((M._count_word(0), M._count_word(12, cap=True), M._count_word(13), M._count_word(13, cap=True)),
                         ('zero', 'Twelve', '13', '13'))
        data, pub_specs, lab_specs, catalog, _counts = _sample_fixtures()
        prod0, lab0 = catalog[0], catalog[1]
        cat_3_6 = [dict(prod0, pid='p%d' % i) for i in range(3)] + [dict(lab0, pid='l%d' % i) for i in range(6)]
        for it in cat_3_6:
            it['catalog'] = cat_3_6
        prod_html = M.render_products(cat_3_6, data)
        self.assertIn('All 9 Coco Research products and what each does for you: three available now and six in the lab.', prod_html)
        self.assertIn('Nine products in two groups. Three you can use today, six still in the lab, each with its stage stated plainly.', prod_html)
        lab_html = M.render_lab(cat_3_6, data)
        self.assertIn('Six projects in progress, from public early previews to private betas.', lab_html)
        self.assertIn('Five labels, used the same way on every page.', lab_html)
        with mock.patch.object(M, 'LAB_STAGE_KEY', M.LAB_STAGE_KEY[:4]):
            self.assertIn('Four labels, used the same way on every page.', M.render_lab(cat_3_6, data))

    def test_render_sitemap_and_render_llms(self):
        _data, _pub, _lab, catalog, _counts = _sample_fixtures()
        catalog[2]['spec']['slug'] = 'a&b'
        sm = M.render_sitemap(catalog)
        self.assertIn('<loc>%s/whats-new/</loc>\n    <lastmod>2026-11-26</lastmod>' % M.SITE, sm)
        self.assertIn('<loc>%s/demo-prod/</loc>\n    <lastmod>2026-11-26</lastmod>' % M.SITE, sm)
        self.assertIn('<loc>%s/demo-prev/</loc>\n    <lastmod>2026-10-15</lastmod>' % M.SITE, sm)
        self.assertIn('<loc>%s/a&amp;b/</loc>\n    <lastmod>2026-11-01</lastmod>' % M.SITE, sm)
        self.assertIn('<loc>%s/demo-src/</loc>\n  </url>' % M.SITE, sm)
        self.assertIn('<loc>%s/</loc>\n  </url>' % M.SITE, sm)
        self.assertIn('<loc>%s/rijul-kalra/</loc>\n  </url>' % M.SITE, sm)
        self.assertNotIn('demo-cats', sm)
        for it in catalog:
            it['row'].pop('release_date', None)
        self.assertNotIn('<lastmod>', M.render_sitemap(catalog))
        llms = M.render_llms(catalog)
        self.assertIn('1. Data stays local. Voice runs offline. Our tools run on your machine.', llms)
        self.assertNotIn('speech model', llms)
        self.assertIn('## Products (1, available now)', llms)
        self.assertIn('## In the lab (5)', llms)
        self.assertIn('Stage: Available now. Licence: Open-core. Tests: Green.', llms)
        self.assertNotIn('Omitted in llms', llms)
        self.assertNotIn('Available now..', llms)

    def test_main_cli_modes_and_check_drift(self):
        data, pub_specs, lab_specs, _catalog, _counts = _sample_fixtures()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            (root / 'docs').mkdir()
            (root / 'data' / 'products.json').write_text(json.dumps(data))
            (root / 'data' / 'product-pages-public.json').write_text(json.dumps(pub_specs))
            (root / 'data' / 'product-pages-lab.json').write_text(json.dumps(lab_specs))
            (root / 'docs' / 'released-counts.json').write_text(json.dumps({
                'personas': {'total': 70}, 'departments': {'total': 10},
                'skills': {'total': 130}, 'commands': {'customer_facing': 80}, 'agents': {'total': 12},
            }))

            def run_main(argv, expect_exit=None):
                buf = io.StringIO()
                with contextlib.ExitStack() as stack:
                    for obj, attr_name, val in (
                        (M, 'ROOT', root), (S, 'ROOT', root), (S, 'DATA', root / 'data' / 'products.json'),
                        (S, 'SPEC_PUBLIC', root / 'data' / 'product-pages-public.json'),
                        (S, 'SPEC_LAB', root / 'data' / 'product-pages-lab.json'),
                        (sys, 'argv', ['render-product-pages.py'] + argv),
                    ):
                        stack.enter_context(mock.patch.object(obj, attr_name, val))
                    stack.enter_context(contextlib.redirect_stdout(buf))
                    if expect_exit is None:
                        M.main()
                    else:
                        with self.assertRaises(SystemExit) as cm:
                            M.main()
                        if expect_exit is not True:
                            self.assertEqual(cm.exception.code, expect_exit)
                return buf.getvalue()

            self.assertNotIn('aria-current="page"', run_main(['--print-nav', 'none']))
            self.assertIn('aria-current="page"', run_main(['--print-nav', 'products']))
            run_main([], expect_exit=True)
            three_js = root / 'assets' / 'vendor' / 'three' / 'three.module.min.js'
            three_js.parent.mkdir(parents=True)
            three_js.write_text('// three')
            run_main(['--only', 'demo-prod'])
            self.assertTrue((root / 'demo-prod' / 'index.html').is_file())
            self.assertFalse((root / 'products' / 'index.html').is_file())
            run_main([])
            self.assertFalse((root / 'm0' / 'index.html').exists())
            for rel in ('demo-prod/index.html', 'demo-prev/index.html', 'products/index.html',
                        'lab/index.html', 'whats-new/index.html', 'sitemap.xml', 'llms.txt'):
                self.assertTrue((root / rel).is_file(), rel)
            self.assertEqual(run_main(['--check']), '')
            stale = root / 'llms.txt'
            stale.write_text('stale\n')
            self.assertIn('--- llms.txt', run_main(['--check'], expect_exit=1))
            self.assertEqual(stale.read_text(), 'stale\n')
            run_main(['--include-custom'])
            self.assertTrue((root / 'm0' / 'index.html').is_file())

    def test_real_repo_specs_every_field_rendered(self):
        pub_specs = json.loads((REPO_ROOT / 'data' / 'product-pages-public.json').read_text())
        lab_specs = json.loads((REPO_ROOT / 'data' / 'product-pages-lab.json').read_text())
        data = {'products': [], 'lab': []}
        for pid, spec in pub_specs.items():
            row = {
                'id': pid, 'name': pid, 'page': spec['slug'] + '/', 'tag': 'Available now, v1.0.0',
                'status': 'Source available, early preview', 'open_source': pid != 'coco-si',
                'licence_short': 'Open-core' if pid == 'coco-si' else 'Apache-2.0',
                'for_you': 'For you %s' % pid, 'who_for': 'Who for %s' % pid,
            }
            if pid in ('coco-si', 'voice'):
                data['products'].append(row)
            else:
                row['href'] = spec.get('code_repository', 'https://example.org/' + pid)
                data['lab'].append(row)
        for pid, spec in lab_specs['lab'].items():
            data['lab'].append({
                'id': pid, 'name': pid, 'page': spec['slug'] + '/', 'status': 'Private, in the lab',
                'open_source': False, 'licence_short': 'Private', 'for_you': 'For you %s' % pid, 'who_for': 'Who for %s' % pid,
            })
        catalog = S.build_catalog(data, pub_specs, lab_specs)
        for it in catalog:
            it['catalog'] = catalog
        self.assertEqual(len(catalog), 10)
        for it in catalog:
            spec = it['spec']
            html = M.render_page(it, data)
            ld = _parse_jsonld(html) if it['bucket'] != 'lab' else None
            if it['bucket'] == 'lab':
                self.assertNotIn('application/ld+json', html)
            for val in (spec['meta_description'], spec['does_for_you'], spec['who_detail']):
                self.assertIn(M.esc(val), html)
            self.assertIn(M.attr(spec.get('og_image', M.DEFAULT_OG)), html)
            for pairs in (spec['does'], spec['status'], spec['kns'], spec['next']):
                for left, right in pairs:
                    self.assertIn(M.esc(left), html)
                    self.assertIn(M.esc(right), html)
            if it['pid'] == 'coco-si':
                self.assertEqual(ld['@graph'][0]['license'], 'https://github.com/coco-research/coco#licence')
                self.assertNotIn('/blob/main/LICENSE', html)
                self.assertNotIn('operatingSystem', ld['@graph'][0])
            elif it['pid'] == 'voice':
                self.assertIn('arm64', ld['@graph'][0]['operatingSystem'])
                self.assertIn('Coco.Voice_0.20.9_aarch64.AppImage', html)
            elif it['pid'] == 'aloomannu':
                self.assertIn('aloo-cats-scene.js', html)
                self.assertIn('mailto:product@cocoresearch.org', html)

    def test_try_dl_contains_only_code_and_span(self):
        class TryDlParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_try_dl = False
                self.depth = 0
                self.ul_count = 0
                self.items = []
                self.cur_item = None
                self.bad = []

            def handle_starttag(self, tag, attrs):
                classes = set((dict(attrs).get('class') or '').split())
                if not self.in_try_dl:
                    if tag == 'ul' and 'try-dl' in classes:
                        self.in_try_dl = True
                        self.depth = 1
                        self.ul_count += 1
                    return
                self.depth += 1
                if 'link-pill' in classes:
                    self.bad.append('link-pill inside .try-dl')
                if self.depth == 2:
                    if tag != 'li':
                        self.bad.append('expected <li> inside .try-dl, got <%s>' % tag)
                    else:
                        self.cur_item = []
                elif self.depth == 3:
                    if self.cur_item is not None:
                        self.cur_item.append(tag)
                else:
                    self.bad.append('unexpected nested <%s> at depth %d in .try-dl' % (tag, self.depth))

            def handle_endtag(self, tag):
                if not self.in_try_dl:
                    return
                if self.depth == 2 and tag == 'li' and self.cur_item is not None:
                    if self.cur_item != ['code', 'span']:
                        self.bad.append('expected li > code + span, got %r' % (self.cur_item,))
                    self.items.append(self.cur_item)
                    self.cur_item = None
                self.depth -= 1
                if self.depth == 0:
                    self.in_try_dl = False

        def check_try_dl(html_text, expect_lists):
            p = TryDlParser()
            p.feed(html_text)
            p.close()
            self.assertEqual(p.ul_count, expect_lists)
            self.assertEqual(p.bad, [])
            if expect_lists:
                self.assertTrue(p.items)

        pub_specs = json.loads((REPO_ROOT / 'data' / 'product-pages-public.json').read_text())
        lab_specs = json.loads((REPO_ROOT / 'data' / 'product-pages-lab.json').read_text())
        data = {'products': [], 'lab': []}
        for pid, spec in pub_specs.items():
            row = {
                'id': pid, 'name': pid, 'page': spec['slug'] + '/', 'tag': 'Available now, v1.0.0',
                'status': 'Source available, early preview', 'open_source': pid != 'coco-si',
                'licence_short': 'Open-core' if pid == 'coco-si' else 'Apache-2.0',
                'for_you': 'For you %s' % pid, 'who_for': 'Who for %s' % pid,
            }
            if pid in ('coco-si', 'voice'):
                data['products'].append(row)
            else:
                row['href'] = spec.get('code_repository', 'https://example.org/' + pid)
                data['lab'].append(row)
        for pid, spec in lab_specs['lab'].items():
            data['lab'].append({
                'id': pid, 'name': pid, 'page': spec['slug'] + '/', 'status': 'Private, in the lab',
                'open_source': False, 'licence_short': 'Private', 'for_you': 'For you %s' % pid, 'who_for': 'Who for %s' % pid,
            })
        catalog = S.build_catalog(data, pub_specs, lab_specs)
        for it in catalog:
            it['catalog'] = catalog
        for it in catalog:
            html = M.render_page(it, data)
            check_try_dl(html, 1 if it['pid'] == 'voice' else 0)
        voice_html = (REPO_ROOT / 'voice' / 'index.html').read_text(encoding='utf-8')
        check_try_dl(voice_html, 1)
        with self.assertRaises(AssertionError):
            check_try_dl('<ul class="try-dl"><li><a class="link-pill" href="#x">x</a></li></ul>', 1)


if __name__ == '__main__':
    unittest.main()
