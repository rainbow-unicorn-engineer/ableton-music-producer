#!/usr/bin/env python3
"""mcp_server.py — the Library Analyst as an MCP server.

The piece nobody ships: an MCP server that knows every sound you own.
Registers in Claude Desktop alongside XLNT-Ableton (see
docs/claude_desktop_config.sample.json), and the two cooperate:

    "Find me a dark textured bass one-shot near F minor and load it
     onto a new audio track."
      → the analyst finds it (this server)
      → the Ableton server loads it (XLNT-Ableton)

Tools: find_sounds (the star), similar_to, analyze_file, library_stats.
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
def find_sounds(description: str = "", key: str = None,
                bpm_min: float = None, bpm_max: float = None,
                category: str = None, limit: int = 10) -> str:
    """Search the sample library by natural description.

    Parameters:
    - description: free text, e.g. "dark punchy bass one-shot". Understands
      darkness/brightness, punch, loudness, one-shot vs loop, category
      words (kick, bass, vocal...), key names ("near F minor"), and
      matches leftover words against file names.
    - key: e.g. "F minor" — matches that key plus musically neighboring
      keys (relative major/minor, ±1 semitone), exact key ranked first.
    - bpm_min / bpm_max: tempo range for loops.
    - category: kick/snare/hat/clap/perc/bass/vocal/fx/texture/pad/...
    - limit: max results.

    Returns JSON list, best match first, each with path, category, key,
    bpm, duration, brightness, punch, loudness, match_score.
    """
    bpm_range = (bpm_min, bpm_max) if bpm_min is not None and bpm_max is not None else None
    results = search_mod.find_sounds(description=description, key=key,
                                     bpm_range=bpm_range, category=category,
                                     limit=limit)
    return json.dumps(results, indent=2)


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
def library_stats() -> str:
    """Coverage report of the whole library: totals, analyzed count,
    loops vs one-shots, and breakdowns by category and by key — what you
    have lots of, and what you lack. Returns JSON."""
    return json.dumps(search_mod.library_stats(), indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
