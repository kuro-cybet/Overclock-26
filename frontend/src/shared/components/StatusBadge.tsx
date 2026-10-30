import React from 'react';

interface StatusBadgeProps {
  status?: string | null;
  type?: 'status' | 'priority' | 'urgency' | 'readiness';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const rawStatus = typeof status === 'string' ? status : (status ? String(status) : '');
  const norm = rawStatus.toLowerCase().replace(/[\s-]/g, '_');

  let style = 'bg-gray-100 text-gray-700 border-gray-300';

  if (['critical', 'p1', 'unconfirmed', 'blocked', 'cancelled'].includes(norm)) {
    style = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['high', 'p2', 'stale', 'pending_approval', 'warning'].includes(norm)) {
    style = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['medium', 'p3', 'in_progress', 'pending_parts'].includes(norm)) {
    style = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (['low', 'p4', 'confirmed', 'completed', 'resolved', 'operational', 'available', 'approved'].includes(norm)) {
    style = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['open', 'assigned', 'submitted', 'correlated'].includes(norm)) {
    style = 'bg-purple-50 text-purple-700 border-purple-200';
  }

  const label = rawStatus ? rawStatus.replace(/_/g, ' ') : 'N/A';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border capitalize tracking-wide ${style} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-80" />
      {label}
    </span>
  );
};
