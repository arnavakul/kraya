import assert from 'node:assert/strict';
import test from 'node:test';
import { agentWorkflowView, createGmailComposeUrl, createMailtoUrl } from '../src/lib/agentWorkflow.js';

test('renders a structured agent result with supplier names and actual status', () => {
  const view = agentWorkflowView({
    runId: 'run-1',
    workflow_status: 'supplier_review_required',
    supplier_discovery_result: {
      suppliers: [{ supplier: { supplier_id: 'supplier-1', name: 'Synthetic Business Laptop Co.' } }],
    },
    supplier_eligibility_results: [{
      supplier_id: 'supplier-1', decision: 'manual_review', reason: 'Capacity needs verification.',
    }],
    clarification_questions: ['Confirm delivery lead time.'],
    rfq_drafts: [],
    errors: [],
  });

  assert.equal(view.status, 'supplier_review_required');
  assert.equal(view.decisions[0].supplierName, 'Synthetic Business Laptop Co.');
  assert.equal(view.decisions[0].decision, 'manual_review');
  assert.equal(view.clarificationQuestions[0], 'Confirm delivery lead time.');
  assert.deepEqual(view.rfqDrafts, []);
});

test('restores persisted run status and displays execution errors', () => {
  const view = agentWorkflowView({
    runId: 'run-2', runStatus: 'FAILED', completedAt: '2026-11-16T10:00:00Z',
    errorMessage: 'The agent service timed out.',
  });
  assert.equal(view.status, 'FAILED');
  assert.equal(view.runStatus, 'FAILED');
  assert.equal(view.errorMessage, 'The agent service timed out.');
  assert.deepEqual(view.errors, []);
});

test('generates pre-filled Gmail compose and mailto URLs and maps RFQ dispatch status', () => {
  const gmailUrl = createGmailComposeUrl({
    to: 'supplier@example.com',
    subject: 'Request for Quotation: Laptops',
    body: 'Please provide quotation.',
  });
  assert.ok(gmailUrl.startsWith('https://mail.google.com/mail/?view=cm&fs=1'));
  assert.ok(gmailUrl.includes('to=supplier%40example.com'));
  assert.ok(gmailUrl.includes('su=Request+for+Quotation%3A+Laptops'));
  assert.ok(gmailUrl.includes('body=Please+provide+quotation.'));

  const mailtoUrl = createMailtoUrl({
    to: 'supplier@example.com',
    subject: 'RFQ',
    body: 'Details here',
  });
  assert.ok(mailtoUrl.startsWith('mailto:supplier@example.com?'));
  assert.ok(mailtoUrl.includes('subject=RFQ'));

  const view = agentWorkflowView({
    runId: 'run-3',
    workflow_status: 'pending_approval',
    rfq_drafts: [{
      rfq_id: 'rfq-1',
      recipient_email: 'akul@technova.com',
      email_subject: 'RFQ: Networking',
      email_body: 'Body text',
      status: 'pending_approval',
      supplier: { name: 'TechNova Solutions', contact_email: 'akul@technova.com' },
    }],
    dispatches: [],
  });

  assert.equal(view.rfqDrafts.length, 1);
  assert.equal(view.rfqDrafts[0].isDispatched, false);
  assert.ok(view.rfqDrafts[0].gmailUrl.includes('akul%40technova.com'));

  const dispatchedView = agentWorkflowView({
    runId: 'run-4',
    workflow_status: 'DISPATCHED',
    rfq_drafts: [{
      rfq_id: 'rfq-1',
      recipient_email: 'akul@technova.com',
      email_subject: 'RFQ: Networking',
      email_body: 'Body text',
      status: 'DISPATCHED',
    }],
    dispatches: [{ rfq_id: 'rfq-1', tracking_id: 'TRK-TEST1234' }],
  });
  assert.equal(dispatchedView.status, 'DISPATCHED');
  assert.equal(dispatchedView.rfqDrafts[0].isDispatched, true);
  assert.equal(dispatchedView.rfqDrafts[0].dispatchReceipt.tracking_id, 'TRK-TEST1234');
});
