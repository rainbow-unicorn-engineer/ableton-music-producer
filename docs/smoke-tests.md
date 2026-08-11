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

- [ ] Switch the control surface to `AbletonMCP_UDP` (Preferences → Link,
      Tempo & MIDI). Only one script on TCP 9877 at a time.
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
