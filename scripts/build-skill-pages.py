#!/usr/bin/env python3
"""Skill pages, a measured page and a sitemap. stdlib only. --out DIR [--evals DIR]."""
import datetime, hashlib, html, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent.parent.resolve()
PAGES = ROOT / 'scripts' / 'skill-pages'
EVALS = ROOT / 'evals'
SITE, ORIGIN = 'https://cocoresearch.org', 'https://github.com/coco-research/coco'
SOURCE_PREFIX, INSTALL = 'https://github.com/coco-research/', 'npx cocosuperintelligence'
WHEN_LIMIT, WHEN_MAX = 80, 6
_LEAD = r'(Use proactively when|Use this when|Trigger when|Use when)'
_LEADIN_RE = re.compile(rf'(?:(?<=^)|(?<=[.!?;])\s+|(?<=,)\s+){_LEAD}\b\s*:?\s*', re.I)
_LEADIN_START = re.compile(rf'{_LEAD}\b', re.I)
_ABBREV = re.compile(r'(?i)(?:e\.g|i\.e|etc|vs|mr|mrs|dr|st|jr|sr|fig|cf|al)\.$')
_INITIALS = re.compile(r'(?:[A-Za-z]\.){2,}$')
# ponytail: listed word or -ing counts as a verb. Upgrade path: a real tagger.
_VERBS = frozenset('add adapt analyse analyze ask asked audit build catch check click clone commit complete configure convert create debug define delete design detect diagnose discard document edit extract fill find finish finished fix generate get hand help implement inspect install jot keep launch list make map migrate modify move note open optimize plan polish produce promote prune publish read refactor refresh remove render replicate resume review run save scan set ship skip start switch test train translate update verify visualize wait write'.split())
_ING_SKIP = frozenset({'something', 'nothing', 'anything', 'everything', 'during', 'morning'})
_CALLOUT = re.compile(r"(?i)^(?:announce at start\b|version\b|package\b|flags:|arguments:|last updated\b|stop\b|do not read\b|i(?:'m| am) using the .+ skill\b)")
_SLOTS = ('name', 'title', 'summary', 'domain', 'install', 'source_url')
_SLOT_RE, _WHEN_RE = re.compile(r'\{\{([a-z_]+)\}\}'), re.compile(r'\{\{#when\}\}(.*?)\{\{/when\}\}', re.S)
_MEASURED_RE = re.compile(r'[ \t]*\{\{#measured\}\}(.*?)\{\{/measured\}\}\n?', re.S)
_ALLOWED = {'{{name}}', '{{title}}', '{{summary}}', '{{domain}}', '{{install}}', '{{source_url}}', '{{#when}}', '{{/when}}', '{{.}}', '{{#measured}}', '{{/measured}}', '{{score}}', '{{tasks}}', '{{run_date}}'}
MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
_ISO, _SHA256, _RECORD = re.compile(r'\d{4}-\d{2}-\d{2}'), re.compile(r'[0-9a-f]{64}'), '-heldout.json'
_DANGLING = re.compile(r'(?i)\s+(?:for|to|and|or|with|of|in|on|a|an|the|its|their|by|from|as|into|before|after|when|if|not|that|via|per|without|within|about|than|then|so)$')
_PEEL = re.compile(r"^(?:(?:the|a|an)\s+)?(?:user|users|agent|someone|somebody|you)\s+(?:(?:wants|want|asks|ask|needs|need|must|should)\s+)?(?:to\s+)?(?=\S)(.+)$", re.I)
_MACHINE, _STYLES = ('~/', '/Users/', '/home/', 'C:\\'), {'>', '>-', '>+', '|', '|-', '|+'}
_ESC = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\', '/': '/'}
SLUG_WORD_CASING = {'gsd': 'GSD', 'prd': 'PRD', 'ui': 'UI', 'ux': 'UX', 'uat': 'UAT', 'pr': 'PR', 'api': 'API', 'cli': 'CLI', 'ai': 'AI', 'coco': 'Coco'}
TITLE_OVERRIDES = {'officecli': 'OfficeCLI'}
EXTRA_PERSON_NAMES = ('Karpathy',)  # ponytail: rosters miss these; add as reviews find them.

def esc(value): return html.escape(value, quote=True)
def one_line(text): return ' '.join(text.split())

