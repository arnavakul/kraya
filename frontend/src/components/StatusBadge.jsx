import { formatStatus } from '../lib/format';

function tone(status) {
  if (status === 'DRAFT') return '';
  if (status === 'COMPLETED') return 'done';
  if (status === 'REJECTED' || status === 'CANCELLED') return 'bad';
  return 'active';
}

export default function StatusBadge({ status }) {
  const t = tone(status);
  return <span className={`rq-badge${t ? ` rq-badge--${t}` : ''}`}>{formatStatus(status)}</span>;
}
