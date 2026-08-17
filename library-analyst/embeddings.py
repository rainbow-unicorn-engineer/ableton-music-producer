#!/usr/bin/env python3
"""embeddings.py — CLAP vectors: the library's "meaning space".

→ *CLAP is a model trained on millions of (sound, caption) pairs. It
turns any audio clip — or any sentence — into a point in a 512-number
"meaning space", where things that SOUND alike (or sound like the
sentence describes) sit close together. That upgrades search from
word-mapping to true vibe search: "abandoned mall at 3am energy" can
literally be measured against every sound you own.*

CLAP is heavy (PyTorch + a ~2 GB checkpoint) and wants Python 3.11, so
like Demucs it lives in the `xlnt-audio` conda env — `scripts/
setup-audio-env.bat` installs it. This module runs in two modes:

* **inside the audio env** (laion_clap importable): does the real work.
* **anywhere else**: the query modes shell out to the audio env's Python
  (XLNT_AUDIO_PY or XLNT_DEMUCS env var), so the MCP server — which runs
  on the main Python — can still embed a search phrase.

Usage (from an Anaconda Prompt, one overnight run):
    conda run -n xlnt-audio python library-analyst/embeddings.py --scan

    # plumbing modes (the MCP server calls these for you):
    python embeddings.py --text "dark metallic scream"   # JSON vector
    python embeddings.py --embed-file "C:/some/sound.wav"
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import db as dbmod
else:
    from . import db as dbmod

EMBED_DIM = 512
AUDIO_ENV_VARS = ("XLNT_AUDIO_PY", "XLNT_DEMUCS")  # either points at the env

INSTALL_HINT = (
    "CLAP isn't available. Run scripts/setup-audio-env.bat once (it "
    "installs laion-clap into the xlnt-audio Python 3.11 env and sets "
    "the environment variable this module looks for), then embed the "
    "library overnight: "
    "`conda run -n xlnt-audio python library-analyst/embeddings.py --scan`"
)

_model = None  # loaded once per process


def clap_available_here():
    return importlib.util.find_spec("laion_clap") is not None


def audio_env_python():
    """The interpreter that has CLAP, when this one doesn't."""
    for var in AUDIO_ENV_VARS:
        exe = os.environ.get(var)
        if exe:
            return exe
    return None


# ---------------------------------------------------------------------------
# Vector packing — float32 bytes in the samples.embedding BLOB column
# ---------------------------------------------------------------------------

def pack_vector(vec):
    v = np.asarray(vec, dtype=np.float32).reshape(-1)
    n = np.linalg.norm(v)
    if n > 0:
        v = v / n          # store unit vectors: cosine = plain dot product
    return v.tobytes()


def unpack_vector(blob):
    return np.frombuffer(blob, dtype=np.float32)


# ---------------------------------------------------------------------------
# The model (only importable inside the audio env)
# ---------------------------------------------------------------------------

def _load_model():
    global _model
    if _model is None:
        import laion_clap
        _model = laion_clap.CLAP_Module(enable_fusion=False)
        _model.load_ckpt()  # downloads the default checkpoint on first run
    return _model


def embed_text_here(text):
    model = _load_model()
    vec = model.get_text_embedding([text, text])[0]  # model wants a batch
    return np.asarray(vec, dtype=np.float32)


def embed_files_here(paths):
    model = _load_model()
    vecs = model.get_audio_embedding_from_filelist(x=[str(p) for p in paths])
    return np.asarray(vecs, dtype=np.float32)


# ---------------------------------------------------------------------------
# The bridge — usable from ANY Python
# ---------------------------------------------------------------------------

def embed_text(text):
    """Text → vector, wherever we are. Raises RuntimeError with the
    install hint when CLAP is reachable nowhere."""
    if clap_available_here():
        return embed_text_here(text)
    exe = audio_env_python()
    if not exe:
        raise RuntimeError(INSTALL_HINT)
    out = subprocess.run(
        [exe, str(Path(__file__).resolve()), "--text", text, "--json"],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"CLAP text embedding failed:\n{out.stderr[-1500:]}")
    return np.asarray(json.loads(out.stdout.strip().splitlines()[-1]),
                      dtype=np.float32)


