import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, User, Bot, AlertTriangle, ShieldCheck, RefreshCw, X, BookOpen, Sparkles } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import MessageMeta from '../components/MessageMeta';

const SUGGESTED_PROMPTS = [
  "Guide me as a first-time voter",
  "I am 18 and want to vote for the first time",
  "What is EVM and VVPAT?",
  "What is NOTA?",
  "How do I check my name in voter list?",
  "What is a coalition government?",
];

// ---------------------------------------------------------------------------
// react-markdown component map — styles markdown elements inside chat bubbles
// ---------------------------------------------------------------------------
const MD_COMPONENTS = {
  // Paragraphs
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  // Bullet lists
  ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2 pl-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2 pl-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  // Bold
  strong: ({ children }) => <strong className="font-bold">{children}</strong>,
  // Inline code
  code: ({ children }) => (
    <code className="bg-slate-100 text-secondary text-sm px-1.5 py-0.5 rounded font-mono">{children}</code>
  ),
  // Blockquote (used for source reminders)
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-secondary/30 pl-3 my-2 text-slate-600 italic text-sm">
      {children}
    </blockquote>
  ),
  // Links — always open in new tab, never dangerouslySetInnerHTML
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-secondary underline underline-offset-2 hover:opacity-80 break-words"
    >
      {children}
    </a>
  ),
  // Headings inside chat (use modest sizes)
  h1: ({ children }) => <h2 className="text-lg font-extrabold text-primary mb-2 mt-1">{children}</h2>,
  h2: ({ children }) => <h3 className="text-base font-bold text-primary mb-1.5 mt-1">{children}</h3>,
  h3: ({ children }) => <h4 className="text-sm font-bold text-slate-700 mb-1 mt-1">{children}</h4>,
};


