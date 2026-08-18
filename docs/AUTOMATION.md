# Automation — making the track move

*Built 2026-08-18. The gap this closes: the Arrangement Doctor kept
reporting "zero automation in the project", and every 8 bars was a
photocopy of the last 8. That is most of what "sounds plain" means.*

→ **Automation** = a knob that moves on its own over time. A filter
opening across a build, a pad swelling into a drop, a bass ducking out
for one bar. Records move constantly; demos don't.

---

## The four tools

### `list_automatable_parameters(track_index, filter="")`

Every knob on a track that automation can move, with the exact numeric
range each accepts. **Run this first** — parameter names are exact
strings and ranges differ per plugin, so guessing wastes a round trip.

    list_automatable_parameters(track_index=18, filter="freq")

### `filter_sweep(track_index, start_bar, end_bar, from_hz, to_hz, ...)`

→ A **filter sweep** is the sound of something being progressively
muffled or un-muffled. Opening one across a build is the most common
tension device in dance music; closing one is how a section gets pulled
away.

Frequencies go in as Hz and are converted to Live's internal 0–1
logarithmic scale (100 Hz = 0.30, 1 kHz = 0.60, 10 kHz = 0.90).

    filter_sweep(track_index=18, start_bar=54, end_bar=62,
                 from_hz=200, to_hz=12000, shape="exp")

`shape="exp"` holds the filter low and opens late — that is the classic
build shape, because the ear reads the *acceleration*, not the average.

### `volume_ride(track_index, start_bar, end_bar, from_level, to_level, ...)`

→ A **volume ride** is a hand-drawn fade. On Live's fader **0.85 = 0 dB
(unity)**; 0.0 is silence.

    volume_ride(track_index=32, start_bar=46, end_bar=50,
                from_level=0.0, to_level=0.75, shape="s")

`shape="s"` eases both ends, which sounds like a hand on a fader rather
than a straight line.

### `write_automation(...)` — anything else

Any parameter, any curve. `value_mode="normalized"` lets you work in
0–1 when a plugin's own units are opaque.

    write_automation(track_index=56, parameter_name="Dry/Wet",
                     start_bar=62, end_bar=70,
                     from_value=0.4, to_value=0.9,
                     shape="sine", cycles=4)

---

## The shapes, and when each one is right

| shape | motion | use it for |
|---|---|---|
| `linear` | steady | short 1-bar moves where curve doesn't register |
| `exp` | slow, then rushing | **builds** — tension comes from acceleration |
| `log` | fast, then easing | **drops** — the release should land immediately |
| `s` | eased both ends | fades that should sound human |
| `sine` | smooth oscillation | wobbles, tremolo, movement inside a drop |
| `triangle` | angular oscillation | rhythmic, more obvious than sine |

`curve` sets how dramatic `exp`/`log` are (2 = gentle, 5 = extreme).
`cycles` sets how many times `sine`/`triangle` swing.

---

## How it works underneath (and the one gotcha)

Arrangement automation lives **inside a clip**. So there must be a clip
on that track covering `start_bar` — the tools find the right one
automatically and say so plainly if there isn't one.

Curves are written as breakpoints `resolution` beats apart (default
0.25 = 16th notes). Finer is smoother and slower to write; 0.25 is
inaudibly smooth for sweeps and fades.

Bars are 1-based and fractions are allowed: `start_bar=54.5` is halfway
through bar 54.

---

## The standing rule from PRODUCTION-STANDARD.md

> Nothing static for more than 8 bars. Ever.
> At least 3 automated parameters running at all times.

That rule was unenforceable before these tools existed. It isn't now.
