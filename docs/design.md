# Design: what it looks and feels like

Two design surfaces live in this repository, and they answer to different rules:

1. **The site** (`index.html`, `coco/index.html`, and the explainer pages). Marketing and
   documentation. Light only, deliberately.
2. **The HTML that skills produce for users.** Every skill that generates a page must satisfy
   the design skills' contracts, including dark mode.

Confusing the two is the most common mistake here. The site wins for the site. The skills win
for skill output. Until this document existed that split was unwritten, which meant a reader
could reasonably conclude either that the site is non-compliant or that skill output may be
light-only.

## 1. The site

### Tokens

Defined once per page in an inline `:root` block, duplicated between `index.html:30-45` and
`coco/index.html:30-45` and byte-identical. There is no shared stylesheet and no CSS build
step.

| Token | Value | Role |
| --- | --- | --- |
| `--ink` | `#14171c` | primary text |
| `--ink-2` | `#333336` | secondary text |
| `--muted` | `#5b6169` | tertiary text, and body copy |
| `--surface` | `#f6f5f2` | the one off-white for tinted sections and the footer |
| `--white` | `#fff` | page ground |
| `--blue` | `#0a3a66` | the accent |
| `--link` | `#0a3a66` | same value, on purpose: one accent throughout |
| `--hair` | `rgba(0,0,0,.10)` | the single hairline |
| `--shadow` | `0 5px 30px rgba(0,0,0,.22)` | the single elevation |
| `--ease` | `cubic-bezier(.4,0,.6,1)` | the single curve |
| `--dur` | `.32s` | the single duration |
| `--stadium` | `100px` | buttons and chips |
| `--wide` | `1024px` | content width |
| `--sans` | `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif` | type family |

**Five colours, one shadow value, one easing curve.** The rationale is written in the file
(`index.html:23-29`): the type scale, spacing and proportions follow the Apple methodology
derived from computed styles ranked by usage, and the accent is deliberately a deep navy
rather than a system blue, to keep the identity distinct.

**Nothing else is tokenised.** Spacing, radii and z-index are literals.

### Typography

Weights are **400 and 600 only**. There is no 500 and no 700 anywhere on the site.

The scale, in px: 80 h1, 56 stat numeral, 48 h2, 38 flagship h2, 28 h3, 24 product h3, 19
eyebrow, 17 body and controls, 15 small feature text, 14 overlay name, 12 fine print, 11
uppercase micro-label.

**Tracking flips sign with size.** This is the one non-obvious typographic rule, and it is
commented once in the source (`coco/index.html:106`). Negative tracking above roughly 40px
(`-.015em` h1, `-.012em` h2, `-.022em` body), positive at and below 28px (`+.007em` h3),
strongly positive on uppercase micro-labels (`+.04em` chips, `+.06em` overlay keys). A label
at 22px with negative tracking will look wrong and the reason will not be obvious from the
markup.

### Shape and depth

Radii on a three-step scale: `14px` media and modal, `18px` tiles and screenshots, `100px`
stadium for buttons and chips. Plus `6px` on focus rings and `2px` on the tab underline.

Depth is one value, `var(--shadow)`, applied to media and to overlays only. Structure is drawn
with one hairline, `1px solid var(--hair)`. **No element carries both a border and a shadow.**

### Motion

One curve, one duration, and only `opacity`, `color` and `transform` are animated. Entrance is
opacity plus a `translateY(14px)` over `.45s`, staggered by index. Hover is opacity only, and
there is no press state.

`prefers-reduced-motion` is honoured in both CSS and JavaScript: the smooth-scroll rule is
gated, panel and reveal animations are gated, and the film's autoplay is skipped, with controls
exposed instead. This is the standard to hold new work to, and it is the rule most often
forgotten because a page looks correct without it.

**Entrance motion is allowed. Continuous motion is not.** No pulse, no glow, no breathing
effect on static content.

### Accessibility