// ---------------------------------------------------------------------------
// ChatPage
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// SuggestedReplies — guided flow chips below last assistant message
// ---------------------------------------------------------------------------
const SuggestedReplies = ({ replies, onSelect, disabled }) => {
  if (!replies || replies.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {replies.map((reply, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onSelect(reply)}
          disabled={disabled}
          className="flex items-center gap-1.5 bg-blue-50 border border-secondary/30 text-secondary text-sm font-medium py-1.5 px-3.5 rounded-full hover:bg-secondary hover:text-white hover:border-secondary transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Sparkles size={11} className="flex-shrink-0" />
          {reply}
        </button>
      ))}
    </div>
  );
};

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

  // Guided reply chips — only shown below the LAST assistant message
  const lastAssistantIdx = messages.reduce(
    (acc, msg, i) => (msg.role === 'assistant' ? i : acc), -1
  );

  return (
    <div className="max-w-7xl mx-auto px-3 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-8 min-h-[calc(100svh-7rem)] flex flex-col">
      <div className="mb-5 sm:mb-7 text-center flex flex-col items-center">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-primary mb-3 tracking-tight leading-tight">
          VoteWise Assistant
        </h1>
        <p className="text-muted font-light text-base sm:text-lg md:text-xl max-w-2xl leading-relaxed">
          Ask neutral, factual questions about the Indian election process.
        </p>
        <div className="h-1 w-20 sm:w-24 bg-gradient-to-r from-secondary to-[#4F46E5] rounded-full mt-4 sm:mt-6 shadow-[0_0_10px_rgba(59,130,246,0.3)]"></div>
      </div>

      <div className="h-[calc(100svh-11rem)] min-h-[560px] sm:min-h-[620px] max-h-[900px] bg-white/95 backdrop-blur-3xl rounded-[1.75rem] sm:rounded-[2.5rem] border border-border flex flex-col overflow-hidden mb-4 shadow-xl">

        {/* Chat Header / Settings */}
        <div className="flex-shrink-0 bg-slate-50 border-b border-border p-4 sm:p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-start sm:items-center text-sm">
            <ShieldCheck className="text-success mr-2 mt-0.5 sm:mt-0 flex-shrink-0" size={18} />
            <span className="text-muted">AI responses are filtered for neutrality.</span>
          </div>
          <div className="flex w-full sm:w-auto items-center space-x-2">
            <label className="text-sm font-bold text-text flex-shrink-0">Tone:</label>
            <select
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="w-full sm:w-auto bg-white border border-border text-primary text-sm rounded-xl focus:ring-secondary focus:border-secondary block p-2 backdrop-blur-md outline-none transition-all shadow-sm"
            >
              <option value="general">General</option>
              <option value="first-time-voter">First-Time Voter</option>
              <option value="student">School Student</option>
              <option value="elderly">Elderly</option>
            </select>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-6 space-y-5 sm:space-y-8 bg-transparent">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-full sm:max-w-[85%] lg:max-w-[80%] min-w-0 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 h-9 w-9 sm:h-10 sm:w-10 rounded-full flex items-center justify-center shadow-sm border ${msg.role === 'user' ? 'bg-gradient-to-br from-secondary to-[#4F46E5] ml-2 sm:ml-3 border-secondary' : 'bg-blue-50 mr-2 sm:mr-3 border-blue-100 backdrop-blur-md'}`}>
                  {msg.role === 'user' ? <User className="text-white" size={18} /> : <Bot className="text-secondary" size={18} />}
                </div>

                <div className={`flex min-w-0 flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Message bubble */}
                  <div className={`p-4 sm:p-5 rounded-3xl max-w-full ${
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
                    <div className="break-words text-[15px] prose-chat">
                      {msg.role === 'assistant'
                        ? <ReactMarkdown components={MD_COMPONENTS}>{msg.content}</ReactMarkdown>
                        : <span className="leading-relaxed whitespace-pre-wrap">{msg.content}</span>
                      }
                    </div>
                  </div>

                  {/* RAG fallback badge — shown ONLY when Gemini was unavailable */}
                  {msg.role === 'assistant' && msg.meta?.used_rag_fallback && (
                    <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-500 font-medium">
                      <BookOpen size={12} className="text-secondary" />
                      <span>Answered from VoteWise knowledge base</span>
                    </div>
                  )}

                  {/* Guided reply chips — only on the LAST assistant message */}
                  {msg.role === 'assistant' &&
                    messages.indexOf(msg) === lastAssistantIdx &&
                    !isLoading && (
                    <SuggestedReplies
                      replies={msg.meta?.suggested_replies || []}
                      onSelect={handleSuggestedPrompt}
                      disabled={isLoading}
                    />
                  )}

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
              <div className="flex flex-row max-w-[90%] sm:max-w-[75%]">
                <div className="flex-shrink-0 h-9 w-9 sm:h-10 sm:w-10 rounded-full bg-blue-50 mr-2 sm:mr-3 flex items-center justify-center border border-blue-100 backdrop-blur-md shadow-sm">
                  <Bot className="text-secondary" size={18} />
                </div>
                <div className="bg-slate-50 backdrop-blur-md border border-border p-4 sm:p-5 rounded-3xl rounded-tl-sm flex space-x-2 items-center shadow-sm">
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
          <div className="flex-shrink-0 bg-amber-50 border-t border-amber-200 p-3 flex justify-between items-center text-sm gap-2">
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
        <div className="flex-shrink-0 p-3 sm:p-5 lg:p-6 bg-slate-100 backdrop-blur-xl border-t border-border">
          {/* Static quick prompts — only before any real conversation */}
          {messages.length <= 1 && (
            <div className="mb-3 sm:mb-4">
              <p className="text-xs font-bold text-muted uppercase tracking-wider mb-2">Quick start:</p>
              <div className="flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className={`flex-shrink-0 border text-sm py-2 px-4 rounded-full transition-all text-left shadow-sm ${
                      idx === 0
                        ? 'bg-secondary/10 border-secondary/40 text-secondary font-semibold hover:bg-secondary hover:text-white'
                        : 'bg-white border-border text-muted hover:border-secondary hover:text-primary hover:bg-slate-50'
                    }`}
                    disabled={isLoading}
                  >
                    {idx === 0 && '✨ '}{prompt}
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
              className="w-full bg-white border border-border text-primary rounded-2xl pl-4 sm:pl-5 pr-14 py-3.5 sm:py-4 focus:outline-none focus:ring-2 focus:ring-secondary focus:border-transparent transition-all shadow-sm backdrop-blur-sm"
              disabled={isLoading}
              maxLength={500}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              aria-label="Send message"
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
