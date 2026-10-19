import asyncio
from typing import List, Optional, Dict, Tuple
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.reranker_service import RerankerService
from app.services.bm25_store import bm25_store, rrf_fuse
from app.config import settings

# Singleton condivisi tra endpoint HTTP ed eval script:
# stessa pipeline, stessa istanza, stesso comportamento.
vector_store = VectorStore()
llm_service = LLMService()
reranker = RerankerService()


def retrieve_candidates(query: str, document_ids: Optional[List[str]] = None) -> List[Dict]:
    """Retrieval ibrido: BM25 (keyword) + vector search (semantico)
    fusi con Reciprocal Rank Fusion. Se HYBRID_SEARCH_ENABLED=false
    usa solo il vector search (backward compatible)."""
    # Vector search (sempre attivo)
    search_results = vector_store.search(
        query=query,
        n_results=settings.retrieval_candidates,
        document_ids=document_ids
    )
    vector_ranking = []
    if search_results and search_results['documents']:
        for i, doc in enumerate(search_results['documents'][0]):
            vector_ranking.append({
                "id": search_results['ids'][0][i],
                "content": doc,
                "metadata": search_results['metadatas'][0][i],
                "score": 1 - search_results['distances'][0][i]
            })

    if not settings.hybrid_search_enabled:
        fused = vector_ranking
    else:
        # BM25 search (keyword) + fusione RRF
        bm25_ranking = bm25_store.search(
            query,
            n_results=settings.retrieval_candidates,
            document_ids=document_ids
        )
        # I doc fusi via RRF prendono 'score' dal ranking vettoriale quando
        # disponibile (serve per il confidence), altrimenti 0.
        fused = rrf_fuse([vector_ranking, bm25_ranking],
                         top_n=settings.retrieval_candidates)

    # Deduplica chunk con contenuto identico (es. stesso PDF caricato piu' volte)
    seen_contents = set()
    unique_candidates = []
    for doc in fused:
        norm = doc["content"].strip()
        if norm not in seen_contents:
            seen_contents.add(norm)
            unique_candidates.append(doc)
    return unique_candidates


async def run_rag(
    query: str,
    document_ids: Optional[List[str]] = None
) -> Tuple[List[Dict], str, float, bool]:
    """Pipeline RAG completa: hybrid retrieval -> rerank -> generazione.

    Ritorna (context, answer, confidence, is_filtered).
    """
    candidates = retrieve_candidates(query, document_ids)

    # Rerank: il cross-encoder riordina e tiene i top_k migliori
    context = await asyncio.to_thread(
        reranker.rerank, query, candidates, settings.top_k
    )

    # Generazione con contesto rerankato
    answer, confidence, is_filtered = await llm_service.generate_answer(query, context)
    return context, answer, confidence, is_filtered
