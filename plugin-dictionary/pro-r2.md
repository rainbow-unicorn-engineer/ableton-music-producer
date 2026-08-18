# FabFilter Pro-R 2

**What it is (plain English):** the reverb → *reverb is the sound of a
space — the reflections a room adds. Pro-R 2 fakes any space from a
closet to a cathedral, tuned with musical controls instead of physics
jargon.*

**When we reach for it:** vocal space (send, not insert), supersaw and
pad width in melodic sections, snare tails, and the "huge drop into dead
silence" trick (automate the send off right before the drop). For
character/vintage spaces the Abbey Road Waves stuff competes; Pro-R 2 is
the clean modern default.

**Key controls:** Space (one knob that morphs room size *and* matching
decay time — the star), Decay Rate (stretch/shrink the tail), Brightness,
Character (Clean → Chorus for movement), Distance (close-up vs. back of
the hall), Width, Mix (100% on a return track), Predelay (→ *a gap before
the reverb starts, so the dry hit stays punchy*), and the Decay Rate EQ —
*paint the tail's frequency response: pull reverb out of the lows so the
sub stays clean, always.*

**Macro rack:** `AGT ProR2` — Space, Decay Rate, Brightness, Mix,
Predelay, Width.

**Agent access:** macro rack; direct params for the Decay Rate EQ
(`param_dump` → `pro-r2.params.json`).

**Gotchas:** reverb on the sub = instant mud — high-pass every reverb
return around 150–250 Hz (the Decay Rate EQ does it inside the plugin).
On returns keep Mix at 100% and ride the send amount instead, or Mix
automation and send automation will fight.

**Recipes that use it:** (grows with /skills)
