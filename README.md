# XLNT Studio

**Goal:** the best Ableton AI integration in existence — hybrid TCP/UDP
control, a library analyst that knows every sound you own, a plugin
dictionary the agent can act on, and an audio feedback pipeline that gives
the AI ears.

→ *MCP (Model Context Protocol) is the plug standard that lets Claude call
outside tools — here, tools that drive Ableton Live.*

## Architecture

```
┌─────────────────────────────────────────────────┐
│              YOU + CLAUDE (the brain)           │
│           Claude Desktop / Claude Code          │
└───────┬──────────┬──────────┬──────────┬────────┘
        │          │          │          │
   ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼──────┐
   │Producer │ │ Custom │ │ Library │ │  Audio  │
   │   Pal   │ │  MCP   │ │ Analyst │ │  Ears   │
   │(stable  │ │(TCP+UDP│ │ (your   │ │(spectro-│
   │  core)  │ │ hybrid)│ │ sounds) │ │ grams)  │
   └────┬────┘ └───┬────┘ └─────────┘ └─────────┘
        │          │
   ┌────▼──────────▼────┐
   │  ABLETON LIVE 12   │
   └────────────────────┘
```

Five components. Producer Pal is installed, not built. The other four live
in this repo.

## Status

| Phase | Component | State |
|-------|-----------|-------|
| 0 | Repo, docs, conventions | ✅ done |
| 1 | `ableton-mcp/` — hybrid TCP/UDP server + Remote Script + als injectors + `param_dump` | ✅ built, awaiting on-machine smoke tests |
| 2 | `library-analyst/` | ⬜ next |
| 3 | `plugin-dictionary/` + AGT macro racks | 🌱 template seeded, grows with use |
| 4 | `ears/` | ⬜ (the `AudioCapture.amxd` recorder patch is already vendored in `ableton-mcp/tools/max4live/`) |
| 5 | `skills/` style cookbook | ⬜ forever ongoing |

## How to run each piece

**The MCP server** (the "hands" — Claude's control over Ableton):

1. Follow `docs/setup-windows.md` once (installs the Remote Script inside
   Ableton and registers the server with Claude Desktop).
2. After that it starts automatically whenever Claude Desktop launches.

**The custom tools** (standalone, run from a terminal):

```bash
# Dump every parameter of a plugin to JSON (Ableton must be open)
python ableton-mcp/tools/param_dump.py --track 0 --device 0 --name serum2

# Inject tempo automation / warp markers into a .als file (Ableton CLOSED)
python ableton-mcp/tools/als_automation_injector.py --help
python ableton-mcp/tools/als_warp_injector.py --help

# UDP smoke test: stream a sine sweep to a mapped macro while a loop plays
python ableton-mcp/udp/sweep_smoke_test.py --track 0 --device 0 --param 1
```

**Tests** (run anywhere, no Ableton needed):

```bash
pip install pytest
pytest ableton-mcp/tests/
```

## Docs

- `docs/setup-windows.md` — the one-time install walkthrough (start here)
- `docs/smoke-tests.md` — the checklist that proves each layer works
- `docs/decisions.md` — why things are the way they are
- `docs/THIRD_PARTY.md` — what was vendored from whom, and the licenses

## Credits

Built on the shoulders of
[uisato/ableton-mcp-extended](https://github.com/uisato/ableton-mcp-extended)
(hybrid TCP/UDP server, MIT) and
[jhurliman/ableton-mcp](https://github.com/jhurliman/ableton-mcp) (als
injection tools + AudioCapture patch, MIT), which itself forks
[ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp). See
`docs/THIRD_PARTY.md`.
