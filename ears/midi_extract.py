#!/usr/bin/env python3
"""midi_extract.py — pull the notes out of audio, into a MIDI clip.

→ *MIDI extraction: listen to a recording and write down which notes are
played, when, and for how long — as a .mid file you can drop straight
onto an Ableton MIDI track to study a reference's chords or topline.*

Two engines, same output format (the house pattern):

* **basic-pitch** (Spotify's model, `pip install basic-pitch`) —
  polyphonic → *hears chords: many notes at once.* Preferred.
* **fallback** (numpy autocorrelation) — monophonic → *hears one note at
  a time; fine for basslines and toplines, useless for chords.* Keeps
  the tool alive and testable anywhere.

Best results: run stems.py first and extract from a single stem
(bass stem → bassline MIDI, vocal stem → topline MIDI), not the full mix.

Usage:
    python midi_extract.py --file "C:/refs/stems/htdemucs/ref/bass.wav"
    python midi_extract.py --file topline.wav --bpm 140
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import load_stereo, to_mono  # noqa: E402

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PPQ = 480  # MIDI ticks per quarter note

FALLBACK_NOTE = (
    "engine: fallback (monophonic) — hears one note at a time. For chords "
    "install basic-pitch on the studio machine: `pip install basic-pitch`."
)


def basic_pitch_available():
    return importlib.util.find_spec("basic_pitch") is not None


def note_name(midi):
    return f"{NOTE_NAMES[int(midi) % 12]}{int(midi) // 12 - 1}"


# ---------------------------------------------------------------------------
# Engine 1: basic-pitch (polyphonic)
# ---------------------------------------------------------------------------

def _extract_basic_pitch(path, out):
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    _, midi_data, note_events = predict(str(path), ICASSP_2022_MODEL_PATH)
    midi_data.write(str(out))
    notes = [{"start_s": round(float(s), 3),
              "dur_s": round(float(e - s), 3),
              "midi": int(p), "name": note_name(p)}
             for s, e, p, *_ in sorted(note_events)]
    return notes, "basic-pitch (polyphonic)"


# ---------------------------------------------------------------------------
# Engine 2: fallback — monophonic autocorrelation pitch tracking
# ---------------------------------------------------------------------------

def _frame_f0(seg, sr, fmin=50.0, fmax=1000.0):
    """One frame's fundamental via autocorrelation → *slide the sound
    against itself; the shift where it best matches is one period of the
    note.* Returns None for silence/noise."""
    seg = seg - seg.mean()
    energy = float(np.sqrt(np.mean(seg ** 2)))
    if energy < 1e-4:
        return None
    ac = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
    if ac[0] <= 0:
        return None
    lag_min = int(sr / fmax)
    lag_max = min(int(sr / fmin), len(ac) - 1)
    if lag_max <= lag_min:
        return None
    lag = lag_min + int(np.argmax(ac[lag_min:lag_max + 1]))
    if ac[lag] / ac[0] < 0.5:  # not periodic enough to be a pitch
        return None
    return sr / lag


def _extract_fallback(path, out, bpm, frame=2048, hop=512):
    samples, sr = load_stereo(path)
    y = to_mono(samples)
    if len(y) < frame:
        y = np.pad(y, (0, frame - len(y)))
    n_frames = 1 + (len(y) - frame) // hop
    midis = np.full(n_frames, -1, dtype=int)
    for i in range(n_frames):
        f0 = _frame_f0(y[i * hop:i * hop + frame], sr)
        if f0:
            midis[i] = int(round(69 + 12 * np.log2(f0 / 440.0)))
    # median-ish smoothing: a lone frame differing from both neighbors is noise
    for i in range(1, n_frames - 1):
        if midis[i] != midis[i - 1] and midis[i] != midis[i + 1] \
                and midis[i - 1] == midis[i + 1]:
            midis[i] = midis[i - 1]
    # segment runs of the same note
    notes = []
    min_frames = max(1, int(0.08 * sr / hop))  # notes shorter than 80 ms = noise
    i = 0
    while i < n_frames:
        if midis[i] < 0:
            i += 1
            continue
        j = i
        while j < n_frames and midis[j] == midis[i]:
            j += 1
        if j - i >= min_frames and 0 <= midis[i] <= 127:
            notes.append({"start_s": round(i * hop / sr, 3),
                          "dur_s": round((j - i) * hop / sr, 3),
                          "midi": int(midis[i]),
                          "name": note_name(midis[i])})
        i = j
    _write_midi(notes, out, bpm)
    return notes, "fallback (monophonic)"


# ---------------------------------------------------------------------------
# Minimal Standard MIDI File writer (no dependencies)
# ---------------------------------------------------------------------------

def _var_len(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _write_midi(notes, out, bpm=120.0):
    """One-track SMF: tempo meta + note on/off pairs, velocity 96."""
    tick_per_s = PPQ * bpm / 60.0
    events = []  # (tick, priority, bytes) — offs before ons at same tick
    for n in notes:
        on = int(round(n["start_s"] * tick_per_s))
        off = int(round((n["start_s"] + n["dur_s"]) * tick_per_s))
        events.append((on, 1, bytes([0x90, n["midi"], 96])))
        events.append((max(off, on + 1), 0, bytes([0x80, n["midi"], 0])))
    events.sort(key=lambda e: (e[0], e[1]))
    track = bytearray()
    tempo = int(round(60_000_000 / bpm))
    track += b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big")
    prev = 0
    for tick, _, ev in events:
        track += _var_len(tick - prev) + ev
        prev = tick
    track += b"\x00\xff\x2f\x00"  # end of track
    header = (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big")
              + (1).to_bytes(2, "big") + PPQ.to_bytes(2, "big"))
    chunk = b"MTrk" + len(track).to_bytes(4, "big") + bytes(track)
    Path(out).write_bytes(header + chunk)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(path, out=None, bpm=120.0, max_notes=500):
    """Audio in, MIDI out. Returns a report dict; the .mid lands next to
    the audio (or at `out`)."""
    path = Path(path)
    out = Path(out) if out else path.with_suffix(".mid")
    if basic_pitch_available():
        notes, engine = _extract_basic_pitch(path, out)
    else:
        notes, engine = _extract_fallback(path, out, bpm)
    pitches = [n["midi"] for n in notes]
    report = {
        "file": str(path),
        "midi_file": str(out),
        "engine": engine,
        "note_count": len(notes),
        "pitch_range": (f"{note_name(min(pitches))}–{note_name(max(pitches))}"
                        if pitches else None),
        "notes": notes[:max_notes],
    }
    if engine.startswith("fallback"):
        report["engine_note"] = FALLBACK_NOTE
    if len(notes) > max_notes:
        report["notes_truncated"] = len(notes) - max_notes
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default=None, help="output .mid path")
    ap.add_argument("--bpm", type=float, default=120.0,
                    help="tempo written into the MIDI file (fallback engine)")
    args = ap.parse_args(argv)
    r = extract(args.file, args.out, args.bpm)
    shown = dict(r)
    shown["notes"] = shown["notes"][:12]
    print(json.dumps(shown, indent=2))
    print(f"\nMIDI: {r['midi_file']} ({r['note_count']} notes, {r['engine']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
