#!/usr/bin/env python3
"""Assert .claude-plugin.json last skills/commands claims match customer-facing SSoT."""
import json, re, sys
counts = json.load(open('docs/asset-counts.json'))
skills = str(counts['skills']['total'])
commands = str(counts['commands']['customer_facing'])
shipped = str(counts['commands']['shipped'])
desc = json.load(open('.claude-plugin.json'))['description']
pairs = re.findall(r'(\d+) (skills|commands|agents)', desc)
last = {}
for n, w in pairs:
    last[w] = n
if last.get('commands') == shipped and shipped != commands:
    print(f'FAIL: plugin stamps public commands to shipped files ({shipped}); customer_facing is {commands}')
    sys.exit(1)
if last.get('skills') != skills:
    print(f'FAIL: plugin last skills claim {last.get("skills")}, customer-facing is {skills}')
    sys.exit(1)
if last.get('commands') != commands:
    print(f'FAIL: plugin last commands claim {last.get("commands")}, customer_facing is {commands}')
    sys.exit(1)
print(f'PASS: plugin customer-facing skills={skills} commands={commands}')
