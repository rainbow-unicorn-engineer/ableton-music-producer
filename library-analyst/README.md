# library-analyst — Phase 2 (not started)

The piece nobody ships: an MCP server that knows every sound you own.

Planned layout (from the project plan):

- `scanner.py` — walk the sample directories; store path, filename, size,
  hash → *a fingerprint of the file's contents, so re-scans skip unchanged
  files* — in SQLite (`db/`, gitignored)
- `analysis.py` — per-file features via librosa: BPM, key, duration,
  brightness (spectral centroid), punch (onset strength), loudness (RMS);
  optional CLAP embeddings for true vibe search
- `mcp_server.py` — tools: `find_sounds()`, `similar_to()`,
  `analyze_file()`, `library_stats()`

Build order: scanner on ONE folder → analysis sanity-check → full library
overnight scan → MCP wrapper → CLAP last (it's the cherry, not the cake).
