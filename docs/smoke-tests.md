# Smoke Tests — the checklist that proves each layer works

→ *A smoke test is a quick "does it turn on" test — the minimum action that
proves a component is alive, before trusting it with real work.*

Run these in order after `docs/setup-windows.md`. Each layer depends on the
one above it.

## 0. Producer Pal (fallback core)

- [ ] In Claude Desktop: *"connect to my Live set and tell me the tempo"*
- Expected: the correct BPM comes back.

## 1. TCP control plane

- [ ] Ableton open, `AbletonMCP` control surface enabled.
- [ ] In Claude Desktop: *"Create a MIDI track named TEST and write a 1-bar
      C minor chord."*
- Expected: the track appears in Ableton with a clip containing C–E♭–G.

## 2. param_dump (unlocks all plugins)

- [ ] Load Serum 2 (or any plugin) on track 0.
- [ ] In a terminal:
      `python ableton-mcp/tools/param_dump.py --track 0 --device 0 --name serum2`
- Expected: `plugin-dictionary/serum2.params.json` appears, full of named
  parameters with normalized values.
- [ ] Repeat for each FabFilter / Soundtoys / KClip / Waves / NI plugin the
      first time you use it.

## 3. UDP performance plane

**Post-merge (2026-08-13): one script does both planes.** Run
`scripts\install-remote-script.bat` (Ableton closed), then select only
`AbletonMCP` as the control surface — no more switching. `AbletonMCP_UDP`
is retired; don't select it (it would fight for TCP port 9877).

- [ ] After install: Ableton's log shows "UDP performance plane started
      on port 9878" alongside the TCP listening message.
- [ ] Map a macro or synth filter cutoff at track 0 / device 0 / param 1.
- [ ] Start a loop playing, then:
      `python ableton-mcp/udp/sweep_smoke_test.py --track 0 --device 0 --param 1`
- Expected: **watch the knob glide** in two smooth sine sweeps over ~8
  seconds. A stutter or two is fine (UDP is allowed to drop packets); a
  frozen knob is a failure.
- [ ] Optional deeper test: the XY mouse controller demo in
      `ableton-mcp/udp/examples/xy_mouse_controller/` (needs
      `pip install pynput screeninfo`).

## 4. als injection (offline .als surgery)

⚠️ Always run on a COPY of a set, with Ableton CLOSED — the injectors
rewrite the project file. (They write to a separate output path by default.)

- [ ] Save a tiny test set with one audio clip on a track named "Vocals".
- [ ] `python ableton-mcp/tools/als_warp_injector.py --help` and follow the
      usage to inject a couple of warp markers from a JSON file.
- Expected: opening the output `.als` shows the warp markers on the clip.

## 5. Offline unit tests (no Ableton needed — run anywhere, any time)

```bash
pytest ableton-mcp/tests/
```

- Expected: 152 passing. Run this after every change to the server or tools.

## 6. Reverse-engineering pipeline (no Ableton needed)

- [ ] Offline tests first: `pytest ears/tests/` — expected: all passing
      (includes `test_reverse.py`, the pipeline's own suite).
- [ ] **Reference card:** pick one target track (the Weekend GRiZ flip),
      then `python ears/references.py --file "C:/refs/<track>.wav"`.
- Expected: `references/<slug>.reference.json` + spectrogram + structure
  PNGs appear; the printed skeleton looks like the track's actual
  arrangement (sanity-check the drop positions by ear).
- [ ] **compare_mix:** bounce anything from Ableton, then
      `python ears/compare_mix.py --bounce <bounce>.wav --reference <slug> --png`
- Expected: a gaps list ("3.2 LU quieter", "sub 4 dB light") and a
  stacked-spectrogram PNG.
- [ ] **Stems** — Demucs wants **Python 3.11** (3.12 breaks its build
      tooling with a `pkgutil.ImpImporter` error). One-time setup in an
      Anaconda Prompt:
      `conda create -n xlnt-audio python=3.11 -y`, activate it,
      `pip install demucs basic-pitch`, then
      `setx XLNT_DEMUCS "C:\Users\<you>\anaconda3\envs\xlnt-audio\python.exe"`
      and restart Claude Desktop. First separation downloads the ~1 GB
      model. Then:
      `python ears/stems.py --file "C:/refs/<track>.wav" --analyze`
- Expected: `stems/htdemucs/<track>/` holds vocals/drums/bass/other WAVs
  plus per-stem LUFS and a stem-balance readout. First run is slow.
- [ ] **MIDI:** `python ears/midi_extract.py --file <bass stem>.wav --bpm <bpm>`
- Expected: a `.mid` appears; drop it on an Ableton MIDI track and the
  bassline is recognizably theirs. For **chords** (polyphonic), run it
  from the xlnt-audio env where basic-pitch lives:
  `C:\Users\<you>\anaconda3\envs\xlnt-audio\python.exe ears/midi_extract.py --file ...`
  — from the regular Python it falls back to one-note-at-a-time mode.
- [ ] **Via MCP:** in Claude Desktop, *"list my reference cards"* then
      *"compare my latest bounce against <name>"* — the agent should do
      steps 2–3 itself.

## 7a. Vocal tools (no models needed — instant)

- [ ] **Clash:** split any reference with stems, then
      `python ears/clash.py --a <vocals.wav> --b <other.wav> --png`
- Expected: contested-% per band, a "worst overlap near N Hz" verdict,
  and a bar chart. Vocal vs sub should read clean; vocal vs mids busy.
- [ ] **Mashup:** `python ears/mashup.py --acapella <vox> --beat <beat>`
      (add `--acapella-key`/`--beat-bpm` overrides if detection is unsure)
- Expected: transpose in semitones, warp % with half/double-time feel,
  and warnings if the numbers will sound ugly.
- [ ] **Via MCP:** *"where does this vocal clash with my beat?"* and
      *"how do I fit this acapella over my track?"*

## 7. Vibe search (CLAP)

- [ ] One-time, after `setup-audio-env.bat`: run the overnight embedding
      scan from an Anaconda Prompt:
      `conda run -n xlnt-audio python library-analyst\embeddings.py --scan`
      (resumable — stop and re-run any time; GPU makes it much faster).
- [ ] Check coverage: in Claude Desktop, *"what's my embedding status?"*
- [ ] **The vibe test:** *"find me sounds like 'haunted carousel music
      box'"* — results should FEEL right even where no filename matches.
      First query per session takes ~10–30 s (model load), then fast.
- [ ] **The by-ear test:** *"find sounds similar to <some library file>,
      by ear"* — should beat the feature-based similar_to on character.
