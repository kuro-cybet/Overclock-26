import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { useAuth } from '../../core/auth/AuthProvider';
import { StatCard } from '../../shared/components/StatCard';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { DataTable } from '../../shared/components/DataTable';
import { QuickReportModal } from '../../features/incident-intake/QuickReportModal';
import {
  Calendar,
  AlertCircle,
  ClipboardList,
  Sparkles,
  PlusCircle,
  Building,
  CheckCircle2,
  Users,
  ShieldAlert,
  Clock,
  ArrowRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const FacultyDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [bookingTitle, setBookingTitle] = useState('');
  const [bookingPurpose, setBookingPurpose] = useState('lecture');
  const [bookingRoomId, setBookingRoomId] = useState('');
  const [bookingDate, setBookingDate] = useState(() => {
    const d = new Date(Date.now() + 86400000);
    return d.toISOString().split('T')[0];
  });
  const [bookingStartTime, setBookingStartTime] = useState('10:00');
  const [bookingEndTime, setBookingEndTime] = useState('12:00');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);
  const [rooms, setRooms] = useState<any[]>([]);
  const [isSubmittingBooking, setIsSubmittingBooking] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [dashData, roomsData] = await Promise.all([
        api.getDashboard('faculty'),
        api.getRooms('status=available&limit=40')
      ]);
      setData(dashData);
      setRooms(roomsData);
      if (roomsData.length > 0 && !bookingRoomId) {
        setBookingRoomId(roomsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingTitle || !bookingRoomId || !bookingDate) return;

    setBookingError(null);
    setBookingSuccess(null);
    setIsSubmittingBooking(true);

    try {
      const startIso = new Date(`${bookingDate}T${bookingStartTime}:00`).toISOString();
      const endIso = new Date(`${bookingDate}T${bookingEndTime}:00`).toISOString();

      const created = await api.createBooking({
        room_id: bookingRoomId,
        title: bookingTitle,
        purpose: bookingPurpose,
        start_time: startIso,
        end_time: endIso,
        equipment_required: ['projector', 'wifi']
      });

      setBookingSuccess(`Room confirmed under code ${created.booking_code}!`);
      setBookingTitle('');
      await loadDashboard();
      setTimeout(() => {
        setBookingModalOpen(false);
        setBookingSuccess(null);
      }, 1500);
    } catch (err: any) {
      setBookingError(err.message || 'Booking conflict: Selected room is already reserved for this slot.');
    } finally {
      setIsSubmittingBooking(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#8EB9D8] mx-auto mb-3" />
        <p className="text-xs text-gray-500 font-medium">Loading Academic Workspace...</p>
      </div>
    );
  }

  const kpi = data?.kpi || { classes_today: 0, my_requests: 0, room_issues: 0, exam_alerts: 0 };

  const timetableCols = [
    {
      header: 'Booking Code',
      accessor: 'booking_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.booking_code}</span>
    },
    {
      header: 'Session / Exam Title',
      accessor: 'title' as const,
      render: (r: any) => (
        <div>
          <span className="font-bold text-gray-800 text-xs block">{r.title}</span>
          <span className="text-[11px] text-gray-500">Academic Term 2026</span>
        </div>
      )
    },
    {
      header: 'Purpose',
      accessor: 'purpose' as const,
      render: (r: any) => {
        const p = (r.purpose ? String(r.purpose) : 'General').replace(/_/g, ' ');
        const isExam = r.purpose === 'examination';
        return (
          <span
            className={`capitalize px-2.5 py-0.5 rounded-full text-[11px] font-extrabold ${
              isExam ? 'bg-amber-100 text-amber-800' : 'bg-blue-50 text-blue-700'
            }`}
          >
            {p}
          </span>
        );
      }
    },
    {
      header: 'Time Window',
      render: (r: any) => (
        <div className="text-gray-700 text-xs font-medium">
          <span className="font-bold block text-gray-800">{new Date(r.start_time).toLocaleDateString()}</span>
          <span className="text-[11px] font-mono text-gray-500">
            {new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(r.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      )
    },
    {
      header: 'Status',
      accessor: 'status' as const,
      render: (r: any) => <StatusBadge status={r.status} />
    }
  ];

  const requestCols = [
    {
      header: 'Ticket Code',
      accessor: 'report_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.report_code}</span>
    },
    {
      header: 'Subject & Description',
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
      render: (r: any) => <span className="capitalize px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-semibold">{r.category}</span>
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
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#8EB9D8]/30 text-[#1f4a6e]">
              Faculty Academic Desk
            </span>
            <span className="text-xs text-gray-500 font-medium">Academic Year 2026</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Faculty Academic Workspace</h1>
          <p className="text-xs text-gray-500 mt-1">
            Welcome, <span className="font-bold text-gray-800">{user?.name}</span> ({user?.department || 'Computer Science'}). Coordinate course sessions, lab resources, and academic support tickets.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setBookingModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-white border border-slate-200 hover:border-[#345873] text-[#345873] rounded-2xl text-xs font-bold transition cursor-pointer shadow-xs"
          >
            <PlusCircle size={16} />
            <span>Book Room</span>
          </button>
          <button
            onClick={() => setReportModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-[#8EB9D8] hover:bg-[#7ba9cb] text-white rounded-2xl text-xs font-bold transition cursor-pointer shadow-xs"
          >
            <AlertCircle size={16} />
            <span>Report Room Issue</span>
          </button>
          <button
            onClick={() => navigate('/faculty/exam-support')}
            className="flex items-center space-x-2 px-4 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-2xl text-xs font-bold transition cursor-pointer"
          >
            <ShieldAlert size={16} />
            <span>Exam Standby</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Classes Today"
          value={kpi.classes_today}
          subtitle="Scheduled sessions"
          icon={<Calendar size={20} />}
          accentColor="#8EB9D8"
        />
        <StatCard
          title="My Open Requests"
          value={kpi.my_requests}
          subtitle="Support & maintenance"
          icon={<ClipboardList size={20} />}
          accentColor="#345873"
        />
        <StatCard
          title="Campus Room Issues"
          value={kpi.room_issues}
          subtitle="Active facility repairs"
          icon={<AlertCircle size={20} />}
          accentColor="#F29877"
        />
        <StatCard
          title="Upcoming Exam Alerts"
          value={kpi.exam_alerts}
          subtitle="Monitored exam halls"
          icon={<Sparkles size={20} />}
          accentColor="#10b981"
        />
      </div>

      {/* Timetable Table: 10 records per page */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-extrabold text-sm text-[#345873]">My Allocated Lectures & Exam Timetable</h3>
          <button
            onClick={() => navigate('/faculty/timetable')}
            className="text-xs font-bold text-[#345873] hover:underline flex items-center space-x-1 cursor-pointer"
          >
            <span>View All Timetables</span>
            <ArrowRight size={14} />
          </button>
        </div>
        <DataTable
          columns={timetableCols}
          data={data?.timetable || []}
          keyField="id"
          pageSize={10}
          emptyMessage="No scheduled classes allocated for your department."
        />
      </div>

      {/* Submitted Requests Table: 10 records per page */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-extrabold text-sm text-[#345873]">My Submitted Operational Requests</h3>
          <button
            onClick={() => navigate('/faculty/requests')}
            className="text-xs font-bold text-[#345873] hover:underline flex items-center space-x-1 cursor-pointer"
          >
            <span>View All Tickets</span>
            <ArrowRight size={14} />
          </button>
        </div>
        <DataTable
          columns={requestCols}
          data={data?.my_requests || []}
          keyField="id"
          pageSize={10}
          emptyMessage="You have not submitted any room issues yet."
        />
      </div>

      <QuickReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        onSubmitted={() => loadDashboard(true)}
      />

      {/* Booking Modal */}
      {bookingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">Book Academic Space</h3>
            <p className="text-xs text-gray-500 mb-4">Timetable validation checks for conflicts automatically.</p>

            {bookingError && (
              <div className="p-3 mb-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                {bookingError}
              </div>
            )}

            {bookingSuccess && (
              <div className="p-3 mb-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center space-x-2">
                <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
                <span>{bookingSuccess}</span>
              </div>
            )}

            <form onSubmit={handleCreateBooking} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Session Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CS401 Machine Learning Seminar"
                  value={bookingTitle}
                  onChange={(e) => setBookingTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Purpose</label>
                  <select
                    value={bookingPurpose}
                    onChange={(e) => setBookingPurpose(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  >
                    <option value="lecture">Lecture</option>
                    <option value="lab_session">Lab Session</option>
                    <option value="examination">Examination</option>
                    <option value="seminar">Seminar / Workshop</option>
                    <option value="meeting">Review Session</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Date</label>
                  <input
                    type="date"
                    required
                    value={bookingDate}
                    onChange={(e) => setBookingDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Start Time</label>
                  <input
                    type="time"
                    required
                    value={bookingStartTime}
                    onChange={(e) => setBookingStartTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">End Time</label>
                  <input
                    type="time"
                    required
                    value={bookingEndTime}
                    onChange={(e) => setBookingEndTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Select Room</label>
                <select
                  value={bookingRoomId}
                  onChange={(e) => setBookingRoomId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.room_number}) — Capacity: {r.capacity} seats ({r.type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setBookingModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingBooking}
                  className="px-5 py-2 bg-[#8EB9D8] hover:bg-[#7ba9cb] text-white rounded-xl text-xs font-bold transition cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingBooking ? 'Validating...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
