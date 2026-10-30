import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { RefreshCw } from 'lucide-react';

export const CampusView: React.FC = () => {
  const { user } = useAuth();
  // Only operations staff may change readiness; everyone else views the status.
  const canUpdateReadiness = user?.role === 'admin' || user?.role === 'technician';

  const [rooms, setRooms] = useState<any[]>([]);
  const [buildings, setBuildings] = useState<any[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [selectedBuilding]);

  const loadData = async () => {
    try {
      const [roomsData, bldData] = await Promise.all([
        api.getRooms(selectedBuilding ? `building_id=${selectedBuilding}` : ''),
        api.getBuildings()
      ]);
      setRooms(roomsData);
      setBuildings(bldData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateReadiness = async (roomId: string, newStatus: string) => {
    try {
      await api.updateRoomReadiness(roomId, newStatus);
      await loadData();
    } catch (err: any) {
      alert(`Error updating readiness: ${err.message}`);
    }
  };

  const cols = [
    {
      header: 'Room Number',
      accessor: 'room_number' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.room_number}</span>
    },
    {
      header: 'Name & Type',
      accessor: 'name' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block text-xs">{r.name}</span>
          <span className="text-[10px] text-gray-500 capitalize">{(r.type ? String(r.type) : 'Room').replace(/_/g, ' ')}</span>
        </div>
      )
    },
    {
      header: 'Capacity',
      accessor: 'capacity' as const,
      render: (r: any) => <span className="font-medium">{r.capacity} seats</span>
    },
    {
      header: 'Operational Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Daily Readiness',
      accessor: 'daily_readiness_status' as const,
      render: (r: any) => (
        <div className="flex flex-col space-y-1">
          <div className="flex items-center space-x-2">
            <StatusBadge status={r.daily_readiness_status} />
            {canUpdateReadiness && (
              <select
                value={r.daily_readiness_status}
                onChange={(e) => handleUpdateReadiness(r.id, e.target.value)}
                className="text-[10px] border border-slate-200 rounded px-1.5 py-0.5 bg-white text-gray-700 cursor-pointer"
              >
                <option value="confirmed">Confirmed</option>
                <option value="stale">Stale</option>
                <option value="unconfirmed">Unconfirmed</option>
              </select>
            )}
          </div>
          <span className="text-[10px] text-gray-400">
            Source: {r.freshness_source || 'inspection'} ({r.confirmed_by || 'Unsigned'})
          </span>
        </div>
      )
    },
    {
      header: 'Last Checked',
      accessor: 'readiness_checked_at' as const,
      render: (r: any) => (
        <span className="text-[11px] text-gray-500">
          {r.readiness_checked_at ? new Date(r.readiness_checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Campus Facilities & Room Readiness</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Monitor all 6 University Blocks, 18 Floors, 60 Classrooms & Labs with confirmed, stale, and unconfirmed indicators.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedBuilding}
            onChange={(e) => setSelectedBuilding(e.target.value)}
            className="text-xs font-bold text-[#345873] bg-white border border-slate-200 px-3 py-2 rounded-xl focus:outline-none cursor-pointer"
          >
            <option value="">All 6 Campus Buildings</option>
            {buildings.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.code})
              </option>
            ))}
          </select>

          <button
            onClick={loadData}
            className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <DataTable
        columns={cols}
        data={rooms}
        keyField="id"
      />
    </div>
  );
};

