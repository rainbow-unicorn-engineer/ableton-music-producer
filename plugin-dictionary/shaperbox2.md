# ShaperBox 2 (Cableguys)

**What it is (plain English):** a multi-effect that moves a control up and
down over time in sync with your song — most importantly here, a *volume
shaper*: it rhythmically dips the level of a track. → *This fakes
"sidechain ducking": the pumping effect where the bass gets quiet each time
the kick hits, so the kick punches through.*

**When we reach for it:** it lives in the XLNT Starter template on the
**SUB**, **MID SYNTHS**, and **FX** group buses (preset: `BA Sidechain`),
ducking those buses every 1/4 note in Beat mode with a 1-shot MIDI trigger.
Reach for it any time a sustained sound needs to breathe around the kick.

**Key controls:** (name → what it does, in human words)

- **Volume (depth), template setting 60%** → how hard the duck bites: 0% =
  no dip, 100% = fully silent at the bottom of the dip
- **Mix** → blend of processed vs. untouched signal for the Volume band
- **Master Mix** → same blend but for the whole plugin at once
- **Trim** → static volume offset; set once by hand, not something to ride
- **LFO Smooth** → rounds off the duck curve so the pumping sounds less
  abrupt
- **Sidechain input** (dropdown on the Live device, currently "No Input")
  → the template's duck is *timed* (every 1/4 note), not *triggered by the
  actual kick*. Route the kick bus in here to make it react to real drums.

**Macro rack:** none yet — planned as `AGT ShaperBox2` (map Volume depth,
Mix, LFO Smooth, Master Mix to named macro knobs; see Phase 3.2 in the
project plan)

**Agent access:** direct params (see `shaperbox2.params.json`) — currently
exposed:

| index | name | meaning |
|-------|------|---------|
| 0 | Device On | on/off switch |
| 1 | Volume Gain Mid | the duck depth for the Mid band (the 60% slider) |

**Gotchas:**

- ShaperBox publishes **nothing** to Ableton by default — every control
  must be exposed via Configure mode (wrench icon on the Live device, then
  click-hold-drag the control in the plugin window). Quick flicks don't
  register; drag slowly.
- Parameter names are per-band: the Volume slider registers as "Volume
  Gain **Mid**" because the template uses a single Mid band. Adding bands
  will add separate parameters.
- Values in the params JSON are normalized 0–1, and the plugin's percent
  display doesn't map 1:1 (60% on the slider read back as 0.50) — trust
  the plugin UI for musical values, the JSON for automation.
- Mix / Master Mix registration was still pending as of 2026-08-11 — if
  they refuse to appear in Configure mode, they're host-invisible and the
  AGT macro rack is the workaround.

**Recipes that use it:** (links into /skills — none yet)
