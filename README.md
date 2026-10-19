# 🚀 Enterprise RAG Lite

![CI](https://github.com/NiL87AI/enterprise-rag-lite/actions/workflows/ci.yml/badge.svg)

Sistema di Retrieval-Augmented Generation (RAG) **100% gratuito, locale e Demo-Ready**, ottimizzato per offrire prestazioni di livello enterprise anche su hardware limitato (es. laptop con 8GB RAM).

## ✨ Caratteristiche Principali
- 🆓 **Zero Costi & 100% Locale**: Nessuna API key esterna. Tutti i dati, i documenti e i modelli rimangono sul tuo computer (Privacy-First).
- 🧠 **Ricerca Semantica Avanzata**: Utilizza il modello di embedding `nomic-embed-text` per una comprensione profonda del contesto, superando i limiti della semplice ricerca per parole chiave.
- 🔍 **Hybrid Search (BM25 + Semantico + RRF)**: Retrieval in due canali paralleli — BM25 per keyword/codici esatti e vector search per il significato — fusi con **Reciprocal Rank Fusion** (k=60). Copre sia query semantiche sia codici precisi (protocolli, numeri di parte), il punto debole tipico dei RAG solo-vettoriali.
- 🎯 **Reranking Cross-Encoder**: Pipeline in due stadi — il retrieval ibrido recupera 15 candidati, poi un reranker (`ms-marco-MiniLM-L-12-v2`, ONNX ottimizzato per CPU) li riordina valutando query e passaggio insieme. Aumenta sensibilmente la precisione dei top-3 senza GPU né costi.
- 🛡️ **Sicurezza Enterprise (Anti-Allucinazione)**: 
  - Prompt strict che forza l'LLM a rispondere *solo* in base ai documenti forniti.
  - Sistema di "Filtraggio" attivo: se l'informazione non è presente, il sistema lo dichiara esplicitamente invece di inventare.
- 📊 **Confidence Score Reale**: Punteggio di affidabilità derivato dalla similarità coseno del best match post-reranking (calibrato sul range effettivo del modello di embedding), dimezzato quando il sistema dichiara di non aver trovato la risposta.
- 🚫 **Smart Upload Validation**: Il backend analizza automaticamente i file in ingresso e blocca il caricamento di report generati dal sistema stesso, prevenendo il degrado della qualità dei dati (Garbage-In-Garbage-Out).
- 📚 **Citazione delle Fonti**: Ogni risposta è collegata ai paragrafi esatti del documento originale, con punteggio di corrispondenza (Match %) visibile.
- 🧪 **Eval Harness Integrato**: Script in `backend/eval/` che misura su dataset reale *answer accuracy*, *retrieval hit rate* e *refusal accuracy* (domande trappola). Genera report JSON + Markdown: le metriche sono misurate, non dichiarate.

## 🛠️ Stack Tecnologico
- **Backend**: FastAPI + Python (con validazione avanzata dei dati)
- **Frontend**: Next.js 14 + React + Tailwind CSS
- **Vector Database**: ChromaDB (locale, persistente)
- **Keyword Search**: BM25 (`rank_bm25`) + Reciprocal Rank Fusion
- **Reranker**: FlashRank `ms-marco-MiniLM-L-12-v2` (cross-encoder ONNX, CPU)
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
```

### 3. Avvia il Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Su Windows: venv\Scripts\activate | Su macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Il backend sarà attivo su `http://localhost:8000` (documentazione interattiva su `http://localhost:8000/docs`).

### 4. Avvia il Frontend (Next.js)
In un secondo terminale:
```bash
cd frontend
npm install
npm run dev
```
Apri `http://localhost:3000` nel browser, carica un PDF dalla barra laterale e inizia a fare domande.

## 🧪 Test & Valutazione (Eval Harness)

### Unit & Integration Tests
La suite di test copre API, chunking PDF, hybrid search (BM25 + RRF), calibrazione del confidence e rilevamento dei rifiuti (senza richiedere Ollama attivo):
```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

### Evaluation End-to-End
Con Ollama in esecuzione e i documenti di test caricati, puoi misurare **answer accuracy**, **retrieval hit rate** e **refusal accuracy** sul dataset di valutazione:
```bash
cd backend
python -m eval.run_eval
```
Lo script stampa il riepilogo a terminale e genera `backend/eval/eval_report.json` e `backend/eval/eval_report.md`.

