'use client';

import { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, Trash2, Loader2, Bot, User, Layers, HelpCircle, Sparkles, Plus, MessageSquare, Download, Calendar } from 'lucide-react';
import axios from 'axios';
import { jsPDF } from 'jspdf';

interface Source {
  content: string;
  metadata: any;
  score: number;
}

interface ChatResponse {
  answer: string;
  sources: Source[];
  confidence: number;
  filtered: boolean;
}

interface Message {
  sender: 'user' | 'ai';
  text: string;
  sources?: Source[];
  confidence?: number;
  filtered?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  messages: Message[];
  documents: Array<{id: string, filename: string}>;
}

const STORAGE_KEY = 'rag_conversations';

export default function Home() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{id: string, filename: string}>>([]);
  const [uploading, setUploading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConvId, setCurrentConvId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Carica conversazioni da localStorage all'avvio
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setConversations(parsed);
        if (parsed.length > 0) {
          loadConversation(parsed[0].id, parsed);
        }
      }
    } catch (e) {
      console.error('Errore caricamento cronologia:', e);
    }
  }, []);

  // Salva conversazioni su localStorage quando cambiano i messaggi
  useEffect(() => {
    if (messages.length === 0 && !currentConvId) return;
    
    const convId = currentConvId || crypto.randomUUID();
    const title = messages.find(m => m.sender === 'user')?.text.slice(0, 50) || 'Nuova conversazione';
    
    const newConv: Conversation = {
      id: convId,
      title: title + (title.length >= 50 ? '...' : ''),
      createdAt: new Date().toISOString(),
      messages: messages,
      documents: uploadedFiles
    };

    setConversations(prev => {
      const existing = prev.findIndex(c => c.id === convId);
      let updated;
      if (existing >= 0) {
        updated = [...prev];
        updated[existing] = newConv;
      } else {
        updated = [newConv, ...prev];
      }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Errore salvataggio:', e);
      }
      return updated;
    });

    if (!currentConvId) {
      setCurrentConvId(convId);
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = (convId: string, convList?: Conversation[]) => {
    const list = convList || conversations;
    const conv = list.find(c => c.id === convId);
    if (conv) {
      setMessages(conv.messages);
      setUploadedFiles(conv.documents || []);
      setCurrentConvId(conv.id);
    }
  };

  const newConversation = () => {
    setMessages([]);
    setUploadedFiles([]);
    setCurrentConvId(null);
    setQuery('');
  };

  const deleteConversation = (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Eliminare questa conversazione?')) return;
    
    const updated = conversations.filter(c => c.id !== convId);
    setConversations(updated);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.error('Errore eliminazione:', e);
    }
    
    if (currentConvId === convId) {
      newConversation();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_URL}/api/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadedFiles([...uploadedFiles, { id: res.data.document_id, filename: file.name }]);
    } catch (error) {
      alert('Errore nel caricamento del file.');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim() || loading) return;
    const userQuery = query;
    setQuery('');
    setLoading(true);
    setMessages(prev => [...prev, { sender: 'user', text: userQuery }]);

    try {
      const res = await axios.post(`${API_URL}/api/chat`, {
        query: userQuery,
        document_ids: uploadedFiles.map(f => f.id)
      });
      const data: ChatResponse = res.data;
      setMessages(prev => [...prev, { 
        sender: 'ai', 
        text: data.answer,
        sources: data.sources,
        confidence: data.confidence,
        filtered: data.filtered
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        sender: 'ai', 
        text: 'Errore durante l\'elaborazione. Verifica che il backend sia attivo.' 
      }]);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await axios.delete(`${API_URL}/api/documents/${docId}`);
      setUploadedFiles(uploadedFiles.filter(f => f.id !== docId));
    } catch (error) {
      alert('Impossibile eliminare il documento.');
    }
  };

  const exportToPDF = () => {
    if (messages.length === 0) {
      alert('Nessun messaggio da esportare.');
      return;
    }

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 15;
    const maxWidth = pageWidth - margin * 2;
    let y = 20;

    // Titolo
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('Enterprise RAG - Report Conversazione', margin, y);
    y += 10;

    // Data
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(100);
    const date = new Date().toLocaleString('it-IT');
    doc.text(`Generato il: ${date}`, margin, y);
    y += 8;

    // Documenti analizzati
    if (uploadedFiles.length > 0) {
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(0);
      doc.text('Documenti analizzati:', margin, y);
      y += 6;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      uploadedFiles.forEach(f => {
        doc.text(`• ${f.filename}`, margin + 3, y);
        y += 5;
      });
      y += 3;
    }

    // Linea divisoria
    doc.setDrawColor(200);
    doc.line(margin, y, pageWidth - margin, y);
    y += 10;

    // Messaggi
    messages.forEach((msg) => {
      if (y > 270) {
        doc.addPage();
        y = 20;
      }

      if (msg.sender === 'user') {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(30, 64, 175);
        doc.text('TU', margin, y);
        y += 5;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(0);
        const lines = doc.splitTextToSize(msg.text, maxWidth);
        doc.text(lines, margin, y);
        y += lines.length * 5 + 6;
      } else {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(79, 70, 229);
        doc.text('ASSISTENTE AI', margin, y);
        if (msg.confidence !== undefined) {
          doc.setFontSize(9);
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(100);
          doc.text(`(Confidence: ${(msg.confidence * 100).toFixed(0)}%${msg.filtered ? ' - FILTRATO' : ''})`, margin + 35, y);
        }
        y += 5;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(0);
        const lines = doc.splitTextToSize(msg.text, maxWidth);
        doc.text(lines, margin, y);
        y += lines.length * 5 + 3;

        // Fonti
        if (msg.sources && msg.sources.length > 0) {
          doc.setFontSize(9);
          doc.setFont('helvetica', 'italic');
          doc.setTextColor(80);
          doc.text('Fonti:', margin + 3, y);
          y += 4;
          msg.sources.forEach((src, idx) => {
            if (y > 270) {
              doc.addPage();
              y = 20;
            }
            const srcText = `[${idx + 1}] (Match: ${(src.score * 100).toFixed(0)}%) "${src.content.slice(0, 200)}${src.content.length > 200 ? '...' : ''}"`;
            const srcLines = doc.splitTextToSize(srcText, maxWidth - 6);
            doc.text(srcLines, margin + 6, y);
            y += srcLines.length * 4 + 2;
          });
          y += 3;
        }
        y += 3;
      }
    });

    // Footer su ogni pagina
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(
        `Pagina ${i} di ${totalPages} - Generato da Enterprise RAG Lite`,
        pageWidth / 2,
        doc.internal.pageSize.getHeight() - 10,
        { align: 'center' }
      );
    }

    doc.save(`conversazione-rag-${Date.now()}.pdf`);
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Adesso';
    if (mins < 60) return `${mins} min fa`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} ore fa`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} giorni fa`;
    return d.toLocaleDateString('it-IT');
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800 antialiased overflow-hidden">
      
      {/* SIDEBAR SINISTRA */}
      <aside className="w-80 bg-slate-900 text-slate-200 flex flex-col border-r border-slate-800 shrink-0">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-2 text-indigo-400 mb-1">
            <Layers className="w-6 h-6" />
            <span className="font-bold text-lg tracking-wider text-white">RAG ENTERPRISE</span>
          </div>
          <p className="text-xs text-slate-400">Ambiente di Analisi Locale protetto</p>
        </div>

        {/* Bottone Nuova Conversazione */}
        <div className="p-4 border-b border-slate-800">
          <button
            onClick={newConversation}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuova Conversazione
          </button>
        </div>

        {/* Cronologia Conversazioni */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1 min-h-0">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest px-2 mb-3 flex items-center gap-1.5">
            <MessageSquare className="w-3 h-3" /> Cronologia
          </h3>
          {conversations.length === 0 ? (
            <div className="text-center py-6 text-slate-600">
              <p className="text-xs">Nessuna conversazione</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`group flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${
                  currentConvId === conv.id 
                    ? 'bg-indigo-600/20 border border-indigo-500/50' 
                    : 'hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-slate-200 truncate font-medium">{conv.title}</p>
                  <p className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                    <Calendar className="w-2.5 h-2.5" />
                    {formatDate(conv.createdAt)} • {conv.messages.length} msg
                  </p>
                </div>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="text-slate-500 hover:text-rose-400 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Elimina"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Area Upload */}
        <div className="p-4 border-t border-b border-slate-800">
          <label className="block group">
            <div className="border-2 border-dashed border-slate-700 group-hover:border-indigo-500 rounded-xl p-4 text-center cursor-pointer bg-slate-800/40 hover:bg-slate-800 transition-all duration-200">
              {uploading ? (
                <Loader2 className="w-5 h-5 mx-auto mb-1 text-indigo-400 animate-spin" />
              ) : (
                <Upload className="w-5 h-5 mx-auto mb-1 text-slate-400 group-hover:text-indigo-400 transition-colors" />
              )}
              <span className="block text-xs font-semibold text-slate-300">
                {uploading ? 'Elaborazione...' : 'Carica PDF'}
              </span>
            </div>
            <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" disabled={uploading || loading} />
          </label>

          {uploadedFiles.length > 0 && (
            <div className="mt-3 space-y-1.5">
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-1">Documenti Attivi</h3>
              {uploadedFiles.map((file) => (
                <div key={file.id} className="flex items-center justify-between bg-slate-800/60 p-2 rounded-lg border border-slate-700/50 group">
                  <div className="flex items-center gap-1.5 truncate pr-1">
                    <FileText className="w-3 h-3 text-indigo-400 shrink-0" />
                    <span className="text-[10px] text-slate-300 truncate">{file.filename}</span>
                  </div>
                  <button onClick={() => handleDelete(file.id)} className="text-slate-500 hover:text-rose-400 p-0.5 opacity-0 group-hover:opacity-100">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-3 bg-slate-950 text-[10px] text-slate-500 flex items-center justify-between">
          <span>Stato: <strong className="text-emerald-400">Online</strong></span>
          <span>100% Privato</span>
        </div>
      </aside>

      {/* AREA CENTRALE */}
      <main className="flex-1 flex flex-col h-full bg-white relative">
        
        <header className="h-16 border-b border-slate-100 px-8 flex items-center justify-between shrink-0 bg-white/80 backdrop-blur-md sticky top-0 z-10">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Spazio di Lavoro Dinamico</h2>
            <p className="text-[11px] text-slate-500">I dati non vengono trasmessi a server terzi</p>
          </div>
          <button
            onClick={exportToPDF}
            disabled={messages.length === 0}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
            title="Esporta conversazione in PDF"
          >
            <Download className="w-4 h-4" />
            Esporta PDF
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-indigo-200">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-2">Benvenuto in RAG Enterprise</h1>
              <p className="text-slate-500 text-sm leading-relaxed">
                Carica i tuoi documenti nella barra laterale e inizia a fare domande. 
                L&apos;AI risponderà <strong>esclusivamente</strong> in base al contenuto dei tuoi file.
              </p>
              <div className="mt-6 flex gap-3 text-[11px] text-slate-500">
                <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> Cronologia salvata</span>
                <span className="flex items-center gap-1"><Download className="w-3 h-3" /> Export PDF</span>
              </div>
            </div>
          )}

          {messages.map((msg, index) => (
            <div key={index} className={`flex gap-4 max-w-3xl mx-auto ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.sender === 'ai' && (
                <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-indigo-600" />
                </div>
              )}

              <div className="flex flex-col space-y-2 max-w-[85%]">
                <div className={`p-4 rounded-2xl shadow-sm text-sm leading-relaxed border ${
                  msg.sender === 'user' 
                    ? 'bg-indigo-600 text-white border-indigo-700 rounded-br-none' 
                    : 'bg-slate-50 text-slate-800 border-slate-100 rounded-bl-none'
                }`}>
                  <p className="whitespace-pre-line">{msg.text}</p>
                  
                  {msg.sender === 'ai' && msg.confidence !== undefined && (
                    <div className="mt-3 pt-3 border-t border-slate-200 flex items-center gap-2 text-[10px]">
                      <span className="text-slate-500 font-medium">Confidence:</span>
                      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden max-w-[100px]">
                        <div 
                          className={`h-full rounded-full ${
                            msg.confidence > 0.7 ? 'bg-emerald-500' : 
                            msg.confidence > 0.5 ? 'bg-yellow-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${msg.confidence * 100}%` }}
                        />
                      </div>
                      <span className={`font-bold ${
                        msg.confidence > 0.7 ? 'text-emerald-600' : 
                        msg.confidence > 0.5 ? 'text-yellow-600' : 'text-rose-600'
                      }`}>
                        {(msg.confidence * 100).toFixed(0)}%
                      </span>
                      {msg.filtered && (
                        <span className="bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase">
                          Filtrato
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                  <div className="pl-1 pt-1">
                    <details className="group border border-slate-100 rounded-xl bg-slate-50/50 overflow-hidden transition-all duration-200">
                      <summary className="list-none flex items-center justify-between p-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100/50 select-none">
                        <span className="flex items-center gap-1.5"><HelpCircle className="w-3.5 h-3.5 text-indigo-500" /> Fonti</span>
                        <span className="text-[10px] bg-slate-200/70 group-open:bg-slate-200 px-2 py-0.5 rounded-full transition-colors">{msg.sources.length} blocchi</span>
                      </summary>
                      <div className="p-3 pt-1 border-t border-slate-100 space-y-2 bg-white">
                        {msg.sources.map((src, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-100">
                            <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 mb-1.5 uppercase">
                              <span>Riferimento {idx + 1}</span>
                              <span className="bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded text-[9px]">Match: {(src.score * 100).toFixed(0)}%</span>
                            </div>
                            <p className="italic leading-relaxed">&ldquo;{src.content}&rdquo;</p>
                            {src.metadata?.filename && (
                              <p className="mt-2 text-[10px] text-slate-400 flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {src.metadata.filename}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-4 max-w-3xl mx-auto justify-start">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-xs text-slate-500 ml-2">Analisi in corso...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-slate-100 p-4 bg-white shrink-0">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-2 items-center bg-slate-50 border border-slate-200 rounded-2xl p-2 focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={uploadedFiles.length === 0 ? "Carica prima un PDF per iniziare..." : "Chiedi qualcosa sui tuoi documenti..."}
                className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none disabled:opacity-50"
                disabled={loading || uploadedFiles.length === 0}
              />
              <button
                onClick={handleQuery}
                disabled={loading || !query.trim() || uploadedFiles.length === 0}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-xl p-2.5 transition-all duration-200 shrink-0"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[10px] text-slate-400 text-center mt-2">
              Powered by Llama 3.2 (Locale) • Zero dati condivisi
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}