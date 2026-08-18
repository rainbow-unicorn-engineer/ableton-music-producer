# Roadmap — From Working System to Label-Worthy Tracks

*The goal shifts now: Phases 0–4 built the studio assistant. This roadmap
is about using it to reach the quality bar of the artists you study —
Skrillex, Levity, David Guetta, The Chainsmokers — and to reverse-engineer
their records into skills you own.*

## Part 1 — Yes, you can reverse-engineer your favorite tracks

Here's the honest breakdown of what's possible, from already-works to
needs-building:

**Works today.** Drop any track (a purchased file or your own bounce)
into `analyze_bounce`: you get its loudness DNA (LUFS, true peak,
dynamics), its frequency balance (how much sub vs. mids vs. highs), its
spectrogram (see the arrangement's energy visually), and via the library
analyst its key and tempo. Comparing those numbers against your own
bounce is already real reverse-engineering: "their sub sits 6 dB above
their low-mids; mine doesn't."

**Buildable next (small):** a `compare_mix` tool — your bounce vs. a
reference, side by side: loudness delta, band-by-band difference,
spectrograms stacked. This turns "make it sound pro" into a checklist of
measurable gaps. *Highest payoff per line of code in this whole roadmap.*

**Buildable next (medium):** a **structure analyzer** — energy over time,
sliced into bars → "intro 16 bars, build 16, drop 32, break 16..." The
arrangement math of any reference, extracted automatically. This feeds
directly into `skills/` recipe docs.

**Buildable (bigger, well-trodden):** **stem separation** — AI models
(Demucs) that split a finished track into vocals / drums / bass / other.
Then each stem goes through the ears separately: how their drum bus is
balanced, what their bass actually does under the vocal. Also **melody →
MIDI extraction** (basic-pitch) — pull the chord progression and topline
of a reference into a MIDI clip you can study in Ableton.

**The honest limit.** No tool recovers their actual synth patches, plugin
chains, or session. Sound-design reverse-engineering stays a craft:
listen, look at the spectrogram, find the closest sound you own
(`similar_to` and `find_sounds` help), and resynthesize toward the
reference. That craft is exactly what the plan's Phase 5 recipes capture
— and each reverse-engineered track becomes a recipe you never have to
figure out twice.

## Part 2 — Optimize the system (build order, by payoff)

1. **`references/` workflow + `compare_mix`** — a folder of your target
   tracks, each analyzed once into a "reference card" (JSON + PNG);
   a tool that diffs any bounce against any card. *Small build.*
2. **Structure analyzer** (`ears/structure.py`) — bar-by-bar energy map →
   arrangement skeletons for the recipe docs. *Medium.*
3. **Stem separation** (Demucs) + per-stem ears. *Bigger; needs a beefy
   one-time model download — the Alienware can handle it.*
4. **MIDI extraction** (basic-pitch) — reference chords/toplines as MIDI.
5. **AGT macro racks** for your workhorse plugins (the Phase 3 plan:
   Serum, Pro-C 2, Saturn, Decapitator, KClip) so the agent can ride the
   sounds it helps design.
6. **CLAP vibe search** — the deferred cherry: search your library by
   *sound* similarity to a reference clip, not just words.
7. **Merge the two Remote Scripts** (TCP+UDP in one) — quality-of-life.

## Part 3 — The craft loop that actually gets you signed

Tools don't get tracks signed; reps do. The weekly cycle, using
everything built:

**1. Dissect one reference (60–90 min).** Pick one track you'd kill to
have made. Run it through the ears (+ stems and structure when built).
With Claude, write the recipe doc in `skills/`: arrangement math, sound
palette (with `find_sounds` queries to your closest matches), signature
techniques, mix targets (their LUFS, their band balance). One per week —
that's a cookbook of 50 in a year.

**2. Sketch fast, from the recipe (2–3 sessions).** Agent sets up the
session from the recipe: tempo, track groups, sounds found and loaded,
MIDI drafts of the progression. You spend your time on the 30% — the
hook, the sound design, the feel. The plan's anti-procrastination clause
is law: at least one musical session per week, always.

**3. Bounce → ears → fix, every session.** End each session with a
bounce and `analyze_bounce`. Fix the top measurable problem (mud, weak
sub, over-limiting) *while the session is fresh*. Clean mixes come from
catching problems at sketch stage, not heroic mastering.

**4. Finish against the reference.** A track is "done" when
`compare_mix` against its reference card shows: loudness within ~1 LU of
target, true peak under -1 dBTP, no band more than a few dB off the
reference balance, and — the part no meter judges — you'd play it twice.

**5. Ship and repeat.** Finished > perfect. Every genre you named runs
on different targets (tearout lives at 140+ BPM and crushed dynamics;
Guetta/Chainsmokers pop-dance lives near 120–128, more dynamic, vocal
up front) — your reference cards make those differences explicit numbers
instead of folklore.

## The standing rule

From the original plan, unchanged, because it's the whole game: **the
agent automates the mechanical 70%; you own the sacred 30% — what it
says, how it feels, when it's done.**
