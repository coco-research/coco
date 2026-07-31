---
name: generate-slides
description: Generate a slide deck as a self-contained HTML page
---

Load the visual-explainer skill and generate a slide deck for: $@

Before writing HTML, read `./templates/slide-deck.html`, `./references/slide-patterns.md`, and only the shared CSS/library sections needed for the source.

Plan the deck first: inventory the source, map every item to slides, choose a narrative arc, and assign a composition to each slide. Use the 10 slide types and nav chrome from `slide-patterns.md`/`slide-deck.html`, including carousel dots, prev/next, slide count, and keyboard controls. Keep each slide to `100dvh`; split dense content across slides rather than scrolling or dropping content.

Use visual-first slides: diagrams, charts, tables, SVG accents, and images from `surf` only when they clarify the story. Vary compositions; three centered slides in a row is a smell.

Write to `~/.agent/diagrams/` and open in the browser.
