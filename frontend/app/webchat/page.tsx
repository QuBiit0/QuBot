'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, Bot, User, Loader2, Paperclip, Image, FileText, X, 
  MoreVertical, Trash2, Copy, CheckCircle, AlertCircle, 
  ChevronDown, Settings, Zap, MessageSquare, Clock, Plus,
  PanelRight, Sparkles, Square, Mic, MicOff, Sun, Moon,
  Home, Wifi, WifiOff
} from 'lucide-react';
import Link from 'next/link';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 
  (process.env.NODE_ENV === 'development' ? 'http://localhost:8000/api/v1' : '/api/v1');

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status: 'streaming' | 'done' | 'error';
  attachments?: Attachment[];
  tools?: ToolExecution[];
}

interface Attachment {
  id: string;
  type: 'image' | 'file' | 'text';
  name: string;
  url?: string;
  content?: string;
}

interface ToolExecution {
  name: string;
  status: 'running' | 'done' | 'error';
  result?: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: Date;
  updated_at: Date;
  message_count: number;
}

const AGENTS = [
  { id: 'orchestrator', name: 'Orchestrator', icon: <Sparkles className="w-4 h-4" />, color: '#6366f1' },
  { id: 'dev', name: 'Developer', icon: <Bot className="w-4 h-4" />, color: '#10b981' },
  { id: 'research', name: 'Researcher', icon: <FileText className="w-4 h-4" />, color: '#f59e0b' },
  { id: 'design', name: 'Designer', icon: <Image className="w-4 h-4" />, color: '#ec4899' },
];

