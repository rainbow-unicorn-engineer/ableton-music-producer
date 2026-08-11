# CLAUDE.md — read me first

This repo controls **Ableton Live 12 on Windows**. It is a music production
copilot system, not a normal software project.

## The jargon rule (non-negotiable)

Explain all audio jargon in plain English. Never assume producer vocabulary.
The first time a technical term appears in any doc, code comment, or chat
reply, add a plain-English translation marked with →.

## Repo map

| Folder | What lives there | Status |
|--------|-----------------|--------|
| `ableton-mcp/` | The custom hybrid MCP server: TCP control plane + UDP performance plane, the Remote Script that lives inside Ableton, and custom tools (`als` injectors, `param_dump`) | **Phase 1 — built** |
| `library-analyst/` | Sound library scanner + analysis + SQLite + MCP server (`find_sounds`, `similar_to`, `analyze_file`, `library_stats`) | **Phase 2 — built** |
| `plugin-dictionary/` | One markdown page per plugin + `.params.json` dumps from `param_dump` | Seeded (template only) |
| `ears/` | Audio feedback pipeline: spectrograms + LUFS | Phase 4 — not started |
| `skills/` | Style cookbook — production recipes | Phase 5 — not started |
| `docs/` | Setup guides, smoke tests, decisions, third-party attribution | Living |

## Conventions

- Commit style: `tool: als tempo injection working`, `docs: ...`, `vendor: ...`
- Vendor code (uisato's `ableton-mcp-extended`, Hurliman's tools) was committed
  as an unmodified baseline first, so every local change is diffable. See
  `docs/THIRD_PARTY.md` before rewriting vendored files.
- TCP (port 9877) is the control plane → *commands that must arrive exactly
  once, in order: create tracks, write MIDI, load devices.*
- UDP (port 9878) is the performance plane → *fast, lossy streams for
  continuous knob movement; a dropped packet is inaudible.*
- Never commit `.wav`, `.als`, or the analyst database — the `.gitignore`
  enforces this.
- Test on the machine that runs Ableton. Unit tests (`ableton-mcp/tests/`)
  run anywhere; anything marked `integration` needs Live open.

## The rule that keeps this honest

The agent automates the mechanical 70% (setup, sound-finding, MIDI drafts,
gain staging). The human owns the sacred 30% (what it says, how it feels,
when it's done).
