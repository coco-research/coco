---
name: journey-map
description: >
  Loads full context for a React Flow (@xyflow/react) user journey mapping
  project. Use when working on, extending, debugging, or building features for
  the journey map tool. Triggers on: "journey map project", "open journey map",
  "work on journey map", "build user journey", "react flow journey project",
  "journey-map app", or any request to add features like swimlanes,
  emotion curves, persona nodes, touchpoints, or pain point markers.
---

# Journey Map Project

## Project

- **Locating it:** this skill does not assume a fixed install path. See
  "Locating the Project" below before running any commands.
- **Stack:** React 19 + Vite + TypeScript + `@xyflow/react` (React Flow v12)
- **Purpose:** Rich user journey map tool for PMs and UX researchers

## Locating the Project

Before making changes, find the project root:

1. If the user gives a path, use it.
2. Otherwise search common locations, e.g.:
   ```bash
   find "$HOME" -maxdepth 5 -iname "journey-map" -type d 2>/dev/null
   ```
3. If nothing is found, ask the user where the project lives.

## Dev Commands

Run from the project root located above:

```bash
npm run dev      # start dev server (Vite)
npm run build    # production build
npm run preview  # preview build
```

## Stack

Single package: `@xyflow/react` (React Flow v12). There is no AntV X6
dependency — the project fully migrated off X6, and no `--legacy-peer-deps`
flag is needed on React 19.

See `references/packages.md` for imports, node pattern, layout constants, file structure.

## Implemented Features

| Feature | Mechanism |
|---|---|
| Swimlanes (persona rows) | `swimlaneBg` node type — wide colored band, zIndex=0 |
| Stage headers + narratives | `stageHeader` / `stageNarr` node types |
| Touchpoint cards | `touchpoint` node — seq badge, timing chip, emoji, title, badges |
| Emotion curve | `EmotionCurve.tsx` SVG component below canvas |
| Ad-hoc cross-flow | `AdHocFlow.tsx` component below canvas |
| Pan + zoom | React Flow built-in |
| Minimap | React Flow `<MiniMap>` |
| Controls | React Flow `<Controls>` |
| Persona focus/dim | `focusPersona` state → opacity on non-focused touchpoints |
| Detail panel | Click touchpoint → slide-in right panel |

## References

- Full package list + versions + plugin roles: `references/packages.md`
- React Flow (MIT licensed, https://github.com/xyflow/xyflow) is the only
  graph engine this project uses.
