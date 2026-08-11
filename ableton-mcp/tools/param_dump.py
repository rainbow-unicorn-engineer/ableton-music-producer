#!/usr/bin/env python3
"""param_dump — dump a device's full parameter map to JSON.

Every plugin exposes its knobs to Ableton as a numbered list (parameter 0,
1, 2...) but the numbers are meaningless without names. This tool talks to
the AbletonMCP Remote Script over TCP → *the reliable "control plane"
connection on port 9877* — and dumps the full name↔number map, so
"set Serum's filter cutoff to 40%" becomes a real, executable command.

Output format (one object per parameter):

    {"index": 3, "name": "Filter Cutoff", "min": 0.0, "max": 1.0,
     "current_value": 0.4}

`current_value` is normalized 0.0–1.0 → *0% to 100% of the knob's travel,
regardless of what units the plugin displays.* The raw display string is
kept in `display_value` so humans can sanity-check.

Usage (Ableton must be OPEN with the AbletonMCP control surface enabled):

    # Dump device 0 on track 0, save to the plugin dictionary
    python param_dump.py --track 0 --device 0 --name serum2

    # Just print to the terminal
    python param_dump.py --track 0 --device 0

    # Rack chains: dump the first device inside chain 2
    python param_dump.py --track 0 --device 0 --chain 2 --name sub-layer
"""

import argparse
import json
import socket
import sys
from pathlib import Path

HOST = "localhost"
TCP_PORT = 9877  # the Remote Script's control-plane port
RECV_TIMEOUT = 10.0

# plugin-dictionary/ lives two levels up from this file (repo root)
DEFAULT_OUT_DIR = Path(__file__).resolve().parents[2] / "plugin-dictionary"


def send_command(command_type, params=None, host=HOST, port=TCP_PORT):
    """Send one JSON command to the Remote Script and return its result.

    The wire protocol is a single JSON object each way:
      request:  {"type": <command>, "params": {...}}
      response: {"status": "success", "result": {...}}
                or {"status": "error", "message": "..."}
    """
    payload = json.dumps({"type": command_type, "params": params or {}})
    with socket.create_connection((host, port), timeout=RECV_TIMEOUT) as sock:
        sock.sendall(payload.encode("utf-8"))
        sock.settimeout(RECV_TIMEOUT)
        chunks = []
        response = None
        while response is None:
            try:
                chunk = sock.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
            # The script sends one JSON object; stop as soon as it parses.
            try:
                response = json.loads(b"".join(chunks).decode("utf-8"))
            except json.JSONDecodeError:
                continue  # partial packet — keep reading
    if response is None:
        raise ConnectionError("No response from Ableton (is Live open with "
                              "the AbletonMCP control surface enabled?)")
    if response.get("status") == "error":
        raise RuntimeError("Ableton error: " + response.get("message", "unknown"))
    return response.get("result", response)


def format_dump(result):
    """Convert a get_device_parameters result into the dictionary format."""
    params = []
    for p in result.get("parameters", []):
        params.append({
            "index": p["index"],
            "name": p["name"],
            "min": p["min"],
            "max": p["max"],
            "current_value": p["value"],       # normalized 0.0–1.0
            "display_value": p.get("display_value", ""),
            "is_quantized": p.get("is_quantized", False),
            "value_items": p.get("value_items", []),
        })
    return {
        "device_name": result.get("device_name", ""),
        "device_class": result.get("device_class", ""),
        "parameter_count": result.get("parameter_count", len(params)),
        "parameters": params,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--track", type=int, required=True, help="track index (0-based)")
    ap.add_argument("--device", type=int, required=True, help="device index on that track (0-based)")
    ap.add_argument("--chain", type=int, default=None, help="optional rack chain index")
    ap.add_argument("--name", default=None,
                    help="save as plugin-dictionary/<name>.params.json (omit to print only)")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                    help="where .params.json files land (default: plugin-dictionary/)")
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=TCP_PORT)
    args = ap.parse_args(argv)

    req = {"track_index": args.track, "device_index": args.device, "show_all": True}
    if args.chain is not None:
        req["chain_index"] = args.chain

    result = send_command("get_device_parameters", req,
                          host=args.host, port=args.port)
    dump = format_dump(result)

    text = json.dumps(dump, indent=2)
    if args.name:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out_path = args.out_dir / f"{args.name}.params.json"
        out_path.write_text(text, encoding="utf-8")
        print(f"{dump['device_name']}: {dump['parameter_count']} parameters -> {out_path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
