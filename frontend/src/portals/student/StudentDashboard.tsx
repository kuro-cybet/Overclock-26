import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { StatCard } from '../../shared/components/StatCard';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { DataTable } from '../../shared/components/DataTable';
import { QuickReportModal } from '../../features/incident-intake/QuickReportModal';
import {
  MessageSquarePlus,
  AlertTriangle,
  ClipboardList,
  Wifi,
  Building,
  CheckCircle2,
  Shield,
  HelpCircle,
  Megaphone
} from 'lucide-react';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await api.getDashboard('student');
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#A58ACF] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Loading Student Service Desk...</p>
      </div>
    );
  }

  const kpi = data?.kpi || { my_requests: 0, relevant_incidents: 0, facility_status: '95%', notifications: 0 };

  const myReportCols = [
    {
      header: 'Ticket ID',
      accessor: 'report_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.report_code}</span>
    },
    {
      header: 'Issue Reported',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block text-xs">{r.title}</span>
          <p className="text-[11px] text-gray-500 line-clamp-1">{r.description}</p>
        </div>
      )
    },
    {
      header: 'Category',
      accessor: 'category' as const,
      render: (r: any) => <span className="capitalize text-gray-600">{r.category}</span>
    },
    {
      header: 'Urgency',
      accessor: 'urgency' as const,
      render: (r: any) => <StatusBadge status={r.urgency} />
    },
    {
      header: 'Resolution Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Date Logged',
      accessor: 'created_at' as const,
      render: (r: any) => (
        <span className="text-[11px] text-gray-400 font-mono">
          {new Date(r.created_at).toLocaleDateString()}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Student Welcome & Quick Report Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#A58ACF]/25 text-[#543b7a]">
              Student Services Workspace
            </span>
            <span className="text-xs text-gray-500 font-medium">Campus Life & Support</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Hello, {user?.name}</h1>
          <p className="text-xs text-gray-500 mt-1">
            Report network disruptions, lab equipment troubles, or classroom facilities in seconds.
          </p>
        </div>

        <button
          onClick={() => setReportModalOpen(true)}
          className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-[#A58ACF] hover:bg-[#9274be] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start sm:self-auto"
        >
          <MessageSquarePlus size={16} />
          <span>Quick Issue Report</span>
        </button>
      </div>

      {/* KPI Cards (My requests, relevant campus incidents, facility status and notifications) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="My Open Tickets"
          value={kpi.my_requests}
          subtitle="Complaints tracked"
          icon={<ClipboardList size={20} />}
          accentColor="#A58ACF"
        />
        <StatCard
          title="Active Campus Outages"
          value={kpi.relevant_incidents}
          subtitle="Being fixed by dispatch"
          icon={<AlertTriangle size={20} />}
          accentColor="#F29877"
        />
        <StatCard
          title="Facility Readiness"
          value="94.2%"
          subtitle="Classrooms operational"
          icon={<Building size={20} />}
          accentColor="#10b981"
        />
        <StatCard
          title="Live Alerts"
          value={kpi.notifications}
          subtitle="Updates on your issues"
          icon={<Megaphone size={20} />}
          accentColor="#345873"
        />
      </div>

      {/* Quick Action Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          onClick={() => setReportModalOpen(true)}
          className="bg-white p-5 rounded-3xl border border-slate-200 hover:border-[#A58ACF] transition cursor-pointer shadow-xs group"
        >
          <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <Wifi size={20} />
          </div>
          <h3 className="font-extrabold text-sm text-[#345873]">Wi-Fi & Network Trouble</h3>
          <p className="text-xs text-gray-500 mt-1">
            Report dead zones, slow speeds or eduroam login problems.
          </p>
        </div>

        <div
          onClick={() => setReportModalOpen(true)}
          className="bg-white p-5 rounded-3xl border border-slate-200 hover:border-[#A58ACF] transition cursor-pointer shadow-xs group"
        >
          <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <Building size={20} />
          </div>
          <h3 className="font-extrabold text-sm text-[#345873]">Lab & Classroom Hardware</h3>
          <p className="text-xs text-gray-500 mt-1">
            Report broken monitors, projector faults or power strip issues.
          </p>
        </div>

        <div
          onClick={() => setReportModalOpen(true)}
          className="bg-white p-5 rounded-3xl border border-slate-200 hover:border-[#A58ACF] transition cursor-pointer shadow-xs group"
        >
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-105 transition">
            <CheckCircle2 size={20} />
          </div>
          <h3 className="font-extrabold text-sm text-[#345873]">Cleanliness & Sanitation</h3>
          <p className="text-xs text-gray-500 mt-1">
            Restroom supplies, spills, waste bins or hygiene requests.
          </p>
        </div>
      </div>

      {/* My Submitted Requests Table */}
      <div className="space-y-3">
        <h3 className="font-extrabold text-sm text-[#345873]">My Incident Tracking & Resolution History</h3>
        <DataTable
          columns={myReportCols}
          data={data?.my_requests || []}
          keyField="id"
          emptyMessage="You have not submitted any issue reports yet."
        />
      </div>

      <QuickReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        onSubmitted={() => loadDashboard(true)}
      />
    </div>
  );
};

