"""Grader for the c4-architecture pilot. Deterministic: no model calls, no network.

grade(item, output) scores the Mermaid diagram in a model reply against the system
described in the item. Each ```mermaid block is scored and the best one counts.

    C4 syntax   score = 0.2 * valid + 0.4 * containers + 0.4 * relations
    flowchart   score = min(0.7, 0.4 * containers + 0.4 * relations)

No mermaid block scores 0.

valid         The block opens with a C4 keyword (C4Context, C4Container, C4Component,
              C4Dynamic or C4Deployment), braces balance, it has at least one element
              and one relationship, and every relationship ends at a defined element.
              A boundary or deployment node is not an element: Mermaid cannot draw a
              relationship to one.
containers    Fraction of the item's containers matched to an element label. Matching
              ignores case and punctuation. An exact label wins first, then a substring
              either way (the shorter side at least 4 characters). One label serves one
              container, so a single catch-all element cannot stand in for several.
              Person elements never match: a person is not a container.
relations     Fraction of the item's [A, B] pairs joined by a relationship between the
              elements matched to A and B, in either direction. Extra elements and
              relationships cost nothing.

C4 elements are Person, System, Container and Component, with the Db, Queue and _Ext
variants. Relationships are Rel, BiRel and Rel_*. A block that opens with a C4 keyword,
or defines any C4 element, is graded as C4. Anything else (a flowchart, say) is read for
node labels and --> style edges and capped at 0.7.

Only the first 200,000 characters of a reply, and the first 500 of each diagram line, are read.
"""
import re

W_VALID, W_CONTAINERS, W_RELATIONS, FLOWCHART_CAP = 0.2, 0.4, 0.4, 0.7
MAX_CHARS, MAX_LINE = 200_000, 500  # bounds the work a runaway reply can cause

_FENCE = re.compile(r"```[ \t]*mermaid[^\n]*\n(.*?)(?:```|\Z)", re.S | re.I)
_FRONTMATTER = re.compile(r"\A\s*---[ \t]*\n.*?\n---[ \t]*(?:\n|\Z)", re.S)
_C4_KEYWORDS = {"C4Context", "C4Container", "C4Component", "C4Dynamic", "C4Deployment"}
_ELEMENT = re.compile(
    r"\s*(Person|System|Container|Component)(?:Db|Queue)?(?:_Ext)?\s*\(\s*"
    r"[\"']?([\w.-]+)[\"']?\s*,\s*(?:\"((?:[^\"\\]|\\.)*)\"|([^,)\n]*))")
_GROUP = re.compile(r"\s*(?:\w*Boundary|Deployment_Node|Node(?:_[LR])?)\s*\(\s*[\"']?([\w.-]+)")
_REL = re.compile(
    r"\s*(?:Bi)?Rel(?:_\w+)?\s*\(\s*[\"']?([\w.-]+)[\"']?\s*,\s*[\"']?([\w.-]+)[\"']?\s*[,)]")
# Flowchart edges: --> --- -.-> ==> --o --x, with an optional |label| or edge text
# ("-- text -->", "--text-->", "-. text .->", "== text ==>").
_ARROW = re.compile(
    r"<?(?:--[ \t]+[^\n]{1,60}?[ \t]+--+[>ox]?"
    r"|--(?=[^\s>-])\S{1,40}?--+[>ox]?"
    r"|-\.[ \t]+[^\n]{1,60}?[ \t]+\.-+[>ox]?"
    r"|==[ \t]+[^\n]{1,60}?[ \t]+==+[>ox]?"
    r"|-\.+-*[>ox]?|==+[>ox]?|--+[>ox]?)(?:[ \t]*\|[^|\n]*\|)?")
_NODE = re.compile(r"\s*([\w-]+)\s*(?:[\[({>]+\s*(.*?)\s*[\])}]+)?(?::::\w+)?\s*$")
_FLOW_SKIP = re.compile(r"(?:graph|flowchart|subgraph|end|classdef|class|style|linkstyle|click|direction)\b", re.I)


def _key(s):
    return " ".join(re.sub(r"[\W_]+", " ", s.lower()).split())


def _lines(block):
    block = _FRONTMATTER.sub("", block, count=1)
    return [l[:MAX_LINE] for l in block.splitlines() if l.strip() and not l.strip().startswith("%%")]


def _c4(lines):
    """Return (labels {alias: label}, persons {alias}, relationships [(from, to)], groups {alias})."""
    labels, persons, rels, groups = {}, set(), [], set()
    for line in lines:
        m = _ELEMENT.match(line)
        if m:
            labels[m.group(2)] = (m.group(3) if m.group(3) is not None else m.group(4)).strip()
            (persons.add if m.group(1) == "Person" else persons.discard)(m.group(2))
            continue
        m = _GROUP.match(line)
        if m:
            groups.add(m.group(1))
            continue
        m = _REL.match(line)
        if m:
            rels.append((m.group(1), m.group(2)))
    return labels, persons, rels, groups