def first_sentence(text):
    """Split only on '. ' before a capital, a digit, or the end. Not '.json', 'e.g.', 'v1.2', 'U.S.'."""
    text, i = one_line(text), 0
    while text:
        idx = text.find('. ', i)
        if idx == -1: return text.strip()
        word, nxt = text[:idx + 1].split()[-1], text[idx + 2:idx + 3]
        if _ABBREV.match(word) or _INITIALS.match(word) or (len(word) >= 2 and word[-2].isdigit() and nxt.isdigit()):
            i = idx + 2
            continue
        if nxt.isupper() or nxt.isdigit() or nxt == '': return text[:idx + 1].strip()
        i = idx + 2
    return ''

def _leadin(text): return bool(_LEADIN_START.match((text or '').strip()))
def _bad_end(text):
    stripped = (text or '').rstrip()
    return (not stripped) or stripped.endswith((',', '...', '…'))
def _done(text): return bool(text) and (text[-1] in '.!?' or text.endswith(('."', ".'")))
def _end_sentence(text):
    text = (text or '').strip()
    return '' if (not text or _bad_end(text)) else (text if _done(text) else text + '.')
def slug_words(slug):
    text = ' '.join(SLUG_WORD_CASING.get(w, w) for w in slug.replace('_', '-').split('-') if w)
    return (text[0].upper() + text[1:]) if text else ''

def title_source(h1, slug):
    """('override'|'h1'|'slug', title). Drop a leading '/' and cut at the first ' — ' or ' - '."""
    if slug in TITLE_OVERRIDES: return 'override', TITLE_OVERRIDES[slug]
    heading = one_line(h1 or '')
    heading = heading[1:] if heading.startswith('/') else heading
    cut = min((c for c in (heading.find(sep) for sep in (' — ', ' - ')) if c != -1), default=len(heading))
    if cut != len(heading): heading = heading[:cut].strip()
    return ('h1', heading) if heading and heading != slug else ('slug', slug_words(slug))

