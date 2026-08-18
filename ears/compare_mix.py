#!/usr/bin/env python3
"""compare_mix.py — your bounce vs. a reference, side by side.

The roadmap's highest-payoff tool: turns "make it sound pro" into a
checklist of measurable gaps.

→ *It diffs the numbers: loudness delta (are you 3 LU quieter than the
reference?), true peak (are you clipping where they aren't?), dynamics,
and band-by-band balance ("their sub sits 6 dB above their low-mids;
yours doesn't"). Optionally renders both spectrograms stacked in one
PNG so the differences are visible, not just numeric.*

The reference can be a saved card name (see references.py) or any audio
file (analyzed on the fly).

Usage:
    python compare_mix.py --bounce mix_v3.wav --reference weekend-griz-flip
    python compare_mix.py --bounce mix_v3.wav --reference "C:/refs/ref.wav" --png
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loudness  # noqa: E402
import references  # noqa: E402

# Band-balance differences smaller than this aren't worth chasing.
BAND_TOLERANCE_DB = 2.5


def _metrics_for(ref):
    """Reference metrics from a card name, card path, or audio file."""
    p = Path(str(ref))
    if p.exists() and p.suffix.lower() not in (".json",):
        m = loudness.measure(p)
        m["name"] = p.stem
        return m, "audio file (analyzed now)"
    card = references.load_card(ref)
    return card, "reference card"


def compare(bounce, reference, png=False, out_dir=None):
    """Returns the full diff dict, including a human-readable gap list."""
    bounce = Path(bounce)
    mine = loudness.measure(bounce)
    ref, ref_kind = _metrics_for(reference)

    lufs_delta = round(mine["integrated_lufs"] - ref["integrated_lufs"], 2)
    lra_delta = round(mine["loudness_range_lu"] - ref["loudness_range_lu"], 1)
    band_delta = {
        band: round(mine["band_energy_db"].get(band, 0.0)
                    - ref["band_energy_db"].get(band, 0.0), 1)
        for band in mine["band_energy_db"]
    }

    gaps = []
    if abs(lufs_delta) > 1.0:
        word = "quieter" if lufs_delta < 0 else "louder"
        gaps.append(f"Your bounce is {abs(lufs_delta):.1f} LU {word} than "
                    f"the reference ({mine['integrated_lufs']} vs "
                    f"{ref['integrated_lufs']} LUFS).")
    if mine["true_peak_dbtp"] > -1.0:
        gaps.append(f"Your true peak is {mine['true_peak_dbtp']} dBTP "
                    f"(reference: {ref['true_peak_dbtp']}) — keep under "
                    f"-1.0 or lossy encoders will clip.")
    if abs(lra_delta) > 2.0:
        word = "more compressed" if lra_delta < 0 else "more dynamic"
        gaps.append(f"Your mix is {abs(lra_delta):.1f} LU {word} than the "
                    f"reference (loudness range {mine['loudness_range_lu']} "
                    f"vs {ref['loudness_range_lu']} LU).")
    for band, d in band_delta.items():
        if abs(d) > BAND_TOLERANCE_DB:
            word = "light" if d < 0 else "heavy"
            gaps.append(f"{band}: {abs(d):.1f} dB {word} vs. the reference "
                        f"(yours {mine['band_energy_db'][band]}, "
                        f"theirs {ref['band_energy_db'][band]}).")
    verdict = ("Within range of the reference on every measured axis — "
               "the rest is taste." if not gaps else
               f"{len(gaps)} measurable gap(s) — fix the top one first.")

    result = {
        "bounce": str(bounce),
        "reference": ref.get("name", str(reference)),
        "reference_kind": ref_kind,
        "lufs": {"bounce": mine["integrated_lufs"],
                 "reference": ref["integrated_lufs"],
                 "delta": lufs_delta},
        "true_peak_dbtp": {"bounce": mine["true_peak_dbtp"],
                           "reference": ref["true_peak_dbtp"]},
        "loudness_range_lu": {"bounce": mine["loudness_range_lu"],
                              "reference": ref["loudness_range_lu"],
                              "delta": lra_delta},
        "band_delta_db": band_delta,
        "band_energy_db": {"bounce": mine["band_energy_db"],
                           "reference": ref["band_energy_db"]},
        "gaps": gaps,
        "verdict": verdict,
    }
    if png:
        result["comparison_png"] = str(_render_png(
            bounce, ref, result, out_dir))
    return result


def _render_png(bounce, ref, result, out_dir=None):
    """Both spectrograms stacked in one image, gaps printed underneath."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import spectrogram

    out_dir = Path(out_dir) if out_dir else Path(bounce).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_mine = spectrogram.render(bounce, out_dir / "_cmp_mine.png")
    ref_png = ref.get("spectrogram_png")
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=110)
    for ax, (title, png_path) in zip(axes, [
            (f"YOURS — {Path(bounce).name}", tmp_mine),
            (f"REFERENCE — {ref.get('name', 'reference')}", ref_png)]):
        if png_path and Path(png_path).exists():
            ax.imshow(plt.imread(str(png_path)))
        else:
            ax.text(0.5, 0.5, "no spectrogram on the card",
                    ha="center", va="center")
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.suptitle(result["verdict"], fontsize=10, y=0.995)
    out = out_dir / (Path(bounce).stem + ".vs."
                     + str(ref.get("name", "ref")) + ".png")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    tmp_mine.unlink(missing_ok=True)
    return out


def summarize(result):
    lines = [f"{Path(result['bounce']).name} vs {result['reference']}:"]
    lines += [f"  • {g}" for g in result["gaps"]]
    lines.append(result["verdict"])
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bounce", required=True, help="your mix bounce")
    ap.add_argument("--reference", required=True,
                    help="card name, card path, or reference audio file")
    ap.add_argument("--png", action="store_true",
                    help="render stacked-spectrogram comparison PNG")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)
    r = compare(args.bounce, args.reference, png=args.png,
                out_dir=args.out_dir)
    print(json.dumps(r, indent=2))
    print()
    print(summarize(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
