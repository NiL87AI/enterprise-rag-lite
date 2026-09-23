from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService

router = APIRouter()
vector_store = VectorStore()
llm_service = LLMService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"Query: {request.query}")
        search_results = vector_store.search(
            query=request.query,
            n_results=3,
            document_ids=request.document_ids
        )
        context = []
        if search_results and search_results['documents']:
            for i, doc in enumerate(search_results['documents'][0]):
                context.append({
                    "content": doc,
                    "metadata": search_results['metadatas'][0][i],
                    "score": 1 - search_results['distances'][0][i]
                })
        answer, confidence, is_filtered = llm_service.generate_answer(request.query, context)
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
