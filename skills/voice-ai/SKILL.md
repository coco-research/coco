---
name: voice-ai
description: "Voice AI architecture and implementation guide. Covers two architectures: speech-to-speech (OpenAI Realtime API, lowest latency) and pipeline (STT->LLM->TTS, more control). Includes provider-specific patterns for OpenAI Realtime, Vapi, Deepgram, ElevenLabs, and LiveKit. Use when building voice agents, voice-enabled apps, or real-time conversational AI."
source: vibeship-spawner-skills (Apache 2.0)
---

# Voice AI — Architecture & Implementation

You are a voice AI architect who has shipped production voice agents handling millions of calls. You understand the physics of latency — every component adds milliseconds, and the sum determines whether conversations feel natural or awkward.

## Core Insight: Two Architectures

| Architecture | Latency | Control | Best For |
|-------------|---------|---------|----------|
| Speech-to-Speech (S2S) | Lowest (~200-400ms) | Less controllable | Natural conversation, emotion preservation |
| Pipeline (STT->LLM->TTS) | Higher (~600-1200ms) | Full control at each step | Custom logic, debugging, provider mixing |

---

## Part 1: Architecture Patterns

### Speech-to-Speech Architecture

Direct audio-to-audio processing for lowest latency. Models like OpenAI Realtime API preserve emotion and achieve the most natural conversation flow.

**Strengths:**
- Preserves vocal emotion and nuance
- Lowest end-to-end latency
- Single provider simplicity

**Weaknesses:**
- Less controllable intermediate steps
- Harder to debug
- Provider lock-in

### Pipeline Architecture

Separate STT -> LLM -> TTS for maximum control at each step.

**Strengths:**
- Mix best-in-class providers (Deepgram STT + GPT-4o + ElevenLabs TTS)
- Debug each component independently
- Custom logic between steps (filters, guardrails, logging)

**Weaknesses:**
- Higher cumulative latency
- More integration complexity
- More failure points

### Voice Activity Detection (VAD)

Detect when user starts/stops speaking. Critical for natural turn-taking.

**Key metrics:**
- Silence threshold: 500-1000ms typical
- Prefix padding: 200-300ms to avoid clipping speech start
- Use semantic VAD (context-aware) over silence-only detection

---

## Part 2: Provider Implementation

### OpenAI Realtime API

Native voice-to-voice with GPT-4o. Best for integrated voice AI without separate STT/TTS.

```python
import asyncio
import websockets
import json
import base64

OPENAI_API_KEY = "sk-..."

async def voice_session():
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }

    async with websockets.connect(url, extra_headers=headers) as ws:
        # Configure session
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "alloy",  # alloy, echo, fable, onyx, nova, shimmer
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "get_weather",
                        "description": "Get weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }))

        # Send audio (PCM16, 24kHz, mono)
        async def send_audio(audio_bytes):
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(audio_bytes).decode()
            }))

        # Receive events
        async for message in ws:
            event = json.loads(message)
            if event["type"] == "response.audio.delta":
                # Play audio chunk
                audio_bytes = base64.b64decode(event["delta"])
                # send to speaker...
```

### Vapi Voice Agent

Build voice agents with Vapi platform. Best for phone-based agents and quick deployment.

```python
from flask import Flask, request, jsonify
import vapi

app = Flask(__name__)
client = vapi.Vapi(api_key="...")

# Create an assistant
assistant = client.assistants.create(
    name="Support Agent",
    model={
        "provider": "openai",
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful support agent..."
            }
        ]
    },
    voice={
        "provider": "11labs",
        "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel
    },
    firstMessage="Hi! How can I help you today?",
    transcriber={
        "provider": "deepgram",
        "model": "nova-2"
    }
)

# Webhook for conversation events
@app.route("/vapi/webhook", methods=["POST"])
def vapi_webhook():
    event = request.json

    if event["type"] == "function-call":
        name = event["functionCall"]["name"]
        args = event["functionCall"]["parameters"]
        if name == "check_order":
            result = check_order(args["order_id"])
            return jsonify({"result": result})

    elif event["type"] == "end-of-call-report":
        transcript = event["transcript"]
        save_transcript(event["call"]["id"], transcript)

    return jsonify({"ok": True})

# Start outbound call
call = client.calls.create(
    assistant_id=assistant.id,
    customer={"number": "+1234567890"},
    phoneNumber={"twilioPhoneNumber": "+0987654321"}
)

# Or create web call
web_call = client.calls.create(
    assistant_id=assistant.id,
    type="web"
)
# Returns URL for WebRTC connection
```

### Deepgram STT + ElevenLabs TTS

Best-in-class transcription and synthesis. Use when you want the highest quality custom pipeline.

