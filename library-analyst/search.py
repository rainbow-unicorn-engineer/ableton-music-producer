"""search.py — turn words into database queries.

`find_sounds("reverse cymbal swell", key="D# minor")` maps descriptive
words onto (a) the numeric features analysis.py stored and (b) the words
in the file's own name and folders — which, in a sample library, is where
almost all the meaning actually lives.

* dark / bright        → brightness (spectral centroid) below / above the
                         library's own median — *"dark" is relative to
                         YOUR sounds, not some universal constant*
* punchy / soft        → punch above / below median
* loud / quiet         → loudness above / below median
* one-shot / loop      → duration under / over 2 seconds
* kick, bass, vocal... → category (a strong hint, not a hard filter)
* every other word     → matched against file name and folders, with
                         synonyms ("riser" also finds "uplifter"), plural
                         stemming, and a bonus for matching MORE of the
                         query

**Rewritten 2026-08-18.** The old version silently returned arbitrary
rows when nothing matched — a search for "reverse cymbal" came back with
ten 808s, all scored 0.0, which reads exactly like ten good matches.
Now: rows that match none of the query words are dropped, every result
carries `matched_terms` explaining *why* it is there, and a search that
finds nothing says so.
"""

import math
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import db as dbmod
    from taxonomy import CATEGORY_PATTERNS
    from analysis import NOTE_NAMES
else:
    from . import db as dbmod
    from .taxonomy import CATEGORY_PATTERNS
    from .analysis import NOTE_NAMES

ONESHOT_MAX_SECONDS = 2.0

_FEATURE_WORDS = {
    "dark":     ("brightness", "low"),  "deep":   ("brightness", "low"),
    "warm":     ("brightness", "low"),  "dull":   ("brightness", "low"),
    "muffled":  ("brightness", "low"),
    "bright":   ("brightness", "high"), "sparkly": ("brightness", "high"),
    "crisp":    ("brightness", "high"), "airy":   ("brightness", "high"),
    "shiny":    ("brightness", "high"),
    "punchy":   ("punch", "high"),      "hard":   ("punch", "high"),
    "sharp":    ("punch", "high"),      "transient": ("punch", "high"),
    "snappy":   ("punch", "high"),      "tight":  ("punch", "high"),
    "soft":     ("punch", "low"),       "smooth": ("punch", "low"),
    "loud":     ("loudness", "high"),   "powerful": ("loudness", "high"),
    "energetic": ("loudness", "high"),  "huge":   ("loudness", "high"),
    "quiet":    ("loudness", "low"),    "subtle": ("loudness", "low"),
    "gritty":   ("punch", "high"),
}

# Word → the other words that mean the same thing in a sample pack.
# Matching ANY member counts as matching the word the user typed. This is
# what makes "riser" find files named "Uplifter" and "downlifter" find
# files named "Fall".
_SYNONYMS = [
    {"reverse", "rev", "reversed", "backwards", "backward"},
    {"riser", "rise", "uplifter", "uplift", "build", "buildup"},
    {"downlifter", "downlift", "downer", "fall", "falling"},
    {"cymbal", "crash", "ride", "china", "splash"},
    {"impact", "boom", "slam", "hit", "cinematic"},
    {"sweep", "swoosh", "whoosh", "noise", "wind"},
    {"vocal", "vox", "acapella", "acapela", "adlib", "chant", "phrase",
     "voice"},
    {"chop", "chops", "stutter", "glitch"},
    {"sub", "808", "low", "subbass"},
    {"bass", "reese", "growl", "wobble", "wub", "donk", "yoi"},
    {"pluck", "stab", "pizz"},
    {"atmosphere", "atmos", "ambience", "ambient", "texture", "drone",
     "soundscape", "background"},
    {"perc", "percussion", "conga", "bongo", "tamb", "tambourine",
     "shaker", "rim", "tom", "cowbell"},
    {"hat", "hihat", "hh"},
    {"clap", "snap"},
    {"snare", "rimshot"},
    {"kick", "bd", "bassdrum"},
    {"fill", "roll", "turnaround"},
    {"vinyl", "crackle", "tape", "dust"},
    {"foley", "found", "field"},
    {"lead", "melody", "riff", "topline"},
    {"chord", "chords", "harmony", "keys"},
    {"pad", "pads", "swell", "wash"},
]

_CATEGORY_WORDS = {name for name, _ in CATEGORY_PATTERNS} | {
    "hihat", "808", "sub", "vox", "riser", "atmosphere", "drone", "stab"}

