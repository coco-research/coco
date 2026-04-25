---
name: openai-whisper
description: Speech-to-text transcription via OpenAI Whisper. Supports two modes — Local CLI (no API key, runs on-device) and Cloud API (fast, scalable, requires OPENAI_API_KEY). Use when the user needs to transcribe audio files, translate speech, or convert audio to text.
homepage: https://openai.com/research/whisper
---

# OpenAI Whisper — Speech-to-Text

Transcribe audio files using OpenAI's Whisper model. Two modes available depending on your needs:

| Mode | Latency | Cost | Privacy | Setup |
|------|---------|------|---------|-------|
| Local CLI | Slower (on-device GPU/CPU) | Free | Audio never leaves machine | Install `whisper` binary |
| Cloud API | Fast | Per-minute pricing | Audio sent to OpenAI | `OPENAI_API_KEY` required |

---

## Mode 1: Local CLI

Run Whisper locally with no API key required. Models download to `~/.cache/whisper` on first run.

### Quick Start

```bash
whisper /path/audio.mp3 --model medium --output_format txt --output_dir .
```

### Common Commands

```bash
# Transcribe to text file
whisper /path/audio.mp3 --model medium --output_format txt --output_dir .

# Transcribe with translation to English
whisper /path/audio.m4a --task translate --output_format srt

# Transcribe with specific language
whisper /path/audio.wav --model large --language en --output_format json
```

### Model Selection

| Model | Speed | Accuracy | VRAM |
|-------|-------|----------|------|
| `tiny` | Fastest | Lowest | ~1 GB |
| `base` | Fast | Low | ~1 GB |
| `small` | Medium | Good | ~2 GB |
| `medium` | Slow | Better | ~5 GB |
| `large` | Slowest | Best | ~10 GB |
| `turbo` | Fast | Good (default) | ~6 GB |

### Output Formats

- `txt` — Plain text transcript
- `srt` — SubRip subtitle format with timestamps
- `vtt` — WebVTT subtitle format
- `json` — Detailed JSON with word-level timestamps
- `tsv` — Tab-separated values

### Notes

- `--model` defaults to `turbo` on most installs
- Use smaller models for speed, larger for accuracy
- GPU acceleration used automatically when available

---

## Mode 2: Cloud API

Transcribe via OpenAI's `/v1/audio/transcriptions` endpoint. Faster for large batches, no local GPU needed.

### Quick Start

```bash
{baseDir}/scripts/transcribe.sh /path/to/audio.m4a
```

Defaults:
- Model: `whisper-1`
- Output: `<input>.txt`

### Common Commands

```bash
# Basic transcription
{baseDir}/scripts/transcribe.sh /path/to/audio.m4a

# Specify model and output
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg --model whisper-1 --out /tmp/transcript.txt

# With language hint
{baseDir}/scripts/transcribe.sh /path/to/audio.m4a --language en

# With speaker name hints (improves accuracy)
{baseDir}/scripts/transcribe.sh /path/to/audio.m4a --prompt "Speaker names: Peter, Daniel"

# JSON output with timestamps
{baseDir}/scripts/transcribe.sh /path/to/audio.m4a --json --out /tmp/transcript.json
```

### Raw curl Example

```bash
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F file="@/path/to/audio.m4a" \
  -F model="whisper-1" \
  -F response_format="text"
```

### API Key Setup

Set `OPENAI_API_KEY` environment variable, or configure in `~/.clawdbot/clawdbot.json`:

```json5
{
  skills: {
    "openai-whisper-api": {
      apiKey: "OPENAI_KEY_HERE"
    }
  }
}
```

---

## Choosing Between Modes

| Consideration | Local CLI | Cloud API |
|---------------|-----------|-----------|
| Privacy-sensitive audio | Best | Audio sent to OpenAI |
| Large batch processing | Slow without GPU | Fast and parallel |
| Offline usage | Works offline | Requires internet |
| Cost | Free (hardware cost) | Per-minute pricing |
| Setup complexity | Install binary + models | API key only |
| Audio format support | Most formats | Most formats |
