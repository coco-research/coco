# CoCo skill pages

Static pages for public skills on cocoresearch.org. One stylesheet, no JavaScript. A generator fills `skill.template.html`. This folder also holds a filled skill example and a filled Measured skills page.

## Pages

| File | URL | What it is |
|---|---|---|
| `skill.template.html` | `/coco/skills/<name>/` | Slot template. One generated page per skill. |
| `skill.example.html` | — | Same page, filled by hand from `_sample-SKILL.md`. Measured figures are layout samples. |
| `measured.html` | `/coco/skills/measured/` | Held-out scores. The rows in this file are layout samples. |
| `skills.css` | — | Shared styles. Dark by default. Light when `prefers-color-scheme` is light. |

## Slots

| Slot | Holds |
|---|---|
| `{{name}}` | URL slug |
| `{{title}}` | Skill title |
| `{{summary}}` | One sentence. Also the meta description |
| `{{domain}}` | Domain label |
| `{{install}}` | One command line |
| `{{#when}}` … `{{/when}}` | Repeated once per "use it when" item. `{{.}}` is that item |
| `{{source_url}}` | URL of the skill's SKILL.md |
| `{{#measured}}` … `{{/measured}}` | Optional. Omit the whole block when the skill has no score |
| `{{score}}` | Held-out pass rate |
| `{{tasks}}` | Number of held-out tasks |
| `{{run_date}}` | Date of that run |

## How a generator fills them

1. Read that skill's SKILL.md.
2. Copy `skill.template.html`.
3. Escape every value for HTML.
4. Replace each slot. Repeat `{{#when}}<li>{{.}}</li>{{/when}}` once per item, in order.
5. When the skill has a measured run, fill `{{score}}`, `{{tasks}}`, and `{{run_date}}` and remove the measured markers. When it does not, delete the whole `{{#measured}}` block.
6. Write the page to `/coco/skills/<name>/`.
7. Rebuild the Measured skills page from the latest Monday run. One row per measured skill. Set the bar with `style="--v:<score>"` (a number from 0 to 1). Up is `↑` plus the delta, down is `↓` plus the delta, and a flat run is the words `no change`.

## Rules

- No persona or person names.
- No internal team names.
- Only facts from that skill's SKILL.md, or from the measured run.
- The only organisation names on the chrome are CoCo Research and CoCo Super Intelligence.
- measured.html is a layout sample; the published measured page is generated from real run records.
