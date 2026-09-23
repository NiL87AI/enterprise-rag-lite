# 🚀 Enterprise RAG Lite

Sistema di Retrieval-Augmented Generation (RAG) **100% gratuito e locale**, ottimizzato per funzionare anche su hardware limitato (es. laptop con 8GB RAM e CPU integrata).

## ✨ Caratteristiche
- 🆓 **Zero costi**: Nessuna API key di OpenAI o servizi a pagamento.
- 🔒 **Privacy-First**: Tutti i dati, i documenti e i modelli rimangono sul tuo computer.
- 💻 **Hardware Friendly**: Funziona su macchine con risorse limitate grazie a modelli ottimizzati.
- 🛡️ **Anti-Allucinazione**: Filtri di sicurezza (prompt strict + confidence score) per rispondere solo in base ai documenti caricati.
- 📚 **Citazione Fonti**: Ogni risposta mostra i paragrafi esatti del PDF da cui è stata estratta l'informazione.
- 💾 **Cronologia & Export**: Salvataggio automatico delle conversazioni ed esportazione in PDF.

## 🛠️ Stack Tecnologico
- **Backend**: FastAPI + Python
- **Frontend**: Next.js 14 + React + Tailwind CSS
- **Vector Database**: ChromaDB (locale)
- **LLM**: Ollama (`llama3.2:3b`)
- **Embeddings**: Ollama (`all-minilm`)

## 🚀 Avvio Rapido

### 1. Prerequisiti
Assicurati di avere installato:
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [Ollama](https://ollama.com/) (in esecuzione in background)

### 2. Scarica i modelli Ollama
Apri il terminale e lancia:
```bash
ollama pull llama3.2:3b
ollama pull all-minilm