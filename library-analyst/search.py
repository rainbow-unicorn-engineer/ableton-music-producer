"""search.py — turn words into database queries.

`find_sounds("dark punchy bass one-shot", key="F minor")` works by mapping
descriptive words onto the numeric features analysis.py stored:

* dark / bright        → brightness (spectral centroid) below / above the
                         library's own median — *"dark" is relative to
                         YOUR sounds, not some universal constant*
* punchy / soft        → punch above / below median
* loud / quiet         → loudness above / below median
* one-shot / loop      → duration under / over 2 seconds
* kick, bass, vocal... → category column (see taxonomy.py)
* leftover words       → matched against file names and paths

When CLAP embeddings land (the plan's optional power-up), description
matching upgrades to true vibe search; the word-mapping stays as the
fast path and the fallback.
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
    "bright":   ("brightness", "high"), "sparkly": ("brightness", "high"),
    "crisp":    ("brightness", "high"), "airy":   ("brightness", "high"),
    "punchy":   ("punch", "high"),      "hard":   ("punch", "high"),
    "sharp":    ("punch", "high"),      "transient": ("punch", "high"),
    "soft":     ("punch", "low"),       "smooth": ("punch", "low"),
    "loud":     ("loudness", "high"),   "powerful": ("loudness", "high"),
    "energetic": ("loudness", "high"),
    "quiet":    ("loudness", "low"),    "subtle": ("loudness", "low"),
    "gritty":   ("punch", "high"),
}

_CATEGORY_WORDS = {name for name, _ in CATEGORY_PATTERNS} | {
    "hihat", "808", "sub", "vox", "riser", "atmosphere", "drone", "stab"}

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


def find_sounds(description="", key=None, bpm_range=None, category=None,
                limit=10, db_path=None, fuzzy_key=True):
    """The star tool. Returns a list of sample dicts, best matches first."""
    conn = dbmod.connect(db_path)
    meds = _medians(conn)

    words = re.findall(r"[a-z0-9#]+", (description or "").lower())
    feature_prefs = []      # (column, 'low'|'high')
    text_words = []
    for w in words:
        if w in _FEATURE_WORDS:
            feature_prefs.append(_FEATURE_WORDS[w])
        elif category is None and w in _CATEGORY_WORDS:
            category = {"hihat": "hat", "808": "kick", "sub": "bass",
                        "vox": "vocal", "riser": "fx", "atmosphere": "texture",
                        "drone": "texture", "stab": "chord"}.get(w, w)
        elif w in ("oneshot", "one", "shot", "hit"):
            feature_prefs.append(("duration", "low"))
        elif w in ("loop", "loops", "groove"):
            feature_prefs.append(("duration", "high"))
        elif w not in ("a", "the", "of", "in", "near", "me", "and", "with",
                       "some", "sample", "sound", "minor", "major", "min",
                       "maj", "key"):
            text_words.append(w)

    if key is None:
        key = parse_key(description)

    where, params = ["missing = 0"], []
    if category:
        where.append("category = ?")
        params.append(category)
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

    scored = []
    for r in rows:
        score = 0.0
        if key and r["key"] == key:
            score += 2.0            # exact key beats neighboring key
        for col, direction in feature_prefs:
            val = r[col if col != "duration" else "duration"]
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
        low_path = r["path"].lower()
        for w in text_words:
            if w in low_path:
                score += 1.0
        scored.append((score, r))

    scored.sort(key=lambda t: (-t[0], t[1]["path"]))
    out = []
    for score, r in scored[:limit]:
        d = dict(r)
        d.pop("embedding", None)
        d["match_score"] = round(score, 2)
        out.append(d)
    conn.close()
    return out


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