def embed_file(path):
    """Audio file → vector, wherever we are."""
    if clap_available_here():
        return embed_files_here([path])[0]
    exe = audio_env_python()
    if not exe:
        raise RuntimeError(INSTALL_HINT)
    out = subprocess.run(
        [exe, str(Path(__file__).resolve()), "--embed-file", str(path),
         "--json"],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"CLAP audio embedding failed:\n{out.stderr[-1500:]}")
    return np.asarray(json.loads(out.stdout.strip().splitlines()[-1]),
                      dtype=np.float32)


# ---------------------------------------------------------------------------
# The overnight scan — fill the embedding column
# ---------------------------------------------------------------------------

def embed_pending(db_path=None, batch_size=16, limit=None, progress=True):
    """Embed every analyzed file that has no embedding yet. Safe to stop
    and re-run — it always picks up where it left off. Returns
    (done, failed)."""
    if not clap_available_here():
        raise RuntimeError(
            "Run the scan from the audio env: conda run -n xlnt-audio "
            "python library-analyst/embeddings.py --scan")
    conn = dbmod.connect(db_path)
    rows = conn.execute(
        "SELECT id, path FROM samples WHERE missing = 0 AND analyzed_at IS "
        "NOT NULL AND embedding IS NULL"
        + (f" LIMIT {int(limit)}" if limit else "")).fetchall()
    done = failed = 0
    t0 = time.time()
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        existing = [r for r in batch if Path(r["path"]).exists()]
        try:
            vecs = embed_files_here([r["path"] for r in existing])
            for r, v in zip(existing, vecs):
                conn.execute("UPDATE samples SET embedding=? WHERE id=?",
                             (pack_vector(v), r["id"]))
            done += len(existing)
        except Exception:
            # batch failed — try one by one so a single bad file can't
            # poison its neighbours
            for r in existing:
                try:
                    v = embed_files_here([r["path"]])[0]
                    conn.execute("UPDATE samples SET embedding=? WHERE id=?",
                                 (pack_vector(v), r["id"]))
                    done += 1
                except Exception as exc:
                    failed += 1
                    if progress:
                        print(f"  ! {Path(r['path']).name}: {exc}",
                              file=sys.stderr)
        failed += len(batch) - len(existing)
        conn.commit()
        if progress and done and done % 320 < batch_size:
            rate = done / max(time.time() - t0, 1e-9)
            remaining = (len(rows) - done - failed) / max(rate, 1e-9)
            print(f"  {done}/{len(rows)} embedded "
                  f"(~{remaining / 3600:.1f} h remaining)", flush=True)
    conn.close()
    return done, failed


def embedding_coverage(db_path=None):
    conn = dbmod.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM samples WHERE missing=0 "
                         "AND analyzed_at IS NOT NULL").fetchone()[0]
    have = conn.execute("SELECT COUNT(*) FROM samples WHERE missing=0 "
                        "AND embedding IS NOT NULL").fetchone()[0]
    conn.close()
    return {"analyzed": total, "embedded": have, "remaining": total - have}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", action="store_true",
                    help="embed every analyzed-but-unembedded file")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--text", default=None, help="embed a phrase")
    ap.add_argument("--embed-file", default=None, help="embed one audio file")
    ap.add_argument("--json", action="store_true",
                    help="print the raw vector as JSON (plumbing mode)")
    ap.add_argument("--db", default=None)
    args = ap.parse_args(argv)

    if args.text is not None:
        vec = embed_text(args.text) if not clap_available_here() \
            else embed_text_here(args.text)
        print(json.dumps([float(x) for x in vec]))
        return 0
    if args.embed_file is not None:
        vec = embed_file(args.embed_file) if not clap_available_here() \
            else embed_files_here([args.embed_file])[0]
        print(json.dumps([float(x) for x in vec]))
        return 0
    if args.scan:
        done, failed = embed_pending(args.db, limit=args.limit)
        print(f"Embedding done: {done} files, {failed} failures.")
        print(json.dumps(embedding_coverage(args.db)))
        return 0
    print(json.dumps(embedding_coverage(args.db), indent=2))
    print("\nNothing to do — pass --scan, --text or --embed-file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
