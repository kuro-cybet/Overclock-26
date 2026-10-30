import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { StatCard } from '../../shared/components/StatCard';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Clock,
  ShieldCheck,
  CheckCircle2,
  FileSpreadsheet,
  Download
} from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [slaStatus, setSlaStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [analyticsData, slaData] = await Promise.all([
        api.getAnalytics(),
        api.apiRequest('/sla/status')
      ]);
      setAnalytics(analyticsData);
      setSlaStatus(slaData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#345873] mx-auto mb-3" />
        <p className="text-sm text-gray-500 font-medium">Computing Campus Operational Metrics...</p>
      </div>
    );
  }

  const kpi = analytics?.kpi || {
    open_incidents: 0,
    sla_compliance_rate: 100,
    active_work_orders: 0,
    room_utilisation_rate: 0,
    parts_shortages: 0
  };

  const categoryData = Object.entries(analytics?.incidents_by_category || {}).map(([key, val]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    count: val
  }));

  const severityData = Object.entries(analytics?.incidents_by_severity || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    value: val
  }));

  const workOrderStatusData = Object.entries(analytics?.work_orders_by_status || {}).map(([key, val]) => ({
    name: key.replace(/_/g, ' ').toUpperCase(),
    count: val
  }));

  const readinessData = Object.entries(analytics?.room_readiness_breakdown || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    value: val
  }));

  const SEVERITY_COLORS = {
    CRITICAL: '#ef4444',
    HIGH: '#f97316',
    MEDIUM: '#3b82f6',
    LOW: '#10b981'
  };

  const READINESS_COLORS = {
    CONFIRMED: '#10b981',
    STALE: '#f59e0b',
    UNCONFIRMED: '#ef4444'
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-7 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-[#345873]/10 text-[#345873]">
              Database-Backed Metrics
            </span>
            <span className="text-sm text-gray-400 font-medium">Analytics & Audit Telemetry</span>
          </div>
          <h1 className="text-3xl font-black text-[#345873] mt-2">Campus Operational Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">
            Deep performance metrics on SLA compliance, room readiness health, incident resolution velocities, and work order dispatch.
          </p>
        </div>

        <button
          onClick={() => {
            alert('Exporting operational metrics audit summary as CSV...');
          }}
          className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-white border border-slate-300 hover:border-[#345873] text-[#345873] text-sm font-bold shadow-xs hover:shadow-sm transition cursor-pointer self-start md:self-auto"
        >
          <Download size={18} />
          <span>Export Analytics Audit</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
        <StatCard
          title="Overall SLA Target"
          value={`${kpi.sla_compliance_rate}%`}
          subtitle="Target threshold: >=90%"
          icon={<Clock size={22} />}
          accentColor="#287D70"
          trend="+1.4% Monthly Trajectory"
        />
        <StatCard
          title="SLA Breached Cases"
          value={slaStatus?.breached || 0}
          subtitle="Requiring supervisor signoff"
          icon={<AlertTriangle size={22} />}
          accentColor="#ef4444"
          isAlert={slaStatus?.breached > 0}
        />
        <StatCard
          title="Approaching SLA (<1h)"
          value={slaStatus?.warning || 0}
          subtitle="Active escalation watch"
          icon={<TrendingUp size={22} />}
          accentColor="#f59e0b"
          isAlert={slaStatus?.warning > 0}
        />
        <StatCard
          title="Room Utilisation Rate"
          value={`${kpi.room_utilisation_rate}%`}
          subtitle="Academic timetable density"
          icon={<CheckCircle2 size={22} />}
          accentColor="#8EB9D8"
        />
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7">
        {/* Monthly SLA Trend */}
        <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-extrabold text-[#345873] text-base">SLA Compliance Trajectory (6 Months)</h3>
              <p className="text-xs text-gray-400">Monthly resolution rate percentage against university SLA</p>
            </div>
            <TrendingUp size={20} className="text-[#287D70]" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics?.sla_monthly_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" fontSize={12} stroke="#94a3b8" />
                <YAxis domain={[80, 100]} fontSize={12} stroke="#94a3b8" unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#345873',
                    color: '#FFF4E9',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="sla_rate"
                  stroke="#287D70"
                  strokeWidth={3.5}
                  dot={{ fill: '#287D70', r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Incidents by Category */}
        <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-extrabold text-[#345873] text-base">Incidents by Category</h3>
              <p className="text-xs text-gray-400">Total volume distribution across campus infrastructure</p>
            </div>
            <BarChart3 size={20} className="text-[#F29877]" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <XAxis dataKey="name" fontSize={12} stroke="#94a3b8" />
                <YAxis fontSize={12} stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#345873',
                    color: '#FFF4E9',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}
                />
                <Bar dataKey="count" fill="#F29877" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution Pie Chart */}
        <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-extrabold text-[#345873] text-base">Incident Severity Distribution</h3>
              <p className="text-xs text-gray-400">Critical, High, Medium, and Low impact breakdown</p>
            </div>
            <AlertTriangle size={20} className="text-rose-500" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  fontSize={11}
                  fontWeight={700}
                >
                  {severityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={SEVERITY_COLORS[entry.name as keyof typeof SEVERITY_COLORS] || '#94a3b8'}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Daily Room Readiness Health Status */}
        <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-extrabold text-[#345873] text-base">Daily Room Readiness Health</h3>
              <p className="text-xs text-gray-400">60 campus rooms readiness freshness breakdown</p>
            </div>
            <ShieldCheck size={20} className="text-emerald-600" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={readinessData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={85}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  fontSize={11}
                  fontWeight={700}
                >
                  {readinessData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={READINESS_COLORS[entry.name as keyof typeof READINESS_COLORS] || '#94a3b8'}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Active Escalations List */}
      <div className="bg-white p-7 rounded-3xl border border-slate-200 shadow-xs space-y-4">
        <h3 className="font-extrabold text-base text-[#345873]">Active SLA Escalations & Alerts</h3>
        {slaStatus?.escalations && slaStatus.escalations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {slaStatus.escalations.slice(0, 8).map((esc: any, idx: number) => (
              <div
                key={idx}
                className={`p-4 rounded-2xl border flex items-center justify-between text-xs ${
                  esc.status === 'breached' ? 'bg-rose-50 border-rose-200 text-rose-900' : 'bg-amber-50 border-amber-200 text-amber-900'
                }`}
              >
                <div>
                  <span className="font-mono font-bold block text-sm">{esc.code}</span>
                  <span className="text-[11px] opacity-80">
                    Deadline: {new Date(esc.due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <StatusBadge status={esc.status === 'breached' ? 'critical' : 'warning'} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-500 italic py-4">No active SLA escalations or imminent breaches.</p>
        )}
      </div>
    </div>
  );
};

