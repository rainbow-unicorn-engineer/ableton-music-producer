#!/usr/bin/env python3
"""analysis.py — give every sample a musical description in numbers.

Per file it extracts (the plan's feature table):

| feature    | plain English                                             |
|------------|-----------------------------------------------------------|
| bpm        | tempo of loops (skipped for one-shots — too short to have one) |
| key        | what note/key a sample sits in, e.g. 'F minor'            |
| duration   | seconds — also how we tell one-shot vs. loop              |
| brightness | dark rumble vs. bright sparkle (spectral centroid, in Hz) |
| punch      | soft pad vs. hard transient (onset strength)              |
| loudness   | quiet texture vs. full-power stab (RMS energy)            |

Two engines, same results format:

* **librosa** (preferred — `pip install librosa`): the well-tested MIR
  library the plan calls for. Used automatically when importable.
* **fallback** (numpy/scipy + stdlib): keeps the analyst working — and
  testable — where librosa isn't installed. WAV-only.

Usage:

    # Analyze everything the scanner found that isn't analyzed yet
    python analysis.py

    # Just one file, printed as JSON (no database involved)
    python analysis.py --file "D:/Samples/Bass/dark_sub_F.wav"
"""

import argparse
import json
import math
import sys
import time
import wave
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import db as dbmod
else:
    from . import db as dbmod

try:
    import librosa
    HAVE_LIBROSA = True
except ImportError:
    HAVE_LIBROSA = False

# Files shorter than this are one-shots: no meaningful tempo to detect.
MIN_LOOP_SECONDS = 1.5

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Schmuckler key profiles → *how strongly each of the 12 pitch
# classes "belongs" in a major or minor key, from listening experiments.
# We correlate the sample's pitch content against all 24 rotations and the
# best match wins.*
_MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                           2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                           2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


# ---------------------------------------------------------------------------
# Audio loading
# ---------------------------------------------------------------------------

def load_audio(path, sr=22050, max_seconds=90.0):
    """Return (mono_float_array, sample_rate). Long files are truncated —
    90 seconds is plenty to characterize any sample."""
    if HAVE_LIBROSA:
        y, sr = librosa.load(str(path), sr=sr, mono=True, duration=max_seconds)
        return y.astype(np.float64), sr
    return _load_wav_fallback(path, max_seconds)


def _load_wav_fallback(path, max_seconds):
    """Stdlib WAV reader (fallback engine). 16/24/32-bit PCM and 32-bit float."""
    if Path(path).suffix.lower() != ".wav":
        raise RuntimeError(
            f"Fallback engine reads .wav only — install librosa (+ffmpeg) "
            f"for {Path(path).suffix} files")
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = min(wf.getnframes(), int(max_seconds * sr))
        raw = wf.readframes(n_frames)
    if sampwidth == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sampwidth == 4:
        # could be int32 or float32 — PCM int32 is overwhelmingly more common in wave files
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif sampwidth == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        ints = (b[:, 0].astype(np.int32)
                | (b[:, 1].astype(np.int32) << 8)
                | (b[:, 2].astype(np.int32) << 16))
        ints = np.where(ints >= 1 << 23, ints - (1 << 24), ints)
        data = ints.astype(np.float64) / float(1 << 23)
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sampwidth}")
    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    return data, sr


# ---------------------------------------------------------------------------
# Shared DSP helpers (fallback engine)
# ---------------------------------------------------------------------------

def _stft_mag(y, sr, n_fft=2048, hop=512):
    """Magnitude spectrogram → *sound sliced into short moments, each
    described by how much energy sits at each frequency.*"""
    if len(y) < n_fft:
        y = np.pad(y, (0, n_fft - len(y)))
    window = np.hanning(n_fft)
    n_frames = 1 + (len(y) - n_fft) // hop
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n_frames, n_fft),
        strides=(y.strides[0] * hop, y.strides[0])).copy()
    spec = np.abs(np.fft.rfft(frames * window, axis=1)).T  # (freqbins, frames)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
    return spec, freqs, hop


def _onset_envelope(spec):
    """Spectral flux → *how much the sound changes moment to moment; spikes
    line up with drum hits and note starts.*"""
    diff = np.diff(spec, axis=1)
    flux = np.maximum(diff, 0.0).sum(axis=0)
    return np.concatenate([[0.0], flux])


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _punch(y, sr, frame=1024, hop=512):
    """Punch, engine-independent: how suddenly the loudness envelope rises,
    relative to the sound's average level → *a kick slams from silence to
    full power in one instant (high punch); a pad fades in (low punch).*
    Scale-invariant, so quiet and loud files compare fairly."""
    if len(y) < frame:
        y = np.pad(y, (0, frame - len(y)))
    n_frames = 1 + (len(y) - frame) // hop
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n_frames, frame),
        strides=(y.strides[0] * hop, y.strides[0])).copy()
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    rise = np.diff(np.concatenate([[0.0], rms]))  # leading silence frame
    if rms.mean() <= 0:
        return 0.0
    return float(np.max(np.maximum(rise, 0.0)) / (rms.mean() + 1e-9))


