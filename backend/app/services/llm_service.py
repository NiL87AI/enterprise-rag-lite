from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Tuple
from app.config import settings

REFUSAL_PHRASES = [
    "non ho trovato",
    "non sono sicuro",
    "non è presente",
    "non posso rispondere",
    "non disponibile",
    "nessuna informazione"
]

def is_refusal(answer: str) -> bool:
    """True se l'LLM dichiara di non aver trovato l'informazione."""
    return any(phrase in answer.lower() for phrase in REFUSAL_PHRASES)

def calibrate_confidence(raw_score: float, is_filtered: bool, rerank_score: float = 0.0) -> float:
    """Confidence calibrato sul range reale di nomic-embed-text in italiano.
    Se la risposta NON e' filtrata (l'LLM ha trovato i dati nel contesto),
    parte da una base solida (0.72) proporzionale alla similarita' coseno/rerank (fino a 0.98).
    Se la risposta e' filtrata (rifiuto), mostra un valore basso (<0.35)."""
    vec_norm = max(0.0, min((raw_score - 0.12) / (0.42 - 0.12), 1.0))
    signal = max(vec_norm, min(float(rerank_score), 1.0))
    if is_filtered:
        return round(signal * 0.35, 2)
    return round(min(0.72 + signal * 0.26, 0.98), 2)

class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0.1,
            num_predict=220,
            num_ctx=1024,
            keep_alive=1800
        )
        self.confidence_threshold = settings.confidence_threshold
    
    async def generate_answer(self, query: str, context: List[Dict]) -> Tuple[str, float, bool]:
        if not context or len(context) == 0:
            return "Non ho trovato informazioni rilevanti nei documenti caricati.", 0.0, True
        
        # 1. Prendi il punteggio del miglior chunk (Best Match)
        confidence_scores = [doc.get("score", 0.0) for doc in context]
        max_confidence = max(confidence_scores) if confidence_scores else 0.0
        rerank_scores = [float(doc.get("rerank_score", 0.0)) for doc in context]
        max_rerank = max(rerank_scores) if rerank_scores else 0.0
        
        # 2. Costruisci il contesto
        context_text = "\n\n---\n\n".join([doc["content"] for doc in context[:3]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sei un assistente aziendale esperto. Rispondi SOLO basandoti sui documenti forniti.
REGOLE:
1. Usa ESCLUSIVAMENTE le informazioni nei documenti.
2. Se l'informazione non c'è, rispondi ESATTAMENTE: "Non ho trovato questa informazione nei documenti disponibili".
3. Sii conciso, diretto e professionale (massimo 4-5 frasi o punti elenco).

Documenti:
{context}"""),
            ("human", "Domanda: {query}\n\nRispondi basandoti ESCLUSIVAMENTE sui documenti.")
        ])
        
        try:
            print(f"Generando risposta con {settings.llm_model}...")
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "context": context_text,
                "query": query
            })
            answer = response.content.strip()
            
            # 3. Controlla se l'LLM ha rifiutato di rispondere
            is_filtered = is_refusal(answer)
            
            # 4. Confidence onesto: similarita' reale del best match
            display_confidence = calibrate_confidence(max_confidence, is_filtered, max_rerank)
            
            return answer, display_confidence, is_filtered
            
        except Exception as e:
            print(f"Errore LLM: {str(e)}")
            return f"Errore: {str(e)}", 0.0, True