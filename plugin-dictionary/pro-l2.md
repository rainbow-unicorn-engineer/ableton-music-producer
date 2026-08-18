# FabFilter Pro-L 2

**What it is (plain English):** the final limiter → *a limiter is a brick
wall for volume: nothing gets past the ceiling, and everything under it
gets turned up toward it. It's the last device before your track meets
the world, and it's where "make it loud" happens.*

**When we reach for it:** the master chain, always last (or KClip3 into
Pro-L 2 — clipper shaves the peaks, limiter catches the rest). Also on
the drum bus for aggressive styles.

**Key controls:** Gain (how hard you push into the ceiling — this is the
loudness knob), Output/Ceiling (set to **-1.0 dBTP** so lossy encoders
don't clip — the ears' true-peak check exists exactly for this), Style
(Transparent/Punchy for our genres; Aggressive for tearout), Attack &
Release (shorter = louder but crunchier), Channel Link (unlink transients
a touch for wider drops), and **True Peak Limiting: ON**.

**Macro rack:** none — per the plan, limiter gain works better as a
direct parameter call while watching the meters.

**Agent access:** direct params (run `param_dump` → `pro-l2.params.json`).
The loop: agent pushes Gain, you bounce, `analyze_bounce` reports LUFS +
true peak, agent adjusts. Loudness by measurement, not by ear-fatigue.

**Gotchas:** its loudness metering is the same BS.1770 standard the ears
use — they should agree within a hair; if they don't, something upstream
is clipping. More than ~6 dB of gain reduction stops being "loud" and
starts being "small": back off and fix the mix balance instead (that's
what `compare_mix` gaps are for).

**Recipes that use it:** (grows with /skills)
