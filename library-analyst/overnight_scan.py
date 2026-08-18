#!/usr/bin/env python3
"""overnight_scan.py — one command before bed, a full report in the morning.

Does, in order:
  1. Scans every audio file under the given roots into the library database.
  2. Analyzes everything not yet analyzed (BPM, key, brightness, punch,
     loudness). This is the slow, overnight part.
  3. Inventories every .zip under the roots and tries to match each one to
     an already-extracted folder (same name) under the roots or the
     --extracted-hint locations. Unmatched zips go in the report's
     "to extract" list — their samples are invisible until unzipped.
  4. Writes a review document: docs/library-report.md in the repo.

Safe to interrupt (Ctrl+C): progress is saved continuously, the report is
still written with whatever finished, and re-running resumes where it
stopped — already-analyzed files are never redone.

Usage:

    python overnight_scan.py --root "C:/Music Production" --extracted-hint "D:/"
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db as dbmod
import scanner
import analysis
import search

REPORT_PATH = Path(__file__).resolve().parents[1] / "docs" / "library-report.md"


def _norm(name):
    """Normalize a name for zip↔folder matching: lowercase, alnum only."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


def zip_inventory(roots, extracted_hints, hint_depth=3):
    """Find every .zip under the roots; try to match each to an extracted
    folder by (normalized) name anywhere under the roots or the hint
    locations. Returns (matched, unmatched) lists of dicts."""
    zips = []
    for root in roots:
        root = Path(root)
        if root.exists():
            zips.extend(root.rglob("*.zip"))

    # index of candidate folder names -> path
    dir_index = {}

    def add_dir(p):
        key = _norm(p.name)
        if key and key not in dir_index:
            dir_index[key] = p

    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_dir():
                add_dir(p)
    for hint in extracted_hints:
        hint = Path(hint)
        if not hint.exists():
            continue
        add_dir(hint)
        stack = [(hint, 0)]
        while stack:
            cur, depth = stack.pop()
            if depth >= hint_depth:
                continue
            try:
                for p in cur.iterdir():
                    if p.is_dir():
                        add_dir(p)
                        stack.append((p, depth + 1))
            except (PermissionError, OSError):
                continue

    matched, unmatched = [], []
    for z in sorted(set(zips)):
        key = _norm(z.stem)
        hit = dir_index.get(key)
        if hit is None:  # containment fallback: "Pack.zip" vs "Pack v2"
            for dkey, dpath in dir_index.items():
                if key and (key in dkey or dkey in key) and min(len(key), len(dkey)) >= 8:
                    hit = dpath
                    break
        entry = {
            "zip": str(z),
            "name": z.name,
            "size_mb": round(z.stat().st_size / 1e6, 1),
            "extracted_at": str(hit) if hit else None,
        }
        (matched if hit else unmatched).append(entry)
    return matched, unmatched