Present: a global `:focus-visible` outline (2px navy, 3px offset) on links, buttons, tabbable
elements and video; complete ARIA tablist semantics with arrow, Home and End keys; a modal with
`role="dialog"`, `aria-modal`, a focus trap, `inert` and `aria-hidden` on the page behind it,
and focus returned to the trigger on close; descriptive `alt` text on every image and an
`aria-label` on every video; 44px touch targets on nav links and close buttons; a `<noscript>`
fallback that reveals the content.

Missing, and worth fixing when the page is next opened: **no skip-to-content link**, **no
`<main>` landmark**, and an empty `aria-label=""` on the nav mark.

### Layout

Fixed breakpoints, not fluid type. `clamp()` appears zero times on either page; there are four
media queries on the site, two for width and two for motion. Mobile reflows grids to one
column, keeps tabs reachable in an overflow scroller, and makes the nav swipeable rather than
hiding destinations.

## 2. Known drift in the site

Recorded rather than silently corrected, because each needs a decision about which side is
right:

- `index.html` and `coco/index.html` diverge on mobile heading sizes: `44/32/20` against
  `48/34/21`.
- Three colours sit outside the token set: `#111` film-modal chrome, `#5b9bd5` as a hero SVG
  gradient stop, and `theme_color: "#0A0F1F"` in `assets/site/site.webmanifest`.
- The site breaks the "no pure white" rule that `skills/design-taste-frontend` mandates, by
  design: `--white` is `#fff`.
- `systems/superintelligence/HOW-IT-WORKS.html` is a third, older style: Tailwind slate values,
  a `#1a73e8` accent, no media queries, no dark mode. It is not covered by the site tokens and
  it is not compliant with the skill contracts either.
- A site redesign is in flight (SpaceX hero direction). Treat this section as the current state,
  not the target.

## 3. HTML that skills produce

Skill output is judged by the design skills, which are opinionated and machine-adjacent. The
load-bearing rules, quoted:

- **`skills/ui-ux-pro-max/SKILL.md:38-47`:** 4.5:1 minimum contrast, visible focus rings,
  `aria-label` on icon-only buttons, 44 by 44px minimum touch targets, 16px minimum body text
  on mobile.
- **`skills/design-taste-frontend/SKILL.md:189`:** "Max 1 accent color. Saturation < 80% by
  default." **`:193`:** once an accent is chosen for a page it is used on the whole page.
  **`:220`:** pick one corner-radius scale for the page and keep it. **`:534-535`:** dark mode
  is mandatory for any consumer-facing page; never ship light-only or dark-only. **`:529`:**
  motion above intensity 3 must honour `prefers-reduced-motion`, non-negotiable. **`:588`:**
  no pure `#000000` and no pure `#ffffff`.
- **`skills/tailwind-patterns/SKILL.md:66`:** use custom properties for the palette, and three
  to five accents at most. **`:68`** bans the default violet and fuchsia accents, cyan plus
  magenta plus purple neon, and gradient-mesh blobs. **`:73-74`:** depth sparingly, hero and
  elevated sections only. **`:104`** is the acceptance test: the styling must still be
  recognisable if compared against a generic dark template.
- **`skills/coco-diagram/SKILL.md:24`** names a different brand default for diagrams: paper
  `#f5f5f5`, ink `#2d3142`, accent magenta `#BE185D`. Diagram output is its own surface and
  should not be forced into the site palette.

Where the design skills and the site disagree, the site wins for the site and the skills win
for generated output. If you are editing a skill that generates HTML, follow the skills.

## 4. What is enforced

**Counts only.** `tests/check-site-counts.py`, invoked by `tests/check-asset-counts.sh` in CI,
regex-matches 17 specific strings across `index.html` and `coco/index.html` against
`docs/asset-counts.json`, including the hero SVG's department array.

That means copy is load-bearing: a headline, subtitle, stat tile or `og:description` that
contains a number is asserted. Rewriting one without updating the checker turns CI red. See
`docs/rules.md` R7.

**Everything else above is convention.** No stylelint, no eslint, no prettier, no htmlhint, no
axe, no pa11y. Colours, tokens, radii, shadows, contrast, alt text, focus styles, dark mode and
reduced motion have no mechanical check. Treat this document as the contract, and treat a
reviewer who cites it as the enforcement.
