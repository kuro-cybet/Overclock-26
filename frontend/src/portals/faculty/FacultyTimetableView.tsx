import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  Calendar,
  PlusCircle,
  RefreshCw,
  Search,
  Filter,
  CheckCircle,
  Building,
  Clock,
  Sparkles
} from 'lucide-react';

export const FacultyTimetableView: React.FC = () => {
  const [bookings, setBookings] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [purposeFilter, setPurposeFilter] = useState('all');

  // Booking Modal State
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [bookingTitle, setBookingTitle] = useState('');
  const [bookingPurpose, setBookingPurpose] = useState('lecture');
  const [bookingRoomId, setBookingRoomId] = useState('');
  const [bookingDate, setBookingDate] = useState(() => {
    const tomorrow = new Date(Date.now() + 86400000);
    return tomorrow.toISOString().split('T')[0];
  });
  const [bookingStartTime, setBookingStartTime] = useState('09:00');
  const [bookingEndTime, setBookingEndTime] = useState('11:00');
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [bookingsData, roomsData] = await Promise.all([
        api.getBookings(),
        api.getRooms('status=available&limit=40')
      ]);
      setBookings(bookingsData);
      setRooms(roomsData);
      if (roomsData.length > 0 && !bookingRoomId) {
        setBookingRoomId(roomsData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingTitle || !bookingRoomId || !bookingDate) return;

    setBookingError(null);
    setBookingSuccess(null);
    setIsSubmitting(true);

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

      setBookingSuccess(`Booking ${created.booking_code} confirmed! Room allocated.`);
      setBookingTitle('');
      await loadData();
      setTimeout(() => {
        setBookingModalOpen(false);
        setBookingSuccess(null);
      }, 1500);
    } catch (err: any) {
      setBookingError(err.message || 'Timetable conflict: Selected room is already reserved for this slot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredBookings = bookings.filter((b) => {
    const matchesSearch =
      b.title?.toLowerCase().includes(search.toLowerCase()) ||
      b.booking_code?.toLowerCase().includes(search.toLowerCase());
    const matchesPurpose = purposeFilter === 'all' || b.purpose === purposeFilter;
    return matchesSearch && matchesPurpose;
  });

  const cols = [
    {
      header: 'Booking Code',
      accessor: 'booking_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.booking_code}</span>
    },
    {
      header: 'Session Title',
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
      header: 'Scheduled Slot',
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

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-[#8EB9D8]/30 text-[#1f4a6e]">
              Faculty Timetable Management
            </span>
            <span className="text-xs text-gray-500 font-medium">Deterministic Conflict Engine</span>
          </div>
          <h1 className="text-2xl font-black text-[#345873] mt-1">Timetable & Room Allocations</h1>
          <p className="text-xs text-gray-500 mt-1">
            Browse schedule allocations, reserve classrooms and labs, and review examination slots with conflict validation.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setBookingModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-[#8EB9D8] hover:bg-[#7ba9cb] text-white rounded-2xl text-xs font-bold transition cursor-pointer shadow-xs"
          >
            <PlusCircle size={16} />
            <span>Book New Session / Room</span>
          </button>
          <button
            onClick={loadData}
            className="p-2.5 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search size={16} className="absolute left-3.5 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search session title or booking code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#345873]"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter size={16} className="text-gray-400" />
          <span className="text-xs font-bold text-gray-600">Purpose:</span>
          <select
            value={purposeFilter}
            onChange={(e) => setPurposeFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#345873]"
          >
            <option value="all">All Purposes ({bookings.length})</option>
            <option value="lecture">Lectures</option>
            <option value="lab_session">Lab Sessions</option>
            <option value="examination">Examinations</option>
            <option value="seminar">Seminars</option>
          </select>
        </div>
      </div>

      {/* DataTable: 10 records per page */}
      <DataTable
        columns={cols}
        data={filteredBookings}
        keyField="id"
        pageSize={10}
        emptyMessage="No timetable bookings matched your filter criteria."
      />

      {/* Booking Modal */}
      {bookingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">Book Academic Session</h3>
            <p className="text-xs text-gray-500 mb-4">
              Real-time conflict validation prevents double-booking across faculty allocations.
            </p>

            {bookingError && (
              <div className="p-3 mb-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                {bookingError}
              </div>
            )}

            {bookingSuccess && (
              <div className="p-3 mb-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center space-x-2">
                <CheckCircle size={16} className="text-emerald-600 shrink-0" />
                <span>{bookingSuccess}</span>
              </div>
            )}

            <form onSubmit={handleCreateBooking} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Session / Course Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CS410 Parallel Processing Guest Lecture"
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
                    <option value="meeting">Review Meeting</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Booking Date</label>
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
                <label className="block text-xs font-bold text-gray-700 mb-1">Select Campus Room</label>
                <select
                  value={bookingRoomId}
                  onChange={(e) => setBookingRoomId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.room_number}) — Cap: {r.capacity} seats ({r.type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setBookingModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-[#8EB9D8] hover:bg-[#7ba9cb] text-white rounded-xl text-xs font-bold transition cursor-pointer shadow-xs disabled:opacity-50"
                >
                  {isSubmitting ? 'Validating Slot...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
