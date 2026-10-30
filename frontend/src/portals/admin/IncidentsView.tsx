import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Filter, Layers, CheckSquare, Search, Sparkles, RefreshCw } from 'lucide-react';

export const IncidentsView: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<any | null>(null);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [selectedReportsForCorrelation, setSelectedReportsForCorrelation] = useState<string[]>([]);
  const [correlating, setCorrelating] = useState(false);

  useEffect(() => {
    loadData();
  }, [filterSeverity]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [incData, repData] = await Promise.all([
        api.getIncidents(filterSeverity ? `severity=${filterSeverity}` : ''),
        api.getReports('status=submitted')
      ]);
      setIncidents(incData);
      setReports(repData);
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
      await api.correlateReports({
        report_ids: selectedReportsForCorrelation,
        target_incident_id: targetIncidentId,
        new_title: 'Correlated Cluster Outage'
      });
      setSelectedReportsForCorrelation([]);
      await loadData();
      alert('Reports successfully correlated to incident! All submitters notified.');
    } catch (err: any) {
      alert(`Correlation error: ${err.message}`);
    } finally {
      setCorrelating(false);
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
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 text-xs">
              Select an incident from the table to view real-time diagnostics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

