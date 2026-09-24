# 🚀 Enterprise RAG Lite

Sistema di Retrieval-Augmented Generation (RAG) **100% gratuito, locale e Demo-Ready**, ottimizzato per offrire prestazioni di livello enterprise anche su hardware limitato (es. laptop con 8GB RAM).

## ✨ Caratteristiche Principali
- 🆓 **Zero Costi & 100% Locale**: Nessuna API key esterna. Tutti i dati, i documenti e i modelli rimangono sul tuo computer (Privacy-First).
- 🧠 **Ricerca Semantica Avanzata**: Utilizza il modello di embedding `nomic-embed-text` per una comprensione profonda del contesto, superando i limiti della semplice ricerca per parole chiave.
- 🛡️ **Sicurezza Enterprise (Anti-Allucinazione)**: 
  - Prompt strict che forza l'LLM a rispondere *solo* in base ai documenti forniti.
  - Sistema di "Filtraggio" attivo: se l'informazione non è presente, il sistema lo dichiara esplicitamente invece di inventare.
- 📊 **Confidence Score Calibrato**: Mostra un punteggio di affidabilità dinamico (95%+ per risposte verificate), basato sul "Best Match" semantico, proprio come i sistemi RAG professionali.
- 🚫 **Smart Upload Validation**: Il backend analizza automaticamente i file in ingresso e blocca il caricamento di report generati dal sistema stesso, prevenendo il degrado della qualità dei dati (Garbage-In-Garbage-Out).
- 📚 **Citazione delle Fonti**: Ogni risposta è collegata ai paragrafi esatti del documento originale, con punteggio di corrispondenza (Match %) visibile.

## 🛠️ Stack Tecnologico
- **Backend**: FastAPI + Python (con validazione avanzata dei dati)
- **Frontend**: Next.js 14 + React + Tailwind CSS
- **Vector Database**: ChromaDB (locale, persistente)
- **LLM**: Ollama (`llama3.2:3b` per velocità e efficienza)
- **Embeddings**: Ollama (`nomic-embed-text` per alta precisione semantica)

## 🚀 Avvio Rapido

### 1. Prerequisiti
Assicurati di avere installato:
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [Ollama](https://ollama.com/) (in esecuzione in background)

### 2. Scarica i modelli Ollama
Apri il terminale e lancia questi comandi per ottenere le ultime versioni ottimizzate:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text