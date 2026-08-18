#!/usr/bin/env python3
"""mcp_server.py — the Library Analyst as an MCP server.

The piece nobody ships: an MCP server that knows every sound you own.
Registers in Claude Desktop alongside XLNT-Ableton (see
docs/claude_desktop_config.sample.json), and the two cooperate:

    "Find me a dark textured bass one-shot near F minor and load it
     onto a new audio track."
      → the analyst finds it (this server)
      → the Ableton server loads it (XLNT-Ableton)

Tools: find_sounds (the star), similar_to, analyze_file, library_stats,
analyze_bounce — and the reverse-engineering pipeline: make_reference_card,
list_reference_cards, compare_mix, analyze_structure, separate_stems,
extract_midi.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

import analysis as analysis_mod
import search as search_mod

mcp = FastMCP("XLNT-Library")


@mcp.tool()
def find_sounds(description: str = "", query: str = "", key: str = None,
                bpm: float = None, bpm_min: float = None,
                bpm_max: float = None, category: str = None,
                exclude: str = "", limit: int = 10,
                strict: bool = True) -> str:
    """Search the sample library by description. THE tool for "find me a…".

    Matches the words you type against every file name and folder in the
    library (with synonyms — "riser" also finds files named "Uplifter",
    "reverse" also finds "R"/"backwards"), and against the stored audio
    features.

    Parameters:
    - description (or query — same thing): free text, e.g.
      "reverse cymbal swell", "dark punchy bass one-shot",
      "vocal adlib skrrt". Understands darkness/brightness, punch,
      loudness, one-shot vs loop, category words (kick, bass, vocal…),
      key names ("near F minor") and a bare tempo number ("124").
    - key: e.g. "D# minor" — HARD filter, but includes musically
      neighbouring keys (relative major/minor, ±1 semitone), exact first.
    - bpm: target tempo. Half and double time score too — a 62 BPM loop
      sits perfectly in a 124 BPM track.
    - bpm_min / bpm_max: hard tempo range instead.
    - category: kick/snare/clap/hat/perc/bass/vocal/fx/texture/pad/…
      Passing it here is a hard filter; a category word inside the
      description is only a strong hint.
    - exclude: comma-separated text to reject on (e.g. "drum kits,demo").
    - strict: drop files matching none of your words (default true).
      Set false to see feature-only guesses.

    Returns JSON with `query_understood` (what the words were taken to
    mean), `results` (each with `matched_terms` saying WHY it matched),
    and a `warning` when nothing really matched — a search that finds
    nothing says so instead of returning arbitrary rows.
    """
    text = description or query
    bpm_range = ((bpm_min, bpm_max)
                 if bpm_min is not None and bpm_max is not None else None)
    excl = [e.strip() for e in exclude.split(",") if e.strip()]
    report = search_mod.find_sounds_report(
        description=text, key=key, bpm=bpm, bpm_range=bpm_range,
        category=category, exclude=excl, limit=limit, strict=strict)
    return json.dumps(report, indent=2)


@mcp.tool()
def similar_to(path: str, limit: int = 10) -> str:
    """"More like this one": nearest neighbours of a library file in
    feature space (brightness, punch, loudness, duration; same key and
    category rank closer). `path` may be a full path or just a filename
    already in the library. Returns JSON list with a `distance` field
    (smaller = more similar)."""
    return json.dumps(search_mod.similar_to(path, limit=limit), indent=2)


@mcp.tool()
def analyze_file(path: str) -> str:
    """Full feature readout of any single audio file on disk (doesn't
    need to be in the library): duration, bpm, key, brightness, punch,
    loudness. Returns JSON."""
    return json.dumps(analysis_mod.analyze_file(path), indent=2)


@mcp.tool()
def analyze_bounce(path: str, out_dir: str = None) -> str:
    """Phase 4 'ears': full mix feedback on a bounced audio file.
    Measures integrated LUFS, true peak (dBTP), loudness range, and
    per-band energy balance (sub/bass/low-mid/mid/high-mid/high), renders
    a spectrogram PNG next to the file (or into out_dir), and returns it
    all as JSON including a human-readable summary. Use on bounces from
    the AudioCapture.amxd recorder or File > Export."""
    ears_dir = Path(__file__).resolve().parents[1] / "ears"
    sys.path.insert(0, str(ears_dir))
    import analyze_bounce as ab
    return json.dumps(ab.analyze(path, out_dir), indent=2)


@mcp.tool()
def vibe_search(description: str = None, audio_path: str = None,
                category: str = None, limit: int = 10) -> str:
    """TRUE vibe search: rank the whole library by CLAP meaning-space
    similarity to a sentence ("haunted carousel music box", "abandoned
    mall energy") or to a piece of audio (audio_path = any file on disk —
    'find me sounds like THIS drop'). Works beyond filenames and stored
    features — it's judging by how things actually sound. Optional
    category filter (bass/kick/vocal/...). Needs the one-time embedding
    scan; if it says so, fall back to find_sounds. First query in a
    session takes ~10-30 s (model loads), then it's fast."""
    import vibe as vibe_mod
    return json.dumps(vibe_mod.vibe_search(description=description,
                                           audio_path=audio_path,
                                           category=category, limit=limit),
                      indent=2)