def _body(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---': return '\n'.join(lines[i + 1:])
    return text

def first_h1(body):
    fence = False
    for line in body.splitlines():
        if line.strip().startswith('```'):
            fence = not fence
            continue
        if not fence and line.startswith('# ') and not line.startswith('##'): return one_line(line[2:])
    return ''

def _plain(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', re.sub(r'\*+', '', text))
    return one_line(re.sub(r'`([^`]*)`', r'\1', text))

def _skip_line(line):
    s = line.strip()
    return (not s or s.startswith(('#', '```', '|', '>', '- ', '* ', '+ ', '!`'))
            or bool(re.match(r'\d+\.\s', s) or re.fullmatch(r'[-*]{3,}', s) or re.fullmatch(r'</?[A-Za-z][\w:-]*>', s)))

def paragraph_sentence(body):
    lines = body.splitlines()
    start = next((i + 1 for i, line in enumerate(lines) if line.startswith('# ') and not line.startswith('##')), 0)
    index, end, fence = start, min(len(lines), start + 40), False
    while index < end:
        if lines[index].strip().startswith('```'):
            fence, index = not fence, index + 1
            continue
        if fence or _skip_line(lines[index]):
            index += 1
            continue
        buf = []
        while index < end and lines[index].strip() and not lines[index].strip().startswith('```') and not _skip_line(lines[index]):
            buf.append(lines[index].strip()); index += 1
        sentence = first_sentence(_plain(' '.join(buf)))
        if sentence and not _leadin(sentence) and not _CALLOUT.match(sentence) and _done(sentence): return sentence
    return ''

def later_sentence(description):
    text = one_line(description)
    first = first_sentence(text)
    rest = text[len(first):].strip() if text.startswith(first) else ''
    while rest:
        sentence = first_sentence(rest)
        if sentence and not _leadin(sentence) and not _bad_end(sentence) and _done(sentence): return sentence
        if not sentence or len(sentence) >= len(rest): break
        rest = rest[len(sentence):].strip()
    return ''

def _repair(text):
    cleaned = re.sub(r'(?:\.\.\.|…)+\s*$', '', one_line(text or '')).rstrip().rstrip(',').strip()
    if cleaned and cleaned[-1] not in '.!?' and '. ' in cleaned:
        earlier = first_sentence(cleaned)
        if earlier and earlier[-1] in '.!?' and len(earlier) < len(cleaned): return earlier
    return _end_sentence(cleaned)

def _bad_summary(text):
    text = text or ''
    return text.startswith('You have access') or any(tok in text for tok in _MACHINE)

def summary_source(description, body):
    sentence, paragraph = first_sentence(description), paragraph_sentence(body)
    if sentence and not _leadin(sentence) and not _bad_end(sentence): return _end_sentence(sentence)
    if paragraph and not _bad_end(paragraph): return paragraph
    later = later_sentence(description)
    if later: return later
    for candidate in (paragraph, sentence, description, _LEADIN_RE.sub('', one_line(description))):
        fixed = _repair(candidate)
        if fixed and not _leadin(fixed) and not _bad_end(fixed): return fixed
    return 'This skill ships with Coco.'

def _take_quoted(value, q):
    if not value.startswith(q): return None
    out, i = [], 1
    while i < len(value):
        char = value[i]
        if q == '"' and char == '\\':
            if i + 1 >= len(value): return None
            out.append(_ESC.get(value[i + 1], value[i + 1])); i += 2; continue
        if char == q:
            if q == "'" and i + 1 < len(value) and value[i + 1] == "'":
                out.append("'"); i += 2; continue
            return ''.join(out)
        out.append(char); i += 1
    return None

def _unquote(raw):
    value = raw.strip()
    if value[:1] in '"\'':
        parsed = _take_quoted(value, value[0])
        if parsed is not None: return parsed
    return value.split(' #', 1)[0].rstrip() if ' #' in value else value

def _block_scalar(style, lines):
    indents = [len(line) - len(line.lstrip(' \t')) for line in lines if line.strip()]
    width = min(indents) if indents else 0
    cleaned = ['' if not line.strip() else line[width:] for line in lines]
    while cleaned[:1] == ['']: cleaned.pop(0)
    while cleaned[-1:] == ['']: cleaned.pop()
    if not style.startswith('>'): return '\n'.join(cleaned)
    paragraphs, buf = [], []
    for line in cleaned:
        if line == '' and buf:
            paragraphs.append(' '.join(part.strip() for part in buf)); buf = []
        elif line:
            buf.append(line)
    if buf: paragraphs.append(' '.join(part.strip() for part in buf))
    return '\n\n'.join(paragraphs)

def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---': return {}
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None: return {}
    data, i = {}, 1
    while i < end:
        line = lines[i]
        if not line.strip() or line[0] in ' \t' or line.lstrip().startswith('#') or ':' not in line:
            i += 1; continue
        key, _, rest = line.partition(':')
        key, rest, i = key.strip(), rest.strip(), i + 1
        if rest in _STYLES:
            block = []
            while i < end and (not lines[i].strip() or lines[i][0] in ' \t'):
                block.append(lines[i]); i += 1
            data[key] = _block_scalar(rest, block)
        elif rest == '':
            while i < end and (not lines[i].strip() or lines[i][0] in ' \t'): i += 1
            data[key] = ''
        else:
            data[key] = _unquote(rest)
    return data

def installable_bundles():
    proc = subprocess.run(['bash', str(ROOT / 'scripts' / 'installable-bundles.sh'), '--one-per-line'], check=True, capture_output=True, text=True)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]

def bundle_domains(bundles):
    domains = {'core': 'Core'}
    for bundle in bundles:
        label, pack = bundle, ROOT / 'systems' / bundle / 'pack.json'
        if pack.is_file():
            title = json.loads(pack.read_text(encoding='utf-8')).get('title')
            if title and str(title).strip(): label = one_line(str(title))
        domains[bundle] = label
    return domains

def discover(bundles):
    found, seen = [], {}
    def add(path, bundle):
        slug, rel = path.parent.name, path.relative_to(ROOT).as_posix()
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug): raise SystemExit(f'ERROR: skill directory name is not a page slug: {rel}')
        if slug in seen: raise SystemExit(f'ERROR: two skills share the page name {slug}: {seen[slug]} and {rel}')
        text = path.read_text(encoding='utf-8')
        body = _body(text)
        seen[slug] = rel
        found.append({'slug': slug, 'h1': first_h1(body), 'body': body, 'bundle': bundle, 'rel': rel,
                      'description': one_line(str(parse_frontmatter(text).get('description') or ''))})
    for path in sorted((ROOT / 'skills').glob('*/SKILL.md')):
        if path.is_file(): add(path, 'core')
    for bundle in bundles:
        base = ROOT / 'systems' / bundle
        paths = list(sorted((base / 'skills').glob('*/SKILL.md')))
        paths += sorted(p for p in base.glob('*/SKILL.md') if p.parent.name != 'skills')
        for path in paths:
            if path.is_file(): add(path, bundle)
    return found

