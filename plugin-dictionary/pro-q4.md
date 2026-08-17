# FabFilter Pro-Q 4

**What it is (plain English):** the scalpel EQ → *an equalizer turns
frequency ranges up or down; Pro-Q 4 is the surgical one — up to 24 bands,
each placeable anywhere, with a real-time analyzer so you see the sound
you're cutting.*

**When we reach for it:** every mix task that starts with "there's too
much/too little of X": cutting mud (250–500 Hz), taming harshness
(3–4 kHz), high-passing everything that isn't bass, notching resonances,
carving space so the sub and the kick don't fight (dynamic bands +
sidechain), and the classic dubstep move — matching a bass's EQ curve to
sit against the drums.

**Key controls:** each band has Frequency (where), Gain (how much up/down),
Q (how narrow → *high Q = a needle, low Q = a broad brush*), and Shape
(bell, shelf, cut...). Dynamic mode makes a band duck only when energy
appears there → *an EQ cut that happens only when needed.* Spectrum Grab:
click the analyzer's peaks to create bands right on resonances.

**Macro rack:** none — per the plan, precision EQ moves work better as
direct parameter calls than as 8 fixed knobs.

**Agent access:** direct params (run `param_dump` on it first time it's
loaded → save as `pro-q4.params.json` next to this page).

**Gotchas:** the agent sees bands as numbered parameter slots — tell it
which band you mean by frequency ("the 300 Hz cut"), not by color.
Natural Phase mode sounds best but costs CPU; Linear Phase adds latency —
leave Zero Latency on while producing, decide at mixdown.

**Recipes that use it:** (grows with /skills)
