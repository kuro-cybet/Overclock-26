import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Wrench, RefreshCw, UserCheck, ShieldAlert, AlertTriangle, Send, CheckCircle2 } from 'lucide-react';

export const WorkOrdersView: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role?.toLowerCase() === 'admin' || user?.role?.toLowerCase() === 'system_admin';
  const isTechnician = !isAdmin ||
    user?.role?.toLowerCase() === 'technician' ||
    user?.role?.toLowerCase()?.includes('technician') ||
    user?.sub_role?.toLowerCase()?.includes('technician') ||
    user?.sub_role?.toLowerCase()?.includes('incharge') ||
    user?.sub_role?.toLowerCase()?.includes('janitor');

  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [staff, setStaff] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWO, setSelectedWO] = useState<any | null>(null);

  // Admin Direct Reassignment Modal state
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [selectedTechId, setSelectedTechId] = useState('');
  const [reassignReason, setReassignReason] = useState('Skill match rebalance');

  // Technician "Request Reassignment" Modal state
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [requestReasonPreset, setRequestReasonPreset] = useState('Skill mismatch — requires specialized certification / license');
  const [requestNotes, setRequestNotes] = useState('');
  const [requestUrgency, setRequestUrgency] = useState('normal');
  const [submittingRequest, setSubmittingRequest] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [woData, staffData] = await Promise.all([
        api.getWorkOrders(),
        api.getStaff()
      ]);
      setWorkOrders(woData);
      setStaff(staffData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Admin Direct Reassignment handler
  const handleAdminReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWO || !selectedTechId) return;

    try {
      await api.reassignWorkOrder(selectedWO.id, {
        new_technician_id: selectedTechId,
        reassignment_reason: reassignReason
      });
      setReassignModalOpen(false);
      await loadData();
      alert('Work order successfully reassigned by administrator.');
    } catch (err: any) {
      alert(`Reassignment failed: ${err.message}`);
    }
  };

  // Technician Request Reassignment handler
  const handleTechnicianRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWO) return;

    setSubmittingRequest(true);
    try {
      await api.requestWorkOrderReassignment(selectedWO.id, {
        reason: requestReasonPreset,
        urgency: requestUrgency,
        notes: requestNotes
      });
      setRequestModalOpen(false);
      setRequestNotes('');
      await loadData();
      alert(`Reassignment request submitted to dispatch supervisor for ${selectedWO.work_order_code}.`);
    } catch (err: any) {
      alert(`Failed to submit request: ${err.message}`);
    } finally {
      setSubmittingRequest(false);
    }
  };

  const cols = [
    {
      header: 'WO Code',
      accessor: 'work_order_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.work_order_code}</span>
    },
    {
      header: 'Title & Actions',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block text-xs">{r.title}</span>
          {r.blocked_reason && (
            <span className="text-[10px] text-rose-600 font-semibold block mt-0.5">
              Blocked: {r.blocked_reason}
            </span>
          )}
          {r.evidence_notes && r.evidence_notes.includes('Reassignment Requested') && (
            <span className="text-[10px] text-amber-700 font-bold block mt-0.5">
              ⚠️ Reassignment Request Pending Review
            </span>
          )}
        </div>
      )
    },
    {
      header: 'Priority',
      accessor: 'priority' as const,
      render: (r: any) => <StatusBadge status={r.priority} />
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Assigned Tech',
      accessor: 'assigned_technician_id' as const,
      render: (r: any) => {
        const assigned = staff.find(s => s.user_id === r.assigned_technician_id);
        return (
          <span className="text-xs font-semibold text-gray-700">
            {assigned ? assigned.name : 'Unassigned'}
          </span>
        );
      }
    },
    {
      header: 'Action',
      render: (r: any) => {
        if (r.status === 'completed') {
          return (
            <span className="text-[11px] text-emerald-600 font-bold px-2 py-1 bg-emerald-50 rounded-lg">
              Completed
            </span>
          );
        }

        const hasPendingRequest = r.evidence_notes && r.evidence_notes.includes('Reassignment Requested');

        // Technician cannot reassign; only request reassignment
        if (isTechnician) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedWO(r);
                setRequestModalOpen(true);
              }}
              className={`px-3 py-1.5 rounded-xl text-[11px] font-bold transition cursor-pointer shadow-xs ${
                hasPendingRequest
                  ? 'bg-amber-100 text-amber-900 hover:bg-amber-200 border border-amber-300'
                  : 'bg-amber-600 hover:bg-amber-700 text-white'
              }`}
            >
              {hasPendingRequest ? 'Update Request' : 'Request Reassignment'}
            </button>
          );
        }

        // Admin has direct reassignment authority
        return (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setSelectedWO(r);
              setReassignModalOpen(true);
            }}
            className="px-3 py-1.5 bg-[#345873] text-white rounded-xl text-[11px] font-bold hover:bg-[#253f54] transition cursor-pointer"
          >
            Reassign
          </button>
        );
      }
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Work Orders & Assignments</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {isTechnician
              ? 'Review your assigned tasks, monitor status, and request reassignment from your supervisor if blocked.'
              : 'Manage dispatch, enforce skills matching, evaluate technician availability, and resolve blocks.'}
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <DataTable
        columns={cols}
        data={workOrders}
        keyField="id"
      />

      {/* Technician "Request Reassignment" Modal */}
      {requestModalOpen && selectedWO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-[#345873]">
                  Request Work Order Reassignment
                </h3>
                <p className="text-xs text-gray-500 font-mono">
                  {selectedWO.work_order_code} — {selectedWO.title}
                </p>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-3 my-3 text-xs text-amber-800 leading-relaxed">
              <strong>Notice:</strong> As a technician, you cannot directly transfer or reassign tasks.
              Submitting this form notifies your Facilities Supervisor / Dispatch Desk to review your justification and assign an eligible colleague.
            </div>

            <form onSubmit={handleTechnicianRequestSubmit} className="space-y-3.5 mt-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Reason for Reassignment Request
                </label>
                <select
                  required
                  value={requestReasonPreset}
                  onChange={(e) => setRequestReasonPreset(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                >
                  <option value="Skill mismatch — requires specialized certification / license">
                    Skill mismatch — requires specialized certification / license
                  </option>
                  <option value="Workload excessive — concurrent high-priority task in progress">
                    Workload excessive — concurrent high-priority task in progress
                  </option>
                  <option value="Shift ending — insufficient time remaining to conclude safely">
                    Shift ending — insufficient time remaining to conclude safely
                  </option>
                  <option value="Missing diagnostic equipment or specialized replacement parts">
                    Missing diagnostic equipment or specialized replacement parts
                  </option>
                  <option value="Physical site hazard or restricted facility access">
                    Physical site hazard or restricted facility access
                  </option>
                  <option value="Health / personal availability constraint">
                    Health / personal availability constraint
                  </option>
                  <option value="Other operational constraint">
                    Other operational constraint
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Urgency Level
                </label>
                <select
                  value={requestUrgency}
                  onChange={(e) => setRequestUrgency(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                >
                  <option value="normal">Normal — Routine shift handover</option>
                  <option value="high">High — Active disruption requiring prompt attention</option>
                  <option value="critical">Critical — Classroom or lab blocked</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Handover Notes / Specific Justification
                </label>
                <textarea
                  rows={3}
                  value={requestNotes}
                  onChange={(e) => setRequestNotes(e.target.value)}
                  placeholder="Detail any troubleshooting already performed, specific parts required, or safety notes for the next technician..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-none"
                />
              </div>

              <div className="pt-3 flex justify-end space-x-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setRequestModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingRequest}
                  className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold cursor-pointer transition shadow-xs flex items-center space-x-1.5"
                >
                  <Send size={13} />
                  <span>{submittingRequest ? 'Submitting...' : 'Submit Request to Supervisor'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Admin Direct Reassign Modal (Only accessible by Administrators) */}
      {reassignModalOpen && selectedWO && !isTechnician && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">
              Directly Reassign Work Order {selectedWO.work_order_code}
            </h3>
            <p className="text-xs text-gray-500 mb-4">{selectedWO.title}</p>

            <form onSubmit={handleAdminReassignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Select Replacement Technician
                </label>
                <select
                  required
                  value={selectedTechId}
                  onChange={(e) => setSelectedTechId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                >
                  <option value="">Choose an available technician...</option>
                  {staff
                    .filter((s) => s.availability_status !== 'absent')
                    .map((s) => (
                      <option key={s.user_id} value={s.user_id}>
                        {s.name} ({s.shift} shift) - Load: {s.current_workload} tasks - Skills: {s.skills.join(', ')}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Policy Justification / Reason
                </label>
                <input
                  type="text"
                  required
                  value={reassignReason}
                  onChange={(e) => setReassignReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                >
                </input>
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setReassignModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#253f54] cursor-pointer"
                >
                  Confirm Reassignment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
