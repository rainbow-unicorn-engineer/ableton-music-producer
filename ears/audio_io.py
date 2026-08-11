"""audio_io.py — load a bounce for the ears.

Uses librosa/soundfile when available (any format, via the same stack the
library analyst uses); falls back to a stdlib WAV reader otherwise.
Returns STEREO when the file is stereo — loudness metering needs both
channels — plus a mono mix for the spectrogram.
"""

import wave
from pathlib import Path

import numpy as np

try:
    import soundfile as sf
    HAVE_SOUNDFILE = True
except ImportError:
    HAVE_SOUNDFILE = False


def load_stereo(path, max_seconds=600.0):
    """Return (samples, sr): samples shaped (n, channels), float64 in ±1."""
    if HAVE_SOUNDFILE:
        data, sr = sf.read(str(path), always_2d=True, dtype="float64")
        n = int(max_seconds * sr)
        return data[:n], sr
    return _load_wav(path, max_seconds)


def _load_wav(path, max_seconds):
    if Path(path).suffix.lower() != ".wav":
        raise RuntimeError("Without soundfile installed, only .wav bounces "
                           "are readable — `pip install soundfile`")
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        n = min(wf.getnframes(), int(max_seconds * sr))
        raw = wf.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        ints = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16))
        ints = np.where(ints >= 1 << 23, ints - (1 << 24), ints)
        data = ints.astype(np.float64) / float(1 << 23)
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sw}")
    return data.reshape(-1, ch), sr


def to_mono(samples):
    return samples.mean(axis=1)
