

# client.py  (16 kHz, 160-sample, hands-free)
import asyncio
import websockets
import sounddevice as sd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8000/esp32"
SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLES_PER_FRAME = 1920
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 2

# Set high latency to reduce buffer overflow
sd.default.latency = ('high', 'high')


def open_stream(in_out: str):
    cls = sd.InputStream if in_out == 'in' else sd.OutputStream
    try:
        s = cls(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=SAMPLES_PER_FRAME,
        )
        s.start()
        logger.info(f"🎧 {in_out.title()} stream ready")
        return s
    except Exception as e:
        logger.error(f"{in_out} failed: {e}")
        return None


async def send_audio(ws, mic):
    """Continuously read from mic and send PCM data"""
    while True:
        try:
            data, overflowed = await asyncio.to_thread(mic.read, SAMPLES_PER_FRAME)
            if overflowed:
                logger.warning("⚠️ Mic buffer overflow detected")

            # --- ADD THIS LOG LINE ---
            if data.size > 0:
                logger.debug(
                    f"🎤 Read {data.size} samples from mic (overflowed: {overflowed})")
            else:
                logger.debug("🎤 Read 0 samples from mic (silence or no input)")
            # --------------------------

            await ws.send(data.tobytes())  # Corrected from send_bytes
        except websockets.exceptions.ConnectionClosed:
            logger.info("📡 WebSocket closed, stopping mic")
            break
        except Exception as e:
            logger.error(f"🎤 Mic error: {e}")
            break


async def ws_to_speaker(spk, ws):
    """Continuously receive and play audio from WebSocket"""
    try:
        async for msg in ws:
            pcm = np.frombuffer(msg, dtype=np.int16)
            if pcm.size > 0:
                spk.write(pcm)
    except websockets.exceptions.ConnectionClosed:
        logger.info("🔊 Speaker stopped due to closed connection")


async def main():
    mic = open_stream('in')
    spk = open_stream('out')
    if not (mic and spk):
        logger.error("❌ Failed to initialize audio streams")
        return

    while True:
        try:
            logger.info("🔗 Connecting …")
            async with websockets.connect(WS_URL) as ws:
                logger.info("✅ Connected to server")
                await asyncio.gather(
                    send_audio(ws, mic),
                    ws_to_speaker(spk, ws)
                )
        except Exception as e:
            logger.warning(f"⚠️ Connection error: {e}")
            await asyncio.sleep(3)  # Wait before reconnecting

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Exiting due to Ctrl+C")
