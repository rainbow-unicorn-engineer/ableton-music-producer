"""arrangement_doctor.py — read an arrangement like a producer, not a meter.

The ears (`analyze_bounce`, `compare_mix`) measure technical hygiene:
loudness, true peak, band balance. They are blind to the thing that
actually makes a track sound amateur — **not enough happening, and
nothing changing.**

This module reads the raw arrangement data from the Remote Script and
answers the questions a producer would ask:

* How many elements are actually sounding in each 8-bar block?
* Which *roles* are missing versus what a full drop contains?
* Is this block identical to the last one? (the boredom detector)
* Which roles does the song never use at all?

→ *A "role" is what a sound does in the mix — kick, sub, bass, clap, hat,
cymbal, perc, lead, chord, vocal, riser, impact, fx. Pros build sections
by role, not by track: "this drop needs a clap and an open hat" is a
concrete instruction; "add more energy" is not.*

Pure functions, no MCP or Live dependencies — unit-testable anywhere.
"""

import re

# ---------------------------------------------------------------------------
# Role classification
# ---------------------------------------------------------------------------

# Order matters: first match wins. Matched against track name first, then
# the clip name, both lowercased.
ROLE_PATTERNS = [
    ("reference",  r"^ref\b|reference|\bref$"),
    ("trigger",    r"trigger"),
    ("kick",       r"kick|bassdrum|\bbd\b"),
    ("clap/snare", r"snare|clap|\brim"),
    ("hat",        r"\bhat|hi-?hat|\bhh\b|closed|\bopen\b"),
    ("cymbal",     r"ride|crash|cymbal"),
    ("perc",       r"perc|shaker|tamb|conga|bongo|top ?loop|\btom\b|cowbell"),
    ("sub",        r"\bsub\b|808 ?low"),
    ("bass",       r"bass|reese|growl|wobb|\b808\b"),
    ("vocal",      r"vocal|\bvox\b|acapella|adlib|chop|migos|verse|hook"),
    ("chord",      r"chord|piano|keys|rhodes|\bpad\b|brass|string|captain|organ"),
    ("lead",       r"lead|\bld\b|synth|serum|pluck|\barp\b|stab|melod|idea"),
    ("riser",      r"\brise|uplift|riser|\bup\b|build"),
    ("downlifter", r"\bdown\b|downlift|fall"),
    ("impact",     r"impact|laser|boom|\bhit\b"),
    ("fx",         r"\bfx\b|noise|sweep|texture|atmos|foley|fill|whoosh|vinyl"),
]

# Roles that exist for routing/reference, not as audible song elements.
NON_ELEMENT_ROLES = {"reference", "trigger"}

# What a full commercial drop contains. Missing entries here are the
# actionable to-do list for a thin-sounding section.
DROP_STANDARD = [
    "kick", "sub", "bass", "clap/snare", "hat", "cymbal",
    "perc", "lead", "vocal", "fx",
]

# What a break/breakdown usually contains.
BREAK_STANDARD = ["chord", "vocal", "fx", "perc"]

# What a build contains.
BUILD_STANDARD = ["riser", "clap/snare", "impact", "fx"]

STANDARDS = {
    "drop": DROP_STANDARD,
    "break": BREAK_STANDARD,
    "build": BUILD_STANDARD,
}


def classify_roles(track_name, clip_name=""):
    """Return every role a track/clip plays.

    Multi-role on purpose: a track called "KICK & SNARE" genuinely carries
    two roles, and reporting only the first would hide a missing snare.
    Track name wins; the clip name is consulted only if the track name says
    nothing (generic tracks like "17-Audio").
    """
    for source in (track_name or "", clip_name or ""):
        low = source.lower()
        found = [role for role, pattern in ROLE_PATTERNS
                 if re.search(pattern, low)]
        if found:
            return found
    return ["unclassified"]


def classify_role(track_name, clip_name=""):
    """Primary role only (first match) — kept for simple callers."""
    return classify_roles(track_name, clip_name)[0]


# ---------------------------------------------------------------------------
# Block analysis
# ---------------------------------------------------------------------------

def _overlaps(clip_start, clip_end, block_start, block_end):
    """True if a clip sounds at any point inside the block."""
    return clip_start < block_end and clip_end > block_start


