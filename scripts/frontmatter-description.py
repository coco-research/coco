#!/usr/bin/env python3
"""Render a YAML frontmatter string description as one catalog line (stdlib)."""
import json
from pathlib import Path
import re
import sys


def description(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or lines[0].strip() != '---':
        return ''
    for index, line in enumerate(lines[1:], 1):
        if line.strip() in ('---', '...'):
            break
        if not line.startswith('description:'):
            continue
        value = line.split(':', 1)[1].strip()
        if re.fullmatch(r'[|>](?:[1-9][+-]?|[+-][1-9]?)?(?:\s+#.*)?', value):
            body = []
            for following in lines[index + 1:]:
                if following and not following[0].isspace():
                    break
                body.append(following.strip())
            value = ' '.join(body)
        elif value.startswith('"'):
            value = json.JSONDecoder().raw_decode(value)[0]
        elif value.startswith("'"):
            match = re.match(r"'((?:[^']|'')*)'", value)
            value = match.group(1).replace("''", "'") if match else ''
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0]
        return ' '.join(str(value).split())
    return ''


if __name__ == '__main__':
    print(description(Path(sys.argv[1])))
