import React, { useState } from 'react';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { BookOpen, TrendingUp, Award, Calendar, Clock, CheckCircle2 } from 'lucide-react';

const ENROLLED_COURSES = [
  { id: 'cs101', code: 'CS-401', title: 'Operating Systems', instructor: 'Dr. Ramesh Iyer', credits: 4, attendance: 92, grade: 'A', status: 'active', schedule: 'Mon/Wed/Fri 09:00–10:00, Room 301-A' },
  { id: 'cs102', code: 'CS-405', title: 'Computer Networks', instructor: 'Prof. Ananya Bose', credits: 4, attendance: 78, grade: 'B+', status: 'active', schedule: 'Tue/Thu 11:00–12:30, Lab 204-A' },
  { id: 'cs103', code: 'CS-410', title: 'Database Management Systems', instructor: 'Dr. Kiran Patel', credits: 3, attendance: 88, grade: 'A-', status: 'active', schedule: 'Mon/Wed 14:00–15:30, Room 208-B' },
  { id: 'cs104', code: 'MA-301', title: 'Discrete Mathematics', instructor: 'Prof. Leela Krishnan', credits: 3, attendance: 65, grade: 'C+', status: 'at_risk', schedule: 'Tue/Thu 09:00–10:30, Room 105-C' },
  { id: 'cs105', code: 'CS-420', title: 'Machine Learning', instructor: 'Dr. Fatima Sheikh', credits: 4, attendance: 95, grade: 'A+', status: 'active', schedule: 'Mon/Wed/Fri 12:00–13:00, Lab 301-B' },
  { id: 'cs106', code: 'HS-201', title: 'Technical Communication', instructor: 'Ms. Clara D\'Souza', credits: 2, attendance: 100, grade: 'A', status: 'active', schedule: 'Fri 15:00–17:00, Seminar Hall 2' },
];

const ASSIGNMENTS = [
  { id: 'a1', course: 'CS-401', title: 'Scheduling Algorithms Report', due: '2026-11-05', submitted: false, marks: null, status: 'pending' },
  { id: 'a2', course: 'CS-405', title: 'Packet Capture Lab', due: '2026-11-03', submitted: true, marks: '42/50', status: 'graded' },
  { id: 'a3', course: 'CS-410', title: 'ER Diagram Assignment', due: '2026-10-30', submitted: true, marks: '38/40', status: 'graded' },
  { id: 'a4', course: 'MA-301', title: 'Graph Theory Problem Set', due: '2026-11-07', submitted: false, marks: null, status: 'overdue' },
  { id: 'a5', course: 'CS-420', title: 'Linear Regression Implementation', due: '2026-11-10', submitted: false, marks: null, status: 'pending' },
  { id: 'a6', course: 'HS-201', title: 'Technical Paper Draft', due: '2026-11-14', submitted: false, marks: null, status: 'pending' },
];

const EXAM_SCHEDULE = [
  { id: 'e1', course: 'CS-401', title: 'Mid-Semester Exam', date: '2026-11-18', time: '10:00 – 12:00', room: 'Exam Hall 1', status: 'upcoming' },
  { id: 'e2', course: 'CS-405', title: 'Mid-Semester Exam', date: '2026-11-19', time: '14:00 – 16:00', room: 'Exam Hall 2', status: 'upcoming' },
  { id: 'e3', course: 'MA-301', title: 'Mid-Semester Exam', date: '2026-11-20', time: '10:00 – 12:00', room: 'Exam Hall 3', status: 'upcoming' },
  { id: 'e4', course: 'CS-101', title: 'Unit Test 1', date: '2026-10-15', time: '09:00 – 10:00', room: 'Room 301-A', status: 'completed' },
];

