"""Vocal-tools tests — the clash analyzer on synthetic vocal/beat pairs
and the mashup matcher's key/tempo math. All synthetic; no real vocals.
"""
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import clash    # noqa: E402
import mashup   # noqa: E402

SR = 44100


def write_wav(path, samples, sr=SR):
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(samples)
    if arr.ndim == 1:
        arr = arr[:, None]
    ints = (np.clip(arr, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(arr.shape[1])
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(ints.tobytes())


def sine(freq, seconds, amp, sr=SR):
    t = np.arange(int(seconds * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t)


# ---------------------------------------------------------------------------
# clash.py
# ---------------------------------------------------------------------------

def test_clash_detected_when_sharing_a_band(tmp_path):
    """'Vocal' at 300 Hz vs a beat that ALSO lives at 300 Hz: the low-mid
    band must be heavily contested and the peak near 300 Hz."""
    vocal = tmp_path / "vocal.wav"
    beat = tmp_path / "beat.wav"
    write_wav(vocal, sine(300, 4.0, 0.5))
    write_wav(beat, sine(300, 4.0, 0.45) + sine(55, 4.0, 0.4))
    r = clash.analyze_clash(vocal, beat, "vocal", "beat")
    lowmid = next(b for b in r["bands"] if b["band"] == "low-mid")
    assert lowmid["contested_pct"] > 80.0
    assert abs(r["peak_clash_hz"] - 300) < 60
    assert r["fixes"] and "low-mid" in r["fixes"][0]


def test_no_clash_when_bands_disjoint(tmp_path):
    """Vocal at 300 Hz vs a sub-only beat: nothing to fight over."""
    vocal = tmp_path / "vocal.wav"
    beat = tmp_path / "beat.wav"
    write_wav(vocal, sine(300, 4.0, 0.5))
    write_wav(beat, sine(45, 4.0, 0.6))
    r = clash.analyze_clash(vocal, beat, "vocal", "beat")
    assert all(b["contested_pct"] < 10.0 for b in r["bands"])
    assert r["fixes"] == []
    assert "coexist" in r["verdict"]


def test_clash_png(tmp_path):
    vocal = tmp_path / "vocal.wav"
    beat = tmp_path / "beat.wav"
    write_wav(vocal, sine(300, 2.0, 0.5))
    write_wav(beat, sine(300, 2.0, 0.5))
    r = clash.analyze_clash(vocal, beat, png=True)
    assert Path(r["clash_png"]).exists()
    assert Path(r["clash_png"]).stat().st_size > 5_000


def test_clash_rejects_mismatched_sample_rates(tmp_path):
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    write_wav(a, sine(300, 1.0, 0.5), sr=44100)
    write_wav(b, sine(300, 1.0, 0.5), sr=48000)
    with pytest.raises(RuntimeError, match="[Ss]ample rates differ"):
        clash.analyze_clash(a, b)


# ---------------------------------------------------------------------------
# mashup.py — key math
# ---------------------------------------------------------------------------

def test_relative_keys_need_no_shift():
    assert mashup.semitone_shift("A minor", "C major") == 0
    assert mashup.semitone_shift("C major", "A minor") == 0
    assert mashup.semitone_shift("G minor", "G minor") == 0


def test_shift_picks_smallest_direction():
    assert mashup.semitone_shift("A minor", "D minor") == 5
    assert mashup.semitone_shift("A minor", "F minor") == -4
    assert mashup.semitone_shift("G major", "F# major") == -1
    assert abs(mashup.semitone_shift("C major", "F# major")) == 6


def test_compatible_keys():
    assert mashup.compatible_keys("G minor") == ["G minor", "A# major"]
    assert mashup.compatible_keys("C major") == ["C major", "A minor"]


# ---------------------------------------------------------------------------
# mashup.py — tempo math
# ---------------------------------------------------------------------------

def test_tempo_small_stretch_is_clean():
    plan = mashup.tempo_plan(140.0, 144.0)
    assert plan["feel"] == "straight"
    assert plan["stretch_pct"] == pytest.approx(2.86, abs=0.01)
    assert plan["clean"]


def test_tempo_prefers_halftime_over_huge_stretch():
    plan = mashup.tempo_plan(72.0, 144.0)   # 72 vocal over 144 beat
    assert "half-time" in plan["feel"]
    assert plan["stretch_pct"] == pytest.approx(0.0, abs=0.01)


def test_tempo_flags_ugly_stretch():
    plan = mashup.tempo_plan(100.0, 128.0)
    assert not plan["clean"]                # 28% or half-time 36% — both ugly


# ---------------------------------------------------------------------------
# mashup.py — end to end with overrides
# ---------------------------------------------------------------------------

def test_match_end_to_end(tmp_path):
    vox = tmp_path / "vox 140bpm.wav"
    beat = tmp_path / "beat 144bpm.wav"
    write_wav(vox, sine(220, 2.0, 0.5))
    write_wav(beat, sine(98, 2.0, 0.5))
    r = mashup.match(vox, beat, acapella_key="A minor", beat_key="G minor")
    assert r["acapella"]["bpm"] == 140 and r["beat"]["bpm"] == 144
    assert r["semitone_shift"] == -2
    assert r["tempo"]["clean"]
    assert any("Transpose" in s for s in r["steps"])
    assert any("Warp" in s for s in r["steps"])
    assert r["no_transpose_keys"] == ["G minor", "A# major"]


def test_match_requires_key_or_override(tmp_path):
    vox = tmp_path / "vox.wav"          # no bpm in name
    beat = tmp_path / "beat.wav"
    write_wav(vox, np.zeros(SR))        # silence: no key, no bpm
    write_wav(beat, np.zeros(SR))
    with pytest.raises(RuntimeError, match="overrides"):
        mashup.match(vox, beat)
