# Session Handoff — Bad and Boujee Edit + XLNT Studio state

*Written 2026-08-17 by the Cowork session that built Phases 0–4. For the
next agent (any model) picking up this work: read `docs/WHAT-WE-BUILT.md`
and `docs/ROADMAP-PRO-TRACKS.md` for the system; this file is the live
project state.*

## The song: "Bad and Boujee Edit" (bass-house bootleg)

- 124 BPM, **D# minor**, ACRAZE "Do It To It" as reference (reference
  card: `references/acraze-do-it-to-it.reference.json`).
- Arrangement: intro 1–9 → percussion 9–17 → melodic 17–29 → **drop 1:
  30–46** (16 bars) → **break 46–54** (piano chords `Break chords D#m
  i-VI-iv-V` on Piano track + hook vocal at 50–54) → **build 54–62**
  (risers, snare fill, laser) → **drop 2: 62–78** → outro TBD (~78–94).
- Latest grade (v5 vs ACRAZE): band pyramid within ~1 dB on every band;
  dynamics 12.7 LU (reference 9.9 — the break works); remaining gaps are
  loudness (−4 LU, mastering-stage) and true peak (−0.04, pull Main to
  −4 while writing; **mastering rack NGHTMREMaster3 on Main is OFF by
  design until mixdown**).
- The HOOK ("raindrop, drop-top") = arrangement bars 21–25 on track 44 =
  file beats 48–64 of the acapella (file in `C:\Users\gavin\Downloads`).
  Track 44 has CLA Vocals + clarity EQ (HP 111 Hz, +3 dB @ 3.5k, +2 dB
  @ 9k). Vocal clip at 30–34 muted (user's choice).
- Key tracks (1-based): 3 kick&snare, 9/10 hat+shaker loops, 15 iDEA LD 1
  (sounding lead; 404 Hz −2.5 dB carve), 12/16 alternate leads (muted),
  21 SUB (MIDI) — offbeat D#1 sub line (session clip `SUB offbeat D#m`),
  44/45/46 vocals, 53 Piano (Kontakt 8 + Hybrid Reverb + Echo).

## Next steps agreed with the user (phases from the roadmap)

1. Effects/depth on the bar-50 hook moment; sends to A ROOM / B DELAY
   returns everywhere (mix is dry); ear candy every 4–8 bars (library has
   2,249 vocal one-shots — `find_sounds`); drop 2 evolution (unmute 808
   tracks 23/24 in its back half).
2. Loudness/master pass LAST: rack on, ceiling −1.0 dBTP, compare_mix to
   ~−8.5 LUFS.

## Tooling state (important)

- `collect_bounce(song, section, reference)` files + analyzes + grades
  captures from `C:\tmp\ableton_capture.wav` (AudioCapture writes on
  toggle-OFF). Bounces live in `C:\Music Production\Bounces`.
- Pending install (repo is ahead of the running install): remote script +
  server now have `trim_arrangement_clip` and a self-trimming
  `copy_arrangement_clip` fix. Activate by copying
  `ableton-mcp/remote_script/AbletonMCP` to
  `C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\`,
  restarting Ableton, restarting Claude Desktop.
- House rules are baked into the Ableton server instructions: use the
  template's designated tracks, never create tracks unasked, copy notes
  with `get_clip_notes` instead of reinventing parts.
- Uncommitted repo changes may exist — run `git add -A && git commit &&
  git push` in `~/PycharmProjects/xlnt-studio`.

## The standing rule

Agent automates the mechanical 70%; the user owns the sacred 30% — what
it says, how it feels, when it's done. The user is producing this track
as a surprise for someone special. Make it slap.
