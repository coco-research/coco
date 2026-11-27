#!/usr/bin/env python3
"""Unit tests for the Aloo Mannu page, no-cloud privacy wording, and banner generator."""
import html
import importlib.util
import json
import re
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'assets' / 'js' / 'render-aloo-banners.py'
ALOO_HTML = REPO_ROOT / 'aloomannu' / 'index.html'
LAB_SPEC = REPO_ROOT / 'data' / 'product-pages-lab.json'
README_PNG = REPO_ROOT / 'aloomannu' / 'banner-readme.png'
SOCIAL_PNG = REPO_ROOT / 'aloomannu' / 'social-preview-1280x640.png'
FORBIDDEN_BYTES = re.compile(b'(?:/' + b'Users/|/home/|/private/var/folders/)', re.I)
FORBIDDEN_CAT_LABEL = re.compile(
    r'\b(?:left\s+cat\s+is\s+(?:aloo|mannu)|right\s+cat\s+is\s+(?:aloo|mannu)|'
    r'aloo\s*\((?:left|right|smaller|taller)\)|mannu\s*\((?:left|right|smaller|taller)\))\b',
    re.I,
)


def _load_mod():
    spec = importlib.util.spec_from_file_location('render_aloo_banners', SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _load_mod()


def _chunk(ctype, body):
    crc = zlib.crc32(ctype + body) & 0xFFFFFFFF
    return struct.pack('>I', len(body)) + ctype + body + struct.pack('>I', crc)


def _make_png(width, height, extra_chunks=(), include_iend=True):
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00' + b'\x00\x00\x00' * width)
    parts = [M.PNG_SIG, _chunk(b'IHDR', ihdr), *extra_chunks, _chunk(b'IDAT', idat)]
    if include_iend:
        parts.append(_chunk(b'IEND', b''))
    return b''.join(parts)


def _list_chunks(raw):
    assert raw[:8] == M.PNG_SIG
    pos, w, h, chunks = 8, 0, 0, []
    while pos + 8 <= len(raw):
        length = struct.unpack('>I', raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        body = raw[pos + 8:pos + 8 + length]
        chunks.append(ctype)
        if ctype == b'IHDR' and len(body) >= 8:
            w, h = struct.unpack('>II', body[:8])
        pos += 12 + length
        if ctype == b'IEND':
            break
    return w, h, chunks


class AlooBannersAndPageTest(unittest.TestCase):
    def test_strip_png_metadata_strips_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'sample.png'
            raw = _make_png(16, 12, extra_chunks=(_chunk(b'tEXt', b'Author\x00secret'), _chunk(b'pHYs', b'\x00' * 9)))
            p.write_bytes(raw)
            w, h, nbytes = M.strip_png_metadata(p)
            self.assertEqual((w, h), (16, 12))
            self.assertLess(nbytes, len(raw))
            w2, h2, chunks = _list_chunks(p.read_bytes())
            self.assertEqual((w2, h2), (16, 12))
            self.assertEqual(chunks, [b'IHDR', b'IDAT', b'IEND'])

            bad = Path(tmp) / 'bad.png'
            bad.write_bytes(b'not a png')
            with self.assertRaises(ValueError):
                M.strip_png_metadata(bad)

            trunc = Path(tmp) / 'trunc.png'
            ihdr = _chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0))
            trunc.write_bytes(M.PNG_SIG + ihdr + struct.pack('>I', 10) + b'IEND' + b'\x00' * 4)
            with self.assertRaisesRegex(ValueError, 'truncated'):
                M.strip_png_metadata(trunc)

            no_iend = Path(tmp) / 'no_iend.png'
            no_iend.write_bytes(_make_png(8, 8, include_iend=False))
            with self.assertRaisesRegex(ValueError, 'IHDR or IEND'):
                M.strip_png_metadata(no_iend)

            big = Path(tmp) / 'big.png'
            big.write_bytes(M.PNG_SIG + ihdr + _chunk(b'IDAT', b'\x00' * 1_000_050) + _chunk(b'IEND', b''))
            with self.assertRaisesRegex(ValueError, '1 MB'):
                M.strip_png_metadata(big)

    def test_write_readme_preview_html_escapes_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'preview.html'
            M.write_readme_preview_html(out, 'a"b<c>.png')
            txt = out.read_text(encoding='utf-8')
            self.assertIn('src="a&quot;b&lt;c&gt;.png"', txt)
            self.assertNotIn('No network', txt)

    def test_shipped_banner_pngs_clean_and_exact_dimensions(self):
        for path, expected in ((README_PNG, (1280, 560)), (SOCIAL_PNG, (1280, 640))):
            self.assertTrue(path.is_file(), str(path))
            raw = path.read_bytes()
            self.assertGreater(len(raw), 0)
            self.assertLess(len(raw), 1_000_000)
            w, h, chunks = _list_chunks(raw)
            self.assertEqual((w, h), expected)
            self.assertTrue(set(chunks).issubset(M.KEEP_CHUNKS), f'unexpected chunks in {path.name}: {set(chunks)}')
            self.assertIsNone(FORBIDDEN_BYTES.search(raw))

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
        self.assertIn(html.escape(spec['og_image'], quote=True), page)
        self.assertIn(html.escape(spec['og_image_alt'], quote=True), page)
        for pairs in (spec['does'], spec['status'], spec['kns'], spec['next']):
            for left, right in pairs:
                self.assertIn(html.escape(left, quote=False), page)
                self.assertIn(html.escape(right, quote=False), page)

        for needle in (
            'data-product="aloomannu" data-own-stage>',
            'id="aloo-cats-canvas"',
            'src="../assets/js/aloo-cats-scene.js"',
            'mailto:product@cocoresearch.org',
        ):
            self.assertIn(needle, page)
        self.assertNotIn('application/ld+json', page)
        pause = re.search(r'<button[^>]*data-cats-motion-toggle[^>]*>', page)
        self.assertIsNotNone(pause)
        self.assertNotIn('aria-pressed', pause.group(0))
        self.assertIsNone(re.search(r'<img\b|\.jpe?g\b', page, re.I))
        self.assertIsNone(FORBIDDEN_CAT_LABEL.search(page))


if __name__ == '__main__':
    unittest.main()
