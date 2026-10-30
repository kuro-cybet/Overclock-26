import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { QuickReportModal } from '../../features/incident-intake/QuickReportModal';
import {
  PlusCircle,
  RefreshCw,
  ClipboardList,
  Search,
  Filter,
  CheckCircle,
  Clock,
  Sparkles,
  AlertTriangle,
  X
} from 'lucide-react';

export const FacultyRequestsView: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [selectedReport, setSelectedReport] = useState<any | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await api.getReports();
      setReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.title?.toLowerCase().includes(search.toLowerCase()) ||
      r.report_code?.toLowerCase().includes(search.toLowerCase()) ||
      r.description?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;
    const matchesCat = categoryFilter === 'all' || r.category === categoryFilter;
    return matchesSearch && matchesStatus && matchesCat;
  });

  const cols = [
    {
      header: 'Ticket Code',
      accessor: 'report_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.report_code}</span>
    },
    {
      header: 'Issue Headline & Description',
      accessor: 'title' as const,
      render: (r: any) => (
        <div className="max-w-md">
          <span className="font-bold text-gray-800 text-xs block">{r.title}</span>
          <span className="text-[11px] text-gray-500 line-clamp-1">{r.description}</span>
        </div>
      )
    },
    {
      header: 'Category',
      accessor: 'category' as const,
      render: (r: any) => (
        <span className="capitalize px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700">
          {r.category}
        </span>
      )
    },
    {
      header: 'Urgency',
      accessor: 'urgency' as const,
      render: (r: any) => <StatusBadge status={r.urgency} />
    },
    {
      header: 'Status',
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
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#8EB9D8]/30 text-[#1f4a6e]">
              Faculty Support Ticket Hub
            </span>
            <span className="text-xs text-gray-500 font-medium">Automatic Intake & Triage</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">My Academic Support Requests</h1>
          <p className="text-xs text-gray-500 mt-1">
            Track submitted tickets for classroom AV repairs, lab computers, climate control, and facility maintenance.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setReportModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-[#8EB9D8] hover:bg-[#7ba9cb] text-white rounded-2xl text-xs font-bold transition cursor-pointer shadow-xs"
          >
            <PlusCircle size={16} />
            <span>New Support Request</span>
          </button>
          <button
            onClick={() => loadReports()}
            className="p-2.5 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
        <div className="relative w-full sm:w-72">
          <Search size={16} className="absolute left-3.5 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search tickets by code or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#345873]"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter size={16} className="text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#345873]"
          >
            <option value="all">All Statuses ({reports.length})</option>
            <option value="submitted">Submitted</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#345873]"
          >
            <option value="all">All Categories</option>
            <option value="classroom">Classroom AV</option>
            <option value="network">Network / Wi-Fi</option>
            <option value="equipment">Lab Equipment</option>
            <option value="electrical">Electrical</option>
            <option value="cleanliness">Sanitation</option>
          </select>
        </div>
      </div>

      {/* DataTable: 10 records per page */}
      <DataTable
        columns={cols}
        data={filteredReports}
        keyField="id"
        pageSize={10}
        onRowClick={(row) => setSelectedReport(row)}
        emptyMessage="No academic support requests found."
      />

      {/* Ticket Details Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 relative">
            <button
              onClick={() => setSelectedReport(null)}
              className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 cursor-pointer"
            >
              <X size={20} />
            </button>

            <div className="flex items-center space-x-2 text-xs text-gray-500 mb-1">
              <span className="font-mono font-bold text-[#345873]">{selectedReport.report_code}</span>
              <span>•</span>
              <span className="capitalize">{selectedReport.category}</span>
            </div>
            <h3 className="text-base font-extrabold text-[#345873]">{selectedReport.title}</h3>
            
            <p className="text-xs text-gray-600 mt-2 p-3 bg-slate-50 rounded-xl border border-slate-100">
              {selectedReport.description}
            </p>

            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              <div>
                <span className="text-gray-500 block text-[10px]">Current Status</span>
                <StatusBadge status={selectedReport.status} />
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">Urgency Rating</span>
                <StatusBadge status={selectedReport.urgency} />
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">Submitted Date</span>
                <span className="font-semibold text-gray-800">
                  {new Date(selectedReport.created_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500 block text-[10px]">Triage Engine</span>
                <span className="font-semibold text-emerald-600 flex items-center space-x-1">
                  <CheckCircle size={12} />
                  <span>AI Intake Verified</span>
                </span>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedReport(null)}
                className="px-4 py-2 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#284459] transition cursor-pointer"
              >
                Close Ticket View
              </button>
            </div>
          </div>
        </div>
      )}

      <QuickReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        onSubmitted={() => loadReports(true)}
      />
    </div>
  );
};
