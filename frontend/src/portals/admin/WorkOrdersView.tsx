import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Wrench, RefreshCw, UserCheck, ShieldAlert } from 'lucide-react';

export const WorkOrdersView: React.FC = () => {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [staff, setStaff] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWO, setSelectedWO] = useState<any | null>(null);
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [selectedTechId, setSelectedTechId] = useState('');
  const [reassignReason, setReassignReason] = useState('Skill match rebalance');

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

  const handleReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWO || !selectedTechId) return;

    try {
      await api.reassignWorkOrder(selectedWO.id, {
        new_technician_id: selectedTechId,
        reassignment_reason: reassignReason
      });
      setReassignModalOpen(false);
      await loadData();
      alert('Work order successfully reassigned!');
    } catch (err: any) {
      alert(`Reassignment failed: ${err.message}`);
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
      render: (r: any) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedWO(r);
            setReassignModalOpen(true);
          }}
          className="px-2.5 py-1 bg-[#345873] text-white rounded-lg text-[11px] font-bold hover:bg-[#253f54] transition cursor-pointer"
        >
          Reassign
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Work Orders & Assignments</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Manage dispatch, enforce skills matching, evaluate technician availability, and resolve blocks.
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

      {/* Reassign Modal */}
      {reassignModalOpen && selectedWO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">
              Reassign Work Order {selectedWO.work_order_code}
            </h3>
            <p className="text-xs text-gray-500 mb-4">{selectedWO.title}</p>

            <form onSubmit={handleReassignSubmit} className="space-y-4">
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
                />
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

