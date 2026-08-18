#!/usr/bin/env python3
"""clash.py — find where two sounds fight for the same frequencies.

→ *Masking: when two sounds carry energy in the same frequency range at
the same time, the louder one hides the other — the classic "I can't
hear the vocal over the bass" problem. This tool measures exactly where
and how badly two tracks mask each other, so "make space for the vocal"
becomes "duck 250–500 Hz in the instrumental when the vocal plays".*

Typical pairs to feed it:
    vocal stem      vs  instrumental (your beat, or a mix minus vocals)
    your bass       vs  your kick
    reference vocal vs  reference instrumental (via stems.py — study how
                        THEY made space)

A band is "contested" in a frame when BOTH sides are active there and
within 6 dB of each other — neither wins, both smear.

Usage:
    python clash.py --a vocal.wav --b instrumental.wav
    python clash.py --a vocal.wav --b beat.wav --png
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import load_stereo, to_mono  # noqa: E402

BANDS = [
    ("sub",      20,    60),
    ("bass",     60,   250),
    ("low-mid", 250,   500),
    ("mid",     500,  2000),
    ("high-mid", 2000, 6000),
    ("high",    6000, 20000),
]

ACTIVE_DB = -40.0     # a band quieter than this (rel. its own max) is idle
CONTEST_DB = 6.0      # both active and within this many dB = contested


def _band_frames(y, sr, n_fft=4096, hop=1024):
    """Per-frame energy per band, plus the average spectrum (for finding
    the single worst frequency)."""
    if len(y) < n_fft:
        y = np.pad(y, (0, n_fft - len(y)))
    window = np.hanning(n_fft)
    n_frames = 1 + (len(y) - n_fft) // hop
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n_frames, n_fft),
        strides=(y.strides[0] * hop, y.strides[0])).copy()
    spec = np.abs(np.fft.rfft(frames * window, axis=1)).T ** 2  # (bins, frames)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
    band_energy = np.zeros((len(BANDS), n_frames))
    for bi, (_, lo, hi) in enumerate(BANDS):
        sel = (freqs >= lo) & (freqs < hi)
        if sel.any():
            band_energy[bi] = spec[sel].sum(axis=0)
    return band_energy, spec, freqs


def _to_db(band_energy):
    ref = band_energy.max() or 1.0
    with np.errstate(divide="ignore"):
        return 10 * np.log10(np.maximum(band_energy / ref, 1e-12))


def analyze_clash(path_a, path_b, label_a="A", label_b="B",
                  png=False, out_dir=None, max_seconds=300.0):
    """Returns per-band contested percentages, the worst single
    frequency, and plain-English fixes, worst first."""
    ya, sra = load_stereo(path_a, max_seconds=max_seconds)
    yb, srb = load_stereo(path_b, max_seconds=max_seconds)
    if sra != srb:
        raise RuntimeError(
            f"Sample rates differ ({sra} vs {srb}) — export both at the "
            f"same rate (Ableton: File > Export, same settings twice)")
    a, b = to_mono(ya), to_mono(yb)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]

    ea, spec_a, freqs = _band_frames(a, sra)
    eb, spec_b, _ = _band_frames(b, sra)
    n_frames = min(ea.shape[1], eb.shape[1])
    da, db_ = _to_db(ea[:, :n_frames]), _to_db(eb[:, :n_frames])

    bands_out = []
    for bi, (name, lo, hi) in enumerate(BANDS):
        active = (da[bi] > ACTIVE_DB) & (db_[bi] > ACTIVE_DB)
        contested = active & (np.abs(da[bi] - db_[bi]) < CONTEST_DB)
        pct = 100.0 * contested.sum() / max(n_frames, 1)
        bands_out.append({
            "band": name, "range_hz": [lo, hi],
            "contested_pct": round(float(pct), 1),
            f"{label_a}_active_pct": round(100.0 * float(
                (da[bi] > ACTIVE_DB).mean()), 1),
            f"{label_b}_active_pct": round(100.0 * float(
                (db_[bi] > ACTIVE_DB).mean()), 1),
        })

    # the single worst frequency: where the two average spectra overlap most
    avg_a = spec_a[:, :n_frames].mean(axis=1)
    avg_b = spec_b[:, :n_frames].mean(axis=1)
    overlap = np.minimum(avg_a / (avg_a.max() or 1.0),
                         avg_b / (avg_b.max() or 1.0))
    audible = (freqs >= 60) & (freqs <= 8000)
    peak_hz = float(freqs[audible][int(np.argmax(overlap[audible]))])

    ranked = sorted(bands_out, key=lambda x: -x["contested_pct"])
    fixes = []
    for band in ranked[:3]:
        if band["contested_pct"] < 10.0:
            break
        lo, hi = band["range_hz"]
        fixes.append(
            f"{band['band']} ({lo}-{hi} Hz) is contested "
            f"{band['contested_pct']}% of the time — sidechain-duck "
            f"{label_b} there when {label_a} plays, or cut a few dB with "
            f"a dynamic EQ band (Pro-Q 4 dynamic mode).")
    verdict = (f"Worst overlap near {peak_hz:.0f} Hz. " + (fixes[0] if fixes
               else "No serious masking — these two coexist cleanly."))

    result = {
        "a": {"label": label_a, "file": str(path_a)},
        "b": {"label": label_b, "file": str(path_b)},
        "seconds_compared": round(n / sra, 2),
        "bands": bands_out,
        "peak_clash_hz": round(peak_hz, 1),
        "fixes": fixes,
        "verdict": verdict,
    }
    if png:
        out_dir = Path(out_dir) if out_dir else Path(path_a).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        result["clash_png"] = str(_render_png(
            result, out_dir / (Path(path_a).stem + ".vs."
                               + Path(path_b).stem + ".clash.png")))
    return result


def _render_png(result, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [b["band"] for b in result["bands"]]
    pcts = [b["contested_pct"] for b in result["bands"]]
    colors = ["#e4572e" if p >= 25 else "#f3a712" if p >= 10 else "#7fb069"
              for p in pcts]
    fig, ax = plt.subplots(figsize=(9, 4), dpi=110)
    ax.bar(names, pcts, color=colors)
    ax.axhline(10, color="#888", lw=0.8, ls="--")
    ax.set_ylabel("Contested time (%)")
    ax.set_title(f"{result['a']['label']} vs {result['b']['label']} — "
                 f"worst overlap ~{result['peak_clash_hz']:.0f} Hz")
    ax.set_ylim(0, max(100, max(pcts) * 1.15 if pcts else 100))
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--a", required=True, help="first file (e.g. vocal)")
    ap.add_argument("--b", required=True, help="second file (e.g. beat)")
    ap.add_argument("--label-a", default="vocal")
    ap.add_argument("--label-b", default="instrumental")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)
    r = analyze_clash(args.a, args.b, args.label_a, args.label_b,
                      png=args.png, out_dir=args.out_dir)
    print(json.dumps(r, indent=2))
    print("\n" + r["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
