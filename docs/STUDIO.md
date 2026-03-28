# CoCo Studio Features

Studio is the premium tier of CoCo Platform. It adds voice, AI generation, and advanced analytics features on top of the free Core edition.

## Enabling Studio

```bash
export COCO_EDITION=studio
# Or add to .env file
```

## Features

### Jarvis Voice Assistant
Cinematic voice overlay with health ring, reactive canvas, and briefing sequences. Activated from the Home page or via voice command.

### Text-to-Speech (Kokoro)
Local TTS engine using the Kokoro 82M-parameter model. Content-addressed caching, 4 voice options. No API key needed.

### Speech-to-Text (Deepgram)
Real-time transcription via Deepgram API. Requires `DEEPGRAM_API_KEY`.

### Agent Replay
Generates shareable HTML time-lapse files from agent sessions. View the full conversation, tool calls, and file changes.

### Morning Podcast
Auto-generated 2-3 minute audio briefing of overnight activity across all projects.

### Self-Improvement
Agents that analyze the platform's own codebase and suggest improvements. Runs in git worktree isolation with verification gates.

### Folder Analysis
Deep analysis pipeline for document folders — extracts entities, relationships, and insights.

## License

Studio features are licensed under BSL 1.1. On March 28, 2029, they convert to MIT. See [LICENSE-STUDIO](../LICENSE-STUDIO).
