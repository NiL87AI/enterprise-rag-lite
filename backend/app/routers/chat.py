import asyncio
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.rag_pipeline import run_rag
from app.services.llm_service import calibrate_confidence

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
                score=calibrate_confidence(
                    doc.get("score", 0.0),
                    False,
                    float(doc.get("rerank_score", 0.0))
                )
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
