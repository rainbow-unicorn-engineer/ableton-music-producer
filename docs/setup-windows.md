# Windows Setup — one-time install walkthrough

Everything here happens on the machine that runs Ableton Live 12.
Budget ~30 minutes. Check off as you go.

## 1. Prerequisites

- [ ] **Python 3.10+** — `python --version` in a terminal to check.
      Install from python.org if missing (tick "Add python.exe to PATH").
- [ ] **Git** — `git --version`
- [ ] **uv** (fast Python package manager, optional but recommended):
      `pip install uv`
- [ ] **FFmpeg** (audio file swiss-army knife, needed in Phase 2 for the
      library analyst): download from ffmpeg.org, add to PATH
- [ ] **Claude Desktop** installed
- [ ] **Claude Code** installed: `npm install -g @anthropic-ai/claude-code`
- [ ] **Ableton Live 12** installed and opened at least once

## 2. Get this repo onto the machine

```bash
git clone <your-github-remote>/xlnt-studio.git
cd xlnt-studio
pip install -e ableton-mcp/          # or: uv pip install -e ableton-mcp/
```

Verify: `python -c "from mcp.server.fastmcp import FastMCP; print('ok')"`

## 3. Install Producer Pal (the stable core)

Producer Pal is installed, not built — it's the reliable fallback while the
custom server evolves, and its Agent Skill/REST API are reference
implementations to learn from.

- [ ] Download the `.amxd` device + `.mcpb` extension from producer-pal.org
- [ ] Double-click the `.mcpb` → installs into Claude Desktop
- [ ] Drop `Producer_Pal.amxd` on an empty MIDI track named `PP`
- [ ] Save that track into your default template
      (File → Save Live Set as Default)
- [ ] Test in Claude Desktop: *"connect to my Live set and tell me the tempo"*

## 4. Install the Remote Script inside Ableton

→ *A Remote Script is a small Python program Ableton itself runs; ours
opens the TCP/UDP sockets Claude talks to.*

This repo ships two, in `ableton-mcp/remote_script/`:

| Folder | What it is | Ports |
|--------|-----------|-------|
| `AbletonMCP/` | The full control-surface script — every TCP command (tracks, clips, MIDI, devices, browser) | TCP 9877 |
| `AbletonMCP_UDP/` | The hybrid variant — TCP plus the UDP performance plane for real-time parameter streaming | TCP 9877 + UDP 9878 |

⚠️ Both bind TCP 9877, so **enable only one at a time** in Preferences.
Start with `AbletonMCP` (full command set). Switch to `AbletonMCP_UDP` for
UDP streaming sessions, or edit one script's `TCP_PORT` if you want both
live at once. (Unifying them is on the roadmap — see `docs/decisions.md`.)

Install steps:

1. Open File Explorer, paste into the address bar:
   `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts`
   (create the `Remote Scripts` folder if it doesn't exist)
2. Copy the folders `AbletonMCP` and `AbletonMCP_UDP` from
   `xlnt-studio\ableton-mcp\remote_script\` into it.
3. Restart Ableton Live.
4. Preferences (`Ctrl+,`) → **Link, Tempo & MIDI** tab → in an empty
   **Control Surface** slot select **AbletonMCP** → set its **Input** and
   **Output** to **None**.
5. Look for the status-bar message: *"AbletonMCP: Listening for commands
   on port 9877"*.

## 5. Register the server with Claude Desktop

Claude Desktop → Settings → Developer → Edit Config, then merge this into
`claude_desktop_config.json` (a ready-to-edit copy lives at
`docs/claude_desktop_config.sample.json`):

```json
{
  "mcpServers": {
    "XLNT-Ableton": {
      "command": "python",
      "args": ["C:/path/to/xlnt-studio/ableton-mcp/server/server.py"]
    }
  }
}
```

Replace the path with your real clone location (forward slashes are fine).
Restart Claude Desktop and look for the tools/hammer icon.

## 6. Prove it works

Run the checklist in `docs/smoke-tests.md`. The first one:

> "Create a MIDI track named TEST and write a 1-bar C minor chord."

If a track appears in Ableton with a clip on it, the hands are alive.
