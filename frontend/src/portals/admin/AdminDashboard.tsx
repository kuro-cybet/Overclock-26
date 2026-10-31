import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { StatCard } from '../../shared/components/StatCard';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { DataTable } from '../../shared/components/DataTable';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  Wrench,
  Building,
  Boxes,
  FileCheck,
  Play,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Cpu,
  Megaphone
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [noticeTitle, setNoticeTitle] = useState('');
  const [noticeMessage, setNoticeMessage] = useState('');
  const [noticeType, setNoticeType] = useState('info');
  const [noticePosting, setNoticePosting] = useState(false);
  const [noticeFeedback, setNoticeFeedback] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.getDashboard('admin');
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePostNotice = async (event: React.FormEvent) => {
    event.preventDefault();
    setNoticePosting(true);
    setNoticeFeedback('');
    try {
      const result = await api.createBroadcastNotification({
        title: noticeTitle.trim(),
        message: noticeMessage.trim(),
        type: noticeType,
      });
      setNoticeFeedback(`Announcement posted to ${result.recipient_count} active users.`);
      setNoticeTitle('');
      setNoticeMessage('');
    } catch (err: any) {
      setNoticeFeedback(`Could not post announcement: ${err.message}`);
    } finally {
      setNoticePosting(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#345873] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Aggregating Campus Operations Data...</p>
      </div>
    );
  }

  const kpi = data?.kpi || {
    open_incidents: 0,
    sla_compliance_rate: 100,
    active_work_orders: 0,
    room_utilisation_rate: 0,
    parts_shortages: 0,
    pending_approvals: 0
  };

  // Convert categories object into recharts array
  const categoryData = Object.entries(data?.category_distribution || {}).map(([key, val]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    count: val
  }));

  const incidentsCols = [
    {
      header: 'Incident Code',
      accessor: 'incident_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.incident_code}</span>
    },
    {
      header: 'Issue & Location',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block">{r.title}</span>
          <span className="text-[10px] text-gray-400 capitalize">{r.category}</span>
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
      header: 'Correlated',
      accessor: 'correlated_count' as const,
      render: (r: any) => (
        <span className="px-2 py-0.5 bg-blue-50 text-blue-700 font-bold rounded-lg text-xs">
          {r.correlated_count} reports
        </span>
      )
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Title & Simulator CTA Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#F29877]/20 text-[#d9673d]">
              Live Campus Command
            </span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Operations Control Centre</h1>
          <p className="text-xs text-gray-500 mt-1">
            {user?.sub_role === 'system_admin'
              ? 'Unrestricted root authority across all operational modules, simulations, staff schedules, and system overrides.'
              : user?.sub_role === 'department_manager'
              ? 'Department authorization authority: incident resolution, expenditure approvals, and SLA tracking.'
              : user?.sub_role === 'facilities_admin'
              ? 'Facilities authority: campus room readiness, building assets, and field work orders.'
              : user?.sub_role === 'procurement_approver'
              ? 'Procurement authority: inventory parts stock, parts reservations, and purchase approvals.'
              : 'Unified multi-role command oversight, AI intake telemetry, and operational coordination.'}
          </p>
        </div>

        {user?.sub_role === 'system_admin' ? (
          <button
            onClick={() => navigate('/admin/simulator')}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-[#F29877] to-[#e07b55] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start md:self-auto"
          >
            <Play size={16} fill="white" />
            <span>Launch Scenario Simulator</span>
          </button>
        ) : user?.sub_role === 'department_manager' ? (
          <button
            onClick={() => navigate('/admin/approvals')}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-[#345873] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start md:self-auto"
          >
            <FileCheck size={16} />
            <span>Review Approvals Queue</span>
          </button>
        ) : user?.sub_role === 'facilities_admin' ? (
          <button
            onClick={() => navigate('/admin/campus')}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-[#287D70] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start md:self-auto"
          >
            <Building size={16} />
            <span>Campus & Readiness Center</span>
          </button>
        ) : user?.sub_role === 'procurement_approver' ? (
          <button
            onClick={() => navigate('/admin/inventory')}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-[#A58ACF] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start md:self-auto"
          >
            <Boxes size={16} />
            <span>Inventory & Parts Requisitions</span>
          </button>
        ) : (
          <button
            onClick={() => navigate('/admin/simulator')}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-[#F29877] to-[#e07b55] text-white text-xs font-bold shadow-md hover:shadow-lg transition cursor-pointer self-start md:self-auto"
          >
            <Play size={16} fill="white" />
            <span>Launch Scenario Simulator</span>
          </button>
        )}
      </div>

      {/* KPI Cards (Page 4 Blueprint: Open incidents, SLA compliance, active work orders, room utilisation, parts shortages) */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          title="Open Incidents"
          value={kpi.open_incidents}
          subtitle="Triage & active resolution"
          icon={<AlertTriangle size={20} />}
          accentColor="#F29877"
          isAlert={kpi.open_incidents > 30}
        />
        <StatCard
          title="SLA Compliance"
          value={`${kpi.sla_compliance_rate}%`}
          subtitle="University SLA targets"
          icon={<Clock size={20} />}
          accentColor="#287D70"
          trend="+1.4% vs last month"
        />
        <StatCard
          title="Active Work Orders"
          value={kpi.active_work_orders}
          subtitle="Assigned & in-progress"
          icon={<Wrench size={20} />}
          accentColor="#345873"
        />
        <StatCard
          title="Room Utilisation"
          value={`${kpi.room_utilisation_rate}%`}
          subtitle="Academic schedule load"
          icon={<Building size={20} />}
          accentColor="#8EB9D8"
        />
        <StatCard
          title="Parts Shortages"
          value={kpi.parts_shortages}
          subtitle="At or below threshold"
          icon={<Boxes size={20} />}
          accentColor="#dc2626"
          isAlert={kpi.parts_shortages > 0}
        />
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="mb-4 flex items-center gap-2">
          <Megaphone size={18} className="text-[#F29877]" />
          <div>
            <h2 className="text-sm font-extrabold text-[#345873]">Post campus announcement</h2>
            <p className="text-[11px] text-gray-500">
              This in-app notification will be visible to all active users.
            </p>
          </div>
        </div>
        <form onSubmit={handlePostNotice} className="grid gap-3 md:grid-cols-[1fr_180px]">
          <input
            required
            maxLength={255}
            value={noticeTitle}
            onChange={(event) => setNoticeTitle(event.target.value)}
            placeholder="Announcement title"
            className="rounded-xl border border-slate-200 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#345873]"
          />
          <select
            value={noticeType}
            onChange={(event) => setNoticeType(event.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs"
          >
            <option value="info">Information</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
            <option value="action_required">Action required</option>
          </select>
          <textarea
            required
            maxLength={5000}
            rows={3}
            value={noticeMessage}
            onChange={(event) => setNoticeMessage(event.target.value)}
            placeholder="Write the announcement for the campus..."
            className="rounded-xl border border-slate-200 px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#345873] md:col-span-2"
          />
          <div className="flex items-center justify-between gap-3 md:col-span-2">
            <p role="status" className="text-xs font-semibold text-[#287D70]">{noticeFeedback}</p>
            <button
              type="submit"
              disabled={noticePosting || !noticeTitle.trim() || !noticeMessage.trim()}
              className="shrink-0 rounded-xl bg-[#345873] px-4 py-2.5 text-xs font-bold text-white transition hover:bg-[#253f54] disabled:opacity-50"
            >
              {noticePosting ? 'Posting...' : 'Post to all users'}
            </button>
          </div>
        </form>
      </section>

      {/* Visual Analytics Row: Category Distribution & SLA Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-[#345873] text-sm">Incident Distribution by Category</h3>
              <p className="text-[11px] text-gray-400">Total tickets logged in active term</p>
            </div>
            <Cpu size={18} className="text-[#F29877]" />
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <XAxis dataKey="name" fontSize={11} stroke="#94a3b8" />
                <YAxis fontSize={11} stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#345873',
                    color: '#FFF4E9',
                    borderRadius: '12px',
                    fontSize: '12px'
                  }}
                />
                <Bar dataKey="count" fill="#F29877" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-[#345873] text-sm">SLA Compliance Trajectory</h3>
              <p className="text-[11px] text-gray-400">Monthly resolution rate percentage</p>
            </div>
            <TrendingUp size={18} className="text-[#287D70]" />
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.sla_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" fontSize={11} stroke="#94a3b8" />
                <YAxis domain={[80, 100]} fontSize={11} stroke="#94a3b8" unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#345873',
                    color: '#FFF4E9',
                    borderRadius: '12px',
                    fontSize: '12px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="sla_rate"
                  stroke="#287D70"
                  strokeWidth={3}
                  dot={{ fill: '#287D70', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Critical & Recent Incidents Overview Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-[#345873]">Critical & Recent Incidents</h3>
            <p className="text-xs text-gray-500">Live operational events tracked across all buildings</p>
          </div>
          <button
            onClick={() => navigate('/admin/incidents')}
            className="text-xs font-bold text-[#345873] flex items-center hover:underline cursor-pointer"
          >
            <span>View All Incidents</span>
            <ArrowRight size={14} className="ml-1" />
          </button>
        </div>

        <DataTable
          columns={incidentsCols}
          data={data?.recent_incidents || []}
          keyField="id"
          onRowClick={(row: any) => navigate(`/admin/incidents`)}
        />
      </div>

      {/* Pending Approvals Summary */}
      {data?.pending_approvals && data.pending_approvals.length > 0 && (
        <div className="bg-amber-50/60 border border-amber-200 rounded-3xl p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <FileCheck size={18} className="text-amber-700" />
              <h4 className="font-bold text-amber-900 text-sm">
                Pending Approvals Requiring Authorization ({data.pending_approvals.length})
              </h4>
            </div>
            <button
              onClick={() => navigate('/admin/approvals')}
              className="text-xs font-bold text-amber-800 hover:underline cursor-pointer"
            >
              Go to Approval Desk
            </button>
          </div>
          <div className="space-y-2">
            {data.pending_approvals.map((app: any) => (
              <div
                key={app.id}
                className="bg-white p-3.5 rounded-2xl border border-amber-100 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-gray-800 capitalize">
                    {(app.approval_type ? String(app.approval_type) : 'Approval').replace(/_/g, ' ')}
                  </span>
                  <p className="text-gray-500 text-[11px] mt-0.5">{app.justification}</p>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-[#345873] text-sm block">
                    ${Number(app.cost_amount || 0).toFixed(2)}
                  </span>
                  <span className="text-[10px] text-amber-700 font-bold uppercase">Pending Decision</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
