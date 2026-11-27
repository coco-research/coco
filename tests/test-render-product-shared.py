#!/usr/bin/env python3
"""Unit tests for scripts/render_product_shared.py."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_PATH = REPO_ROOT / 'scripts' / 'render_product_shared.py'


def _load_shared():
    spec = importlib.util.spec_from_file_location('render_product_shared', SHARED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load_shared()


def _sample_fixtures():
    data = {
        'products': [
            {'id': 'demo-prod', 'name': 'Demo <Prod> & Co', 'page': 'demo-prod/', 'tag': 'Available now, v1.2.3, on npm',
             'for_you': 'Fast & <safe> helper', 'description_html': 'Uses <b>open</b> tools.'},
            {'id': 'demo-plain', 'name': 'Demo Plain', 'page': 'demo-plain/', 'tag': 'Available now',
             'for_you': 'Plain build', 'description': 'Plain text description'},
        ],
        'lab': [
            {'id': 'heliopause', 'name': 'Heliopause by Coco Research', 'page': 'heliopause/',
             'href': 'https://example.org/heliopause', 'status': 'Source available, early preview',
             'for_you': 'Local status board', 'description': 'Local status board.'},
            {'id': 'demo-arch', 'name': 'Demo Archived', 'page': 'demo-arch/"x',
             'href': 'https://example.org/arch', 'status': 'Source available, Archived reference',
             'for_you': 'Old prototype', 'description': 'Archived project.'},
            {'id': 'demo-pre', 'name': 'Demo Pre', 'page': 'demo-pre/',
             'href': 'https://example.org/pre', 'status': 'Source available, pre-alpha',
             'for_you': 'Pre-alpha tool', 'description': 'Early code.'},
            {'id': 'demo-priv', 'name': 'Demo Private', 'page': 'demo-priv/',
             'status': 'Private, in the lab', 'for_you': 'Internal only', 'description': 'Private experiment.'},
            {'id': 'demo-beta', 'name': 'Demo Beta', 'page': 'demo-beta/',
             'status': 'Private beta, used daily', 'for_you': 'Beta lab tool', 'description': 'Beta tool.'},
        ],
    }
    pub_specs = {
        'demo-prod': {'slug': 'demo-prod', 'diagram': 'editions', 'version': '1.2.3',
                      'app_category': 'UtilitiesApplication', 'os': 'macOS',
                      'license_url': 'https://example.org/lic', 'code_repository': 'https://example.org/repo',
                      'stage': {'chip': 'Released', 'cls': 'released'},
                      'try': {'downloads': [('demo_1.2.3.dmg', 'Mac <ARM> & Intel')]}},
        'demo-plain': {'slug': 'demo-plain', 'diagram': 'frames', 'licence_href': 'https://example.org/lic-fb',
                       'stage': {'chip': 'Released', 'cls': 'released'}, 'try': {}},
        'heliopause': {'slug': 'heliopause', 'diagram': 'heliosphere', 'version': '0.5.0',
                       'programming_language': 'Python', 'stage': {'chip': 'Preview', 'cls': 'source'}, 'try': {}},
        'demo-arch': {'slug': 'demo-arch', 'diagram': 'ripple', 'stage': {'chip': 'Archived', 'cls': 'source'}, 'try': {}},
        'demo-pre': {'slug': 'demo-pre', 'diagram': 'council', 'stage': {'chip': 'Pre-alpha', 'cls': 'source'}, 'try': {}},
    }
    lab_specs = {
        'lab': {
            'demo-priv': {'slug': 'demo-priv', 'diagram': 'router', 'stage': {'chip': 'Lab', 'cls': 'lab'}, 'try': {}},
            'demo-beta': {'slug': 'demo-beta', 'diagram': 'vault', 'stage': {'chip': 'Private beta', 'cls': 'beta'}, 'try': {}},
        }
    }
    return data, pub_specs, lab_specs


class EscapingAndLinksTests(unittest.TestCase):
    def test_esc_and_attr(self):
        self.assertEqual(M.esc('<a & "b" \'c\'>'), '&lt;a &amp; "b" \'c\'&gt;')
        self.assertEqual(M.attr('<a & "b" \'c\'>'), '&lt;a &amp; &quot;b&quot; &#x27;c&#x27;&gt;')

    def test_require_https_accepts_and_rejects(self):
        self.assertIsNone(M.require_https('https://example.org/path?a=1&b=2', 'ok'))
        for bad in ('http://example.org', 'javascript:alert(1)', 'data:text/html,1', '', 'https://example.org/<x', 'https://example.org/>x'):
            with self.subTest(bad=bad):
                with self.assertRaises(SystemExit) as ctx:
                    M.require_https(bad, 'ctx-label')
                self.assertIn('ctx-label', str(ctx.exception))
                self.assertIn('https://', str(ctx.exception))

    def test_render_desc_html(self):
        raw = 'A & B <a class="inline" href="https://example.org/?a=1&b=2" rel="noopener">Docs & Guide</a> tail.'
        exp = 'A &amp; B <a class="inline" href="https://example.org/?a=1&amp;b=2" rel="noopener">Docs &amp; Guide</a> tail.'
        self.assertEqual(M.render_desc_html(raw, 'desc'), exp)
        for bad in (
            '<b>bold</b>',
            'ok <a class="inline" href="https://example.org" rel="noopener">x</a> <i>bad</i>',
            'ok <a class="inline" href="http://example.org" rel="noopener">x</a>',
            'ok <a class="inline" href="javascript:alert(1)" rel="noopener">x</a>',
            'dangling > bracket',
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(SystemExit):
                    M.render_desc_html(bad, 'desc')


class SvgAndJsonLdTests(unittest.TestCase):
    def test_world_fallback_svg_motif_and_diagram(self):
        motif_svg = M.world_fallback_svg('coco-si', {'diagram': 'editions'})
        self.assertIn('class="world-svg-fallback"', motif_svg)
        self.assertIn('viewBox="0 0 1200 800"', motif_svg)
        self.assertIn('focusable="false"', motif_svg)
        self.assertIn(M.WORLD_FALLBACK_MOTIFS['coco-si'], motif_svg)
        self.assertNotIn('translate(610 250)', motif_svg)

        diag_svg = M.world_fallback_svg('demo-prod', {'diagram': 'editions'})
        self.assertIn('translate(610 250) scale(1.25)', diag_svg)
        self.assertIn(M.DIAGRAMS['editions'], diag_svg)

    def test_build_jsonld_shipped_source_and_lab(self):
        data, pub_specs, lab_specs = _sample_fixtures()
        self.assertEqual(M.build_jsonld('demo-priv', 'lab', data['lab'][3], lab_specs['lab']['demo-priv']), '')

        shipped = M.build_jsonld('demo-prod', 'shipped', data['products'][0], pub_specs['demo-prod'])
        self.assertTrue(shipped.startswith('\n<script type="application/ld+json">\n') and shipped.endswith('\n</script>'))
        app, crumb = json.loads(shipped.split('\n', 2)[2].rsplit('\n', 1)[0])['@graph']
        self.assertEqual(app['@type'], 'SoftwareApplication')
        self.assertEqual(app['description'], 'Uses open tools.')
        self.assertEqual(app['softwareVersion'], '1.2.3')
        self.assertEqual(app['offers'], {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'})
        self.assertEqual(app['license'], 'https://example.org/lic')
        self.assertEqual(crumb['@type'], 'BreadcrumbList')
        self.assertEqual(crumb['itemListElement'][1]['item'], 'https://cocoresearch.org/demo-prod/')

        src_row = {'id': 's1', 'name': 'Src <!-- </script>', 'href': 'https://example.org/s1', 'description': 'Desc'}
        src_html = M.build_jsonld('s1', 'source', src_row, {'slug': 's1', 'version': '0.9.0', 'licence_href': 'https://example.org/l'})
        inner = src_html.split('\n', 2)[2].rsplit('\n', 1)[0]
        self.assertNotIn('<', inner)
        self.assertIn('\\u003c!-- \\u003c/script>', inner)
        self.assertEqual(src_html.count('</script>'), 1)
        src_ent = json.loads(inner)['@graph'][0]
        self.assertEqual(src_ent['@type'], 'SoftwareSourceCode')
        self.assertEqual(src_ent['codeRepository'], 'https://example.org/s1')
        self.assertEqual(src_ent['version'], '0.9.0')

        # M2: shipped spec without 'os' omits operatingSystem (never falls back to Windows).
        no_os_spec = dict(pub_specs['demo-prod'])
        no_os_spec.pop('os', None)
        no_os_html = M.build_jsonld('demo-prod', 'shipped', data['products'][0], no_os_spec)
        no_os_app = json.loads(no_os_html.split('\n', 2)[2].rsplit('\n', 1)[0])['@graph'][0]
        self.assertNotIn('operatingSystem', no_os_app)

        # M1 + M2 on real repo data: coco-si uses #licence (never bare /LICENSE) and omits operatingSystem; voice keeps os.
        real_pub = json.loads((M.ROOT / 'data' / 'product-pages-public.json').read_text(encoding='utf-8'))
        si_html = M.build_jsonld('coco-si', 'shipped', {'name': 'Coco Super Intelligence', 'description': 'Advisory board.'}, real_pub['coco-si'])
        si_app = json.loads(si_html.split('\n', 2)[2].rsplit('\n', 1)[0])['@graph'][0]
        self.assertEqual(si_app['license'], 'https://github.com/coco-research/coco#licence')
        self.assertFalse(si_app['license'].endswith('/LICENSE'))
        self.assertNotIn('operatingSystem', si_app)
        voice_html = M.build_jsonld('voice', 'shipped', {'name': 'Coco Voice', 'description': 'Speech to text.'}, real_pub['voice'])
        voice_app = json.loads(voice_html.split('\n', 2)[2].rsplit('\n', 1)[0])['@graph'][0]
        self.assertIn('Linux x64 and arm64', voice_app['operatingSystem'])

        no_ver = M.build_jsonld('demo-arch', 'source', data['lab'][1], pub_specs['demo-arch'])
        self.assertNotIn('version', json.loads(no_ver.split('\n', 2)[2].rsplit('\n', 1)[0])['@graph'][0])

    def test_ld_script_breadcrumb_and_collection_ld(self):
        script = M.ld_script({'note': 'a <!-- </script> \u2014 b'})
        inner = script.split('\n', 2)[2].rsplit('\n', 1)[0]
        self.assertNotIn('<', inner)
        self.assertIn('\\u003c!-- \\u003c/script>', inner)
        self.assertIn('\u2014', script)
        self.assertEqual(script.count('</script>'), 1)

        crumb = M.breadcrumb('Products', 'https://cocoresearch.org/products/')
        self.assertEqual(crumb['@type'], 'BreadcrumbList')
        self.assertEqual(crumb['itemListElement'][0]['item'], 'https://cocoresearch.org/')
        self.assertEqual(crumb['itemListElement'][1], {'@type': 'ListItem', 'position': 2, 'name': 'Products', 'item': 'https://cocoresearch.org/products/'})

        data, pub_specs, lab_specs = _sample_fixtures()
        cat = M.build_catalog(data, pub_specs, lab_specs)
        col = M.collection_ld('Products \u2014 Coco Research', 'https://cocoresearch.org/products/', 'All items', cat[:2])
        page, col_crumb = col['@graph']
        self.assertEqual(page['@type'], 'CollectionPage')
        self.assertEqual(page['mainEntity']['numberOfItems'], 2)
        self.assertEqual(page['mainEntity']['itemListElement'][0]['url'], 'https://cocoresearch.org/demo-prod/')
        self.assertEqual(col_crumb['itemListElement'][1]['name'], 'Products')


class CatalogDatesAndStagesTests(unittest.TestCase):
    def test_human_date(self):
        self.assertEqual(M.human_date('2026-01-05'), '5 Jan 2026')
        self.assertEqual(M.human_date('2026-12-31'), '31 Dec 2026')
        for bad in ('', '2026-01', '2026-xx-01'):
            with self.assertRaises(ValueError):
                M.human_date(bad)
        with self.assertRaises(IndexError):
            M.human_date('2026-13-01')

    def test_build_catalog_and_load_catalog(self):
        data, pub_specs, lab_specs = _sample_fixtures()
        cat = M.build_catalog(data, pub_specs, lab_specs)
        self.assertEqual([it['pid'] for it in cat], ['demo-prod', 'demo-plain', 'heliopause', 'demo-arch', 'demo-pre', 'demo-priv', 'demo-beta'])
        self.assertEqual([it['bucket'] for it in cat], ['shipped', 'shipped', 'source', 'source', 'source', 'lab', 'lab'])
        self.assertEqual([it['private'] for it in cat], [False, False, False, False, False, True, True])

        with self.assertRaises(SystemExit) as ctx:
            M.build_catalog({'products': [{'id': 'ghost-id', 'name': 'Ghost'}], 'lab': []}, pub_specs, lab_specs)
        self.assertIn('ghost-id', str(ctx.exception))

        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            p_data, p_pub, p_lab = t / 'products.json', t / 'pub.json', t / 'lab.json'
            p_data.write_text(json.dumps(data))
            p_pub.write_text(json.dumps(pub_specs))
            p_lab.write_text(json.dumps(lab_specs))
            with mock.patch.object(M, 'DATA', p_data), mock.patch.object(M, 'SPEC_PUBLIC', p_pub), mock.patch.object(M, 'SPEC_LAB', p_lab):
                loaded_data, loaded_cat = M.load_catalog()
            self.assertEqual((len(loaded_cat), loaded_data['products'][0]['id']), (7, 'demo-prod'))
            self.assertIs(loaded_cat[0]['catalog'], loaded_cat)
            with mock.patch.object(M, 'DATA', t / 'missing.json'):
                with self.assertRaises(FileNotFoundError):
                    M.load_catalog()

    def test_counts_ctx_live_and_isolated(self):
        live = json.loads((REPO_ROOT / 'docs' / 'released-counts.json').read_text())
        exp = {'personas': live['personas']['total'], 'departments': live['departments']['total'],
               'skills': live['skills']['total'], 'commands': live['commands']['customer_facing'], 'agents': live['agents']['total']}
        with mock.patch.object(M, 'ROOT', REPO_ROOT):
            self.assertEqual(M.counts_ctx(), exp)

        with tempfile.TemporaryDirectory() as tmp:
            docs_dir = Path(tmp) / 'docs'
            docs_dir.mkdir()
            (docs_dir / 'released-counts.json').write_text(json.dumps({
                'personas': {'total': 11}, 'departments': {'total': 2},
                'skills': {'total': 33}, 'commands': {'customer_facing': 44}, 'agents': {'total': 5},
            }))
            with mock.patch.object(M, 'ROOT', Path(tmp)):
                self.assertEqual(M.counts_ctx(), {'personas': 11, 'departments': 2, 'skills': 33, 'commands': 44, 'agents': 5})

    def test_stage_helpers(self):
        data, pub_specs, lab_specs = _sample_fixtures()
        by_id = {it['pid']: it for it in M.build_catalog(data, pub_specs, lab_specs)}
        src_plain = {'pid': 'x', 'bucket': 'source', 'row': {'status': 'Source available, MIT'}, 'spec': {'stage': {'cls': 'source'}}}

        self.assertEqual(M.stage_chip_text(by_id['demo-prod']), 'Available now \u00b7 v1.2.3')
        self.assertEqual(M.stage_chip_text(by_id['demo-plain']), 'Available now')
        self.assertEqual(M.stage_chip_text(by_id['demo-arch']), 'Archived')
        self.assertEqual(M.stage_chip_text(by_id['heliopause']), 'Source available')
        self.assertEqual(M.stage_chip_text(by_id['demo-priv']), 'In the lab')

        self.assertEqual(M.stage_label(by_id['demo-prod']), 'Available now \u00b7 v1.2.3')
        self.assertEqual(M.stage_label(by_id['demo-priv']), 'Private, in the lab')
        self.assertEqual(M.stage_label(by_id['heliopause']), 'Early preview')
        self.assertEqual(M.stage_label(by_id['demo-arch']), 'Archived')
        self.assertEqual(M.stage_label(by_id['demo-pre']), 'Pre-alpha')
        self.assertEqual(M.stage_label(src_plain), 'Source available')
        self.assertEqual(M.stage_label(by_id['demo-beta']), 'Private beta')

        self.assertEqual((M.stage_shape(by_id['demo-prod']), M.stage_shape(by_id['heliopause']), M.stage_shape(by_id['demo-priv'])),
                         ('sh-dot', 'sh-ring', 'sh-sq'))
        self.assertEqual((M.stage_key(by_id['demo-prod']), M.stage_key(by_id['heliopause']), M.stage_key(by_id['demo-beta']), M.stage_key(by_id['demo-priv'])),
                         ('released', 'source', 'beta', 'lab'))
        self.assertEqual(M.short_status(by_id['demo-prod']), 'Available now, v1.2.3, on npm')
        self.assertEqual(M.short_status(by_id['demo-beta']), 'Private beta, used daily')


class ChromeAndBuildersTests(unittest.TestCase):
    def test_menu_nav_and_footer_html(self):
        data, pub_specs, lab_specs = _sample_fixtures()
        cat = M.build_catalog(data, pub_specs, lab_specs)

        menu = M.menu_group_html(cat, 2, '../')
        for snippet in ('data-group="products"', '<span class="sn-m-n">2</span>', '<span class="sn-m-n">5</span>',
                        'Demo &lt;Prod&gt; &amp; Co', 'Fast &amp; &lt;safe&gt; helper', '>Heliopause</span>',
                        '<span class="sn-m-badge">Archived</span>',
                        '<span class="sn-m-priv"><span class="sh sh-sq" aria-hidden="true"></span>Private, in the lab</span>'):
            self.assertIn(snippet, menu)

        nav = M.nav_html(cat, 'lab', three=True)
        for snippet in ('href="../lab/" aria-current="page"', 'data-theme-toggle', 'data-motion-toggle>Pause 3D</button>',
                        'Browse all 7 products', 'id="sn-drawer-title">Site menu</h2>'):
            self.assertIn(snippet, nav)

        nav_no3 = M.nav_html(cat, None, three=False)
        self.assertNotIn('aria-current="page"', nav_no3)
        self.assertNotIn('data-motion-toggle', nav_no3)
        self.assertIn('data-theme-toggle', nav_no3)

        nav_home = M.nav_html(cat, 'products', three=True, prefix='./', home=True)
        self.assertNotIn('data-theme-toggle', nav_home)
        self.assertEqual(nav_home.count('data-motion-toggle hidden'), 2)
        self.assertIn('aria-controls="site-products-menu" aria-current="page"', nav_home)
        self.assertIn('<span class="sn-brand" id="sn-drawer-title">', nav_home)

        foot = M.footer_html(data, '\n          <li><a href="https://example.org/mit">MIT</a></li>')
        for snippet in ('href="../demo-arch/&quot;x"', 'Demo &lt;Prod&gt; &amp; Co', ' <span class="sn-badge">Archived</span>', 'https://example.org/mit'):
            self.assertIn(snippet, foot)

    def test_head_html_three_and_plain(self):
        h3 = M.head_html(title='A & "B"', desc='D <"1">', slug='demo-prod', og_img='https://cocoresearch.org/og.png?x=1&y=2',
                         og_alt='Alt "img"', robots='\n<meta name="robots" content="noindex">', jsonld='\n<!--ld-->',
                         three=True, product_id='demo-prod', own_stage=True)
        for snippet in ('<html lang="en" data-product="demo-prod" data-own-stage>', '<title>A &amp; "B"</title>',
                        'content="A &amp; &quot;B&quot;"', 'content="D &lt;&quot;1&quot;&gt;"',
                        'href="https://cocoresearch.org/demo-prod/"', 'prefers-reduced-motion: reduce',
                        'coco-3d-pause:', '<script type="importmap">', M.THREE_URL, 'product-scene.js'):
            self.assertIn(snippet, h3)

        h0 = M.head_html(title='Plain', desc='Desc', slug='plain', og_img=M.DEFAULT_OG, og_alt='Alt', robots='', jsonld='', three=False)
        self.assertIn('<html lang="en">', h0)
        for absent in ('data-product=', 'data-own-stage', 'importmap', 'product-scene.js', 'coco-3d-pause:'):
            self.assertNotIn(absent, h0)
        self.assertIn("d.className += ' js';", h0)
        self.assertIn('site-nav.js', h0)

    def test_li_dl_copy_box_part_head_dir_hero_sec_open_and_stage_page(self):
        data, pub_specs, lab_specs = _sample_fixtures()
        cat = M.build_catalog(data, pub_specs, lab_specs)

        self.assertEqual(M.li_dl(pub_specs['demo-prod']), '            <li><code>demo_1.2.3.dmg</code><span>Mac &lt;ARM&gt; &amp; Intel</span></li>')
        self.assertEqual(M.li_dl(pub_specs['demo-plain']), '')

        box = M.copy_box('Install "Demo"', 'npx demo --flag="1" & echo <ok>')
        self.assertIn('aria-label="Install &quot;Demo&quot;"', box)
        self.assertIn('<code class="install-cmd">npx demo --flag="1" &amp; echo &lt;ok&gt;</code>', box)
        self.assertIn('data-copy="npx demo --flag=&quot;1&quot; &amp; echo &lt;ok&gt;"', box)
        self.assertIn('data-copy-status aria-live="polite"', box)

        ph_no_sub = M.part_head('01', 'A & B', 'Title <1>')
        self.assertIn('id="h-p-01"', ph_no_sub)
        self.assertIn('A &amp; B', ph_no_sub)
        self.assertNotIn('sec-sub', ph_no_sub)
        self.assertIn('<p class="sec-sub">Sub &amp; &lt;note&gt;</p>', M.part_head('02', 'Eye', 'Title', 'Sub & <note>'))

        hero = M.dir_hero(eyebrow='Dir & <1>', h1='<em>All</em>', for_you='For <you>', who_k='Who & why',
                          who='Builders <all>', actions=['<a href="#a">Go</a>'], badges=[('released"x', 'Live & <now>')])
        self.assertIn('<h1 id="h-hero" class="display"><em>All</em></h1>', hero)
        self.assertIn('data-kind="stage" data-stage="released&quot;x">Live &amp; &lt;now&gt;</span>', hero)
        self.assertIn('<p class="p-for-you">For &lt;you&gt;</p>', hero)

        so = M.sec_open('try', '04', 'Try & run', 'Run <it>', 'Detail & more')
        self.assertIn('id="try" class="sec p-part" data-part="04" aria-labelledby="h-try"', so)
        self.assertIn('<h2 id="h-try" class="sec-title">Run &lt;it&gt;</h2>', so)
        self.assertIn('<p class="sec-sub">Detail &amp; more</p>', so)
        self.assertNotIn('sec-sub', M.sec_open('top', '01', 'Eye', 'Head'))

        page = M.stage_page('products', title='Products', desc='All products', jsonld='', hero=hero, body='<p>Body</p>', catalog=cat, data=data)
        for snippet in ('<html lang="en" data-product="products">', '<body data-page="products">', 'href="?motion=off"',
                        'data-page-main="products"', 'aria-controls="site-products-menu" aria-current="page"',
                        M.DIAGRAMS['editions'], '<p>Body</p>'):
            self.assertIn(snippet, page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
