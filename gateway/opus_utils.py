import opuslib


def decode_opus(data: bytes) -> bytes:
    dec = opuslib.Decoder(48000, 1)
    pcm = dec.decode(data, 480)        # returns array of samples
    return pcm.tobytes()


def encode_opus(pcm: bytes) -> bytes:
    enc = opuslib.Encoder(48000, 1, application=opuslib.APPLICATION_AUDIO)
    data = enc.encode(pcm, 480)
    return data
