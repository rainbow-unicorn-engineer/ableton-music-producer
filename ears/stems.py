#!/usr/bin/env python3
"""stems.py — split a finished track into its instruments.

→ *Stem separation: an AI model (Demucs, from Meta) listens to a mixed
track and pulls it apart into four stems — vocals, drums, bass, and
"other" (synths, guitars, everything else). Not perfect, but good enough
to study how a reference's drum bus is balanced or what its bass really
does under the vocal.*

Then each stem goes through the ears separately (`analyze_stems`):
per-stem loudness, band balance, and spectrograms.

Heavy dependency, guarded: Demucs is installed on the studio machine
(`pip install demucs`) and downloads its model (~1 GB) on first run.
This module works without it — it just tells you what to install.

Usage:
    python stems.py --file "C:/refs/weekend_griz_flip.wav"
    python stems.py --file ref.wav --two-stems vocals   # vocals vs rest
    python stems.py --file ref.wav --analyze            # + ears per stem
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_MODEL = "htdemucs"
STEM_NAMES = ("vocals", "drums", "bass", "other")

# Demucs wants Python 3.11, which may not be the Python running this
# repo (3.12 breaks its build tooling). Point this env var at the
# python.exe of whatever environment has Demucs installed, e.g.:
#   setx XLNT_DEMUCS "C:\Users\you\anaconda3\envs\xlnt-audio\python.exe"
DEMUCS_ENV_VAR = "XLNT_DEMUCS"

INSTALL_HINT = (
    "Demucs isn't installed (or isn't visible from this Python). On the "
    "studio machine: Demucs wants Python 3.11 — make a dedicated env "
    "(`conda create -n xlnt-audio python=3.11`, activate it, then "
    "`pip install demucs`; first separation downloads the ~1 GB model). "
    "If that env isn't the one running this code, set the XLNT_DEMUCS "
    "environment variable to that env's python.exe so the ears can "
    "find it."
)


def demucs_python():
    """The interpreter to run Demucs with, in order: the XLNT_DEMUCS env
    var (another environment's python.exe), else this interpreter if
    Demucs is importable here, else None."""
    exe = os.environ.get(DEMUCS_ENV_VAR)
    if exe:
        return exe
    if importlib.util.find_spec("demucs") is not None:
        return sys.executable
    return None


def demucs_available():
    return demucs_python() is not None


def build_command(path, out_dir, model=DEFAULT_MODEL, two_stems=None,
                  mp3=False, python_exe=None):
    """The exact `python -m demucs` invocation — separated out so tests
    can verify it without Demucs installed."""
    exe = python_exe or demucs_python() or sys.executable
    cmd = [exe, "-m", "demucs", "-n", model,
           "-o", str(out_dir), str(path)]
    if two_stems:
        cmd[5:5] = ["--two-stems", two_stems]
    if mp3:
        cmd.insert(5, "--mp3")
    return cmd


def separate(path, out_dir=None, model=DEFAULT_MODEL, two_stems=None):
    """Run Demucs. Returns {stem_name: wav_path}. Raises with a
    plain-English install hint when Demucs is missing."""
    path = Path(path)
    if not demucs_available():
        raise RuntimeError(INSTALL_HINT)
    out_dir = Path(out_dir) if out_dir else path.parent / "stems"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_command(path, out_dir, model=model, two_stems=two_stems)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Demucs failed:\n{proc.stderr[-2000:]}")
    stem_dir = out_dir / model / path.stem
    stems = {p.stem: str(p) for p in sorted(stem_dir.glob("*.wav"))}
    if not stems:
        raise RuntimeError(f"Demucs finished but no stems found in "
                           f"{stem_dir} — check its output:\n"
                           f"{proc.stdout[-1000:]}")
    return stems


def analyze_stems(path, out_dir=None, model=DEFAULT_MODEL, two_stems=None,
                  spectrograms=True):
    """Separate, then run the ears on every stem. Returns one combined
    report: per-stem LUFS, band balance, and (optionally) spectrogram
    PNGs — the numbers behind 'how is their drum bus balanced?'."""
    import loudness
    stems = separate(path, out_dir=out_dir, model=model, two_stems=two_stems)
    report = {"file": str(path), "model": model, "stems": {}}
    for name, wav in stems.items():
        m = loudness.measure(wav)
        entry = {
            "path": wav,
            "integrated_lufs": m["integrated_lufs"],
            "true_peak_dbtp": m["true_peak_dbtp"],
            "band_energy_db": m["band_energy_db"],
        }
        if spectrograms:
            import spectrogram
            entry["spectrogram_png"] = str(spectrogram.render(wav))
        report["stems"][name] = entry
    # the balance question, answered directly
    lufs = {n: s["integrated_lufs"] for n, s in report["stems"].items()}
    loudest = max(lufs, key=lufs.get)
    report["stem_balance_lu"] = {
        n: round(v - lufs[loudest], 1) for n, v in lufs.items()}
    report["summary"] = (
        f"Loudest stem: {loudest}. Balance (LU below it): "
        + ", ".join(f"{n} {d}" for n, d in report["stem_balance_lu"].items()
                    if n != loudest))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", required=True)
    ap.add_argument("--out-dir", default=None,
                    help="default: <file's folder>/stems")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--two-stems", default=None, choices=STEM_NAMES,
                    help="split into <stem> vs everything-else only")
    ap.add_argument("--analyze", action="store_true",
                    help="also run the ears on each stem")
    args = ap.parse_args(argv)
    if args.analyze:
        print(json.dumps(analyze_stems(args.file, args.out_dir,
                                       args.model, args.two_stems), indent=2))
    else:
        print(json.dumps(separate(args.file, args.out_dir, args.model,
                                  args.two_stems), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
