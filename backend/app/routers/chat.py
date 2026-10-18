import asyncio
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.reranker_service import RerankerService
from app.config import settings

router = APIRouter()
vector_store = VectorStore()
llm_service = LLMService()
reranker = RerankerService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"Query: {request.query}")
        # 1) Retrieval ampio: prendi molti candidati col vector search
        search_results = vector_store.search(
            query=request.query,
            n_results=settings.retrieval_candidates,
            document_ids=request.document_ids
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
            reranker.rerank, request.query, candidates, settings.top_k
        )
        answer, confidence, is_filtered = await llm_service.generate_answer(request.query, context)
        sources = [
            SourceDocument(
                content=doc["content"],
                metadata=doc["metadata"],
                score=doc["score"]
            )
            for doc in context[:3]
        ]
        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            filtered=is_filtered
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
