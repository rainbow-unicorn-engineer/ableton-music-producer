#!/usr/bin/env python3
"""mashup.py — make an acapella and a beat agree on key and tempo.

→ *A mashup drops the vocal from one song over the music of another. It
only works when the two agree on key (so the notes don't sour) and tempo
(so the words land on the beat). This tool measures both sides and tells
you the exact transpose and stretch to apply in Ableton.*

Key matching happens in "relative space": A minor and C major contain
the same notes, so a vocal in A minor sits fine over a C major beat —
the tool exploits that to find the SMALLEST pitch shift that works
(smaller shifts sound more natural; past ~4 semitones voices get
chipmunky or growly unless that's the point — hello AlterBoy).

Tempo matching allows half/double time: a 72 BPM vocal flows naturally
over a 144 BPM beat, so the tool picks whichever relationship needs the
least stretching. Past ~8% stretch, warping artifacts get audible.

Usage:
    python mashup.py --acapella vox.wav --beat mybeat.wav
    python mashup.py --acapella vox.wav --beat beat.wav --acapella-key "A minor" --beat-bpm 144
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# analysis lives in the library analyst (monorepo sharing, as planned)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "library-analyst"))

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAX_CLEAN_STRETCH_PCT = 8.0     # beyond this, warping artifacts get audible
MAX_NATURAL_SHIFT_ST = 4       # beyond this, voices stop sounding human


def _parse_key(key):
    note, mode = key.strip().split()
    return NOTE_NAMES.index(note), mode.lower()


def _relative_major(idx, mode):
    """Every key expressed as its relative major (A minor -> C major),
    because relative keys share all their notes."""
    return (idx + 3) % 12 if mode == "minor" else idx


def semitone_shift(src_key, dst_key):
    """Smallest transpose (in semitones, -6..+6) that makes `src_key`
    material fit over `dst_key` material."""
    si, sm = _parse_key(src_key)
    di, dm = _parse_key(dst_key)
    diff = (_relative_major(di, dm) - _relative_major(si, sm)) % 12
    return diff - 12 if diff > 6 else diff


def compatible_keys(key):
    """Keys that need NO transpose over `key`: itself and its relative."""
    i, m = _parse_key(key)
    if m == "minor":
        return [key, f"{NOTE_NAMES[(i + 3) % 12]} major"]
    return [key, f"{NOTE_NAMES[(i - 3) % 12]} minor"]


def tempo_plan(src_bpm, dst_bpm):
    """How to warp `src_bpm` material onto a `dst_bpm` grid. Considers
    straight, half-time, and double-time — picks the least stretching."""
    options = [
        ("straight", dst_bpm / src_bpm),
        ("half-time feel (vocal at half the beat's pace)",
         dst_bpm / (src_bpm * 2.0)),
        ("double-time feel (vocal at twice the beat's pace)",
         (dst_bpm * 2.0) / src_bpm),
    ]
    feel, ratio = min(options, key=lambda o: abs(o[1] - 1.0))
    stretch_pct = (ratio - 1.0) * 100.0
    return {
        "feel": feel,
        "stretch_ratio": round(ratio, 4),
        "stretch_pct": round(stretch_pct, 2),
        "clean": abs(stretch_pct) <= MAX_CLEAN_STRETCH_PCT,
    }


def match(acapella, beat, acapella_key=None, beat_key=None,
          acapella_bpm=None, beat_bpm=None):
    """The full plan: analyze both files (or trust the overrides), return
    transpose + warp instructions and warnings."""
    import analysis as analysis_mod

    def info(path, key, bpm):
        if key is None or bpm is None:
            feats = analysis_mod.analyze_file(path)
            key = key or feats.get("key")
            bpm = bpm or feats.get("bpm")
        return {"file": str(path), "key": key, "bpm": bpm}

    a = info(acapella, acapella_key, acapella_bpm)
    b = info(beat, beat_key, beat_bpm)
    missing = [side["file"] for side in (a, b)
               if side["key"] is None or side["bpm"] is None]
    if missing:
        raise RuntimeError(
            "Couldn't detect key/BPM for: " + "; ".join(missing)
            + " — pass overrides (--acapella-key / --beat-bpm etc.), or "
            "put the BPM in the filename ('vox 144bpm.wav')")

    shift = semitone_shift(a["key"], b["key"])
    plan = tempo_plan(float(a["bpm"]), float(b["bpm"]))

    steps, warnings = [], []
    if shift == 0:
        steps.append(f"No transpose needed — {a['key']} sits over "
                     f"{b['key']} as-is (same or relative key).")
    else:
        steps.append(f"Transpose the acapella {shift:+d} semitones "
                     f"(clip view > Transpose, or AlterBoy Pitch for "
                     f"character).")
        if abs(shift) > MAX_NATURAL_SHIFT_ST:
            warnings.append(
                f"{abs(shift)} semitones is a big vocal shift — expect an "
                f"unnatural timbre. Options: shift the BEAT the other way "
                f"instead, or lean into it with AlterBoy formant tricks.")
    steps.append(
        f"Warp the acapella to {b['bpm']} BPM — {plan['feel']}, "
        f"{plan['stretch_pct']:+.1f}% stretch (Complex Pro warp mode for "
        f"vocals).")
    if not plan["clean"]:
        warnings.append(
            f"{abs(plan['stretch_pct']):.1f}% stretch exceeds the ~"
            f"{MAX_CLEAN_STRETCH_PCT:.0f}% clean limit — artifacts likely. "
            f"Consider a different beat tempo, or re-chop the vocal in "
            f"phrases instead of one long warp.")

    return {
        "acapella": a,
        "beat": b,
        "semitone_shift": shift,
        "tempo": plan,
        "no_transpose_keys": compatible_keys(b["key"]),
        "steps": steps,
        "warnings": warnings,
        "verdict": ("Clean fit — do it." if not warnings else
                    "Workable, with caveats: " + " ".join(warnings)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--acapella", required=True)
    ap.add_argument("--beat", required=True)
    ap.add_argument("--acapella-key", default=None, help='e.g. "A minor"')
    ap.add_argument("--beat-key", default=None)
    ap.add_argument("--acapella-bpm", type=float, default=None)
    ap.add_argument("--beat-bpm", type=float, default=None)
    args = ap.parse_args(argv)
    r = match(args.acapella, args.beat, args.acapella_key, args.beat_key,
              args.acapella_bpm, args.beat_bpm)
    print(json.dumps(r, indent=2))
    print()
    for s in r["steps"]:
        print("  • " + s)
    print("\n" + r["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
