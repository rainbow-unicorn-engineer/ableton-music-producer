# ears — Phase 4 (built)

→ *Claude can't hear audio natively — but it can read pictures and numbers
derived from it. This folder turns a bounce into both.*

## The pieces

| File | Job |
|------|-----|
| `analyze_bounce.py` | **the one command**: loudness report + spectrogram PNG + JSON, all next to the bounce |
| `loudness.py` | integrated LUFS (BS.1770, gated), true peak (dBTP), loudness range, per-band energy balance. Uses `pyloudnorm` if installed, else a built-in meter validated against reference tones |
| `spectrogram.py` | mel spectrogram PNG → *time left-right, frequency low-high, brightness = energy* |
| `audio_io.py` | shared loader (soundfile-first, WAV fallback) |

Also exposed as the **`analyze_bounce` MCP tool** on the XLNT-Library
server, so the agent can measure a bounce without you running anything.

## Setup (once)

```bash
pip install -r ears/requirements.txt
```

**Getting audio out of Ableton:** drop
`ableton-mcp/tools/max4live/AudioCapture.amxd` on the master track — toggle
it to bounce whatever plays. (File → Export Audio works too.)

## The workflow

1. Bounce the section you're working on.
2. `python ears/analyze_bounce.py --file "C:/bounces/mix_v3.wav"`
3. Drop the PNG + JSON into a Claude chat (or let the agent call the
   `analyze_bounce` tool itself).
4. The agent reads the mix — muddy low-mids, harsh 3–4k, weak sub,
   over-limited — and directs fixes. Pair with MiniMeters screenshots for
   real-time confirmation.

## Reading the numbers

- **Integrated LUFS** — streaming targets ≈ -14; club masters -8 to -6.
- **True peak** — keep under **-1.0 dBTP** or lossy encoders clip.
- **Loudness range** — small = steamroller, large = dynamic.
- **Band energy** — dB relative to the loudest band; "low-mid close to 0
  while sub is negative" is the classic signature of mud.

## Tests

```bash
pytest ears/tests/
```

Validates the LUFS meter against BS.1770 reference behavior (calibration
tone, gain tracking, silence gating), inter-sample true peak, band
localization, and the full analyze_bounce chain.
