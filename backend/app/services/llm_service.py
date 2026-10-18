from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Tuple
from app.config import settings

class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0.1,
            max_tokens=800,
            num_ctx=2048
        )
        self.confidence_threshold = settings.confidence_threshold
    
    def generate_answer(self, query: str, context: List[Dict]) -> Tuple[str, float, bool]:
        if not context or len(context) == 0:
            return "Non ho trovato informazioni rilevanti nei documenti caricati.", 0.0, True
        
        # 1. Prendi il punteggio del miglior chunk (Best Match)
        confidence_scores = [doc.get("score", 0.5) for doc in context]
        max_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        # 2. Costruisci il contesto
        context_text = "\n\n---\n\n".join([doc["content"] for doc in context[:3]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sei un assistente aziendale esperto. Rispondi SOLO basandoti sui documenti forniti.
REGOLE:
1. Usa ESCLUSIVAMENTE le informazioni nei documenti.
2. Se l'informazione non c'è, rispondi ESATTAMENTE: "Non ho trovato questa informazione nei documenti disponibili".
3. Sii conciso e professionale.

Documenti:
{context}"""),
            ("human", "Domanda: {query}\n\nRispondi basandoti ESCLUSIVAMENTE sui documenti.")
        ])
        
        try:
            print(f"Generando risposta con {settings.llm_model}...")
            chain = prompt | self.llm
            response = chain.invoke({
                "context": context_text,
                "query": query
            })
            answer = response.content.strip()
            
            # 3. Controlla se l'LLM ha rifiutato di rispondere
            refusal_phrases = [
                "non ho trovato",
                "non sono sicuro",
                "non è presente",
                "non posso rispondere",
                "non disponibile",
                "nessuna informazione"
            ]
            is_filtered = any(phrase in answer.lower() for phrase in refusal_phrases)
            
            # 4. Confidence onesta: deriva dalla similarita' coseno reale
            # del best match (score = 1 - cosine distance, calcolato in chat.py).
            # Per nomic-embed-text: <~0.40 = match debole, >~0.70 = match forte.
            # Rimappiamo linearmente quel range su 0-1 e poi penalizziamo
            # la risposta se l'LLM ha dichiarato di non aver trovato nulla.
            raw_score = max_confidence
            calibrated = (raw_score - 0.40) / (0.70 - 0.40)
            calibrated = max(0.0, min(calibrated, 1.0))
            display_confidence = calibrated if not is_filtered else calibrated * 0.5
            display_confidence = round(display_confidence, 2)
            
            return answer, display_confidence, is_filtered
            
        except Exception as e:
            print(f"Errore LLM: {str(e)}")
            return f"Errore: {str(e)}", 0.0, True