def persona_names():
    """Display names from roster.json, plus a capitalised last word of 5+ letters."""
    names = set()
    for path in sorted((ROOT / 'systems' / 'superintelligence').glob('*/roster.json')):
        for person in json.loads(path.read_text(encoding='utf-8')).get('personas') or []:
            display = one_line(person) if isinstance(person, str) else one_line(str(person.get('name') or '')) if isinstance(person, dict) else ''
            if not display: continue
            names.add(display)
            last = display.split()[-1]
            if sum(c.isalpha() for c in last) >= 5 and last[:1].isupper(): names.add(last)
    names.update(EXTRA_PERSON_NAMES)
    return names

def _compiled(names):
    return [(n, re.compile(r'(?<!\w)' + re.escape(n) + r'(?!\w)', re.I)) for n in sorted(names, key=len, reverse=True)]

def matched_name(text, names):
    """First roster name in text, whole word, case-insensitive. Longest wins."""
    if not text or not names: return None
    compiled = names if isinstance(names, list) else _compiled(names)
    return next((name for name, pattern in compiled if pattern.search(text)), None)

def source_url(rel):
    url = f'{ORIGIN}/blob/main/' + '/'.join(quote(part) for part in rel.split('/'))
    if not url.startswith(SOURCE_PREFIX): raise SystemExit(f'ERROR: source URL must start with {SOURCE_PREFIX}')
    return url

def _word(text):
    match = re.match(r"[A-Za-z][A-Za-z'’-]*", text.lstrip(' \t"\'“”‘’'))
    return match.group(0).lower() if match else ''

def starts_with_verb(text):
    word = _word(text)
    return bool(word) and word not in _ING_SKIP and ((len(word) > 4 and word.endswith('ing')) or word in _VERBS)

def _peel(text):
    match = _PEEL.match(text.strip())
    return match.group(1).strip() if match else ''

def _cut_on_verbs(text):
    """Split on ', ' / '; ' / ' or ' only where the next piece starts with a verb."""
    parts, buf, index, quoted = [], [], 0, False
    while index < len(text):
        char = text[index]
        if char == '"':
            quoted, buf, index = not quoted, buf + [char], index + 1
            continue
        delim = next((item for item in (' or ', '; ', ', ') if not quoted and text.startswith(item, index)), None)
        rest = re.sub(r'^(?:or|and)\s+', '', text[index + len(delim):], count=1, flags=re.I) if delim else ''
        if delim and starts_with_verb(rest):
            piece = one_line(''.join(buf)).strip(' ,;')
            if piece: parts.append(piece)
            index += len(delim)
            extra = re.match(r'(?:or|and)\s+', text[index:], flags=re.I)
            buf, index = [], index + (extra.end() if extra else 0)
            continue
        buf.append(char); index += 1
    tail = one_line(''.join(buf)).strip(' ,;')
    return parts + ([tail] if tail else [])

def _split_verbs(clause):
    parts = _cut_on_verbs(clause)
    if parts and not starts_with_verb(parts[0]):
        peeled = _peel(parts[0])
        if not peeled or not starts_with_verb(peeled): return None
        if len(parts) == 1: parts = _cut_on_verbs(peeled)
        else: parts[0] = one_line(peeled).strip(' ,;')
    if not parts or any(not starts_with_verb(part) or len(part) > WHEN_LIMIT for part in parts): return None
    return parts[:WHEN_MAX]

def _close_item(text):
    text = text.rstrip(' ,;')
    while text.count('(') > text.count(')'):
        cut = text.rfind('(')
        if cut <= 0: break
        text = text[:cut].rstrip(' ,;')
    while text.count('"') % 2 == 1:
        cut = text.rfind('"')
        if cut <= 0: break
        text = text[:cut].rstrip(' ,;')
    while True:
        shorter = _DANGLING.sub('', text).rstrip(' ,;—-')
        if shorter == text or not shorter: break
        text = shorter
    return text.strip(' —-')

def _fit80(text):
    text = re.sub(r'^[:\-–—]\s*', '', re.sub(r'(?:\.\.\.|…)+$', '', one_line(text).strip().rstrip('.').strip()).rstrip()).strip()
    if len(text) <= WHEN_LIMIT: return _close_item(text)
    window = text[:WHEN_LIMIT]
    cut = max(window.rfind(mark) for mark in (', ', '; ', ' or ', ' — ', ' -- ', ': '))
    window = window[:cut] if cut >= 12 else (window.rsplit(' ', 1)[0] if ' ' in window else window)
    return _close_item(window) or _close_item(text[:WHEN_LIMIT])

