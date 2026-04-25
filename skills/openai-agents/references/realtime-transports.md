# Realtime Transport Options: WebRTC vs WebSocket

This reference explains the two transport options for realtime voice agents and when to use each.

---

## Overview

OpenAI Agents Realtime SDK supports two transport mechanisms:
1. **WebRTC** (Web Real-Time Communication)
2. **WebSocket** (WebSocket Protocol)

Both enable bidirectional audio streaming, but have different characteristics.

---

## WebRTC Transport

### Characteristics
- **Lower latency**: ~100-200ms typical
- **Better audio quality**: Built-in adaptive bitrate
- **Peer-to-peer optimizations**: Direct media paths when possible
- **Browser-native**: Designed for browser environments

### When to Use
- ✅ Browser-based voice UI
- ✅ Low latency critical (conversational AI)
- ✅ Real-time voice interactions
- ✅ Production voice applications

### Browser Example
```typescript
import { RealtimeSession, RealtimeAgent } from '@openai/agents-realtime';

const voiceAgent = new RealtimeAgent({
  name: 'Voice Assistant',
  instructions: 'You are helpful.',
  voice: 'alloy',
});

const session = new RealtimeSession(voiceAgent, {
  apiKey: sessionApiKey, // From your backend
  transport: 'webrtc', // ← WebRTC
});

await session.connect();
```

### Pros
- Best latency for voice
- Handles network jitter better
- Automatic echo cancellation
- NAT traversal built-in

### Cons
- Requires browser environment (or WebRTC libraries in Node.js)
- Slightly more complex setup
- STUN/TURN servers may be needed for some networks

---

## WebSocket Transport

### Characteristics
- **Slightly higher latency**: ~300-500ms typical
- **Simpler protocol**: Standard WebSocket connection
- **Works anywhere**: Node.js, browser, serverless
- **Easier debugging**: Text-based protocol

### When to Use
- ✅ Node.js server environments
- ✅ Simpler implementation preferred
- ✅ Testing and development
- ✅ Non-latency-critical use cases

### Node.js Example
```typescript
import { RealtimeAgent } from '@openai/agents-realtime';
import { OpenAIRealtimeWebSocket } from '@openai/agents-realtime';

const voiceAgent = new RealtimeAgent({
  name: 'Voice Assistant',
  instructions: 'You are helpful.',
  voice: 'alloy',
});

const transport = new OpenAIRealtimeWebSocket({
  apiKey: process.env.OPENAI_API_KEY,
});

const session = await voiceAgent.createSession({
  transport, // ← WebSocket
});

await session.connect();
```

### Browser Example
```typescript
const session = new RealtimeSession(voiceAgent, {
  apiKey: sessionApiKey,
  transport: 'websocket', // ← WebSocket
});
```

### Pros
- Works in Node.js without extra libraries
- Simpler to debug (Wireshark, browser DevTools)
- More predictable behavior
- Easier proxy/firewall setup

### Cons
- Higher latency than WebRTC
- No built-in jitter buffering
- Manual echo cancellation needed

---

## Comparison Table

| Feature | WebRTC | WebSocket |
|---------|--------|-----------|
| **Latency** | ~100-200ms | ~300-500ms |
| **Audio Quality** | Adaptive bitrate | Fixed bitrate |
| **Browser Support** | Native | Native |
| **Node.js Support** | Requires libraries | Native |
| **Setup Complexity** | Medium | Low |
| **Debugging** | Harder | Easier |
| **Best For** | Production voice UI | Development, Node.js |

---

## Audio I/O Handling

### Automatic (Default)
Both transports handle audio I/O automatically in browser:

```typescript
const session = new RealtimeSession(voiceAgent, {
  transport: 'webrtc', // or 'websocket'
});

// Audio automatically captured from microphone
// Audio automatically played through speakers
await session.connect();
```

### Manual (Advanced)
For custom audio sources/sinks:

```typescript
import { OpenAIRealtimeWebRTC } from '@openai/agents-realtime';

// Custom media stream (e.g., from canvas capture)
const customStream = await navigator.mediaDevices.getDisplayMedia();

const transport = new OpenAIRealtimeWebRTC({
  mediaStream: customStream,
});

const session = await voiceAgent.createSession({
  transport,
});
```

---

## Network Considerations

### WebRTC
- **Firewall**: May require STUN/TURN servers
- **NAT Traversal**: Handles automatically
- **Bandwidth**: Adaptive (300 Kbps typical)
- **Port**: Dynamic (UDP preferred)

### WebSocket
- **Firewall**: Standard HTTPS port (443)
- **NAT Traversal**: Not needed
- **Bandwidth**: ~100 Kbps typical
- **Port**: 443 (wss://) or 80 (ws://)

---

## Security

### WebRTC
- Encrypted by default (DTLS-SRTP)
- Peer identity verification
- Media plane encryption

### WebSocket
- TLS encryption (wss://)
- Standard HTTPS security model

**Both are secure for production use.**

---

## Debugging Tips

### WebRTC
```javascript
// Enable WebRTC debug logs
localStorage.setItem('debug', 'webrtc:*');

// Monitor connection stats
session.transport.getStats().then(stats => {
  console.log('RTT:', stats.roundTripTime);
  console.log('Jitter:', stats.jitter);
});
```

### WebSocket
```javascript
// Monitor WebSocket frames in browser DevTools (Network tab)

// Or programmatically
session.transport.on('message', (data) => {
  console.log('WS message:', data);
});
```

---

## Recommendations

### Production Voice UI (Browser)
```typescript
// Use WebRTC for best latency
transport: 'webrtc'
```

### Backend Processing (Node.js)
```typescript
// Use WebSocket for simplicity
const transport = new OpenAIRealtimeWebSocket({
  apiKey: process.env.OPENAI_API_KEY,
});
```

### Development/Testing
```typescript
// Use WebSocket for easier debugging
transport: 'websocket'
```

### Mobile Apps
```typescript
// Use WebRTC for better quality
// Ensure WebRTC support in your framework
transport: 'webrtc'
```

---

## Migration Between Transports

Switching transports is simple - change one line:

```typescript
// From WebSocket
const session = new RealtimeSession(agent, {
  transport: 'websocket',
});

// To WebRTC (just change transport)
const session = new RealtimeSession(agent, {
  transport: 'webrtc',
});

// Everything else stays the same!
```

---

**Last Updated**: 2025-10-26
**Source**: [OpenAI Agents Docs - Voice Agents](https://openai.github.io/openai-agents-js/guides/voice-agents)
