#!/usr/bin/env python3
"""scanner.py — walk your sample folders and remember every audio file.

For each audio file it stores path, filename, size, and a hash → *a
fingerprint of the file's contents, so re-scans skip unchanged files.*
Analysis (BPM, key, brightness...) is a separate, slower pass — see
`analysis.py`. The plan's build order: scan ONE folder first, sanity-check,
then unleash it on the full library overnight.

Usage:

    # First scan — start with one folder to test
    python scanner.py --root "D:/Samples/Drums"

    # Add more roots any time; re-runs are incremental
    python scanner.py --root "D:/Samples" --root "E:/Splice"

    # See what's in the database
    python scanner.py --stats
"""

import argparse
import hashlib
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import db as dbmod
    from taxonomy import categorize
else:  # imported as a package (tests)
    from . import db as dbmod
    from .taxonomy import categorize

AUDIO_EXTS = {".wav", ".aif", ".aiff", ".mp3", ".flac", ".ogg", ".m4a"}


def file_hash(path, chunk=1 << 20):
    """Fingerprint file contents (blake2b — fast and collision-safe)."""
    h = hashlib.blake2b(digest_size=16)
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def iter_audio_files(root):
    root = Path(root)
    if not root.exists():
        raise SystemExit(f"error: folder does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"error: not a folder: {root} "
                         "(zips must be extracted first)")
    for p in sorted(root.rglob("*")):
        if not (p.is_file() and p.suffix.lower() in AUDIO_EXTS):
            continue
        # skip macOS AppleDouble junk ("._foo.wav") and hidden files —
        # they're metadata stubs, not audio, and always fail analysis
        if p.name.startswith("._") or p.name.startswith("."):
            continue
        yield p


def scan(roots, db_path=None, progress=True):
    """Scan folders into the database. Returns (added, updated, unchanged).

    Incremental logic: if size+mtime match what we stored, the file is
    assumed unchanged and we don't even re-hash it (cheap). If they
    differ, we re-hash; a changed hash resets the analysis columns so
    `analysis.py` knows to revisit the file.
    """
    conn = dbmod.connect(db_path)
    cur = conn.cursor()
    # purge any junk rows indexed before the AppleDouble filter existed
    cur.execute("DELETE FROM samples WHERE filename LIKE '.%'")
    added = updated = unchanged = 0
    seen_paths = []

    for root in roots:
        for p in iter_audio_files(root):
            path_str = str(p.resolve())
            seen_paths.append(path_str)
            stat = p.stat()
            row = cur.execute(
                "SELECT size, mtime, hash FROM samples WHERE path = ?",
                (path_str,)).fetchone()

            if row and row["size"] == stat.st_size and row["mtime"] == stat.st_mtime:
                cur.execute("UPDATE samples SET missing = 0 WHERE path = ?", (path_str,))
                unchanged += 1
                continue

            digest = file_hash(p)
            if row is None:
                cur.execute(
                    """INSERT INTO samples (path, filename, size, mtime, hash, category, missing)
                       VALUES (?, ?, ?, ?, ?, ?, 0)""",
                    (path_str, p.name, stat.st_size, stat.st_mtime, digest,
                     categorize(path_str)))
                added += 1
            elif row["hash"] != digest:
                # contents changed — stale analysis must be redone
                cur.execute(
                    """UPDATE samples SET filename=?, size=?, mtime=?, hash=?,
                       category=?, bpm=NULL, key=NULL, duration=NULL,
                       brightness=NULL, punch=NULL, loudness=NULL,
                       embedding=NULL, analyzed_at=NULL, missing=0
                       WHERE path=?""",
                    (p.name, stat.st_size, stat.st_mtime, digest,
                     categorize(path_str), path_str))
                updated += 1
            else:
                # same contents, new timestamp — just refresh bookkeeping
                cur.execute("UPDATE samples SET size=?, mtime=?, missing=0 WHERE path=?",
                            (stat.st_size, stat.st_mtime, path_str))
                unchanged += 1

            if progress and (added + updated) % 500 == 0 and (added + updated):
                print(f"  ...{added + updated} files fingerprinted", flush=True)

    # Flag rows under the scanned roots whose files vanished
    seen = set(seen_paths)
    for root in roots:
        prefix = str(Path(root).resolve())
        for row in cur.execute(
                "SELECT path FROM samples WHERE path LIKE ? AND missing = 0",
                (prefix + "%",)).fetchall():
            if row["path"] not in seen:
                cur.execute("UPDATE samples SET missing = 1 WHERE path = ?", (row["path"],))

    conn.commit()
    conn.close()
    return added, updated, unchanged


def stats(db_path=None):
    conn = dbmod.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM samples WHERE missing = 0").fetchone()[0]
    analyzed = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE missing = 0 AND analyzed_at IS NOT NULL"
    ).fetchone()[0]
    print(f"{total} files known, {analyzed} analyzed "
          f"({total - analyzed} awaiting analysis.py)")
    for row in conn.execute(
            """SELECT COALESCE(category, '(uncategorized)') c, COUNT(*) n
               FROM samples WHERE missing = 0 GROUP BY c ORDER BY n DESC"""):
        print(f"  {row['c']:>16}: {row['n']}")
    conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", action="append", default=[],
                    help="folder to scan (repeatable)")
    ap.add_argument("--db", default=None, help="database file (default: db/library.sqlite3)")
    ap.add_argument("--stats", action="store_true", help="print library stats and exit")
    args = ap.parse_args(argv)

    if args.stats:
        stats(args.db)
        return 0
    if not args.root:
        ap.error("give at least one --root folder (or --stats)")

    t0 = time.time()
    added, updated, unchanged = scan(args.root, args.db)
    print(f"Scan done in {time.time() - t0:.1f}s — "
          f"{added} new, {updated} changed, {unchanged} unchanged.")
    print("Next: python analysis.py   (fills in BPM, key, brightness, ...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
