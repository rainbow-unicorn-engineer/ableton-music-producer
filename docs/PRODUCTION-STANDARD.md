# The Production Standard — What "Release Ready" Actually Means

*Written 2026-08-17 after an honest look at "Bad and Boujee Edit" v5.
This doc exists because the system told you the track was close to the
reference when your ears told you it was boring. **Your ears were right.**
This is the correction, and the standard we work to from now on.*

---

## Part 1 — What the numbers actually mean (metric literacy)

### The "within 1 dB of ACRAZE" claim

It is **literally true and nearly worthless.** Here is exactly what it
measured:

`compare_mix` takes the *average energy* of the whole track, buckets it
into six very wide frequency ranges, and compares the ratios between
those buckets. That's it.

Why that can't judge a record:

- **It's an average over 3+ minutes.** Your empty bars and your full bars
  get blended into one number. A track that is 50% silence and 50% wall
  of sound can average out identical to a consistently dense record.
- **Six buckets is almost no resolution.** "Mid" is 500–2000 Hz — that
  single number covers your lead, your vocal, your snare body, and your
  hat fundamentals all at once.
- **Ratios, not content.** White noise shaped to the same curve as ACRAZE
  scores a perfect match. So does a sine wave with the right EQ.
- **It cannot hear:** arrangement density, sound design quality, groove,
  transient impact, stereo width, movement, variation, tension, or
  whether a human wants to hear it twice.

**What band balance IS good for:** catching gross tonal faults. Way too
much 250–500 Hz = mud. No sub = thin on a club system. Highs 10 dB down =
dull. It's a *hygiene check* — like checking a photo isn't upside down.
It is not a grade.

### The metrics ranked by what they actually tell you

| Metric | What it catches | Weight in "is this good?" |
|---|---|---|
| Band balance (6-band) | gross tonal faults | ~5% |
| True peak | technical clipping | pass/fail only |
| Integrated LUFS | mastering stage only | 0% while writing |
| Loudness range (LRA) | whether sections contrast at all | ~10% |
| **Element density per section** | thin vs. full arrangement | **~30%** |
| **Variation rate** | boring vs. engaging | **~25%** |
| **Sound design quality** | signature vs. generic | **~30%** — *not measurable, only judgeable* |

The system currently measures the top three well, the middle two not at
all, and the bottom one never (no tool can). That imbalance is why it
gave you false comfort.

---

## Part 2 — The layer standard

A commercial bass-house / tech-house drop runs **18–25 simultaneous
elements.** Not 18 tracks — 18 things making sound at once. Here is the
full inventory, by role:

### Low end (3–4)
- Kick
- Sub (pure sine, mono, below ~100 Hz)
- Bass mid/growl layer (the *character* — distorted, filtered, the part
  people air-bass to)
- Optional: 808 or reese for accents/transitions

### Drums (6–9)
- Clap and/or snare on 2 & 4 (usually **both**, layered)
- Closed hats (offbeat 8ths or driving 16ths)
- Open hat (the "tss" that creates swing)
- Ride or cymbal wash
- Shaker / tambourine
- Percussion loop (congas, rims, found sounds)
- Top loop (a pre-mixed groove layer that glues everything)
- Tom / fill hits every 4 or 8 bars
- Crash on the downbeat of every 8

### Melodic (2–4)
- Main riff/lead
- Counter-melody or stab that answers it (call and response)
- Chord bed, often heavily filtered so it's felt not heard
- Optional: pluck/arp for top-end sparkle

### Vocal (2–5 in a bootleg — **this is your product**)
- Main hook phrase
- Chopped/stuttered version riding the beat
- Adlibs ("skrrt", "yeah", "woo") in the gaps
- Reversed or pitched tail leading into sections
- Vocal texture/pad (a formant-shifted sustain under the drop)

### FX & glue (4–6)
- Riser tail carrying **over** the drop's first bar (never stop at the
  transition — always let it bleed 1 bar in)
- Impact/boom on the downbeat
- Reverse cymbal or reverse vocal into each section
- White-noise sweep every 8 bars
- Atmosphere/room-tone bed (vinyl crackle, field noise) — the thing that
  makes a mix feel like a *place*
