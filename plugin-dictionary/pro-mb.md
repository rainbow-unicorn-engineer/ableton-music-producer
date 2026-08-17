# FabFilter Pro-MB

**What it is (plain English):** the multiband compressor → *a compressor
that treats up to six frequency ranges separately — clamp the boomy lows
without touching the crisp highs, or vice versa. Think of it as six
Pro-Cs, each guarding its own lane.*

**When we reach for it:** controlling a wild bass patch whose sub and
mids fight each other (classic with Serum growls), de-boxing a muddy
drum bus, taming only the harsh 2–5 kHz of a lead when it screams,
dynamic low-end control on the master, and "OTT-style" upward+downward
squash (Pro-MB does it cleaner than the freebie).

**Key controls:** per band — Threshold, Ratio, Attack, Release, Range
(the maximum dB it's allowed to move → *a safety leash most compressors
don't have*), and Level. Expert mode adds per-band sidechain. Bands only
process where you create them — untouched frequencies pass through
unprocessed, which is the whole point.

**Macro rack:** `AGT ProMB` — Band 1 Threshold, Band 1 Range, Band 2
Threshold, Band 2 Range, Global Dry/Wet. (Two bands covers the usual
sub-vs-mids fight; go direct for more.)

**Agent access:** macro rack for the common moves; direct params for
full setups (`param_dump` → `pro-mb.params.json`).

**Gotchas:** every crossover you add slightly smears the sound — use the
fewest bands that solve the problem, and Dynamic Phase mode (default)
unless mastering. If you're reaching for 4+ bands on one sound, the sound
design probably needs fixing at the source instead.

**Recipes that use it:** (grows with /skills)
