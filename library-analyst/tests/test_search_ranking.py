"""Unit tests for search ranking — the fix for the 'ten 808s for every
query' bug. Pure functions only; no database needed."""
import sys, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_a = types.ModuleType("analysis")
_a.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
sys.modules.setdefault("analysis", _a)
sys.modules.setdefault("db", types.ModuleType("db"))

from search import (expand_term, parse_query, score_terms, split_path,
                    _bpm_score, _stem)

REVERSE_DOWNLIFTER = (r"C:\Music Production\User Library\Samples\Processed"
                      r"\Reverse\Evolution Of Sound - Downlifter 10 G 124BPM R.wav")
CYMBAL = r"C:\Music Production\User Library\Samples\Cymbals\909 Cymbal Crash 1.wav"
EIGHT_OH_EIGHT = r"C:\Music Production\User Library\808 Subs\808_sub.wav"
UPLIFTER = r"C:\Music Production\User Library\FX\EvoSounds - Uplifters - Super 6.wav"
LONG_RISER = r"C:\Music Production\User Library\FX\XLNT-FX Long Riser 13.wav"


def s(query, path):
    terms = [expand_term(w) for w in parse_query(query)["text_words"]]
    return score_terms(terms, path)[0]


def test_irrelevant_files_score_zero():
    """The actual bug: 'reverse cymbal swell' returned ten 808s."""
    assert s("reverse cymbal swell", EIGHT_OH_EIGHT) == 0.0


def test_relevant_beats_irrelevant():
    assert s("reverse cymbal swell", CYMBAL) > s("reverse cymbal swell", EIGHT_OH_EIGHT)


def test_synonyms_find_differently_named_files():
    """'riser' must find a file called Uplifter — nobody types both."""
    assert s("riser", UPLIFTER) > 0


def test_filename_beats_folder():
    """A word in the file's own name means more than the same word in a
    folder every sample in the pack shares."""
    assert s("riser", LONG_RISER) > s("reverse", REVERSE_DOWNLIFTER)


def test_matching_more_words_ranks_higher():
    two = s("reverse riser", r"C:\lib\Reverse Riser Sweep.wav")
    one = s("reverse riser", r"C:\lib\Reverse Crash.wav")
    assert two > one


def test_plural_stemming():
    assert _stem("cymbals") == "cymbal"
    assert s("cymbals", CYMBAL) > 0


def test_category_word_still_matches_filenames():
    """Old bug: 'riser' was consumed as a category hint and never used as
    a search word, so it couldn't find files literally named Riser."""
    q = parse_query("riser")
    assert q["category_hint"] == "fx"
    assert "riser" in q["text_words"]


def test_bare_tempo_number_is_a_bpm_hint_not_a_word():
    q = parse_query("hat loop 124")
    assert q["bpm_hint"] == 124.0
    assert "124" not in q["text_words"]


def test_half_time_loops_score():
    """A 62 BPM loop sits perfectly in a 124 BPM track."""
    assert _bpm_score(62, 124) > 0
    assert _bpm_score(124, 124) > _bpm_score(62, 124)
    assert _bpm_score(150, 124) == 0.0


def test_stopwords_dropped():
    assert parse_query("find me some kind of sound")["text_words"] == ["kind"]


def test_split_path_strips_extension():
    fname, folder, _ = split_path(CYMBAL)
    assert fname == "909 cymbal crash 1"
    assert folder == "cymbals"
