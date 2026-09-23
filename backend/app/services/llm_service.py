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
        
        confidence_scores = [doc.get("score", 0.5) for doc in context]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        if avg_confidence < self.confidence_threshold:
            return "Non sono sicuro di poter rispondere accuratamente.", avg_confidence, True
        
        context_text = "\n\n---\n\n".join([doc["content"] for doc in context[:3]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sei un assistente aziendale. Rispondi SOLO basandoti sui documenti forniti.
REGOLE:
1. Usa ESCLUSIVAMENTE le informazioni nei documenti
2. Se l'informazione non c'e, rispondi: "Non ho trovato questa informazione nei documenti disponibili"
3. Cita le fonti quando possibile
4. NON inventare mai nulla
5. Sii conciso

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
            answer = response.content
            
            refusal_phrases = [
                "non ho trovato",
                "non sono sicuro",
                "non e presente",
                "non posso rispondere",
                "non disponibile",
                "nessuna informazione"
            ]
            is_filtered = any(phrase in answer.lower() for phrase in refusal_phrases)
            
            return answer, avg_confidence, is_filtered
            
        except Exception as e:
            print(f"Errore LLM: {str(e)}")
            return f"Errore: {str(e)}", 0.0, True