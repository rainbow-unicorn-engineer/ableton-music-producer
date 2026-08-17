# How XLNT Studio Makes Music — The Workflow, Explained

*The companion to the User Guide. That one lists the tools; this one
answers "…but then what?" — how a song you love becomes a recipe, how a
recipe becomes your track, and how you become a sound designer along the
way. Plain English throughout, → marks a jargon translation.*

---

## The loop at a glance

```
you share a track you love, and say WHAT you love about it
        ↓
CARD      the track's measurable DNA, made once      (minutes)
        ↓
DISSECT   stems, MIDI, structure, clash — the full autopsy   (one session)
        ↓
RECIPE    a written how-to in skills/ — the reusable lesson
        ↓
SKETCH    we build from the recipe in YOUR Ableton, together
        ↓
BOUNCE → COMPARE → FIX   the improvement loop, every session
        ↓
SHIP      done = gaps closed + you'd play it twice
```

Every arrow is a thing you can say out loud to Claude. The cookbook and
your skills grow one lap at a time.

---

## What "dissecting the flip" actually does

The card told us WHAT the Weekend flip is (G minor, 144, -6 LUFS,
drop-heavy structure). Dissection answers HOW it works. Five moves, all
automated, ~20 minutes of machine time:

1. **Stem split** — Demucs pulls it into vocals / drums / bass / other.
   Now instead of one wall of sound, you have four things you can study
   (and hear!) separately. *Open the stems in Ableton and listen to just
   their drums. This alone is a masterclass.*
2. **Per-stem ears** — each stem gets measured: how loud is their drum
   bus vs. their bass? What frequencies does their vocal own? Result:
   "drums sit 2 LU under the bass" — numbers you can copy.
3. **MIDI extraction** — the bass stem becomes a .mid file. Drop it on
   an Ableton track, and you're looking at GRiZ's actual bassline notes:
   the rhythm, the intervals, where it breathes. Steal the *grammar*,
   not the audio.
4. **Clash analysis** — vocal stem vs. everything else: where did they
   carve space for Mac Miller's voice? ("their beat ducks 300-500 Hz
   when the vocal plays") — mixing technique, extracted.
5. **The recipe gets written** — everything above lands in one document
   (see below). The track is now a lesson you own forever.

## Bounces: what to export, when

→ *A bounce = your project rendered to one audio file. File → Export
Audio/Video.*

| Situation | What to bounce | Why |
|---|---|---|
| Working on a drop/section | Just those bars (loop-select them, export selection) | Fast loop: 30 seconds to bounce, instant analysis of exactly what you're touching |
| End of a session | The whole track so far | Structure + loudness comparisons need the full arc |
| "Is my low end right?" | The section, twice: full mix and with vocal/lead muted | Feeds `analyze_clash` — your own masking check |
| Done-ish | Full track, best export settings | The final `compare_mix` against the card before shipping |

Rule of thumb: **bounce what you're working on, compare the whole thing
weekly.** Both take one sentence to Claude afterwards.

## What goes in a recipe, and why it matters

