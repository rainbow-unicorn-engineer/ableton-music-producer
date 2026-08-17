#!/usr/bin/env python3
"""structure.py — extract the arrangement math of any track.

→ *Arrangement: how a track's energy is organized over time — intro,
build, drop, break. This tool slices a track into bars (musical measures)
and measures each bar's energy, then groups bars into labeled sections.
The output is the "arrangement skeleton": e.g. intro 16 → build 16 →
drop 32 → break 16 → drop 32.*

That skeleton is the first thing to steal from a reference track — it
feeds straight into the recipe docs in `skills/`.

How sections get their names (heuristics, honestly imperfect):

* **drop** — loud AND sub-heavy → *the payoff section: full energy with
  the bass frequencies (under ~150 Hz) carrying real weight.*
* **build** — energy rising into a drop, sub still thin → *the ramp-up.*
* **break** — quiet section after a drop → *the breather.*
* **intro / outro** — first / last section when quiet.

Usage:
    python structure.py --file "C:/refs/weekend_griz_flip.wav"
    python structure.py --file mix.wav --bpm 140 --png
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import load_stereo, to_mono  # noqa: E402

# Sample packs and bounces often label tempo in the filename — trust that
# over the detector (same rule as the library analyst).
_BPM_NAME_RE = re.compile(r"(?:^|[^0-9])(\d{2,3})\s?bpm|bpm\s?(\d{2,3})",
                          re.IGNORECASE)

# A bar's sub content above this share of its total energy = "sub present".
SUB_HZ = 150.0
SUB_PRESENT_RATIO = 0.20
# Bars quieter than this (relative to the loudest bar) count as silence.
SILENCE_DB = -45.0


def bpm_from_filename(path):
    for m in _BPM_NAME_RE.finditer(Path(path).name):
        val = float(m.group(1) or m.group(2))
        if 50 <= val <= 220:
            return val
    return None


def detect_bpm(y, sr, lo=60.0, hi=200.0):
    """Tempo via spectral-flux onsets + autocorrelation → *find the
    time-lag at which the rhythm best lines up with itself; that lag is
    the beat.* Same approach the library analyst's fallback engine uses.
    """
    n_fft, hop = 2048, 512
    if len(y) < n_fft:
        return None
    window = np.hanning(n_fft)
    n_frames = 1 + (len(y) - n_fft) // hop
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n_frames, n_fft),
        strides=(y.strides[0] * hop, y.strides[0])).copy()
    spec = np.abs(np.fft.rfft(frames * window, axis=1)).T
    diff = np.diff(spec, axis=1)
    env = np.concatenate([[0.0], np.maximum(diff, 0.0).sum(axis=0)])
    env = env - env.mean()
    if not np.any(env):
        return None
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    fps = sr / hop
    lag_min = max(1, int(round(fps * 60.0 / hi)))
    lag_max = min(len(ac) - 1, int(round(fps * 60.0 / lo)))
    if lag_max <= lag_min:
        return None
    lag = lag_min + int(np.argmax(ac[lag_min:lag_max + 1]))
    if ac[lag] <= 0:
        return None
    return round(60.0 * fps / lag, 1)


def bar_profile(y, sr, bpm, beats_per_bar=4):
    """Per-bar energy (dB, loudest bar = 0) and sub-energy share."""
    bar_len = int(round(beats_per_bar * 60.0 / bpm * sr))
    n_bars = max(1, len(y) // bar_len)
    energy_db = np.empty(n_bars)
    sub_ratio = np.empty(n_bars)
    rms_all = np.empty(n_bars)
    for i in range(n_bars):
        seg = y[i * bar_len:(i + 1) * bar_len]
        rms_all[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0.0
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
        freqs = np.fft.rfftfreq(len(seg), 1.0 / sr)
        total = spec.sum()
        sub_ratio[i] = float(spec[freqs < SUB_HZ].sum() / total) if total > 0 else 0.0
    ref = rms_all.max() or 1.0
    with np.errstate(divide="ignore"):
        energy_db = 20 * np.log10(np.maximum(rms_all / ref, 1e-6))
    return energy_db, sub_ratio, bar_len / sr


def _segment(energy_db, sub_ratio, min_len=4):
    """Group bars into sections wherever the (energy level, sub presence)
    character changes. Sections shorter than `min_len` bars merge into a
    neighbor — arrangement moves in 4/8/16-bar blocks, not single bars."""
    n = len(energy_db)
    # smooth energy over a 2-bar window to ignore one-bar fills
    smooth = np.convolve(energy_db, np.ones(2) / 2, mode="same")

    def level(i):
        e = smooth[i]
        if e <= SILENCE_DB:
            return "silent"
        if e > -8.0:
            return "high"
        if e > -20.0:
            return "mid"
        return "low"

    def character(i):
        return (level(i), sub_ratio[i] >= SUB_PRESENT_RATIO)

    bounds = [0]
    for i in range(1, n):
        if character(i) != character(i - 1):
            bounds.append(i)
    bounds.append(n)
    sections = [[a, b] for a, b in zip(bounds[:-1], bounds[1:])]
    # merge short sections into the more similar neighbor
    merged = True
    while merged and len(sections) > 1:
        merged = False
        for idx, (a, b) in enumerate(sections):
            if b - a < min_len:
                if idx == 0:
                    sections[1][0] = a
                else:
                    sections[idx - 1][1] = b
                sections.pop(idx)
                merged = True
                break
    return [(a, b) for a, b in sections]


def _label(sections, energy_db, sub_ratio):
    """Attach heuristic names. Returns list of dicts."""
    out = []
    n_sec = len(sections)
    for idx, (a, b) in enumerate(sections):
        e = float(np.mean(energy_db[a:b]))
        sub = float(np.mean(sub_ratio[a:b]))
        loud = e > -8.0
        subby = sub >= SUB_PRESENT_RATIO
        prev = out[-1] if out else None
        if e <= SILENCE_DB:
            label = "silence"
        elif loud and subby:
            label = "drop"
        elif idx == 0:
            label = "intro"
        elif idx == n_sec - 1 and not loud:
            label = "outro"
        elif prev and prev["label"] in ("drop",) and not loud:
            label = "break"
        elif not loud:
            # rising toward a louder next section = build
            nxt_e = (float(np.mean(energy_db[sections[idx + 1][0]:sections[idx + 1][1]]))
                     if idx + 1 < n_sec else e)
            label = "build" if nxt_e > e + 3.0 else "break"
        else:
            label = "section"
        out.append({
            "label": label,
            "start_bar": int(a),
            "length_bars": int(b - a),
            "avg_energy_db": round(e, 1),
            "sub_presence": round(sub, 2),
        })
    return out


def analyze_structure(path, bpm=None, beats_per_bar=4, png=False,
                      out_dir=None, max_seconds=600.0):
    """The full readout: bpm, per-bar energy, labeled sections, skeleton."""
    path = Path(path)
    samples, sr = load_stereo(path, max_seconds=max_seconds)
    y = to_mono(samples)
    bpm_source = "given"
    if bpm is None:
        bpm = bpm_from_filename(path)
        bpm_source = "filename"
    if bpm is None:
        bpm = detect_bpm(y, sr)
        bpm_source = "detected"
    if bpm is None:
        raise RuntimeError(
            "Couldn't determine tempo — pass --bpm (or put it in the "
            "filename, e.g. 'ref 140bpm.wav')")
    energy_db, sub_ratio, bar_seconds = bar_profile(y, sr, bpm, beats_per_bar)
    sections = _label(_segment(energy_db, sub_ratio), energy_db, sub_ratio)
    skeleton = " → ".join(f"{s['label']} {s['length_bars']}" for s in sections)
    result = {
        "file": str(path),
        "bpm": float(bpm),
        "bpm_source": bpm_source,
        "beats_per_bar": beats_per_bar,
        "bar_seconds": round(bar_seconds, 3),
        "total_bars": len(energy_db),
        "sections": sections,
        "skeleton": skeleton,
        "bar_energy_db": [round(float(e), 1) for e in energy_db],
    }
    if png:
        out_dir = Path(out_dir) if out_dir else path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        result["structure_png"] = str(_render_png(
            result, out_dir / (path.stem + ".structure.png")))
    return result


def _render_png(result, out):
    """Bar-energy chart with shaded, labeled sections."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    energy = result["bar_energy_db"]
    fig, ax = plt.subplots(figsize=(14, 4), dpi=110)
    ax.bar(range(len(energy)), np.array(energy) - min(energy),
           bottom=min(energy), width=1.0, color="#444", edgecolor="none")
    palette = {"drop": "#e4572e", "build": "#f3a712", "break": "#5b85aa",
               "intro": "#7fb069", "outro": "#7fb069", "silence": "#222",
               "section": "#9b7ede"}
    for s in result["sections"]:
        a, b = s["start_bar"], s["start_bar"] + s["length_bars"]
        ax.axvspan(a - 0.5, b - 0.5, alpha=0.25,
                   color=palette.get(s["label"], "#9b7ede"))
        ax.text((a + b) / 2, ax.get_ylim()[1] * 0.02 + max(energy) - 3,
                f"{s['label']}\n{s['length_bars']}", ha="center", va="top",
                fontsize=8, color="#eee",
                bbox=dict(boxstyle="round", fc="#000", alpha=0.5))
    ax.set_xlabel(f"Bar ({result['bpm']:.0f} BPM, "
                  f"{result['beats_per_bar']}/4)")
    ax.set_ylabel("Bar energy (dB)")
    ax.set_title(Path(result["file"]).name + " — " + result["skeleton"])
    ax.set_facecolor("#111")
    fig.patch.set_facecolor("#111")
    for spine in ax.spines.values():
        spine.set_color("#666")
    ax.tick_params(colors="#ccc")
    ax.xaxis.label.set_color("#ccc")
    ax.yaxis.label.set_color("#ccc")
    ax.title.set_color("#eee")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--bpm", type=float, default=None,
                    help="tempo, if the detector shouldn't guess")
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--png", action="store_true",
                    help="also render <name>.structure.png")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)
    r = analyze_structure(args.file, bpm=args.bpm,
                          beats_per_bar=args.beats_per_bar,
                          png=args.png, out_dir=args.out_dir)
    print(json.dumps({k: v for k, v in r.items() if k != "bar_energy_db"},
                     indent=2))
    print(f"\nSkeleton: {r['skeleton']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
