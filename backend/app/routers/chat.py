import asyncio
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.rag_pipeline import run_rag

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"Query: {request.query}")
        context, answer, confidence, is_filtered = await run_rag(
            request.query, request.document_ids
        )
        sources = [
            SourceDocument(
                content=doc["content"],
                metadata=doc["metadata"],
                score=doc["score"]
            )
            for doc in context
        ]
        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            filtered=is_filtered
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
