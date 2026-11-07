const STAGE_LABELS = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  VALIDATING: 'Validating',
  SOURCING: 'Sourcing',
  QUOTING: 'Quoting',
  EVALUATION: 'Evaluation',
  NEGOTIATION: 'Negotiation',
  APPROVAL: 'Approval',
  PO_DRAFT: 'PO draft',
  COMPLETED: 'Completed',
  REJECTED: 'Rejected',
  CANCELLED: 'Cancelled',
};

export function stageLabel(status) {
  if (!status) return '—';
  const key = String(status).toUpperCase();
  return STAGE_LABELS[key] || key.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function timeAgo(isoDate) {
  if (!isoDate) return 'just now';

  const diffMs = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.round(diffMs / 60000);
  if (Math.abs(minutes) < 1) return 'just now';
  if (Math.abs(minutes) < 60) return `${Math.round(minutes)} min ago`;

  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return `${hours} hr ago`;

  const days = Math.round(hours / 24);
  if (Math.abs(days) < 30) return `${days} day${days === 1 ? '' : 's'} ago`;

  const months = Math.round(days / 30);
  if (Math.abs(months) < 12) return `${months} month${months === 1 ? '' : 's'} ago`;

  const years = Math.round(months / 12);
  return `${years} year${years === 1 ? '' : 's'} ago`;
}

export function trendText(current, previous) {
  if (previous === 0) {
    if (current === 0) return { text: 'No change', tone: 'neutral' };
    return { text: `${current} in this period`, tone: 'up' };
  }

  const delta = current - previous;
  const pct = (delta / previous) * 100;
  const direction = delta >= 0 ? 'up' : 'down';
  const label = `${Math.abs(Math.round(pct))}%`;

  return {
    text: `${delta >= 0 ? 'Up' : 'Down'} ${label} vs prior period`,
    tone: direction,
  };
}

function entityLabel(entityType) {
  const type = (entityType || '').toUpperCase();
  if (type.includes('SUPPLIER')) return 'Supplier';
  if (type.includes('REQUEST')) return 'Request';
  if (type.includes('APPROVAL')) return 'Approval';
  return 'Item';
}

export function describeActivity(item) {
  if (!item) {
    return { icon: 'info', title: 'Recent activity', sub: '' };
  }

  const action = (item.action || '').toUpperCase();
  const entity = entityLabel(item.entityType);
  const title = item.entityLabel || entity;

  if (action.includes('CREATED')) {
    return {
      icon: 'plus',
      title: `${entity} created`,
      sub: title,
    };
  }

  if (action.includes('APPROVED')) {
    return {
      icon: 'check',
      title: `${entity} approved`,
      sub: title,
    };
  }

  if (action.includes('REJECTED') || action.includes('CANCELLED')) {
    return {
      icon: 'alert',
      title: `${entity} updated`,
      sub: title,
    };
  }

  if (action.includes('STATUS') || action.includes('UPDATED') || action.includes('CHANGED')) {
    const from = item.previousState ? stageLabel(item.previousState) : null;
    const to = item.newState ? stageLabel(item.newState) : null;
    return {
      icon: 'sync',
      title: `${entity} updated`,
      sub: from && to ? `${from} → ${to}` : title,
    };
  }

  return {
    icon: 'info',
    title: `${entity} update`,
    sub: title,
  };
}
