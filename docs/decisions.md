# Decisions — why things are the way they are

Newest first. One entry per decision that a future collaborator (human or
agent) might want to reverse.

## 2026-08-11 — Analyst has a librosa-first, numpy-fallback engine

`analysis.py` uses librosa when importable (the plan's choice — best BPM
and chroma estimators) and otherwise falls back to a built-in numpy/scipy
engine (STFT centroid, spectral-flux onsets, autocorrelation tempo,
Krumhansl key matching; WAV-only). Same output format either way. Reason:
the fallback keeps the test suite runnable in any environment, and keeps
the analyst alive if a librosa install ever breaks. The fallback is the
fully-tested path; librosa calls are standard one-liners.

## 2026-08-11 — find_sounds maps words to features, CLAP deferred

"dark" means brightness below the library's own median — relative to YOUR
sounds, not a universal constant. Word→feature mapping lives in
`search.py`; CLAP embeddings (true vibe search) remain the planned
power-up, and the `embedding` column already waits for them. Ship the
cake, add the cherry later — the plan's own build order.

## 2026-08-11 — Two Remote Scripts, enable one at a time

uisato ships a full-featured TCP-only script (~2,150 lines, 46 commands)
and a slim hybrid TCP+UDP script (~410 lines) separately, and both bind
TCP 9877. We vendored both rather than merging on day one: merging 2k+
lines of Live-API code before ever running it on the real machine is how
you get un-debuggable breakage. **Roadmap:** once both pass their smoke
tests on the studio machine, port the UDP listener (~80 lines) into the
full script and retire the slim one.

## 2026-08-11 — Package renamed `MCP_Server` → `server`

The plan's repo map calls the folder `ableton-mcp/server/`. Kept the
vendor's internal structure otherwise; the rename touched two lazy imports
in `server.py` (now with a script-mode fallback) and test imports. All 143
vendor tests still pass, so the rename is proven safe.

## 2026-08-11 — als injectors live in `tools/`, not inside the server

They're offline file surgery (Ableton must be closed) with zero
dependencies on the MCP server — keeping them standalone means they can be
tested anywhere and can't destabilize the live control path. Wire them in
as MCP tools later, the way the plan sequences it ("test in isolation with
Claude Code before wiring into the MCP server").

## 2026-08-11 — vocal_to_midi and mashup server tools deferred

Hurliman's PR also contains `audio_analysis.py` (vocal→MIDI, key
detection, frequency-clash analysis) and server additions. The plan's
priority order puts these third ("later, when vocals enter the workflow"),
and each carries heavy deps (librosa etc.) that belong to Phase 2's
environment anyway. `docs/THIRD_PARTY.md` records exactly where to
retrieve them.

## 2026-08-11 — ElevenLabs module not vendored

Voice generation isn't in the XLNT plan. Less surface area = fewer
dependencies (`elevenlabs`, `python-dotenv` pin conflicts) on a machine
that must stay stable for music-making.

## From the plan (standing decisions)

- **Monorepo** — the pieces share code; the analysis functions will serve
  both the library analyst and the audio ears.
- **TCP = control plane, UDP = performance plane** — a dropped control
  packet corrupts a project; a dropped performance packet is one missed
  knob position out of 60/sec.
- **Fork, don't build from scratch** — uisato's server + Hurliman's tools
  did the reverse-engineering already.
- **Producer Pal stays installed** — stable fallback + reference
  implementation until the custom build fully surpasses it.
- **Commit style** — `tool: als tempo injection working`; one working tool
  per commit.
