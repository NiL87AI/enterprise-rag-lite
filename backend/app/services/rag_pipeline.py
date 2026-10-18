import asyncio
from typing import List, Optional, Dict, Tuple
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.reranker_service import RerankerService
from app.config import settings

# Singleton condivisi tra endpoint HTTP e eval script:
# stessa pipeline, stessa istanza, stesso comportamento.
vector_store = VectorStore()
llm_service = LLMService()
reranker = RerankerService()

async def run_rag(
    query: str,
    document_ids: Optional[List[str]] = None
) -> Tuple[List[Dict], str, float, bool]:
    """Pipeline RAG completa: retrieval -> rerank -> generazione.

    Ritorna (context, answer, confidence, is_filtered).
    """
    # 1) Retrieval ampio: molti candidati dal vector search
    search_results = vector_store.search(
        query=query,
        n_results=settings.retrieval_candidates,
        document_ids=document_ids
    )
    candidates = []
    if search_results and search_results['documents']:
        for i, doc in enumerate(search_results['documents'][0]):
            candidates.append({
                "content": doc,
                "metadata": search_results['metadatas'][0][i],
                "score": 1 - search_results['distances'][0][i]
            })

    # 2) Rerank: il cross-encoder riordina e tiene i top_k migliori
    context = await asyncio.to_thread(
        reranker.rerank, query, candidates, settings.top_k
    )

    # 3) Generazione con contesto rerankato
    answer, confidence, is_filtered = await llm_service.generate_answer(query, context)
    return context, answer, confidence, is_filtered
