---
name: meta:media
description: Multimodal memory — ingest, embed, and search media (images, video, audio, files) with Gemini Embedding 2 + ChromaDB
trigger: |
  ACTIVATE when:
  - User sends an image, screenshot, file, video, or audio
  - User says "remember this", "save this image", "store this", "log this media"
  - User asks "find that diagram", "search for", "what images do we have", "recall", "media search"
  - User asks to generate an image/diagram and wants it saved
  - Code references a past asset (screenshot, diagram, mockup, recording)
  ALSO proactively query when:
  - User discusses a topic and a past media asset might be relevant
  - User references "that screenshot", "the diagram from last week", etc.
---

# /media-memory — Multimodal Memory System

You have access to a persistent multimodal memory system at `~/.claude/media-memory/`. It stores every piece of media (images, video, audio, files) with rich metadata and Gemini Embedding 2 vectors in ChromaDB.

## Directory Layout
```
~/.claude/media-memory/
  assets/          # stored media files
  chroma/          # ChromaDB vector store
  metadata.db      # SQLite structured metadata
  scripts/
    ingest.py      # ingestion + embedding
    search.py      # search with filters
    schema.py      # metadata models
```

## Commands

All commands run from `~/.claude/media-memory/` using `uv run`.

### Ingest (store + embed)
```bash
cd ~/.claude/media-memory && uv run scripts/ingest.py "<file_path>" \
  --source "user|generated|url|ingested" \
  --description "Natural language description of the media" \
  --tags "tag1,tag2,tag3" \
  --type "image|video|audio|document|file" \
  --text "Extracted text or transcript content"
```

### Search (hybrid: semantic + metadata)
```bash
cd ~/.claude/media-memory && uv run scripts/search.py "search query" \
  --type image \
  --source user \
  --tags "architecture,diagram" \
  --from "2026-03-01" \
  --to "2026-03-28" \
  --limit 10 \
  --mode hybrid|semantic|metadata \
  --json
```

### Recent items
```bash
cd ~/.claude/media-memory && uv run scripts/search.py --recent --limit 10
```

### Stats
```bash
cd ~/.claude/media-memory && uv run scripts/search.py --stats
```

## Behavior Rules

### On Ingest (when user sends or generates media)
1. Copy the file to `assets/` via `ingest.py`
2. ALWAYS provide `--description` with a rich natural language description of the content
3. ALWAYS provide relevant `--tags` for semantic categorization
4. Set `--source` accurately: `user` (user sent it), `generated` (Claude/AI created it), `url` (downloaded), `ingested` (bulk import)
5. For screenshots: describe what's visible (UI elements, text, code, diagrams)
6. For documents: extract key text into `--text`
7. Report the result to the user: "Saved to media memory: {description}"

### On Search (when user asks about past media)
1. Use `--mode hybrid` by default (combines semantic + metadata)
2. Add `--type` filter when user specifies media kind
3. Add `--tags` filter when user mentions categories
4. Add date filters when user references timeframes ("last week", "this month")
5. Show results with descriptions and asset paths
6. Offer to open/display the asset if it's an image

### Proactive Recall
When a conversation topic overlaps with stored media:
1. Run a quick semantic search with the current topic
2. If relevant results found (similarity > 0.7), mention: "I found a related {type} in media memory: {description}"
3. Don't be noisy — only surface genuinely relevant assets

## Environment
- **No API key needed** — uses ChromaDB's built-in local embeddings (all-MiniLM-L6-v2 via onnxruntime)
- Everything runs locally, zero external calls
- ChromaDB: local persistent storage, cosine similarity
- Model cached at `~/.cache/chroma/onnx_models/` (downloaded once on first use)

## Metadata Schema
| Field | Type | Description |
|-------|------|-------------|
| id | string | Auto-generated: `{type}_{hash}_{stem}` |
| filename | string | Original filename |
| type | string | image, video, audio, document, file |
| timestamp | ISO 8601 | When ingested |
| source | string | user, generated, url, ingested |
| description | string | Natural language description |
| extracted_text | string | OCR / transcript / content |
| tags | JSON array | Semantic tags |
| original_path | string | Where it came from |
| asset_path | string | Path in assets/ |
| embedded | boolean | Whether vector is in ChromaDB |
