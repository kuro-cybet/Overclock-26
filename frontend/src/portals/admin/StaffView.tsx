import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Users, RefreshCw } from 'lucide-react';

export const StaffView: React.FC = () => {
  const [staff, setStaff] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStaff();
  }, []);

  const loadStaff = async () => {
    setLoading(true);
    try {
      const data = await api.getStaff();
      setStaff(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'absent' ? 'available' : 'absent';
    try {
      await api.updateStaffStatus(userId, nextStatus);
      await loadStaff();
    } catch (err: any) {
      alert(`Error updating status: ${err.message}`);
    }
  };

  const cols = [
    {
      header: 'Technician Name',
      accessor: 'name' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block text-xs">{r.name}</span>
          <span className="text-[10px] text-gray-400">{r.email}</span>
        </div>
      )
    },
    {
      header: 'Sub-Role',
      accessor: 'sub_role' as const,
      render: (r: any) => (
        <span className="font-semibold text-gray-700 capitalize text-xs">
          {r.sub_role ? r.sub_role.replace(/_/g, ' ') : 'Technician'}
        </span>
      )
    },
    {
      header: 'Shift',
      accessor: 'shift' as const,
      render: (r: any) => <span className="capitalize text-xs text-gray-600">{r.shift}</span>
    },
    {
      header: 'Skills Matrix',
      accessor: 'skills' as const,
      render: (r: any) => (
        <div className="flex flex-wrap gap-1">
          {r.skills.map((s: string, i: number) => (
            <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-medium capitalize">
              {s}
            </span>
          ))}
        </div>
      )
    },
    {
      header: 'Current Workload',
      accessor: 'current_workload' as const,
      render: (r: any) => (
        <span className="font-mono font-bold text-xs">
          {r.current_workload} active tasks
        </span>
      )
    },
    {
      header: 'Availability',
      accessor: 'availability_status' as const,
      render: (r: any) => (
        <div className="flex items-center space-x-2">
          <StatusBadge status={r.availability_status} />
          <button
            onClick={() => handleToggleStatus(r.user_id, r.availability_status)}
            className="text-[10px] px-2 py-0.5 rounded border border-slate-200 bg-white hover:bg-gray-50 text-gray-700 font-semibold cursor-pointer"
          >
            Mark {r.availability_status === 'absent' ? 'Available' : 'Absent'}
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Technicians & Skills Matrix</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            24 support staff across Morning, Evening, and Night shifts with skill tags, workload balancing, and presence tracking.
          </p>
        </div>

        <button
          onClick={loadStaff}
          className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <DataTable
        columns={cols}
        data={staff}
        keyField="user_id"
      />
    </div>
  );
};