export const StudentMyLearningView: React.FC = () => {
  const [tab, setTab] = useState<'courses' | 'assignments' | 'exams'>('courses');

  const totalCredits = ENROLLED_COURSES.reduce((s, c) => s + c.credits, 0);
  const avgAttendance = Math.round(ENROLLED_COURSES.reduce((s, c) => s + c.attendance, 0) / ENROLLED_COURSES.length);
  const pendingAssignments = ASSIGNMENTS.filter(a => a.status === 'pending' || a.status === 'overdue').length;
  const upcomingExams = EXAM_SCHEDULE.filter(e => e.status === 'upcoming').length;

  const courseCols = [
    { header: 'Code', accessor: 'code' as const, render: (r: any) => <span className="font-mono font-bold text-xs text-[#345873]">{r.code}</span> },
    { header: 'Course', accessor: 'title' as const, render: (r: any) => <span className="font-bold text-sm text-gray-800">{r.title}</span> },
    { header: 'Instructor', accessor: 'instructor' as const, render: (r: any) => <span className="text-xs text-gray-500">{r.instructor}</span> },
    { header: 'Credits', accessor: 'credits' as const, render: (r: any) => <span className="font-bold text-xs text-gray-700">{r.credits}</span> },
    {
      header: 'Attendance',
      accessor: 'attendance' as const,
      render: (r: any) => (
        <div className="flex items-center space-x-2">
          <div className="w-14 bg-slate-100 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full"
              style={{ width: `${r.attendance}%`, backgroundColor: r.attendance < 75 ? '#ef4444' : r.attendance < 85 ? '#f59e0b' : '#10b981' }}
            />
          </div>
          <span className={`text-xs font-bold ${r.attendance < 75 ? 'text-red-500' : 'text-gray-600'}`}>{r.attendance}%</span>
        </div>
      )
    },
    { header: 'Grade', accessor: 'grade' as const, render: (r: any) => <span className="font-black text-sm text-[#345873]">{r.grade}</span> },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  const assignmentCols = [
    { header: 'Course', accessor: 'course' as const, render: (r: any) => <span className="font-mono font-bold text-xs text-[#345873]">{r.course}</span> },
    { header: 'Assignment', accessor: 'title' as const, render: (r: any) => <span className="font-bold text-sm text-gray-800">{r.title}</span> },
    { header: 'Due Date', accessor: 'due' as const, render: (r: any) => <span className="font-mono text-xs text-gray-500">{r.due}</span> },
    { header: 'Marks', accessor: 'marks' as const, render: (r: any) => <span className="text-xs font-bold text-gray-600">{r.marks || '—'}</span> },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  const examCols = [
    { header: 'Course', accessor: 'course' as const, render: (r: any) => <span className="font-mono font-bold text-xs text-[#345873]">{r.course}</span> },
    { header: 'Exam', accessor: 'title' as const, render: (r: any) => <span className="font-bold text-sm text-gray-800">{r.title}</span> },
    { header: 'Date', accessor: 'date' as const, render: (r: any) => <span className="font-mono text-xs text-gray-600">{r.date}</span> },
    { header: 'Time', accessor: 'time' as const, render: (r: any) => <span className="text-xs text-gray-500">{r.time}</span> },
    { header: 'Venue', accessor: 'room' as const, render: (r: any) => <span className="text-xs font-semibold text-gray-700">{r.room}</span> },
    { header: 'Status', accessor: 'status' as const, render: (r: any) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center space-x-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
          <BookOpen size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-[#345873]">My Learning</h1>
          <p className="text-xs text-gray-500 mt-0.5">Enrolled courses, assignments, grades and exam schedule</p>
        </div>
      </div>

      {/* Demonstration Dataset Banner */}
      <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-3 text-xs text-amber-900">
        <span className="px-2 py-0.5 rounded-md bg-amber-200 font-black text-[10px] tracking-wide text-amber-900 shrink-0">
          DEMONSTRATION DATASET
        </span>
        <p>
          Enrolled courses, attendance metrics, and assignment submissions shown below represent a simulated academic curriculum dataset.
        </p>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Enrolled Courses', value: ENROLLED_COURSES.length, icon: <BookOpen size={18} />, color: '#345873' },
          { label: 'Total Credits', value: totalCredits, icon: <Award size={18} />, color: '#A58ACF' },
          { label: 'Avg Attendance', value: `${avgAttendance}%`, icon: <TrendingUp size={18} />, color: avgAttendance < 75 ? '#ef4444' : '#10b981' },
          { label: 'Pending Tasks', value: pendingAssignments, icon: <Clock size={18} />, color: '#F29877' },
        ].map((k, i) => (
          <div key={i} className="bg-white rounded-3xl border border-slate-200 shadow-xs p-5 flex items-center space-x-4">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0" style={{ backgroundColor: `${k.color}18`, color: k.color }}>
              {k.icon}
            </div>
            <div>
              <p className="text-2xl font-black" style={{ color: k.color }}>{k.value}</p>
              <p className="text-xs text-gray-400 font-semibold">{k.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Low Attendance Warning */}
      {ENROLLED_COURSES.some(c => c.attendance < 75) && (
        <div className="flex items-center space-x-3 bg-red-50 border border-red-200 rounded-2xl px-4 py-3">
          <CheckCircle2 size={16} className="text-red-400 shrink-0" />
          <p className="text-xs text-red-700 font-semibold">
            ⚠️ Your attendance in <strong>MA-301 (Discrete Mathematics)</strong> is below the 75% threshold. You may be barred from the semester exam. Please contact your faculty advisor.
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-2">
        {([
          { key: 'courses', label: 'My Courses' },
          { key: 'assignments', label: 'Assignments' },
          { key: 'exams', label: 'Exam Schedule' },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-5 py-2 rounded-full text-xs font-bold transition ${
              tab === t.key ? 'bg-[#345873] text-white shadow' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-extrabold text-sm text-[#345873]">
            {tab === 'courses' ? 'Enrolled Courses — Semester 7' : tab === 'assignments' ? 'Assignments & Submissions' : 'Upcoming Examinations'}
          </h3>
        </div>
        <div className="p-4">
          {tab === 'courses' && <DataTable columns={courseCols} data={ENROLLED_COURSES} keyField="id" emptyMessage="No courses enrolled." />}
          {tab === 'assignments' && <DataTable columns={assignmentCols} data={ASSIGNMENTS} keyField="id" emptyMessage="No assignments found." />}
          {tab === 'exams' && <DataTable columns={examCols} data={EXAM_SCHEDULE} keyField="id" emptyMessage="No exams scheduled." />}
        </div>
      </div>
    </div>
  );
};

