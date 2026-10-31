import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import {
  Calendar,
  Clock,
  Building,
  User,
  BookOpen,
  RefreshCw,
  AlertCircle,
  GraduationCap
} from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function format12Hour(time24: string): string {
  if (!time24 || !time24.includes(':')) return time24 || '';
  const [hStr, mStr] = time24.split(':');
  let h = parseInt(hStr, 10);
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12;
  if (h === 0) h = 12;
  return `${h}:${mStr} ${ampm}`;
}

export const StudentTimetableView: React.FC = () => {
  const [scheduleData, setScheduleData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [viewMode, setViewMode] = useState<'weekly' | 'today'>('weekly');

  useEffect(() => {
    loadTimetable();
  }, []);

  const loadTimetable = async () => {
    setLoading(true);
    try {
      const data = await api.getMyTimetable();
      setScheduleData(data);
      if (data?.today_dow != null && data.today_dow <= 5) {
        setSelectedDay(data.today_dow);
      }
    } catch (err) {
      console.error('Failed to load student timetable', err);
    } finally {
      setLoading(false);
    }
  };

  const weeklySchedule = scheduleData?.weekly_schedule || [];
  const todayClasses = scheduleData?.today_classes || [];
  const daySchedule = weeklySchedule.filter((s: any) => s.day_of_week === selectedDay);
  daySchedule.sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">My Academic Timetable</h1>
          <p className="text-xs text-gray-500 mt-1">
            Weekly scheduled course lectures, laboratory sessions, designated halls, and faculty mentors.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
            <button
              onClick={() => setViewMode('weekly')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                viewMode === 'weekly' ? 'bg-[#345873] text-white shadow-xs' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Weekly Grid
            </button>
            <button
              onClick={() => setViewMode('today')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                viewMode === 'today' ? 'bg-[#345873] text-white shadow-xs' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Today's Classes ({todayClasses.length})
            </button>
          </div>

          <button
            onClick={loadTimetable}
            className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer shadow-xs"
            title="Refresh Timetable"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* TODAY'S UPCOMING HIGHLIGHT CARD */}
      {todayClasses.length > 0 && viewMode === 'weekly' && (
        <div className="bg-gradient-to-r from-[#345873] to-[#287D70] rounded-3xl p-6 text-white shadow-md">
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#FFD6BA] block mb-1">
            Next Upcoming Session Today
          </span>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-black">{todayClasses[0].course_name} ({todayClasses[0].course_code})</h2>
              <p className="text-xs text-slate-200 mt-0.5">
                Instructor: {todayClasses[0].faculty_name} • Venue: {todayClasses[0].room_name} ({todayClasses[0].room_number})
              </p>
            </div>
            <div className="px-4 py-2 rounded-2xl bg-white/10 backdrop-blur-xs font-mono font-black text-sm tracking-wide self-start sm:self-auto border border-white/20">
              {format12Hour(todayClasses[0].start_time)} - {format12Hour(todayClasses[0].end_time)}
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Today Only */}
      {viewMode === 'today' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-base font-extrabold text-[#345873]">
            Classes Scheduled for Today ({DAYS[scheduleData?.today_dow ?? 0]})
          </h2>
          {todayClasses.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">
              No classes scheduled for today. You are free to pursue self-study or lab projects.
            </div>
          ) : (
            <div className="space-y-3">
              {todayClasses.map((s: any, idx: number) => (
                <div
                  key={s.id || idx}
                  className="p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-[#345873] transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-xs bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full">
                        {s.course_code}
                      </span>
                      <span className="font-extrabold text-[#345873] text-sm">{s.course_name}</span>
                    </div>
                    <p className="text-xs text-gray-500">
                      Faculty: <span className="font-semibold text-gray-700">{s.faculty_name}</span> • Room: <span className="font-semibold text-gray-700">{s.room_name} ({s.room_number})</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-extrabold text-[#345873] text-sm block">
                      {format12Hour(s.start_time)} - {format12Hour(s.end_time)}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                      {s.slot_type}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* VIEW: Weekly Grid */}
      {viewMode === 'weekly' && (
        <div className="space-y-6">
          {/* Day Tabs */}
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

          {daySchedule.length === 0 ? (
            <div className="bg-white rounded-3xl p-10 border border-slate-200 text-center text-gray-400 text-sm">
              Your timetable has not been published yet for {DAYS[selectedDay]}.
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
                      <span className="text-xs font-mono font-bold text-gray-500 flex items-center">
                        <Clock size={12} className="mr-1 text-gray-400" />
                        {format12Hour(slot.start_time)} - {format12Hour(slot.end_time)}
                      </span>
                    </div>

                    <h3 className="font-extrabold text-[#345873] text-sm leading-tight mb-1">
                      {slot.course_name}
                    </h3>
                    <p className="text-xs text-gray-500 flex items-center mt-1">
                      <User size={13} className="mr-1 text-gray-400 shrink-0" />
                      <span>{slot.faculty_name}</span>
                    </p>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-gray-600">
                      <span className="flex items-center">
                        <Building size={14} className="mr-1 text-[#287D70]" />
                        {slot.room_name} ({slot.room_number})
                      </span>
                      <span className="font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[10px]">
                        {slot.credits} Credits
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

