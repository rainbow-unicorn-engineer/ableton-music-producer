#!/usr/bin/env python3
"""references.py — the reference-card workflow.

→ *A reference card: one JSON file that captures a target track's
measurable DNA — loudness (LUFS), true peak, dynamics, band balance,
key, tempo, and arrangement skeleton — plus its spectrogram PNG.
Analyze a reference once, compare your bounces against it forever.*

Cards live in `references/` at the repo root (created on first use).
The audio itself is never copied there — only the numbers and pictures.

Usage:
    python references.py --file "C:/refs/Weekend (GRiZ flip).wav"
    python references.py --file ref.wav --name "weekend-griz-flip"
    python references.py --list
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loudness  # noqa: E402
import spectrogram  # noqa: E402
import structure  # noqa: E402

# The monorepo's stated reason to exist: the analysis functions serve both
# the library analyst and the ears. Key detection lives there — reuse it.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "library-analyst"))

REFS_DIR = Path(__file__).resolve().parents[1] / "references"


def _slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "reference"


def make_card(path, name=None, refs_dir=None, bpm=None):
    """Analyze one reference track into a card. Returns the card dict."""
    path = Path(path)
    refs_dir = Path(refs_dir) if refs_dir else REFS_DIR
    refs_dir.mkdir(parents=True, exist_ok=True)
    name = _slug(name or path.stem)

    card = {
        "name": name,
        "source_file": str(path),
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    card.update({k: v for k, v in loudness.measure(path).items()
                 if k != "file"})

    try:  # key/bpm via the library analyst's engine (librosa or fallback)
        import analysis as analysis_mod
        feats = analysis_mod.analyze_file(path)
        card["key"] = feats.get("key")
        if bpm is None:
            bpm = feats.get("bpm")
    except Exception as exc:  # the card is still useful without a key
        card["key"] = None
        card["key_error"] = str(exc)

    try:
        struct = structure.analyze_structure(path, bpm=bpm, png=True,
                                             out_dir=refs_dir)
        card["bpm"] = struct["bpm"]
        card["structure"] = {
            "skeleton": struct["skeleton"],
            "total_bars": struct["total_bars"],
            "sections": struct["sections"],
        }
        card["structure_png"] = struct.get("structure_png")
    except RuntimeError as exc:  # no tempo found — card still works
        card["bpm"] = bpm
        card["structure"] = None
        card["structure_error"] = str(exc)

    png = spectrogram.render(path, refs_dir / (name + ".spectrogram.png"))
    card["spectrogram_png"] = str(png)

    card_path = refs_dir / (name + ".reference.json")
    card_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
    card["card_path"] = str(card_path)
    return card


def list_cards(refs_dir=None):
    """All cards on file: name, key, bpm, LUFS, skeleton."""
    refs_dir = Path(refs_dir) if refs_dir else REFS_DIR
    out = []
    if refs_dir.is_dir():
        for f in sorted(refs_dir.glob("*.reference.json")):
            try:
                c = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            out.append({
                "name": c.get("name", f.stem),
                "card_path": str(f),
                "key": c.get("key"),
                "bpm": c.get("bpm"),
                "integrated_lufs": c.get("integrated_lufs"),
                "true_peak_dbtp": c.get("true_peak_dbtp"),
                "skeleton": (c.get("structure") or {}).get("skeleton"),
            })
    return out


def load_card(name_or_path, refs_dir=None):
    """Find a card by name (fuzzy) or path. Raises with the available
    names if nothing matches."""
    refs_dir = Path(refs_dir) if refs_dir else REFS_DIR
    p = Path(name_or_path)
    if p.suffix == ".json" and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    want = _slug(str(name_or_path))
    candidates = list_cards(refs_dir)
    for c in candidates:
        if c["name"] == want:
            return json.loads(Path(c["card_path"]).read_text(encoding="utf-8"))
    for c in candidates:
        if want in c["name"] or c["name"] in want:
            return json.loads(Path(c["card_path"]).read_text(encoding="utf-8"))
    have = ", ".join(c["name"] for c in candidates) or "(none yet)"
    raise FileNotFoundError(
        f"No reference card matching '{name_or_path}'. On file: {have}. "
        f"Make one: python references.py --file <track>")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=None, help="reference track to analyze")
    ap.add_argument("--name", default=None, help="card name (default: filename)")
    ap.add_argument("--bpm", type=float, default=None)
    ap.add_argument("--list", action="store_true", help="show all cards")
    args = ap.parse_args(argv)
    if args.list or not args.file:
        cards = list_cards()
        if not cards:
            print("No reference cards yet. Make one:\n"
                  "  python references.py --file \"C:/refs/track.wav\"")
        for c in cards:
            print(f"  {c['name']}: {c.get('key')} {c.get('bpm')} BPM, "
                  f"{c.get('integrated_lufs')} LUFS — {c.get('skeleton')}")
        return 0
    card = make_card(args.file, name=args.name, bpm=args.bpm)
    print(json.dumps({k: v for k, v in card.items()
                      if k not in ("structure",)}, indent=2))
    if card.get("structure"):
        print(f"\nSkeleton: {card['structure']['skeleton']}")
    print(f"\nCard: {card['card_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