export default function WebChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [sessions, setSessions] = useState<ChatSession[]>([
    { id: '1', title: 'Project Planning', created_at: new Date(), updated_at: new Date(), message_count: 12 },
    { id: '2', title: 'Code Review', created_at: new Date(), updated_at: new Date(), message_count: 8 },
    { id: '3', title: 'Research Tasks', created_at: new Date(), updated_at: new Date(), message_count: 5 },
  ]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [selectedAgent]);

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

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
      status: 'done',
    };

    const assistantId = `assistant-${Date.now()}`;
    setMessages(prev => [
      ...prev,
      userMsg,
      { id: assistantId, role: 'assistant', content: '', timestamp: new Date(), status: 'streaming', tools: [] },
    ]);

    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text, agent_id: selectedAgent?.id }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      if (!res.body) throw new Error('No response body');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        fullContent += chunk;
        
        setMessages(prev => prev.map(m => 
          m.id === assistantId 
            ? { ...m, content: fullContent }
            : m
        ));
      }

      setMessages(prev => prev.map(m => 
        m.id === assistantId 
          ? { ...m, status: 'done' }
          : m
      ));

    } catch (err) {
      const error = err as Error;
      let friendlyMessage = 'Something went wrong. Please try again.';
      
      if (error.name === 'AbortError') {
        setMessages(prev => prev.map(m => 
          m.id === assistantId 
            ? { ...m, status: 'done', content: m.content || '[Cancelled]' }
            : m
        ));
        return;
      }
      
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        friendlyMessage = 'Unable to connect to the server. Please check your internet connection.';
      } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        friendlyMessage = 'Session expired. Please log in again.';
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        friendlyMessage = 'You do not have permission to perform this action.';
      } else if (error.message.includes('429') || error.message.includes('Too Many')) {
        friendlyMessage = 'Too many requests. Please wait a moment and try again.';
      } else if (error.message.includes('500') || error.message.includes('Internal Server')) {
        friendlyMessage = 'Server error. Our team has been notified. Please try again later.';
      } else if (error.message.includes('503') || error.message.includes('Service Unavailable')) {
        friendlyMessage = 'Service temporarily unavailable. Please try again in a few minutes.';
      }
      
      setMessages(prev => prev.map(m => 
        m.id === assistantId 
          ? { ...m, status: 'error', content: friendlyMessage }
          : m
      ));
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, selectedAgent]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
  };

  const copyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const clearChat = () => {
    setMessages([]);
  };

  const newChat = () => {
    setActiveSession(null);
    setMessages([]);
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="h-full flex" style={{ background: darkMode ? '#060912' : '#f8fafc' }}>
      
      {/* Sidebar */}
      <div className={`${showSidebar ? 'w-64' : 'w-0'} transition-all duration-200 flex-shrink-0 border-r overflow-hidden`}
        style={{ borderColor: darkMode ? 'rgba(255,255,255,0.05)' : '#e2e8f0', background: darkMode ? 'rgba(10,15,30,0.95)' : '#ffffff' }}>
        
        <div className="p-4 h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #3b6fff, #a371f7)' }}>
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold" style={{ color: darkMode ? '#e6edf3' : '#1e293b' }}>WebChat</span>
            </div>
            <button onClick={() => setDarkMode(!darkMode)} className="p-1.5 rounded-lg transition-colors" style={{ background: darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9' }}>
              {darkMode ? <Sun className="w-4 h-4" style={{ color: '#94a3b8' }} /> : <Moon className="w-4 h-4" style={{ color: '#64748b' }} />}
            </button>
          </div>

          {/* New Chat */}
          <button onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] font-medium mb-4 transition-colors"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff' }}>
            <Plus className="w-4 h-4" />
            New Chat
          </button>

          {/* Sessions */}
          <div className="flex-1 overflow-y-auto space-y-1">
            <div className="text-[10px] font-semibold uppercase tracking-wider px-3 py-2" style={{ color: darkMode ? 'rgba(255,255,255,0.3)' : '#94a3b8' }}>
              Recent Chats
            </div>
            {sessions.map(session => (
              <button key={session.id}
                onClick={() => setActiveSession(session.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${activeSession === session.id ? '' : 'hover:bg-white/5'}`}
                style={{ 
                  background: activeSession === session.id ? (darkMode ? 'rgba(99,102,241,0.15)' : '#f1f5f9') : 'transparent',
                  borderLeft: activeSession === session.id ? '2px solid #6366f1' : '2px solid transparent'
                }}>
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }} />
                  <span className="text-[13px] truncate flex-1" style={{ color: darkMode ? 'rgba(255,255,255,0.8)' : '#475569' }}>
                    {session.title}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1 pl-5">
                  <Clock className="w-3 h-3" style={{ color: darkMode ? 'rgba(255,255,255,0.25)' : '#cbd5e1' }} />
                  <span className="text-[10px]" style={{ color: darkMode ? 'rgba(255,255,255,0.25)' : '#94a3b8' }}>
                    {formatTime(session.updated_at)}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Bottom */}
          <div className="pt-4 border-t" style={{ borderColor: darkMode ? 'rgba(255,255,255,0.05)' : '#e2e8f0' }}>
            <button className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] transition-colors hover:bg-white/5"
              style={{ color: darkMode ? 'rgba(255,255,255,0.6)' : '#64748b' }}>
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Header */}
        <div className="flex-none px-4 py-3 border-b flex items-center justify-between"
          style={{ borderColor: darkMode ? 'rgba(255,255,255,0.05)' : '#e2e8f0', background: darkMode ? 'rgba(6,9,18,0.8)' : '#ffffff' }}>
          
          <div className="flex items-center gap-3">
            <button onClick={() => setShowSidebar(!showSidebar)} className="p-1.5 rounded-lg transition-colors hover:bg-white/5">
              <PanelRight className="w-4 h-4" style={{ color: darkMode ? 'rgba(255,255,255,0.5)' : '#64748b' }} />
            </button>
            
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${selectedAgent?.color ?? '#6366f1'}20` }}>
              <span style={{ color: selectedAgent?.color ?? '#6366f1' }}>{selectedAgent?.icon ?? '🤖'}</span>
            </div>
            <div>
              <div className="text-[13px] font-medium" style={{ color: darkMode ? '#e6edf3' : '#1e293b' }}>
                {selectedAgent?.name ?? 'Default Agent'}
              </div>
              <div className="flex items-center gap-1.5">
                {connectionStatus === 'connected' ? (
                  <Wifi className="w-3 h-3" style={{ color: '#22c55e' }} />
                ) : connectionStatus === 'error' ? (
                  <WifiOff className="w-3 h-3" style={{ color: '#ef4444' }} />
                ) : (
                  <div className="w-3 h-3 rounded-full animate-pulse" style={{ background: '#f59e0b' }} />
                )}
                <span className="text-[10px]" style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }}>
                  {isStreaming ? 'Thinking...' : connectionStatus === 'connected' ? 'Ready' : connectionStatus === 'error' ? 'Connection issue' : 'Connecting...'}
                </span>
              </div>
            </div>
          </div>
          
          <Link href="/dashboard" className="ml-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors"
            style={{ background: darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9', color: darkMode ? 'rgba(255,255,255,0.6)' : '#64748b', border: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0' }}>
            <Home className="w-3.5 h-3.5" />
            Office
          </Link>
        </div>

        <div className="flex items-center gap-2">
            {/* Agent Selector */}
            <div className="relative">
              <select
                value={selectedAgent?.id ?? ''}
                onChange={e => setSelectedAgent(AGENTS.find(a => a.id === e.target.value) || AGENTS[0])}
                className="appearance-none px-3 py-1.5 pr-8 rounded-lg text-[12px] font-medium cursor-pointer"
                style={{ background: darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9', color: darkMode ? 'rgba(255,255,255,0.8)' : '#475569', border: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0' }}>
                {AGENTS.map(agent => (
                  <option key={agent.id} value={agent.id}>{agent.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none" style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }} />
            </div>

            {isStreaming && (
              <button onClick={stopStreaming}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors"
                style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                <Square className="w-3.5 h-3.5" />
                Stop
              </button>
            )}

            <button onClick={clearChat}
              className="p-1.5 rounded-lg transition-colors hover:bg-white/5"
              style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }}>
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center -mt-20">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center mb-4" 
                style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 8px 32px rgba(99,102,241,0.3)' }}>
                <Bot className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: darkMode ? '#e6edf3' : '#1e293b' }}>
                Chat with {selectedAgent?.name ?? 'Default Agent'}
              </h2>
              <p className="text-[14px] text-center max-w-md" style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }}>
                Ask questions, delegate tasks, or request help with coding, research, design, and more.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 justify-center max-w-lg">
                {['Write a Python script', 'Review my code', 'Research AI trends', 'Create a task plan'].map((suggestion, i) => (
                  <button key={i}
                    onClick={() => setInput(suggestion)}
                    className="px-3 py-1.5 rounded-lg text-[12px] transition-colors"
                    style={{ background: darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9', color: darkMode ? 'rgba(255,255,255,0.6)' : '#64748b', border: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0' }}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              darkMode={darkMode}
              onCopy={() => copyMessage(message.id, message.content)}
              isCopied={copiedId === message.id}
            />
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex-none px-4 pb-4 pt-2">
          <div className="flex gap-3 items-end"
            style={{ background: darkMode ? 'rgba(15,23,42,0.9)' : '#ffffff', borderRadius: 16, border: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0', padding: 12 }}>
            
            <button className="p-2 rounded-lg transition-colors shrink-0 hover:bg-white/5"
              style={{ color: darkMode ? 'rgba(255,255,255,0.4)' : '#94a3b8' }}>
              <Paperclip className="w-5 h-5" />
            </button>

            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Message ${selectedAgent?.name ?? 'Agent'}...`}
              rows={1}
              className="flex-1 bg-transparent text-[14px] resize-none focus:outline-none max-h-32 leading-relaxed"
              style={{ color: darkMode ? '#e6edf3' : '#1e293b', caretColor: '#6366f1' }}
              onInput={e => {
                const el = e.currentTarget;
                el.style.height = 'auto';
                el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
              }}
            />

            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="flex-none w-9 h-9 flex items-center justify-center rounded-xl transition-all shrink-0"
              style={{ 
                background: input.trim() && !isStreaming ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : (darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9'),
                boxShadow: input.trim() && !isStreaming ? '0 4px 15px rgba(99,102,241,0.3)' : 'none',
                opacity: input.trim() || isStreaming ? 1 : 0.5
              }}>
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <Send className="w-4 h-4" style={{ color: input.trim() ? '#fff' : (darkMode ? 'rgba(255,255,255,0.3)' : '#cbd5e1') }} />
              )}
            </button>
          </div>
          
          <p className="text-[11px] text-center mt-2" style={{ color: darkMode ? 'rgba(255,255,255,0.25)' : '#94a3b8' }}>
            {selectedAgent?.name ?? 'Agent'} can make mistakes. Consider verifying important information.
          </p>
        </div>
      </div>
    </div>
  );
}

function ChatMessage({ message, darkMode, onCopy, isCopied }: { 
  message: Message; 
  darkMode: boolean;
  onCopy: () => void;
  isCopied: boolean;
}) {
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'streaming';
  const isError = message.status === 'error';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
        isUser 
          ? 'bg-gradient-to-br from-blue-500 to-indigo-600' 
          : 'bg-gradient-to-br from-purple-500/20 to-blue-500/20 border'
      }`}
        style={{ borderColor: isUser ? 'transparent' : 'rgba(99,102,241,0.3)' }}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-blue-400" />}
      </div>

      <div className={`max-w-[75%] flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl text-[14px] leading-relaxed ${
          isUser
            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-br-sm'
            : isError
            ? 'bg-red-500/10 border border-red-500/20 text-red-400 rounded-bl-sm'
            : darkMode
            ? 'bg-slate-800/80 text-slate-200 rounded-bl-sm'
            : 'bg-slate-100 text-slate-700 rounded-bl-sm'
        }`}
          style={!isUser && !isError && darkMode ? { border: '1px solid rgba(255,255,255,0.05)' } : {}}>
          
          {message.content || (isStreaming ? <StreamingIndicator /> : null)}
          
          {isError && (
            <span className="flex items-center gap-1 mt-1 text-[12px] opacity-70">
              <AlertCircle className="w-3.5 h-3.5" />
              Error occurred
            </span>
          )}
        </div>

        {message.tools && message.tools.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-1">
            {message.tools.map((tool, i) => (
              <span key={i} className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px]"
                style={{ background: darkMode ? 'rgba(99,102,241,0.1)' : '#f1f5f9', color: darkMode ? '#818cf8' : '#6366f1' }}>
                {tool.status === 'running' ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : tool.status === 'done' ? (
                  <CheckCircle className="w-3 h-3" />
                ) : (
                  <AlertCircle className="w-3 h-3" />
                )}
                {tool.name}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 mt-1">
          <span className="text-[11px]" style={{ color: darkMode ? 'rgba(255,255,255,0.3)' : '#94a3b8' }}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          
          {!isStreaming && message.content && (
            <button onClick={onCopy}
              className="p-1 rounded transition-colors hover:bg-white/5"
              style={{ color: isCopied ? '#22c55e' : (darkMode ? 'rgba(255,255,255,0.3)' : '#94a3b8') }}>
              {isCopied ? <CheckCircle className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StreamingIndicator() {
  return (
    <span className="inline-flex items-center gap-1">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
      ))}
    </span>
  );
}
