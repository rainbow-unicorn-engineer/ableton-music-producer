# Little AlterBoy (Soundtoys)

**What it is (plain English):** the voice changer → *it shifts a vocal's
pitch (how high the notes are) and formant (the size-of-the-throat
character) independently — so you can make a voice deeper without making
it slower or chipmunky, or vice versa.*

**When we reach for it:** the modern bass-music vocal toolkit: pitched-
down "demon" ad-libs (Suicideboys territory), formant-up hook doubles,
robotic hard-tune (Quantize mode), talkbox-ish octave layers under a
lead, and turning one vocal take into a fake crowd of different voices.

**Key controls:** Pitch (semitone shift — snap to ±12 for octaves),
Formant (character shift, independent of pitch — *the magic knob*),
Drive (Soundtoys tube grit on the way out), Mix, and the mode switch:
Transpose (smooth shift), Quantize (hard-tune to a scale → *the T-Pain
setting*), Robot (locks everything to one monotone pitch).

**Macro rack:** `AGT AlterBoy` — Pitch, Formant, Drive, Mix (per the
plan).

**Agent access:** macro rack; direct params via `param_dump` →
`little-alterboy.params.json`.

**Gotchas:** it's monophonic — feed it one voice; chords in = garbage
out (stack instances on separate takes instead). Extreme formant moves
get metallic fast: ±3 semitones of formant reads as character, ±7 reads
as effect. In Robot/Quantize mode the *input* performance's pitch
stability barely matters, so save perfect takes for Transpose mode.

**Recipes that use it:** (grows with /skills)
