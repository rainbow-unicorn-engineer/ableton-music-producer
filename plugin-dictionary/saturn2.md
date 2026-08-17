# FabFilter Saturn 2

**What it is (plain English):** the multiband saturator → *saturation
adds harmonics — the pleasant crunch and warmth of pushed analog gear.
Saturn 2 does it per frequency band, with a modulation system bolted on,
which makes it as much a sound-design tool as a mixing one.*

**When we reach for it:** the #1 bass-music weapon: driving the **mids
only** of a sub/growl so it reads on laptop speakers while the sub stays
clean underneath (the trick behind half of Skrillex/Subtronics bass
tone). Also: warming flat drums (Warm Tape), aggressive vocal grit,
and modulated drive (an LFO on a band's drive = movement for free).

**Key controls:** per band — Drive (how hard), Style (Tape/Tube/Amp/
Smudge/Destroy → *from gentle warmth to total destruction*), Mix
(parallel per band), Tone controls; global Feedback (adds growl of its
own), and the drag-anywhere modulation system (XLFOs, envelopes) — *any
knob can wobble.*

**Macro rack:** `AGT Saturn2` — Drive, Mix, Tone (per the plan). Worth
adding: Feedback, Band 2 Drive.

**Agent access:** macro rack for rides; direct params for band setup and
modulation (`param_dump` → `saturn2.params.json`).

**Gotchas:** saturating the sub band directly makes it boomy and eats
headroom — split around ~120 Hz and drive the top band only. Level rises
with drive; use per-band Mix/Level to compare fairly. HQ mode
(oversampling) matters here more than most plugins — aliasing on heavy
drive sounds cheap.

**Recipes that use it:** (grows with /skills)
