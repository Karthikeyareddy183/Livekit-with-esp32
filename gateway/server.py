# server.py  (complete, fixed gateway using livekit-rtc)
import asyncio
from collections import deque
from fastapi import FastAPI, WebSocket
from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from config import (
    LIVEKIT_WS_URL,
    LK_API_KEY,
    LK_API_SECRET,
    ROOM_NAME,
    GATEWAY_PORT,
    ESP32_WS_PATH,
)

app = FastAPI()

# Opus codecs are unused in this path; we forward raw PCM 48 kHz mono.
FRAME_BYTES = 960 * 2          # 960 samples × 2 bytes/sample = 1920 bytes


@app.websocket(ESP32_WS_PATH)
async def esp32_ws(ws: WebSocket):
    await ws.accept()
    print("✅ ESP32 connected")

    # 1. Token for the gateway participant
    token = (
        AccessToken(LK_API_KEY, LK_API_SECRET)
        .with_identity("esp32-gateway")
        .with_grants(VideoGrants(room_join=True, room=ROOM_NAME))
        .to_jwt()
    )

    # 2. Connect to LiveKit via WebRTC
    room = rtc.Room()
    await room.connect(LIVEKIT_WS_URL, token)
    print("→ RTC connected to LiveKit")

    # 3. Publish a microphone track so the agent can hear the ESP32
    source = rtc.AudioSource(48000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("esp32-mic", source)
    await room.local_participant.publish_track(track)

    # 4. Buffer incoming raw PCM and forward in 20 ms chunks
    buf = bytearray()

    async def from_esp32():
        nonlocal buf
        async for pcm_bytes in ws.iter_bytes():
            buf.extend(pcm_bytes)
            while len(buf) >= FRAME_BYTES:
                frame_data = buf[:FRAME_BYTES]
                buf = buf[FRAME_BYTES:]
                # print("forwarding frame", len(frame_data))
                frame = rtc.AudioFrame(
                    data=bytes(frame_data),
                    sample_rate=48000,
                    num_channels=1,
                    samples_per_channel=960,
                )
                await source.capture_frame(frame)

    # 5. Pump agent audio from LiveKit → client
    async def to_esp32():
        print("Waiting for remote audio track...")
        while True:
            for participant in room.remote_participants.values():
                for pub in participant.track_publications.values():
                    if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.track:
                        pub.set_subscribed(True)
                        stream = rtc.AudioStream(pub.track)
                        print("Found remote audio track, starting playback")
                        async for event in stream:
                            await ws.send_bytes(event.frame.data.tobytes())
                        return  # track ended / agent left
            await asyncio.sleep(0.2)

    try:
        await asyncio.gather(from_esp32(), to_esp32())
    finally:
        await room.disconnect()
        print("🔌 Disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=GATEWAY_PORT)