@mcp.tool()
def similar_sound(path: str, limit: int = 10) -> str:
    """'More like this one', judged by EAR (CLAP embeddings) instead of
    by stored feature numbers — finds sounds that share the vibe, not
    just the brightness/punch stats. `path` can be a library file
    (instant, uses its stored vector) or any audio file on disk. Use
    similar_to for the fast feature-based version."""
    import vibe as vibe_mod
    return json.dumps(vibe_mod.similar_sound(path, limit=limit), indent=2)


@mcp.tool()
def embedding_status() -> str:
    """How much of the library has CLAP embeddings (vibe search
    coverage): analyzed vs embedded vs remaining. If remaining is large,
    the overnight scan hasn't run (or hasn't finished)."""
    import embeddings as emb_mod
    return json.dumps(emb_mod.embedding_coverage(), indent=2)


def _ears_import(module_name):
    """Import a module from the ears package (monorepo sibling)."""
    ears_dir = Path(__file__).resolve().parents[1] / "ears"
    if str(ears_dir) not in sys.path:
        sys.path.insert(0, str(ears_dir))
    import importlib
    return importlib.import_module(module_name)


@mcp.tool()
def make_reference_card(path: str, name: str = None, bpm: float = None) -> str:
    """Analyze a reference track ONCE into a permanent 'reference card':
    loudness DNA (LUFS, true peak, dynamics), band balance, key, tempo,
    arrangement skeleton (intro 16 -> build 16 -> drop 32...), spectrogram
    and structure PNGs. Cards live in references/ at the repo root and are
    what compare_mix diffs bounces against. Pass bpm if the filename
    doesn't contain it and detection might stumble (e.g. halftime)."""
    refs = _ears_import("references")
    card = refs.make_card(path, name=name, bpm=bpm)
    return json.dumps({k: v for k, v in card.items()
                       if k != "bar_energy_db"}, indent=2)


@mcp.tool()
def list_reference_cards() -> str:
    """All saved reference cards: name, key, BPM, LUFS, true peak, and
    arrangement skeleton. Use before compare_mix to see what's on file."""
    refs = _ears_import("references")
    return json.dumps(refs.list_cards(), indent=2)


@mcp.tool()
def compare_mix(bounce: str, reference: str, png: bool = False) -> str:
    """The reverse-engineering workhorse: diff a bounce against a
    reference — loudness delta (LU), true peak, dynamics, and band-by-band
    balance gaps ('their sub sits 6 dB above their low-mids; yours
    doesn't'). `reference` is a saved card name (see list_reference_cards)
    or any audio file path (analyzed on the fly). png=True also renders
    both spectrograms stacked in one image. Returns JSON with a `gaps`
    list — fix the top one first."""
    cm = _ears_import("compare_mix")
    result = cm.compare(bounce, reference, png=png)
    result["summary"] = cm.summarize(result)
    return json.dumps(result, indent=2)


@mcp.tool()
def analyze_structure(path: str, bpm: float = None, png: bool = False) -> str:
    """Extract a track's arrangement math: per-bar energy sliced at its
    tempo, grouped into labeled sections (intro/build/drop/break/outro)
    and a skeleton like 'intro 16 -> build 16 -> drop 32'. Feeds straight
    into skills/ recipe docs. Tempo comes from `bpm`, the filename
    ('ref 140bpm.wav'), or detection — in that order. png=True renders a
    bar-energy chart with shaded sections."""
    st = _ears_import("structure")
    r = st.analyze_structure(path, bpm=bpm, png=png)
    r.pop("bar_energy_db", None)
    return json.dumps(r, indent=2)


@mcp.tool()
def separate_stems(path: str, out_dir: str = None, two_stems: str = None,
                   analyze: bool = True) -> str:
    """Split a finished track into stems (vocals / drums / bass / other)
    with Demucs, then run the ears on each stem: per-stem LUFS, band
    balance, spectrograms, and a stem-balance readout ('drums 2.1 LU under
    the bass'). two_stems='vocals' gives vocals vs. everything-else.
    Heavy: needs `pip install demucs` (~1 GB model on first run) and takes
    minutes per track. analyze=False returns just the stem file paths."""
    st = _ears_import("stems")
    if analyze:
        return json.dumps(st.analyze_stems(path, out_dir=out_dir,
                                           two_stems=two_stems), indent=2)
    return json.dumps(st.separate(path, out_dir=out_dir,
                                  two_stems=two_stems), indent=2)