def _cap_item(text):
    """Capitalise the first letter. A leading quote or dot is dropped so the item can start on a letter."""
    text = (text or '').strip()
    if not text or text[0].isupper() or text[0].isdigit(): return text
    if text[0].islower(): return text[0].upper() + text[1:]
    core = (text.replace('"', '') if text.count('"') % 2 == 0 else text).lstrip(' ."\'“”‘’').strip()
    if core[:1].islower(): return core[0].upper() + core[1:]
    return core if core[:1].isupper() or core[:1].isdigit() else text

def when_items(description):
    text = one_line(description)
    match = _LEADIN_RE.search(text)
    clause = first_sentence(text[match.end():]).strip().rstrip('.').strip() if match else ''
    if not clause: return []
    parts = _split_verbs(clause)
    if parts: return [_cap_item(part) for part in parts]
    peeled = _peel(clause)
    used = peeled if peeled and starts_with_verb(peeled) else clause
    item = _cap_item(_fit80(used))
    return [item] if item else []

def present(skill, domains):
    title = title_source(skill['h1'], skill['slug'])[1]
    summary = summary_source(skill['description'], skill['body'])
    if _bad_summary(summary):
        paragraph = paragraph_sentence(skill['body'])
        summary = paragraph if paragraph and not _bad_summary(paragraph) else f'{title} skill for Coco Super Intelligence.'
    return {'slug': skill['slug'], 'name': skill['slug'], 'title': title, 'summary': summary,
            'when': when_items(skill['description']), 'domain': domains.get(skill['bundle'], skill['bundle']),
            'install': INSTALL, 'source_url': source_url(skill['rel']), 'rel': skill['rel']}

def _load(path):
    """Parsed JSON, or None. Records are repo data, but they are still checked before use."""
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError): return None

def _num(value, low=0.0, high=1.0):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high else None

def _count(value): return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None
def _skip(slug, why): print(f'measured skip {slug}: {why}', file=sys.stderr)

def _date(value):
    if not isinstance(value, str) or not _ISO.fullmatch(value): return None
    try: datetime.date.fromisoformat(value)
    except ValueError: return None
    return value

def _rel(path):
    try: return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError: return str(path)

def run_date(iso): return f'{MONTHS[int(iso[5:7]) - 1]} {int(iso[8:10])}'

def skill_record(record):
    """(score, tasks, date) from a held-out skill run, else None. Every field is checked."""
    if not isinstance(record, dict): return None
    score, tasks, date, sha = _num(record.get('mean')), _count(record.get('n')), _date(record.get('date')), record.get('skill_sha256')
    if score is None or tasks is None or date is None or not isinstance(sha, str) or not _SHA256.fullmatch(sha): return None
    return score, tasks, date

def shown_run(evals, skill_dir, slug, sha):
    """Newest kept held-out record for this exact SKILL.md: (file, record), else (None, None)."""
    found = []
    for path in sorted((skill_dir / 'runs').glob('*' + _RECORD)):
        stem, record = path.name[:-len(_RECORD)], _load(path)
        if not isinstance(record, dict) or record.get('split') != 'heldout' or record.get('skill_sha256') != sha: continue
        if stem != 'baseline':
            kept = _load(Path(evals) / 'skills' / '_rounds' / slug / (stem + '.json'))
            if not isinstance(kept, dict) or kept.get('outcome') != 'kept': continue
        found.append((str(record.get('date') or ''), stem != 'baseline', path, record))
    if not found: return None, None
    _, _, path, record = max(found, key=lambda item: (item[0], item[1]))
    return path, record

def measured_rows(evals, skills, kept):
    """One row per measured skill, from committed records. Anything unclear drops the row."""
    by_slug, rows = {skill['slug']: skill for skill in skills}, []
    skills_dir = Path(evals) / 'skills'
    for path in (sorted(skills_dir.iterdir()) if skills_dir.is_dir() else []):
        baseline_path = path / 'runs' / 'baseline-heldout.json'
        if not path.is_dir() or path.name.startswith('_') or not baseline_path.is_file(): continue
        slug, source = path.name, by_slug.get(path.name)
        if source is None: _skip(slug, 'no run for the current SKILL.md'); continue
        run_path, record = shown_run(evals, path, slug, hashlib.sha256((ROOT / source['rel']).read_bytes()).hexdigest())
        if run_path is None: _skip(slug, 'no run for the current SKILL.md'); continue
        baseline, shown = skill_record(_load(baseline_path)), skill_record(record)
        if baseline is None: _skip(slug, f'bad record {_rel(baseline_path)}'); continue
        if shown is None: _skip(slug, f'bad record {_rel(run_path)}'); continue
        rows.append({'slug': slug, 'title': source['title'], 'score': shown[0], 'baseline': baseline[0],
                     'tasks': shown[1], 'date': shown[2], 'model': record.get('model'), 'executor': record.get('executor'),
                     'embed_model': None, 'href': f'/coco/skills/{quote(slug)}/' if slug in kept else None})
    return rows

