import { useEffect, useRef, useState } from 'react';
import { useAgentChat } from '../context/AgentChatContext';
import FormattedMessage from '../components/FormattedMessage';
import '../styles/agentChat.css';

/* ------------------------------------------------------------------ */
/* SVG Icons                                                          */
/* ------------------------------------------------------------------ */

function RobotIcon({ className = 'svg-icon' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="4" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8.01" y2="16" strokeWidth="2.4" />
      <line x1="16" y1="16" x2="16.01" y2="16" strokeWidth="2.4" />
      <path d="M10 19h4" />
    </svg>
  );
}

function UserAvatarIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
    </svg>
  );
}

function PaperclipIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="19" height="19">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function SendPlaneIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

function LayersStackIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
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

const DEFAULT_STAGES = [
  'Requirement Analysis',
  'Supplier Discovery',
  'Quote Collection',
  'Evaluation & Comparison',
  'Recommendation',
];

const QUICK_PROMPTS = [
  'Show supplier options',
  "What's the current status?",
  'Compare top 3 quotes',
  'I need 20 laptops for my R&D team with ₹20,00,000 budget in Mumbai',
];

/* ------------------------------------------------------------------ */
/* Subcomponents                                                      */
/* ------------------------------------------------------------------ */

function StepsChecklist({ steps }) {
  if (!steps?.length) return null;
  return (
    <ul className="chat-steps-list">
      {steps.map((s, i) => {
        const isDone = s.status === 'done' || s.done;
        const isCurrent = s.status === 'current';

        return (
          <li key={i} className={`chat-step-item chat-step-item--${isDone ? 'done' : isCurrent ? 'current' : 'pending'}`}>
            <span className="chat-step-icon">
              {isDone ? (
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.4" width="14" height="14">
                  <path d="M3.5 8.5L6.5 11.5L12.5 4.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : isCurrent ? (
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeDasharray="3 2" width="14" height="14">
                  <circle cx="8" cy="8" r="6" />
                </svg>
              ) : (
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" width="14" height="14">
                  <circle cx="8" cy="8" r="6" />
                  <path d="M8 5v3.2l2.2 1.4" strokeLinecap="round" />
                </svg>
              )}
            </span>
            <span className="chat-step-label">{s.label}</span>
          </li>
        );
      })}
    </ul>
  );
}

function ProcurementProgressCard({ progress }) {
  if (!progress) return null;
  const stages = progress.stages || DEFAULT_STAGES;
  const currentIdx = typeof progress.currentStageIndex === 'number'
    ? progress.currentStageIndex
    : stages.findIndex((s) => s.toLowerCase() === (progress.currentStage || '').toLowerCase());

  return (
    <div className="chat-progress-card">
      <div className="chat-progress-header">
        <span className="chat-progress-icon"><LayersStackIcon /></span>
        <strong className="chat-progress-title">Procurement in Progress</strong>
      </div>
      <div className="chat-progress-stepper">
        {stages.map((stage, i) => {
          const isDone = i < currentIdx;
          const isCurrent = i === currentIdx;
          const isLast = i === stages.length - 1;

          return (
            <div key={stage} className={`chat-stepper-node ${isLast ? 'chat-stepper-node--last' : ''}`}>
              <div className="chat-node-indicator">
                <div
                  className={`chat-node-circle ${
                    isDone ? 'chat-node-circle--done' : isCurrent ? 'chat-node-circle--current' : 'chat-node-circle--pending'
                  }`}
                >
                  {isDone ? (
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.5" width="10" height="10">
                      <path d="M3 7.5L5.5 10L11 4" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : isCurrent ? (
                    <div className="chat-node-dot" />
                  ) : null}
                </div>
                {!isLast && (
                  <div className={`chat-node-track ${isDone ? 'chat-node-track--done' : ''}`} />
                )}
              </div>
              <span className={`chat-node-label ${isCurrent ? 'chat-node-label--current' : isDone ? 'chat-node-label--done' : ''}`}>
                {stage}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Full-Screen Minimalist Agent Chat View                             */
/* ------------------------------------------------------------------ */

export default function AgentChat() {
  const { messages, isPending, sendMessage, clearChat } = useAgentChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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

  return (
    <div className="chat-fullscreen-container">
      {/* Top Header */}
      <header className="chat-minimal-header">
        <div className="chat-header-brand">
          <div className="chat-bot-avatar chat-bot-avatar--lg chat-bot-avatar--glow">
            <RobotIcon className="chat-bot-svg" />
          </div>
          <div>
            <h1 className="chat-main-title">Chat with Kraya Agent</h1>
            <p className="chat-main-subtitle">
              Describe your procurement need, ask for updates, compare suppliers, or get real-time recommendations.
            </p>
          </div>
        </div>

        <div className="chat-header-right">
          <div className="chat-agent-online-pill">
            <span className="online-indicator-dot" />
            <span>Agent Online</span>
          </div>
          <button
            type="button"
            className="chat-clear-btn"
            onClick={clearChat}
            title="Start fresh conversation"
          >
            <RefreshIcon />
            <span>Reset</span>
          </button>
        </div>
      </header>

      {/* Messages Scroll Feed */}
      <main className="chat-scroll-area">
        <div className="chat-feed-column">
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div key={msg.id} className={`chat-msg-row chat-msg-row--${isUser ? 'user' : 'agent'}`}>
                {!isUser && (
                  <div className="chat-bot-avatar">
                    <RobotIcon className="chat-bot-svg" />
                  </div>
                )}
                <div className="chat-bubble-container">
                  <div className={`chat-bubble chat-bubble--${isUser ? 'user' : 'agent'}`}>
                    {msg.typing ? (
                      <div className="chat-typing">
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                      </div>
                    ) : (
                      <>
                        <FormattedMessage text={msg.text} />
                        {msg.steps && <StepsChecklist steps={msg.steps} />}
                        {msg.followUp && <p className="chat-bubble-followup">{msg.followUp}</p>}
                      </>
                    )}
                  </div>
                  {msg.progress && <ProcurementProgressCard progress={msg.progress} />}
                  <span className="chat-msg-time">{formatTime(msg.timestamp)}</span>
                </div>
                {isUser && (
                  <div className="chat-user-avatar">
                    <UserAvatarIcon />
                  </div>
                )}
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Quick Prompts */}
      <div className="chat-prompts-row">
        <div className="chat-prompts-inner">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="chat-prompt-chip"
              onClick={() => handleSend(prompt)}
              disabled={isPending}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Bottom Input Capsule */}
      <footer className="chat-bottom-dock">
        <div className="chat-input-capsule">
          <button
            className="chat-attachment-btn"
            type="button"
            aria-label="Attach documents"
            title="Attach specification or RFQ"
          >
            <PaperclipIcon />
          </button>
          <textarea
            ref={inputRef}
            className="chat-textarea"
            placeholder='Ask something... (e.g., "Show supplier options", "What&apos;s the current status?", "Compare top 3 quotes")'
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isPending}
          />
          <button
            className="chat-submit-btn"
            type="button"
            aria-label="Send message"
            onClick={() => handleSend()}
            disabled={!input.trim() || isPending}
          >
            <SendPlaneIcon />
          </button>
        </div>
      </footer>
    </div>
  );
}
