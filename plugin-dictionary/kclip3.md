# KClip3 (Kazrog)

**What it is (plain English):** the clipper → *clipping shaves the very
tops off peaks instead of turning them down like a limiter. Done right,
you lose nothing you can hear and gain loudness — it's how bass music
gets so loud without pumping.* You also have KClip Zero (the free
one-knob version) — same idea, fewer controls.

**When we reach for it:** the master chain (KClip3 shaving peaks →
Pro-L 2 catching what's left — the standard loud-genre stack), the drum
bus (clip the kick's peak so the limiter never sees it), and individual
drops that need density.

**Key controls:** Input Drive (how hard you push into the ceiling — the
loudness knob), Clip Shape (Hard = maximum loud, softer shapes = warmer),
Saturation types for added color, Output Trim, Mix, and oversampling
(keep at 4x+ on the master → *stops digital aliasing artifacts*). The
difference meter lets you hear only what's being removed — *the honesty
button.*

**Macro rack:** `AGT KClip` — Input Drive, Output Trim, Mix (per the
plan).

**Agent access:** macro rack; direct params via `param_dump` →
`kclip3.params.json`.

**Gotchas:** clip *peaks*, not *body* — if the difference meter plays
recognizable music instead of ticks, you've gone too far. Order matters:
clipper **before** limiter. And `analyze_bounce`'s true-peak number is
the referee: post-chain bounces should still land under -1.0 dBTP.

**Recipes that use it:** (grows with /skills)
