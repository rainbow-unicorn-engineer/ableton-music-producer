#!/usr/bin/env python3
"""UDP smoke test — stream a sine-shaped sweep to a device parameter.

This proves the performance plane works: → *UDP is the fast, lossy channel
(port 9878) used for continuous knob movement while music plays; a dropped
packet is one missed knob position out of ~60/sec and is inaudible.*

Run it while a loop is playing in Ableton and WATCH THE KNOB GLIDE:

    python sweep_smoke_test.py --track 0 --device 0 --param 1

Map `--param` to something audible (filter cutoff on a synth, or a macro
knob on a rack) for maximum satisfaction.
"""

import argparse
import json
import math
import socket
import sys
import time

HOST = "localhost"
UDP_PORT = 9878  # the Remote Script's performance-plane port


def sweep_values(duration_s, rate_hz, cycles):
    """Yield (t, value) pairs tracing `cycles` full sine waves over the
    duration, sampled `rate_hz` times per second. Values are 0.0–1.0."""
    n_steps = max(1, int(duration_s * rate_hz))
    for i in range(n_steps + 1):
        t = i / rate_hz
        phase = (i / n_steps) * cycles * 2 * math.pi
        value = 0.5 + 0.5 * math.sin(phase - math.pi / 2)  # start at 0.0
        yield t, round(value, 4)


def make_packet(track, device, param, value):
    """Build one UDP datagram in the Remote Script's JSON format."""
    return json.dumps({
        "type": "set_device_parameter",
        "params": {
            "track_index": track,
            "device_index": device,
            "parameter_index": param,
            "value": value,
        },
    }).encode("utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--track", type=int, default=0)
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--param", type=int, default=1, help="parameter index to sweep")
    ap.add_argument("--duration", type=float, default=8.0, help="seconds")
    ap.add_argument("--rate", type=float, default=60.0, help="updates per second")
    ap.add_argument("--cycles", type=float, default=2.0, help="full up-down sweeps")
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=UDP_PORT)
    args = ap.parse_args(argv)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Sweeping track {args.track} / device {args.device} / "
          f"param {args.param} for {args.duration}s at {args.rate}/sec — "
          "watch the knob in Ableton.")
    start = time.monotonic()
    sent = 0
    for t, value in sweep_values(args.duration, args.rate, args.cycles):
        # pace the stream in real time
        lag = start + t - time.monotonic()
        if lag > 0:
            time.sleep(lag)
        sock.sendto(make_packet(args.track, args.device, args.param, value),
                    (args.host, args.port))
        sent += 1
    print(f"Done — {sent} packets sent. If the knob glided smoothly, "
          "the UDP performance plane is alive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
