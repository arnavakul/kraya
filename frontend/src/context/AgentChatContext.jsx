import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { api } from '../lib/api';

const AgentChatContext = createContext(null);

export const useAgentChat = () => {
  const ctx = useContext(AgentChatContext);
  if (!ctx) throw new Error('useAgentChat must be used within an AgentChatProvider');
  return ctx;
};

const INITIAL_GREETING = {
  id: 'greeting',
  role: 'agent',
  text: "Hello! I'm Kraya Agent, your autonomous AI procurement co-pilot. I can validate requirements, analyze your catalog suppliers, compare quotes, and draft RFQs. How can I help you today?",
  timestamp: new Date(),
};

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function AgentChatProvider({ children }) {
  const [messages, setMessages] = useState([INITIAL_GREETING]);
  const [conversationId, setConversationId] = useState(null);
  const [isPending, setIsPending] = useState(false);
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);

  const sendMessage = useCallback(async (text) => {
    const trimmed = (text || '').trim();
    if (!trimmed || isPending) return;

    const userMsg = {
      id: uid(),
      role: 'user',
      text: trimmed,
      timestamp: new Date(),
    };

    const placeholderId = uid();
    const placeholderMsg = {
      id: placeholderId,
      role: 'agent',
      typing: true,
      text: '',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, placeholderMsg]);
    setIsPending(true);

    try {
      const data = await api('/agent/chat', {
        method: 'POST',
        body: {
          message: trimmed,
          conversationId: conversationId || null,
        },
      });

      if (data?.conversationId) {
        setConversationId(data.conversationId);
      }

      const agentMsg = {
        id: uid(),
        role: 'agent',
        text: data?.reply || "I've processed your procurement request.",
        followUp: data?.followUp || null,
        steps: data?.steps || null,
        progress: data?.procurementProgress || null,
        timestamp: new Date(),
      };

      setMessages((prev) => prev.map((m) => (m.id === placeholderId ? agentMsg : m)));
    } catch (err) {
      const errorMsg = {
        id: uid(),
        role: 'agent',
        text: err?.message || 'Sorry, I encountered an issue connecting to the procurement agent service. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => prev.map((m) => (m.id === placeholderId ? errorMsg : m)));
    } finally {
      setIsPending(false);
    }
  }, [conversationId, isPending]);

  const clearChat = useCallback(() => {
    setMessages([{ ...INITIAL_GREETING, timestamp: new Date() }]);
    setConversationId(null);
  }, []);

  const openWidget = useCallback(() => setIsWidgetOpen(true), []);
  const closeWidget = useCallback(() => setIsWidgetOpen(false), []);
  const toggleWidget = useCallback(() => setIsWidgetOpen((prev) => !prev), []);

  return (
    <AgentChatContext.Provider
      value={{
        messages,
        conversationId,
        isPending,
        isWidgetOpen,
        sendMessage,
        clearChat,
        openWidget,
        closeWidget,
        toggleWidget,
      }}
    >
      {children}
    </AgentChatContext.Provider>
  );
}
