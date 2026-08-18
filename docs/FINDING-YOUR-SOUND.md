# Finding Your Sound — A Discovery Protocol

*Written 2026-08-18, correcting a mistake in `PRODUCTION-STANDARD.md`.
That doc said your job was to describe the sound you want so the agent
could chase it. That's a recipe for executing sounds that already exist.
This doc is about the other thing — finding one that doesn't.*

---

## The correction

**Sound design intent is not specification. It is recognition.**

You cannot describe a sound the world hasn't heard, because the words for
it don't exist yet. "Talking bass" describes Tape B *after* Tape B. The
description is always downstream of the discovery.

What actually happens:

1. Someone generates a large volume of strange material — usually while
   trying to do something else.
2. One thing sounds *wrong in an interesting way.*
3. They **recognize** it. This is the whole skill. Most producers hear
   the same accident and hit undo.
4. They develop it obsessively and put it on everything until people
   associate the sound with their name.

Step 3 is the sacred 30%. Steps 1 and 2 are volume problems — and volume
is exactly what a machine is for.

**So the division is:**

| The system | You |
|---|---|
| Generate hundreds of candidates | Hear the one that's alive |
| Push tools past sane settings, at scale | Say "that — again, more of that" |
| Capture and catalogue every accident | Refuse to lose the thread |
| Measure how *unlike* everything else a sound is | Decide it's yours |
| Reproduce and vary a chosen direction | Put it on every track until it's a signature |

You never have to describe the destination. You only have to react
honestly to what you hear — which is the one thing you're already
excellent at (you called this track boring while the meters said fine).

---

## How the signatures you admire were actually found

Read these as *mechanisms*, not trivia. Every one is reproducible.

**Rezz — constraint and repetition.** A narrow palette (mid-range wobble,
few elements, hypnotic repetition) used relentlessly. The sound isn't
technically complex; it's *identifiable* because she never diluted it.
Mechanism: **radical constraint**, then repetition until it's a brand.

**Skrillex — misuse at extremes.** Wavetable position automated far past
musical intent, run into distortion stages never designed for it. The
"scream" existed because the tool was pushed somewhere its designers
didn't imagine. Mechanism: **abuse the tool**.

**Burial — source material nobody else has.** Found vocals, vinyl noise,
deliberately unquantized timing. Impossible to copy because the raw
ingredients were personal. Mechanism: **own the source**.

**Flume / Tape B — resampling depth.** A sound bounced, mangled, bounced
again, four or five generations deep. By generation three the origin is
unrecognizable and unclonable. Mechanism: **resample until it's yours**.

**Bassnectar — physical priority.** Designed for a body in a room, not
for headphones. Mechanism: **optimize for a different target than
everyone else**.

Five mechanisms: **constrain, abuse, own the source, resample deep,
change the target.** None require talent you don't have. All require
volume and honest ears.

---

## The protocol

### Phase 0 — Set the constraint (30 minutes, once per sound-hunt)

Pick a box and stay in it. Constraint is what makes discovery possible;
infinite options produce averages.

Examples of a good box:
- One synth, no presets, one oscillator.
- One source recording (your voice, a door, a car) and nothing else.
- Only sounds that came out of a chain you built and can't fully predict.
- A rule: nothing may be used unprocessed. Everything is resampled twice.

Write the box down. Breaking it later is fine — *unconsciously* drifting
out of it is what kills sound-hunts.

### Phase 1 — Volume (the system's job)

I generate 50–200 candidates inside the box: randomized macro states,
extreme parameter sweeps, chains applied in wrong orders, resample
generations. Every single one gets bounced, auto-named, analyzed and
catalogued — so nothing is ever lost to a closed window again.

Your involvement here is **zero**. You do not audition while I generate.

### Phase 2 — The listening pass (your job, 20 minutes)

You listen to the batch in one sitting with one instruction:

> React in under two seconds. "No" / "no" / "no" / **"wait."**

Only "wait" matters. You are not judging quality — most of it will be
garbage, that's the point. You're listening for *aliveness*: something
that makes you lean in, or laugh, or feel slightly uncomfortable.

Log every "wait." Three per hundred is a good hit rate.

### Phase 3 — Development (both)

Take each "wait" and I generate 30 variations *around* it — same
direction, different degrees. You listen again. This converges fast:
usually two rounds to find the version that's undeniable.

Then: **resample it and run it back through Phase 1.** Depth is where
uniqueness lives. A sound at generation four cannot be reverse-engineered
by anyone, including us.

### Phase 4 — Commit and repeat it

A signature isn't one great patch — it's a sound people can *name after
you*. That requires you to use it on the next five tracks even when
you're bored of it. You will get bored long before the audience notices
it. That gap is where most producers abandon their own sound.

Rule: **when you find it, it goes in every track for a year.**

---

## What we build to make this real

Three tools, in order of value:

**1. Novelty score.** You have CLAP embeddings on 45,000 sounds — a map
of everything you own. Any new sound can be measured for *distance from
its nearest neighbour in that map.* High distance means: this doesn't
sound like anything in a 45,000-file library. That is a real, computable
proxy for "nobody has heard this." Nothing else on the market does this.

**2. The Sound Lab.** Batch generator: take a source, apply N randomized
processing chains (order, depth, and settings varied), bounce every
result, score each for novelty, and hand you the top 20 ranked. This is
Phase 1 automated end to end.

**3. Capture-everything.** Any sound that plays in the studio gets
recorded, embedded and catalogued automatically, so "that weird thing
from Tuesday" is always findable. The bar-50 hook disappearing on us is
exactly the failure this prevents — no accident is ever lost.

Together these turn sound discovery from luck into a *process with a
throughput*: candidates per week, hit rate, development cycles. That's
the workflow other producers would want to know about — not a plugin
chain, a **system for manufacturing accidents and never losing the good
ones.**

---

## The honest constraints

- **Novelty is measurable; taste isn't.** The score finds sounds unlike
  your library. Whether one is *good* is yours alone, forever.
- **A signature takes months, not sessions.** The protocol raises your
  candidate throughput by maybe 50x. It doesn't skip the recognition
  reps — those are ear-time and only you can log them.
- **Copies don't become signatures.** Anything derived from someone
  else's preset can be traced back. Depth (resampling) and source
  ownership (your recordings) are what make it untraceable and yours.

---

## Where this sits next to the current track

"Bad and Boujee Edit" is a bootleg built from sample packs, made for fun
and as a gift. It is a *fantastic* vehicle for learning arrangement,
mixing and the tooling — and a terrible vehicle for finding a signature,
because every ingredient is someone else's. Finish it, ship it, enjoy it.

The next track starts with Phase 0.