def router_row(evals):
    """Newest routing record whose top-level split is "descriptions". None when none is usable."""
    runs, best = Path(evals) / 'routing' / 'runs', None
    for path in (sorted(runs.glob('*.json')) if runs.is_dir() else []):
        data = _load(path)
        if not isinstance(data, dict) or data.get('split') != 'descriptions':
            _skip('router', f'not a descriptions-split record {_rel(path)}')
            continue
        if data.get('method') != 'embed':
            _skip('router', f'not an embedding record {_rel(path)}')
            continue
        run = data.get('run')
        if not isinstance(run, dict): continue
        vs = data.get('vs_keyword') if isinstance(data.get('vs_keyword'), dict) else run.get('vs_keyword')
        score = _num(data.get('top1_accuracy'))
        baseline = _num(vs.get('baseline_top1')) if isinstance(vs, dict) else None
        tasks, date = _count(run.get('n_labelled')), _date(run.get('date'))
        if score is None or baseline is None or tasks is None or date is None: _skip('router', f'bad record {_rel(path)}'); continue
        if best is None or (date, path.name) > best[0]:
            embed = run.get('embed_model')
            best = ((date, path.name), {'slug': 'skill-router', 'title': 'Skill router (on descriptions, not names)', 'href': None, 'score': score,
                                        'baseline': baseline, 'tasks': tasks, 'date': date, 'model': None,
                                        'executor': None, 'embed_model': embed if isinstance(embed, str) else None})
    return best[1] if best else None

def _change(score, baseline):
    delta = round(round(score, 2) - round(baseline, 2), 2)
    return ('up', f'↑ {delta:.2f}') if delta > 0 else ('down', f'↓ {-delta:.2f}') if delta < 0 else ('flat', 'no change')

def score_row(row):
    name = f'<a href="{esc(row["href"])}">{esc(row["title"])}</a>' if row['href'] else esc(row['title'])
    score, cls, change = f'{row["score"]:.2f}', *_change(row['score'], row['baseline'])
    return _ROW % (name, score, score, f'{row["baseline"]:.2f}', cls, change, row['tasks'], run_date(row['date']))

def _notes(rows):
    models = sorted({(row['model'], row['executor']) for row in rows
                     if isinstance(row.get('model'), str) and isinstance(row.get('executor'), str)})
    embeds = sorted({row['embed_model'] for row in rows if isinstance(row.get('embed_model'), str)})
    lines = ['      <p class="note">Skill score = mean grader score (0 to 1) on that skill\'s held-out tasks. Baseline = the skill as first measured. Router score = share of held-out descriptions (prompts that never name the team) routed to the right team, compared with keyword matching on the same prompts. Without a local embedding server, the Coco router falls back to the keyword matching shown beside its score, and says so. Tasks and graders are committed in evals/.</p>']
    lines += [f'      <p class="note">Skills scored with {esc(model)} ({esc(executor)}).</p>' for model, executor in models]
    lines += [f'      <p class="note">Router scored with {esc(embed)} embeddings.</p>' for embed in embeds]
    return '\n'.join(lines)

_ROW = ('          <tr>\n            <td class="skill" data-label="Skill">%s</td>\n'
        '            <td data-label="Score">%s<span class="track"><span class="bar" style="--v:%s"></span></span></td>\n'
        '            <td data-label="Baseline">%s</td>\n            <td class="%s" data-label="Change">%s</td>\n'
        '            <td data-label="Tasks">%s</td>\n            <td data-label="Last run">%s</td>\n          </tr>')

