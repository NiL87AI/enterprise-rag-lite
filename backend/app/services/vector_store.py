import chromadb
from langchain_ollama import OllamaEmbeddings
from typing import List, Dict, Optional
from app.config import settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embeddings = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, chunks: List[Dict], document_id: str, filename: str):
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        documents = [chunk["content"] for chunk in chunks]
        print(f"Generando embeddings per {len(documents)} chunk...")
        embeddings = self.embeddings.embed_documents(documents)
        metadatas = [
            {
                **chunk["metadata"],
                "document_id": document_id,
                "filename": filename
            }
            for chunk in chunks
        ]
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"OK: {len(chunks)} chunk salvati")
    
    def search(self, query: str, n_results: int = 3, document_ids: Optional[List[str]] = None):
        query_embedding = self.embeddings.embed_query(query)
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )
        return results
    
    def delete_document(self, document_id: str):
        self.collection.delete(where={"document_id": document_id})
