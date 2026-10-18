from typing import List, Dict
from app.config import settings

class RerankerService:
    """Reranker cross-encoder leggero (ONNX, ottimizzato per CPU).

    Il retrieval vettoriale e' veloce ma grossolano: riordina i candidati
    con un modello cross-encoder che valuta query+passaggio insieme.
    Se flashrank non e' disponibile, degrada in modo pulito al
    ranking vettoriale originale.
    """

    def __init__(self):
        self.ranker = None
        if settings.reranker_enabled:
            try:
                from flashrank import Ranker
                self.ranker = Ranker(model_name=settings.reranker_model)
                print(f"Reranker attivo: {settings.reranker_model}")
            except Exception as e:
                print(f"Reranker disabilitato ({e}), uso ranking vettoriale")

    def rerank(self, query: str, docs: List[Dict], top_k: int) -> List[Dict]:
        if not self.ranker or not docs:
            return docs[:top_k]
        from flashrank import RerankRequest
        passages = [
            {"id": i, "text": d["content"], "meta": d.get("metadata", {})}
            for i, d in enumerate(docs)
        ]
        results = self.ranker.rerank(RerankRequest(query=query, passages=passages))
        ranked = []
        for r in results[:top_k]:
            doc = dict(docs[r["id"]])
            doc["rerank_score"] = r["score"]
            ranked.append(doc)
        return ranked
