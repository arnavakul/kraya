export function createGmailComposeUrl({ to, subject, body }) {
  const base = 'https://mail.google.com/mail/?view=cm&fs=1';
  const params = new URLSearchParams();
  if (to) params.set('to', to);
  if (subject) params.set('su', subject);
  if (body) params.set('body', body);
  return `${base}&${params.toString()}`;
}

export function createMailtoUrl({ to, subject, body }) {
  const params = new URLSearchParams();
  if (subject) params.set('subject', subject);
  if (body) params.set('body', body);
  const query = params.toString();
  return `mailto:${to || ''}${query ? `?${query}` : ''}`;
}

export function agentWorkflowView(run) {
  if (!run) return null;

  const supplierNames = new Map(
    (run.supplier_discovery_result?.suppliers ?? []).map((assessment) => [
      assessment.supplier?.supplier_id,
      assessment.supplier?.name,
    ]),
  );

  const decisions = (run.supplier_eligibility_results ?? []).map((decision) => ({
    ...decision,
    supplierName: supplierNames.get(decision.supplier_id) ?? decision.supplier_id,
  }));

  const qualifiedOrReview = decisions.filter(
    (d) => d.eligible || d.decision === 'manual_review' || d.decision === 'eligible'
  );
  const excluded = decisions.filter(
    (d) => !d.eligible && d.decision !== 'manual_review' && d.decision !== 'eligible'
  );

  const dispatches = run.dispatches ?? [];
  const isWorkflowDispatched = run.workflow_status === 'DISPATCHED' || run.runStatus === 'DISPATCHED' || run.status === 'DISPATCHED';

  const rfqDrafts = (run.rfq_drafts ?? []).map((draft) => {
    const recipientEmail = draft.recipient_email || draft.supplier?.contact_email || draft.supplier?.email || '';
    const subject = draft.email_subject || 'Request for Quotation';
    const body = draft.email_body || '';
    const dispatchReceipt = dispatches.find((d) => d.rfq_id === draft.rfq_id || d.supplier_name === draft.supplier?.name) || draft.dispatch_receipt;
    const isDispatched = draft.status === 'DISPATCHED' || draft.status === 'approved' || isWorkflowDispatched || Boolean(dispatchReceipt);

    return {
      ...draft,
      recipientEmail,
      isDispatched,
      dispatchReceipt,
      gmailUrl: createGmailComposeUrl({ to: recipientEmail, subject, body }),
      mailtoUrl: createMailtoUrl({ to: recipientEmail, subject, body }),
    };
  });

  return {
    status: isWorkflowDispatched ? 'DISPATCHED' : (run.workflow_status ?? run.runStatus ?? 'UNKNOWN'),
    runStatus: run.runStatus ?? null,
    completedAt: run.completedAt ?? null,
    errorMessage: run.errorMessage ?? null,
    clarificationQuestions: run.clarification_questions ?? [],
    decisions,
    qualifiedOrReview,
    excluded,
    rfqDrafts,
    dispatches,
    emailThread: run.email_thread ?? [],
    pendingAiDraft: run.pending_ai_draft ?? null,
    errors: [...(run.errors ?? []), ...(run.intake_errors ?? [])],
  };
}