@mcp.tool()
def extract_midi(path: str, out: str = None, bpm: float = 120.0) -> str:
    """Pull the notes out of audio into a .mid file you can drop onto an
    Ableton MIDI track — a reference's chords or topline as editable MIDI.
    Polyphonic (hears chords) when basic-pitch is installed; otherwise a
    built-in monophonic tracker (one note at a time — fine for basslines
    and toplines). Best on a single stem from separate_stems, not the full
    mix. Returns JSON with the note list and the .mid path."""
    me = _ears_import("midi_extract")
    return json.dumps(me.extract(path, out=out, bpm=bpm), indent=2)


@mcp.tool()
def analyze_clash(path_a: str, path_b: str, label_a: str = "vocal",
                  label_b: str = "instrumental", png: bool = False) -> str:
    """Find where two sounds FIGHT for the same frequencies (masking):
    per-band contested-time percentages, the single worst frequency, and
    concrete fixes ('duck 250-500 Hz in the instrumental when the vocal
    plays'). Feed it a vocal stem vs your beat, your bass vs your kick,
    or a reference's vocal vs its instrumental (via separate_stems) to
    study how THEY made space. Files must share a sample rate."""
    cl = _ears_import("clash")
    return json.dumps(cl.analyze_clash(path_a, path_b, label_a, label_b,
                                       png=png), indent=2)


@mcp.tool()
def mashup_match(acapella: str, beat: str, acapella_key: str = None,
                 beat_key: str = None, acapella_bpm: float = None,
                 beat_bpm: float = None) -> str:
    """Make an acapella and a beat agree: detects both sides' key and BPM
    (or takes overrides), then returns the exact Ableton moves — smallest
    semitone transpose (using relative-key equivalence: A minor fits over
    C major as-is), warp target with half/double-time awareness, and
    warnings when the stretch (>8%) or shift (>4 st) will sound
    unnatural. Also lists which keys need no transpose at all."""
    mu = _ears_import("mashup")
    return json.dumps(mu.match(acapella, beat, acapella_key=acapella_key,
                               beat_key=beat_key, acapella_bpm=acapella_bpm,
                               beat_bpm=beat_bpm), indent=2)


@mcp.tool()
def library_stats() -> str:
    """Coverage report of the whole library: totals, analyzed count,
    loops vs one-shots, and breakdowns by category and by key — what you
    have lots of, and what you lack. Returns JSON."""
    return json.dumps(search_mod.library_stats(), indent=2)


@mcp.tool()
def collect_bounce(song: str, section: str = "full pass",
                   analyze: bool = True, reference: str = None) -> str:
    """Grab the AudioCapture recording, file it properly, and (optionally)
    analyze it — no manual Move-Item ever again.

    Moves C:/tmp/ableton_capture.wav into C:/Music Production/Bounces/ as
    '<song> - <section> - v<N>.wav' with the version number auto-detected
    (v1, v2, v3... based on what's already there). Then runs analyze_bounce
    on it, and if `reference` is given (a reference card name), also runs
    compare_mix. Returns JSON with the new path and the analysis.

    Workflow: toggle AudioCapture off after recording, then just call this.
    """
    import re
    import shutil
    capture = Path("C:/tmp/ableton_capture.wav")
    bounces = Path("C:/Music Production/Bounces")
    if not capture.exists():
        return ("No capture found at C:/tmp/ableton_capture.wav — is the "
                "AudioCapture toggle off? (The file is written on toggle-off.)")
    bounces.mkdir(parents=True, exist_ok=True)
    version = 1
    pattern = re.compile(re.escape(song) + r" - " + re.escape(section)
                         + r" - v(\d+)\.wav$", re.IGNORECASE)
    for f in bounces.glob("*.wav"):
        m = pattern.search(f.name)
        if m:
            version = max(version, int(m.group(1)) + 1)
    dest = bounces / ("{0} - {1} - v{2}.wav".format(song, section, version))
    shutil.move(str(capture), str(dest))
    out = {"filed_as": str(dest), "version": version}
    if analyze:
        ab = _ears_import("analyze_bounce")
        out["analysis"] = ab.analyze(str(dest))
    if reference:
        try:
            out["comparison"] = json.loads(compare_mix(str(dest), reference))
        except Exception as exc:
            out["comparison_error"] = str(exc)
    return json.dumps(out, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
