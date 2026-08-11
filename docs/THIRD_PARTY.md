# Third-Party Code — what was vendored from whom

→ *"Vendoring" means copying another project's code into this repo (rather
than installing it as a dependency), so we can modify it freely. The rule:
commit the unmodified baseline first, so every local change is diffable
with plain `git log`/`git diff`.*

## uisato/ableton-mcp-extended (MIT)

<https://github.com/uisato/ableton-mcp-extended> — the hybrid TCP/UDP
foundation. Vendored unmodified in commit tagged "vendor: baseline", then
adapted (package renamed `MCP_Server` → `server`, test imports updated).

| Their path | Our path |
|-----------|----------|
| `MCP_Server/` | `ableton-mcp/server/` |
| `AbletonMCP_Remote_Script/__init__.py` | `ableton-mcp/remote_script/AbletonMCP/__init__.py` |
| `Ableton-MCP_hybrid-server/AbletonMCP_UDP/__init__.py` | `ableton-mcp/remote_script/AbletonMCP_UDP/__init__.py` |
| `experimental_tools/xy_mouse_controller/` | `ableton-mcp/udp/examples/xy_mouse_controller/` |
| `tests/` | `ableton-mcp/tests/` |

Not vendored: `elevenlabs_mcp/` (voice generation — out of scope for now),
`skills/ableton-songwriter` (superseded by our own `/skills` cookbook).

License copy: `docs/licenses/uisato-ableton-mcp-extended-LICENSE`.

## jhurliman/ableton-mcp, PR #1 (MIT)

<https://github.com/jhurliman/ableton-mcp/pull/1> — John Hurliman's
December 2025 mashup experiment (fork of ahujasid/ableton-mcp). We
cherry-picked, per the plan, rather than wholesale-copying:

| Their path | Our path | Why |
|-----------|----------|-----|
| `MCP_Server/als_warp_injector.py` | `ableton-mcp/tools/als_warp_injector.py` | warp-marker injection into `.als` files — the diff-detective work is already done |
| `MCP_Server/als_automation_injector.py` | `ableton-mcp/tools/als_automation_injector.py` | tempo/energy automation envelope injection |
| `Max4Live/AudioCapture.amxd` | `ableton-mcp/tools/max4live/AudioCapture.amxd` | the WAV-recorder patch — Phase 4's way of getting audio OUT of Ableton |

Deliberately left behind (grab later if needed): `audio_analysis.py`
(`vocal_to_midi`, structure analysis — waiting until vocals enter the
workflow), his server.py additions (set_eq_bands, sidechain routing,
batch_move_clips — revisit when mashup workflows begin), and the Replicate
endpoints.

License copy: `docs/licenses/jhurliman-ableton-mcp-LICENSE`.

## Not in the repo at all

**Producer Pal** (producer-pal.org) is installed into Claude Desktop /
Ableton directly — see `docs/setup-windows.md` §3.
