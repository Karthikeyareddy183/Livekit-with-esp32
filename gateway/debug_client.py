# debug_client.py
import asyncio
import websockets
import sounddevice as sd
import numpy as np
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

URL = "ws://localhost:8000/esp32"
SAMPLE_RATE = 48_000
CHANNELS = 1
FRAME_BYTES = 960 * 2   # 20 ms of 16-bit PCM @ 48 kHz


def open_stream():
    try:
        s = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=960,
        )
        s.start()
        return s
    except Exception as e:
        print("Mic failed:", e)
        return None


async def main():
    mic = open_stream()
    if not mic:
        return
    async with websockets.connect(URL) as ws:
        print("🎤 Connected to gateway – will send 10 s of audio")
        for _ in range(500):               # 500 × 20 ms ≈ 10 s
            data, _ = mic.read(960)
            await ws.send(data.tobytes())
            vol = np.sqrt(np.mean(np.square(data.astype(np.float32))))
            print(f"sent {len(data)} samples, RMS={vol:.0f}")
        print("finished sending")

if __name__ == "__main__":
    asyncio.run(main())