- Delay throws on the last word of a vocal phrase

### Movement (not elements — **rules**)
- Nothing static for more than 8 bars. Ever.
- Every 8th bar: a fill, a mute, a filter sweep, or an added layer.
- The back half of every 16-bar section differs from the front half.
- At least 3 automated parameters running at all times.

**Count your drop against that list. That count is the single best
predictor of whether a track sounds "full" or "plain."**

---

## Part 3 — Gap analysis: "Bad and Boujee Edit" v5

Read straight from the Live set on 2026-08-17.

### What is actually playing

| Section | Bars | Elements sounding |
|---|---|---|
| Drop 1 front | 30–38 | kick+snare, hats (34–38 only), shaker (34–38 only), iDEA LD 2, iDEA LD 1 (30–34 only), Serum 2, sub, vocal | **~7** |
| Drop 1 back | 38–46 | kick+snare, hats, shaker, sub, lead riff (**38–42 only**) | **4–5** |
| Break | 46–54 | **piano only** | **1** |
| Build | 54–62 | noise riser, uplifter, snare fill | **3** |
| Drop 2 | 62–78 | kick+snare, sub, and lead **or** hats — never both | **3–4** |

### The five findings, in priority order

**1. Drop 2 is broken, not just thin.** The clips alternate: bars 62–66
have the lead but no hats; 66–70 have hats but no lead; 70–74 lead again,
no hats; 74–78 hats, no lead. **There is no vocal anywhere in drop 2** —
your entire second half is missing the hook the song exists for. There is
no Serum, no iDEA LD 2. This isn't a taste problem, it's damage from
clips being placed piecemeal.

**2. The break is one instrument.** Bars 46–54 = piano chords alone. The
hook paste at bar 50 is **not in the set** (it was lost to an undo or a
reload). The "singalong trap" — the whole emotional payoff — does not
exist yet.

**3. Bars 42–46 have no melodic content at all.** Kick, hats, shaker,
sub. Four elements. This is the emptiest passage in the track and it sits
in the middle of your main drop.