_CATEGORY_ALIAS = {"hihat": "hat", "808": "kick", "sub": "bass",
                   "vox": "vocal", "riser": "fx", "atmosphere": "texture",
                   "drone": "texture", "stab": "chord"}

_STOPWORDS = {"a", "an", "the", "of", "in", "on", "for", "near", "me",
              "and", "with", "some", "sample", "samples", "sound",
              "sounds", "minor", "major", "min", "maj", "key", "that",
              "this", "like", "find", "something", "any", "bpm"}

# A key mention needs more than a bare letter (else "dark" reads as D):
# an accidental ("Ab", "f#") or an explicit mode ("F minor", "Fm", "g maj").
_KEY_RE = re.compile(
    r"\b([A-Ga-g])\s?(#|b|sharp|flat)?\s*(minor|major|min|maj|m)?\b", re.ASCII)

_FLAT_TO_SHARP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
                  "Cb": "B", "Fb": "E"}


def parse_key(text):
    """Pull 'F minor' / 'f# maj' / 'Ab' out of free text. Returns
    'F minor'-style string or None."""
    if not text:
        return None
    for m in _KEY_RE.finditer(text.strip()):
        acc, mode_raw = m.group(2), (m.group(3) or "").lower()
        if not acc and not mode_raw:
            continue  # a bare letter isn't a key mention
        note = m.group(1).upper()
        if acc in ("#", "sharp"):
            note += "#"
        elif acc in ("b", "flat"):
            note = _FLAT_TO_SHARP.get(note + "b", note)
        if note not in NOTE_NAMES:
            continue
        mode = "minor" if mode_raw in ("minor", "min", "m") else "major"
        return f"{note} {mode}"
    return None


def neighboring_keys(key):
    """Keys that blend well with `key` → *the relative major/minor shares
    every note; ±1 semitone is one small pitch-shift away.* Used for
    "near F minor" searches."""
    note, mode = key.split()
    i = NOTE_NAMES.index(note)
    other = "major" if mode == "minor" else "minor"
    out = [key, f"{note} {other}"]                        # parallel key (same tonic)
    if mode == "minor":
        out.append(f"{NOTE_NAMES[(i + 3) % 12]} major")   # relative major
    else:
        out.append(f"{NOTE_NAMES[(i - 3) % 12]} minor")   # relative minor
    out.append(f"{NOTE_NAMES[(i + 1) % 12]} {mode}")
    out.append(f"{NOTE_NAMES[(i - 1) % 12]} {mode}")
    return out


