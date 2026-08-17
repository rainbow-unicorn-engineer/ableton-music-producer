"""Reverse-engineering pipeline tests — structure analyzer, reference
cards, compare_mix, MIDI extraction (fallback engine), and the Demucs
wrapper's guard rails. All on synthetic audio; no real tracks needed.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import compare_mix    # noqa: E402
import midi_extract   # noqa: E402
import references     # noqa: E402
import stems          # noqa: E402
import structure      # noqa: E402

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


def two_part_track(bpm=120.0, bars_each=16):
    """Synthetic arrangement: quiet mid-frequency intro (no sub), then a
    loud drop with a heavy 50 Hz sub. The simplest track with structure."""
    bar_s = 4 * 60.0 / bpm
    intro = sine(400, bars_each * bar_s, 0.05)
    drop = (sine(50, bars_each * bar_s, 0.6)
            + sine(400, bars_each * bar_s, 0.25))
    return np.concatenate([intro, drop])


# ---------------------------------------------------------------------------
# structure.py
# ---------------------------------------------------------------------------

def test_bpm_from_filename():
    assert structure.bpm_from_filename("ref 140bpm.wav") == 140
    assert structure.bpm_from_filename("Weekend flip BPM 96.wav") == 96
    assert structure.bpm_from_filename("no tempo here.wav") is None


def test_detect_bpm_click_track():
    """Clicks every 0.5 s = 120 BPM; the detector should find it."""
    n = SR * 20
    y = np.zeros(n)
    rng = np.random.default_rng(1)
    for start in range(0, n, SR // 2):
        y[start:start + 400] = rng.standard_normal(400) * 0.8
    bpm = structure.detect_bpm(y, SR)
    assert bpm is not None and abs(bpm - 120.0) < 3.0


def test_structure_finds_intro_and_drop(tmp_path):
    f = tmp_path / "twopart.wav"
    write_wav(f, two_part_track())
    r = structure.analyze_structure(f, bpm=120.0)
    assert r["total_bars"] == 32
    assert r["bpm"] == 120.0 and r["bpm_source"] == "given"
    labels = [s["label"] for s in r["sections"]]
    assert labels[0] == "intro"
    assert "drop" in labels
    drop = r["sections"][labels.index("drop")]
    assert drop["sub_presence"] >= structure.SUB_PRESENT_RATIO
    assert abs(drop["length_bars"] - 16) <= 1
    assert "intro" in r["skeleton"] and "drop" in r["skeleton"]


def test_structure_png(tmp_path):
    f = tmp_path / "twopart 120bpm.wav"       # tempo read from filename
    write_wav(f, two_part_track())
    r = structure.analyze_structure(f, png=True)
    assert r["bpm_source"] == "filename"
    assert Path(r["structure_png"]).exists()
    assert Path(r["structure_png"]).stat().st_size > 5_000


# ---------------------------------------------------------------------------
# references.py
# ---------------------------------------------------------------------------

def test_reference_card_roundtrip(tmp_path):
    f = tmp_path / "my_ref.wav"
    write_wav(f, two_part_track())
    refs = tmp_path / "refs"
    card = references.make_card(f, name="My Ref!", refs_dir=refs, bpm=120.0)
    assert card["name"] == "my-ref"                     # slugged
    assert Path(card["card_path"]).exists()
    assert Path(card["spectrogram_png"]).exists()
    assert card["integrated_lufs"] < 0
    assert card["structure"] and "drop" in card["structure"]["skeleton"]

    listed = references.list_cards(refs)
    assert [c["name"] for c in listed] == ["my-ref"]

    loaded = references.load_card("my ref", refs_dir=refs)   # fuzzy
    assert loaded["integrated_lufs"] == card["integrated_lufs"]

    with pytest.raises(FileNotFoundError):
        references.load_card("does-not-exist", refs_dir=refs)


# ---------------------------------------------------------------------------
# compare_mix.py
# ---------------------------------------------------------------------------

def test_compare_against_audio_reference(tmp_path):
    ref = tmp_path / "reference.wav"
    write_wav(ref, two_part_track())
    mine = tmp_path / "bounce.wav"
    write_wav(mine, two_part_track() * 0.3)   # ~10.5 dB quieter, same shape
    r = compare_mix.compare(mine, ref)
    assert r["lufs"]["delta"] < -6.0
    assert any("quieter" in g for g in r["gaps"])
    assert set(r["band_delta_db"]) == {"sub", "bass", "low-mid", "mid",
                                       "high-mid", "high"}
    assert "gap" in r["verdict"]


def test_compare_against_card(tmp_path):
    ref = tmp_path / "reference.wav"
    write_wav(ref, two_part_track())
    refs = tmp_path / "refs"
    references.make_card(ref, name="target", refs_dir=refs, bpm=120.0)
    old = references.REFS_DIR
    references.REFS_DIR = refs
    try:
        mine = tmp_path / "bounce.wav"
        write_wav(mine, two_part_track())     # identical → no gaps
        r = compare_mix.compare(mine, "target")
        assert r["reference_kind"] == "reference card"
        assert abs(r["lufs"]["delta"]) < 0.5
        assert r["gaps"] == []
        assert "Within range" in r["verdict"]
    finally:
        references.REFS_DIR = old


# ---------------------------------------------------------------------------
# midi_extract.py — fallback engine
# ---------------------------------------------------------------------------

def test_midi_extract_melody(tmp_path):
    f = tmp_path / "melody.wav"
    # A3 → E4 → A4, half a second each, clean sines
    mel = np.concatenate([sine(220.0, 0.5, 0.5),
                          sine(329.63, 0.5, 0.5),
                          sine(440.0, 0.5, 0.5)])
    write_wav(f, mel)
    r = midi_extract.extract(f, bpm=120.0)
    assert r["engine"].startswith(("fallback", "basic-pitch"))
    got = [n["midi"] for n in r["notes"]]
    assert got == [57, 64, 69]
    assert r["pitch_range"] == "A3–A4"
    midi_bytes = Path(r["midi_file"]).read_bytes()
    assert midi_bytes[:4] == b"MThd" and b"MTrk" in midi_bytes


def test_midi_extract_silence(tmp_path):
    f = tmp_path / "silence.wav"
    write_wav(f, np.zeros(SR))
    r = midi_extract.extract(f)
    assert r["note_count"] == 0 and r["pitch_range"] is None


def test_midi_var_len_encoding():
    assert midi_extract._var_len(0) == b"\x00"
    assert midi_extract._var_len(127) == b"\x7f"
    assert midi_extract._var_len(128) == b"\x81\x00"
    assert midi_extract._var_len(100000) == b"\x86\x8d\x20"


# ---------------------------------------------------------------------------
# stems.py — guard rails (Demucs itself only runs on the studio machine)
# ---------------------------------------------------------------------------

def test_stems_build_command(tmp_path):
    import os
    os.environ.pop(stems.DEMUCS_ENV_VAR, None)
    cmd = stems.build_command("ref.wav", tmp_path, model="htdemucs",
                              two_stems="vocals")
    assert cmd[0] == sys.executable       # no env var, no demucs → this python
    assert cmd[1:3] == ["-m", "demucs"]
    assert "--two-stems" in cmd and cmd[cmd.index("--two-stems") + 1] == "vocals"
    assert cmd[-1] == "ref.wav"
    assert cmd[cmd.index("-n") + 1] == "htdemucs"


def test_stems_env_var_picks_other_python(tmp_path):
    """XLNT_DEMUCS points the wrapper at another env's interpreter —
    the escape hatch for 'Demucs wants Python 3.11'."""
    import os
    os.environ[stems.DEMUCS_ENV_VAR] = r"C:\envs\xlnt-audio\python.exe"
    try:
        assert stems.demucs_available()
        cmd = stems.build_command("ref.wav", tmp_path)
        assert cmd[0] == r"C:\envs\xlnt-audio\python.exe"
    finally:
        os.environ.pop(stems.DEMUCS_ENV_VAR, None)


def test_stems_missing_demucs_message(tmp_path):
    import os
    os.environ.pop(stems.DEMUCS_ENV_VAR, None)
    if stems.demucs_available():
        pytest.skip("demucs installed here — guard rail not reachable")
    f = tmp_path / "mix.wav"
    write_wav(f, sine(200, 1.0, 0.5))
    with pytest.raises(RuntimeError, match="pip install demucs"):
        stems.separate(f)
