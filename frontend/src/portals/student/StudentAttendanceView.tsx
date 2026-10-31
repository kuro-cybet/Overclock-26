import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import {
  UserCheck,
  AlertTriangle,
  CheckCircle,
  Clock,
  BookOpen,
  RefreshCw,
  TrendingUp,
  ShieldCheck
} from 'lucide-react';

export const StudentAttendanceView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAttendance();
  }, []);

  const loadAttendance = async () => {
    setLoading(true);
    try {
      const res = await api.getMyAttendance();
      setData(res);
    } catch (err) {
      console.error('Failed to load student attendance', err);
    } finally {
      setLoading(false);
    }
  };

  const courses = data?.courses || [];
  const overallPct = data?.overall_percentage ?? 88.5;
  const hasShortage = data?.has_overall_shortage || courses.some((c: any) => c.has_shortage_warning);
  const threshold = data?.threshold ?? 75.0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">My Attendance & Academic Standing</h1>
          <p className="text-xs text-gray-500 mt-1">
            Official curriculum session tracking, minimum {threshold}% examination eligibility compliance.
          </p>
        </div>

        <button
          onClick={loadAttendance}
          className="p-2.5 bg-white border border-slate-200 text-gray-600 rounded-2xl hover:bg-gray-50 transition cursor-pointer self-start sm:self-auto shadow-xs"
          title="Refresh Attendance Data"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* OVERALL ATTENDANCE KPI & WARNING BANNER */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
              Cumulative Attendance
            </span>
            <span className="text-3xl font-black text-[#345873] mt-1 block">
              {overallPct}%
            </span>
            <span className="text-[11px] font-semibold text-gray-500">
              Regulatory Minimum: {threshold}%
            </span>
          </div>
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center font-black text-xl shadow-xs ${
            overallPct >= threshold ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
          }`}>
            <UserCheck size={32} />
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
              Examination Eligibility
            </span>
            <span className={`text-lg font-black mt-1 block ${
              overallPct >= threshold ? 'text-emerald-700' : 'text-rose-700'
            }`}>
              {overallPct >= threshold ? 'Eligible for Regular Exams' : 'Shortage Detention Risk'}
            </span>
            <span className="text-[11px] text-gray-500">
              {overallPct >= threshold ? 'Full exam hall permit granted' : 'Requires HoD condonation'}
            </span>
          </div>
          <div className="w-16 h-16 rounded-2xl bg-[#FFF4E9] flex items-center justify-center text-[#d9673d]">
            <ShieldCheck size={32} />
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
              Registered Courses
            </span>
            <span className="text-3xl font-black text-[#345873] mt-1 block">
              {courses.length} Subjects
            </span>
            <span className="text-[11px] text-gray-500">Academic Term 2026</span>
          </div>
          <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-700">
            <BookOpen size={32} />
          </div>
        </div>
      </div>

      {/* SHORTAGE ALERT */}
      {hasShortage && (
        <div className="bg-rose-50 border border-rose-200 rounded-3xl p-5 flex items-start space-x-3 text-rose-900">
          <AlertTriangle size={22} className="text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-extrabold text-sm">Attendance Shortage Warning Alert</h4>
            <p className="text-xs mt-0.5 text-rose-700">
              One or more enrolled courses have fallen below the mandatory {threshold}% threshold. Please meet your course coordinator or academic mentor immediately to clear outstanding absences.
            </p>
          </div>
        </div>
      )}

      {/* SUBJECT-WISE ATTENDANCE BREAKDOWN */}
      <div className="space-y-4">
        <h2 className="text-base font-extrabold text-[#345873]">Course-Wise Attendance Records</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {courses.map((c: any) => {
            const isShort = c.percentage < threshold;
            return (
              <div
                key={c.course_id}
                className={`bg-white rounded-3xl p-6 border transition shadow-xs ${
                  isShort ? 'border-rose-300 ring-1 ring-rose-200' : 'border-slate-200 hover:border-[#345873]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-50 text-blue-700">
                    {c.course_code}
                  </span>
                  <span className={`text-base font-black ${
                    isShort ? 'text-rose-600' : 'text-emerald-700'
                  }`}>
                    {c.percentage}%
                  </span>
                </div>

                <h3 className="font-extrabold text-[#345873] text-sm mb-1">{c.course_name}</h3>
                <p className="text-xs text-gray-400 mb-4">{c.credits} Credits • Theory & Lab Combined</p>

                {/* Progress bar */}
                <div className="w-full bg-slate-100 rounded-full h-2 mb-4 overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      isShort ? 'bg-rose-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, c.percentage)}%` }}
                  />
                </div>

                {/* Detailed counts */}
                <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center text-xs">
                  <div className="p-2 rounded-xl bg-slate-50">
                    <span className="text-[10px] text-gray-400 block font-bold">Conducted</span>
                    <span className="font-black text-gray-800 text-sm">{c.conducted}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-emerald-50">
                    <span className="text-[10px] text-emerald-700 block font-bold">Attended</span>
                    <span className="font-black text-emerald-800 text-sm">{c.attended}</span>
                  </div>
                  <div className="p-2 rounded-xl bg-rose-50">
                    <span className="text-[10px] text-rose-700 block font-bold">Missed</span>
                    <span className="font-black text-rose-800 text-sm">{c.missed}</span>
                  </div>
                </div>

                {isShort && (
                  <div className="mt-3 px-3 py-1.5 bg-rose-50 text-rose-700 text-[11px] font-bold rounded-xl flex items-center justify-between">
                    <span>Below 75% limit</span>
                    <span>Needs {Math.ceil((0.75 * c.conducted - c.attended) / 0.25)} consecutive sessions</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

