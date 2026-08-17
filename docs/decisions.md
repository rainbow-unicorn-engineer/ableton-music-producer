# Decisions — why things are the way they are

Newest first. One entry per decision that a future collaborator (human or
agent) might want to reverse.

## 2026-08-13 — Vocal tools built fresh, not vendored

The plan's deferred "vocal tools" (Hurliman's vocal_to_midi + mashup
server) are closed out by building the two missing capabilities natively
instead of vendoring: `ears/clash.py` (masking analyzer — per-band
contested-time between any two files, worst-frequency readout, concrete
duck/EQ fixes) and `ears/mashup.py` (key/tempo matcher — smallest
transpose via relative-key equivalence, half/double-time-aware warp
plan, artifact warnings past 8% stretch / 4 semitones). Reason:
vocal→MIDI was already superseded by `midi_extract.py`, and the fresh
modules integrate with the ears' loader, testing conventions, and the
jargon rule — where the vendored code would have brought its own audio
stack. `docs/THIRD_PARTY.md` still records where the originals live.

## 2026-08-13 — Remote Scripts merged: one script, both planes

The UDP listener (~90 lines: `start_udp_server`, `_udp_server_loop`,
`_process_udp_command`) is now ported into the full TCP script, exactly
as the two-scripts decision below planned ("once both pass their smoke
tests"). Both had passed on the studio machine, so the merge window was
open. Key adaptations: the UDP fast path calls the FULL script's
`_set_device_parameter` (chain-aware, name-or-index — richer than the
slim script's), batches fan out per-parameter so one bad index can't
kill its neighbours, a UDP startup failure can never take down the TCP
plane, and `schedule_message` falls back to a direct call outside Live's
main loop (which is also what makes the merge unit-testable —
`test_udp_merge.py`). The slim `AbletonMCP_UDP` folder stays in the repo
as reference but is retired: select only `AbletonMCP` in Preferences.
Install with `scripts/install-remote-script.bat`.

## 2026-08-12 — CLAP lives in the audio env; the MCP server bridges by subprocess

Vibe search shipped (`embeddings.py` + `vibe.py`). The CLAP model needs
Python 3.11 + PyTorch, so like Demucs it lives in the `xlnt-audio` conda
env; the library database just stores 512-float unit vectors (BLOB
column, waiting since Phase 2). The MCP server — running on the main
Python — embeds *queries* by shelling out to the audio env
(XLNT_AUDIO_PY), then does the cosine search itself in numpy: one model
dependency, zero new dependencies on the stable path. Cost: the first
vibe query per session pays ~10–30 s of model load. The overnight
`--scan` fills the column and is resumable. find_sounds stays as the
instant word-based fallback — ship the cake, keep the cake.

## 2026-08-12 — Reverse-engineering pipeline: heavy models guarded, never required

`stems.py` (Demucs) and `midi_extract.py` (basic-pitch) wrap models that
are gigabytes on disk and minutes per track. Neither is a hard dependency:
`stems` raises a plain-English install hint when Demucs is missing (the
exact message is under test), and `midi_extract` falls back to a built-in
monophonic autocorrelation tracker + a dependency-free Standard-MIDI-File
writer — the house librosa-first/fallback pattern from the analyst,
applied again. Consequence: the whole test suite runs on any machine;
the models install once on the studio machine and are picked up
automatically.

## 2026-08-12 — Reference cards live in `references/`, audio never copied there

A card is the *measurements* of a target track (JSON + spectrogram +
structure PNGs), not the track. Cards are committable (no copyright
issues, small files); the source audio stays wherever it lives. Card
names are slugs ("Weekend (GRiZ flip)" → `weekend-griz-flip`) so chat,
CLI, and MCP calls can all reference them loosely — `load_card` matches
fuzzily and lists what's on file when it can't.

## 2026-08-12 — `structure.py` has its own small tempo detector

It duplicates ~30 lines of the analyst's fallback BPM logic (spectral
flux + autocorrelation) instead of importing across packages. Reason:
ears modules stay standalone (each is a runnable CLI), and the analyst's
version is entangled with its database batch path. `references.py` — a
higher-level orchestrator — DOES import the analyst for key detection,
which is the monorepo's stated purpose ("the analysis functions serve
both the library analyst and the audio ears"). Low-level modules stay
independent; orchestrators may reach across.

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