```python
import asyncio
from deepgram import DeepgramClient, LiveTranscriptionEvents
from elevenlabs import ElevenLabs

# Deepgram real-time transcription
deepgram = DeepgramClient(api_key="...")

async def transcribe_stream(audio_stream):
    connection = deepgram.listen.live.v("1")

    async def on_transcript(result):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            print(f"Heard: {transcript}")
            if result.is_final:
                await handle_user_input(transcript)

    connection.on(LiveTranscriptionEvents.Transcript, on_transcript)

    await connection.start({
        "model": "nova-2",       # Best quality
        "language": "en",
        "smart_format": True,
        "interim_results": True,  # Get partial results
        "utterance_end_ms": 1000,
        "vad_events": True,       # Voice activity detection
        "encoding": "linear16",
        "sample_rate": 16000
    })

    async for chunk in audio_stream:
        await connection.send(chunk)

    await connection.finish()

# ElevenLabs streaming synthesis
eleven = ElevenLabs(api_key="...")

def text_to_speech_stream(text: str):
    """Stream TTS audio chunks."""
    audio_stream = eleven.text_to_speech.convert_as_stream(
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
        model_id="eleven_turbo_v2_5",       # Fastest
        text=text,
        output_format="pcm_24000"           # Raw PCM for low latency
    )
    for chunk in audio_stream:
        yield chunk

# WebSocket for lowest latency TTS
async def tts_websocket(text_stream):
    async with eleven.text_to_speech.stream_async(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_turbo_v2_5"
    ) as tts:
        async for text_chunk in text_stream:
            audio = await tts.send(text_chunk)
            yield audio
        final_audio = await tts.flush()
        yield final_audio
```

---

## Part 3: Latency Optimization

### Latency Budget

Target: **< 800ms** total round-trip for natural conversation feel.

| Component | Target | Notes |
|-----------|--------|-------|
| STT | 100-200ms | Use interim results |
| LLM | 200-400ms | Stream tokens |
| TTS | 100-200ms | Stream audio chunks |
| Network | 50-100ms | Choose nearest region |

### Streaming Everything

The single most important optimization: **stream every component**.

- **STT**: Enable interim results for early processing
- **LLM**: Token streaming to start TTS before LLM finishes
- **TTS**: Chunk streaming to start playback before full synthesis

### Barge-In Detection

Allow users to interrupt the AI mid-response:

1. Use VAD to detect user speech during AI playback
2. Immediately stop TTS playback
3. Clear audio output queue
4. Process the interruption as new input

---

## Anti-Patterns

### Non-Streaming Pipeline
**Why bad**: Adds seconds of latency. User perceives as slow. Loses conversation flow.
**Instead**: Stream everything — STT interim results, LLM token streaming, TTS chunk streaming. Start TTS before LLM finishes.

### Ignoring Interruptions
**Why bad**: Frustrating user experience. Feels like talking to a machine.
**Instead**: Implement barge-in detection. Use VAD to detect user speech. Stop TTS immediately. Clear audio queue.

### Silence-Only Turn Detection
**Why bad**: Misses conversational cues. Cuts off users who pause to think.
**Instead**: Use semantic VAD that considers context, not just silence duration.

### Long Responses
**Why bad**: Voice responses over 2-3 sentences feel like lectures.
**Instead**: Constrain response length in system prompts. Prompt for spoken format (concise, conversational).

### Single Provider Lock-in
**Why bad**: May not be best quality for each component. Single point of failure.
**Instead**: Mix best providers — Deepgram for STT (speed + accuracy), ElevenLabs for TTS (voice quality), OpenAI/Anthropic for LLM.

---

## Sharp Edges

| Issue | Severity | Solution |
|-------|----------|----------|
| Latency exceeds budget | Critical | Measure and budget latency for each component |
| Jitter in response time | High | Target jitter metrics, use buffering |
| Poor turn detection | High | Use semantic VAD with context awareness |
| No barge-in support | High | Implement barge-in detection with VAD |
| Overly long responses | Medium | Constrain response length in prompts |
| Unnatural phrasing | Medium | Prompt for spoken format |
| Background noise issues | Medium | Implement noise handling / filtering |
| STT transcription errors | Medium | Mitigate with prompt hints and context |

---

## Requirements

- Python or Node.js
- API keys for chosen providers
- Audio handling knowledge (PCM, sample rates, encoding)
- WebSocket support for real-time streaming

## Capabilities

- Voice agent architecture design
- Speech-to-speech implementation
- Pipeline (STT->LLM->TTS) implementation
- Voice activity detection
- Turn-taking and barge-in detection
- Latency optimization
- Provider selection and integration

## Related Skills

Works well with: `openai-api`, `openai-agents`, `openai-whisper`, `ai-product`
