import { formatStatus } from '../lib/format';

const TONES = { ACTIVE: 'done', BLOCKED: 'bad' }; // INACTIVE keeps the neutral grey badge

export default function SupplierStatusBadge({ status }) {
  const tone = TONES[status];
  return <span className={`rq-badge${tone ? ` rq-badge--${tone}` : ''}`}>{formatStatus(status)}</span>;
}
