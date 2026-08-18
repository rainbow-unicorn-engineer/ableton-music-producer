# Track 001 — "UKG Demon" · Session & Sound Design Lesson

*Everything we built, every choice explained, and the full demon-bass
recipe. Your first entry in the cookbook — come back to this whenever
you forget why something works. G minor · 138 BPM · started 2026-08-15.*

---

## Part 1 — Why every choice in the sketch

**138 BPM.** Dead center of the UK garage pocket (the scene lives
130–140), and deliberately NOT 140/144 — enough contrast from your
Weekend-flip work that the two don't blur.

**G minor.** Your library's top keys are all minor, the flip card is
G minor, and minor = the darkness this track wants. Practical bonus:
everything you learn here transfers key-for-key to the flip rebuild.

**The 2-step kick (beats 1 and the "and" of 2).** House/techno kicks
land on every beat — a march. Garage *removes* the kick from beat 3,
so the pattern constantly falls forward into the next bar. That missing
kick is the genre. → *Syncopation: putting weight where the ear doesn't
expect it, creating pull.*

**Snares on 2 and 4 (the backbeat)** — the oldest contract in popular
music; the listener's body clock. Ghost snares (velocity ~40) at the
swung end of bars add the "live drummer" flutter.

**The swing — the single most important lesson in this file.** Every
off-16th hat is placed at **60% swing**: instead of the grid position
(x.25 / x.75), they land late (x.30 / x.80). Open the drum clip and
LOOK: notes sitting just right of the gridlines. That lateness is the
shuffle, the bounce, the human. A grid-perfect version of this exact
pattern is the "algorithmic sound" listeners are tired of. Velocities
also vary (45–70) — machines hit identically, humans don't.

**The rolling sub.** Long root G1 anchors each bar ("this is home"),
then syncopated stabs and a swung octave pop (G1→G2 at the and-of-2) —
pure garage bassline vocabulary. It ends on D (the 5th) as a question
mark that pulls the loop back around. Sub rule you'll keep forever:
**one note at a time, no unison, mono below ~150 Hz.**

**The demon's silence.** DEMON BASS plays only 4 notes, all placed in
gaps the sub leaves. → *Call and response: the oldest funk trick —
one voice asks, another answers.* Later, the vocal takes the "call"
role and the demon answers IT. A monster that never shuts up isn't
scary; one that answers from the dark is.

**Dark stabs (Gm → Gm → Dm → F).** The garage organ-stab role, voiced
from G minor's own chord family. Dm is the dark cousin (minor 5th
chord — moody, unresolved); F major briefly lifts before falling back
into Gm — tension earns release, in miniature, every two bars.

