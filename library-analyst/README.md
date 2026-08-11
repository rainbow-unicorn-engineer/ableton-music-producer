# library-analyst — Phase 2 (built)

The piece nobody ships: an MCP server that knows every sound you own.

## The pieces

| File | Job |
|------|-----|
| `scanner.py` | walks your sample folders; stores path, size, hash → *a fingerprint of the file's contents, so re-scans skip unchanged files* — in SQLite (`db/`, gitignored) |
| `analysis.py` | per-file features: BPM, key (e.g. "F minor"), duration, brightness, punch, loudness. Uses **librosa** when installed; falls back to a built-in numpy engine (WAV-only) so it works everywhere |
| `search.py` | turns "dark punchy bass one-shot near F minor" into a scored database query |
| `mcp_server.py` | exposes it all to Claude: `find_sounds` (the star), `similar_to`, `analyze_file`, `library_stats` |
| `taxonomy.py` | folder-name heuristics: `Kicks/` → kick, `Vocal Chops/` → vocal, ... |

## Setup (once)

```bash
pip install -r library-analyst/requirements.txt
```

Then register the server in Claude Desktop's config alongside XLNT-Ableton
(see `docs/claude_desktop_config.sample.json` for the ready-made block).

## The build order (from the plan)

```bash
cd library-analyst

# 1. Scanner on ONE folder — verify database rows appear
python scanner.py --root "D:/Samples/SomeSmallFolder"
python scanner.py --stats

# 2. Analysis on those files — sanity-check BPM/key against files you know
python analysis.py
python analysis.py --file "D:/Samples/SomeSmallFolder/some_bass_F.wav"

# 3. Full library scan (run overnight; 80K files takes hours)
python scanner.py --root "D:/Samples"
python analysis.py

# 4. Restart Claude Desktop → the XLNT-Library tools appear
# 5. CLAP embeddings last (the cherry, not the cake) — see requirements.txt
```

Re-scans are incremental: unchanged files are skipped, changed files are
re-analyzed, deleted files drop out of search results.

## The magic test

> "Find me a dark textured bass one-shot near F minor and load it onto a
> new audio track."

The analyst finds it (`find_sounds`), the Ableton server loads it — two
servers cooperating.

## Tests

```bash
pytest library-analyst/tests/
```

Builds a synthetic library (dark 50 Hz kick, bright noise hat, 140 BPM
F bass loop, F-minor pad) and verifies scan → analyze → search → similarity
→ stats end to end. Runs with or without librosa installed.
