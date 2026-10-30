import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Filter, Sparkles, RefreshCw, Plus, Wrench, X } from 'lucide-react';

export const IncidentsView: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<any | null>(null);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [selectedReportsForCorrelation, setSelectedReportsForCorrelation] = useState<string[]>([]);
  const [correlating, setCorrelating] = useState(false);
  const [incidentDetails, setIncidentDetails] = useState<any | null>(null);
  const [staff, setStaff] = useState<any[]>([]);

  // Create work order modal state
  const [woModalOpen, setWoModalOpen] = useState(false);
  const [woTitle, setWoTitle] = useState('');
  const [woDescription, setWoDescription] = useState('');
  const [woPriority, setWoPriority] = useState('P3');
  const [assignMode, setAssignMode] = useState<'auto' | 'manual'>('auto');
  const [woTechId, setWoTechId] = useState('');
  const [creatingWo, setCreatingWo] = useState(false);

  useEffect(() => {
    loadData();
  }, [filterSeverity]);

  useEffect(() => {
    if (selectedIncident?.id) {
      loadIncidentDetails(selectedIncident.id);
    } else {
      setIncidentDetails(null);
    }
  }, [selectedIncident?.id]);

  const loadIncidentDetails = async (id: string) => {
    try {
      const details = await api.getIncidentDetails(id);
      setIncidentDetails(details);
      return details;
    } catch (err) {
      console.error(err);
      setIncidentDetails(null);
      return null;
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [incData, repData, staffData] = await Promise.all([
        api.getIncidents(filterSeverity ? `severity=${filterSeverity}` : ''),
        api.getReports('status=submitted'),
        api.getStaff()
      ]);
      setIncidents(incData);
      setReports(repData);
      setStaff(staffData);
      if (incData.length > 0 && !selectedIncident) {
        setSelectedIncident(incData[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCorrelate = async (targetIncidentId?: string) => {
    if (selectedReportsForCorrelation.length === 0) return;
    setCorrelating(true);
    try {
      const incident = await api.correlateReports({
        report_ids: selectedReportsForCorrelation,
        target_incident_id: targetIncidentId,
        new_title: 'Correlated Cluster Outage'
      });
      setSelectedReportsForCorrelation([]);
      await loadData();

      if (incident?.id) {
        setSelectedIncident(incident);
        const details = await loadIncidentDetails(incident.id);
        const workOrder = details?.work_orders?.[0];
        const technician = workOrder
          ? staff.find((member) => member.user_id === workOrder.assigned_technician_id)
          : null;

        if (workOrder) {
          alert(
            `Incident ${incident.incident_code} created. Work order ${workOrder.work_order_code} ` +
            (technician ? `assigned to ${technician.name}.` : 'is waiting for a technician.')
          );
        } else {
          alert(`Incident ${incident.incident_code} created.`);
        }
      } else {
        alert('Reports correlated successfully.');
      }
    } catch (err: any) {
      alert(`Correlation error: ${err.message}`);
    } finally {
      setCorrelating(false);
    }
  };

  const openWorkOrderModal = () => {
    if (!selectedIncident) return;
    setWoTitle(`Repair: ${selectedIncident.title}`);
    setWoDescription(selectedIncident.description || '');
    setWoPriority(selectedIncident.priority || 'P3');
    setAssignMode('auto');
    setWoTechId('');
    setWoModalOpen(true);
  };

  const handleCreateWorkOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident) return;

    setCreatingWo(true);
    try {
      const workOrder = await api.createWorkOrder({
        incident_id: selectedIncident.id,
        title: woTitle,
        description: woDescription,
        priority: woPriority,
        auto_assign: assignMode === 'auto',
        assigned_technician_id: assignMode === 'manual' ? woTechId : undefined,
      });

      setWoModalOpen(false);
      await loadData();
      await loadIncidentDetails(selectedIncident.id);

      const technician = staff.find((member) => member.user_id === workOrder.assigned_technician_id);
      alert(
        `Work order ${workOrder.work_order_code} created` +
        (technician ? ` and assigned to ${technician.name}.` : ' (unassigned).')
      );
    } catch (err: any) {
      alert(`Could not create work order: ${err.message}`);
    } finally {
      setCreatingWo(false);
    }
  };

  const toggleReportSelection = (reportId: string) => {
    setSelectedReportsForCorrelation(prev =>
      prev.includes(reportId) ? prev.filter(id => id !== reportId) : [...prev, reportId]
    );
  };

  const cols = [
    {
      header: 'Incident Code',
      accessor: 'incident_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.incident_code}</span>
    },
    {
      header: 'Summary & Category',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 block text-xs">{r.title}</span>
          <span className="text-[10px] text-gray-500 capitalize">{r.category}</span>
        </div>
      )
    },
    {
      header: 'Severity',
      accessor: 'severity' as const,
      render: (r: any) => <StatusBadge status={r.severity} />
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
      header: 'Linked Reports',
      accessor: 'correlated_count' as const,
      render: (r: any) => (
        <span className="px-2 py-0.5 bg-blue-50 text-blue-800 rounded font-bold text-[11px]">
          {r.correlated_count}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Incidents & Intelligent Triage</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            View canonical incident streams, inspect linked user reports, and merge correlated events.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-white px-3 py-1.5 rounded-xl border border-slate-200">
            <Filter size={14} className="text-gray-400" />
            <span className="text-xs font-semibold text-gray-600">Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="text-xs font-bold text-[#345873] bg-transparent focus:outline-none cursor-pointer"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <button
            onClick={loadData}
            className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
            title="Refresh"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Main Grid: Incident Table & Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <DataTable
            columns={cols}
            data={incidents}
            keyField="id"
            onRowClick={(row) => setSelectedIncident(row)}
          />

          {/* Uncorrelated Incoming Reports & Correlation Engine */}
          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles size={18} className="text-[#F29877]" />
                <h3 className="font-bold text-[#345873] text-sm">
                  Incoming Uncorrelated Reports ({reports.length})
                </h3>
              </div>

              {selectedReportsForCorrelation.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-gray-500">
                    {selectedReportsForCorrelation.length} selected
                  </span>
                  <button
                    disabled={correlating}
                    onClick={() => handleCorrelate(selectedIncident?.id)}
                    className="px-3 py-1.5 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#253f54] transition cursor-pointer"
                  >
                    {correlating ? 'Merging...' : `Merge into Selected Incident`}
                  </button>
                  <button
                    disabled={correlating}
                    onClick={() => handleCorrelate()}
                    className="px-3 py-1.5 bg-[#F29877] text-white rounded-xl text-xs font-bold hover:bg-[#e07b55] transition cursor-pointer"
                  >
                    Create New Canonical
                  </button>
                </div>
              )}
            </div>

            <p className="text-xs text-gray-500">
              Select multiple complaints below to merge into one operational incident while preserving each user's original ticket record:
            </p>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {reports.length === 0 ? (
                <p className="text-xs text-gray-400 italic py-3 text-center">
                  All submitted reports have been correlated or triaged.
                </p>
              ) : (
                reports.map((rep) => {
                  const isChecked = selectedReportsForCorrelation.includes(rep.id);
                  return (
                    <div
                      key={rep.id}
                      onClick={() => toggleReportSelection(rep.id)}
                      className={`p-3 rounded-2xl border text-xs flex items-center justify-between transition cursor-pointer ${
                        isChecked
                          ? 'bg-[#FFF4E9] border-[#F29877] ring-1 ring-[#F29877]'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-0.5 rounded text-[#345873]"
                        />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-mono font-bold text-[#345873]">{rep.report_code}</span>
                            <span className="font-semibold text-gray-800">{rep.title}</span>
                          </div>
                          <p className="text-gray-500 text-[11px] mt-0.5">{rep.description}</p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <StatusBadge status={rep.urgency} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Selected Incident Detail Inspector */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs h-fit sticky top-24">
          {selectedIncident ? (
            <div className="space-y-5">
              <div className="border-b border-slate-100 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-sm font-black text-[#345873] bg-[#FFF4E9] px-2.5 py-1 rounded-lg">
                    {selectedIncident.incident_code}
                  </span>
                  <StatusBadge status={selectedIncident.priority} />
                </div>
                <h3 className="font-extrabold text-base text-gray-900 leading-tight">
                  {selectedIncident.title}
                </h3>
                <p className="text-xs text-gray-500 mt-1 capitalize">
                  Category: <span className="font-bold text-gray-700">{selectedIncident.category}</span>
                </p>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-gray-400 block font-semibold text-[10px] uppercase tracking-wider">
                    Operational Status
                  </span>
                  <div className="mt-1">
                    <StatusBadge status={selectedIncident.status} />
                  </div>
                </div>

                <div>
                  <span className="text-gray-400 block font-semibold text-[10px] uppercase tracking-wider">
                    Resolution SLA Deadline
                  </span>
                  <span className="font-bold text-gray-800 block mt-0.5">
                    {selectedIncident.sla_due_at
                      ? new Date(selectedIncident.sla_due_at).toLocaleString()
                      : 'N/A'}
                  </span>
                  {selectedIncident.is_sla_breached && (
                    <span className="text-rose-600 font-bold text-[11px]">
                      SLA Target Breached (Escalated to Director)
                    </span>
                  )}
                </div>

                <div>
                  <span className="text-gray-400 block font-semibold text-[10px] uppercase tracking-wider">
                    Summary & Scope
                  </span>
                  <p className="text-gray-700 leading-relaxed bg-[#FFF4E9]/50 p-3 rounded-xl border border-peach/50 mt-1">
                    {selectedIncident.description}
                  </p>
                </div>

                <div>
                  <span className="text-gray-400 block font-semibold text-[10px] uppercase tracking-wider">
                    Correlated Tickets
                  </span>
                  <span className="text-xs font-bold text-blue-700">
                    {selectedIncident.correlated_count} individual reports linked
                  </span>
                </div>

                <div>
                  <span className="text-gray-400 block font-semibold text-[10px] uppercase tracking-wider">
                    Work Orders
                  </span>
                  {incidentDetails?.work_orders?.length ? (
                    <div className="space-y-1.5 mt-1">
                      {incidentDetails.work_orders.map((wo: any) => {
                        const technician = staff.find((member) => member.user_id === wo.assigned_technician_id);
                        return (
                          <div
                            key={wo.id}
                            className="flex items-center justify-between gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2"
                          >
                            <div>
                              <span className="font-mono font-bold text-[#345873]">
                                {wo.work_order_code}
                              </span>
                              <span className="block text-[10px] text-gray-500">
                                {technician ? technician.name : 'Awaiting technician'}
                              </span>
                            </div>
                            <StatusBadge status={wo.status} />
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-[11px] text-gray-400 italic mt-1">
                      No work order yet.
                    </p>
                  )}

                  {!incidentDetails?.work_orders?.length &&
                    !['resolved', 'closed', 'cancelled'].includes(selectedIncident.status) && (
                      <button
                        onClick={openWorkOrderModal}
                        className="mt-2 w-full flex items-center justify-center space-x-1.5 px-3 py-2 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#253f54] transition cursor-pointer"
                      >
                        <Plus size={13} />
                        <span>Create Work Order</span>
                      </button>
                    )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 text-xs">
              Select an incident from the table to view real-time diagnostics.
            </div>
          )}
        </div>
      </div>

      {/* Create Work Order Modal */}
      {woModalOpen && selectedIncident && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-[#FFF4E9] text-[#F29877] flex items-center justify-center shrink-0">
                  <Wrench size={20} />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-[#345873]">Create Work Order</h3>
                  <p className="text-xs text-gray-500 font-mono">
                    {selectedIncident.incident_code} — {selectedIncident.title}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setWoModalOpen(false)}
                className="text-gray-400 hover:text-gray-700 cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateWorkOrder} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Work Title</label>
                <input
                  type="text"
                  required
                  value={woTitle}
                  onChange={(e) => setWoTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  required
                  value={woDescription}
                  onChange={(e) => setWoDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Priority</label>
                <select
                  value={woPriority}
                  onChange={(e) => setWoPriority(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                >
                  <option value="P1">P1 — Critical (4h SLA)</option>
                  <option value="P2">P2 — High (12h SLA)</option>
                  <option value="P3">P3 — Medium (48h SLA)</option>
                  <option value="P4">P4 — Low (96h SLA)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Dispatch</label>
                <div className="flex items-center space-x-4 text-xs font-semibold text-gray-700">
                  <label className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="radio"
                      checked={assignMode === 'auto'}
                      onChange={() => setAssignMode('auto')}
                    />
                    <span>Auto-assign best technician</span>
                  </label>
                  <label className="flex items-center space-x-1.5 cursor-pointer">
                    <input
                      type="radio"
                      checked={assignMode === 'manual'}
                      onChange={() => setAssignMode('manual')}
                    />
                    <span>Choose technician</span>
                  </label>
                </div>
              </div>

              {assignMode === 'manual' && (
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Technician</label>
                  <select
                    required
                    value={woTechId}
                    onChange={(e) => setWoTechId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  >
                    <option value="">Select a technician...</option>
                    {staff
                      .filter((member) => !['absent', 'on_leave'].includes(member.availability_status))
                      .map((member) => (
                        <option key={member.user_id} value={member.user_id}>
                          {member.name} ({member.shift}) — load {member.current_workload} — {member.skills.join(', ')}
                        </option>
                      ))}
                  </select>
                </div>
              )}

              <div className="pt-3 flex justify-end space-x-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setWoModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingWo || (assignMode === 'manual' && !woTechId)}
                  className="px-5 py-2 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#253f54] transition cursor-pointer disabled:opacity-50"
                >
                  {creatingWo ? 'Creating...' : 'Create & Dispatch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

