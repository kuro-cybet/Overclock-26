import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { StatCard } from '../../shared/components/StatCard';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { DataTable } from '../../shared/components/DataTable';
import {
  Wrench,
  Clock,
  CheckCircle,
  AlertOctagon,
  FileText,
  Boxes,
  Send,
  UploadCloud,
  CheckSquare
} from 'lucide-react';

export const TechnicianDashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTask, setActiveTask] = useState<any | null>(null);
  const [diagnosis, setDiagnosis] = useState('');
  const [checklist, setChecklist] = useState<any[]>([]);
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [savingTask, setSavingTask] = useState(false);
  const [historicalCases, setHistoricalCases] = useState<any[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboard('technician');
      setData(res);
      if (res.active_task) {
        setActiveTask(res.active_task);
        setDiagnosis(res.active_task.diagnosis || '');
        setEvidenceNotes(res.active_task.evidence_notes || '');
        try {
          setChecklist(JSON.parse(res.active_task.checklist || '[]'));
        } catch {
          setChecklist([
            { task: 'Isolate power & inspect cabling', done: false },
            { task: 'Run hardware diagnostics', done: false },
            { task: 'Sign-off operational test', done: false }
          ]);
        }
        // Load historical intelligence for active task
        api.getHistoricalCases('network', res.active_task.title).then(setHistoricalCases).catch(() => {});
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChecklistItem = (index: number) => {
    const next = [...checklist];
    next[index].done = !next[index].done;
    setChecklist(next);
  };

  const handleUpdateTaskStatus = async (newStatus: string) => {
    if (!activeTask) return;
    setSavingTask(true);
    try {
      await api.updateWorkOrder(activeTask.id, {
        status: newStatus,
        diagnosis,
        checklist,
        evidence_notes: evidenceNotes
      });
      alert(`Work Order status updated to: ${newStatus}`);
      await loadDashboard();
    } catch (err: any) {
      alert(`Task update failed: ${err.message}`);
    } finally {
      setSavingTask(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#287D70] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Loading Technician Workspace...</p>
      </div>
    );
  }

  const kpi = data?.kpi || { assigned: 0, in_progress: 0, completed: 0, blocked: 0 };

  const taskCols = [
    {
      header: 'WO Code',
      accessor: 'work_order_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#287D70]">{r.work_order_code}</span>
    },
    {
      header: 'Task Title',
      accessor: 'title' as const,
      render: (r: any) => <span className="font-bold text-gray-800 text-xs">{r.title}</span>
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
      header: 'Select Task',
      render: (r: any) => (
        <button
          onClick={() => {
            setActiveTask(r);
            setDiagnosis(r.diagnosis || '');
            setEvidenceNotes(r.evidence_notes || '');
            try {
              setChecklist(JSON.parse(r.checklist || '[]'));
            } catch {
              setChecklist([]);
            }
          }}
          className="px-2.5 py-1 bg-[#287D70] text-white rounded-lg text-[11px] font-bold hover:bg-[#1f5f55] cursor-pointer"
        >
          Work On This
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#287D70]/20 text-[#287D70]">
              Operational Field Desk
            </span>
            <span className="text-xs text-gray-500 font-medium">{data?.shift}</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Technician Workspace</h1>
          <p className="text-xs text-gray-500 mt-1">
            Logged in as <span className="font-bold text-gray-800">{user?.name}</span> (Sub-role: {user?.sub_role?.replace(/_/g, ' ') || 'Maintenance Technician'}).
          </p>
        </div>

        <div className="px-4 py-2 bg-[#FFF4E9] rounded-2xl border border-peach text-xs text-gray-700">
          <span className="font-bold text-[#345873]">Campus Stock Alert:</span> {data?.parts_shortages} critical items low on stock
        </div>
      </div>

      {/* KPI Cards (Assigned, in-progress, completed, blocked) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Assigned Work"
          value={kpi.assigned}
          subtitle="Awaiting action"
          icon={<Clock size={20} />}
          accentColor="#345873"
        />
        <StatCard
          title="In Progress"
          value={kpi.in_progress}
          subtitle="Currently underway"
          icon={<Wrench size={20} />}
          accentColor="#287D70"
        />
        <StatCard
          title="Completed Jobs"
          value={kpi.completed}
          subtitle="Closed & verified"
          icon={<CheckCircle size={20} />}
          accentColor="#10b981"
        />
        <StatCard
          title="Blocked Work"
          value={kpi.blocked}
          subtitle="Parts or access delay"
          icon={<AlertOctagon size={20} />}
          accentColor="#ef4444"
          isAlert={kpi.blocked > 0}
        />
      </div>

      {/* Current Task Diagnosis & Status Update Console */}
      {activeTask && (
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono font-bold text-sm text-[#287D70] bg-[#287D70]/10 px-2 py-0.5 rounded">
                  {activeTask.work_order_code}
                </span>
                <StatusBadge status={activeTask.priority} />
                <StatusBadge status={activeTask.status} />
              </div>
              <h3 className="text-base font-extrabold text-gray-900 mt-1">{activeTask.title}</h3>
              <p className="text-xs text-gray-500">{activeTask.description}</p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleUpdateTaskStatus('in_progress')}
                disabled={savingTask}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Mark In-Progress
              </button>
              <button
                onClick={() => handleUpdateTaskStatus('completed')}
                disabled={savingTask}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Complete & Sign Off
              </button>
              <button
                onClick={() => handleUpdateTaskStatus('blocked')}
                disabled={savingTask}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Flag Blocked
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Checklist */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs text-gray-700 uppercase tracking-wider flex items-center">
                <CheckSquare size={14} className="mr-1 text-[#287D70]" />
                Field Inspection Checklist
              </h4>
              <div className="space-y-2">
                {checklist.map((item, idx) => (
                  <label
                    key={idx}
                    className="flex items-center space-x-3 p-3 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white transition cursor-pointer text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={item.done}
                      onChange={() => handleToggleChecklistItem(idx)}
                      className="rounded text-[#287D70] focus:ring-[#287D70]"
                    />
                    <span className={item.done ? 'line-through text-gray-400 font-medium' : 'text-gray-800 font-semibold'}>
                      {item.task}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Diagnosis & Evidence */}
            <div className="space-y-3">
              {/* Historical Incident Intelligence Context (Upgrade 3B) */}
              {historicalCases.length > 0 && (
                <div className="bg-[#FFF4E9]/70 border border-peach rounded-2xl p-3 text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[#345873] font-bold">
                    <span className="flex items-center space-x-1">
                      <FileText size={13} className="text-[#F29877]" />
                      <span>Historical Incident Intelligence (Verified Prior Cases)</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full font-bold">
                      {historicalCases[0].confidence_label}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-700">
                    <strong className="text-gray-900">Past Verified Diagnosis:</strong> {historicalCases[0].diagnosis}
                  </p>
                  <p className="text-[11px] text-gray-700">
                    <strong className="text-gray-900">Proven Action:</strong> {historicalCases[0].action_taken} (Avg duration: {historicalCases[0].resolution_duration_minutes}m)
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Technician Diagnosis Notes
                </label>
                <textarea
                  rows={3}
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="Record multimeter readings, hardware status, root cause..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#287D70] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Evidence Upload & Field Notes
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={evidenceNotes}
                    onChange={(e) => setEvidenceNotes(e.target.value)}
                    placeholder="Attach image URLs or physical tag serial verification..."
                    className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#287D70] focus:outline-none"
                  />
                  <button
                    onClick={() => handleUpdateTaskStatus(activeTask.status)}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-xl text-xs font-bold transition cursor-pointer"
                  >
                    Save Notes
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Task Queue Table */}
      <div className="space-y-3">
        <h3 className="font-extrabold text-sm text-[#345873]">My Assigned Task Queue</h3>
        <DataTable
          columns={taskCols}
          data={data?.my_tasks || []}
          keyField="id"
          emptyMessage="No tasks currently assigned to your shift profile."
        />
      </div>
    </div>
  );
};

