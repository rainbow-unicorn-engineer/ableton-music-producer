#!/usr/bin/env python3
"""analyze_bounce.py — the whole feedback loop in one command.

Bounce audio out of Ableton (the AudioCapture.amxd patch on the master
track, or File → Export), then:

    python analyze_bounce.py --file "C:/bounces/mix_v3.wav"

You get: the loudness report (LUFS, true peak, loudness range, band
balance) printed AND saved as `<name>.ears.json`, plus the spectrogram
PNG next to it. Drop both into a Claude chat — or let the agent fetch
them itself via the XLNT-Library `analyze_bounce` tool — and the mix
critique can begin.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loudness  # noqa: E402
import spectrogram  # noqa: E402


def analyze(path, out_dir=None):
    path = Path(path)
    out_dir = Path(out_dir) if out_dir else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = loudness.measure(path)
    metrics["summary"] = loudness.summarize(metrics)
    png = spectrogram.render(path, out_dir / (path.stem + ".spectrogram.png"))
    metrics["spectrogram_png"] = str(png)
    report = out_dir / (path.stem + ".ears.json")
    report.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics["report_json"] = str(report)
    return metrics


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--out-dir", default=None,
                    help="where the PNG + JSON land (default: next to the file)")
    args = ap.parse_args(argv)
    m = analyze(args.file, args.out_dir)
    print(json.dumps({k: v for k, v in m.items() if k != "summary"}, indent=2))
    print()
    print(m["summary"])
    print(f"\nSpectrogram: {m['spectrogram_png']}\nReport: {m['report_json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