def measured_page(template, rows):
    header, footer = _chrome(template, 'header', 'top'), _chrome(template, 'footer', 'foot')
    table = ('      <table class="scores">\n        <thead>\n          <tr>\n'
             '            <th scope="col">Skill</th>\n            <th scope="col">Score</th>\n'
             '            <th scope="col">Baseline</th>\n            <th scope="col">Change</th>\n'
             '            <th scope="col">Tasks</th>\n            <th scope="col">Last run</th>\n'
             '          </tr>\n        </thead>\n        <tbody>\n%s\n        </tbody>\n      </table>')
    body = table % '\n'.join(score_row(row) for row in rows) if rows else '      <p class="empty">No measured skills yet.</p>'
    description = 'Held-out scores for the skills we measure, from the eval runs committed in the repository.'
    page = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '  <title>Measured skills · Coco skills</title>\n'
            f'  <meta name="description" content="{esc(description)}">\n'
            '  <link rel="canonical" href="https://cocoresearch.org/coco/skills/measured/">\n'
            '  <link rel="stylesheet" href="/coco/skills/skills.css">\n</head>\n<body>\n'
            f'  {header}\n  <div class="col">\n    <main>\n      <h1>Measured skills</h1>\n'
            f'      <p class="lede">{esc(description)}</p>\n{body}\n{_notes(rows)}\n    </main>\n'
            f'    {footer}\n  </div>\n</body>\n</html>\n')
    return finish(page, 'coco/skills/measured/index.html')

def load_template():
    text = (PAGES / 'skill.template.html').read_text(encoding='utf-8')
    if text.startswith('<!--'):
        end = text.find('-->')
        if end < 0: raise SystemExit('ERROR: unclosed slot comment in skill template')
        text = text[end + 3:].lstrip('\r\n')
    if not _MEASURED_RE.search(text): raise SystemExit('ERROR: template is missing the {{#measured}} block')
    if 'href="/coco/skills/skills.css"' not in text: raise SystemExit('ERROR: skill template stylesheet must be /coco/skills/skills.css')
    unknown = set(re.findall(r'\{\{[^{}]+\}\}', text)) - _ALLOWED
    if unknown: raise SystemExit('ERROR: template has unexpected slots: ' + ', '.join(sorted(unknown)))
    if not _WHEN_RE.search(text): raise SystemExit('ERROR: template is missing the {{#when}} block')
    return text

def _chrome(template, tag, cls):
    match = re.search(rf'(<{tag} class="{cls}">.*?</{tag}>)', template, re.S)
    if not match: raise SystemExit(f'ERROR: template is missing <{tag} class="{cls}">')
    return match.group(1)

def expand_when(template, items):
    match = _WHEN_RE.search(template)
    if not match: raise SystemExit('ERROR: template is missing the {{#when}} block')
    inner = match.group(1)
    if '{{' in inner and '{{.}}' not in inner: raise SystemExit('ERROR: {{#when}} block has an unexpected slot')
    indent = template[template.rfind('\n', 0, match.start()) + 1:match.start()]
    rendered = ('\n' + indent).join(inner.replace('{{.}}', esc(item)) for item in items)
    return template[:match.start()] + rendered + template[match.end():]

def fill_slots(page, skill):
    values = {key: esc(skill[key]) for key in _SLOTS}
    return _SLOT_RE.sub(lambda m: values.get(m.group(1), m.group(0)), page)

def finish(page, label):
    if '{{' in page: raise SystemExit(f'ERROR: unfilled slot in {label}')
    return page if page.endswith('\n') else page + '\n'

def drop_when(template):
    page, count = re.subn(
        r'[ \t]*<section class="block">\s*<h2>Use it when</h2>\s*<ul class="when">\s*'
        r'\{\{#when\}\}.*?\{\{/when\}\}\s*</ul>\s*</section>\n?', '', template, count=1, flags=re.S)
    if count != 1: raise SystemExit('ERROR: template is missing the Use it when section')
    return page

def skill_page(template, skill, measured=None):
    page = expand_measured(template, measured) if measured else drop_measured(template)
    page = expand_when(page, skill['when']) if skill['when'] else drop_when(page)
    return finish(fill_slots(page, skill), f'coco/skills/{skill["slug"]}/index.html')

def expand_measured(template, row):
    match = _MEASURED_RE.search(template)
    if not match: raise SystemExit('ERROR: template is missing the {{#measured}} block')
    lines = match.group(1).strip('\n').split('\n')
    if lines and not lines[-1].strip(): lines.pop()
    block, values = '\n'.join(lines), {'{{score}}': f'{row["score"]:.2f}', '{{tasks}}': str(row['tasks']), '{{run_date}}': run_date(row['date'])}
    for slot, value in values.items(): block = block.replace(slot, esc(value))
    return template[:match.start()] + block + '\n' + template[match.end():]

def drop_measured(template):
    page, count = re.subn(r'[ \t]*\{\{#measured\}\}.*?\{\{/measured\}\}\n?', '', template, count=1, flags=re.S)
    if count != 1: raise SystemExit('ERROR: template is missing the {{#measured}} block')
    return page

