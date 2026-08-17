# Serum 2 (Xfer Records)

**What it is (plain English):** the wavetable synthesizer → *a wavetable
is a flipbook of tiny waveforms; the synth plays one page and can sweep
through the book while a note holds, which is why one Serum note can
morph from smooth to snarling. Serum 2 is the genre-defining bass-music
synth — most growls, screeches, and modern leads you love were born
here.*

**When we reach for it:** every original synth sound — mid basses and
growls first (your genres live there), plus leads, plucks, keys, pads.
If the sound doesn't exist in your 45k samples, Serum is where we make
it exist.

**Key controls (the 20% that makes 80% of sounds):**
- **OSC A/B → WT Position:** which page of the flipbook. THE knob —
  automate or LFO it and a static tone becomes a living one.
- **Warp:** bends the waveform itself (FM, Bend, Sync, Formant...) →
  *the sound-mangler; FM-from-B is the doorway to growl territory.*
- **Unison + Detune:** stacks copies slightly out of tune → *one voice
  becomes a crowd; supersaw leads = high unison, basses = low or none
  (keep the low end mono).*
- **Filter + Drive:** darkens/shapes the tone; drive adds grit inside
  the synth. Notch/formant filter types + movement = talky basses.
- **Env 2/3 & LFOs:** drag any of them onto any knob → *automatic knob
  movement; LFO on WT position or filter cutoff is where "wub" lives.*
- **FX rack:** Serum's own chain (Hyper/Dimension, Distortion, EQ...) —
  order matters, experiment.
- **Macros 1–4:** four master knobs you wire to anything — map these to
  the AGT rack so the agent can ride your patch.

**Macro rack:** `AGT Serum2` — Cutoff, Resonance, Wave Position, Unison
Detune, Drive, LFO Rate, FX Mix, Space (per the plan).

**Agent access:** macro rack for rides; direct params via
`serum2.params.json` (seeded). During sound-design sessions the agent
sets parameters by name while you judge by ear.

**Gotchas:** CPU-hungry — freeze tracks you're done with. Keep unison
OFF below ~150 Hz or the sub smears (split sub and mid bass onto
separate tracks — the house style anyway). The preset browser is a
teacher: find a sound you love, then work out WHY it works knob by knob
— that's a sound-design lesson per preset, free.

**Recipes that use it:** (every growl recipe to come — see /skills)
