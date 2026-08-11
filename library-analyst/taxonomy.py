"""taxonomy.py — guess what a sample IS from its folder and file name.

Folder-name heuristics first, per the plan: sample packs are usually
organized (Kicks/, 808s/, Vocal Chops/...), so the path is a strong hint.
The category feeds search ("find me a kick...") and library_stats.
"""

import re

# Order matters: first match wins. Checked against the FULL lowercased
# path, so folder names count as much as file names.
CATEGORY_PATTERNS = [
    ("kick",    r"kick|bd[_ -]|bassdrum|808s?(?![a-z])"),
    ("snare",   r"snare|sn[_ -]|rim(shot)?"),
    ("clap",    r"clap"),
    ("hat",     r"\bhat|hihat|hi[_ -]?hat|\bhh[_ -]|cymbal|ride|crash"),
    ("perc",    r"perc|conga|bongo|shaker|tamb|cowbell|timbale"),
    ("tom",     r"\btom(s)?\b"),
    ("bass",    r"\bbass|\bsub\b|reese|wobble"),
    ("vocal",   r"vocal|vox|acapella|adlib|phrase|chant|choir"),
    ("fx",      r"\bfx\b|riser|sweep|impact|downlifter|uplifter|whoosh|foley|sfx"),
    ("texture", r"texture|ambien|atmo|drone|noise|vinyl|field"),
    ("pad",     r"\bpad(s)?\b"),
    ("pluck",   r"pluck"),
    ("lead",    r"\blead(s)?\b"),
    ("chord",   r"chord|stab"),
    ("keys",    r"piano|keys|rhodes|organ|epiano"),
    ("guitar",  r"guitar|gtr"),
    ("brass",   r"brass|horn|trumpet|sax"),
    ("strings", r"string|violin|cello"),
    ("loop",    r"loop|groove|break(beat)?|drum[_ -]?loop"),
]


def categorize(path):
    """Return a category slug for a file path, or None if nothing matches."""
    low = path.lower().replace("\\", "/")
    for name, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, low):
            return name
    return None
