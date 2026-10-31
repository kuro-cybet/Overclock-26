import { formatINR } from '../../shared/utils/currency';
import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { FileCheck, ShieldAlert, Check, X, RefreshCw } from 'lucide-react';

export const ApprovalsView: React.FC = () => {
  const { user } = useAuth();
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [decisionModal, setDecisionModal] = useState<{ id: string; action: 'approved' | 'rejected' } | null>(null);
  const [reason, setReason] = useState('Authorized under operational department protocol');

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.getApprovals();
      setApprovals(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!decisionModal) return;

    try {
      await api.decideApproval(decisionModal.id, {
        decision: decisionModal.action,
        decision_reason: reason
      });
      setDecisionModal(null);
      await loadApprovals();
      alert(`Approval decision (${decisionModal.action}) recorded successfully!`);
    } catch (err: any) {
      alert(`Decision rejected: ${err.message}`);
    }
  };

  const cols = [
    {
      header: 'Approval Type',
      accessor: 'approval_type' as const,
      render: (r: any) => (
        <span className="font-bold text-[#345873] capitalize text-xs">
          {(r.approval_type ? String(r.approval_type) : 'General').replace(/_/g, ' ')}
        </span>
      )
    },
    {
      header: 'Cost / Commitment',
      accessor: 'cost_amount' as const,
      render: (r: any) => (
        <span className="font-mono font-bold text-gray-800">
          {formatINR(r.cost_amount)}
        </span>
      )
    },
    {
      header: 'Justification',
      accessor: 'justification' as const,
      render: (r: any) => <span className="text-gray-600 text-xs">{r.justification}</span>
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Submitted',
      accessor: 'created_at' as const,
      render: (r: any) => (
        <span className="text-[11px] text-gray-500">
          {new Date(r.created_at).toLocaleDateString()}
        </span>
      )
    },
    {
      header: 'Decision Action',
      render: (r: any) => {
        if (r.status !== 'pending') {
          return (
            <span className="text-[10px] text-gray-400 font-semibold italic">
              Decided by {r.decision_reason || 'Approver'}
            </span>
          );
        }
        return (
          <div className="flex space-x-1.5">
            <button
              onClick={() => setDecisionModal({ id: r.id, action: 'approved' })}
              className="px-2.5 py-1 bg-emerald-600 text-white rounded-lg text-[11px] font-bold hover:bg-emerald-700 transition cursor-pointer flex items-center space-x-1"
            >
              <Check size={12} />
              <span>Approve</span>
            </button>
            <button
              onClick={() => setDecisionModal({ id: r.id, action: 'rejected' })}
              className="px-2.5 py-1 bg-rose-600 text-white rounded-lg text-[11px] font-bold hover:bg-rose-700 transition cursor-pointer flex items-center space-x-1"
            >
              <X size={12} />
              <span>Reject</span>
            </button>
          </div>
        );
      }
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Governance & Pending Approvals</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Enforces strict Separation of Duties. Requester cannot approve their own requests; System Admins cannot override Business rules.
          </p>
        </div>

        <button
          onClick={loadApprovals}
          className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="bg-white p-4 rounded-2xl border border-slate-200 text-xs flex items-center space-x-3 text-slate-700">
        <ShieldAlert size={18} className="text-[#F29877] shrink-0" />
        <p>
          Logged in as <span className="font-bold">{user?.name}</span> ({user?.role}{' '}
          {user?.sub_role ? `• ${String(user.sub_role).replace(/_/g, ' ')}` : ''}). If you attempt to approve your own submission, the backend will strictly enforce the separation of duties policy and return HTTP 403 Forbidden.
        </p>
      </div>

      <DataTable
        columns={cols}
        data={approvals}
        keyField="id"
      />

      {/* Decision Modal */}
      {decisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-extrabold text-[#345873] mb-1 capitalize">
              Confirm {decisionModal.action}
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Enter policy reason for auditing and audit trail persistence:
            </p>

            <form onSubmit={handleDecisionSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Audit Reason</label>
                <textarea
                  required
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setDecisionModal(null)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`px-4 py-2 text-white rounded-xl text-xs font-bold cursor-pointer ${
                    decisionModal.action === 'approved' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  Confirm Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


