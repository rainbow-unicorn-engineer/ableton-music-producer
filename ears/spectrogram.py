#!/usr/bin/env python3
"""spectrogram.py — render a bounce as a picture of sound.

→ *A spectrogram: time runs left-right, frequency runs low-high (log
scale, like hearing), brightness = energy. A muddy mix shows as smeared
glow at 250–500 Hz; a harsh one as hot bands at 3–4 kHz; a weak sub as
darkness below 60 Hz.*

Output lands next to the input as `<name>.spectrogram.png` (or --out).
Uses librosa's mel spectrogram when available; numpy STFT otherwise.

Usage:
    python spectrogram.py --file "C:/bounces/mix_v3.wav"
"""

import argparse
import sys
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import load_stereo, to_mono  # noqa: E402

try:
    import librosa
    import librosa.display
    HAVE_LIBROSA = True
except ImportError:
    HAVE_LIBROSA = False


def render(path, out=None, max_seconds=300.0):
    samples, sr = load_stereo(path, max_seconds=max_seconds)
    y = to_mono(samples)
    out = Path(out) if out else Path(path).with_suffix(".spectrogram.png")

    fig, ax = plt.subplots(figsize=(14, 6), dpi=110)
    if HAVE_LIBROSA:
        S = librosa.feature.melspectrogram(y=y.astype(np.float32), sr=sr,
                                           n_fft=4096, hop_length=1024,
                                           n_mels=192, fmin=20, fmax=20000)
        S_db = librosa.power_to_db(S, ref=np.max)
        img = librosa.display.specshow(S_db, sr=sr, hop_length=1024,
                                       x_axis="time", y_axis="mel",
                                       fmin=20, fmax=20000, ax=ax,
                                       cmap="magma")
    else:
        n_fft, hop = 4096, 1024
        if len(y) < n_fft:
            y = np.pad(y, (0, n_fft - len(y)))
        window = np.hanning(n_fft)
        n_frames = 1 + (len(y) - n_fft) // hop
        frames = np.lib.stride_tricks.as_strided(
            y, shape=(n_frames, n_fft),
            strides=(y.strides[0] * hop, y.strides[0])).copy()
        spec = np.abs(np.fft.rfft(frames * window, axis=1)).T ** 2
        S_db = 10 * np.log10(np.maximum(spec / spec.max(), 1e-10))
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        times = np.arange(n_frames) * hop / sr
        img = ax.pcolormesh(times, freqs, S_db, cmap="magma",
                            shading="auto", vmin=-80, vmax=0)
        ax.set_yscale("symlog", linthresh=100)
        ax.set_ylim(20, 20000)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Hz")
    fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.01)
    ax.set_title(Path(path).name)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default=None, help="output PNG path")
    args = ap.parse_args(argv)
    out = render(args.file, args.out)
    print(f"Spectrogram -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