def _problems(lines, labels, rels, groups):
    """Why the block would not render as C4."""
    code = "\n".join(lines)
    ends = {a for pair in rels for a in pair}
    onto = sorted(a for a in ends if a in groups and a not in labels)
    ghost = sorted(a for a in ends if a not in labels and a not in groups)
    return [p for ok, p in (
        (not lines or lines[0].split()[0] not in _C4_KEYWORDS, "does not open with a C4 keyword"),
        (code.count("{") != code.count("}"), "unbalanced braces"),
        (not labels or not rels, "needs at least one element and one relationship"),
        (onto, "relationship ends at a boundary or node, which cannot take one: " + ", ".join(onto)),
        (ghost, "relationship names an undefined alias: " + ", ".join(ghost)),
    ) if ok]


def _edges(stmt):
    """Split a flowchart statement into groups of node texts at top-level arrows and ampersands."""
    groups, group, buf, depth, i = [], [], "", 0, 0
    while i < len(stmt):
        depth = max(0, depth + (stmt[i] in "[({") - (stmt[i] in "])}"))
        m = _ARROW.match(stmt, i) if depth == 0 else None
        if m:
            groups.append(group + [buf])
            group, buf, i = [], "", m.end()
        elif stmt[i] == "&" and depth == 0:
            group.append(buf)
            buf, i = "", i + 1
        else:
            buf += stmt[i]
            i += 1
    groups.append(group + [buf])
    return groups


def _flowchart(lines):
    """Return (nodes {id: label}, edges [(from, to)]) read from a flowchart-style block."""
    nodes, edges = {}, []
    for line in lines:
        for stmt in line.split(";"):
            if _FLOW_SKIP.match(stmt.strip()):
                continue
            prev = None
            for parts in _edges(stmt):
                ids = []
                for part in parts:
                    m = _NODE.match(part)
                    if m:
                        label = (m.group(2) or "").strip().strip("\"'`/\\") or None
                        nodes[m.group(1)] = label or nodes.get(m.group(1), m.group(1))
                        ids.append(m.group(1))
                if prev is not None:
                    edges += [(a, b) for a in prev for b in ids]
                prev = ids
    return nodes, edges


def _match(names, labels):
    """Map each name to the set of ids whose label matches it. One label serves one name.

    ponytail: words are compared, not meaning, so a renamed container ("Farms Database"
    for "Farms DB") is missed. Upgrade path: an accepted-labels list on each item.
    """
    by_key = {}
    for ident, label in labels.items():
        if _key(label):
            by_key.setdefault(_key(label), set()).add(ident)
    taken, got = set(), {}
    for exact in (True, False):
        for name in names:
            n = _key(name)
            if name in got or not n:
                continue
            for k in by_key:
                if k not in taken and (k == n if exact else min(len(n), len(k)) >= 4 and (n in k or k in n)):
                    taken.add(k)
                    got[name] = by_key[k]
                    break
    return got


def _grade_block(item, block):
    lines = _lines(block)
    labels, persons, rels, groups = _c4(lines)
    is_c4 = bool(labels) or (bool(lines) and lines[0].split()[0] in _C4_KEYWORDS)
    if is_c4:
        problems = _problems(lines, labels, rels, groups)
        nodes = {alias: label for alias, label in labels.items() if alias not in persons}
    else:
        problems = []
        nodes, rels = _flowchart(lines)
    names, wanted = item["containers"], item["relations"]
    got = _match(names, nodes)
    joined = {frozenset(p) for p in rels}
    linked = [
        pair for pair in wanted
        if any(frozenset((x, y)) in joined for x in got.get(pair[0], ()) for y in got.get(pair[1], ()))
    ]
    c_frac = len(got) / len(names) if names else 1.0
    r_frac = len(linked) / len(wanted) if wanted else 1.0
    notes = []
    if is_c4:
        raw = W_VALID * (0.0 if problems else 1.0) + W_CONTAINERS * c_frac + W_RELATIONS * r_frac
        notes += ["C4 block problem: " + p for p in problems]
    else:
        raw = min(FLOWCHART_CAP, W_CONTAINERS * c_frac + W_RELATIONS * r_frac)
        notes.append("not C4 syntax: read as a flowchart, score capped at %.1f" % FLOWCHART_CAP)
    lost = [n for n in names if n not in got]
    if lost:
        notes.append("containers found %d/%d, missing: %s" % (len(got), len(names), "; ".join(lost)))
    unlinked = [" -> ".join(p) for p in wanted if p not in linked]
    if unlinked:
        notes.append("relations found %d/%d, missing: %s" % (len(linked), len(wanted), "; ".join(unlinked)))
    return {"score": round(min(1.0, max(0.0, raw)), 4), "notes": notes}


def grade(item, output):
    output = (output if isinstance(output, str) else "")[:MAX_CHARS]
    blocks = _FENCE.findall(output.replace("\r\n", "\n"))
    if not blocks:
        return {"score": 0.0, "notes": ["no mermaid block"]}
    return max((_grade_block(item, b) for b in blocks), key=lambda r: r["score"])
