"""db.py — the analyst's memory.

SQLite → *a database that's just a single file — no server to run.* The
file lives in `library-analyst/db/` (gitignored; regenerate any time by
re-scanning).

Schema follows the project plan, plus bookkeeping columns so re-scans are
cheap and vanished files don't haunt search results.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / "db" / "library.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    id          INTEGER PRIMARY KEY,
    path        TEXT UNIQUE NOT NULL,
    filename    TEXT NOT NULL,
    size        INTEGER,
    mtime       REAL,
    hash        TEXT,               -- fingerprint of file contents
    bpm         REAL,               -- tempo of loops (NULL for one-shots)
    key         TEXT,               -- e.g. 'F minor'
    duration    REAL,               -- seconds
    brightness  REAL,               -- spectral centroid, Hz (dark low, sparkly high)
    punch       REAL,               -- onset strength (soft pad low, hard transient high)
    loudness    REAL,               -- RMS energy 0..1-ish
    category    TEXT,               -- kick/snare/hat/bass/vocal/fx/texture/... (folder-name heuristics)
    embedding   BLOB,               -- CLAP vector, when enabled (Phase 2 power-up)
    analyzed_at REAL,               -- unix time of last analysis; NULL = not analyzed yet
    missing     INTEGER DEFAULT 0   -- 1 = file no longer on disk at last scan
);
CREATE INDEX IF NOT EXISTS idx_samples_category ON samples(category);
CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key);
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
"""


def connect(db_path=None):
    """Open (and if needed create) the library database."""
    db_path = Path(db_path) if db_path else DEFAULT_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
