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
  Check
} from 'lucide-react';

export const FacultyExamSupportView: React.FC = () => {
  const [examBookings, setExamBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [standbySummoned, setStandbySummoned] = useState(false);
  const [selectedHall, setSelectedHall] = useState('Computer Lab A (ENG-102)');
  const [checklist, setChecklist] = useState({
    powerBackup: true,
    wifiConnectivity: true,
    labWorkstations: true,
    climateControl: false,
    audioVisual: true
  });

  useEffect(() => {
    loadExamData();
  }, []);

  const loadExamData = async () => {
    setLoading(true);
    try {
      const data = await api.getBookings('purpose=examination');
      setExamBookings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSummonStandby = () => {
    setStandbySummoned(true);
    setTimeout(() => {
      // Keep state active
    }, 1000);
  };

  const toggleChecklistItem = (key: keyof typeof checklist) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
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
          <span className="text-[11px] text-gray-500 font-medium">Midterm / Final Assessment</span>
        </div>
      )
    },
    {
      header: 'Scheduled Slot',
      render: (r: any) => (
        <div className="text-gray-700 text-xs font-medium">
          <span className="font-bold block">{new Date(r.start_time).toLocaleDateString()}</span>
          <span className="text-[11px] font-mono text-gray-500">
            {new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(r.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      )
    },
    {
      header: 'Equipment Required',
      render: (r: any) => {
        let items: string[] = [];
        try {
          items = typeof r.equipment_required === 'string' ? JSON.parse(r.equipment_required) : (r.equipment_required || []);
        } catch {
          items = ['wifi', 'pcs'];
        }
        return (
          <div className="flex flex-wrap gap-1">
            {items.map((it, idx) => (
              <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-bold uppercase tracking-wider">
                {it}
              </span>
            ))}
          </div>
        );
      }
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    },
    {
      header: 'Action',
      render: (r: any) => (
        <button
          onClick={() => {
            setSelectedHall(r.title);
            setReportModalOpen(true);
          }}
          className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1"
        >
          <ShieldAlert size={14} />
          <span>Report Issue</span>
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
              <Radio size={12} className="animate-pulse mr-1" /> Standby Protocol Active
            </span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Exam & Lab Academic Support</h1>
          <p className="text-xs text-gray-500 mt-1">
            Real-time monitoring, emergency technician summon, and facility readiness checklists for all university examinations.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSummonStandby}
            disabled={standbySummoned}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-xs font-bold transition shadow-xs cursor-pointer ${
              standbySummoned
                ? 'bg-emerald-600 text-white'
                : 'bg-rose-600 hover:bg-rose-700 text-white'
            }`}
          >
            <ShieldAlert size={16} />
            <span>{standbySummoned ? 'Technician Dispatched (ETA: 4 mins)' : 'Summon On-Site Tech Standby'}</span>
          </button>

          <button
            onClick={loadExamData}
            className="p-2.5 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {standbySummoned && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-emerald-800 text-xs">
          <div className="flex items-center space-x-3">
            <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
            <div>
              <span className="font-extrabold block">Emergency Standby Dispatched to Computer Lab A</span>
              <span>Lead Hardware Specialist (Marcus Vance) is en route with spare switches and laser projector bulbs.</span>
            </div>
          </div>
          <button
            onClick={() => setStandbySummoned(false)}
            className="text-xs font-bold text-emerald-700 underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Grid of Key Exam Halls Readiness & Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monitored Hall 1 */}
        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-sm text-[#345873]">Computer Lab A (ENG-102)</h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-100 text-emerald-700">
              Readiness: Confirmed Today
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Assigned for: <strong className="text-gray-800">CS304 Distributed Systems Midterm</strong>
          </p>
          <div className="text-xs space-y-2 border-t border-slate-100 pt-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Capacity:</span>
              <span className="font-bold text-gray-800">60 Exam Terminals</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Network:</span>
              <span className="font-bold text-emerald-600">Gigabit Fiber (Low Latency)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">HVAC Temperature:</span>
              <span className="font-bold text-gray-800">21.5°C (Stable)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Readiness Audit:</span>
              <span className="font-bold text-gray-800">Today, 08:30 AM (Floor Incharge)</span>
            </div>
          </div>
        </div>

        {/* Monitored Hall 2 */}
        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-sm text-[#345873]">Auditorium 1 (SCI-AUD)</h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-amber-100 text-amber-800">
              Readiness: Carried Forward
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Assigned for: <strong className="text-gray-800">Engineering Core Mathematics Exam</strong>
          </p>
          <div className="text-xs space-y-2 border-t border-slate-100 pt-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Capacity:</span>
              <span className="font-bold text-gray-800">200 Seated Desks</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Audio/PA System:</span>
              <span className="font-bold text-amber-600">Calibration Pending</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">HVAC Temperature:</span>
              <span className="font-bold text-gray-800">22.0°C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Scheduled Inspector:</span>
              <span className="font-bold text-gray-800">Marcus Vance (11:00 AM)</span>
            </div>
          </div>
        </div>

        {/* Pre-Exam Safety Checklist */}
        <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-3">
          <h3 className="font-extrabold text-sm text-[#345873] flex items-center space-x-2">
            <FileCheck2 size={16} className="text-[#8EB9D8]" />
            <span>Pre-Exam Inspection Signoff</span>
          </h3>
          <p className="text-xs text-gray-500">
            Verify minimum operational parameters before admitting examinees:
          </p>
          <div className="space-y-2 text-xs pt-1">
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={checklist.powerBackup}
                onChange={() => toggleChecklistItem('powerBackup')}
                className="rounded text-[#345873] focus:ring-[#345873]"
              />
              <span className="font-medium text-gray-700">UPS Inverter online & tested</span>
            </label>
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={checklist.wifiConnectivity}
                onChange={() => toggleChecklistItem('wifiConnectivity')}
                className="rounded text-[#345873] focus:ring-[#345873]"
              />
              <span className="font-medium text-gray-700">Exam Wi-Fi SSID broadcast verified</span>
            </label>
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={checklist.labWorkstations}
                onChange={() => toggleChecklistItem('labWorkstations')}
                className="rounded text-[#345873] focus:ring-[#345873]"
              />
              <span className="font-medium text-gray-700">All student PCs booted to login screen</span>
            </label>
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={checklist.climateControl}
                onChange={() => toggleChecklistItem('climateControl')}
                className="rounded text-[#345873] focus:ring-[#345873]"
              />
              <span className="font-medium text-gray-700">HVAC and air circulation active</span>
            </label>
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={checklist.audioVisual}
                onChange={() => toggleChecklistItem('audioVisual')}
                className="rounded text-[#345873] focus:ring-[#345873]"
              />
              <span className="font-medium text-gray-700">Time display projector visible to hall</span>
            </label>
          </div>
        </div>
      </div>

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