def analyze(tracks, beats_per_bar=4.0, block_bars=8, start_bar=1,
            end_bar=None, standard="drop", boundaries=None):
    """Analyze an arrangement into per-block reports.

    Parameters
    ----------
    tracks : list of dicts as returned by the Remote Script's
        get_arrangement_info — each with 'index', 'name', and
        'arrangement_clips' (each clip: start_time, end_time, muted, name).
    beats_per_bar : from the time signature.
    block_bars : block size in bars (8 is the musical unit that matters).
    start_bar, end_bar : 1-based bar window. end_bar None = last clip.
    standard : which role checklist to compare against ('drop', 'break',
        'build') — or None to skip the missing-roles report.

    Returns a dict with 'blocks', 'summary' and 'roles_never_used'.
    """
    # Flatten every audible clip into (role, track_name, start, end).
    # A track muted at the mixer silences all its clips — honoured when the
    # Remote Script reports it (older scripts omit the key; assume audible).
    events = []
    for t in tracks:
        if t.get("muted"):
            continue
        tname = t.get("name", "")
        for clip in t.get("arrangement_clips", []):
            if clip.get("muted"):
                continue
            roles = classify_roles(tname, clip.get("name", ""))
            events.append({
                "roles": roles,
                "track": tname,
                "track_index": t.get("index", -1),
                "start": clip.get("start_time", 0.0),
                "end": clip.get("end_time", 0.0),
            })

    # A track counts as a song element unless every role it plays is
    # infrastructure (the reference track, sidechain triggers).
    song_elements = [e for e in events
                     if any(r not in NON_ELEMENT_ROLES for r in e["roles"])]
    if not song_elements:
        return {"blocks": [], "summary": {"error": "no audible clips found"},
                "roles_never_used": []}

    last_beat = max(e["end"] for e in song_elements)
    first_beat = (start_bar - 1) * beats_per_bar
    # end_bar is EXCLUSIVE — "drop 30-38" ends at the downbeat of bar 38,
    # matching how every other tool and doc in this project talks about bars.
    if end_bar:
        last_beat = (end_bar - 1) * beats_per_bar
    block_beats = block_bars * beats_per_bar

    # Block edges: fixed 8-bar grid, or aligned to supplied bar boundaries
    # (pass the project's cue points so blocks match real sections).
    if boundaries:
        edges = sorted({(b - 1) * beats_per_bar for b in boundaries
                        if first_beat <= (b - 1) * beats_per_bar <= last_beat}
                       | {first_beat, last_beat})
    else:
        edges = None

    blocks = []
    prev_signature = None
    beat = first_beat
    edge_i = 0
    while beat < last_beat:
        if edges:
            edge_i += 1
            b_end = edges[edge_i] if edge_i < len(edges) else last_beat
        else:
            b_end = beat + block_beats
        sounding = [e for e in song_elements
                    if _overlaps(e["start"], e["end"], beat, b_end)]
        # ELEMENTS = distinct tracks making sound. 32 vocal-chop clips on
        # one track are one element (the chop layer), not 32.
        track_ids = {e["track_index"] for e in sounding}
        roles_present = sorted({r for e in sounding for r in e["roles"]
                                if r not in NON_ELEMENT_ROLES})
        signature = tuple(sorted(track_ids))

        checklist = STANDARDS.get(standard) if standard else None
        missing = ([r for r in checklist if r not in roles_present]
                   if checklist else [])

        blocks.append({
            "start_bar": int(beat / beats_per_bar) + 1,
            "end_bar": int(b_end / beats_per_bar) + 1,
            "element_count": len(track_ids),
            "roles_present": roles_present,
            "missing_roles": missing,
            "elements": sorted({e["track"] for e in sounding}),
            "identical_to_previous": signature == prev_signature and bool(signature),
            "density": ("empty" if not sounding else
                        "sparse" if len(sounding) <= 6 else
                        "medium" if len(sounding) <= 12 else "full"),
        })
        prev_signature = signature
        beat = b_end

    used_roles = {r for e in song_elements for r in e["roles"]}
    never_used = [r for r, _ in ROLE_PATTERNS
                  if r not in used_roles and r not in NON_ELEMENT_ROLES]

    non_empty = [b for b in blocks if b["element_count"] > 0]
    repeats = sum(1 for b in blocks if b["identical_to_previous"])
    summary = {
        "blocks_analyzed": len(blocks),
        "avg_elements": (round(sum(b["element_count"] for b in non_empty)
                               / len(non_empty), 1) if non_empty else 0),
        "max_elements": max((b["element_count"] for b in blocks), default=0),
        "min_elements_nonempty": min((b["element_count"] for b in non_empty),
                                     default=0),
        "identical_blocks": repeats,
        "repetition_pct": (round(100.0 * repeats / len(blocks))
                           if blocks else 0),
    }
    return {"blocks": blocks, "summary": summary,
            "roles_never_used": never_used}


# ---------------------------------------------------------------------------
# Human-readable report
# ---------------------------------------------------------------------------

def format_report(result, standard="drop"):
    """Turn analyze() output into something a producer can act on."""
    blocks = result.get("blocks", [])
    if not blocks:
        return "No audible clips found in that range."
    s = result["summary"]
    lines = ["=== Arrangement Doctor ===",
             f"Average {s['avg_elements']} elements per 8-bar block "
             f"(commercial drop target: 18-25).",
             f"Thinnest non-empty block: {s['min_elements_nonempty']} elements | "
             f"Fullest: {s['max_elements']}.",
             f"Repetition: {s['identical_blocks']}/{s['blocks_analyzed']} blocks "
             f"are identical to the one before ({s['repetition_pct']}%).",
             ""]
    for b in blocks:
        flag = "  <-- IDENTICAL to previous block" if b["identical_to_previous"] else ""
        lines.append(f"bars {b['start_bar']}-{b['end_bar']}: "
                     f"{b['element_count']} elements ({b['density']}){flag}")
        if b["roles_present"]:
            lines.append(f"    has:     {', '.join(b['roles_present'])}")
        if b["missing_roles"]:
            lines.append(f"    MISSING: {', '.join(b['missing_roles'])}")
    if result.get("roles_never_used"):
        lines.append("")
        lines.append("Roles never used anywhere in this song: "
                     + ", ".join(result["roles_never_used"]))
    return "\n".join(lines)
