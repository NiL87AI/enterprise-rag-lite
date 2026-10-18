import pytest
from app.services.bm25_store import BM25Store, rrf_fuse


# --- BM25Store ------------------------------------------------------------

def _chunks(texts):
    return [{"content": t, "metadata": {"chunk_index": i, "total_chunks": len(texts)}}
            for i, t in enumerate(texts)]

@pytest.fixture
def store(tmp_path):
    return BM25Store(index_path=str(tmp_path / "bm25_test.pkl"))


def test_bm25_keyword_match_ranks_first(store):
    store.add_documents(_chunks([
        "Le ferie annuali sono 30 giorni lavorativi.",
        "Il numero di protocollo 2024/1234 regola le trasferte.",
        "Il magazzino apre alle 8:00 dal lunedi al venerdi."
    ]), "doc1", "policy.pdf")
    results = store.search("protocollo 2024/1234")
    assert results[0]["id"] == "doc1_1"          # il chunk col codice esatto vince
    assert results[0]["bm25_score"] > results[-1]["bm25_score"]


def test_bm25_empty_store(store):
    assert store.search("qualsiasi cosa") == []


def test_bm25_delete(store):
    store.add_documents(_chunks(["documento uno", "documento due"]), "d1", "a.pdf")
    store.add_documents(_chunks(["altro testo"]), "d2", "b.pdf")
    store.delete_document("d1")
    assert all(d["document_id"] == "d2" for d in store.corpus)


def test_bm25_persistence(tmp_path):
    path = str(tmp_path / "persist.pkl")
    s1 = BM25Store(index_path=path)
    s1.add_documents(_chunks(["testo persistente segreto"]), "d9", "x.pdf")
    s2 = BM25Store(index_path=path)          # nuova istanza = reload da disco
    assert s2.search("persistente segreto")[0]["document_id"] == "d9"


# --- RRF fusion -----------------------------------------------------------

def test_rrf_merges_rankings():
    vector = [{"id": "a", "content": "A", "score": 0.8},
              {"id": "b", "content": "B", "score": 0.7}]
    bm25   = [{"id": "b", "content": "B"},
              {"id": "c", "content": "C"}]
    fused = rrf_fuse([vector, bm25], k=60)
    ids = [d["id"] for d in fused]
    assert ids[0] == "b"        # presente in entrambi -> primo
    assert set(ids) == {"a", "b", "c"}
    # 'b' e' al rank 1 (index 1) in vector e rank 0 in bm25:
    assert abs(fused[0]["rrf_score"] - (1/62 + 1/61)) < 1e-9


def test_rrf_top_n():
    r1 = [{"id": str(i), "content": f"c{i}", "score": 0.5} for i in range(20)]
    fused = rrf_fuse([r1], top_n=15)
    assert len(fused) == 15


def test_rrf_single_ranking_passthrough():
    r = [{"id": "x", "content": "X", "score": 0.9}]
    fused = rrf_fuse([r])
    assert fused[0]["id"] == "x"
