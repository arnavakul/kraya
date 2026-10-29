import { formatStatus } from '../lib/format';

// The happy path. REJECTED and CANCELLED sit outside it and are shown as a banner instead.
const FLOW = [
  'DRAFT', 'SUBMITTED', 'VALIDATING', 'SOURCING', 'QUOTING',
  'EVALUATION', 'NEGOTIATION', 'APPROVAL', 'PO_DRAFT', 'COMPLETED',
];

export default function RequestStepper({ status }) {
  const current = FLOW.indexOf(status); // -1 when rejected or cancelled

  return (
    <ol className={`rq-steps${current < 0 ? ' rq-steps--stopped' : ''}`} aria-label="Request progress">
      {FLOW.map((step, i) => (
        <li key={step}
            className={current >= 0 && i < current ? 'done' : undefined}
            aria-current={i === current ? 'step' : undefined}>
          {current >= 0 && i < current && '✓ '}{formatStatus(step)}
        </li>
      ))}
    </ol>
  );
}