def _medians(conn):
    meds = {}
    for col in ("brightness", "punch", "loudness"):
        vals = [r[0] for r in conn.execute(
            f"SELECT {col} FROM samples WHERE missing=0 AND {col} IS NOT NULL")]
        vals.sort()
        meds[col] = vals[len(vals) // 2] if vals else None
    return meds


# ---------------------------------------------------------------------------
# Text matching — pure functions, unit-testable without a database
# ---------------------------------------------------------------------------

def _stem(word):
    """Crude plural stripper so 'cymbals' matches 'cymbal'."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("es") and not word.endswith("ses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def expand_term(word):
    """A query word plus every synonym and stem that should also count."""
    base = _stem(word)
    alts = {word, base}
    for group in _SYNONYMS:
        if word in group or base in group:
            alts |= group
    return {a for a in alts if len(a) >= 2}


def split_path(path):
    """(filename without extension, immediate folder, full path) lowercased."""
    low = path.lower().replace("\\", "/")
    parts = [p for p in low.split("/") if p]
    fname = parts[-1] if parts else low
    fname = re.sub(r"\.[a-z0-9]{2,4}$", "", fname)
    folder = parts[-2] if len(parts) >= 2 else ""
    return fname, folder, low


# Where a word matched, and what that is worth. A hit in the file's own
# name is the strongest signal; a hit anywhere in a long path is the
# weakest (every file under "Samples/Processed/Reverse/" would otherwise
# look like a match for "processed").
_W_FILENAME_WORD = 4.5   # whole word in the filename
_W_FILENAME_PART = 3.0   # inside a longer word in the filename
_W_FOLDER = 1.5          # the immediate containing folder
_W_PATH = 0.75           # somewhere else in the path


def score_terms(terms, path):
    """Score one file path against the expanded query terms.

    `terms` is a list of sets (one set of alternates per word the user
    typed). Returns (score, matched_words) where matched_words names the
    alternate that actually hit, so results can explain themselves.
    """
    fname, folder, low = split_path(path)
    score = 0.0
    matched = []
    for alts in terms:
        best, best_alt = 0.0, None
        for alt in alts:
            if re.search(r"(?<![a-z0-9])" + re.escape(alt) + r"(?![a-z0-9])",
                         fname):
                w = _W_FILENAME_WORD
            elif alt in fname:
                w = _W_FILENAME_PART
            elif alt in folder:
                w = _W_FOLDER
            elif alt in low:
                w = _W_PATH
            else:
                continue
            if w > best:
                best, best_alt = w, alt
        if best:
            score += best
            matched.append(best_alt)
    if terms:
        # Matching 4 of 4 words should beat matching 1 word very strongly.
        score += 3.0 * (len(matched) / float(len(terms)))
    return score, matched


def parse_query(description, category=None):
    """Split free text into feature preferences, a category hint, a bpm
    hint, and the leftover words to match against file names."""
    words = re.findall(r"[a-z0-9#]+", (description or "").lower())
    feature_prefs, text_words = [], []
    cat_hint, bpm_hint = None, None
    for w in words:
        if w in _FEATURE_WORDS:
            feature_prefs.append(_FEATURE_WORDS[w])
            continue
        if w.isdigit() and 60 <= int(w) <= 200:
            bpm_hint = float(w)
            continue
        if w in ("oneshot", "one", "shot"):
            feature_prefs.append(("duration", "low"))
            continue
        if w in ("loop", "loops", "groove"):
            feature_prefs.append(("duration", "high"))
        if w in _CATEGORY_WORDS and cat_hint is None:
            cat_hint = _CATEGORY_ALIAS.get(w, w)
            # NOT `continue` — the word still matters for filename matching.
        if w not in _STOPWORDS:
            text_words.append(w)
    return {
        "feature_prefs": feature_prefs,
        "text_words": text_words,
        "category_hint": category or cat_hint,
        "category_is_filter": category is not None,
        "bpm_hint": bpm_hint,
    }


def _bpm_score(row_bpm, target):
    """Reward a tempo match, and half/double time (a 62 BPM loop sits
    perfectly in a 124 BPM track)."""
    if row_bpm is None or not target:
        return 0.0
    best = 0.0
    for mult in (1.0, 0.5, 2.0):
        diff = abs(row_bpm - target * mult)
        if diff <= 1.0:
            best = max(best, 2.0 if mult == 1.0 else 1.5)
        elif diff <= 4.0:
            best = max(best, 1.0 if mult == 1.0 else 0.6)
    return best


def find_sounds(description="", key=None, bpm_range=None, category=None,
                limit=10, db_path=None, fuzzy_key=True, bpm=None,
                exclude=None, strict=True):
    """The star tool. Returns a list of sample dicts, best matches first.

    strict=True (default) drops files that match none of the words typed,
    instead of padding the list with arbitrary rows.
    """
    conn = dbmod.connect(db_path)
    meds = _medians(conn)

    q = parse_query(description, category)
    if key is None:
        key = parse_key(description)
    target_bpm = bpm or q["bpm_hint"]
    terms = [expand_term(w) for w in q["text_words"]]
    excl = [e.lower() for e in (exclude or [])]

    where, params = ["missing = 0"], []
    if q["category_is_filter"]:
        where.append("category = ?")
        params.append(q["category_hint"])
    if key:
        keys = neighboring_keys(key) if fuzzy_key else [key]
        where.append("key IN (%s)" % ",".join("?" * len(keys)))
        params.extend(keys)
    if bpm_range:
        where.append("bpm BETWEEN ? AND ?")
        params.extend([bpm_range[0], bpm_range[1]])

    rows = conn.execute(
        "SELECT * FROM samples WHERE " + " AND ".join(where),
        params).fetchall()

    scored, text_hits = [], 0
    for r in rows:
        low_path = r["path"].lower()
        if any(e in low_path for e in excl):
            continue
        score, matched = score_terms(terms, r["path"])
        if matched:
            text_hits += 1
        if key:
            score += 2.0 if r["key"] == key else 0.25
        if q["category_hint"] and not q["category_is_filter"]:
            if r["category"] == q["category_hint"]:
                score += 2.5
        score += _bpm_score(r["bpm"], target_bpm)
        for col, direction in q["feature_prefs"]:
            val = r[col]
            if val is None:
                continue
            if col == "duration":
                is_short = val <= ONESHOT_MAX_SECONDS
                score += 1.5 if (is_short == (direction == "low")) else -1.5
            else:
                med = meds.get(col)
                if med is None:
                    continue
                above = val > med
                score += 1.0 if (above == (direction == "high")) else -1.0
        scored.append((score, matched, r))

    conn.close()

    if terms and strict and text_hits:
        scored = [t for t in scored if t[1]]

    scored.sort(key=lambda t: (-t[0], t[2]["path"]))
    out = []
    for score, matched, r in scored[:limit]:
        d = dict(r)
        d.pop("embedding", None)
        d.pop("hash", None)
        d.pop("mtime", None)
        d.pop("size", None)
        d.pop("analyzed_at", None)
        d["match_score"] = round(score, 2)
        d["matched_terms"] = matched
        out.append(d)
    return out


def find_sounds_report(description="", **kw):
    """find_sounds plus an honest header: what the query was understood
    to mean, and a warning when nothing actually matched the words."""
    q = parse_query(description, kw.get("category"))
    results = find_sounds(description, **kw)
    understood = {
        "words_matched_against_filenames": q["text_words"],
        "feature_preferences": [f"{c}:{d}" for c, d in q["feature_prefs"]],
        "category_hint": q["category_hint"],
        "key": kw.get("key") or parse_key(description),
        "bpm_hint": kw.get("bpm") or q["bpm_hint"],
    }
    report = {"query_understood": understood, "results": results}
    if q["text_words"] and not any(r["matched_terms"] for r in results):
        report["warning"] = (
            "No file name in the library contains any of "
            f"{q['text_words']}. These results are ranked on features and "
            "category only — treat them as guesses. Try vibe_search for "
            "meaning-based search, or different words.")
    if not results:
        report["warning"] = (
            "Nothing matched. Loosen the filters: drop the key, widen the "
            "bpm range, or use fewer words.")
    return report


def similar_to(path, limit=10, db_path=None):
    """'More like this one' — nearest neighbours in feature space, using
    z-scores → *each feature rescaled by how much it naturally varies, so
    loudness doesn't drown out key or duration.*"""
    conn = dbmod.connect(db_path)
    target = conn.execute(
        "SELECT * FROM samples WHERE path = ? OR filename = ?",
        (path, path)).fetchone()
    if target is None or target["analyzed_at"] is None:
        conn.close()
        raise ValueError(f"'{path}' isn't in the analyzed library "
                         "(scan + analyze it first)")

    cols = ("brightness", "punch", "loudness", "duration")
    rows = conn.execute(
        "SELECT * FROM samples WHERE missing = 0 AND analyzed_at IS NOT NULL"
    ).fetchall()
    stats = {}
    for c in cols:
        vals = [r[c] for r in rows if r[c] is not None]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
        stats[c] = (mean, math.sqrt(var) or 1.0)

    def vec(r):
        out = []
        for c in cols:
            v = r[c]
            if v is None:
                out.append(0.0)
            else:
                mean, sd = stats[c]
                raw = math.log1p(v) if c == "duration" else v
                mean_ = math.log1p(mean) if c == "duration" else mean
                out.append((raw - mean_) / sd)
        return out

    tv = vec(target)
    scored = []
    for r in rows:
        if r["id"] == target["id"]:
            continue
        dist = math.dist(tv, vec(r))
        if r["key"] and target["key"] and r["key"] != target["key"]:
            dist += 0.5
        if r["category"] and target["category"] and r["category"] != target["category"]:
            dist += 1.0
        scored.append((dist, r))
    scored.sort(key=lambda t: (t[0], t[1]["path"]))

    out = []
    for dist, r in scored[:limit]:
        d = dict(r)
        d.pop("embedding", None)
        d["distance"] = round(dist, 3)
        out.append(d)
    conn.close()
    return out


def library_stats(db_path=None):
    """Coverage report: what you have lots of, what you lack."""
    conn = dbmod.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM samples WHERE missing=0").fetchone()[0]
    analyzed = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE missing=0 AND analyzed_at IS NOT NULL"
    ).fetchone()[0]
    by_cat = {r[0] or "(uncategorized)": r[1] for r in conn.execute(
        "SELECT category, COUNT(*) FROM samples WHERE missing=0 "
        "GROUP BY category ORDER BY COUNT(*) DESC")}
    by_key = {r[0]: r[1] for r in conn.execute(
        "SELECT key, COUNT(*) FROM samples WHERE missing=0 AND key IS NOT NULL "
        "GROUP BY key ORDER BY COUNT(*) DESC")}
    loops = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE missing=0 AND duration > ?",
        (ONESHOT_MAX_SECONDS,)).fetchone()[0]
    conn.close()
    return {
        "total_files": total,
        "analyzed": analyzed,
        "awaiting_analysis": total - analyzed,
        "loops": loops,
        "one_shots": max(analyzed - loops, 0),
        "by_category": by_cat,
        "by_key": by_key,
    }
