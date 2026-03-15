'use client';
import React, { useState, useRef, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tasksCreated?: number[];
  timestamp: Date;
}

function formatTime(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatPanel() {
  const [open, setOpen]       = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: "Hi! I'm Lead, your AI orchestrator. Tell me what you need and I'll coordinate the team.",
      timestamp: new Date(),
    },
  ]);
  const [input,   setInput]   = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 120);
  }, [open]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/v1/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply || 'Task received.',
        tasksCreated: data.tasks_created,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Connection error. Make sure the backend is running.',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const hasInput = input.trim().length > 0;

  return (
    <>
      {/* ── Floating trigger button ── */}
      <button
        onClick={() => setOpen(o => !o)}
        className="fixed bottom-5 right-5 z-50 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200"
        style={{
          background:  open
            ? 'rgba(30,40,70,0.95)'
            : 'linear-gradient(135deg,#3b6fff,#7c3aed)',
          border:      '1px solid rgba(255,255,255,0.1)',
          boxShadow:   open
            ? '0 4px 20px rgba(0,0,0,0.4)'
            : '0 4px 24px rgba(59,111,255,0.45), 0 0 0 1px rgba(59,111,255,0.2)',
        }}
        title="Chat with Lead"
      >
        {open ? (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1l12 12M13 1L1 13" stroke="#8b949e" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : (
          /* Chat bubble icon */
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M17.5 10c0 3.866-3.358 7-7.5 7a8.08 8.08 0 0 1-3.496-.783L3 17.5l1.28-3.004A6.862 6.862 0 0 1 2.5 10c0-3.866 3.358-7 7.5-7s7.5 3.134 7.5 7z"
              fill="rgba(255,255,255,0.9)"
            />
          </svg>
        )}
      </button>

      {/* ── Chat panel ── */}
      {open && (
        <div
          className="fixed bottom-20 right-5 z-50 w-[380px] flex flex-col rounded-2xl overflow-hidden"
          style={{
            height:     '500px',
            background: 'rgba(5,9,18,0.97)',
            backdropFilter: 'blur(24px)',
            border:     '1px solid rgba(255,255,255,0.07)',
            boxShadow:  '0 24px 64px rgba(0,0,0,0.7), 0 0 0 1px rgba(59,111,255,0.08)',
          }}
        >
          {/* ── Header ── */}
          <div
            className="flex items-center gap-3 px-4 py-3 flex-shrink-0"
            style={{
              background:  'linear-gradient(180deg, rgba(59,111,255,0.08) 0%, transparent 100%)',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            {/* Avatar */}
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center text-[13px] font-black flex-shrink-0"
              style={{
                background: 'linear-gradient(135deg,#3b6fff,#7c3aed)',
                color: '#fff',
                boxShadow: '0 0 12px rgba(59,111,255,0.4)',
              }}
            >
              L
            </div>

            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-bold" style={{ color: '#e6edf3' }}>Lead</div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse flex-shrink-0" />
                <span className="text-[10px] font-medium" style={{ color: '#3fb950' }}>
                  Mission Controller · Online
                </span>
              </div>
            </div>

            <span className="text-[10px] font-mono" style={{ color: '#2d4060' }}>
              {messages.length - 1} msgs
            </span>
          </div>

          {/* ── Messages ── */}
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`flex items-end gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar dot */}
                {msg.role === 'assistant' && (
                  <div
                    className="w-6 h-6 rounded-lg flex-shrink-0 flex items-center justify-center text-[10px] font-black"
                    style={{
                      background: 'linear-gradient(135deg,#3b6fff,#7c3aed)',
                      color: '#fff',
                      alignSelf: 'flex-end',
                    }}
                  >
                    L
                  </div>
                )}

                <div className={`flex flex-col gap-0.5 max-w-[78%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className="px-3 py-2 rounded-xl text-[12px] leading-relaxed"
                    style={msg.role === 'user' ? {
                      background: 'linear-gradient(135deg,#3b6fff,#5b48e8)',
                      color:      '#fff',
                      borderBottomRightRadius: 4,
                      boxShadow: '0 2px 12px rgba(59,111,255,0.3)',
                    } : {
                      background: 'rgba(255,255,255,0.05)',
                      color:      '#c9d1d9',
                      border:     '1px solid rgba(255,255,255,0.06)',
                      borderBottomLeftRadius: 4,
                    }}
                  >
                    {msg.content}
                    {msg.tasksCreated && msg.tasksCreated.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {msg.tasksCreated.map(id => (
                          <span
                            key={id}
                            className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                            style={{ background: 'rgba(59,111,255,0.2)', color: '#7ca3ff', border: '1px solid rgba(59,111,255,0.3)' }}
                          >
                            Task #{id}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="text-[9px]" style={{ color: '#2d4060' }}>
                    {formatTime(msg.timestamp)}
                  </span>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex items-end gap-2">
                <div
                  className="w-6 h-6 rounded-lg flex-shrink-0 flex items-center justify-center text-[10px] font-black"
                  style={{ background: 'linear-gradient(135deg,#3b6fff,#7c3aed)', color: '#fff' }}
                >
                  L
                </div>
                <div
                  className="px-3 py-2.5 rounded-xl"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderBottomLeftRadius: 4,
                  }}
                >
                  <div className="flex gap-1 items-center">
                    {[0, 1, 2].map(i => (
                      <span
                        key={i}
                        className="w-1.5 h-1.5 rounded-full animate-bounce"
                        style={{ background: '#3b6fff', animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* ── Input area ── */}
          <div
            className="flex-shrink-0 p-3"
            style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div
              className="flex items-center gap-2 px-3 py-2 rounded-xl"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border:     hasInput
                  ? '1px solid rgba(59,111,255,0.4)'
                  : '1px solid rgba(255,255,255,0.07)',
                transition: 'border-color 0.15s',
              }}
            >
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                placeholder="Give a task to the team…"
                className="flex-1 bg-transparent text-[12px] outline-none"
                style={{
                  color:            '#e6edf3',
                  caretColor:       '#3b6fff',
                  '::placeholder':  { color: '#2d4060' },
                } as React.CSSProperties}
              />
              <button
                onClick={send}
                disabled={!hasInput || loading}
                className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-150"
                style={hasInput && !loading ? {
                  background: 'linear-gradient(135deg,#3b6fff,#7c3aed)',
                  boxShadow:  '0 0 12px rgba(59,111,255,0.4)',
                } : {
                  background: 'rgba(255,255,255,0.06)',
                  opacity: 0.5,
                }}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M1 11L11 1M11 1H4M11 1V8" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="text-center mt-1.5">
              <span className="text-[9px]" style={{ color: '#1e2d45' }}>Enter to send · Lead coordinates your agents</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
