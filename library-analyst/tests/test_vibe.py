"""Vibe-search tests — vector packing, cosine ranking, the self-exclusion
rule, and the guard rails when CLAP/embeddings are absent. No CLAP model
needed: tests inject known vectors, which also pins the storage format.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db as dbmod        # noqa: E402
import embeddings as emb  # noqa: E402
import vibe               # noqa: E402


def make_library(db_path, vectors):
    """A tiny library where each sample carries a known unit vector."""
    conn = dbmod.connect(db_path)
    for i, (name, vec, category) in enumerate(vectors):
        conn.execute(
            "INSERT INTO samples (path, filename, category, analyzed_at, "
            "embedding) VALUES (?, ?, ?, ?, ?)",
            (f"C:/lib/{name}", name, category, time.time(),
             emb.pack_vector(vec) if vec is not None else None))
    conn.commit()
    conn.close()


def unit(*components):
    v = np.zeros(8, dtype=np.float32)
    for idx, val in enumerate(components):
        v[idx] = val
    return v / np.linalg.norm(v)


def test_pack_unpack_roundtrip_and_normalization():
    v = np.array([3.0, 4.0], dtype=np.float32)   # norm 5
    out = emb.unpack_vector(emb.pack_vector(v))
    assert out.dtype == np.float32
    assert np.allclose(out, [0.6, 0.8])          # stored as unit vector
    assert np.isclose(np.linalg.norm(out), 1.0)


def test_vibe_search_ranks_by_cosine(tmp_path):
    db = tmp_path / "lib.sqlite3"
    make_library(db, [
        ("exact.wav",    unit(1.0),        "bass"),
        ("close.wav",    unit(0.9, 0.1),   "bass"),
        ("far.wav",      unit(0.1, 0.9),   "bass"),
        ("opposite.wav", unit(-1.0),       "bass"),
        ("no_vec.wav",   None,             "bass"),   # unembedded: invisible
    ])
    got = vibe.vibe_search(query_vector=unit(1.0), db_path=db, limit=10)
    names = [g["filename"] for g in got]
    assert names[:2] == ["exact.wav", "close.wav"]
    assert names[-1] == "opposite.wav"
    assert "no_vec.wav" not in names
    assert got[0]["similarity"] == pytest.approx(1.0, abs=1e-3)
    sims = [g["similarity"] for g in got]
    assert sims == sorted(sims, reverse=True)
    assert all("embedding" not in g for g in got)


def test_vibe_search_category_filter(tmp_path):
    db = tmp_path / "lib.sqlite3"
    make_library(db, [
        ("bass_hit.wav", unit(1.0), "bass"),
        ("kick_hit.wav", unit(1.0), "kick"),
    ])
    got = vibe.vibe_search(query_vector=unit(1.0), db_path=db,
                           category="kick")
    assert [g["filename"] for g in got] == ["kick_hit.wav"]


def test_similar_sound_uses_stored_vector_and_excludes_self(tmp_path):
    db = tmp_path / "lib.sqlite3"
    make_library(db, [
        ("target.wav",  unit(1.0),      "bass"),
        ("twin.wav",    unit(0.99, 0.1), "bass"),
        ("cousin.wav",  unit(0.5, 0.5),  "texture"),
    ])
    got = vibe.similar_sound("target.wav", db_path=db, limit=5)
    names = [g["filename"] for g in got]
    assert names[0] == "twin.wav"
    assert "target.wav" not in names          # never returns itself


def test_no_embeddings_yet_message(tmp_path):
    db = tmp_path / "lib.sqlite3"
    make_library(db, [("a.wav", None, "bass")])
    with pytest.raises(RuntimeError, match="embeddings.py --scan"):
        vibe.vibe_search(query_vector=unit(1.0), db_path=db)


def test_embed_text_guard_rail(tmp_path):
    """Without CLAP anywhere, embed_text points at the setup script."""
    import os
    if emb.clap_available_here():
        pytest.skip("CLAP installed here — guard rail not reachable")
    saved = {v: os.environ.pop(v, None) for v in emb.AUDIO_ENV_VARS}
    try:
        with pytest.raises(RuntimeError, match="setup-audio-env"):
            emb.embed_text("dark gritty texture")
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


def test_embedding_coverage_counts(tmp_path):
    db = tmp_path / "lib.sqlite3"
    make_library(db, [
        ("a.wav", unit(1.0), "bass"),
        ("b.wav", None,      "bass"),
    ])
    cov = emb.embedding_coverage(db)
    assert cov == {"analyzed": 2, "embedded": 1, "remaining": 1}
