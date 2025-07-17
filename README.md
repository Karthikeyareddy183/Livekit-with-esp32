# LiveKit ESP32 Voice Agent

This project connects an ESP32 (or any PCM audio client) to a LiveKit room via a Python gateway, enabling real-time conversation with an AI voice agent powered by Groq LLM, Whisper STT, and PlayAI TTS.

---

## Features

- **ESP32/PCM client** streams audio to a Python gateway.
- **Gateway** forwards audio to a LiveKit room.
- **AI Agent** joins the room, transcribes speech, generates replies, and speaks back.
- **Noise cancellation, VAD, and turn detection** supported.

---

## Installation

1. **Clone the repository:**

   ```sh
   git clone <your-repo-url>
   cd Livekit-with-esp32
   ```

2. **Install dependencies:**

   - using pip:
     ```sh
     pip install -r requirements.txt
     ```

3. **Configure environment:**
   - Copy `.env.example` to `.env` and fill in your LiveKit credentials, or edit `gateway/config.py` directly.

---

## Configuration

- Edit `gateway/config.py` to set your LiveKit URL, API key/secret, room name, etc.
- Make sure your ESP32 or client is configured to send PCM audio to the gateway's WebSocket endpoint.

---

## Running the System

### 1. Start the Gateway

This bridges audio between the ESP32/client and LiveKit.

```sh
python gateway/server.py
```

### 2. Start the AI Agent

To use the turn-detector, silero, or noise-cancellation plugins, you first need to download the model files:

```bash
python agent.py download-files
```

Speak to your agent
Start your agent in console mode to run inside your terminal:

```bash
python agent.py console
```

Start your agent in dev mode to connect it to LiveKit and make it available from anywhere on the internet:

```bash
python agent.py dev
```

### 3. (Optional) Start the Local Client

If you want to test with your PC's microphone instead of an ESP32:

```sh
python gateway/client.py
```

---

## Usage

- The agent will greet you when it joins the room.
- Speak into your microphone (via ESP32 or local client).
- The agent will transcribe, generate a reply, and speak back.

---

## Troubleshooting

- Ensure all components use the same audio sample rate (default: 48000 Hz).
- If the agent does not respond, check logs for audio frame reception and STT output.
- For best results, use a quiet environment and speak clearly.

---

## File Structure

```
agent/
  agent.py         # AI agent code
gateway/
  server.py        # Gateway server (ESP32 <-> LiveKit)
  client.py        # Local test client (mic <-> LiveKit)
  config.py        # Configuration
```

---
