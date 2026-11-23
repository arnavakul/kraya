import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAgentChat } from '../context/AgentChatContext';
import FormattedMessage from './FormattedMessage';
import '../styles/floatingChatbot.css';

/* ------------------------------------------------------------------ */
/* Icons                                                              */
/* ------------------------------------------------------------------ */

function RobotIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="22" height="22">
      <rect x="3" y="11" width="18" height="10" rx="4" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8.01" y2="16" strokeWidth="2.4" />
      <line x1="16" y1="16" x2="16.01" y2="16" strokeWidth="2.4" />
      <path d="M10 19h4" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

function ExpandIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function formatTime(date) {
  const d = date instanceof Date ? date : new Date(date);
  let h = d.getHours();
  const m = d.getMinutes().toString().padStart(2, '0');
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${h}:${m} ${ampm}`;
}

const QUICK_PROMPTS = [
  'Show supplier options',
  "What's the current status?",
  'Compare top 3 quotes',
];

export default function FloatingChatbot() {
  const { messages, isPending, isWidgetOpen, sendMessage, toggleWidget, closeWidget } = useAgentChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Hide floating launcher if already on the full-screen /agents page
  const isAgentsPage = location.pathname.startsWith('/agents');

  useEffect(() => {
    if (isWidgetOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isWidgetOpen]);

  if (isAgentsPage) return null;

  function handleSend(textToSend) {
    const text = (textToSend || input).trim();
    if (!text || isPending) return;
    setInput('');
    sendMessage(text);
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function goToFullScreen() {
    closeWidget();
    navigate('/agents');
  }

  return (
    <div className="floating-chat-root">
      {/* Floating launcher button */}
      {!isWidgetOpen && (
        <button
          className="floating-chat-trigger"
          type="button"
          onClick={toggleWidget}
          aria-label="Open Kraya AI chat assistant"
        >
          <div className="floating-trigger-icon">
            <RobotIcon />
            <span className="floating-trigger-pulse" />
          </div>
          <span className="floating-trigger-label">Ask Kraya AI</span>
        </button>
      )}

      {/* Floating chat drawer window */}
      {isWidgetOpen && (
        <div className="floating-chat-window">
          {/* Header */}
          <div className="floating-chat-header">
            <div className="floating-header-left">
              <div className="floating-bot-badge">
                <RobotIcon />
              </div>
              <div className="floating-header-titles">
                <span className="floating-agent-name">Kraya Agent</span>
                <span className="floating-agent-status">● Online • AI Co-pilot</span>
              </div>
            </div>

            <div className="floating-header-actions">
              <button
                type="button"
                className="floating-action-btn"
                onClick={goToFullScreen}
                title="Open in full screen"
                aria-label="Full screen"
              >
                <ExpandIcon />
              </button>
              <button
                type="button"
                className="floating-action-btn"
                onClick={closeWidget}
                title="Minimize chat"
                aria-label="Close"
              >
                <CloseIcon />
              </button>
            </div>
          </div>

          {/* Messages feed */}
          <div className="floating-chat-feed">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div key={msg.id} className={`floating-msg-row floating-msg-row--${isUser ? 'user' : 'agent'}`}>
                  {!isUser && (
                    <div className="floating-avatar-agent">
                      <RobotIcon />
                    </div>
                  )}
                  <div className="floating-bubble-wrap">
                    <div className={`floating-bubble floating-bubble--${isUser ? 'user' : 'agent'}`}>
                      {msg.typing ? (
                        <div className="floating-typing">
                          <span />
                          <span />
                          <span />
                        </div>
                      ) : (
                        <>
                          <FormattedMessage text={msg.text} />

                          {msg.steps && (
                            <ul className="floating-steps-list">
                              {msg.steps.map((s, idx) => (
                                <li key={idx} className={`floating-step floating-step--${s.status || (s.done ? 'done' : 'pending')}`}>
                                  <span className="step-bullet">{s.status === 'done' || s.done ? '✓' : s.status === 'current' ? '◌' : '•'}</span>
                                  <span>{s.label}</span>
                                </li>
                              ))}
                            </ul>
                          )}

                          {msg.followUp && (
                            <p className="floating-followup">{msg.followUp}</p>
                          )}
                        </>
                      )}
                    </div>
                    <span className="floating-msg-time">{formatTime(msg.timestamp)}</span>
                  </div>
                  {isUser && (
                    <div className="floating-avatar-user">
                      <UserIcon />
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="floating-quick-prompts">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="floating-prompt-chip"
                onClick={() => handleSend(prompt)}
                disabled={isPending}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="floating-input-bar">
            <textarea
              className="floating-input"
              rows={1}
              placeholder='Ask something... (e.g. "Show supplier options")'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isPending}
            />
            <button
              className="floating-send-btn"
              type="button"
              onClick={() => handleSend()}
              disabled={!input.trim() || isPending}
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
