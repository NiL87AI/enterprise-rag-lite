from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import VectorStore
from app.config import settings
import uuid

router = APIRouter()
pdf_processor = PDFProcessor(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
vector_store = VectorStore()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo PDF supportati")
    try:
        print(f"Processamento {file.filename}...")
        content = await file.read()
        text = pdf_processor.extract_text(content)
        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF senza testo")
        chunks = pdf_processor.split_into_chunks(text)
        print(f"Diviso in {len(chunks)} chunk")
        document_id = str(uuid.uuid4())
        vector_store.add_documents(chunks, document_id, file.filename)
        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    try:
        print(f"Eliminazione documento ID: {document_id}")
        vector_store.delete_document(document_id)
        return {"status": "success", "message": f"Documento {document_id} eliminato"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
