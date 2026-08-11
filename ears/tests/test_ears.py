"""Ears test suite — validates the loudness meter against known signals
and proves the whole analyze_bounce chain runs. No real bounces needed.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import audio_io      # noqa: E402
import loudness      # noqa: E402
import spectrogram   # noqa: E402
import analyze_bounce  # noqa: E402

SR = 48000


def write_wav(path, samples, sr=SR):
    """samples: (n,) mono or (n, ch)."""
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
# loudness: calibration against BS.1770 known values
# ---------------------------------------------------------------------------

def test_lufs_sine_calibration():
    """BS.1770: a 997 Hz sine at -18 dBFS in one channel of a stereo file
    measures ≈ -18 LUFS (K-weighting is ~0 dB at 1 kHz)."""
    amp = 10 ** (-18 / 20) * np.sqrt(2) / np.sqrt(2)  # -18 dBFS sine peak
    x = sine(997, 5.0, 10 ** (-18 / 20) * 1.41421356)
    stereo = np.stack([x, np.zeros_like(x)], axis=1)
    lufs, _ = loudness.integrated_lufs(stereo, SR)
    assert abs(lufs - (-18.0)) < 0.5


def test_lufs_gain_tracking():
    """Dropping the signal 6 dB must drop LUFS by 6."""
    x = sine(997, 4.0, 0.5)
    stereo = np.stack([x, x], axis=1)
    l1, _ = loudness.integrated_lufs(stereo, SR)
    l2, _ = loudness.integrated_lufs(stereo * 0.5, SR)
    assert abs((l1 - l2) - 6.0) < 0.2


def test_gating_ignores_silence():
    """Loud passage + long silence ≈ loudness of the loud passage alone
    (the gate discards silence instead of averaging it in)."""
    x = sine(997, 3.0, 0.5)
    silence = np.zeros(SR * 10)
    both = np.concatenate([x, silence])
    l_loud, _ = loudness.integrated_lufs(np.stack([x, x], 1), SR)
    l_both, _ = loudness.integrated_lufs(np.stack([both, both], 1), SR)
    assert abs(l_loud - l_both) < 1.0


def test_true_peak_finds_intersample_peak():
    """A full-scale sine's true peak is ~0 dBTP even when samples miss
    the crest."""
    x = sine(997.7, 1.0, 0.99)
    tp = loudness.true_peak_dbtp(np.stack([x, x], 1), SR)
    assert -0.3 < tp < 0.3


def test_band_energy_locates_sub():
    x = sine(45, 3.0, 0.7)  # pure sub tone
    be = loudness.band_energy(np.stack([x, x], 1), SR)
    assert be["sub"] == 0.0                     # loudest band is reference
    assert all(v < -30 for k, v in be.items() if k != "sub")


# ---------------------------------------------------------------------------
# spectrogram + orchestrator
# ---------------------------------------------------------------------------

def test_spectrogram_renders_png(tmp_path):
    f = tmp_path / "mix.wav"
    write_wav(f, sine(200, 2.0, 0.5) + sine(3000, 2.0, 0.2))
    out = spectrogram.render(f)
    assert out.exists() and out.stat().st_size > 10_000
    assert out.suffix == ".png"


def test_analyze_bounce_end_to_end(tmp_path):
    f = tmp_path / "club_mix.wav"
    # a crude "track": kick thumps + sub + some highs, 4 seconds
    t = np.arange(SR * 4) / SR
    kick = np.sin(2 * np.pi * 55 * t) * np.exp(-np.mod(t, 0.5) * 18)
    highs = np.random.default_rng(0).standard_normal(len(t)) * 0.05
    write_wav(f, np.stack([kick * 0.8 + highs, kick * 0.8 + highs], 1))
    m = analyze_bounce.analyze(f)
    assert Path(m["spectrogram_png"]).exists()
    assert Path(m["report_json"]).exists()
    saved = json.loads(Path(m["report_json"]).read_text())
    assert saved["integrated_lufs"] < 0
    assert "summary" in saved and saved["duration_s"] == pytest.approx(4.0, abs=0.1)
    assert m["band_energy_db"]["sub"] == 0.0    # kick+sub dominates
