#!/usr/bin/env python3
"""Unit tests for /aloomannu/ page rendering, spec parity, and no-cloud wording."""
import html
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALOO_HTML = REPO_ROOT / 'aloomannu' / 'index.html'
LAB_SPEC = REPO_ROOT / 'data' / 'product-pages-lab.json'
FORBIDDEN_CAT_LABEL = re.compile(
    r'\b(?:(?:left|right)\s+cat\s+is\s+(?:aloo|mannu)\b|'
    r'(?:aloo|mannu)\s*\((?:left|right|smaller|taller)\)(?!\w))',
    re.I,
)


class AlooMannuPageTest(unittest.TestCase):
    def test_forbidden_cat_label_regex(self):
        for bad in ('Aloo (left) calls', 'Mannu (taller).', 'the left cat is Aloo', 'right cat is Mannu'):
            self.assertIsNotNone(FORBIDDEN_CAT_LABEL.search(bad), bad)
        for clean in ('Named after two cats at home: Aloo Mannu.', 'Aloo (cat) and Mannu play.'):
            self.assertIsNone(FORBIDDEN_CAT_LABEL.search(clean), clean)

    def test_aloomannu_page_and_spec_match_and_enforce_no_cloud(self):
        spec = json.loads(LAB_SPEC.read_text(encoding='utf-8'))['lab']['aloomannu']
        page = ALOO_HTML.read_text(encoding='utf-8')
        spec_dump = json.dumps(spec)

        self.assertIn('No cloud: messages never leave your machine', spec_dump)
        self.assertIn('No cloud: messages never leave your machine', page)
        self.assertIn('<span class="kn-num">No cloud</span>', page)
        self.assertNotIn('no network', spec_dump.lower())
        self.assertNotIn('no network', page.lower())

        for val in (spec['meta_description'], spec['does_for_you'], spec['who_detail'],
                    spec['cats_stage']['tagline'], spec['cats_stage']['story']):
            self.assertIn(html.escape(val, quote=False), page)
        self.assertIn('property="og:image" content="%s"' % html.escape(spec['og_image'], quote=True), page)
        self.assertIn('property="og:image:alt" content="%s"' % html.escape(spec['og_image_alt'], quote=True), page)
        self.assertIn('<meta name="description" content="%s">' % html.escape(spec['meta_description'], quote=True), page)
        for pairs in (spec['does'], spec['status'], spec['kns'], spec['next']):
            for left, right in pairs:
                self.assertIn(html.escape(left, quote=False), page)
                self.assertIn(html.escape(right, quote=False), page)

        for needle in (
            'data-product="aloomannu" data-own-stage>',
            'id="aloo-cats-canvas"',
            'src="../assets/js/aloo-cats-scene.js"',
            'mailto:product@cocoresearch.org',
            'Private, in the lab',
        ):
            self.assertIn(needle, page)
        for absent in ('noindex', 'application/ld+json', 'github.com/coco-research/aloomannu'):
            self.assertNotIn(absent, page)
        pause = re.search(r'<button[^>]*data-cats-motion-toggle[^>]*>', page)
        self.assertIsNotNone(pause)
        self.assertNotIn('aria-pressed', pause.group(0))
        self.assertIsNone(re.search(r'<img\b|\.jpe?g\b', page, re.I))
        self.assertIsNone(FORBIDDEN_CAT_LABEL.search(page))


if __name__ == '__main__':
    unittest.main()
