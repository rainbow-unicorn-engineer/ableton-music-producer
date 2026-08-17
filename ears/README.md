# ears — Phase 4 (built) + the reverse-engineering pipeline (built)

→ *Claude can't hear audio natively — but it can read pictures and numbers
derived from it. This folder turns a bounce into both — and turns any
reference track into measurable targets you can chase.*

## The pieces

| File | Job |
|------|-----|
| `analyze_bounce.py` | **the one command**: loudness report + spectrogram PNG + JSON, all next to the bounce |
| `loudness.py` | integrated LUFS (BS.1770, gated), true peak (dBTP), loudness range, per-band energy balance. Uses `pyloudnorm` if installed, else a built-in meter validated against reference tones |
| `spectrogram.py` | mel spectrogram PNG → *time left-right, frequency low-high, brightness = energy* |
| `audio_io.py` | shared loader (soundfile-first, WAV fallback) |
| `references.py` | **reference cards**: analyze a target track once into `references/<name>.reference.json` (+ PNGs) — loudness DNA, key, tempo, arrangement skeleton |
| `compare_mix.py` | your bounce vs. a reference card (or any audio file): loudness delta, band-by-band gaps, stacked spectrograms. *"Make it sound pro" as a checklist* |
| `structure.py` | arrangement math: per-bar energy → labeled sections → `intro 16 → build 16 → drop 32` |
| `stems.py` | Demucs wrapper: split a track into vocals/drums/bass/other, then run the ears on each stem (needs `pip install demucs`) |
| `midi_extract.py` | audio → .mid: polyphonic with basic-pitch installed, built-in monophonic fallback otherwise. Best on single stems |
| `clash.py` | masking analyzer: where two sounds fight for the same frequencies — contested-% per band + the fix ("duck 250–500 Hz when the vocal plays") |
| `mashup.py` | acapella-over-beat matcher: smallest key transpose (relative-key aware), half/double-time warp plan, artifact warnings |

All exposed as MCP tools on the XLNT-Library server: `analyze_bounce`,
`make_reference_card`, `list_reference_cards`, `compare_mix`,
`analyze_structure`, `separate_stems`, `extract_midi` — the agent can run
the whole loop without you touching a terminal.

## The reverse-engineering loop

1. `python ears/references.py --file "C:/refs/Weekend (GRiZ flip).wav"`
   — one card per target track, made once.
2. Produce. Bounce. Then:
   `python ears/compare_mix.py --bounce mix_v3.wav --reference weekend-griz-flip --png`
3. Fix the top gap. Repeat. A track is *done* when the gaps list is empty
   (loudness within ~1 LU, true peak under -1 dBTP, no band more than a
   few dB off) — and you'd play it twice.
4. Going deeper on a reference: `stems.py --analyze` for how their drum
   bus and bass are balanced; `midi_extract.py` on the bass stem for the
   actual notes; `structure.py --png` for the arrangement to steal.

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
localization, and the full analyze_bounce chain — plus the pipeline
(`test_reverse.py`): tempo detection on a click track, section labeling
on a synthetic intro→drop track, reference-card roundtrip, compare_mix
deltas, the monophonic MIDI extractor on a known melody, and the Demucs
wrapper's guard rails. All synthetic audio; no real tracks needed.
