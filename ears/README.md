# ears — Phase 4 (not started)

→ *Claude can't hear audio natively — but it can read pictures and numbers
derived from it.*

Planned pieces:

- **Getting audio out:** the WAV-recorder Max for Live patch is already
  vendored at `ableton-mcp/tools/max4live/AudioCapture.amxd` — drop it on
  the master track, toggle to bounce whatever plays.
- `spectrogram.py` — render the WAV as a spectrogram → *picture of sound:
  time runs left-right, frequency low-high, brightness = energy* — with
  `librosa.display.specshow`, save PNG.
- `loudness.py` — measure LUFS → *the loudness standard streaming
  platforms use* — with `pyloudnorm`; report integrated LUFS + true peak.

Workflow: bounce → run both scripts → drop PNG + numbers into chat → the
agent reads the mix (muddy low-mids, harsh 3–4k, weak sub, over-limited)
and directs fixes. Later: wrap as MCP tools (`analyze_bounce()`).
