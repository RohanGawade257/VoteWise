import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, AlertTriangle, ShieldCheck, RefreshCw, X } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import { useChat } from '../hooks/useChat';
import MessageMeta from '../components/MessageMeta';

const SUGGESTED_PROMPTS = [
  "I am 18. How do I register to vote?",
  "Explain polling day like I am a school student.",
  "What is EVM and VVPAT?",
  "What is a coalition government?",
  "What is NOTA?",
  "How do I check my name in voter list?",
];

// ---------------------------------------------------------------------------
// Lightweight inline markdown renderer — handles **bold** and [text](url).
// Preserves newlines via whitespace-pre-wrap on the parent container.
// No external library required.
// ---------------------------------------------------------------------------
function renderMarkdown(text) {
  if (!text) return null;

  // Regex matches **bold** or [label](url) — in one pass
  const INLINE_RE = /(\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)]+)\))/g;

  return text.split('\n').map((line, li, arr) => {
    const parts = [];
    let lastIndex = 0;
    let match;
    let key = 0;

    INLINE_RE.lastIndex = 0; // reset for each line
    while ((match = INLINE_RE.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.slice(lastIndex, match.index));
      }
      if (match[0].startsWith('**')) {
        // Bold
        parts.push(<strong key={key++}>{match[2]}</strong>);
      } else {
        // Link
        parts.push(
          <a
            key={key++}
            href={match[4]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-secondary underline underline-offset-2 hover:opacity-80"
          >
            {match[3]}
          </a>
        );
      }
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < line.length) {
      parts.push(line.slice(lastIndex));
    }

    return (
      <span key={li}>
        {parts}
        {li < arr.length - 1 && '\n'}
      </span>
    );
  });
}

// ---------------------------------------------------------------------------
// ChatPage
// ---------------------------------------------------------------------------
const ChatPage = () => {
  const [input, setInput] = useState('');
  const [persona, setPersona] = useState('general');
  const { messages, isLoading, error, sendMessage, clearError } = useChat();
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  };

  useEffect(() => {
    // Only auto-scroll when loading starts (to see indicator) 
    // or when the user just sent a message.
    // Do NOT scroll when the assistant finishes responding.
    if (isLoading) {
      scrollToBottom();
    } else if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
      scrollToBottom();
    }
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input, persona);
    setInput('');
  };

  const handleSuggestedPrompt = (prompt) => {
    if (isLoading) return;
    sendMessage(prompt, persona);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8 h-[calc(100vh-4rem)] flex flex-col">
      <SectionHeader
        title="VoteWise Assistant"
        subtitle="Ask neutral, factual questions about the Indian election process."
        centered={true}
      />

      <div className="flex-1 bg-white/95 backdrop-blur-3xl rounded-[2.5rem] border border-border flex flex-col overflow-hidden mb-4 shadow-xl">

        {/* Chat Header / Settings */}
        <div className="bg-slate-50 border-b border-border p-4 sm:p-5 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center text-sm">
            <ShieldCheck className="text-success mr-2" size={18} />
            <span className="text-muted">AI responses are filtered for neutrality.</span>
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-bold text-text">Tone:</label>
            <select
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="bg-white border border-border text-primary text-sm rounded-xl focus:ring-secondary focus:border-secondary block p-2 backdrop-blur-md outline-none transition-all shadow-sm"
            >
              <option value="general">General</option>
              <option value="first-time-voter">First-Time Voter</option>
              <option value="student">School Student</option>
              <option value="elderly">Elderly</option>
            </select>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-8 bg-transparent">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[95%] sm:max-w-[85%] lg:max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center shadow-sm border ${msg.role === 'user' ? 'bg-gradient-to-br from-secondary to-[#4F46E5] ml-3 border-secondary' : 'bg-blue-50 mr-3 border-blue-100 backdrop-blur-md'}`}>
                  {msg.role === 'user' ? <User className="text-white" size={20} /> : <Bot className="text-secondary" size={20} />}
                </div>

                <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Message bubble */}
                  <div className={`p-5 rounded-3xl ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-secondary to-[#4F46E5] text-white rounded-tr-sm shadow-md'
                      : msg.safetyBlocked
                        ? 'bg-amber-50 border border-amber-200 text-slate-800 rounded-tl-sm'
                        : 'bg-white backdrop-blur-md border border-border text-slate-800 rounded-tl-sm shadow-sm'
                  }`}>
                    {/* Safety-blocked badge */}
                    {msg.safetyBlocked && (
                      <div className="flex items-center text-amber-600 font-bold mb-2 text-sm">
                        <AlertTriangle size={16} className="mr-1" /> Request Blocked
                      </div>
                    )}
                    {/* Rendered content */}
                    <div className="whitespace-pre-wrap leading-relaxed text-[15px]">
                      {msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content}
                    </div>
                  </div>

                  {/* Answer provenance badges, confidence, sources */}
                  {msg.role === 'assistant' && (
                    <MessageMeta
                      meta={msg.meta}
                      sources={msg.sources}
                      safetyBlocked={msg.safetyBlocked}
                    />
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex flex-row max-w-[75%]">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-50 mr-3 flex items-center justify-center border border-blue-100 backdrop-blur-md shadow-sm">
                  <Bot className="text-secondary" size={20} />
                </div>
                <div className="bg-slate-50 backdrop-blur-md border border-border p-5 rounded-3xl rounded-tl-sm flex space-x-2 items-center shadow-sm">
                  <div className="w-2.5 h-2.5 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2.5 h-2.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2.5 h-2.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-amber-50 border-t border-amber-200 p-3 flex justify-between items-center text-sm gap-2">
            <span className="text-amber-600 flex items-center gap-2">
              <AlertTriangle size={16} />
              {error}
            </span>
            <button
              onClick={clearError}
              className="flex-shrink-0 text-amber-600 hover:text-amber-700 transition-colors"
              aria-label="Dismiss error"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 sm:p-6 bg-slate-100 backdrop-blur-xl border-t border-border">
          {/* Suggested Prompts — show while conversation is still short */}
          {messages.length <= 2 && (
            <div className="mb-4">
              <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">Try asking:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="bg-white border border-border hover:border-secondary hover:text-primary text-muted text-sm py-2 px-4 rounded-full transition-all text-left shadow-sm hover:shadow-md hover:bg-slate-50"
                    disabled={isLoading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the election process..."
              className="w-full bg-white border border-border text-primary rounded-2xl pl-5 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-secondary focus:border-transparent transition-all shadow-sm backdrop-blur-sm"
              disabled={isLoading}
              maxLength={500}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-2.5 bg-secondary text-white rounded-xl hover:bg-[#2563EB] disabled:opacity-50 disabled:hover:bg-secondary transition-all shadow-[0_4px_14px_rgba(59,130,246,0.4)] flex items-center justify-center"
            >
              {isLoading ? <RefreshCw size={20} className="animate-spin" /> : <Send size={20} />}
            </button>
          </form>
          <div className="text-center mt-3">
            <span className="text-xs text-muted font-light">VoteWise AI can make mistakes. Always verify important dates with the ECI.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
