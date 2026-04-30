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
    // Prevent auto-scrolling to the bottom on initial page load
    if (messages.length > 1 || isLoading) {
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
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8 h-[calc(100vh-4rem)] flex flex-col">
      <SectionHeader
        title="VoteWise Assistant"
        subtitle="Ask neutral, factual questions about the Indian election process."
        centered={true}
      />

      <div className="flex-1 clay-card flex flex-col overflow-hidden mb-4 border-none">

        {/* Chat Header / Settings */}
        <div className="bg-background border-b border-border p-4 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center text-sm">
            <ShieldCheck className="text-success mr-2" size={18} />
            <span className="text-muted">AI responses are filtered for neutrality.</span>
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-bold text-text">Tone:</label>
            <select
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="bg-surface border border-border text-text text-sm rounded-lg focus:ring-secondary focus:border-secondary block p-2"
            >
              <option value="general">General</option>
              <option value="first-time-voter">First-Time Voter</option>
              <option value="student">School Student</option>
              <option value="elderly">Elderly</option>
            </select>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-background/50">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[85%] sm:max-w-[75%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-secondary ml-3' : 'bg-primary mr-3'}`}>
                  {msg.role === 'user' ? <User className="text-surface" size={20} /> : <Bot className="text-surface" size={20} />}
                </div>

                <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Message bubble */}
                  <div className={`p-4 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-secondary text-surface rounded-tr-none'
                      : msg.safetyBlocked
                        ? 'bg-warning/10 border border-warning/20 text-text rounded-tl-none'
                        : 'bg-surface border border-border text-text rounded-tl-none shadow-sm'
                  }`}>
                    {/* Safety-blocked badge */}
                    {msg.safetyBlocked && (
                      <div className="flex items-center text-warning font-bold mb-2 text-sm">
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
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-primary mr-3 flex items-center justify-center">
                  <Bot className="text-surface" size={20} />
                </div>
                <div className="bg-surface border border-border p-4 rounded-2xl rounded-tl-none flex space-x-2 items-center">
                  <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary/80 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-warning/10 border-t border-warning/20 p-3 flex justify-between items-center text-sm gap-2">
            <span className="text-warning flex items-center gap-2">
              <AlertTriangle size={16} />
              {error}
            </span>
            <button
              onClick={clearError}
              className="flex-shrink-0 text-warning hover:text-warning/70 transition-colors"
              aria-label="Dismiss error"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 bg-surface border-t border-border">
          {/* Suggested Prompts — show while conversation is still short */}
          {messages.length <= 2 && (
            <div className="mb-4">
              <p className="text-xs font-bold text-muted uppercase tracking-wider mb-2">Try asking:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="bg-background border border-border hover:border-secondary hover:text-secondary text-text text-sm py-1.5 px-3 rounded-full transition-colors text-left"
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
              className="w-full bg-background border border-border text-text rounded-xl pl-4 pr-12 py-4 focus:outline-none focus:ring-2 focus:ring-secondary focus:border-transparent transition-all shadow-sm"
              disabled={isLoading}
              maxLength={500}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-2 bg-secondary text-surface rounded-lg hover:bg-secondary/90 disabled:opacity-50 disabled:hover:bg-secondary transition-colors flex items-center justify-center"
            >
              {isLoading ? <RefreshCw size={20} className="animate-spin" /> : <Send size={20} />}
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-xs text-muted">VoteWise AI can make mistakes. Always verify important dates with the ECI.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