def index_page(template, skills, bundles, domains):
    header, footer = _chrome(template, 'header', 'top'), _chrome(template, 'footer', 'foot')
    groups, order = {}, []
    for bundle in ('core', *bundles):
        label = domains[bundle]
        if label not in groups:
            order.append(label); groups[label] = []
    for skill in skills:
        groups.setdefault(skill['domain'], [])
        if skill['domain'] not in order: order.append(skill['domain'])
        groups[skill['domain']].append(skill)
    sections = []
    for label in order:
        items = groups.get(label) or []
        if not items: continue
        items.sort(key=lambda skill: (skill['title'].casefold(), skill['slug']))
        rows = []
        for skill in items:
            line = f'<a href="{esc("/coco/skills/" + quote(skill["slug"]) + "/")}">{esc(skill["title"])}</a>'
            if skill['summary']: line += f' — {esc(skill["summary"])}'
            rows.append(f'          <li>{line}</li>')
        sections.append(f'      <section class="block">\n        <h2>{esc(label)}</h2>\n        <ul class="when">\n'
                        + '\n'.join(rows) + '\n        </ul>\n      </section>')
    description, body = 'Agent skills that ship with Coco.', '\n'.join(sections)
    page = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <title>Skills · Coco skills</title>\n'
            f'  <meta name="description" content="{esc(description)}">\n'
            '  <link rel="canonical" href="https://cocoresearch.org/coco/skills/">\n'
            '  <link rel="stylesheet" href="/coco/skills/skills.css">\n</head>\n<body>\n'
            f'  {header}\n  <div class="col">\n    <main>\n      <h1>Skills</h1>\n'
            f'      <p class="lede">{esc(description)}</p>\n'
            '      <p class="lede"><a href="/coco/skills/measured/">Measured skills →</a></p>\n'
            f'{body}\n    </main>\n    {footer}\n  </div>\n</body>\n</html>\n')
    return finish(page, 'coco/skills/index.html')

def sitemap(skills):
    locs = [f'{SITE}/', f'{SITE}/coco/', f'{SITE}/coco/skills/', f'{SITE}/coco/skills/measured/'] + [
        f'{SITE}/coco/skills/{quote(s["slug"])}/' for s in sorted(skills, key=lambda i: i['slug'])]
    body = '\n'.join(f'<url><loc>{esc(loc)}</loc></url>' for loc in locs)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '\n</urlset>\n'

def select(skills, names):
    compiled, kept = _compiled(names), []
    for skill in skills:
        fields = (skill['name'], skill['title'], skill['summary'], *skill['when'])
        hit = next((matched_name(field, compiled) for field in fields if matched_name(field, compiled)), None)
        if hit: print(f'skip {skill["slug"]}: {hit}', file=sys.stderr)
        else: kept.append(skill)
    return kept

def write_out(out, files):
    root = Path(out)
    for rel, content in sorted(files.items()):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    css = root / 'coco' / 'skills' / 'skills.css'
    css.write_bytes((PAGES / 'skills.css').read_bytes())

def main(argv):
    if argv == ['--print-names']:
        for name in sorted(persona_names(), key=str.casefold): print(name)
        return 0
    args, out, evals = list(argv), None, str(EVALS)
    while args:
        flag = args.pop(0)
        if flag == '--out' and args: out = args.pop(0)
        elif flag == '--evals' and args: evals = args.pop(0)
        else: out = None; break
    if not out:
        print('usage: python3 scripts/build-skill-pages.py --out DIR [--evals DIR]\n'
              '       python3 scripts/build-skill-pages.py --print-names', file=sys.stderr)
        return 2
    bundles = installable_bundles()
    domains = bundle_domains(bundles)
    skills = [present(skill, domains) for skill in discover(bundles)]
    kept = select(skills, persona_names())
    rows = sorted(measured_rows(evals, skills, {skill['slug'] for skill in kept}), key=lambda row: (row['title'].casefold(), row['slug']))
    router = router_row(evals)
    measured = {row['slug']: row for row in rows}
    template = load_template()
    files = {f'coco/skills/{skill["slug"]}/index.html': skill_page(template, skill, measured.get(skill['slug'])) for skill in kept}
    files['coco/skills/index.html'] = index_page(template, kept, bundles, domains)
    files['coco/skills/measured/index.html'] = measured_page(template, rows + ([router] if router else []))
    files['sitemap.xml'] = sitemap(kept)
    write_out(out, files)
    print(f'wrote {len(kept)} skill pages')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
