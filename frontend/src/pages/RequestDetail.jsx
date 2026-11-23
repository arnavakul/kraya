import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { canManage } from '../lib/permissions';
import { useRequest, useRequestAudit, useTransition, useRunAgentWorkflow, useLatestAgentWorkflow, useApproveAndDispatchRfq, useSendThreadMessage, useSyncWorkflowStatus, useApproveThreadDraft, useDiscardThreadDraft, usePollInboxAndProcess, useGmailStatus, useConfigureGmail } from '../lib/requests';
import { REASON_STATUSES, formatDate, formatDateTime, formatMoney, formatStatus } from '../lib/format';
import { agentWorkflowView, createGmailComposeUrl, createMailtoUrl } from '../lib/agentWorkflow';
import StatusBadge from '../components/StatusBadge';
import RequestStepper from '../components/RequestStepper';
import { ErrorState, Loading } from '../components/PageState';

function actionLabel(status) {
  if (status === 'SUBMITTED') return 'Submit request';
  if (status === 'CANCELLED') return 'Cancel request';
  if (status === 'REJECTED') return 'Reject request';
  return `Move to ${formatStatus(status)}`;
}

function describe(event) {
  switch (event.action) {
    case 'REQUEST_CREATED': return 'Request created';
    case 'REQUEST_UPDATED': return 'Request edited';
    case 'REQUEST_STATUS_CHANGED':
      return `Moved from ${formatStatus(event.previousState)} to ${formatStatus(event.newState)}`;
    default: return event.action;
  }
}

