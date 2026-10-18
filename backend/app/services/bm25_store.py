import pickle
from pathlib import Path
from typing import List, Dict
from app.config import settings


def _tokenize(text: str) -> List[str]:
    return text.lower().split()


class BM25Store:
    """Indice BM25 parallelo a ChromaDB per l'hybrid search.

    Persiste il corpus come pickle accanto al DB vettoriale e ricostruisce
    l'indice BM25Okapi ad ogni ingestion/delete (operazione veloce per
    corpora di dimensioni tipiche di questo progetto).
    """

    def __init__(self, index_path: str = "./chroma_db/bm25_corpus.pkl"):
        self.index_path = Path(index_path)
        self.corpus: List[Dict] = []   # {id, content, metadata, document_id}
        self._bm25 = None
        self._load()

    def _load(self):
        if self.index_path.exists():
            self.corpus = pickle.loads(self.index_path.read_bytes())
            self._rebuild()

    def _save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_bytes(pickle.dumps(self.corpus))

    def _rebuild(self):
        if self.corpus:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi([_tokenize(d["content"]) for d in self.corpus])
        else:
            self._bm25 = None

    def add_documents(self, chunks: List[Dict], document_id: str, filename: str):
        for chunk in chunks:
            self.corpus.append({
                "id": f"{document_id}_{chunk['metadata']['chunk_index']}",
                "content": chunk["content"],
                "metadata": {**chunk["metadata"],
                             "document_id": document_id, "filename": filename},
                "document_id": document_id,
            })
        self._rebuild()
        self._save()

    def search(self, query: str, n_results: int = 15,
               document_ids: List[str] = None) -> List[Dict]:
        """Ritorna i doc ordinati per score BM25 (decrescente)."""
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        out = []
        for i in ranked:
            doc = self.corpus[i]
            if document_ids and doc["document_id"] not in document_ids:
                continue
            out.append({**doc, "bm25_score": float(scores[i])})
            if len(out) >= n_results:
                break
        return out

    def delete_document(self, document_id: str):
        self.corpus = [d for d in self.corpus if d["document_id"] != document_id]
        self._rebuild()
        self._save()


def rrf_fuse(rankings: List[List[Dict]], k: int = None, top_n: int = 15) -> List[Dict]:
    """Reciprocal Rank Fusion: score(d) = sum_i 1 / (k + rank_i(d)).

    Fonde piu' ranking (es. BM25 + vettoriale) in un'unica lista ordinata.
    I documenti sono identificati dalla chiave 'id'.
    """
    k = k or settings.rrf_k
    scores, by_id = {}, {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            by_id.setdefault(doc_id, doc)
    fused = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return [{**by_id[doc_id], "rrf_score": s} for doc_id, s in fused]


# Singleton condiviso: documents.py (ingestion) e rag_pipeline.py (search)
# usano la STESSA istanza, cosi' i documenti appena caricati sono subito
# ricercabili senza riavvio.
bm25_store = BM25Store()