**Garage Kit (Ableton Core).** Right idiom, zero effort. Drum-sound
upgrades from your 45k library come later — sketch first, gold-plate
never (until it's earned).

## Part 2 — The Demon Bass (Serum 2 recipe)

*Goal: a bass that TALKS — formant movement in the 300 Hz–3 kHz "voice
zone" reads as speech to the human brain, which is why talky basses
grab attention like someone calling your name.*

**Step 0 — expose the knobs (once, unlocks remote control forever).**
In Live, unfold the Serum 2 device (▼ in its title bar) → click
**Configure** → now, in Serum's own window, click/move each control
listed below — each one you touch appears in Live as an automatable
parameter. Touch at minimum: Macro 1–4, Filter Cutoff, Filter
Resonance, OSC A WT Position, Warp amount. When done, run `param_dump`
so the dictionary learns them and Claude can drive them in every
future session.

**The patch, from init (do these in order, listen after EVERY step —
that's the ear training):**

1. **OSC A wavetable:** open the wavetable browser → Vocal/formant
   territory — any table with *vowel / formant / talk* in the name.
   Sweep WT Position by hand and listen: it literally changes vowels.
   Park it somewhere mid.
2. **Range:** OSC A octave **-1** (growl register, since our MIDI sits
   at G2). **Unison = 1** (none) — this is a bass; keep it mono-fat,
   not chorus-wide.
3. **OSC B:** on, plain **sine**, octave **-1**. It's not for hearing —
   it's fuel for step 4.
4. **Warp = FM (from B), amount ~30–40%.** → *FM: oscillator B shakes
   oscillator A hundreds of times per second; the shaking creates new
   harmonics — the snarl.* This knob is the anger dial. Past ~60% it
   becomes noise; the sweet spot growls.
5. **Filter on** (route OSC A+B): type = a fat low-pass (MG-style) or
   Multi/Notch for extra talk. **Cutoff ~400 Hz, resonance ~35%.**
   The filter is the mouth — closed = "oo", open = "ah".
6. **LFO 1 → Cutoff:** drag the LFO 1 header onto the Cutoff knob →
   *the drag-anywhere trick: any wiggle source can drive any knob.*
   Rate **1/4** (synced) to start. Amount: generous — you want the
   mouth visibly opening and closing. Then try drawing the LFO shape:
   a falling ramp = "wow", a double-dip = "wubwub". This is where
   YOUR demon stops sounding like anyone else's.
7. **Envelope 2 → WT Position** (drag it on, medium decay): every note
   *changes vowel as it speaks*. Motion = life.
8. **Global:** Mono + Legato on, Portamento ~30–50 ms — slides between
   the G→F→A# notes like a voice, not a keyboard.
9. **Serum FX:** Distortion (Tube, drive ~25–30%, **post-filter**) for
   grit; a touch of Serum's EQ to tame anything piercing above ~5 kHz.
   Skip Hyper/Dimension — width belongs to stabs and textures, not
   the bass.
10. **After Serum (Ableton chain), when it's talking:** Saturn 2 —
    two bands split at ~120 Hz, drive the TOP band only (the
    dictionary's #1 trick: gritty mids that read on a phone speaker,
    clean sub underneath).

**How to judge it (borrowed ears until yours arrive):** solo DEMON
BASS + UKG DRUMS. If the demon disappears on a laptop speaker, it
needs more FM/distortion in the mids — not more volume. If it sounds
"bee-like," warp is too high. If the wobble feels stiff, the LFO rate
fights the swing — try 1/4 dotted or draw a lazier shape.

## Part 2½ — Patch log (what Claude set remotely, live values)

Set via the exposed Live parameters on DEMON BASS → Serum 2:

| Parameter | Value | Why |
|---|---|---|
| Filter 1 On | On | the "mouth" |
| Filter 1 Freq | 425 Hz (norm 0.5) | mouth mostly closed — the LFO opens it |
| Filter 1 Res | 35% | vowel emphasis without whistling |
| Filter 1 Drive | 15% | grit inside the filter itself |
| A Warp Mode | **FM (B)** (norm **0.48**) | the snarl engine — found by remotely scrubbing the menu and reading the names back |
| A Warp (amount) | 35% | angry, not bees |
| A WT Pos | 50% | mid-table vowel; Env 2 will move it |

Useful forever — Serum 2 warp-menu positions (normalized): Soft Sat
0.46 · **FM (B) 0.48** · FM (Noise) 0.51 · FM (Filter 2) 0.55 ·
FME (Sub) 0.61 · FML (C) 0.67 · FML (Filter 2) 0.72 · PD (Filter 2)
0.81 · AM (C) 0.86. (Also learned: the set-parameter confirmation text
lags one step behind — trust the re-read, not the confirmation.)

## Part 3 — Ableton survival lessons (from this session)

- **Tab** switches Session view (the clip grid — where our clips live)
  and Arrangement view (the timeline — empty until we commit).
- **Double-click a clip** → piano-roll editor at the bottom. Go LOOK at
  the swing in the drum clip.
- **▶ on a clip plays it; Ctrl+Z undoes** — including everything Claude
  just built (we share one undo timeline). **Ctrl+S after anything you
  like.**

## Part 3½ — Bounce v1: the night's biggest lesson

First bounce measured (`ukg-demon-v1.wav`, 4 bars): -10.9 LUFS, true
peak 0.03 dBTP (at the ceiling — no headroom), sub-dominant balance,
highs at **-19.8 dB** — ten dB *darker* than the GRiZ reference card.

Which cracked the case: the track was ALREADY dark. Every complaint of
the night — "background," "no punch," "not dark," "can't hear the
difference" — traced to one cause the ears found in seconds: **the
demon's register (mids) sat -9.8 dB vs. the reference's -2.8 — buried
7 dB below where a featured voice lives.** A mixing problem wearing a
sound-design costume.

**The lesson, permanent:** *quiet masquerades as weak, and weak
masquerades as "bad sound." Before redesigning a sound that feels
lame — check its level first.* Fix applied by gain-staging DOWN
(drums -1.9, sub -1.7, stabs -2.5 dB; demon untouched) — you turn
everything else down, never the hero up, or the mix ratchets to the
ceiling. Also learned: the ear can't A/B from memory (toggle-test
instead), ear fatigue after an hour of looping is physiology, and every
tweak session starts with a "before" bounce from now on.

Also tonight: the CLAP embed scan finished — 44,936 sounds in meaning
space. Vibe search live.

## Part 4 — Where this track goes next

Vocal (the demon's conversation partner — AlterBoy'd, dark), a 16-bar
intro from library textures, arrangement (steal the skeleton math from
a carded reference), first bounce → `analyze_bounce` → first
`compare_mix`. Each step gets added to this file. **What I learned:**
(yours to fill in — one honest sentence per session.)
