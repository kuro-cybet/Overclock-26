import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { QuickReportModal } from '../../features/incident-intake/QuickReportModal';
import {
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Radio,
  FileCheck2,
  Users,
  Wrench,
  Check,
  CheckSquare,
  AlertOctagon
} from 'lucide-react';

export const FacultyExamSupportView: React.FC = () => {
  const [examBookings, setExamBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [standbySummoned, setStandbySummoned] = useState(false);
  const [selectedExam, setSelectedExam] = useState<any | null>(null);
  const [submittingInspection, setSubmittingInspection] = useState(false);
  const [inspectionResult, setInspectionResult] = useState<any | null>(null);

  const [checklist, setChecklist] = useState({
    powerBackup: true,
    wifiConnectivity: true,
    labWorkstations: true,
    climateControl: true,
    audioVisual: true
  });
  const [inspectionNotes, setInspectionNotes] = useState('');

  useEffect(() => {
    loadExamData();
  }, []);

  const loadExamData = async () => {
    setLoading(true);
    try {
      const data = await api.getExaminations();
      setExamBookings(data || []);
      if (data && data.length > 0 && !selectedExam) {
        setSelectedExam(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleChecklistItem = (key: keyof typeof checklist) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleInspectionSubmit = async (status: 'ready' | 'fault_detected') => {
    if (!selectedExam) return;
    setSubmittingInspection(true);
    setInspectionResult(null);

    const failedItems: string[] = [];
    if (!checklist.powerBackup) failedItems.push('UPS Power Backup Offline');
    if (!checklist.wifiConnectivity) failedItems.push('Exam SSID Connectivity Failure');
    if (!checklist.labWorkstations) failedItems.push('Workstations Failed Boot');
    if (!checklist.climateControl) failedItems.push('HVAC Temperature Fault');
    if (!checklist.audioVisual) failedItems.push('AV/Projector Display Failure');

    try {
      const res = await api.submitExamReadiness(selectedExam.id, {
        status,
        checklist,
        notes: inspectionNotes || (status === 'ready' ? 'All pre-exam parameters verified.' : 'Physical inspection reported infrastructure fault.'),
        reported_faults: failedItems
      });
      setInspectionResult(res);
      if (status === 'fault_detected') {
        setStandbySummoned(true);
      }
      await loadExamData();
    } catch (err: any) {
      alert(`Readiness submission failed: ${err.message}`);
    } finally {
      setSubmittingInspection(false);
    }
  };

  const cols = [
    {
      header: 'Exam Code',
      accessor: 'booking_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.booking_code}</span>
    },
    {
      header: 'Examination Session',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 text-xs block">{r.title}</span>
          <span className="text-[11px] text-gray-500 font-medium">Room: {r.room_number} ({r.building_name})</span>
        </div>
      )
    },
    {
      header: 'Scheduled Slot',
      render: (r: any) => (
        <div className="text-gray-700 text-xs font-medium">
          <span className="font-bold block">{new Date(r.start_time).toLocaleDateString()}</span>
          <span className="text-[11px] font-mono text-gray-500">
            {new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({r.hours_remaining}h left)
          </span>
        </div>
      )
    },
    {
      header: 'Room Condition',
      render: (r: any) => (
        <div className="space-y-0.5">
          <span
            className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
              r.daily_readiness_status === 'confirmed_today'
                ? 'bg-emerald-100 text-emerald-800'
                : r.daily_readiness_status === 'unavailable'
                ? 'bg-rose-100 text-rose-800'
                : 'bg-amber-100 text-amber-800'
            }`}
          >
            {r.daily_readiness_status.replace(/_/g, ' ')}
          </span>
          {r.has_open_incident && (
            <p className="text-[10px] text-rose-600 font-bold">Open Incident Flag</p>
          )}
        </div>
      )
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Audit Action',
      render: (r: any) => (
        <button
          onClick={() => setSelectedExam(r)}
          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
            selectedExam?.id === r.id
              ? 'bg-[#345873] text-white'
              : 'bg-slate-100 hover:bg-slate-200 text-gray-700'
          }`}
        >
          {selectedExam?.id === r.id ? 'Inspecting' : 'Inspect Hall'}
        </button>
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
              High-Stakes Examination Readiness
            </span>
            <span className="flex items-center text-emerald-600 font-bold text-xs">
              <Radio size={12} className="animate-pulse mr-1" /> Live Readiness Gateway
            </span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Exam & Lab Academic Support</h1>
          <p className="text-xs text-gray-500 mt-1">
            Real-time monitoring, emergency technician summon, and physical readiness checklists for all university examinations.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setReportModalOpen(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-2xl text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <ShieldAlert size={15} />
            <span>Report Urgent Exam Fault</span>
          </button>

          <button
            onClick={loadExamData}
            className="p-2.5 bg-white text-gray-600 rounded-2xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
            title="Refresh Examination Schedules"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Selected Exam Inspection Panel */}
      {selectedExam && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono font-bold text-xs bg-[#345873]/10 text-[#345873] px-2.5 py-0.5 rounded-md">
                  {selectedExam.booking_code}
                </span>
                <span className="text-xs font-bold text-gray-500">Room: {selectedExam.room_number} ({selectedExam.building_name})</span>
              </div>
              <h3 className="font-black text-base text-gray-800 mt-1">{selectedExam.title}</h3>
              <p className="text-xs text-gray-500">
                Scheduled Start: {new Date(selectedExam.start_time).toLocaleString()} ({selectedExam.hours_remaining} hours remaining)
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleInspectionSubmit('ready')}
                disabled={submittingInspection}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1.5"
              >
                <CheckCircle2 size={15} />
                <span>Confirm Hall Ready</span>
              </button>
              <button
                onClick={() => handleInspectionSubmit('fault_detected')}
                disabled={submittingInspection}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1.5"
              >
                <AlertOctagon size={15} />
                <span>Flag Fault & Alert Ops</span>
              </button>
            </div>
          </div>

          {inspectionResult && (
            <div
              className={`p-3.5 rounded-2xl text-xs font-medium ${
                inspectionResult.status === 'ready'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-50 text-rose-800 border border-rose-200'
              }`}
            >
              <p className="font-bold">{inspectionResult.message}</p>
              <p className="text-[11px] mt-0.5">
                Inspector: {inspectionResult.inspected_by} | Recorded: {inspectionResult.timestamp}
              </p>
            </div>
          )}

          {/* Interactive Inspection Checklist */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-1">
            <div className="space-y-2.5">
              <h4 className="font-bold text-xs text-gray-700 uppercase tracking-wider flex items-center">
                <FileCheck2 size={14} className="mr-1 text-[#345873]" />
                <span>Pre-Exam Physical Verification Checklist</span>
              </h4>
              <div className="space-y-2 text-xs">
                <label className="flex items-center space-x-2.5 p-2 bg-slate-50 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.powerBackup}
                    onChange={() => toggleChecklistItem('powerBackup')}
                    className="rounded text-[#345873]"
                  />
                  <span className="font-medium text-gray-800">UPS Inverter and secondary power feed online</span>
                </label>
                <label className="flex items-center space-x-2.5 p-2 bg-slate-50 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.wifiConnectivity}
                    onChange={() => toggleChecklistItem('wifiConnectivity')}
                    className="rounded text-[#345873]"
                  />
                  <span className="font-medium text-gray-800">Exam Wi-Fi SSID broadcast verified and tested</span>
                </label>
                <label className="flex items-center space-x-2.5 p-2 bg-slate-50 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.labWorkstations}
                    onChange={() => toggleChecklistItem('labWorkstations')}
                    className="rounded text-[#345873]"
                  />
                  <span className="font-medium text-gray-800">Student terminal PCs booted to secure lockdown browser</span>
                </label>
                <label className="flex items-center space-x-2.5 p-2 bg-slate-50 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.climateControl}
                    onChange={() => toggleChecklistItem('climateControl')}
                    className="rounded text-[#345873]"
                  />
                  <span className="font-medium text-gray-800">HVAC and ambient temperature regulation active</span>
                </label>
                <label className="flex items-center space-x-2.5 p-2 bg-slate-50 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.audioVisual}
                    onChange={() => toggleChecklistItem('audioVisual')}
                    className="rounded text-[#345873]"
                  />
                  <span className="font-medium text-gray-800">Countdown clock projector visible to all exam desks</span>
                </label>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-bold text-gray-700">Invigilator Field Observations & Notes</label>
              <textarea
                rows={4}
                value={inspectionNotes}
                onChange={(e) => setInspectionNotes(e.target.value)}
                placeholder="Record any broken seating, lighting flickers, or thermal readings..."
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
              />
              <p className="text-[11px] text-gray-400">
                Notice: Faculty submissions record timestamped audits. Overrides and expenditures remain gated behind administrative approval.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Scheduled Exams Table */}
      <div className="space-y-3">
        <h3 className="font-extrabold text-sm text-[#345873]">Upcoming Scheduled University Examinations</h3>
        <DataTable
          columns={cols}
          data={examBookings}
          keyField="id"
          pageSize={10}
          emptyMessage="No examinations currently scheduled."
        />
      </div>

      <QuickReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        onSubmitted={() => loadExamData()}
      />
    </div>
  );
};
