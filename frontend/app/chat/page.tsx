'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, Loader2, Zap, CheckCircle2, AlertCircle, Home, Wifi, WifiOff } from 'lucide-react';
import Link from 'next/link';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000/api/v1' : '/api/v1');

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'streaming' | 'done' | 'error';
  metadata?: {
    tasks_created?: number[];
    actions_taken?: string[];
  };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hola, soy el Orquestador de Qubot. Dime qué necesitas y crearé y asignaré tareas a tus agentes automáticamente.',
      timestamp: new Date(),
      status: 'done',
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const testConnection = async () => {
      try {
        const res = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });
        if (res.ok) {
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('error');
        }
      } catch {
        setConnectionStatus('error');
      }
    };
    testConnection();
    const interval = setInterval(testConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setInput('');
    setIsStreaming(true);
    setStatusText('Analizando solicitud...');

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
      status: 'done',
    };

    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: 'assistant', content: '', timestamp: new Date(), status: 'streaming' },
    ]);

    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

    try {
      const res = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || `HTTP ${res.status}`);
      }

      if (!res.body) throw new Error('No response body from server');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processBlock = (block: string) => {
        if (!block.trim()) return;
        let eventType = 'message';
        let dataStr = '';
        for (const line of block.split('\n')) {
          if (line.startsWith('event: ')) eventType = line.slice(7).trim();
          else if (line.startsWith('data: ')) dataStr = line.slice(6).trim();
        }
        if (!dataStr) return;

        let payload: unknown;
        try { payload = JSON.parse(dataStr); } catch { return; }

        switch (eventType) {
          case 'status':
            setStatusText((payload as { text: string }).text ?? '');
            break;
          case 'token':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + (payload as { text: string }).text }
                  : m,
              ),
            );
            break;
          case 'done': {
            const d = payload as { tasks_created?: number[]; actions_taken?: string[] };
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, status: 'done', metadata: { tasks_created: d.tasks_created, actions_taken: d.actions_taken } }
                  : m,
              ),
            );
            setStatusText('');
            break;
          }
          case 'error':
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: (payload as { message: string }).message, status: 'error' }
                  : m,
              ),
            );
            setStatusText('');
            break;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() ?? '';
        for (const block of blocks) processBlock(block);
      }
      if (buffer.trim()) processBlock(buffer);

      // Ensure message is marked done if no 'done' event arrived
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId && m.status === 'streaming' ? { ...m, status: 'done' } : m)),
      );
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;
      
      let friendlyMsg = 'Algo salió mal. Por favor, inténtalo de nuevo.';
      const msg = err instanceof Error ? err.message : 'Error desconocido';
      
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
        friendlyMsg = 'No se puede conectar al servidor. Verifica tu conexión a internet.';
      } else if (msg.includes('401') || msg.includes('Unauthorized')) {
        friendlyMsg = 'Tu sesión expiró. Por favor, inicia sesión de nuevo.';
      } else if (msg.includes('403') || msg.includes('Forbidden')) {
        friendlyMsg = 'No tienes permiso para realizar esta acción.';
      } else if (msg.includes('429') || msg.includes('Too Many')) {
        friendlyMsg = 'Demasiadas solicitudes. Espera un momento e intenta de nuevo.';
      } else if (msg.includes('500') || msg.includes('Internal Server')) {
        friendlyMsg = 'Error del servidor. Intenta de nuevo en unos minutos.';
      } else if (msg.includes('503') || msg.includes('Service Unavailable')) {
        friendlyMsg = 'Servicio temporalmente no disponible. Intenta de nuevo en unos minutos.';
      }
      
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: friendlyMsg, status: 'error' } : m,
        ),
      );
    } finally {
      setIsStreaming(false);
      setStatusText('');
    }
  }, [input, isStreaming]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-200 relative overflow-hidden">
      <div className="absolute top-0 right-1/4 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-purple-600/8 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <div className="flex-none px-6 py-4 border-b border-white/5 z-10 bg-slate-950/70 backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-blue-500/30 flex items-center justify-center">
              <Bot className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Orquestador</h1>
              <p className="text-xs text-slate-400 flex items-center gap-1.5">
                {connectionStatus === 'connected' ? (
                  <Wifi className="w-3 h-3 text-emerald-500" />
                ) : connectionStatus === 'error' ? (
                  <WifiOff className="w-3 h-3 text-red-500" />
                ) : (
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                )}
                {isStreaming ? statusText || 'Procesando...' : 'Listo'}
              </p>
            </div>
          </div>
          
          <Link href="/dashboard" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors bg-slate-800/50 border border-white/10 hover:bg-slate-700/50 text-slate-300">
            <Home className="w-3.5 h-3.5" />
            Office
          </Link>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 z-10">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isStreaming && statusText && (
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/5 border border-blue-500/10 rounded-lg w-fit">
            <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
            <span className="text-xs text-blue-300">{statusText}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-none px-4 pb-4 pt-2 z-10 bg-slate-950/50 backdrop-blur-xl border-t border-white/5">
        <div className="flex gap-3 items-end bg-slate-900/80 border border-white/10 rounded-2xl p-3 focus-within:border-blue-500/50 transition-colors">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe un mensaje... (Enter para enviar, Shift+Enter para nueva línea)"
            rows={1}
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder:text-slate-500 resize-none focus:outline-none max-h-32 leading-relaxed"
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = 'auto';
              el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="flex-none w-9 h-9 flex items-center justify-center bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)]"
          >
            {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-2 text-center">
          El orquestador analiza tu mensaje, crea tareas y las asigna automáticamente a los agentes disponibles.
        </p>
      </div>
    </div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
          isUser
            ? 'bg-gradient-to-br from-blue-600 to-indigo-700'
            : 'bg-gradient-to-br from-purple-600/40 to-blue-600/40 border border-white/10'
        }`}
      >
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-blue-300" />}
      </div>

      <div className={`max-w-[75%] flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : message.status === 'error'
              ? 'bg-red-900/30 border border-red-500/30 text-red-300 rounded-bl-sm'
              : 'bg-slate-800/80 backdrop-blur-sm border border-white/5 text-slate-200 rounded-bl-sm'
          }`}
        >
          {message.content || (message.status === 'streaming' ? <StreamingDots /> : null)}
          {message.status === 'error' && <AlertCircle className="w-3.5 h-3.5 text-red-400 inline ml-2" />}
        </div>

        {message.metadata?.actions_taken && message.metadata.actions_taken.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.metadata.actions_taken.map((action, i) => (
              <span
                key={i}
                className="flex items-center gap-1 text-xs px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full"
              >
                <CheckCircle2 className="w-3 h-3" />
                {action}
              </span>
            ))}
          </div>
        )}

        {message.metadata?.tasks_created && message.metadata.tasks_created.filter(Boolean).length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.metadata.tasks_created.filter(Boolean).map((taskId) => (
              <span
                key={taskId}
                className="flex items-center gap-1 text-xs px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-full"
              >
                <Zap className="w-3 h-3" />
                Task #{taskId}
              </span>
            ))}
          </div>
        )}

        <span className="text-xs text-slate-600 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

function StreamingDots() {
  return (
    <span className="inline-flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </span>
  );
}
