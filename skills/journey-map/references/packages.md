# React Flow Package Reference

> **Note:** Migrated from AntV X6 → `@xyflow/react` (React Flow v12). X6 removed entirely.

## Installed Package

| Package | Version | Role |
|---|---|---|
| `@xyflow/react` | ^12.x | Core graph engine — canvas, nodes, edges, pan/zoom/minimap/controls |

## Key Imports

```ts
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type NodeProps,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
```

## Custom Node Pattern

```tsx
// 1. Define component
function MyNode({ data }: { data: MyData }) {
  return <div style={{ width: '100%', height: '100%' }}>...</div>
}

// 2. Register
const nodeTypes = { myNode: MyNode }

// 3. Use in ReactFlow
<ReactFlow nodes={nodes} nodeTypes={nodeTypes} />
```

## Node Object Shape

```ts
{
  id: 'unique-id',
  type: 'myNode',                    // maps to nodeTypes key
  position: { x: 100, y: 200 },
  data: { ...yourData },
  style: { width: 240, height: 200 }, // controls RF layout
  draggable: true,
  selectable: true,
  connectable: false,
  zIndex: 5,
}
```

## Project Structure

```
src/
├── data/journey.ts          ← all data + layout constants
├── nodes/
│   ├── StageHeaderNode.tsx  ← navy stage column header
│   ├── StageNarrNode.tsx    ← dark narrative bar
│   ├── LaneLabelNode.tsx    ← persona label (left col)
│   ├── SwimlaneNode.tsx     ← colored bg band per persona
│   └── TouchpointNode.tsx   ← main card (seq, timing, emoji, badges)
├── utils/buildGraph.ts      ← generates nodes[] from data
├── components/
│   ├── EmotionCurve.tsx     ← SVG curve below canvas
│   └── AdHocFlow.tsx        ← ad-hoc cross-flow section
└── App.tsx                  ← ReactFlowProvider + layout
```

## Layout Constants (from data/journey.ts)

```ts
LABEL_W = 200    // lane label column width
STAGE_W = 240    // each stage column width
GAP     = 8      // gap between cells
HEADER_H = 64    // stage header row height
NARR_H   = 96    // stage narrative row height
LANE_H   = 200   // persona lane height

stageX(n) = LABEL_W + GAP + n * (STAGE_W + GAP)  // x of stage n
laneY(i)  = HEADER_H + GAP + NARR_H + GAP + i * (LANE_H + GAP)  // y of lane i
```

## Peer Dep Note

`@xyflow/react` v12 works cleanly with React 19. No `--legacy-peer-deps` needed.