def write_report(roots, run_info, matched, unmatched, db_path=None):
    stats = search.library_stats(db_path=db_path)
    conn = dbmod.connect(db_path)

    # tempo distribution in 10-BPM buckets
    bpm_rows = conn.execute(
        "SELECT CAST(bpm/10 AS INT)*10 AS bucket, COUNT(*) FROM samples "
        "WHERE missing=0 AND bpm IS NOT NULL GROUP BY bucket ORDER BY bucket"
    ).fetchall()
    # biggest top-level folders by file count
    folder_rows = {}
    for r in conn.execute("SELECT path FROM samples WHERE missing=0"):
        p = Path(r["path"])
        for root in roots:
            root = Path(root)
            try:
                rel = p.relative_to(root)
                top = str(Path(root).name) + "/" + (rel.parts[0] if len(rel.parts) > 1 else "")
                folder_rows[top] = folder_rows.get(top, 0) + 1
                break
            except ValueError:
                continue
    # unanalyzed leftovers (failures / not reached)
    leftovers = [r["path"] for r in conn.execute(
        "SELECT path FROM samples WHERE missing=0 AND analyzed_at IS NULL "
        "ORDER BY path LIMIT 50")]
    leftover_count = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE missing=0 AND analyzed_at IS NULL"
    ).fetchone()[0]
    conn.close()

    lines = []
    a = lines.append
    a("# Library Analysis Report")
    a("")
    a(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by overnight_scan.py*")
    a("")
    a("## Summary of work completed")
    a("")
    a(f"- Roots scanned: {', '.join('`' + str(r) + '`' for r in roots)}")
    a(f"- Scan: **{run_info['added']} new**, {run_info['updated']} changed, "
      f"{run_info['unchanged']} unchanged files")
    a(f"- Analysis: **{run_info['analyzed']} files analyzed** this run, "
      f"{run_info['failed']} failures, in {run_info['elapsed_min']:.0f} min")
    a(f"- Library now: **{stats['total_files']} audio files known, "
      f"{stats['analyzed']} fully analyzed** "
      f"({stats['one_shots']} one-shots, {stats['loops']} loops)")
    if run_info.get("interrupted"):
        a("- ⚠️ Run was interrupted — re-run `overnight_scan.py` to finish; "
          "completed work is saved.")
    a("")
    a("## What the library contains")
    a("")
    a("| Category | Files |")
    a("|----------|-------|")
    for cat, n in stats["by_category"].items():
        a(f"| {cat} | {n} |")
    a("")
    if stats["by_key"]:
        a("### Keys (top 12)")
        a("")
        a("| Key | Files |")
        a("|-----|-------|")
        for key, n in list(stats["by_key"].items())[:12]:
            a(f"| {key} | {n} |")
        a("")
    if bpm_rows:
        a("### Tempo distribution (loops)")
        a("")
        a("| BPM range | Files |")
        a("|-----------|-------|")
        for bucket, n in bpm_rows:
            a(f"| {int(bucket)}–{int(bucket) + 9} | {n} |")
        a("")
    if folder_rows:
        a("### Biggest sources (top-level folders)")
        a("")
        a("| Folder | Files |")
        a("|--------|-------|")
        for name, n in sorted(folder_rows.items(), key=lambda t: -t[1])[:20]:
            a(f"| {name} | {n} |")
        a("")
    if leftover_count:
        a(f"### Files that could not be analyzed ({leftover_count})")
        a("")
        for p in leftovers:
            a(f"- `{p}`")
        if leftover_count > len(leftovers):
            a(f"- ...and {leftover_count - len(leftovers)} more")
        a("")
    a("## Zips already covered by an extracted folder "
      f"({len(matched)})")
    a("")
    a("These zips have a matching extracted folder, so their contents were "
      "scanned from the folder — nothing to do:")
    a("")
    for m in matched:
        a(f"- `{m['name']}` → `{m['extracted_at']}`")
    a("")
    a(f"## ⚠️ Zips that could NOT be analyzed — extract these ({len(unmatched)})")
    a("")
    a("No extracted folder was found for these, so their samples are "
      "invisible to the analyst. Extract them (anywhere under the scanned "
      "roots), then re-run `overnight_scan.py` — it will pick up only the "
      "new files:")
    a("")
    if unmatched:
        a("| Zip | Size (MB) | Location |")
        a("|-----|-----------|----------|")
        for u in unmatched:
            a(f"| {u['name']} | {u['size_mb']} | `{u['zip']}` |")
    else:
        a("*(none — every zip has an extracted counterpart)*")
    a("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", action="append", required=True,
                    help="library root to scan (repeatable)")
    ap.add_argument("--extracted-hint", action="append", default=[],
                    help="extra place to look for extracted zip folders "
                         "(repeatable), e.g. D:/")
    ap.add_argument("--db", default=None)
    args = ap.parse_args(argv)

    t0 = time.time()
    run_info = {"added": 0, "updated": 0, "unchanged": 0,
                "analyzed": 0, "failed": 0, "interrupted": False}
    try:
        print(f"[1/4] Scanning {len(args.root)} root(s)...", flush=True)
        added, updated, unchanged = scanner.scan(args.root, args.db)
        run_info.update(added=added, updated=updated, unchanged=unchanged)
        print(f"      {added} new, {updated} changed, {unchanged} unchanged.")

        print("[2/4] Analyzing (the overnight part — safe to leave)...", flush=True)
        done, failed = analysis.analyze_pending(args.db)
        run_info.update(analyzed=done, failed=failed)
        print(f"      {done} analyzed, {failed} failures.")
    except KeyboardInterrupt:
        run_info["interrupted"] = True
        print("\nInterrupted — writing report with completed work...", flush=True)

    print("[3/4] Cross-referencing zips against extracted folders...", flush=True)
    matched, unmatched = zip_inventory(args.root, args.extracted_hint)
    print(f"      {len(matched)} zips covered, {len(unmatched)} need extraction.")

    print("[4/4] Writing report...", flush=True)
    path = write_report(args.root, dict(run_info,
                                        elapsed_min=(time.time() - t0) / 60),
                        matched, unmatched, args.db)
    print(f"Done in {(time.time() - t0) / 60:.0f} min. Report: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
