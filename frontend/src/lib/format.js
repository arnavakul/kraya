export const STATUSES = [
  'DRAFT', 'SUBMITTED', 'VALIDATING', 'SOURCING', 'QUOTING', 'EVALUATION',
  'NEGOTIATION', 'APPROVAL', 'PO_DRAFT', 'COMPLETED', 'REJECTED', 'CANCELLED',
];

// Moving to these statuses needs a written reason (the backend enforces it too).
export const REASON_STATUSES = new Set(['REJECTED', 'CANCELLED']);

export function formatStatus(status) {
  if (!status) return '';
  if (status === 'PO_DRAFT') return 'PO draft';
  const text = status.replaceAll('_', ' ').toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function formatMoney(amount, currency = 'INR') {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

// "2026-12-15" (a plain date, no timezone) -> "15 Dec 2026"
export function formatDate(isoDate) {
  if (!isoDate) return '—';
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(`${isoDate}T00:00:00`));
}

export function formatDateTime(isoInstant) {
  if (!isoInstant) return '—';
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(isoInstant));
}