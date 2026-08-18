#!/usr/bin/env python3
"""loudness.py — measure a bounce the way streaming platforms do.

Reports:

* **Integrated LUFS** → *the loudness standard (BS.1770) Spotify, Apple
  Music and YouTube use to decide how much to turn your track down.
  Streaming targets sit around -14 LUFS; club masters often land -8 to -6.*
* **True peak (dBTP)** → *the real analog peak between samples, found by
  oversampling. Keep under -1.0 dBTP or lossy encoding will clip.*
* **Loudness range (LRA-ish)** and short-term extremes → *how dynamic the
  track is from section to section.*
* **Band energy** → *how the energy splits across sub / bass / low-mid /
  high-mid / high — the numbers behind "muddy low-mids" or "weak sub".*

Uses `pyloudnorm` when installed; otherwise a built-in BS.1770-4
implementation (K-weighting + gating) that is validated by the test suite.

Usage:
    python loudness.py --file "C:/bounces/mix_v3.wav"
    python loudness.py --file mix.wav --json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import load_stereo  # noqa: E402

try:
    import pyloudnorm  # noqa: F401
    HAVE_PYLOUDNORM = True
except ImportError:
    HAVE_PYLOUDNORM = False

BANDS = [
    ("sub",      20,    60),
    ("bass",     60,   250),
    ("low-mid", 250,   500),
    ("mid",     500,  2000),
    ("high-mid", 2000, 6000),
    ("high",    6000, 20000),
]


# ---------------------------------------------------------------------------
# K-weighting (BS.1770) — two biquad filters
# ---------------------------------------------------------------------------

def _k_weighting_coeffs(sr):
    """Head-effect shelf + high-pass, per BS.1770-4, adapted to sr."""
    # stage 1: high-shelf (models how the head boosts highs)
    db = 3.999843853973347
    f0 = 1681.974450955533
    Q = 0.7071752369554196
    K = np.tan(np.pi * f0 / sr)
    Vh = 10 ** (db / 20.0)
    Vb = Vh ** 0.4996667741545416
    a0 = 1.0 + K / Q + K * K
    b_shelf = np.array([(Vh + Vb * K / Q + K * K) / a0,
                        2.0 * (K * K - Vh) / a0,
                        (Vh - Vb * K / Q + K * K) / a0])
    a_shelf = np.array([1.0, 2.0 * (K * K - 1.0) / a0,
                        (1.0 - K / Q + K * K) / a0])
    # stage 2: high-pass (rumble doesn't count as loudness)
    f0 = 38.13547087602444
    Q = 0.5003270373238773
    K = np.tan(np.pi * f0 / sr)
    a0 = 1.0 + K / Q + K * K
    b_hp = np.array([1.0, -2.0, 1.0]) / a0
    a_hp = np.array([1.0, 2.0 * (K * K - 1.0) / a0,
                     (1.0 - K / Q + K * K) / a0])
    return (b_shelf, a_shelf), (b_hp, a_hp)


def _biquad(x, b, a):
    from scipy.signal import lfilter
    return lfilter(b, a, x, axis=0)


def _k_weight(samples, sr):
    (bs, as_), (bh, ah) = _k_weighting_coeffs(sr)
    return _biquad(_biquad(samples, bs, as_), bh, ah)


def integrated_lufs(samples, sr):
    """BS.1770-4 gated integrated loudness. samples: (n, ch)."""
    kw = _k_weight(samples, sr)
    block = int(0.400 * sr)          # 400 ms blocks...
    hop = int(0.100 * sr)            # ...with 75% overlap
    if len(kw) < block:
        kw = np.pad(kw, ((0, block - len(kw)), (0, 0)))
    n_blocks = 1 + (len(kw) - block) // hop
    powers = np.empty(n_blocks)
    for i in range(n_blocks):
        seg = kw[i * hop:i * hop + block]
        powers[i] = np.mean(seg ** 2, axis=0).sum()  # channel weights = 1
    with np.errstate(divide="ignore"):
        block_lufs = -0.691 + 10 * np.log10(np.maximum(powers, 1e-12))
    # absolute gate at -70 LUFS
    keep = block_lufs > -70.0
    if not keep.any():
        return float("-inf"), block_lufs
    # relative gate: 10 LU under the ungated-but-abs-gated mean
    ref = -0.691 + 10 * np.log10(powers[keep].mean())
    keep &= block_lufs > (ref - 10.0)
    if not keep.any():
        return float("-inf"), block_lufs
    lufs = -0.691 + 10 * np.log10(powers[keep].mean())
    return float(lufs), block_lufs


def true_peak_dbtp(samples, sr, oversample=4):
    """Inter-sample peak via FFT-based oversampling."""
    peak = 0.0
    for ch in range(samples.shape[1]):
        x = samples[:, ch]
        if len(x) == 0:
            continue
        from scipy.signal import resample
        # resample in chunks to bound memory on long bounces
        chunk = sr * 30
        for start in range(0, len(x), chunk):
            seg = x[start:start + chunk]
            up = resample(seg, len(seg) * oversample)
            peak = max(peak, float(np.max(np.abs(up))))
    if peak <= 0:
        return float("-inf")
    return 20 * np.log10(peak)


def band_energy(samples, sr):
    """dB level per frequency band, relative to the loudest band at 0."""
    mono = samples.mean(axis=1)
    n = min(len(mono), sr * 120)
    spec = np.abs(np.fft.rfft(mono[:n] * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    powers = {}
    for name, lo, hi in BANDS:
        sel = (freqs >= lo) & (freqs < hi)
        powers[name] = spec[sel].sum() if sel.any() else 0.0
    ref = max(powers.values()) or 1.0
    return {name: round(10 * np.log10(max(p, 1e-30) / ref), 1)
            for name, p in powers.items()}


def measure(path):
    samples, sr = load_stereo(path)
    if HAVE_PYLOUDNORM:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr)
        lufs = float(meter.integrated_loudness(samples))
        _, blocks = integrated_lufs(samples, sr)   # for range stats
    else:
        lufs, blocks = integrated_lufs(samples, sr)
    audible = blocks[blocks > -70.0]
    loud_range = (float(np.percentile(audible, 95) - np.percentile(audible, 10))
                  if len(audible) > 2 else 0.0)
    return {
        "file": str(path),
        "duration_s": round(len(samples) / sr, 2),
        "sample_rate": sr,
        "channels": samples.shape[1],
        "integrated_lufs": round(lufs, 2),
        "true_peak_dbtp": round(true_peak_dbtp(samples, sr), 2),
        "loudness_range_lu": round(loud_range, 1),
        "band_energy_db": band_energy(samples, sr),
        "meter": "pyloudnorm" if HAVE_PYLOUDNORM else "built-in BS.1770",
    }


def summarize(m):
    """One paragraph a human (or an agent) can act on."""
    lines = [
        f"{Path(m['file']).name}: {m['integrated_lufs']} LUFS integrated, "
        f"true peak {m['true_peak_dbtp']} dBTP, "
        f"loudness range {m['loudness_range_lu']} LU "
        f"({m['duration_s']}s, {m['meter']})."
    ]
    tp = m["true_peak_dbtp"]
    if tp > -0.3:
        lines.append("⚠️ True peak is basically at the ceiling — lossy "
                     "encoders WILL clip this. Trim the limiter output.")
    elif tp > -1.0:
        lines.append("True peak above -1.0 dBTP — fine for clubs, risky "
                     "for streaming encoders.")
    be = m["band_energy_db"]
    if be.get("low-mid", -99) >= -3 and be.get("sub", 0) < be.get("low-mid", 0):
        lines.append("Low-mids carry more energy than the sub — check for "
                     "mud around 250–500 Hz.")
    if be.get("sub", -99) >= 0 and be.get("high", -99) < -25:
        lines.append("Sub-dominant and dark up top — intentional for dub, "
                     "but check the mix translates on small speakers.")
    return " ".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--json", action="store_true", help="machine output only")
    args = ap.parse_args(argv)
    m = measure(args.file)
    if args.json:
        print(json.dumps(m, indent=2))
    else:
        print(json.dumps(m, indent=2))
        print()
        print(summarize(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
