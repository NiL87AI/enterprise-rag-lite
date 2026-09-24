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
    # Controllo base: solo PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo file PDF supportati.")
    
    # 🛡️ CONTROLLO 1: Blocca i file con nome tipico dei report RAG
    if "conversazione-rag-" in file.filename.lower() or "report" in file.filename.lower():
        raise HTTPException(
            status_code=400, 
            detail="⚠️ Sembra che tu stia caricando un report generato dal sistema RAG. Per favore, carica il documento ORIGINALE (es. il CV, un manuale, ecc.)."
        )

    try:
        print(f"Processamento {file.filename}...")
        content = await file.read()
        text = pdf_processor.extract_text(content)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Il PDF non contiene testo estraibile.")
        
        # 🛡️ CONTROLLO 2: Blocca se il contenuto inizia con le firme tipiche del report RAG
        red_flags = [
            "enterprise rag- report conversazione",
            "generato da enterprise rag lite",
            "documenti analizzati:"
        ]
        text_preview = text[:500].lower()  # Controlla solo le prime 500 battute per efficienza
        
        if any(flag in text_preview for flag in red_flags):
            raise HTTPException(
                status_code=400, 
                detail="⚠️ Il contenuto del file sembra essere un report generato da Enterprise RAG Lite. Carica il documento originale."
            )

        chunks = pdf_processor.split_into_chunks(text)
        print(f"Diviso in {len(chunks)} chunk")
        document_id = str(uuid.uuid4())
        vector_store.add_documents(chunks, document_id, file.filename)
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_chunks": len(chunks)
        }
    except HTTPException:
        raise  # Rilancia le eccezioni HTTP già gestite (come quelle qui sopra)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    try:
        print(f"Eliminazione documento ID: {document_id}")
        vector_store.delete_document(document_id)
        return {"status": "success", "message": f"Documento {document_id} eliminato"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))