export default function RequestDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data: r, isPending, isError, error, refetch } = useRequest(id);
  const audit = useRequestAudit(id);
  const transition = useTransition(id);
  const agentRun = useRunAgentWorkflow(id);
  const latestAgentRun = useLatestAgentWorkflow(id);
  const approveAndDispatch = useApproveAndDispatchRfq(id);
  const sendThreadMessage = useSendThreadMessage(id);
  const syncWorkflowStatus = useSyncWorkflowStatus(id);
  const approveThreadDraft = useApproveThreadDraft(id);
  const discardThreadDraft = useDiscardThreadDraft(id);
  const pollInbox = usePollInboxAndProcess(id);
  const gmailStatus = useGmailStatus();
  const configureGmail = useConfigureGmail();

  const [customReply, setCustomReply] = useState('');
  const [autoAiReply, setAutoAiReply] = useState(true);
  const [editedDraftBody, setEditedDraftBody] = useState('');
  const [showGmailConfig, setShowGmailConfig] = useState(false);
  const [gmailEmail, setGmailEmail] = useState('');
  const [gmailAppPass, setGmailAppPass] = useState('');

  // Always resolve latest state: thread approval > discard > message > status sync > newly approved data > fetched latest data > previous run data
  const currentRunData = approveThreadDraft.data || discardThreadDraft.data || sendThreadMessage.data || syncWorkflowStatus.data || approveAndDispatch.data || latestAgentRun.data || agentRun.data;
  const workflowView = agentWorkflowView(currentRunData);

  function handleApproveAndOpenGmail(draft) {
    const gmailUrl = draft.gmailUrl || createGmailComposeUrl({
      to: draft.recipientEmail,
      subject: draft.email_subject,
      body: draft.email_body,
    });
    if (gmailUrl) {
      window.open(gmailUrl, '_blank', 'noopener,noreferrer');
    }
    approveAndDispatch.mutate({ rfqId: draft.rfq_id });
  }

  function handleAutonomousDispatch(draft) {
    approveAndDispatch.mutate({ rfqId: draft.rfq_id });
  }

  const [asking, setAsking] = useState(null); // status that is waiting for a written reason
  const [reason, setReason] = useState('');
  const [actionError, setActionError] = useState('');

  if (isPending) return <Loading label="Loading request…" />;
  if (isError) {
    return (
      <>
        <Link className="rq-back" to="/requests">← All requests</Link>
        <ErrorState error={error} onRetry={refetch} />
      </>
    );
  }

  const manager = canManage(user);
  const forward = r.allowedNextStatuses.filter((s) => !REASON_STATUSES.has(s));
  const closing = r.allowedNextStatuses.filter((s) => REASON_STATUSES.has(s));

  function run(to, why) {
    setActionError('');
    transition.mutate({ to, reason: why }, {
      onSuccess: () => {
        setAsking(null);
        setReason('');
      },
      onError: (err) => setActionError(err.message),
    });
  }

  function choose(to) {
    if (REASON_STATUSES.has(to)) {
      setAsking(to);
      setReason('');
      setActionError('');
    } else {
      run(to);
    }
  }

  return (
    <>
      <Link className="rq-back" to="/requests">← All requests</Link>

      <div className="rq-head">
        <div>
          <span className="rq-ref">{r.reference}</span>
          <StatusBadge status={r.status} />
          <h1 className="rq-detail-title">{r.title}</h1>
        </div>
      </div>

      {(r.status === 'REJECTED' || r.status === 'CANCELLED') && (
        <div className="rq-banner" role="status">
          <strong>{formatStatus(r.status)}.</strong> {r.statusReason}
        </div>
      )}

      <RequestStepper status={r.status} />

      {manager && (r.status === 'DRAFT' || r.allowedNextStatuses.length > 0) && (
        <div className="rq-actions rq-actions--top">
          {forward.map((s, i) => (
            <button key={s} type="button" className={i === 0 ? 'btn' : 'btn ghost'}
                    disabled={transition.isPending} onClick={() => choose(s)}>
              {actionLabel(s)}
            </button>
          ))}
          {r.status === 'DRAFT' && <Link className="btn ghost" to={`/requests/${r.id}/edit`}>Edit</Link>}
          {closing.map((s) => (
            <button key={s} type="button" className="btn danger"
                    disabled={transition.isPending} onClick={() => choose(s)}>
              {actionLabel(s)}
            </button>
          ))}
        </div>
      )}

      {asking && (
        <div className="rq-reason">
          <label className="rq-label" htmlFor="reason">Reason for this change (required)</label>
          <textarea id="reason" className="rq-textarea" maxLength={500} value={reason}
                    onChange={(e) => setReason(e.target.value)} />
          <div className="rq-actions">
            <button className="btn danger" type="button"
                    disabled={!reason.trim() || transition.isPending}
                    onClick={() => run(asking, reason.trim())}>
              {transition.isPending ? 'Saving…' : `Confirm: ${actionLabel(asking)}`}
            </button>
            <button className="btn ghost" type="button" onClick={() => setAsking(null)}>Back</button>
          </div>
        </div>
      )}

      {actionError && <p className="rq-error" role="alert">{actionError}</p>}

      {manager && r.status !== 'DRAFT' && (
        <section className="card rq-section">
          <div className="rq-workflow-top">
            <div>
              <h2 className="rq-h2">AI Sourcing Workflow</h2>
              <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
                Automated supplier discovery, requirement validation, RFQ generation, and email dispatch.
              </p>
            </div>
            <button className="btn" type="button" disabled={agentRun.isPending}
                    onClick={() => agentRun.mutate()}>
              {agentRun.isPending ? 'Running agents…' : 'Run sourcing agents'}
            </button>
          </div>

          {agentRun.isError && <p className="rq-error" role="alert">{agentRun.error.message}</p>}
          {approveAndDispatch.isError && <p className="rq-error" role="alert">{approveAndDispatch.error.message}</p>}

          {workflowView && (
            <div className="rq-workflow-card-body">
              <div className="rq-workflow-meta-chips">
                <span className="rq-workflow-run-chip">
                  <strong>Workflow:</strong> <span className="rq-status-pill">{workflowView.status}</span>
                </span>
                {workflowView.runStatus && (
                  <span className="rq-workflow-run-chip"><strong>Run:</strong> {workflowView.runStatus}</span>
                )}
                {workflowView.completedAt && (
                  <span className="rq-workflow-run-chip"><strong>Completed:</strong> {formatDateTime(workflowView.completedAt)}</span>
                )}
              </div>

              {workflowView.errorMessage && <p className="rq-error" role="alert">{workflowView.errorMessage}</p>}

              {workflowView.clarificationQuestions.length > 0 && (
                <div className="rq-clarifications-box">
                  <strong>Clarifications needed:</strong>
                  <ul>
                    {workflowView.clarificationQuestions.map((question) => <li key={question}>{question}</li>)}
                  </ul>
                </div>
              )}

              {/* Qualified & Assessed Suppliers */}
              {workflowView.qualifiedOrReview.length > 0 && (
                <div className="rq-suppliers-evaluation-block">
                  <span className="rq-suppliers-eval-title">Qualified & Sourced Suppliers</span>
                  <div className="rq-qualified-suppliers-list">
                    {workflowView.qualifiedOrReview.map((supplier) => (
                      <div key={supplier.supplier_id} className="rq-qualified-supplier-row">
                        <div>
                          <div className="rq-qualified-supplier-name">{supplier.supplierName}</div>
                          <div className="rq-qualified-supplier-reason">{supplier.reason}</div>
                        </div>
                        <span className={`rq-decision-badge rq-decision--${supplier.decision}`}>
                          {supplier.decision === 'manual_review' ? 'Manual Review' : 'Qualified'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collapsed Accordion for Excluded Suppliers */}
              {workflowView.excluded.length > 0 && (
                <details className="rq-excluded-accordion">
                  <summary>
                    Assessed suppliers ({workflowView.excluded.length} excluded — click to expand)
                  </summary>
                  <ul className="rq-excluded-list">
                    {workflowView.excluded.map((supplier) => (
                      <li key={supplier.supplier_id} className="rq-excluded-item">
                        <strong>{supplier.supplierName}</strong>
                        <span className="rq-excluded-reason">{supplier.reason}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              {/* RFQ Email Drafts & Live Dispatch */}
              {workflowView.rfqDrafts.length > 0 && (
                <div className="rq-suppliers-evaluation-block">
                  <span className="rq-suppliers-eval-title">Quotation Email & Dispatch</span>
                  {workflowView.rfqDrafts.map((draft) => {
                    const isDispatched = draft.status === 'DISPATCHED' ||
                      workflowView.status === 'DISPATCHED' ||
                      workflowView.dispatches.some((d) => d.rfq_id === draft.rfq_id);
                    const dispatchReceipt = workflowView.dispatches.find((d) => d.rfq_id === draft.rfq_id) || draft.dispatch_receipt;

                    return (
                      <article key={draft.rfq_id} className={`rq-rfq-card ${isDispatched ? 'rq-rfq-card--dispatched' : ''}`}>
                        <div className="rq-rfq-card-head">
                          <div className="rq-rfq-head-left">
                            <span className="rq-rfq-icon-badge">{isDispatched ? '✉✓' : '✉'}</span>
                            <h3 className="rq-rfq-head-title">Quotation Request Email</h3>
                          </div>
                          <span className={`rq-decision-badge ${isDispatched ? 'rq-decision--eligible' : 'rq-decision--manual_review'}`}>
                            {isDispatched ? '✓ Dispatched to Supplier' : 'Awaiting Approval'}
                          </span>
                        </div>

                        <div className="rq-rfq-meta-table">
                          <div className="rq-rfq-meta-row">
                            <span className="rq-rfq-meta-label">Recipient:</span>
                            <span className="rq-rfq-meta-val">
                              <strong>{draft.supplier?.name}</strong> &lt;{draft.recipient_email || draft.supplier?.email || 'supplier@domain.com'}&gt;
                            </span>
                          </div>
                          <div className="rq-rfq-meta-row">
                            <span className="rq-rfq-meta-label">Subject:</span>
                            <span className="rq-rfq-meta-val">{draft.email_subject}</span>
                          </div>
                        </div>

                        <div className="rq-rfq-body-container">
                          <pre className="rq-rfq-body-preview">{draft.email_body}</pre>
                        </div>

                        <div className="rq-rfq-actions-footer">
                          {isDispatched ? (
                            <div className="rq-dispatch-success-banner" style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
                              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                <span className="rq-dispatch-check-icon">✓</span>
                                <div>
                                  <div><strong>Quotation email successfully approved & dispatched to supplier!</strong></div>
                                  <div className="rq-dispatch-receipt-meta">
                                    <span>Recipient: <strong style={{ color: '#f2f5f2' }}>{draft.recipientEmail || draft.supplier?.contact_email || draft.supplier?.email || 'Supplier'}</strong></span>
                                    <span>Tracking ID: <code className="rq-tracking-chip">{dispatchReceipt?.tracking_id || 'TRK-VERIFIED'}</code></span>
                                    <span>Status: <span style={{ color: '#5fdc5a', fontWeight: 'bold' }}>SENT</span></span>
                                    {dispatchReceipt?.timestamp && <span>At: {formatDateTime(dispatchReceipt.timestamp)}</span>}
                                  </div>
                                </div>
                              </div>
                              <a
                                href={draft.gmailUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn ghost"
                                style={{ fontSize: '13px', padding: '6px 14px', whiteSpace: 'nowrap' }}
                              >
                                ✉️ View in Gmail ↗
                              </a>
                            </div>
                          ) : (
                            <>
                              <div className="rq-rfq-actions-left">
                                <strong>Human-in-the-Loop Verification & Dispatch</strong>
                                <span className="rq-rfq-dispatch-help">
                                  Review quotation requirements above. Choose to open and send directly from your Gmail, or trigger autonomous agent dispatch.
                                </span>
                                {approveAndDispatch.isError && (
                                  <span className="rq-error" style={{ marginTop: '4px' }}>
                                    Dispatch error: {approveAndDispatch.error.message}
                                  </span>
                                )}
                              </div>
                              <div className="rq-rfq-actions-right">
                                <div className="rq-rfq-btn-group">
                                  <button
                                    type="button"
                                    className="rq-gmail-btn"
                                    disabled={approveAndDispatch.isPending}
                                    onClick={() => handleApproveAndOpenGmail(draft)}
                                    title="Open directly in Gmail compose in a new tab and approve in Kraya"
                                  >
                                    ✉️ {approveAndDispatch.isPending ? 'Processing…' : 'Approve & Open in Gmail ↗'}
                                  </button>
                                  <button
                                    type="button"
                                    className="rq-agent-dispatch-btn"
                                    disabled={approveAndDispatch.isPending}
                                    onClick={() => handleAutonomousDispatch(draft)}
                                    title="Approve and dispatch autonomously via background agent mailer"
                                  >
                                    ⚡ Autonomous Dispatch
                                  </button>
                                </div>
                                <div className="rq-alt-actions">
                                  <a
                                    href={draft.mailtoUrl}
                                    className="rq-email-link"
                                    onClick={() => approveAndDispatch.mutate({ rfqId: draft.rfq_id })}
                                    title="Open in your default desktop mail app (Outlook, Apple Mail, etc.)"
                                  >
                                    Open in default mail client (mailto) ↗
                                  </a>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}

              {/* Supplier Email Thread & Autonomous AI Negotiation */}
              {(workflowView.status === 'DISPATCHED' || (workflowView.emailThread && workflowView.emailThread.length > 0)) && (
                <div className="rq-thread-section">
                  <div className="rq-thread-container">
                    <div className="rq-thread-head">
                      <h3 className="rq-thread-title">
                        <span>🤖 Autonomous Negotiation & Email Tracking Hub</span>
                      </h3>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span className="rq-status-pill" style={{ background: '#1c1335', color: '#c084fc', border: '1px solid #4a2d7a' }}>
                          AI Co-Pilot: Active
                        </span>
                        {r.status === 'VALIDATING' && (
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: '12px', padding: '4px 10px' }}
                            disabled={syncWorkflowStatus.isPending}
                            onClick={() => syncWorkflowStatus.mutate()}
                          >
                            {syncWorkflowStatus.isPending ? 'Syncing…' : '⚡ Advance Stage to Quoting'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Messages in the thread */}
                    <div className="rq-thread-messages">
                      {/* If emailThread is empty, show initial outbound RFQ */}
                      {(!workflowView.emailThread || workflowView.emailThread.length === 0) && workflowView.rfqDrafts.map((draft) => (
                        <div key={draft.rfq_id} className="rq-thread-msg rq-thread-msg--buyer">
                          <div className="rq-msg-header">
                            <div>
                              <span className="rq-msg-sender">✉️ Kraya Sourcing Agent (on your behalf)</span>
                              <div style={{ fontSize: '12px', color: '#8fa08f', marginTop: '2px' }}>
                                To: {draft.recipientEmail || 'Supplier'} • Subject: {draft.email_subject}
                              </div>
                            </div>
                            <span className="rq-decision-badge rq-decision--eligible">
                              Stage: Quoting
                            </span>
                          </div>
                          <pre className="rq-msg-content">{draft.email_body}</pre>
                        </div>
                      ))}

                      {/* Dynamic thread messages */}
                      {workflowView.emailThread && workflowView.emailThread.map((msg) => {
                        const isAgent = msg.senderType === 'agent';
                        const isSupplier = msg.senderType === 'supplier';
                        return (
                          <div
                            key={msg.id}
                            className={`rq-thread-msg ${isAgent ? 'rq-thread-msg--agent' : isSupplier ? 'rq-thread-msg--supplier' : 'rq-thread-msg--buyer'}`}
                          >
                            <div className="rq-msg-header">
                              <div>
                                <span className="rq-msg-sender">
                                  {isAgent ? '🤖 ' : isSupplier ? '🏢 ' : '✉️ '}
                                  {msg.sender}
                                </span>
                                {msg.subject && (
                                  <div style={{ fontSize: '12px', color: '#8fa08f', marginTop: '2px' }}>
                                    Subject: {msg.subject}
                                  </div>
                                )}
                              </div>
                              <span className="rq-msg-time">{formatDateTime(msg.timestamp)}</span>
                            </div>

                            {msg.strategy && (
                              <div className="rq-strategy-box">
                                <strong>💡 AI Negotiation Strategy:</strong> {msg.strategy}
                              </div>
                            )}

                            <pre className="rq-msg-content">{msg.content}</pre>
                          </div>
                        );
                      })}
                    </div>

                    {/* AI Drafted Negotiation Response (Awaiting Human Approval) */}
                    {workflowView.pendingAiDraft && (
                      <div className="rq-pending-draft-card">
                        <div className="rq-pending-draft-head">
                          <div className="rq-pending-draft-title">
                            <span>🤖 AI Drafted Negotiation Reply</span>
                            <span className="rq-pending-approval-badge">Human Approval Required</span>
                          </div>
                          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                            To: {workflowView.pendingAiDraft.recipient || 'Supplier'}
                          </span>
                        </div>

                        <div className="rq-pending-draft-body">
                          {workflowView.pendingAiDraft.strategy && (
                            <div className="rq-strategy-box">
                              <strong>💡 AI Negotiation Strategy:</strong> {workflowView.pendingAiDraft.strategy}
                            </div>
                          )}
                          <div style={{ fontSize: '12.5px', color: '#cbd5e1' }}>
                            <strong>Subject:</strong> {workflowView.pendingAiDraft.subject}
                          </div>
                          <label htmlFor="draftTextarea" style={{ fontSize: '12px', color: '#94a3b8' }}>
                            Review or edit the AI's drafted email below before approving:
                          </label>
                          <textarea
                            id="draftTextarea"
                            className="rq-draft-edit-textarea"
                            value={editedDraftBody !== '' ? editedDraftBody : (workflowView.pendingAiDraft.body || '')}
                            onChange={(e) => setEditedDraftBody(e.target.value)}
                          />
                        </div>

                        <div className="rq-draft-actions-bar">
                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <button
                              type="button"
                              className="rq-gmail-btn"
                              disabled={approveThreadDraft.isPending}
                              onClick={() => {
                                const bodyToSend = editedDraftBody !== '' ? editedDraftBody : (workflowView.pendingAiDraft.body || '');
                                const recipient = workflowView.rfqDrafts[0]?.recipientEmail || 'akulgameristicofficial@gmail.com';
                                const gmailUrl = createGmailComposeUrl({
                                  to: recipient,
                                  subject: workflowView.pendingAiDraft.subject,
                                  body: bodyToSend,
                                });
                                window.open(gmailUrl, '_blank', 'noopener,noreferrer');
                                approveThreadDraft.mutate({
                                  editedBody: bodyToSend,
                                  editedSubject: workflowView.pendingAiDraft.subject,
                                });
                                setEditedDraftBody('');
                              }}
                            >
                              ✉️ {approveThreadDraft.isPending ? 'Sending…' : 'Approve & Send via Gmail ↗'}
                            </button>

                            <button
                              type="button"
                              className="btn"
                              disabled={approveThreadDraft.isPending}
                              onClick={() => {
                                const bodyToSend = editedDraftBody !== '' ? editedDraftBody : (workflowView.pendingAiDraft.body || '');
                                approveThreadDraft.mutate({
                                  editedBody: bodyToSend,
                                  editedSubject: workflowView.pendingAiDraft.subject,
                                });
                                setEditedDraftBody('');
                              }}
                            >
                              {approveThreadDraft.isPending ? 'Dispatching…' : '✓ Approve & Send Negotiation Email'}
                            </button>
                          </div>

                          <button
                            type="button"
                            className="btn ghost"
                            style={{ color: '#ef4444' }}
                            disabled={discardThreadDraft.isPending}
                            onClick={() => {
                              discardThreadDraft.mutate();
                              setEditedDraftBody('');
                            }}
                          >
                            ✕ Discard Draft
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Thread controls and AI simulation */}
                    <div className="rq-thread-controls">
                      {pollInbox.isPending && (
                        <div className="rq-stage-sync-banner" style={{ background: 'rgba(99, 102, 241, 0.1)', borderColor: '#6366f1', color: '#a5b4fc' }}>
                          <span>🤖 Gemini AI Agent is reading the supplier email & contacting them directly with negotiation terms…</span>
                        </div>
                      )}
                      {pollInbox.data && (
                        <div className="rq-stage-sync-banner">
                          <span>✓ {pollInbox.data.message}</span>
                        </div>
                      )}
                      {pollInbox.isError && (
                        <p className="rq-error" role="alert">Inbox processing error: {pollInbox.error.message}</p>
                      )}

                      {/* Live Gmail IMAP Integration Banner / Setup */}
                      <div className="rq-gmail-integration-card">
                        <div className="rq-gmail-bar-header">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '16px' }}>✉️</span>
                            <strong style={{ color: '#f2f5f2' }}>Live Gmail Integration:</strong>
                            {gmailStatus.data?.connected ? (
                              <span className="rq-decision-badge rq-decision--eligible" style={{ fontSize: '12px' }}>
                                ✓ Connected to {gmailStatus.data.account} ({gmailStatus.data.inbox_count} INBOX emails)
                              </span>
                            ) : (
                              <span className="rq-decision-badge rq-decision--manual_review" style={{ fontSize: '12px' }}>
                                ○ Not Connected (App Password required for live polling)
                              </span>
                            )}
                          </div>
                          <button
                            type="button"
                            className="btn ghost"
                            style={{ fontSize: '12px', padding: '4px 12px' }}
                            onClick={() => setShowGmailConfig(!showGmailConfig)}
                          >
                            {showGmailConfig ? '✕ Close Settings' : '⚙️ Connect / Test Gmail Account'}
                          </button>
                        </div>

                        {showGmailConfig && (
                          <div className="rq-gmail-config-panel">
                            <p style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>
                              To allow Gemini to autonomously read incoming emails from suppliers, enter your Gmail address and a 16-character Google App Password (generate one at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" style={{ color: '#a6f03c', textDecoration: 'underline' }}>Google Account &gt; Security &gt; App Passwords</a>):
                            </p>
                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                              <input
                                type="email"
                                placeholder="your.email@gmail.com"
                                value={gmailEmail}
                                onChange={(e) => setGmailEmail(e.target.value)}
                                className="rq-gmail-input"
                              />
                              <input
                                type="password"
                                placeholder="16-character App Password"
                                value={gmailAppPass}
                                onChange={(e) => setGmailAppPass(e.target.value)}
                                className="rq-gmail-input"
                              />
                              <button
                                type="button"
                                className="btn"
                                disabled={!gmailEmail || !gmailAppPass || configureGmail.isPending}
                                onClick={() => {
                                  configureGmail.mutate({
                                    email: gmailEmail.trim(),
                                    app_password: gmailAppPass.trim(),
                                  });
                                }}
                              >
                                {configureGmail.isPending ? 'Connecting…' : 'Save & Test Connection'}
                              </button>
                            </div>
                            {configureGmail.data && (
                              <div style={{ marginTop: '8px', fontSize: '12.5px', color: configureGmail.data.connected ? '#5fdc5a' : '#ef4444' }}>
                                {configureGmail.data.message}
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {(() => {
                        const primaryDraft = workflowView.rfqDrafts?.[0];
                        const targetSupplierName = primaryDraft?.supplier?.name || primaryDraft?.supplierName || workflowView.qualifiedOrReview?.[0]?.supplierName || 'TechNova Solutions';
                        const targetSupplierEmail = primaryDraft?.recipientEmail || primaryDraft?.recipient_email || primaryDraft?.supplier?.contact_email || primaryDraft?.supplier?.email || 'akulgameristicofficial@gmail.com';
                        const targetItemTitle = r?.items?.[0]?.name || r?.title || 'Required Items';
                        const targetBudget = r?.budgetAmount || 1850000;
                        const quoteAmount = Math.round(targetBudget * 1.05);
                        const negotiatedAmount = Math.round(targetBudget * 0.95);
                        const formattedQuote = formatMoney(quoteAmount, r?.currencyCode || 'INR');
                        const formattedNegotiated = formatMoney(negotiatedAmount, r?.currencyCode || 'INR');

                        return (
                          <div className="rq-quick-sim-bar">
                            <span className="rq-sim-label">Autonomous Email Actions:</span>
                            <button
                              type="button"
                              className="rq-sim-pill-btn"
                              disabled={pollInbox.isPending}
                              onClick={() =>
                                pollInbox.mutate({
                                  supplier_name: targetSupplierName,
                                  supplier_email: targetSupplierEmail,
                                  incoming_message:
                                    `Dear Procurement Team,\n\nThank you for reaching out. We are pleased to provide our formal quotation for ${targetItemTitle}:\n- Quoted Total: ${formattedQuote}\n- Delivery Timeline: 12 days\n- Warranty: 3-year enterprise manufacturer warranty included\n- Payment Terms: Net 30 days\n\nPlease let us know if you would like to proceed.\n\nBest regards,\nSales Director\n${targetSupplierName}`,
                                  auto_reply: autoAiReply,
                                })
                              }
                              title="Simulate supplier quotation response. Gemini will read it, analyze price, and immediately reply with a negotiation counter-offer."
                            >
                              ⚡ Quote Received ({formattedQuote})
                            </button>

                            <button
                              type="button"
                              className="rq-sim-pill-btn"
                              style={{ borderColor: '#3b82f6', color: '#60a5fa' }}
                              disabled={pollInbox.isPending}
                              onClick={() =>
                                pollInbox.mutate({
                                  supplier_name: targetSupplierName,
                                  supplier_email: targetSupplierEmail,
                                  incoming_message:
                                    `Dear Kraya Team,\n\nWe accept your counter-proposal of ${formattedNegotiated} for the full order with Net-30 payment terms and 3-year warranty. We look forward to receiving your official Purchase Order.\n\nBest regards,\nSales Director\n${targetSupplierName}`,
                                  auto_reply: true,
                                })
                              }
                              title="Simulate supplier accepting negotiated price. Moves request to Approval & PO Drafting."
                            >
                              🤝 Supplier Agrees ({formattedNegotiated})
                            </button>

                            <button
                              type="button"
                              className="rq-sim-pill-btn"
                              style={{ borderColor: '#8b5cf6', color: '#c4b5fd' }}
                              disabled={pollInbox.isPending}
                              onClick={() =>
                                pollInbox.mutate({
                                  supplier_name: targetSupplierName,
                                  supplier_email: targetSupplierEmail,
                                  auto_reply: autoAiReply,
                                })
                              }
                              title="Polls Gmail IMAP inbox directly for any new unread replies from the supplier."
                            >
                              🔍 Check Gmail Inbox Now
                            </button>
                          </div>
                        );
                      })()}

                      {/* Custom response composer */}
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (!customReply.trim()) return;
                          const primaryDraft = workflowView.rfqDrafts?.[0];
                          const targetSupplierName = primaryDraft?.supplier?.name || primaryDraft?.supplierName || workflowView.qualifiedOrReview?.[0]?.supplierName || 'TechNova Solutions';
                          const targetSupplierEmail = primaryDraft?.recipientEmail || primaryDraft?.recipient_email || primaryDraft?.supplier?.contact_email || primaryDraft?.supplier?.email || 'akulgameristicofficial@gmail.com';
                          pollInbox.mutate({
                            supplier_name: targetSupplierName,
                            supplier_email: targetSupplierEmail,
                            incoming_message: customReply.trim(),
                            auto_reply: autoAiReply,
                          });
                          setCustomReply('');
                        }}
                      >
                        <div className="rq-thread-input-row">
                          <textarea
                            className="rq-thread-textarea"
                            placeholder="Paste or simulate an email reply from the supplier. Gemini will read it and reply autonomously..."
                            value={customReply}
                            onChange={(e) => setCustomReply(e.target.value)}
                          />
                          <button
                            type="submit"
                            className="btn"
                            disabled={!customReply.trim() || pollInbox.isPending}
                            style={{ height: '42px', whiteSpace: 'nowrap' }}
                          >
                            {pollInbox.isPending ? 'Agent Processing…' : 'Process with Gemini ↵'}
                          </button>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px', fontSize: '12px', color: 'var(--muted)' }}>
                          <input
                            type="checkbox"
                            id="autoAi"
                            checked={autoAiReply}
                            onChange={(e) => setAutoAiReply(e.target.checked)}
                          />
                          <label htmlFor="autoAi" style={{ cursor: 'pointer' }}>
                            Have Gemini AI Autonomous Agent contact supplier directly on my behalf
                          </label>
                        </div>
                      </form>
                    </div>
                  </div>
                </div>
              )}

              {workflowView.errors.map((message, index) => <p key={index} className="rq-error">{message}</p>)}
            </div>
          )}
          {latestAgentRun.isError && latestAgentRun.error?.status !== 404 && <p className="rq-error" role="alert">{latestAgentRun.error.message}</p>}
        </section>
      )}

      <section className="card rq-section">
        <h2 className="rq-h2">Details</h2>
        <div className="rq-meta">
          <div><span className="rq-k">Budget</span><span className="rq-v">{formatMoney(r.budgetAmount, r.currencyCode)}</span></div>
          <div><span className="rq-k">Needed by</span><span className="rq-v">{formatDate(r.neededBy)}</span></div>
          <div><span className="rq-k">Category</span><span className="rq-v">{r.category || '—'}</span></div>
          <div><span className="rq-k">Delivery location</span><span className="rq-v">{r.deliveryLocation || '—'}</span></div>
          <div><span className="rq-k">Created</span><span className="rq-v">{formatDateTime(r.createdAt)}</span></div>
          <div><span className="rq-k">Last updated</span><span className="rq-v">{formatDateTime(r.updatedAt)}</span></div>
        </div>
        {r.description && <p className="rq-desc">{r.description}</p>}
      </section>

      <section className="card rq-section">
        <h2 className="rq-h2">Items</h2>
        <ul className="rq-items">
          {r.items.map((i) => (
            <li key={i.id}>
              <span className="rq-line">{i.lineNo}</span>
              <span>
                <strong>{i.name}</strong>
                {i.description && <span className="rq-note">{i.description}</span>}
              </span>
              <span className="rq-qty">{i.quantity} {i.unit}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card rq-section">
        <h2 className="rq-h2">History</h2>
        {audit.isPending && <Loading label="Loading history…" />}
        {audit.isError && <ErrorState error={audit.error} onRetry={audit.refetch} />}
        {audit.data && (
          <ol className="rq-timeline">
            {[...audit.data].reverse().map((e) => (
              <li key={e.id}>
                <span className="rq-dot" aria-hidden="true" />
                <div>
                  <div>{describe(e)}</div>
                  <div className="rq-time">
                    {e.actorUserId === user?.id ? 'You' : 'A teammate'} · {formatDateTime(e.createdAt)}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </>
  );
}
