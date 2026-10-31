import React, { useState, useEffect, useCallback } from 'react';
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
  CheckSquare,
  Package,
  AlertTriangle,
  CheckCircle2,
  X,
  QrCode
} from 'lucide-react';
import { RoomQrScanner } from '../../shared/components/RoomQrScanner';

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
  const [roomScannerOpen, setRoomScannerOpen] = useState(false);
  const [scannedRoom, setScannedRoom] = useState<any | null>(null);
  const [readinessSaving, setReadinessSaving] = useState(false);
  const [readinessMessage, setReadinessMessage] = useState('');

  // Parts requisition modal state
  const [partsModalOpen, setPartsModalOpen] = useState(false);
  const [inventoryList, setInventoryList] = useState<any[]>([]);
  const [selectedItemId, setSelectedItemId] = useState('');
  const [requestedQty, setRequestedQty] = useState(1);
  const [partsJustification, setPartsJustification] = useState('');
  const [submittingParts, setSubmittingParts] = useState(false);
  const [partsFeedback, setPartsFeedback] = useState<any | null>(null);

  useEffect(() => {
    loadDashboard();
    loadInventory();
    const refresh = window.setInterval(() => {
      api.getDashboard('technician').then(setData).catch((err) => {
        console.error('Failed to refresh technician work queue', err);
      });
    }, 15000);
    return () => window.clearInterval(refresh);
  }, []);

  const loadInventory = async () => {
    try {
      const items = await api.getInventory();
      setInventoryList(items || []);
      if (items && items.length > 0) {
        setSelectedItemId(items[0].id);
      }
    } catch (err) {
      console.error('Failed to load inventory for requisition', err);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboard('technician');
      setData(res);
      if (res.active_task) {
        await selectTask(res.active_task);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectTask = async (task: any) => {
    setActiveTask(task);
    setDiagnosis(task.diagnosis || '');
    setEvidenceNotes(task.evidence_notes || '');
    setPartsFeedback(null);

    // Fetch persistent database checklist items
    try {
      const dbChecklist = await api.getWorkOrderChecklist(task.id);
      setChecklist(dbChecklist || []);
    } catch {
      setChecklist([]);
    }

    // Load historical intelligence
    api.getHistoricalCases('network', task.title).then(setHistoricalCases).catch(() => {});
  };

  const handleToggleChecklistItem = async (item: any) => {
    if (!activeTask) return;
    const nextCompleted = !item.is_completed;
    try {
      const updated = await api.updateChecklistItem(activeTask.id, item.id, {
        is_completed: nextCompleted
      });
      setChecklist((prev) =>
        prev.map((c) => (c.id === item.id ? { ...c, ...updated } : c))
      );
    } catch (err: any) {
      alert(`Checklist update failed: ${err.message}`);
    }
  };

  const handleUpdateTaskStatus = async (newStatus: string) => {
    if (!activeTask) return;

    // Enforce required checklist steps before work-order completion
    if (newStatus === 'completed') {
      const incomplete = checklist.filter((c) => !c.is_completed);
      if (incomplete.length > 0) {
        alert(
          `Cannot sign off as completed: ${incomplete.length} mandatory checklist item(s) remain incomplete.\n\nPlease check off all items before completing.`
        );
        return;
      }
    }

    setSavingTask(true);
    try {
      await api.updateWorkOrder(activeTask.id, {
        status: newStatus,
        diagnosis,
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

  const handleRequisitionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTask || !selectedItemId) return;
    setSubmittingParts(true);
    setPartsFeedback(null);
    try {
      const res = await api.requisitionParts(activeTask.id, {
        item_id: selectedItemId,
        quantity: Number(requestedQty),
        justification: partsJustification
      });
      setPartsFeedback(res);
      // Reload task data to reflect blocked state if stock was depleted
      const updatedTask = await api.getWorkOrderDetails(activeTask.id);
      if (updatedTask?.work_order) {
        setActiveTask(updatedTask.work_order);
      }
    } catch (err: any) {
      alert(`Requisition failed: ${err.message}`);
    } finally {
      setSubmittingParts(false);
    }
  };

  const handleRoomQrScan = useCallback(async (value: string) => {
    const match = value.trim().match(/^(?:campusops-asset:)?([a-z0-9_-]+)$/i);
    setRoomScannerOpen(false);
    if (!match) {
      setReadinessMessage('This QR code does not contain a valid device asset tag.');
      return;
    }

    try {
      const asset = await api.getAssetByTag(match[1]);
      const room = await api.getRoomById(asset.room_id);
      setScannedRoom({ ...room, scanned_asset: asset });
      setReadinessMessage('');
    } catch (err: any) {
      setReadinessMessage(`Could not find the scanned device: ${err.message}`);
    }
  }, []);

  const handleRoomReadinessUpdate = async (status: string) => {
    if (!scannedRoom) return;
    setReadinessSaving(true);
    setReadinessMessage('');
    try {
      const room = await api.updateRoomReadiness(scannedRoom.id, status);
      setScannedRoom(room);
      setReadinessMessage(
        `${room.room_number} readiness saved as ${status.replace(/_/g, ' ')}.`
      );
    } catch (err: any) {
      setReadinessMessage(`Could not save room readiness: ${err.message}`);
    } finally {
      setReadinessSaving(false);
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
  const completedCount = checklist.filter((c) => c.is_completed).length;
  const totalCount = checklist.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

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
          onClick={() => selectTask(r)}
          className={`px-2.5 py-1 rounded-lg text-[11px] font-bold cursor-pointer transition ${
            activeTask?.id === r.id
              ? 'bg-gray-800 text-white'
              : 'bg-[#287D70] text-white hover:bg-[#1f5f55]'
          }`}
        >
          {activeTask?.id === r.id ? 'Working Now' : 'Work On This'}
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
            <span className="text-xs text-gray-500 font-medium">{data?.shift || 'Morning Shift'}</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Technician Operations Hub</h1>
          <p className="text-xs text-gray-500 mt-1">
            Execute dispatched work orders, sign off mandatory field checklists, and request spare parts requisitions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {activeTask && (
            <button
              onClick={() => {
                setPartsModalOpen(true);
                setPartsFeedback(null);
              }}
              className="flex items-center space-x-1.5 px-3.5 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-2xl text-xs font-bold transition shadow-xs cursor-pointer"
            >
              <Package size={15} />
              <span>Requisition Spare Parts</span>
            </button>
          )}

          <button
            onClick={loadDashboard}
            className="p-2.5 bg-white text-gray-600 rounded-2xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
            title="Refresh Tasks"
          >
            <Clock size={16} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Assigned Queue" value={kpi.assigned} icon={<Wrench size={20} />} accentColor="tech" />
        <StatCard title="In Progress" value={kpi.in_progress} icon={<Clock size={20} />} accentColor="admin" />
        <StatCard title="Completed Today" value={kpi.completed} icon={<CheckCircle size={20} />} accentColor="tech" />
        <StatCard title="Blocked on Parts" value={kpi.blocked} icon={<AlertOctagon size={20} />} accentColor="admin" />
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[#345873]">
              <QrCode size={17} className="text-[#287D70]" />
              Daily room readiness scan
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Scan the QR sticker attached to a device in the classroom, inspect the room, then record whether it is working, stale, or unavailable.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setReadinessMessage('');
              setScannedRoom(null);
              setRoomScannerOpen((open) => !open);
            }}
            className="rounded-xl bg-[#287D70] px-4 py-2.5 text-xs font-bold text-white transition hover:bg-[#1f5f55]"
          >
            {roomScannerOpen ? 'Close scanner' : 'Scan room QR'}
          </button>
        </div>

        {roomScannerOpen && (
          <div className="mt-4 max-w-md overflow-hidden rounded-2xl border border-slate-200 p-3">
            <RoomQrScanner onScan={handleRoomQrScan} />
          </div>
        )}

        {scannedRoom && (
          <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-bold text-gray-800">
                {scannedRoom.room_number} · {scannedRoom.name}
              </p>
              <p className="mt-0.5 text-xs text-gray-600">
                Scanned device: {scannedRoom.scanned_asset.name} ({scannedRoom.scanned_asset.asset_tag})
              </p>
              <p className="mt-0.5 text-xs text-gray-500">
                Current status: {String(scannedRoom.daily_readiness_status).replace(/_/g, ' ')}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                ['confirmed_today', 'Working'],
                ['stale', 'Stale'],
                ['unavailable', 'Unavailable'],
              ].map(([status, label]) => (
                <button
                  key={status}
                  type="button"
                  disabled={readinessSaving}
                  onClick={() => handleRoomReadinessUpdate(status)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-[#345873] transition hover:border-[#287D70] hover:text-[#287D70] disabled:opacity-50"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {readinessMessage && (
          <p role="status" className="mt-3 text-xs font-semibold text-[#345873]">
            {readinessMessage}
          </p>
        )}
      </section>

      {/* Active Work Order Action Panel */}
      {activeTask && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono font-bold text-sm text-[#287D70] bg-[#287D70]/10 px-2.5 py-0.5 rounded-lg">
                  {activeTask.work_order_code}
                </span>
                <StatusBadge status={activeTask.priority} />
                <StatusBadge status={activeTask.status} />
              </div>
              <h3 className="text-base font-extrabold text-gray-900 mt-1">{activeTask.title}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{activeTask.description}</p>
              {activeTask.blocked_reason && (
                <div className="mt-2 p-2 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-bold flex items-center space-x-2">
                  <AlertTriangle size={14} className="shrink-0" />
                  <span>Blocked: {activeTask.blocked_reason}</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <button
                onClick={() => handleUpdateTaskStatus('in_progress')}
                disabled={savingTask || activeTask.status === 'in_progress'}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Mark In-Progress
              </button>
              <button
                onClick={() => handleUpdateTaskStatus('completed')}
                disabled={savingTask || activeTask.status === 'completed'}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1"
              >
                <CheckCircle2 size={14} />
                <span>Sign Off Completed</span>
              </button>
              <button
                onClick={() => handleUpdateTaskStatus('blocked')}
                disabled={savingTask || activeTask.status === 'blocked'}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Flag Blocked
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Checklist Column */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-xs text-gray-700 uppercase tracking-wider flex items-center">
                  <CheckSquare size={14} className="mr-1.5 text-[#287D70]" />
                  <span>Mandatory Inspection Checklist</span>
                </h4>
                <span className="text-[11px] font-bold text-gray-500">
                  {completedCount}/{totalCount} Completed ({progressPercent}%)
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    progressPercent === 100 ? 'bg-emerald-500' : 'bg-[#287D70]'
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              <div className="space-y-2 pt-1">
                {checklist.map((item) => (
                  <label
                    key={item.id}
                    className={`flex items-start space-x-3 p-3 rounded-2xl border transition cursor-pointer text-xs ${
                      item.is_completed
                        ? 'border-emerald-200 bg-emerald-50/40 text-gray-500'
                        : 'border-slate-200 bg-slate-50/60 hover:bg-white text-gray-800'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={item.is_completed}
                      onChange={() => handleToggleChecklistItem(item)}
                      className="mt-0.5 rounded text-[#287D70] focus:ring-[#287D70] cursor-pointer"
                    />
                    <div className="flex-1">
                      <span className={item.is_completed ? 'line-through font-medium text-gray-400' : 'font-bold'}>
                        {item.task_description}
                      </span>
                      {item.completed_at && (
                        <p className="text-[10px] text-gray-400 mt-0.5">
                          Signed off {new Date(item.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Diagnosis & Evidence Column */}
            <div className="space-y-3">
              {historicalCases.length > 0 && (
                <div className="bg-[#FFF4E9]/70 border border-peach rounded-2xl p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[#345873] font-bold">
                    <span className="flex items-center space-x-1">
                      <FileText size={13} className="text-[#F29877]" />
                      <span>Historical Incident Intelligence</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full font-bold">
                      {historicalCases[0].confidence_label}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-700">
                    <strong>Past Verified Action:</strong> {historicalCases[0].action_taken}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Technician Diagnosis Notes
                </label>
                <textarea
                  rows={2}
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="Record multimeter readings, hardware status, root cause..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#287D70] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Physical Evidence Notes & Serial Verification
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={evidenceNotes}
                    onChange={(e) => setEvidenceNotes(e.target.value)}
                    placeholder="Attach replacement tag serial or test readings..."
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

      {/* Spare Parts Requisition Modal */}
      {partsModalOpen && activeTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-xl border border-slate-100 animate-scale-up max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-amber-100 text-amber-700 rounded-xl">
                  <Package size={18} />
                </div>
                <div>
                  <h3 className="font-black text-sm text-gray-800">Requisition Spare Parts</h3>
                  <p className="text-[11px] text-gray-500">For {activeTask.work_order_code}: {activeTask.title}</p>
                </div>
              </div>
              <button
                onClick={() => setPartsModalOpen(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-600 cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            {partsFeedback && (
              <div
                className={`p-3.5 rounded-2xl text-xs font-medium ${
                  partsFeedback.type === 'reservation'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                <p className="font-bold">{partsFeedback.message}</p>
                <p className="text-[11px] mt-0.5">
                  Type: <strong>{(partsFeedback.type ? String(partsFeedback.type) : 'Parts').toUpperCase()}</strong> | Status: {partsFeedback.status}
                </p>
              </div>
            )}

            <form onSubmit={handleRequisitionSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Select Required Spare Part (SKU)
                </label>
                <select
                  value={selectedItemId}
                  onChange={(e) => setSelectedItemId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  {inventoryList.map((item) => {
                    const available = Math.max(0, (item.stock_quantity || 0) - (item.reserved_quantity || 0));
                    return (
                      <option key={item.id} value={item.id}>
                        {item.name} ({item.item_code}) — Available: {available} / Total: {item.stock_quantity}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={requestedQty}
                  onChange={(e) => setRequestedQty(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Justification</label>
                <textarea
                  rows={2}
                  value={partsJustification}
                  onChange={(e) => setPartsJustification(e.target.value)}
                  placeholder="Explain why replacement is required..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setPartsModalOpen(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-xs font-bold transition cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={submittingParts}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer"
                >
                  {submittingParts ? 'Submitting...' : 'Submit Requisition'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
