export interface DeepgramConfig {
  available: boolean;
  provider: string;
  websocket_url: string | null;
  config: {
    model: string;
    language: string;
    smart_format: boolean;
    interim_results: boolean;
    utterance_end_ms: number;
  } | null;
}

export interface DeepgramTokenResponse {
  token: string;
  websocket_url: string;
  config: {
    model: string;
    language: string;
    smart_format: boolean;
    interim_results: boolean;
    utterance_end_ms: number;
  };
}

export class DeepgramClient {
  private ws: WebSocket | null = null;
  private mediaRecorder: MediaRecorder | null = null;

  async isAvailable(): Promise<boolean> {
    try {
      const res = await fetch('/api/stt/config');
      if (!res.ok) return false;
      const data: DeepgramConfig = await res.json();
      return data.available;
    } catch {
      return false;
    }
  }

  async start(onTranscript: (text: string, isFinal: boolean) => void): Promise<void> {
    const tokenRes = await fetch('/api/stt/token', { method: 'POST' });
    if (!tokenRes.ok) throw new Error('STT unavailable');
    const { token, websocket_url, config }: DeepgramTokenResponse =
      await tokenRes.json();

    const params = new URLSearchParams({
      model: config.model,
      language: config.language,
      smart_format: String(config.smart_format),
      interim_results: String(config.interim_results),
      utterance_end_ms: String(config.utterance_end_ms),
    });

    this.ws = new WebSocket(`${websocket_url}?${params}`, ['token', token]);

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.channel?.alternatives?.[0]) {
          const transcript: string = data.channel.alternatives[0].transcript;
          const isFinal: boolean = data.is_final ?? false;
          if (transcript) onTranscript(transcript, isFinal);
        }
      } catch {
        // ignore malformed messages
      }
    };

    // Wait for WebSocket to open before starting mic
    await new Promise<void>((resolve, reject) => {
      if (!this.ws) return reject(new Error('WebSocket not created'));
      this.ws.onopen = () => resolve();
      this.ws.onerror = () => reject(new Error('WebSocket connection failed'));
    });

    // Start microphone capture
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    this.mediaRecorder.ondataavailable = (e: BlobEvent) => {
      if (this.ws?.readyState === WebSocket.OPEN && e.data.size > 0) {
        this.ws.send(e.data);
      }
    };
    this.mediaRecorder.start(250); // 250ms chunks
  }

  stop(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.mediaRecorder?.stream.getTracks().forEach((t) => t.stop());
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Send close message per Deepgram protocol
      this.ws.send(JSON.stringify({ type: 'CloseStream' }));
    }
    this.ws?.close();
    this.ws = null;
    this.mediaRecorder = null;
  }
}