**4. Entire categories are missing everywhere:** no clap, no open hat, no
ride, no percussion loop in the drops, no crash on downbeats, no reverse
cymbals, no atmosphere bed, no bass mid layer (you have sub only — the
sub is *felt*, the mid layer is what's *heard*), no vocal chops in the
drops, no adlibs.

**5. Nothing moves.** Zero automation in the project. No filter sweeps,
no volume rides, no delay throws. Every 8 bars is a photocopy of the
previous 8. The sends (A ROOM, B DELAY THRO) are unused, so the mix has
no depth — everything sits at the same distance from the listener.

### The honest summary

The track has a correct *skeleton* and roughly a third of a body.
Skeleton is what the last session built well: right key, right tempo,
right section lengths, right transitions, sub present, band balance
clean. Body is layers, movement, and detail — and that's most of what
makes a record sound professional.

---

## Part 4 — The sacred 30%: what only you can do

The 70/30 split isn't "I do the boring parts." It's a real boundary based
on what can and can't be delegated. Here is the 30%, with examples from
this exact track.

### 1. Taste — the keep/kill verdict

Every A/B comparison. Whether a sound is *right*, not just present.

- *In this track:* you heard "boring and plain" when the metrics said
  fine. That judgment was correct and no tool produced it.
- *Practice:* after every change, ask "better or worse?" — out loud,
  fast, first instinct. Log the verdict. Your first instinct at 2 seconds
  is worth more than your analysis at 2 minutes.

### 2. The idea — the reason the track exists

The hook, the concept, the "what if."

- *In this track:* "Bad and Boujee over bass house so people lose their
  minds" **is** the idea. It's a good one. Everything serves it.
- *Practice:* write the one-sentence idea at the top of every project.
  If a change doesn't serve that sentence, it's decoration.

### 3. Recognition — hearing the accident that's worth keeping

**Corrected 2026-08-18.** This item originally said "describe the sound
you want and the agent chases it." That's how you execute a sound that
already exists, and it's the wrong model for finding one that doesn't —
you can't describe a sound the world hasn't heard, because the words for
it come *after* the discovery.

The real skill is recognition: generating a large volume of strange
material and hearing the one thing that's alive. Most producers hear the
same accident and press undo.

- *In this track:* not applicable — a bootleg from sample packs has no
  room for a signature. This one is for fun.
- *Practice:* the two-second rule. When auditioning a batch, react before
  you can think: "no / no / no / **wait**." Only "wait" counts. Three
  hits per hundred candidates is a good day.
- **Full method: `FINDING-YOUR-SOUND.md`.**

### 4. Groove and feel — where the notes actually sit

Pocket, swing, velocity, human timing. A machine can quantize; only you
can tell if it *bounces*.

- *In this track:* the off-beat sub line I wrote is mathematically
  correct. Whether it *bounces* against your kick is a judgment call —
  nudging it 5–10 ms late is often what makes bass house feel drunk and
  good.
- *Practice:* loop 2 bars, close your eyes, nod your head. If you can't
  nod, the groove is wrong regardless of the grid.

### 5. Emotional arc — tension, release, and what to withhold

Where the track breathes. What you deny the listener so the payoff lands.

- *In this track:* the reason the break matters is that it *takes the
  drums away*. Restraint is the technique. Deciding to hold the hook
  back until bar 50 — that's arc design, and it's yours.
- *Practice:* sketch the energy curve on paper (0–10 per 8 bars) before
  arranging. Then build to it.

### 6. Selection — what makes the cut from 45,000 sounds

I can return 10 candidates in a second. Which one is *the* one is taste.

- *In this track:* I found the Getter/EvoSounds risers. Whether that
  specific riser feels like *your* record is your call.
- *Practice:* audition candidates in context (in the mix, at the right
  bar), never soloed. A sound that's great alone is often wrong in place.

### 7. Knowing when it's done

The hardest one. Metrics never say "done."

- *Practice:* a track is done when you'd play it out twice in one set and
  not skip it. Not when the numbers match a reference.

### What is NOT in the 30% (delegate all of it)

Finding sounds. Placing and copying clips. Building arrangement
skeletons. Gain staging. EQ carving for masking. Measuring loudness.
Naming and filing bounces. Comparing to references. Writing MIDI drafts.
Setting up sends. Renaming tracks. Reference cards. Documentation.

**If you're doing any of the above by hand, tell me and I'll take it.**

---

## Part 5 — What the system needs to become the tool you want

The gap between "good assistant" and "tool you'd give a top producer" is
that the system currently measures *technical hygiene* and can't see
*arrangement quality*. Build order:

1. **Arrangement Doctor** *(biggest win)* — reads the Live set directly
   and reports, per 8-bar block: elements sounding, categories missing
   (using Part 2's inventory), automation count, and repetition score.
   Output: "Drop 2 bars 62–66: 3 elements. Missing: clap, open hat, perc,
   bass mid, vocal, crash. No automation. Identical to 70–74."
2. **Reference layer census** — Demucs-separate a reference, count the
   elements and density per section, and store it in the reference card
   so comparisons are *"their drop has 14 layers, yours has 5"* instead
   of decibels.
3. **Stereo/depth analysis** — mid/side energy per band + reverb-tail
   estimate. Catches "everything is dry and centered," which is most of
   what "flat and boring" means in a mix.
4. **Variation score** — spectral difference between consecutive 8-bar
   blocks. Flags static sections automatically.
5. **Automation writer** — the API supports clip envelopes; give the
   agent the ability to draw filter sweeps, volume rides, and send
   throws instead of asking you to.
6. **Session snapshot/versioning** — save named versions of the set so no
   edit is ever lost (the bar-50 hook disappearing should be impossible).

Items 1, 2 and 4 turn "sounds boring" from a feeling into a measurement.
Item 5 removes the largest remaining manual burden. Item 3 catches the
depth problem. Item 6 protects the work.

---

## The standing rule, restated honestly

The agent automates the mechanical 70% **and measures the technical.**
You own the sacred 30% — taste, idea, character, groove, arc, selection,
and done-ness. The system's job is to make sure the only thing standing
between you and a great record is a decision only you can make.
