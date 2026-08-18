"""Unit tests for the Arrangement Doctor.

The fixture is a stripped copy of the real "Bad and Boujee Edit" set as it
stood on 2026-08-17 — the session where the ears said "1 dB from the
reference" and the producer said "it sounds boring". These tests lock in
the behaviour that catches the second opinion.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from arrangement_doctor import (  # noqa: E402
    analyze, classify_role, classify_roles, format_report,
)


def clips(*bar_pairs, muted=False, name=""):
    return [{"start_time": (a - 1) * 4.0, "end_time": (b - 1) * 4.0,
             "muted": muted, "name": name} for a, b in bar_pairs]


def track(index, name, clip_list, muted=False):
    return {"index": index - 1, "name": name, "muted": muted,
            "arrangement_clips": clip_list}


@pytest.fixture
def bandb():
    """The real arrangement, trimmed to what matters for these assertions."""
    return [
        track(1, "REF", clips((1, 108), name="ACRAZE - Do It To It")),
        track(3, "2.KICK & SNARE", clips((30, 38), (38, 46), (62, 70), (70, 78))),
        track(9, "9-EvoSounds - Hat Loops - Wide Doppler", clips((34, 46), (66, 70), (74, 78))),
        track(10, "10-EvoSounds - Shaker Loops", clips((34, 46), (66, 70), (74, 78))),
        track(12, "iDEA LD 2", clips((30, 38)), muted=True),          # muted at mixer
        track(15, "iDEA LD 1", clips((30, 34), (38, 42), (62, 66), (70, 74))),
        track(21, "SUB (MIDI)", clips((30, 46), (62, 78))),
        track(30, "TRIGGER", clips((30, 46))),                        # infrastructure
        track(44, "44-Migos Bad and Boujee Acapella",
              clips((34, 41)) + clips((30, 34), muted=True)),
        track(45, "45-Migos chops", clips(*[(21 + i // 4, 21.25 + i // 4)
                                            for i in range(32)])),
        track(53, "Piano", clips((46, 54), name="Break chords D#m")),
    ]


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------

def test_multi_role_finds_the_hidden_snare():
    """"KICK & SNARE" is two roles — reporting only 'kick' would hide a
    missing backbeat, which is exactly the bug that let a thin drop pass."""
    roles = classify_roles("2.KICK & SNARE")
    assert "kick" in roles and "clap/snare" in roles


def test_track_name_beats_clip_name():
    # Piano track holding a clip named "Break chords" is still a chord role,
    # and must not be dragged elsewhere by clip wording.
    assert classify_roles("Piano", "Break chords D#m i-VI-iv-V") == ["chord"]


@pytest.mark.parametrize("name,expected", [
    ("SUB (MIDI)", "sub"),
    ("9-EvoSounds - Hat Loops - Wide Doppler", "hat"),
    ("10-EvoSounds - Shaker Loops", "perc"),
    ("RISE 2", "riser"),
    ("IMPACT 1", "impact"),
    ("44-Migos Bad and Boujee Acapella", "vocal"),
    ("iDEA LD 1", "lead"),
])
def test_role_classification(name, expected):
    assert expected in classify_roles(name)


def test_unclassified_is_explicit():
    assert classify_roles("17-Audio", "") == ["unclassified"]


# ---------------------------------------------------------------------------
# element counting
# ---------------------------------------------------------------------------

def test_clip_fragments_are_one_element(bandb):
    """32 vocal-chop clips on one track are ONE element (the chop layer).
    Counting clips instead inflated a 5-element block to 23."""
    res = analyze(bandb, start_bar=21, end_bar=25, boundaries=[21, 25])
    block = res["blocks"][0]
    assert block["element_count"] == 1
    assert block["elements"] == ["45-Migos chops"]


def test_mixer_muted_track_is_silent(bandb):
    """iDEA LD 2 is muted at the mixer — it must not count as an element."""
    res = analyze(bandb, start_bar=30, end_bar=38, boundaries=[30, 38])
    assert "iDEA LD 2" not in res["blocks"][0]["elements"]


def test_reference_and_trigger_tracks_excluded(bandb):
    res = analyze(bandb, start_bar=30, end_bar=38, boundaries=[30, 38])
    elements = res["blocks"][0]["elements"]
    assert "REF" not in elements and "TRIGGER" not in elements


def test_muted_clip_is_silent(bandb):
    """The vocal at 30-34 is a muted clip; the drop's first block has no vocal."""
    res = analyze(bandb, start_bar=30, end_bar=34, boundaries=[30, 34])
    assert "vocal" not in res["blocks"][0]["roles_present"]


# ---------------------------------------------------------------------------
# the findings that matter
# ---------------------------------------------------------------------------

def test_break_is_diagnosed_as_one_element(bandb):
    res = analyze(bandb, start_bar=46, end_bar=54, boundaries=[46, 54])
    block = res["blocks"][0]
    assert block["element_count"] == 1
    assert block["density"] == "sparse"


def test_drop_two_has_no_vocal(bandb):
    """The headline finding: the second half is missing the hook entirely."""
    res = analyze(bandb, start_bar=62, end_bar=78, boundaries=[62, 70, 78])
    for block in res["blocks"]:
        assert "vocal" in block["missing_roles"]


def test_bass_never_used_anywhere(bandb):
    """Sub is present but there is no bass MID layer — sub is felt, the mid
    layer is what's heard. This is why the drop reads as empty."""
    res = analyze(bandb, start_bar=1, end_bar=80)
    assert "bass" in res["roles_never_used"]


def test_identical_blocks_are_flagged():
    """The boredom detector: same tracks, back-to-back."""
    same = [track(3, "KICK", clips((1, 9))), track(9, "HAT", clips((1, 9)))]
    res = analyze(same, start_bar=1, end_bar=9, block_bars=4)
    assert res["blocks"][1]["identical_to_previous"] is True
    assert res["summary"]["repetition_pct"] == 50


def test_summary_reports_thin_average(bandb):
    res = analyze(bandb, start_bar=30, end_bar=78, boundaries=[30, 38, 46, 54, 62, 70, 78])
    # Nowhere near the 18-25 a commercial drop carries.
    assert res["summary"]["avg_elements"] < 10


def test_report_is_readable(bandb):
    text = format_report(analyze(bandb, start_bar=30, end_bar=46,
                                 boundaries=[30, 38, 46]))
    assert "Arrangement Doctor" in text
    assert "MISSING" in text
    assert "elements per 8-bar block" in text