def analyze_file(path):
    """Full feature readout for one audio file. Returns a plain dict."""
    y, sr = load_audio(path)
    if len(y) == 0:
        raise RuntimeError("File decoded to zero samples")
    duration = len(y) / sr
    peak = np.max(np.abs(y))
    if peak > 0:
        y_norm = y / peak
    else:
        y_norm = y

    punch = _punch(y, sr)
    loudness = float(np.sqrt(np.mean(y ** 2)))

    if HAVE_LIBROSA:
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        chroma = np.mean(librosa.feature.chroma_stft(y=y_norm, sr=sr), axis=1)
        bpm = None
        if duration >= MIN_LOOP_SECONDS:
            tempo = librosa.beat.beat_track(y=y, sr=sr)[0]
            tempo = float(np.atleast_1d(tempo)[0])
            bpm = round(tempo, 1) if tempo > 0 else None
    else:
        spec, freqs, hop = _stft_mag(y_norm, sr)
        frame_energy = spec.sum(axis=0)
        active = frame_energy > (frame_energy.max() * 1e-4 if frame_energy.max() > 0 else 0)
        sel = spec[:, active] if active.any() else spec
        centroid = float(np.sum(freqs[:, None] * sel) / max(np.sum(sel), 1e-12))
        onset_env = _onset_envelope(spec)
        chroma = _chroma_fallback(spec, freqs)
        bpm = _bpm_fallback(onset_env, sr, hop) if duration >= MIN_LOOP_SECONDS else None

    key = estimate_key(chroma)
    return {
        "duration": round(duration, 3),
        "bpm": bpm,
        "key": key,
        "brightness": round(centroid, 1),
        "punch": round(punch, 3),
        "loudness": round(loudness, 4),
        "engine": "librosa" if HAVE_LIBROSA else "fallback",
    }


def _chroma_fallback(spec, freqs):
    """Fold the spectrum into 12 pitch classes → *how much C, C#, D...
    energy the sound contains, regardless of octave.*"""
    chroma = np.zeros(12)
    valid = freqs > 25.0
    midi = 69 + 12 * np.log2(np.maximum(freqs[valid], 1e-6) / 440.0)
    pitch_class = np.mod(np.round(midi), 12).astype(int)
    energy = spec[valid].sum(axis=1)
    for pc in range(12):
        chroma[pc] = energy[pitch_class == pc].sum()
    return chroma


def _bpm_fallback(onset_env, sr, hop, lo=60.0, hi=200.0):
    """Tempo by autocorrelation of the onset envelope → *find the time-lag
    at which the rhythm best lines up with itself; that lag is the beat.*"""
    env = onset_env - onset_env.mean()
    if not np.any(env):
        return None
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    fps = sr / hop  # onset frames per second
    lag_min = max(1, int(round(fps * 60.0 / hi)))
    lag_max = min(len(ac) - 1, int(round(fps * 60.0 / lo)))
    if lag_max <= lag_min:
        return None
    lag = lag_min + int(np.argmax(ac[lag_min:lag_max + 1]))
    if ac[lag] <= 0:
        return None
    return round(60.0 * fps / lag, 1)


def estimate_key(chroma):
    """Krumhansl-Schmuckler template matching over all 24 keys."""
    chroma = np.asarray(chroma, dtype=np.float64)
    if chroma.sum() <= 0:
        return None
    best_key, best_score = None, -2.0
    for tonic in range(12):
        rolled = np.roll(chroma, -tonic)
        for profile, mode in ((_MAJOR_PROFILE, "major"), (_MINOR_PROFILE, "minor")):
            score = np.corrcoef(rolled, profile)[0, 1]
            if score > best_score:
                best_score = score
                best_key = f"{NOTE_NAMES[tonic]} {mode}"
    return best_key


# ---------------------------------------------------------------------------
# Batch runner: fill in the database
# ---------------------------------------------------------------------------

def analyze_pending(db_path=None, limit=None, progress=True):
    """Analyze every scanned-but-unanalyzed file. Returns (done, failed)."""
    conn = dbmod.connect(db_path)
    rows = conn.execute(
        "SELECT id, path FROM samples WHERE missing = 0 AND analyzed_at IS NULL"
        + (f" LIMIT {int(limit)}" if limit else "")).fetchall()
    done = failed = 0
    t0 = time.time()
    for i, row in enumerate(rows):
        try:
            feats = analyze_file(row["path"])
            conn.execute(
                """UPDATE samples SET bpm=?, key=?, duration=?, brightness=?,
                   punch=?, loudness=?, analyzed_at=? WHERE id=?""",
                (feats["bpm"], feats["key"], feats["duration"],
                 feats["brightness"], feats["punch"], feats["loudness"],
                 time.time(), row["id"]))
            done += 1
        except Exception as exc:
            failed += 1
            if progress:
                print(f"  ! {Path(row['path']).name}: {exc}", file=sys.stderr)
        if progress and (i + 1) % 200 == 0:
            rate = (i + 1) / max(time.time() - t0, 1e-9)
            remaining = (len(rows) - i - 1) / max(rate, 1e-9)
            print(f"  {i + 1}/{len(rows)} analyzed "
                  f"(~{remaining / 60:.0f} min remaining)", flush=True)
        if (i + 1) % 50 == 0:
            conn.commit()
    conn.commit()
    conn.close()
    return done, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=None,
                    help="analyze a single file and print JSON (no database)")
    ap.add_argument("--db", default=None, help="database file")
    ap.add_argument("--limit", type=int, default=None,
                    help="analyze at most N files this run")
    args = ap.parse_args(argv)

    if not HAVE_LIBROSA:
        print("note: librosa not installed — using the built-in fallback "
              "engine (WAV-only, rougher BPM). `pip install librosa` for "
              "the good stuff.", file=sys.stderr)

    if args.file:
        print(json.dumps(analyze_file(args.file), indent=2))
        return 0

    done, failed = analyze_pending(args.db, args.limit)
    print(f"Analysis done: {done} files, {failed} failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
