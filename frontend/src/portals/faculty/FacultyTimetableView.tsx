import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import {
  Calendar,
  PlusCircle,
  RefreshCw,
  Search,
  CheckCircle,
  Building,
  Clock,
  UserCheck,
  Check,
  X,
  AlertCircle,
  BookOpen,
  Users
} from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

const DEFAULT_FACULTY_SCHEDULE = {
  faculty_id: 'default-faculty',
  today_dow: new Date().getDay() === 0 ? 0 : new Date().getDay() - 1,
  weekly_schedule: [
    { id: 'f-mon-1', day_of_week: 0, start_time: '09:00', end_time: '10:00', slot_type: 'lecture', course_code: 'CS-301', course_name: 'Data Structures & Algorithms', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-mon-2', day_of_week: 0, start_time: '10:15', end_time: '11:15', slot_type: 'lecture', course_code: 'CS-302', course_name: 'Operating Systems & Concurrency', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-102', room_name: 'Lecture Hall 102', room_number: '102' },
    { id: 'f-mon-3', day_of_week: 0, start_time: '11:30', end_time: '12:30', slot_type: 'lecture', course_code: 'CS-303', course_name: 'Database Engineering & SQL', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-mon-4', day_of_week: 0, start_time: '13:30', end_time: '15:30', slot_type: 'lab', course_code: 'CS-304', course_name: 'Computer Networks Lab', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-204', room_name: 'Networks & Systems Lab', room_number: '204' },
    { id: 'f-tue-1', day_of_week: 1, start_time: '09:00', end_time: '10:00', slot_type: 'lecture', course_code: 'CS-302', course_name: 'Operating Systems & Concurrency', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-102', room_name: 'Lecture Hall 102', room_number: '102' },
    { id: 'f-tue-2', day_of_week: 1, start_time: '10:15', end_time: '11:15', slot_type: 'lecture', course_code: 'CS-303', course_name: 'Database Engineering & SQL', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-tue-3', day_of_week: 1, start_time: '11:30', end_time: '12:30', slot_type: 'lecture', course_code: 'CS-301', course_name: 'Data Structures & Algorithms', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-wed-1', day_of_week: 2, start_time: '09:00', end_time: '10:00', slot_type: 'lecture', course_code: 'CS-304', course_name: 'Computer Networks & Protocols', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-wed-2', day_of_week: 2, start_time: '10:15', end_time: '12:15', slot_type: 'lab', course_code: 'CS-301', course_name: 'DSA Programming Lab', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-204', room_name: 'Computing Lab 1', room_number: '204' },
    { id: 'f-thu-1', day_of_week: 3, start_time: '09:00', end_time: '10:00', slot_type: 'lecture', course_code: 'CS-303', course_name: 'Database Engineering & SQL', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-thu-2', day_of_week: 3, start_time: '10:15', end_time: '11:15', slot_type: 'lecture', course_code: 'CS-302', course_name: 'Operating Systems & Concurrency', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-102', room_name: 'Lecture Hall 102', room_number: '102' },
    { id: 'f-fri-1', day_of_week: 4, start_time: '09:00', end_time: '10:00', slot_type: 'lecture', course_code: 'CS-301', course_name: 'Data Structures & Algorithms', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-fri-2', day_of_week: 4, start_time: '10:15', end_time: '11:15', slot_type: 'lecture', course_code: 'CS-304', course_name: 'Computer Networks & Protocols', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-101', room_name: 'Lecture Hall 101', room_number: '101' },
    { id: 'f-sat-1', day_of_week: 5, start_time: '09:30', end_time: '11:30', slot_type: 'tutorial', course_code: 'CS-302', course_name: 'Operating Systems Tutorial & Problem Solving', section_id: 'sec-cse-a', section_name: 'CSE-A', department: 'Computer Science', room_id: 'rm-102', room_name: 'Lecture Hall 102', room_number: '102' },
  ]
};

const DEFAULT_STUDENTS_LIST = [
  { student_id: 'stu-01', name: 'Aarav Sundaram', email: 'aarav.s@campusops.edu', register_number: 'REG-2026-CS001', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-02', name: 'Bhavna Raman', email: 'bhavna.r@campusops.edu', register_number: 'REG-2026-CS002', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-03', name: 'Chetan Venkat', email: 'chetan.v@campusops.edu', register_number: 'REG-2026-CS003', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-04', name: 'Divya Krishnan', email: 'divya.k@campusops.edu', register_number: 'REG-2026-CS004', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-05', name: 'Eashwar Murugan', email: 'eashwar.m@campusops.edu', register_number: 'REG-2026-CS005', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-06', name: 'Gowri Shankar', email: 'gowri.s@campusops.edu', register_number: 'REG-2026-CS006', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-07', name: 'Harish Kumar', email: 'harish.k@campusops.edu', register_number: 'REG-2026-CS007', department: 'Computer Science', default_status: 'present' },
  { student_id: 'stu-08', name: 'Ishwarya Lakshmi', email: 'ishwariya.l@campusops.edu', register_number: 'REG-2026-CS008', department: 'Computer Science', default_status: 'present' },
];

export const FacultyTimetableView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'schedule' | 'today' | 'bookings'>('schedule');
  const [scheduleData, setScheduleData] = useState<any>(DEFAULT_FACULTY_SCHEDULE);
  const [bookings, setBookings] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<number>(0);

  // Attendance Marking State
  const [attendanceModalOpen, setAttendanceModalOpen] = useState(false);
  const [selectedClass, setSelectedClass] = useState<any>(null);
  const [enrolledStudents, setEnrolledStudents] = useState<any[]>(DEFAULT_STUDENTS_LIST);
  const [attendanceRecords, setAttendanceRecords] = useState<Record<string, string>>({});
  const [studentSearch, setStudentSearch] = useState('');
  const [topicCovered, setTopicCovered] = useState('');
  const [attendanceSubmitting, setAttendanceSubmitting] = useState(false);
  const [attendanceFeedback, setAttendanceFeedback] = useState<string | null>(null);

  // Room Booking Modal State
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
      const [schedule, bookingsData, roomsData] = await Promise.all([
        api.getMyTimetable().catch(() => null),
        api.getBookings().catch(() => []),
        api.getRooms('status=available&limit=40').catch(() => [])
      ]);
      const validSchedule = (schedule && Array.isArray(schedule.weekly_schedule) && schedule.weekly_schedule.length > 0)
        ? schedule
        : DEFAULT_FACULTY_SCHEDULE;
      setScheduleData(validSchedule);
      setBookings(Array.isArray(bookingsData) ? bookingsData : []);
      setRooms(Array.isArray(roomsData) ? roomsData : []);
      if (Array.isArray(roomsData) && roomsData.length > 0 && !bookingRoomId) {
        setBookingRoomId(roomsData[0].id);
      }
      if (validSchedule?.today_dow != null && validSchedule.today_dow <= 5) {
        setSelectedDay(validSchedule.today_dow);
      }
    } catch (err) {
      console.error('Failed to load faculty academic schedule', err);
      setScheduleData(DEFAULT_FACULTY_SCHEDULE);
    } finally {
      setLoading(false);
    }
  };

  const openAttendanceModal = async (classSession: any) => {
    setSelectedClass(classSession);
    setAttendanceModalOpen(true);
    setAttendanceFeedback(null);
    setTopicCovered('');
    try {
      const students = await api.getEnrolledStudents(
        classSession.section_id || 'cse-a',
        classSession.course_id || 'cs-301'
      ).catch(() => null);
      const validStudents = (Array.isArray(students) && students.length > 0) ? students : DEFAULT_STUDENTS_LIST;
      setEnrolledStudents(validStudents);
      const defaults: Record<string, string> = {};
      validStudents.forEach((s: any) => {
        defaults[s.student_id] = s.default_status || 'present';
      });
      setAttendanceRecords(defaults);
    } catch (err) {
      console.error('Failed to fetch students', err);
      setEnrolledStudents(DEFAULT_STUDENTS_LIST);
      const defaults: Record<string, string> = {};
      DEFAULT_STUDENTS_LIST.forEach((s) => {
        defaults[s.student_id] = 'present';
      });
      setAttendanceRecords(defaults);
    }
  };

  const markAllStatus = (status: 'present' | 'absent') => {
    const updated: Record<string, string> = {};
    enrolledStudents.forEach((s) => {
      updated[s.student_id] = status;
    });
    setAttendanceRecords(updated);
  };

  const handleAttendanceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClass) return;
    setAttendanceSubmitting(true);
    setAttendanceFeedback(null);

    const payload = {
      section_id: selectedClass.section_id || 'cse-a',
      course_id: selectedClass.course_id || 'cs-301',
      session_date: new Date().toISOString().split('T')[0],
      start_time: selectedClass.start_time,
      end_time: selectedClass.end_time,
      topic_covered: topicCovered || 'Regular Curriculum Session',
      records: Object.entries(attendanceRecords).map(([student_id, status]) => ({
        student_id,
        status,
        remarks: status !== 'present' ? 'Automated roll mark' : null
      }))
    };

    try {
      const res = await api.submitAttendance(payload);
      setAttendanceFeedback(`Attendance marked successfully for ${res.total_marked} students (${res.present_count} Present, ${res.absent_count} Absent, ${res.late_count} Late).`);
      setTimeout(() => {
        setAttendanceModalOpen(false);
      }, 1800);
    } catch (err: any) {
      setAttendanceFeedback(err?.message || 'Failed to submit attendance.');
    } finally {
      setAttendanceSubmitting(false);
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

  const weeklySchedule = scheduleData?.weekly_schedule || [];
  const daySchedule = weeklySchedule.filter((s: any) => s.day_of_week === selectedDay);
  daySchedule.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));

  const presentCount = Object.values(attendanceRecords).filter((s) => s === 'present').length;
  const absentCount = Object.values(attendanceRecords).filter((s) => s === 'absent').length;
  const lateCount = Object.values(attendanceRecords).filter((s) => s === 'late').length;

  const filteredStudents = enrolledStudents.filter((s) =>
    s.name.toLowerCase().includes(studentSearch.toLowerCase()) ||
    s.register_number.toLowerCase().includes(studentSearch.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">My Teaching Schedule & Attendance</h1>
          <p className="text-xs text-gray-500 mt-1">
            Faculty academic timetable, daily classroom sessions, room reservations, and instant student roll call.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setBookingModalOpen(true)}
            className="flex items-center space-x-1.5 px-4 py-2.5 bg-[#345873] hover:bg-[#253f54] text-white rounded-2xl text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <PlusCircle size={16} />
            <span>Book Room / Lab</span>
          </button>
          <button
            onClick={loadData}
            className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer shadow-xs"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-4">
        <button
          onClick={() => setActiveTab('schedule')}
          className={`pb-3 text-xs font-bold transition border-b-2 cursor-pointer flex items-center space-x-2 ${
            activeTab === 'schedule'
              ? 'border-[#345873] text-[#345873]'
              : 'border-transparent text-gray-400 hover:text-gray-600'
          }`}
        >
          <Calendar size={16} />
          <span>Weekly Timetable</span>
        </button>
        <button
          onClick={() => setActiveTab('today')}
          className={`pb-3 text-xs font-bold transition border-b-2 cursor-pointer flex items-center space-x-2 ${
            activeTab === 'today'
              ? 'border-[#345873] text-[#345873]'
              : 'border-transparent text-gray-400 hover:text-gray-600'
          }`}
        >
          <UserCheck size={16} />
          <span>Today's Sessions & Attendance</span>
        </button>
        <button
          onClick={() => setActiveTab('bookings')}
          className={`pb-3 text-xs font-bold transition border-b-2 cursor-pointer flex items-center space-x-2 ${
            activeTab === 'bookings'
              ? 'border-[#345873] text-[#345873]'
              : 'border-transparent text-gray-400 hover:text-gray-600'
          }`}
        >
          <Building size={16} />
          <span>Room Reservations ({bookings.length})</span>
        </button>
      </div>

      {/* TAB 1: Weekly Timetable */}
      {activeTab === 'schedule' && (
        <div className="space-y-6">
          {/* Day Selector */}
          <div className="flex flex-wrap gap-2">
            {DAYS.map((dayName, idx) => (
              <button
                key={dayName}
                onClick={() => setSelectedDay(idx)}
                className={`px-4 py-2 rounded-2xl text-xs font-bold transition cursor-pointer ${
                  selectedDay === idx
                    ? 'bg-[#345873] text-white shadow-xs'
                    : 'bg-white text-gray-600 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                {dayName}
                {scheduleData?.today_dow === idx && (
                  <span className="ml-1.5 px-1.5 py-0.2 bg-amber-400 text-amber-950 rounded-full text-[10px]">
                    Today
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Day's Classes Cards */}
          {daySchedule.length === 0 ? (
            <div className="bg-white rounded-3xl p-8 border border-slate-200 text-center text-gray-400 text-sm">
              No classes scheduled for {DAYS[selectedDay]}. Enjoy your research and prep time!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {daySchedule.map((slot: any) => (
                <div
                  key={slot.id}
                  className="bg-white rounded-3xl p-5 border border-slate-200 shadow-xs hover:border-[#345873] transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-50 text-blue-700">
                        {slot.course_code}
                      </span>
                      <span className="text-[11px] font-mono font-bold text-gray-500 flex items-center">
                        <Clock size={12} className="mr-1 text-gray-400" />
                        {slot.start_time} - {slot.end_time}
                      </span>
                    </div>

                    <h3 className="font-extrabold text-[#345873] text-sm leading-tight mb-1">
                      {slot.course_name}
                    </h3>
                    <p className="text-xs text-gray-500">
                      Section {slot.section_name} • {slot.department}
                    </p>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-gray-600">
                      <span className="flex items-center">
                        <Building size={14} className="mr-1 text-[#287D70]" />
                        {slot.room_name} ({slot.room_number})
                      </span>
                      <span className="capitalize font-semibold text-gray-400 text-[11px]">
                        {slot.slot_type}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => openAttendanceModal(slot)}
                    className="mt-5 w-full py-2.5 bg-[#287D70] hover:bg-[#206359] text-white rounded-2xl text-xs font-bold transition flex items-center justify-center space-x-1.5 cursor-pointer shadow-xs"
                  >
                    <UserCheck size={14} />
                    <span>Mark Roll Attendance</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Today's Sessions & Attendance */}
      {activeTab === 'today' && (
        <div className="space-y-4">
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs">
            <h2 className="text-base font-extrabold text-[#345873] mb-4">
              Today's Scheduled Academic Sessions
            </h2>
            {scheduleData?.today_classes?.length === 0 ? (
              <p className="text-sm text-gray-500">No teaching sessions scheduled for today.</p>
            ) : (
              <div className="space-y-3">
                {scheduleData?.today_classes?.map((slot: any) => (
                  <div
                    key={slot.id}
                    className="p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50 transition"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          {slot.course_code}
                        </span>
                        <span className="font-bold text-gray-800 text-sm">{slot.course_name}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Time: <span className="font-semibold text-gray-700">{slot.start_time} - {slot.end_time}</span> • Venue: <span className="font-semibold text-gray-700">{slot.room_name} ({slot.room_number})</span> • Section: <span className="font-semibold text-gray-700">{slot.section_name}</span>
                      </p>
                    </div>

                    <button
                      onClick={() => openAttendanceModal(slot)}
                      className="px-4 py-2 bg-[#287D70] hover:bg-[#206359] text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer self-start sm:self-auto shrink-0 shadow-xs"
                    >
                      <UserCheck size={14} />
                      <span>Take Attendance</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Room Bookings */}
      {activeTab === 'bookings' && (
        <DataTable
          columns={[
            {
              header: 'Booking Code',
              accessor: 'booking_code' as const,
              render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.booking_code}</span>
            },
            {
              header: 'Purpose / Title',
              accessor: 'title' as const,
              render: (r: any) => (
                <div>
                  <span className="font-bold text-gray-800 block">{r.title}</span>
                  <span className="text-[10px] text-gray-400 capitalize">{r.purpose}</span>
                </div>
              )
            },
            {
              header: 'Time Window',
              render: (r: any) => (
                <span className="text-xs font-mono text-gray-600">
                  {new Date(r.start_time).toLocaleDateString()} {new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(r.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )
            },
            {
              header: 'Status',
              accessor: 'status' as const,
              render: (r: any) => <StatusBadge status={r.status} />
            }
          ]}
          data={bookings}
          keyField="id"
        />
      )}

      {/* ATTENDANCE MARKING MODAL */}
      {attendanceModalOpen && selectedClass && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-extrabold text-[#345873]">
                  Class Roll Call: {selectedClass.course_code} - {selectedClass.course_name}
                </h3>
                <p className="text-xs text-gray-500">
                  Section {selectedClass.section_name} • {selectedClass.start_time} - {selectedClass.end_time}
                </p>
              </div>
              <button
                onClick={() => setAttendanceModalOpen(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-600 cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Actions & Roll Summary */}
            <div className="py-3 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100">
              <div className="flex items-center space-x-2 text-xs">
                <span className="px-2.5 py-1 bg-emerald-50 text-emerald-800 font-bold rounded-lg">
                  Present: {presentCount}
                </span>
                <span className="px-2.5 py-1 bg-rose-50 text-rose-800 font-bold rounded-lg">
                  Absent: {absentCount}
                </span>
                <span className="px-2.5 py-1 bg-amber-50 text-amber-800 font-bold rounded-lg">
                  Late: {lateCount}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => markAllStatus('present')}
                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold cursor-pointer"
                >
                  Mark All Present
                </button>
                <button
                  type="button"
                  onClick={() => markAllStatus('absent')}
                  className="px-2.5 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-bold cursor-pointer"
                >
                  Mark All Absent
                </button>
              </div>
            </div>

            {/* Search filter */}
            <div className="my-3">
              <input
                type="text"
                placeholder="Search enrolled student by name or register number..."
                value={studentSearch}
                onChange={(e) => setStudentSearch(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
              />
            </div>

            {attendanceFeedback && (
              <div className={`p-3 rounded-xl mb-3 text-xs font-bold ${
                attendanceFeedback.includes('successfully')
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-50 text-rose-800 border border-rose-200'
              }`}>
                {attendanceFeedback}
              </div>
            )}

            {/* Student list */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 my-2">
              {filteredStudents.length === 0 ? (
                <p className="text-xs text-gray-400 py-4 text-center">No enrolled students found.</p>
              ) : (
                filteredStudents.map((st) => {
                  const currentStatus = attendanceRecords[st.student_id] || 'present';
                  return (
                    <div
                      key={st.student_id}
                      className="p-3 bg-[#FFF4E9]/30 rounded-2xl border border-slate-200 flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-gray-800 text-xs block">{st.name}</span>
                        <span className="font-mono text-[10px] text-gray-400">{st.register_number}</span>
                      </div>

                      <div className="flex items-center space-x-1">
                        <button
                          type="button"
                          onClick={() => setAttendanceRecords((prev) => ({ ...prev, [st.student_id]: 'present' }))}
                          className={`px-3 py-1 rounded-lg text-xs font-bold cursor-pointer transition ${
                            currentStatus === 'present'
                              ? 'bg-emerald-600 text-white shadow-xs'
                              : 'bg-white text-gray-600 border border-slate-200 hover:bg-emerald-50'
                          }`}
                        >
                          P
                        </button>
                        <button
                          type="button"
                          onClick={() => setAttendanceRecords((prev) => ({ ...prev, [st.student_id]: 'absent' }))}
                          className={`px-3 py-1 rounded-lg text-xs font-bold cursor-pointer transition ${
                            currentStatus === 'absent'
                              ? 'bg-rose-600 text-white shadow-xs'
                              : 'bg-white text-gray-600 border border-slate-200 hover:bg-rose-50'
                          }`}
                        >
                          A
                        </button>
                        <button
                          type="button"
                          onClick={() => setAttendanceRecords((prev) => ({ ...prev, [st.student_id]: 'late' }))}
                          className={`px-3 py-1 rounded-lg text-xs font-bold cursor-pointer transition ${
                            currentStatus === 'late'
                              ? 'bg-amber-500 text-white shadow-xs'
                              : 'bg-white text-gray-600 border border-slate-200 hover:bg-amber-50'
                          }`}
                        >
                          L
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Curriculum Topic & Submit */}
            <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <input
                type="text"
                placeholder="Topic covered today (e.g. Balanced Trees, Thread Synchronization)..."
                value={topicCovered}
                onChange={(e) => setTopicCovered(e.target.value)}
                className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
              />
              <button
                onClick={handleAttendanceSubmit}
                disabled={attendanceSubmitting}
                className="px-5 py-2 bg-[#287D70] hover:bg-[#206359] text-white rounded-xl text-xs font-bold transition disabled:opacity-50 cursor-pointer shadow-xs shrink-0"
              >
                {attendanceSubmitting ? 'Recording...' : 'Submit Roll Call'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ROOM BOOKING MODAL */}
      {bookingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">
              Reserve Room or Laboratory
            </h3>
            <p className="text-xs text-gray-500 mb-4">Request space allocation with automated clash detection</p>

            {bookingError && (
              <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl mb-4 border border-red-200 font-semibold flex items-center">
                <AlertCircle size={16} className="mr-2 shrink-0" />
                <span>{bookingError}</span>
              </div>
            )}

            {bookingSuccess && (
              <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl mb-4 border border-emerald-200 font-semibold flex items-center">
                <CheckCircle size={16} className="mr-2 shrink-0" />
                <span>{bookingSuccess}</span>
              </div>
            )}

            <form onSubmit={handleCreateBooking} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Event / Class Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Advanced Cryptography Lecture"
                  value={bookingTitle}
                  onChange={(e) => setBookingTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Purpose</label>
                <select
                  value={bookingPurpose}
                  onChange={(e) => setBookingPurpose(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none bg-white"
                >
                  <option value="lecture">Lecture / Theory Class</option>
                  <option value="lab_session">Lab Practical Session</option>
                  <option value="examination">Examination / Assessment</option>
                  <option value="seminar">Seminar / Guest Talk</option>
                  <option value="meeting">Department Meeting</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Venue / Room</label>
                <select
                  value={bookingRoomId}
                  onChange={(e) => setBookingRoomId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none bg-white"
                >
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.room_number}) • Capacity: {r.capacity}
                    </option>
                  ))}
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

              <div className="pt-3 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setBookingModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-gray-500 hover:bg-gray-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-[#345873] text-white text-xs font-bold hover:bg-[#253f54] transition cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? 'Verifying Conflict...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
