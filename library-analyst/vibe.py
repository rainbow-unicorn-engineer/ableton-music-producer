"""vibe.py — search the library by how things SOUND.

The deferred cherry, delivered. Where `search.py` maps words onto stored
numbers (dark → low brightness), vibe search asks CLAP to place your
*sentence* in meaning space and returns the sounds that sit closest —
so "haunted carousel music box" works even though no filename says it.

Cosine similarity → *both the sentence and every sound are arrows in a
512-dimension space; the smaller the angle between two arrows, the more
alike they are. We store unit-length arrows, so the angle check is one
multiplication across the whole library — instant.*

Needs the embedding column filled first (one overnight run):
    conda run -n xlnt-audio python library-analyst/embeddings.py --scan
"""

import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import db as dbmod
    import embeddings as emb
else:
    from . import db as dbmod
    from . import embeddings as emb

NO_EMBEDDINGS_MSG = (
    "No CLAP embeddings in the library yet. One-time overnight run: "
    "`conda run -n xlnt-audio python library-analyst/embeddings.py --scan` "
    "(after scripts/setup-audio-env.bat). Until then, find_sounds is the "
    "word-based fallback."
)


def _load_matrix(conn, category=None):
    """All embedded samples as (ids, unit-vector matrix, row lookup)."""
    where = "missing = 0 AND embedding IS NOT NULL"
    params = []
    if category:
        where += " AND category = ?"
        params.append(category)
    rows = conn.execute(
        f"SELECT * FROM samples WHERE {where}", params).fetchall()
    if not rows:
        return [], None, {}
    mat = np.vstack([emb.unpack_vector(r["embedding"]) for r in rows])
    return [r["id"] for r in rows], mat, {r["id"]: r for r in rows}


def _query_vec(description=None, audio_path=None, query_vector=None):
    if query_vector is not None:
        v = np.asarray(query_vector, dtype=np.float32).reshape(-1)
    elif audio_path is not None:
        v = emb.embed_file(audio_path)
    elif description:
        v = emb.embed_text(description)
    else:
        raise ValueError("Give a description, an audio path, or a vector")
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def vibe_search(description=None, audio_path=None, category=None,
                limit=10, db_path=None, query_vector=None):
    """The upgrade to find_sounds: rank the library by CLAP similarity to
    a sentence (`description`) or to a piece of audio (`audio_path` — any
    file on disk, in the library or not: 'find me sounds like THIS').
    `query_vector` bypasses the model (used by tests and callers that
    already embedded). Returns dicts with a `similarity` field (1.0 =
    identical direction in meaning space)."""
    conn = dbmod.connect(db_path)
    ids, mat, lookup = _load_matrix(conn, category=category)
    if mat is None:
        conn.close()
        raise RuntimeError(NO_EMBEDDINGS_MSG)
    q = _query_vec(description, audio_path, query_vector)
    sims = mat @ q                      # unit vectors: dot = cosine
    order = np.argsort(-sims)[:limit]
    out = []
    for i in order:
        d = dict(lookup[ids[int(i)]])
        d.pop("embedding", None)
        d["similarity"] = round(float(sims[int(i)]), 4)
        out.append(d)
    conn.close()
    return out


def similar_sound(path, limit=10, db_path=None, query_vector=None):
    """'More like this one', by EAR instead of by feature numbers. If the
    file is already embedded in the library, its stored vector is used
    (instant); otherwise the file is embedded on the fly. Excludes the
    file itself from results."""
    conn = dbmod.connect(db_path)
    row = conn.execute(
        "SELECT id, embedding FROM samples WHERE (path = ? OR filename = ?)"
        " AND embedding IS NOT NULL", (str(path), str(path))).fetchone()
    conn.close()
    if query_vector is None and row is not None:
        query_vector = emb.unpack_vector(row["embedding"])
    results = vibe_search(audio_path=None if query_vector is not None else path,
                          limit=limit + 1, db_path=db_path,
                          query_vector=query_vector)
    self_id = row["id"] if row is not None else None
    return [r for r in results if r["id"] != self_id][:limit]