A recipe (one markdown file in `skills/`, template provided:
`_TEMPLATE-recipe.md`) captures five things: the **arrangement math**
(section lengths and what changes at each boundary), the **sound
palette** (each element mapped to the closest sounds in YOUR library,
with the exact search queries), the **signature techniques**
(step-by-step device settings for the 2-3 tricks that make the style),
the **mix targets** (the card's numbers restated as goals), and **what
you learned** using it.

Why it's useful: it converts hours of study into minutes of setup — next
time you want "GRiZ funk pocket," the agent reads the recipe and builds
the session skeleton while you make coffee. And it *compounds*: recipe
#30 gets written faster and used better than recipe #1, because by then
half its techniques reference things you already know. This is the
massive book of knowledge you asked about — it just gets written one
dissection at a time, in your own words, about your own tools.

**Where the book lives:** `plugin-dictionary/` (what your gear does),
`skills/` (how styles are made), `references/` (what great tracks
measure), `docs/` (how the system works + why decisions were made). A
new person reading those four folders in a year would inherit everything
you've learned. Export any of it to PDF whenever you want a readable
volume.

## Building a song from scratch, together

Yes — and here's exactly how a guided session runs:

1. **You pick the seed.** A reference ("like the flip but darker"), a
   vibe sentence for the library, or just a key + tempo.
2. **I build the skeleton in your Ableton** — tempo, track groups from
   your template, a drum pattern, a sub line, chords — narrating every
   choice: *"I'm putting the chords on a minor 7th because..."* You say
   yes/no/why at each step. That's the lesson format.
3. **You make the decisions that matter.** I offer 3 sounds for the
   bass; you pick by ear. I draft two hook rhythms; you choose or hum a
   third. Your taste is the instrument being trained.
4. **Sound design moments get zoomed in.** When we need a sound that
   doesn't exist, we open Serum and build it knob by knob — and whatever
   we discover goes in the dictionary/recipe immediately.
5. **Every session ends with bounce → analyze.** You'll watch your own
   numbers walk toward the reference card's, week over week.

## What captivates human ears (the honest version)

No formula guarantees a hit — anyone who says otherwise is selling
something. But decades of music cognition research + what the loudest
genres keep proving give us reliable levers:

- **Tension and release.** The build-drop cycle is a chemical trick:
  anticipation (rising energy, filtered highs, snare rolls) then payoff
  (full spectrum, sub arrives). Your structure analyzer literally graphs
  this. The GRiZ flip's 44-bar drop works because the groove IS the
  reward, re-earned every 8 bars with small changes.
- **The voice zone.** Human ears prioritize 300 Hz–3 kHz — where speech
  lives. Sounds that *talk* (formant filters, vowel-ish growls, vocal
  chops) grab attention because your brain is wired to check whether
  someone's speaking. This is why talky basses rule your genres.
- **Novelty inside familiarity.** The most-loved sounds are ~80%
  expected, 20% surprising (researchers call it the MAYA principle —
  Most Advanced, Yet Acceptable). A totally alien track gets skipped; a
  formula track gets forgotten. Steal structure, invent timbre.
- **Movement.** Static sounds die. LFOs on wavetable position, filter
  wobble, sidechain pump, automation on everything — ears track change,
  not states.
- **Physical low end.** Sub bass is *felt*, not just heard — it's the
  body's channel. Clean, mono, unwavering sub = the platform everything
  else dances on. (Your library report says you're armed for exactly
  this.)
- **Repetition with earned variation.** Hooks work by coming back. The
  craft is changing 10% each return so repetition feels like a friend,
  not a loop.

**How much Serum?** Start with: one patch per song that you built or
heavily modified yourself — that's your signature developing. Use
library samples for everything that isn't the star. As you grow, the
ratio shifts. The `serum2.md` dictionary page (new) covers the knobs
that matter; the deeper knob-by-knob education happens live, in
sessions, documented as we go.

## Finding your lane

"What's unsaturated?" deserves research, not vibes — scenes move
monthly. The framework: unsaturated lanes are almost always
**intersections** (two established sounds not yet combined well), **
revivals with new tools** (an old genre rebuilt with modern sound
design), or **texture gaps** (everyone in a genre using the same
presets = an opening for anyone who doesn't). Your edge is measurable:
a library that skews hard into bass music + a system that can dissect
any candidate sound in minutes. When you're ready, we run a dedicated
research session: survey what's rising, card a handful of frontier
tracks, cross-reference against what your library and skills can
uniquely serve, and pick a lane on evidence.

---

*The rule, as always: the system automates the mechanical 70%. The
sacred 30% — what it says, how it feels, when it's done — is why anyone
will press play twice. That part is yours, and it's trainable. That's
what all of this trains.*
