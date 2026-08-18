# What We Built — The Plain-English Guide

*XLNT Studio, explained without jargon. Read this when you forget what a
piece does, or show it to anyone who asks what you've been building.*

## The one-sentence version

You now have an AI producer's assistant that can **control your Ableton
Live** (create tracks, write melodies, turn knobs), **remembers every
sound you own** (45,000 samples, searchable by describing what you want),
**knows your plugins** (what each knob does), and **can "hear" your
mixes** (by turning sound into pictures and numbers it can read).

## The four pieces, by body part

### 🖐 The Hands — `ableton-mcp/`

A translator that sits between Claude and Ableton. When you type "make a
MIDI track and write a C minor chord," this turns the sentence into
clicks Ableton understands. It has two lanes:

- a **careful lane** for things that must happen exactly once — creating
  tracks, writing notes, loading instruments. Like certified mail.
- a **fast lane** for streaming knob movements while music plays — 60
  updates a second, where a lost message just means one missed knob
  position nobody can hear. Like a firehose.

It also includes tools that operate on Ableton project files directly
while Ableton is closed (adding tempo changes and timing markers), and
`param_dump`, which asks any plugin "list every knob you have" so the
agent can turn them by name.

### 🧠 The Memory — `library-analyst/`

A catalog of your entire sample collection. It listened to ~45,000 files
once and wrote down, for each: how long it is, its musical key, its tempo,
how *dark or bright* it sounds, how *punchy or soft*, and how *loud*. All
of that lives in a little database, so asking **"find me a dark punchy
bass one-shot near F minor"** returns ranked answers in under a second —
and the Hands can then load the winner straight into your session.

It also wrote you a report of what your library contains (spoiler: you
are extremely well armed for bass music and own exactly one pad).

### 📖 The Knowledge — `plugin-dictionary/`

One page per plugin, in human words: what it is, when you reach for it,
what its knobs do, and its quirks. Next to each page sits the raw list of
its knobs that `param_dump` generated. Serum, KNOCK, and ShaperBox are
in; the rule is to add a page the day you first reach for a new plugin,
never all at once.

### 👂 The Ears — `ears/`

Claude can't hear. But it can read pictures and numbers made *from*
sound. After you bounce a mix (save it as one audio file), one command
produces:

- a **spectrogram** — a photo of your sound: time runs left to right,
  bass at the bottom, treble at the top, brightness = energy. Mud, harsh
  spots, and weak sub are visible at a glance.
- a **loudness report** — the same measurements Spotify and record labels
  use: overall loudness (LUFS), true peak (does it clip?), dynamics, and
  how the energy splits between sub / bass / mids / highs.

Drop both into a chat (or let the agent fetch them itself) and you get
mix feedback grounded in measurements, not vibes.

### 🔬 The Study Desk — the reverse-engineering pipeline (in `ears/`)

The newest piece: point it at a track you wish you'd made, and it turns
the record into numbers and pictures you can chase.

- a **reference card** — one file that captures a track's measurable DNA:
  its loudness, its frequency balance, its key and tempo, and its
  **arrangement skeleton** (intro 16 bars → build 16 → drop 32...).
  Made once, kept forever in `references/`.
- **compare_mix** — your bounce vs. any card, as a checklist: "you're 3
  loudness units quieter, your sub is 4 dB light, their drop is 32 bars
  and yours is 16." Fix the top gap, bounce, compare again.
- **stem separation** — an AI model pulls a finished track apart into
  vocals, drums, bass, and everything-else, and each piece goes through
  the Ears separately: how *their* drum bus is balanced, what *their*
  bass does under the vocal.
- **MIDI extraction** — pulls the actual notes out of audio into a clip
  you can drop onto an Ableton track and study.

What it honestly can't do: recover their synth patches or plugin chains.
That part stays craft — but now it's craft aimed by measurements.

## How the pieces work together

> **You:** "Find a dark bass one-shot near F minor and load it under my
> chords, then set the sub duck to 40%."
>
> The **Memory** finds the sample → the **Hands** load it and turn the
> knob (which the **Knowledge** knows by name) → later, the **Ears** tell
> you whether the low end actually works.

## What this is for (and not for)

The system automates the mechanical 70% of producing: setup, sound-
hunting, MIDI drafts, gain staging, measurement. The sacred 30% stays
yours: what the track says, how it feels, when it's done. The tools serve
the tracks — never the reverse.

## Where things live

| Folder | Piece |
|--------|-------|
| `ableton-mcp/` | the Hands (+ project-file tools, `param_dump`) |
| `library-analyst/` | the Memory (scanner, analyzer, search) |
| `plugin-dictionary/` | the Knowledge (one page per plugin) |
| `ears/` | the Ears (`analyze_bounce`) |
| `skills/` | Phase 5: recipes per style — grows with every track |
| `docs/` | guides, decisions, reports (including this file) |

Everything was built test-first: **176 automated checks** run in seconds
(`pytest`) and prove each piece still works after any change.
