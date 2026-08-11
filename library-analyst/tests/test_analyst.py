"""Library Analyst test suite — runs anywhere, no real samples needed.

Builds a tiny synthetic sample library with KNOWN properties (a dark
50 Hz kick, a bright noise hat, a 140 BPM bass loop, an F-minor pad) and
verifies the whole chain: scan → analyze → search → similarity → stats.
"""
import math
import struct
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db as dbmod            # noqa: E402
import scanner                # noqa: E402
import analysis               # noqa: E402
import search                 # noqa: E402
from taxonomy import categorize  # noqa: E402

SR = 22050


def write_wav(path, samples, sr=SR):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.clip(samples, -1.0, 1.0)
    ints = (data * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(ints.tobytes())


def synth_kick(dur=0.5):
    """Dark one-shot: 50 Hz sine with a fast decay."""
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * 50 * t) * np.exp(-t * 8)


def synth_hat(dur=0.15, seed=7):
    """Bright one-shot: white noise burst."""
    rng = np.random.default_rng(seed)
    env = np.exp(-np.arange(int(dur * SR)) / SR * 40)
    return rng.standard_normal(int(dur * SR)) * env * 0.5


def synth_bass_loop(bpm=140.0, bars=2, freq=87.31):  # F2
    """Loop: an F bass note pulsing on every beat at `bpm`."""
    beat = 60.0 / bpm
    n = int(bars * 4 * beat * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    env = np.exp(-np.mod(t, beat) * 12)
    return tone * env * 0.8


def synth_pad_f_minor(dur=4.0):
    """Sustained F minor chord: F3, Ab3, C4 (+octave root)."""
    t = np.arange(int(dur * SR)) / SR
    freqs = [174.61, 207.65, 261.63, 349.23]
    sig = sum(np.sin(2 * np.pi * f * t) for f in freqs)
    fade = np.minimum(1, np.minimum(t / 0.2, (dur - t) / 0.2))
    return sig / len(freqs) * fade * 0.7


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    """A scanned + analyzed synthetic library. Returns (root, db_path)."""
    root = tmp_path_factory.mktemp("samples")
    db_path = tmp_path_factory.mktemp("db") / "test.sqlite3"
    write_wav(root / "Drums" / "Kicks" / "deep_kick_01.wav", synth_kick())
    write_wav(root / "Drums" / "Hats" / "crispy_hat_01.wav", synth_hat())
    write_wav(root / "Bass" / "Loops" / "dark_bass_loop_140.wav", synth_bass_loop())
    write_wav(root / "Synths" / "Pads" / "warm_pad_Fmin.wav", synth_pad_f_minor())
    added, updated, unchanged = scanner.scan([root], db_path, progress=False)
    assert (added, updated, unchanged) == (4, 0, 0)
    done, failed = analysis.analyze_pending(db_path, progress=False)
    assert (done, failed) == (4, 0)
    return root, db_path


# ---------------------------------------------------------------------------
# scanner
# ---------------------------------------------------------------------------

def test_rescan_is_incremental(library):
    root, db_path = library
    added, updated, unchanged = scanner.scan([root], db_path, progress=False)
    assert (added, updated, unchanged) == (0, 0, 4)


def test_changed_file_resets_analysis(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    f = tmp_path / "Kicks" / "kick.wav"
    write_wav(f, synth_kick())
    scanner.scan([tmp_path], db_path, progress=False)
    analysis.analyze_pending(db_path, progress=False)
    write_wav(f, synth_hat())  # same path, new contents
    import os
    os.utime(f, (1, 1))        # force a different mtime
    added, updated, unchanged = scanner.scan([tmp_path], db_path, progress=False)
    assert updated == 1
    conn = dbmod.connect(db_path)
    assert conn.execute("SELECT analyzed_at FROM samples").fetchone()[0] is None


def test_missing_file_flagged(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    f = tmp_path / "Perc" / "shaker.wav"
    write_wav(f, synth_hat(seed=3))
    scanner.scan([tmp_path], db_path, progress=False)
    f.unlink()
    scanner.scan([tmp_path], db_path, progress=False)
    conn = dbmod.connect(db_path)
    assert conn.execute("SELECT missing FROM samples").fetchone()[0] == 1


# ---------------------------------------------------------------------------
# taxonomy + analysis
# ---------------------------------------------------------------------------

def test_categorize_from_folder_names():
    assert categorize(r"D:\Samples\Drums\Kicks\deep_kick_01.wav") == "kick"
    assert categorize("/x/Bass/Loops/dark_bass_loop_140.wav") == "bass"
    assert categorize("/x/foo/Vocal Chops/oohlala.wav") == "vocal"
    assert categorize("/x/misc/unknowable.wav") is None


def test_features_make_physical_sense(library):
    root, db_path = library
    conn = dbmod.connect(db_path)
    rows = {r["filename"]: dict(r) for r in
            conn.execute("SELECT * FROM samples").fetchall()}
    kick = rows["deep_kick_01.wav"]
    hat = rows["crispy_hat_01.wav"]
    pad = rows["warm_pad_Fmin.wav"]
    loop = rows["dark_bass_loop_140.wav"]

    assert hat["brightness"] > kick["brightness"] * 3   # noise ≫ 50 Hz sine
    assert kick["duration"] < 1.0 < pad["duration"]
    assert kick["bpm"] is None                          # one-shots: no tempo
    assert pad["key"] == "F minor"
    assert loop["key"].startswith("F")                  # F-rooted bass
    assert kick["punch"] > pad["punch"]                 # transient vs sustained


def test_bpm_detection_on_loop(library):
    root, db_path = library
    conn = dbmod.connect(db_path)
    bpm = conn.execute(
        "SELECT bpm FROM samples WHERE filename = 'dark_bass_loop_140.wav'"
    ).fetchone()[0]
    assert bpm is not None
    # accept the half/double-tempo ambiguity every tempo detector has
    assert any(abs(bpm - target) < 5 for target in (70, 140, 280))


def test_bpm_from_filename():
    assert analysis.bpm_from_filename("XLNT - Full Loop 19 - Dubstep - 140bpm.wav") == 140
    assert analysis.bpm_from_filename("groove_128 BPM_dark.wav") == 128
    assert analysis.bpm_from_filename("bpm90_shuffle.wav") == 90
    assert analysis.bpm_from_filename("808_kick.wav") is None       # 808 ≠ bpm
    assert analysis.bpm_from_filename("no_tempo_here.wav") is None


def test_filename_bpm_wins(tmp_path):
    f = tmp_path / "Loops" / "test_loop_133bpm.wav"
    write_wav(f, synth_bass_loop(bpm=140.0))  # detector would say ~140
    feats = analysis.analyze_file(f)
    assert feats["bpm"] == 133 and feats["bpm_source"] == "filename"


def test_analyze_single_file(library):
    root, _ = library
    feats = analysis.analyze_file(root / "Synths" / "Pads" / "warm_pad_Fmin.wav")
    assert feats["key"] == "F minor"
    assert 3.5 < feats["duration"] < 4.5


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def test_find_sounds_dark_bass(library):
    _, db_path = library
    hits = search.find_sounds("dark bass", db_path=db_path)
    assert hits and hits[0]["filename"] == "dark_bass_loop_140.wav"


def test_find_sounds_the_magic_test(library):
    """The plan's magic test: 'dark textured bass one-shot near F minor'
    (our library's closest thing is the F bass loop — it must top the
    kick/hat/pad)."""
    _, db_path = library
    hits = search.find_sounds("dark bass near F minor", db_path=db_path)
    assert hits[0]["filename"] == "dark_bass_loop_140.wav"
    assert hits[0]["key"].startswith("F")


def test_find_sounds_bright_oneshot(library):
    _, db_path = library
    hits = search.find_sounds("bright one-shot", category="hat", db_path=db_path)
    assert hits and hits[0]["filename"] == "crispy_hat_01.wav"


def test_find_sounds_bpm_filter(library):
    _, db_path = library
    hits = search.find_sounds("", bpm_range=(130, 150), db_path=db_path)
    files = [h["filename"] for h in hits]
    assert files == ["dark_bass_loop_140.wav"]


def test_key_parsing_variants():
    assert search.parse_key("something near F minor") == "F minor"
    assert search.parse_key("f# min pluck") == "F# minor"
    assert search.parse_key("Ab") == "G# major"
    assert search.parse_key("no key here") is None


def test_neighboring_keys():
    ks = search.neighboring_keys("F minor")
    assert "F minor" in ks and "G# major" in ks     # relative major of Fm = Ab
    assert "F# minor" in ks and "E minor" in ks


def test_similar_to(library):
    _, db_path = library
    sims = search.similar_to("warm_pad_Fmin.wav", db_path=db_path)
    assert len(sims) == 3 and sims[0]["filename"] != "warm_pad_Fmin.wav"
    # distances come back sorted, nearest first
    assert sims[0]["distance"] <= sims[-1]["distance"]
    # for a long dark tonal pad, the long dark tonal bass loop must rank
    # closer than a short bright noise hat (differs on every feature)
    files = [s["filename"] for s in sims]
    assert files.index("dark_bass_loop_140.wav") < files.index("crispy_hat_01.wav")


def test_library_stats(library):
    _, db_path = library
    st = search.library_stats(db_path=db_path)
    assert st["total_files"] == 4 and st["analyzed"] == 4
    assert st["by_category"]["kick"] == 1
    assert st["loops"] + st["one_shots"] == 4
