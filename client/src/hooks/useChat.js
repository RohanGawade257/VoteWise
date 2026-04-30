import { useState, useRef } from 'react';
import { useLanguage, LANGUAGES } from '../context/LanguageContext';

// In dev: use VITE_API_BASE_URL if set, otherwise Vite proxy handles /api → localhost:VITE_BACKEND_PORT
// In prod: same-origin /api (no env var needed)
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const getErrorMessage = (status, fallbackMsg) => {
  switch (status) {
    case 401:
    case 403: return 'API key configuration issue. Please contact the site administrator.';
    case 404: return 'Chat server route not found. Please contact support.';
    case 429: return 'Rate limit exceeded. Please wait a moment and try again.';
    case 503: return 'AI backend is temporarily unavailable.';
    default:  return fallbackMsg || 'Something went wrong. Please try again.';
  }
};

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Namaste! I am VoteWise Assistant. I can help answer your questions about the Indian election process, voter registration, and democracy basics.\n\nWant me to guide you step-by-step as a first-time voter?',
      meta: {
        suggested_replies: [
          'Guide me as a first-time voter',
          'I am 18 and want to vote',
          'What is EVM and VVPAT?',
          'How do I check my name in voter list?',
        ],
      },
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { currentLang } = useLanguage();

  // Guided flow state — tracks the active journey across messages
  const guidedFlowRef = useRef({
    active: false,
    step: null,
    state: {},
  });

  // Ref-based guard: prevents duplicate in-flight requests regardless of render cycles
  const inFlightRef = useRef(false);

  const sendMessage = async (message, persona = 'general', context = '') => {
    const trimmed = message.trim();
    if (!trimmed) return;

    // Hard guard — if a request is already in flight, do nothing
    if (inFlightRef.current) {
      console.warn('[useChat] Duplicate send blocked — request already in flight');
      return;
    }

    const clientRequestId = crypto.randomUUID();
    console.log(`[useChat] Sending | clientRequestId=${clientRequestId} | msg="${trimmed.slice(0, 40)}" | t=${new Date().toISOString()}`);

    inFlightRef.current = true;
    setIsLoading(true);
    setError(null);
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: trimmed }]);

    try {
      let response;
      try {
        const langInfo = LANGUAGES.find(l => l.code === currentLang);
        const langPrompt = (currentLang !== 'en' && langInfo)
          ? `\n\n[CRITICAL SYSTEM INSTRUCTION: You MUST respond entirely in the ${langInfo.name} language.]`
          : '';

        // Snapshot the current guided flow state to send with this request
        const guidedFlowPayload = {
          active: guidedFlowRef.current.active,
          step: guidedFlowRef.current.step,
          state: guidedFlowRef.current.state,
        };

        response = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Client-Request-Id': clientRequestId,
          },
          body: JSON.stringify({
            message: trimmed + langPrompt,
            persona,
            context,
            guidedFlow: guidedFlowPayload,
          }),
        });
      } catch {
        throw new Error('Backend server is not running. Please ensure the server is started on port 8080.');
      }

      const data = await response.json();
      console.log(`[useChat] Response | clientRequestId=${clientRequestId} | status=${response.status} | ok=${response.ok}`);

      if (!response.ok) {
        throw new Error(getErrorMessage(response.status, data.error));
      }

      // Update guided flow state from backend meta
      const meta = data.meta || {};
      if (meta.guided_flow_active) {
        guidedFlowRef.current = {
          active: true,
          step: meta.guided_flow_step || null,
          state: meta.guided_flow_state || {},
        };
        console.log(`[useChat] Guided flow updated | step=${meta.guided_flow_step}`);
      } else if (!meta.guided_flow_active && guidedFlowRef.current.active) {
        // Flow completed or fell through — reset
        guidedFlowRef.current = { active: false, step: null, state: {} };
        console.log('[useChat] Guided flow COMPLETED — resetting');
      }

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          safetyBlocked: data.safety?.blocked,
          meta: data.meta,
        }
      ]);
    } catch (err) {
      console.error(`[useChat] Error | clientRequestId=${clientRequestId} | ${err.message}`);
      setError(err.message);
    } finally {
      inFlightRef.current = false;
      setIsLoading(false);
    }
  };

  const clearError = () => setError(null);

  return { messages, isLoading, error, sendMessage, setMessages, clearError };
};
